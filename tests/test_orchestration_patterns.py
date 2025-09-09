"""
Unit tests for Orchestration Patterns.

Tests all five coordination patterns: MapReduce, Pipeline, Fork-Join,
Scatter-Gather, and Saga with comprehensive pattern selection and execution.
"""
import pytest
from datetime import datetime

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.patterns import (
    OrchestrationPattern,
    PatternExecutor,
    TaskSlice,
    PatternResult,
    MapReducePattern,
    PipelinePattern,
    ForkJoinPattern,
    ScatterGatherPattern,
    SagaPattern,
    BaseOrchestrationPattern,
)


class TestTaskSlice:
    """Test TaskSlice data class"""

    def test_task_slice_creation(self):
        """Test TaskSlice creation with defaults"""
        slice_obj = TaskSlice(slice_id="test-1", content="Test content")

        assert slice_obj.slice_id == "test-1"
        assert slice_obj.content == "Test content"
        assert slice_obj.metadata == {}
        assert slice_obj.dependencies == []
        assert slice_obj.estimated_duration == 1.0

    def test_task_slice_with_metadata(self):
        """Test TaskSlice with custom metadata"""
        metadata = {"priority": "high", "owner": "test-agent"}
        slice_obj = TaskSlice(
            slice_id="test-2",
            content="Complex task",
            metadata=metadata,
            dependencies=["dep-1", "dep-2"],
            estimated_duration=5.0,
        )

        assert slice_obj.metadata == metadata
        assert slice_obj.dependencies == ["dep-1", "dep-2"]
        assert slice_obj.estimated_duration == 5.0


class TestPatternResult:
    """Test PatternResult data class"""

    def test_pattern_result_creation(self):
        """Test PatternResult creation"""
        result = PatternResult(
            pattern=OrchestrationPattern.MAPREDUCE,
            success=True,
            result="Test result",
            execution_time=2.5,
            slices_processed=10,
            agents_used=3,
        )

        assert result.pattern == OrchestrationPattern.MAPREDUCE
        assert result.success is True
        assert result.result == "Test result"
        assert result.execution_time == 2.5
        assert result.slices_processed == 10
        assert result.agents_used == 3
        assert result.error_message == ""
        assert result.metadata == {}


