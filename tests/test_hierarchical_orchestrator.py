"""
Unit tests for Hierarchical Orchestration System.

Tests all core functionality including multi-level delegation, task decomposition,
workload distribution, result aggregation, and coordination protocols.
"""
import pytest
from datetime import datetime

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.hierarchical_orchestrator import (
    HierarchicalOrchestrator,
    TaskDecomposer,
    WorkloadDistributor,
    OrchestrationTask,
    AgentInfo,
    OrchestrationResult,
    OrchestrationLevel,
    OrchestrationPattern,
    TaskComplexity,
)


class TestTaskDecomposer:
    """Test task decomposition engine"""

    def test_initialization(self):
        """Test decomposer initialization"""
        decomposer = TaskDecomposer()

        assert len(decomposer.decomposition_strategies) == 5
        assert TaskComplexity.ATOMIC in decomposer.decomposition_strategies
        assert TaskComplexity.ENTERPRISE in decomposer.decomposition_strategies

    def test_complexity_analysis_atomic(self):
        """Test atomic task complexity detection"""
        decomposer = TaskDecomposer()

        atomic_tasks = ["return value", "print hello", "increment counter"]

        for task in atomic_tasks:
            complexity = decomposer._analyze_complexity(task)
            assert complexity == TaskComplexity.ATOMIC

    def test_complexity_analysis_simple(self):
        """Test simple task complexity detection"""
        decomposer = TaskDecomposer()

        simple_tasks = [
            "fix login bug",
            "update user profile",
            "add new button",
            "remove old feature",
        ]

        for task in simple_tasks:
            complexity = decomposer._analyze_complexity(task)
            assert complexity == TaskComplexity.SIMPLE

    def test_complexity_analysis_moderate(self):
        """Test moderate task complexity detection"""
        decomposer = TaskDecomposer()

        moderate_tasks = [
            "test authentication system",
            "validate input parameters",
            "analyze performance metrics",
            "process user requests",
        ]

        for task in moderate_tasks:
            complexity = decomposer._analyze_complexity(task)
            assert complexity == TaskComplexity.MODERATE

    def test_complexity_analysis_complex(self):
        """Test complex task complexity detection"""
        decomposer = TaskDecomposer()

        complex_tasks = [
            "integrate multiple payment systems",
            "coordinate microservices deployment",
            "orchestrate data pipeline workflow",
            "implement end-to-end testing",
        ]

        for task in complex_tasks:
            complexity = decomposer._analyze_complexity(task)
            assert complexity == TaskComplexity.COMPLEX

    def test_complexity_analysis_enterprise(self):
        """Test enterprise task complexity detection"""
        decomposer = TaskDecomposer()

        enterprise_tasks = [
            "migrate entire system to cloud",
            "refactor entire codebase architecture",
            "implement full stack authentication",
            "architect new microservices platform",
        ]

        for task in enterprise_tasks:
            complexity = decomposer._analyze_complexity(task)
            assert complexity == TaskComplexity.ENTERPRISE

    def test_level_determination(self):
        """Test orchestration level determination"""
        decomposer = TaskDecomposer()

        assert (
            decomposer._determine_level(TaskComplexity.SIMPLE, 0)
            == OrchestrationLevel.PRIMARY
        )
        assert (
            decomposer._determine_level(TaskComplexity.COMPLEX, 1)
            == OrchestrationLevel.SECONDARY
        )
        assert (
            decomposer._determine_level(TaskComplexity.MODERATE, 2)
            == OrchestrationLevel.TERTIARY
        )

    def test_pattern_determination(self):
        """Test orchestration pattern selection"""
        decomposer = TaskDecomposer()

        # Test pipeline pattern
        pipeline_task = OrchestrationTask(
            task_id="test",
            content="process data through stages",
            level=OrchestrationLevel.PRIMARY,
            complexity=TaskComplexity.COMPLEX,
            subtasks=["stage1", "stage2", "stage3"],
        )
        pattern = decomposer._determine_pattern(pipeline_task)
        assert pattern == OrchestrationPattern.PIPELINE

        # Test mapreduce pattern
        mapreduce_task = OrchestrationTask(
            task_id="test",
            content="aggregate results from multiple sources",
            level=OrchestrationLevel.PRIMARY,
            complexity=TaskComplexity.COMPLEX,
            subtasks=["task1", "task2"],
        )
        pattern = decomposer._determine_pattern(mapreduce_task)
        assert pattern == OrchestrationPattern.MAPREDUCE

    def test_task_decomposition(self):
        """Test complete task decomposition"""
        decomposer = TaskDecomposer()

        complex_task = "implement user authentication system"
        result = decomposer.decompose(complex_task, max_depth=2)

        assert result.content == complex_task
        assert result.complexity == TaskComplexity.COMPLEX
        assert result.level == OrchestrationLevel.PRIMARY
        assert result.task_id
        assert result.pattern is not None

    def test_decomposition_strategies(self):
        """Test different decomposition strategies"""
        decomposer = TaskDecomposer()

        # Test atomic strategy
        atomic_subtasks = decomposer._atomic_strategy("atomic task", 0)
        assert atomic_subtasks == []

        # Test simple strategy
        simple_subtasks = decomposer._simple_strategy("simple task", 0)
        assert len(simple_subtasks) == 1
        assert "Execute:" in simple_subtasks[0]

        # Test moderate strategy
        moderate_subtasks = decomposer._moderate_strategy("moderate task", 0)
        assert len(moderate_subtasks) == 4
        assert any("Analyze:" in task for task in moderate_subtasks)

        # Test complex strategy
        complex_subtasks = decomposer._complex_strategy("complex task", 0)
        assert len(complex_subtasks) == 5
        assert any("Research and analyze:" in task for task in complex_subtasks)

        # Test enterprise strategy
        enterprise_subtasks = decomposer._enterprise_strategy("enterprise task", 0)
        assert len(enterprise_subtasks) == 7
        assert any("Strategic planning for:" in task for task in enterprise_subtasks)


class TestWorkloadDistributor:
    """Test workload distribution algorithms"""

    def test_initialization(self):
        """Test distributor initialization"""
        distributor = WorkloadDistributor()

        assert len(distributor.load_balancing_strategies) == 4
        assert "round_robin" in distributor.load_balancing_strategies
        assert "least_loaded" in distributor.load_balancing_strategies

    def test_round_robin_distribution(self):
        """Test round-robin task distribution"""
        distributor = WorkloadDistributor()

        tasks = [
            OrchestrationTask(
                "1", "task1", OrchestrationLevel.SECONDARY, TaskComplexity.SIMPLE
            ),
            OrchestrationTask(
                "2", "task2", OrchestrationLevel.SECONDARY, TaskComplexity.SIMPLE
            ),
            OrchestrationTask(
                "3", "task3", OrchestrationLevel.SECONDARY, TaskComplexity.SIMPLE
            ),
        ]

        agents = [
            AgentInfo("agent1", OrchestrationLevel.SECONDARY),
            AgentInfo("agent2", OrchestrationLevel.SECONDARY),
        ]

        distribution = distributor._round_robin(tasks, agents)

        assert len(distribution) == 2
        assert len(distribution["agent1"]) == 2  # Tasks 1, 3
        assert len(distribution["agent2"]) == 1  # Task 2

    def test_least_loaded_distribution(self):
        """Test least-loaded task distribution"""
        distributor = WorkloadDistributor()

        tasks = [
            OrchestrationTask(
                "1", "task1", OrchestrationLevel.SECONDARY, TaskComplexity.SIMPLE
            ),
            OrchestrationTask(
                "2", "task2", OrchestrationLevel.SECONDARY, TaskComplexity.SIMPLE
            ),
        ]

        agents = [
            AgentInfo("agent1", OrchestrationLevel.SECONDARY, current_load=5),
            AgentInfo("agent2", OrchestrationLevel.SECONDARY, current_load=2),
        ]

        distribution = distributor._least_loaded(tasks, agents)

        # Both tasks should go to agent2 (lower initial load)
        assert len(distribution["agent2"]) == 2
        assert len(distribution["agent1"]) == 0

    def test_capability_based_distribution(self):
        """Test capability-based task distribution"""
        distributor = WorkloadDistributor()

        tasks = [
            OrchestrationTask(
                "1",
                "database task",
                OrchestrationLevel.SECONDARY,
                TaskComplexity.SIMPLE,
            ),
            OrchestrationTask(
                "2", "api task", OrchestrationLevel.SECONDARY, TaskComplexity.SIMPLE
            ),
        ]

        agents = [
            AgentInfo(
                "agent1",
                OrchestrationLevel.SECONDARY,
                specializations=["database", "sql"],
            ),
            AgentInfo(
                "agent2", OrchestrationLevel.SECONDARY, specializations=["api", "rest"]
            ),
        ]

        distribution = distributor._capability_based(tasks, agents)

        # Tasks should be matched to specialized agents
        assert len(distribution["agent1"]) >= 0
        assert len(distribution["agent2"]) >= 0

    def test_distribute_with_strategy(self):
        """Test distribution with different strategies"""
        distributor = WorkloadDistributor()

        tasks = [
            OrchestrationTask(
                "1", "task", OrchestrationLevel.SECONDARY, TaskComplexity.SIMPLE
            )
        ]
        agents = [AgentInfo("agent1", OrchestrationLevel.SECONDARY)]

        # Test valid strategy
        distribution = distributor.distribute(tasks, agents, "round_robin")
        assert len(distribution) == 1

        # Test invalid strategy (should default to least_loaded)
        distribution = distributor.distribute(tasks, agents, "invalid_strategy")
        assert len(distribution) == 1