class TestMapReducePattern:
    """Test MapReduce orchestration pattern"""

    def test_initialization(self):
        """Test MapReduce pattern initialization"""
        pattern = MapReducePattern()

        assert pattern.pattern_type == OrchestrationPattern.MAPREDUCE
        assert pattern.custom_reducers == {}
        assert pattern.execution_stats["total_executions"] == 0

    @pytest.mark.asyncio
    async def test_mapreduce_execution_success(self):
        """Test successful MapReduce execution"""
        pattern = MapReducePattern()

        task_slices = [
            TaskSlice("slice-1", "Process data 1"),
            TaskSlice("slice-2", "Process data 2"),
            TaskSlice("slice-3", "Process data 3"),
        ]

        agents = ["agent-1", "agent-2"]

        result = await pattern.execute(task_slices, agents)

        assert isinstance(result, PatternResult)
        assert result.success
        assert result.pattern == OrchestrationPattern.MAPREDUCE
        assert result.execution_time > 0
        assert result.slices_processed == 3
        assert result.agents_used == 2
        assert result.result is not None

    @pytest.mark.asyncio
    async def test_mapreduce_empty_input(self):
        """Test MapReduce with empty input"""
        pattern = MapReducePattern()

        result = await pattern.execute([], ["agent-1"])

        assert result.success
        assert result.slices_processed == 0

    def test_slice_distribution(self):
        """Test task slice distribution across agents"""
        pattern = MapReducePattern()

        slices = [TaskSlice(f"slice-{i}", f"Data {i}") for i in range(5)]
        agents = ["agent-1", "agent-2"]

        distribution = pattern._distribute_slices(slices, agents)

        assert len(distribution) == 2
        assert len(distribution["agent-1"]) + len(distribution["agent-2"]) == 5

    def test_reduction_type_detection(self):
        """Test reduction type detection"""
        pattern = MapReducePattern()

        # Numeric reduction
        numeric_results = [1, 2, 3, 4, 5]
        assert pattern._determine_reduction_type(numeric_results) == "numeric"

        # String reduction
        string_results = ["hello", "world", "test"]
        assert pattern._determine_reduction_type(string_results) == "string"

        # List reduction
        list_results = [[1, 2], [3, 4], [5, 6]]
        assert pattern._determine_reduction_type(list_results) == "list"

        # Dict reduction
        dict_results = [{"a": 1}, {"b": 2}, {"c": 3}]
        assert pattern._determine_reduction_type(dict_results) == "dict"

        # Mixed reduction
        mixed_results = [1, "hello", [1, 2]]
        assert pattern._determine_reduction_type(mixed_results) == "mixed"

    @pytest.mark.asyncio
    async def test_reduce_phase_numeric(self):
        """Test reduce phase with numeric data"""
        pattern = MapReducePattern()

        numeric_results = [10, 20, 30]
        task_slices = []

        result = await pattern._reduce_phase(numeric_results, task_slices)
        assert result == 60

    @pytest.mark.asyncio
    async def test_reduce_phase_strings(self):
        """Test reduce phase with string data"""
        pattern = MapReducePattern()

        string_results = ["line1", "line2", "line3"]
        task_slices = []

        result = await pattern._reduce_phase(string_results, task_slices)
        assert result == "line1\nline2\nline3"

    def test_custom_reducer_registration(self):
        """Test custom reducer registration"""
        pattern = MapReducePattern()

        def custom_reducer(results):
            return len(results)

        pattern.register_custom_reducer("count", custom_reducer)

        assert "count" in pattern.custom_reducers
        assert pattern.custom_reducers["count"] == custom_reducer

    def test_performance_metrics(self):
        """Test performance metrics tracking"""
        pattern = MapReducePattern()

        # Simulate execution result
        result = PatternResult(
            pattern=OrchestrationPattern.MAPREDUCE,
            success=True,
            execution_time=1.5,
            agents_used=3,
        )

        pattern.update_stats(result)

        metrics = pattern.get_performance_metrics()
        assert metrics["pattern"] == "mapreduce"
        assert metrics["success_rate"] == 100.0
        assert metrics["total_executions"] == 1
        assert metrics["average_execution_time"] == 1.5


class TestPipelinePattern:
    """Test Pipeline orchestration pattern"""

    def test_initialization(self):
        """Test Pipeline pattern initialization"""
        pattern = PipelinePattern()

        assert pattern.pattern_type == OrchestrationPattern.PIPELINE
        assert pattern.stage_processors == {}

    @pytest.mark.asyncio
    async def test_pipeline_execution_success(self):
        """Test successful Pipeline execution"""
        pattern = PipelinePattern()

        task_slices = [TaskSlice("input", "Initial data")]
        agents = ["stage-1", "stage-2", "stage-3"]

        result = await pattern.execute(task_slices, agents)

        assert result.success
        assert result.pattern == OrchestrationPattern.PIPELINE
        assert result.agents_used == 3
        assert "stage_0" in str(result.result)  # Should show processing stages

    @pytest.mark.asyncio
    async def test_pipeline_empty_agents(self):
        """Test Pipeline with no agents"""
        pattern = PipelinePattern()

        task_slices = [TaskSlice("input", "data")]
        agents = []

        result = await pattern.execute(task_slices, agents)

        assert result.success
        assert result.agents_used == 0

    @pytest.mark.asyncio
    async def test_pipeline_stage_processing(self):
        """Test individual pipeline stage processing"""
        pattern = PipelinePattern()

        # Test string processing
        string_result = await pattern._execute_pipeline_stage(
            "agent", "input", "stage_1"
        )
        assert "stage_1" in string_result

        # Test dict processing
        dict_input = {"key": "value"}
        dict_result = await pattern._execute_pipeline_stage(
            "agent", dict_input, "stage_2"
        )
        assert "stage_2" in dict_result
        assert dict_result["key"] == "value"

        # Test list processing
        list_input = ["item1", "item2"]
        list_result = await pattern._execute_pipeline_stage(
            "agent", list_input, "stage_3"
        )
        assert "processed_by_stage_3" in list_result

    def test_stage_processor_registration(self):
        """Test custom stage processor registration"""
        pattern = PipelinePattern()

        async def custom_processor(data):
            return f"Custom: {data}"

        pattern.register_stage_processor("custom_stage", custom_processor)

        assert "custom_stage" in pattern.stage_processors
        assert pattern.stage_processors["custom_stage"] == custom_processor


class TestForkJoinPattern:
    """Test Fork-Join orchestration pattern"""

    def test_initialization(self):
        """Test Fork-Join pattern initialization"""
        pattern = ForkJoinPattern()

        assert pattern.pattern_type == OrchestrationPattern.FORK_JOIN
        assert pattern.join_strategies == {}

    @pytest.mark.asyncio
    async def test_forkjoin_execution_success(self):
        """Test successful Fork-Join execution"""
        pattern = ForkJoinPattern()

        task_slices = [
            TaskSlice("task-1", "Work item 1"),
            TaskSlice("task-2", "Work item 2"),
        ]
        agents = ["fork-1", "fork-2", "fork-3"]

        result = await pattern.execute(task_slices, agents)

        assert result.success
        assert result.pattern == OrchestrationPattern.FORK_JOIN
        assert result.agents_used == 3
        assert result.metadata["successful_forks"] > 0

    @pytest.mark.asyncio
    async def test_fork_task_execution(self):
        """Test individual fork task execution"""
        pattern = ForkJoinPattern()

        task_slice = TaskSlice("test", "Test content")
        result = await pattern._execute_fork_task("agent", task_slice, 1)

        assert result["fork_id"] == 1
        assert "Test content" in result["result"]
        assert "agent" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_join_results(self):
        """Test result joining"""
        pattern = ForkJoinPattern()

        fork_results = [
            {"fork_id": 0, "result": "Result 0"},
            {"fork_id": 1, "result": "Result 1"},
            Exception("Fork 2 failed"),  # Simulated failure
        ]

        joined = await pattern._join_results(fork_results, [])

        assert joined["pattern"] == "fork_join"
        assert joined["total_forks"] == 3
        assert joined["successful_forks"] == 2
        assert len(joined["results"]) == 2

    @pytest.mark.asyncio
    async def test_join_all_failed(self):
        """Test joining when all forks failed"""
        pattern = ForkJoinPattern()

        fork_results = [Exception("Failed"), Exception("Also failed")]
        joined = await pattern._join_results(fork_results, [])

        assert "error" in joined

    def test_join_strategy_registration(self):
        """Test custom join strategy registration"""
        pattern = ForkJoinPattern()

        async def custom_joiner(results):
            return {"custom": "join"}

        pattern.register_join_strategy("custom", custom_joiner)

        assert "custom" in pattern.join_strategies