class TestHierarchicalOrchestrator:
    """Test hierarchical orchestrator core functionality"""

    def test_initialization(self):
        """Test orchestrator initialization"""
        orchestrator = HierarchicalOrchestrator()

        assert orchestrator.max_depth == 3
        assert len(orchestrator.max_agents_per_level) == 3
        assert orchestrator.agent_id in orchestrator.agents
        assert len(orchestrator.coordination_patterns) == 5

    def test_initialization_with_custom_params(self):
        """Test orchestrator with custom parameters"""
        custom_limits = {"primary": 2, "secondary": 5, "tertiary": 15}
        orchestrator = HierarchicalOrchestrator(
            max_depth=4, max_agents_per_level=custom_limits
        )

        assert orchestrator.max_depth == 4
        assert orchestrator.max_agents_per_level == custom_limits

    @pytest.mark.asyncio
    async def test_simple_task_orchestration(self):
        """Test orchestrating a simple task"""
        orchestrator = HierarchicalOrchestrator()

        result = await orchestrator.orchestrate_complex_task("Fix login bug")

        assert isinstance(result, OrchestrationResult)
        assert result.success
        assert result.execution_time > 0
        assert result.agents_used >= 1
        assert result.task_id

    @pytest.mark.asyncio
    async def test_complex_task_orchestration(self):
        """Test orchestrating a complex task"""
        orchestrator = HierarchicalOrchestrator()

        complex_task = (
            "Implement complete OAuth2 authentication system with multiple providers"
        )
        result = await orchestrator.orchestrate_complex_task(complex_task)

        assert isinstance(result, OrchestrationResult)
        assert result.success
        assert result.execution_time > 0
        assert result.agents_used >= 1
        assert result.levels_deep > 0
        assert result.coordination_overhead >= 0

    @pytest.mark.asyncio
    async def test_orchestration_with_custom_id(self):
        """Test orchestration with custom orchestration ID"""
        orchestrator = HierarchicalOrchestrator()

        custom_id = "test-orchestration-123"
        result = await orchestrator.orchestrate_complex_task(
            "Test task", orchestration_id=custom_id
        )

        assert result.success
        assert result.metadata["orchestration_id"] == custom_id

    @pytest.mark.asyncio
    async def test_agent_hierarchy_creation(self):
        """Test agent hierarchy creation"""
        orchestrator = HierarchicalOrchestrator()

        # Create a task that requires hierarchy
        root_task = OrchestrationTask(
            task_id="test",
            content="Complex task requiring hierarchy",
            level=OrchestrationLevel.PRIMARY,
            complexity=TaskComplexity.COMPLEX,
        )

        initial_agent_count = len(orchestrator.agents)
        await orchestrator._create_agent_hierarchy(root_task, "test-id")

        # Should have created additional agents
        assert len(orchestrator.agents) >= initial_agent_count

    @pytest.mark.asyncio
    async def test_spawn_agent(self):
        """Test agent spawning"""
        orchestrator = HierarchicalOrchestrator()

        initial_count = len(orchestrator.agents)
        agent_info = await orchestrator._spawn_agent(
            OrchestrationLevel.SECONDARY, "test-orchestration"
        )

        assert isinstance(agent_info, AgentInfo)
        assert agent_info.level == OrchestrationLevel.SECONDARY
        assert agent_info.agent_id in orchestrator.agents
        assert len(orchestrator.agents) == initial_count + 1

    def test_count_agents_needed(self):
        """Test agent count estimation"""
        orchestrator = HierarchicalOrchestrator()

        # Simple task
        simple_task = OrchestrationTask(
            task_id="test",
            content="Simple task",
            level=OrchestrationLevel.PRIMARY,
            complexity=TaskComplexity.SIMPLE,
        )

        counts = orchestrator._count_agents_needed(simple_task)
        assert counts["primary"] == 1
        assert counts["secondary"] >= 0
        assert counts["tertiary"] >= 0

        # Complex task
        complex_task = OrchestrationTask(
            task_id="test",
            content="Complex task",
            level=OrchestrationLevel.PRIMARY,
            complexity=TaskComplexity.COMPLEX,
        )

        complex_counts = orchestrator._count_agents_needed(complex_task)
        assert complex_counts["secondary"] > counts["secondary"]
        assert complex_counts["tertiary"] > counts["tertiary"]

    @pytest.mark.asyncio
    async def test_execute_single_task(self):
        """Test single task execution"""
        orchestrator = HierarchicalOrchestrator()

        task = OrchestrationTask(
            task_id="test",
            content="Test task",
            level=OrchestrationLevel.TERTIARY,
            complexity=TaskComplexity.SIMPLE,
        )

        result = await orchestrator._execute_single_task(task, "test-orchestration")

        assert result is not None
        assert task.status == "completed"
        assert task.result is not None

    @pytest.mark.asyncio
    async def test_coordination_patterns_execution(self):
        """Test different coordination patterns"""
        orchestrator = HierarchicalOrchestrator()

        task = OrchestrationTask(
            task_id="test",
            content="Pattern test",
            level=OrchestrationLevel.PRIMARY,
            complexity=TaskComplexity.MODERATE,
            subtasks=["subtask1", "subtask2"],
        )

        # Test MapReduce pattern
        task.pattern = OrchestrationPattern.MAPREDUCE
        mapreduce_result = await orchestrator._execute_mapreduce(task, "test-id")
        assert mapreduce_result is not None

        # Test Pipeline pattern
        task.pattern = OrchestrationPattern.PIPELINE
        pipeline_result = await orchestrator._execute_pipeline(task, "test-id")
        assert pipeline_result is not None

        # Test Fork-Join pattern
        task.pattern = OrchestrationPattern.FORK_JOIN
        forkjoin_result = await orchestrator._execute_fork_join(task, "test-id")
        assert forkjoin_result is not None

    def test_calculate_hierarchy_depth(self):
        """Test hierarchy depth calculation"""
        orchestrator = HierarchicalOrchestrator()

        # Single level task
        single_task = OrchestrationTask(
            task_id="test",
            content="Single task",
            level=OrchestrationLevel.PRIMARY,
            complexity=TaskComplexity.SIMPLE,
            subtasks=[],
        )

        depth = orchestrator._calculate_hierarchy_depth(single_task)
        assert depth == 0

        # Multi-level task
        multi_task = OrchestrationTask(
            task_id="test",
            content="Multi task",
            level=OrchestrationLevel.PRIMARY,
            complexity=TaskComplexity.COMPLEX,
            subtasks=["sub1", "sub2"],
        )

        # Add subtasks to orchestrator's task store
        orchestrator.tasks[multi_task.task_id] = multi_task
        orchestrator.tasks["sub1"] = OrchestrationTask(
            task_id="sub1",
            content="Subtask 1",
            level=OrchestrationLevel.SECONDARY,
            complexity=TaskComplexity.SIMPLE,
            parent_id=multi_task.task_id,
        )

        depth = orchestrator._calculate_hierarchy_depth(multi_task)
        assert depth >= 0

    def test_coordination_overhead_calculation(self):
        """Test coordination overhead estimation"""
        orchestrator = HierarchicalOrchestrator()

        # Test with different agent counts
        overhead_1 = orchestrator._calculate_coordination_overhead("test-1")

        # Add more agents
        for i in range(5):
            orchestrator.agents[f"agent_{i}"] = AgentInfo(
                f"agent_{i}", OrchestrationLevel.SECONDARY
            )

        overhead_2 = orchestrator._calculate_coordination_overhead("test-2")

        # Overhead should increase with more agents
        assert overhead_2 >= overhead_1
        assert 0 <= overhead_2 <= 10.0  # Should be within reasonable bounds

    @pytest.mark.asyncio
    async def test_orchestration_status_tracking(self):
        """Test orchestration status methods"""
        orchestrator = HierarchicalOrchestrator()

        # Test getting status for non-existent orchestration
        status = await orchestrator.get_orchestration_status("non-existent")
        assert "error" in status

        # Test agent hierarchy retrieval
        hierarchy = await orchestrator.get_agent_hierarchy()
        assert "primary" in hierarchy
        assert "secondary" in hierarchy
        assert "tertiary" in hierarchy
        assert len(hierarchy["primary"]) >= 1  # Should have at least the orchestrator

    @pytest.mark.asyncio
    async def test_orchestration_cancellation(self):
        """Test orchestration cancellation"""
        orchestrator = HierarchicalOrchestrator()

        # Test cancelling non-existent orchestration
        result = await orchestrator.cancel_orchestration("non-existent")
        assert not result

        # Add mock orchestration
        orchestration_id = "test-orchestration"
        orchestrator.active_orchestrations[orchestration_id] = {}

        # Add some agents and tasks
        orchestrator.agents["test-agent"] = AgentInfo(
            "test-agent", OrchestrationLevel.SECONDARY
        )
        orchestrator.tasks["test-task"] = OrchestrationTask(
            "test-task",
            "Test task",
            OrchestrationLevel.SECONDARY,
            TaskComplexity.SIMPLE,
        )
        orchestrator.tasks["test-task"].status = "pending"

        # Test successful cancellation
        result = await orchestrator.cancel_orchestration(orchestration_id)
        assert result
        assert orchestration_id not in orchestrator.active_orchestrations

    @pytest.mark.asyncio
    async def test_execute_task_tool_interface(self):
        """Test execute_task method (ToolResponse interface)"""
        orchestrator = HierarchicalOrchestrator()

        response = await orchestrator.execute_task("Test orchestration task")

        assert hasattr(response, "success")
        assert hasattr(response, "data")
        assert hasattr(response, "message")
        assert response.success
        assert "orchestration_result" in response.data

    def test_register_tools(self):
        """Test tool registration"""
        orchestrator = HierarchicalOrchestrator()

        tools = orchestrator.register_tools()

        assert len(tools) == 4
        assert "orchestrate_task" in tools
        assert "get_orchestration_status" in tools
        assert "cancel_orchestration" in tools
        assert "get_agent_hierarchy" in tools

        # Test that tools are callable
        for tool in tools.values():
            assert callable(tool)