class TestScatterGatherPattern:
    """Test Scatter-Gather orchestration pattern"""

    def test_initialization(self):
        """Test Scatter-Gather pattern initialization"""
        pattern = ScatterGatherPattern()

        assert pattern.pattern_type == OrchestrationPattern.SCATTER_GATHER
        assert pattern.gather_strategies == {}

    @pytest.mark.asyncio
    async def test_scatter_gather_execution(self):
        """Test successful Scatter-Gather execution"""
        pattern = ScatterGatherPattern()

        task_slices = [TaskSlice("broadcast", "Question for all agents")]
        agents = ["agent-1", "agent-2", "agent-3"]

        result = await pattern.execute(task_slices, agents)

        assert result.success
        assert result.pattern == OrchestrationPattern.SCATTER_GATHER
        assert result.agents_used == 3
        assert result.metadata["responses_received"] == 3

    @pytest.mark.asyncio
    async def test_scatter_task_execution(self):
        """Test individual scatter task execution"""
        pattern = ScatterGatherPattern()

        task = TaskSlice("question", "What is your response?")
        result = await pattern._execute_scatter_task("agent", task, 1)

        assert result["agent_id"] == 1
        assert "What is your response?" in result["response"]
        assert "confidence" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_gather_responses(self):
        """Test response gathering"""
        pattern = ScatterGatherPattern()

        responses = [
            {"agent_id": 0, "response": "Response A", "confidence": 0.8},
            {"agent_id": 1, "response": "Response B", "confidence": 0.9},
            {
                "agent_id": 2,
                "response": "Response A",
                "confidence": 0.7,
            },  # Same as first
        ]

        task = TaskSlice("question", "Test question")
        result = await pattern._gather_responses(responses, task)

        assert result["pattern"] == "scatter_gather"
        assert result["successful_responses"] == 3
        assert "analysis" in result

    def test_response_analysis(self):
        """Test response analysis"""
        pattern = ScatterGatherPattern()

        responses = [
            {"response": "Answer A", "confidence": 0.8},
            {"response": "Answer A", "confidence": 0.9},
            {"response": "Answer B", "confidence": 0.6},
        ]

        analysis = pattern._analyze_responses(responses)

        assert analysis["response_count"] == 3
        assert analysis["average_confidence"] > 0
        assert analysis["response_diversity"] == 2  # Two unique responses
        assert analysis["consensus_strength"] > 0

    def test_gather_strategy_registration(self):
        """Test custom gather strategy registration"""
        pattern = ScatterGatherPattern()

        async def custom_gatherer(responses):
            return {"gathered": len(responses)}

        pattern.register_gather_strategy("count", custom_gatherer)

        assert "count" in pattern.gather_strategies


class TestSagaPattern:
    """Test Saga orchestration pattern"""

    def test_initialization(self):
        """Test Saga pattern initialization"""
        pattern = SagaPattern()

        assert pattern.pattern_type == OrchestrationPattern.SAGA
        assert pattern.compensation_handlers == {}

    @pytest.mark.asyncio
    async def test_saga_execution_success(self):
        """Test successful Saga execution"""
        pattern = SagaPattern()

        task_slices = [
            TaskSlice("step-1", "Transaction step 1"),
            TaskSlice("step-2", "Transaction step 2"),
            TaskSlice("step-3", "Transaction step 3"),
        ]
        agents = ["agent-1", "agent-2", "agent-3"]

        result = await pattern.execute(task_slices, agents)

        assert result.success
        assert result.pattern == OrchestrationPattern.SAGA
        assert len(result.result["completed_steps"]) == 3
        assert result.metadata["steps_completed"] == 3

    @pytest.mark.asyncio
    async def test_saga_step_execution(self):
        """Test individual saga step execution"""
        pattern = SagaPattern()

        task_slice = TaskSlice("transaction", "Process payment")
        result = await pattern._execute_saga_step("agent", task_slice, "payment_step")

        assert "payment_step" in result
        assert "Process payment" in result

    @pytest.mark.asyncio
    async def test_compensation_action_creation(self):
        """Test compensation action creation"""
        pattern = SagaPattern()

        task_slice = TaskSlice("transaction", "Debit account")
        compensation = await pattern._create_compensation_action(
            task_slice, "Debited $100", "debit_step"
        )

        assert callable(compensation)

        # Test compensation execution
        comp_result = await compensation()
        assert comp_result is not None

    @pytest.mark.asyncio
    async def test_saga_compensation_execution(self):
        """Test compensation execution"""
        pattern = SagaPattern()

        # Create mock compensation actions
        compensations = []
        for i in range(3):

            async def compensate(step_id=i):
                return f"Compensated step {step_id}"

            compensations.append(compensate)

        # Execute compensations (should not raise exception)
        await pattern._execute_compensation(compensations)

        # Test should complete without errors
        assert True

    def test_compensation_handler_registration(self):
        """Test compensation handler registration"""
        pattern = SagaPattern()

        async def custom_handler(data):
            return f"Handled: {data}"

        pattern.register_compensation_handler("custom_step", custom_handler)

        assert "custom_step" in pattern.compensation_handlers