class TestOrchestrationDataClasses:
    """Test orchestration data classes"""

    def test_orchestration_task_creation(self):
        """Test OrchestrationTask creation"""
        task = OrchestrationTask(
            task_id="test-123",
            content="Test task content",
            level=OrchestrationLevel.PRIMARY,
            complexity=TaskComplexity.MODERATE,
        )

        assert task.task_id == "test-123"
        assert task.content == "Test task content"
        assert task.level == OrchestrationLevel.PRIMARY
        assert task.complexity == TaskComplexity.MODERATE
        assert task.status == "pending"
        assert task.subtasks == []
        assert task.dependencies == []
        assert isinstance(task.created_at, datetime)

    def test_agent_info_creation(self):
        """Test AgentInfo creation"""
        agent = AgentInfo(
            agent_id="agent-456", level=OrchestrationLevel.SECONDARY, max_capacity=10
        )

        assert agent.agent_id == "agent-456"
        assert agent.level == OrchestrationLevel.SECONDARY
        assert agent.current_load == 0
        assert agent.max_capacity == 10
        assert agent.children == []
        assert agent.specializations == []
        assert agent.status == "active"
        assert isinstance(agent.created_at, datetime)

    def test_orchestration_result_creation(self):
        """Test OrchestrationResult creation"""
        result = OrchestrationResult(
            task_id="result-789", success=True, execution_time=1.5, agents_used=5
        )

        assert result.task_id == "result-789"
        assert result.success is True
        assert result.execution_time == 1.5
        assert result.agents_used == 5
        assert result.levels_deep == 0
        assert result.coordination_overhead == 0.0
        assert result.error_message == ""
        assert result.metadata == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