class TestPatternExecutor:
    """Test central pattern executor"""

    def test_initialization(self):
        """Test PatternExecutor initialization"""
        executor = PatternExecutor()

        assert len(executor.patterns) == 5
        assert OrchestrationPattern.MAPREDUCE in executor.patterns
        assert OrchestrationPattern.SAGA in executor.patterns
        assert executor.execution_history == []

    @pytest.mark.asyncio
    async def test_pattern_execution(self):
        """Test executing specific pattern"""
        executor = PatternExecutor()

        task_slices = [TaskSlice("test", "Test task")]
        agents = ["agent-1"]

        result = await executor.execute_pattern(
            OrchestrationPattern.FORK_JOIN, task_slices, agents
        )

        assert result.success
        assert result.pattern == OrchestrationPattern.FORK_JOIN
        assert len(executor.execution_history) == 1

    @pytest.mark.asyncio
    async def test_invalid_pattern_execution(self):
        """Test executing invalid pattern"""
        executor = PatternExecutor()

        with pytest.raises(ValueError, match="Unknown pattern"):
            await executor.execute_pattern("invalid_pattern", [], [])

    def test_pattern_recommendation_scatter_gather(self):
        """Test pattern recommendation - scatter-gather case"""
        executor = PatternExecutor()

        # Same task to multiple agents
        task_slices = [TaskSlice("question", "What do you think?")]
        agents = ["agent-1", "agent-2", "agent-3"]

        recommendation = executor.recommend_pattern(task_slices, agents)
        assert recommendation == OrchestrationPattern.SCATTER_GATHER

    def test_pattern_recommendation_mapreduce(self):
        """Test pattern recommendation - mapreduce case"""
        executor = PatternExecutor()

        # Many tasks, few agents
        task_slices = [TaskSlice(f"task-{i}", f"Process {i}") for i in range(10)]
        agents = ["agent-1", "agent-2"]

        recommendation = executor.recommend_pattern(task_slices, agents)
        assert recommendation == OrchestrationPattern.MAPREDUCE

    def test_pattern_recommendation_pipeline(self):
        """Test pattern recommendation - pipeline case"""
        executor = PatternExecutor()

        # Tasks with dependencies
        task_slices = [
            TaskSlice("task-1", "First step", dependencies=[]),
            TaskSlice("task-2", "Second step", dependencies=["task-1"]),
            TaskSlice("task-3", "Third step", dependencies=["task-2"]),
        ]
        agents = ["agent-1", "agent-2", "agent-3"]

        recommendation = executor.recommend_pattern(task_slices, agents)
        assert recommendation == OrchestrationPattern.PIPELINE

    def test_pattern_recommendation_saga(self):
        """Test pattern recommendation - saga case"""
        executor = PatternExecutor()

        # Transaction-like tasks
        task_slices = [
            TaskSlice("step-1", "Begin transaction"),
            TaskSlice("step-2", "Execute transaction operations"),
            TaskSlice("step-3", "Commit transaction"),
        ]
        agents = ["agent-1", "agent-2", "agent-3"]

        recommendation = executor.recommend_pattern(task_slices, agents)
        assert recommendation == OrchestrationPattern.SAGA

    def test_pattern_recommendation_fork_join(self):
        """Test pattern recommendation - fork-join default case"""
        executor = PatternExecutor()

        # Equal tasks and agents, no dependencies
        task_slices = [
            TaskSlice("task-1", "Independent task 1"),
            TaskSlice("task-2", "Independent task 2"),
        ]
        agents = ["agent-1", "agent-2"]

        recommendation = executor.recommend_pattern(task_slices, agents)
        assert recommendation == OrchestrationPattern.FORK_JOIN

    @pytest.mark.asyncio
    async def test_auto_pattern_execution(self):
        """Test automatic pattern selection and execution"""
        executor = PatternExecutor()

        task_slices = [TaskSlice("auto-task", "Automatically orchestrated task")]
        agents = ["agent-1", "agent-2"]

        result = await executor.execute_auto_pattern(task_slices, agents)

        assert result.success
        assert result.pattern in [p for p in OrchestrationPattern]

    def test_performance_metrics_retrieval(self):
        """Test performance metrics retrieval"""
        executor = PatternExecutor()

        performance = executor.get_pattern_performance()

        assert len(performance) == 5
        for pattern_name in [
            "mapreduce",
            "pipeline",
            "fork_join",
            "scatter_gather",
            "saga",
        ]:
            assert pattern_name in performance
            assert "success_rate" in performance[pattern_name]
            assert "average_execution_time" in performance[pattern_name]

    def test_execution_history_management(self):
        """Test execution history management"""
        executor = PatternExecutor()

        # Initially empty
        history = executor.get_execution_history()
        assert len(history) == 0

        # Add mock history entry
        executor.execution_history.append(
            {
                "pattern": OrchestrationPattern.MAPREDUCE,
                "timestamp": datetime.now(),
                "task_count": 5,
                "agent_count": 2,
            }
        )

        history = executor.get_execution_history()
        assert len(history) == 1

        # Test history limiting
        history_limited = executor.get_execution_history(limit=0)
        assert len(history_limited) == 0

        # Clear history
        executor.clear_history()
        assert len(executor.execution_history) == 0


class TestBaseOrchestrationPattern:
    """Test base orchestration pattern functionality"""

    class MockPattern(BaseOrchestrationPattern):
        """Mock pattern for testing base functionality"""

        def __init__(self):
            super().__init__(OrchestrationPattern.FORK_JOIN)

        async def execute(self, task_slices, agents):
            return PatternResult(
                pattern=self.pattern_type,
                success=True,
                execution_time=1.0,
                agents_used=len(agents),
            )

    def test_base_pattern_initialization(self):
        """Test base pattern initialization"""
        pattern = self.MockPattern()

        assert pattern.pattern_type == OrchestrationPattern.FORK_JOIN
        assert pattern.execution_stats["total_executions"] == 0
        assert pattern.execution_stats["successful_executions"] == 0

    def test_stats_update(self):
        """Test statistics updating"""
        pattern = self.MockPattern()

        result = PatternResult(
            pattern=OrchestrationPattern.FORK_JOIN,
            success=True,
            execution_time=2.5,
            agents_used=3,
        )

        pattern.update_stats(result)

        stats = pattern.execution_stats
        assert stats["total_executions"] == 1
        assert stats["successful_executions"] == 1
        assert stats["average_execution_time"] == 2.5
        assert stats["agents_utilization"] == [3]

    def test_performance_metrics(self):
        """Test performance metrics calculation"""
        pattern = self.MockPattern()

        # Add some execution results
        results = [
            PatternResult(
                OrchestrationPattern.FORK_JOIN, True, execution_time=1.0, agents_used=2
            ),
            PatternResult(
                OrchestrationPattern.FORK_JOIN, True, execution_time=2.0, agents_used=3
            ),
            PatternResult(
                OrchestrationPattern.FORK_JOIN, False, execution_time=0.5, agents_used=1
            ),
        ]

        for result in results:
            pattern.update_stats(result)

        metrics = pattern.get_performance_metrics()

        assert metrics["pattern"] == "fork_join"
        assert metrics["success_rate"] == 200 / 3  # 2 successful out of 3
        assert metrics["total_executions"] == 3
        assert metrics["average_execution_time"] == 1.167  # (1.0 + 2.0 + 0.5) / 3
        assert metrics["average_agents_used"] == 2.0  # (2 + 3 + 1) / 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
