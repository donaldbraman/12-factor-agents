"""
Orchestration Patterns for Hierarchical Agent Coordination

Implements the five core coordination patterns for complex task orchestration:
- MapReduce: Distribute work, aggregate results  
- Pipeline: Sequential processing chain
- Fork-Join: Parallel execution with synchronization
- Scatter-Gather: Broadcast task, collect responses
- Saga: Transaction-like coordination with compensation

Each pattern provides different coordination semantics optimized for specific
workflow characteristics and performance requirements.
"""
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class OrchestrationPattern(Enum):
    """Available orchestration patterns"""

    MAPREDUCE = "mapreduce"
    PIPELINE = "pipeline"
    FORK_JOIN = "fork_join"
    SCATTER_GATHER = "scatter_gather"
    SAGA = "saga"


@dataclass
class TaskSlice:
    """A slice of work for pattern execution"""

    slice_id: str
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: float = 1.0


@dataclass
class PatternResult:
    """Result from pattern execution"""

    pattern: OrchestrationPattern
    success: bool
    result: Any = None
    execution_time: float = 0.0
    slices_processed: int = 0
    agents_used: int = 0
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseOrchestrationPattern(ABC):
    """Base class for orchestration patterns"""

    def __init__(self, pattern_type: OrchestrationPattern):
        self.pattern_type = pattern_type
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "average_execution_time": 0.0,
            "agents_utilization": [],
        }

    @abstractmethod
    async def execute(
        self, task_slices: List[TaskSlice], agents: List[Any]
    ) -> PatternResult:
        """Execute pattern with given task slices and agents"""
        pass

    def update_stats(self, result: PatternResult):
        """Update execution statistics"""
        self.execution_stats["total_executions"] += 1
        if result.success:
            self.execution_stats["successful_executions"] += 1

        # Update average execution time
        total = self.execution_stats["total_executions"]
        current_avg = self.execution_stats["average_execution_time"]
        new_avg = ((current_avg * (total - 1)) + result.execution_time) / total
        self.execution_stats["average_execution_time"] = new_avg

        # Track agent utilization
        self.execution_stats["agents_utilization"].append(result.agents_used)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get pattern performance metrics"""
        stats = self.execution_stats
        return {
            "pattern": self.pattern_type.value,
            "success_rate": (
                stats["successful_executions"] / max(stats["total_executions"], 1)
            )
            * 100,
            "average_execution_time": stats["average_execution_time"],
            "average_agents_used": (
                sum(stats["agents_utilization"])
                / max(len(stats["agents_utilization"]), 1)
            ),
            "total_executions": stats["total_executions"],
        }


class MapReducePattern(BaseOrchestrationPattern):
    """
    MapReduce Orchestration Pattern

    Distributes work across multiple agents (Map) and aggregates
    results (Reduce). Ideal for parallelizable computational tasks.
    """

    def __init__(self):
        super().__init__(OrchestrationPattern.MAPREDUCE)
        self.custom_reducers: Dict[str, Callable] = {}

    async def execute(
        self, task_slices: List[TaskSlice], agents: List[Any]
    ) -> PatternResult:
        """Execute MapReduce pattern"""

        start_time = asyncio.get_event_loop().time()

        try:
            logger.info(
                f"🗺️ Starting MapReduce with {len(task_slices)} slices, {len(agents)} agents"
            )

            # Map Phase: Distribute work
            map_results = await self._map_phase(task_slices, agents)

            # Reduce Phase: Aggregate results
            final_result = await self._reduce_phase(map_results, task_slices)

            execution_time = asyncio.get_event_loop().time() - start_time

            result = PatternResult(
                pattern=OrchestrationPattern.MAPREDUCE,
                success=True,
                result=final_result,
                execution_time=execution_time,
                slices_processed=len(task_slices),
                agents_used=len(agents),
                metadata={
                    "map_results_count": len(map_results),
                    "reduction_type": self._determine_reduction_type(map_results),
                },
            )

            self.update_stats(result)
            return result

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time

            result = PatternResult(
                pattern=OrchestrationPattern.MAPREDUCE,
                success=False,
                execution_time=execution_time,
                error_message=str(e),
            )

            self.update_stats(result)
            return result

    async def _map_phase(
        self, task_slices: List[TaskSlice], agents: List[Any]
    ) -> List[Any]:
        """Execute map phase - distribute work"""

        # Distribute slices across agents
        agent_assignments = self._distribute_slices(task_slices, agents)

        # Execute map tasks in parallel
        map_coroutines = []
        for agent, slices in agent_assignments.items():
            coroutine = self._execute_map_task(agent, slices)
            map_coroutines.append(coroutine)

        # Wait for all map tasks to complete
        map_results = await asyncio.gather(*map_coroutines, return_exceptions=True)

        # Filter out exceptions and flatten results
        successful_results = []
        for result in map_results:
            if not isinstance(result, Exception):
                if isinstance(result, list):
                    successful_results.extend(result)
                else:
                    successful_results.append(result)

        return successful_results

    async def _reduce_phase(
        self, map_results: List[Any], task_slices: List[TaskSlice]
    ) -> Any:
        """Execute reduce phase - aggregate results"""

        if not map_results:
            return None

        # Determine reduction strategy
        reduction_type = self._determine_reduction_type(map_results)

        if reduction_type == "numeric":
            return sum(r for r in map_results if isinstance(r, (int, float)))
        elif reduction_type == "string":
            return "\n".join(str(r) for r in map_results if r is not None)
        elif reduction_type == "list":
            # Flatten nested lists
            flattened = []
            for r in map_results:
                if isinstance(r, list):
                    flattened.extend(r)
                else:
                    flattened.append(r)
            return flattened
        elif reduction_type == "dict":
            # Merge dictionaries
            merged = {}
            for r in map_results:
                if isinstance(r, dict):
                    merged.update(r)
            return merged
        else:
            # Default: return all results
            return {
                "results": map_results,
                "count": len(map_results),
                "pattern": "mapreduce",
            }

    def _distribute_slices(
        self, slices: List[TaskSlice], agents: List[Any]
    ) -> Dict[Any, List[TaskSlice]]:
        """Distribute task slices across agents"""

        if not agents:
            return {}

        distribution = {agent: [] for agent in agents}

        # Simple round-robin distribution
        for i, slice_obj in enumerate(slices):
            agent = agents[i % len(agents)]
            distribution[agent].append(slice_obj)

        return distribution

    async def _execute_map_task(self, agent: Any, slices: List[TaskSlice]) -> List[Any]:
        """Execute map task on single agent"""

        results = []
        for slice_obj in slices:
            # Simulate agent execution (replace with actual agent call)
            await asyncio.sleep(0.01)  # Simulate work
            result = f"Processed: {slice_obj.content}"
            results.append(result)

        return results

    def _determine_reduction_type(self, results: List[Any]) -> str:
        """Determine appropriate reduction strategy"""

        if not results:
            return "empty"

        first_type = type(results[0])

        if all(isinstance(r, (int, float)) for r in results):
            return "numeric"
        elif all(isinstance(r, str) for r in results):
            return "string"
        elif all(isinstance(r, list) for r in results):
            return "list"
        elif all(isinstance(r, dict) for r in results):
            return "dict"
        else:
            return "mixed"

    def register_custom_reducer(self, name: str, reducer: Callable):
        """Register custom reduction function"""
        self.custom_reducers[name] = reducer


class PipelinePattern(BaseOrchestrationPattern):
    """
    Pipeline Orchestration Pattern

    Sequential processing where output of one agent becomes input
    of the next. Ideal for data transformation workflows.
    """

    def __init__(self):
        super().__init__(OrchestrationPattern.PIPELINE)
        self.stage_processors: Dict[str, Callable] = {}

    async def execute(
        self, task_slices: List[TaskSlice], agents: List[Any]
    ) -> PatternResult:
        """Execute Pipeline pattern"""

        start_time = asyncio.get_event_loop().time()

        try:
            logger.info(f"🔄 Starting Pipeline with {len(agents)} stages")

            # Initialize pipeline with first task slice
            current_data = task_slices[0].content if task_slices else None

            # Process through each pipeline stage
            for i, agent in enumerate(agents):
                stage_name = f"stage_{i}"
                logger.debug(f"Processing stage {i+1}/{len(agents)}: {stage_name}")

                current_data = await self._execute_pipeline_stage(
                    agent, current_data, stage_name
                )

            execution_time = asyncio.get_event_loop().time() - start_time

            result = PatternResult(
                pattern=OrchestrationPattern.PIPELINE,
                success=True,
                result=current_data,
                execution_time=execution_time,
                slices_processed=len(task_slices),
                agents_used=len(agents),
                metadata={
                    "stages_completed": len(agents),
                    "pipeline_depth": len(agents),
                },
            )

            self.update_stats(result)
            return result

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time

            result = PatternResult(
                pattern=OrchestrationPattern.PIPELINE,
                success=False,
                execution_time=execution_time,
                error_message=str(e),
            )

            self.update_stats(result)
            return result

    async def _execute_pipeline_stage(
        self, agent: Any, input_data: Any, stage_name: str
    ) -> Any:
        """Execute single pipeline stage"""

        # Check for custom stage processor
        if stage_name in self.stage_processors:
            return await self.stage_processors[stage_name](input_data)

        # Default stage processing (simulate agent execution)
        await asyncio.sleep(0.05)  # Simulate work

        # Transform data based on stage
        if isinstance(input_data, str):
            return f"{input_data} -> {stage_name}"
        elif isinstance(input_data, dict):
            return {**input_data, stage_name: f"processed_by_{stage_name}"}
        elif isinstance(input_data, list):
            return input_data + [f"processed_by_{stage_name}"]
        else:
            return {"input": input_data, "processor": stage_name}

    def register_stage_processor(self, stage_name: str, processor: Callable):
        """Register custom processor for specific stage"""
        self.stage_processors[stage_name] = processor


class ForkJoinPattern(BaseOrchestrationPattern):
    """
    Fork-Join Orchestration Pattern

    Parallel execution with synchronization point. All agents work
    in parallel, then results are joined. Ideal for independent
    parallel processing.
    """

    def __init__(self):
        super().__init__(OrchestrationPattern.FORK_JOIN)
        self.join_strategies: Dict[str, Callable] = {}

    async def execute(
        self, task_slices: List[TaskSlice], agents: List[Any]
    ) -> PatternResult:
        """Execute Fork-Join pattern"""

        start_time = asyncio.get_event_loop().time()

        try:
            logger.info(f"🍴 Starting Fork-Join with {len(agents)} parallel agents")

            # Fork Phase: Launch parallel executions
            fork_coroutines = []
            for i, agent in enumerate(agents):
                # Assign task slice to agent (or divide work)
                slice_for_agent = (
                    task_slices[i % len(task_slices)] if task_slices else None
                )
                coroutine = self._execute_fork_task(agent, slice_for_agent, i)
                fork_coroutines.append(coroutine)

            # Execute all forks in parallel
            fork_results = await asyncio.gather(
                *fork_coroutines, return_exceptions=True
            )

            # Join Phase: Synchronize and merge results
            joined_result = await self._join_results(fork_results, task_slices)

            execution_time = asyncio.get_event_loop().time() - start_time

            # Count successful executions
            successful_count = len(
                [r for r in fork_results if not isinstance(r, Exception)]
            )

            result = PatternResult(
                pattern=OrchestrationPattern.FORK_JOIN,
                success=successful_count > 0,
                result=joined_result,
                execution_time=execution_time,
                slices_processed=len(task_slices),
                agents_used=len(agents),
                metadata={
                    "successful_forks": successful_count,
                    "failed_forks": len(agents) - successful_count,
                    "join_strategy": "default",
                },
            )

            self.update_stats(result)
            return result

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time

            result = PatternResult(
                pattern=OrchestrationPattern.FORK_JOIN,
                success=False,
                execution_time=execution_time,
                error_message=str(e),
            )

            self.update_stats(result)
            return result

    async def _execute_fork_task(
        self, agent: Any, task_slice: Optional[TaskSlice], fork_id: int
    ) -> Any:
        """Execute task on single fork"""

        # Simulate agent execution
        await asyncio.sleep(0.1)  # Simulate work

        content = task_slice.content if task_slice else f"fork_{fork_id}"

        return {
            "fork_id": fork_id,
            "result": f"Processed by fork {fork_id}: {content}",
            "agent": str(agent),
            "timestamp": datetime.now(),
        }

    async def _join_results(
        self, fork_results: List[Any], task_slices: List[TaskSlice]
    ) -> Any:
        """Join results from all forks"""

        # Filter successful results
        successful_results = [r for r in fork_results if not isinstance(r, Exception)]

        if not successful_results:
            return {"error": "All forks failed"}

        # Default join strategy
        return {
            "pattern": "fork_join",
            "total_forks": len(fork_results),
            "successful_forks": len(successful_results),
            "results": successful_results,
            "join_timestamp": datetime.now(),
        }

    def register_join_strategy(self, name: str, strategy: Callable):
        """Register custom join strategy"""
        self.join_strategies[name] = strategy


class ScatterGatherPattern(BaseOrchestrationPattern):
    """
    Scatter-Gather Orchestration Pattern

    Broadcast same task to multiple agents and collect responses.
    Ideal for consensus building or collecting multiple perspectives.
    """

    def __init__(self):
        super().__init__(OrchestrationPattern.SCATTER_GATHER)
        self.gather_strategies: Dict[str, Callable] = {}

    async def execute(
        self, task_slices: List[TaskSlice], agents: List[Any]
    ) -> PatternResult:
        """Execute Scatter-Gather pattern"""

        start_time = asyncio.get_event_loop().time()

        try:
            logger.info(f"📡 Starting Scatter-Gather with {len(agents)} agents")

            # Use first task slice as the broadcast task
            broadcast_task = (
                task_slices[0]
                if task_slices
                else TaskSlice(slice_id="default", content="scatter_gather_task")
            )

            # Scatter Phase: Broadcast to all agents
            scatter_coroutines = []
            for i, agent in enumerate(agents):
                coroutine = self._execute_scatter_task(agent, broadcast_task, i)
                scatter_coroutines.append(coroutine)

            # Execute all scatters in parallel
            scatter_results = await asyncio.gather(
                *scatter_coroutines, return_exceptions=True
            )

            # Gather Phase: Collect and analyze responses
            gathered_result = await self._gather_responses(
                scatter_results, broadcast_task
            )

            execution_time = asyncio.get_event_loop().time() - start_time

            # Count successful responses
            successful_count = len(
                [r for r in scatter_results if not isinstance(r, Exception)]
            )

            result = PatternResult(
                pattern=OrchestrationPattern.SCATTER_GATHER,
                success=successful_count > 0,
                result=gathered_result,
                execution_time=execution_time,
                slices_processed=len(task_slices),
                agents_used=len(agents),
                metadata={
                    "responses_received": successful_count,
                    "broadcast_task": broadcast_task.slice_id,
                    "gather_strategy": "default",
                },
            )

            self.update_stats(result)
            return result

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time

            result = PatternResult(
                pattern=OrchestrationPattern.SCATTER_GATHER,
                success=False,
                execution_time=execution_time,
                error_message=str(e),
            )

            self.update_stats(result)
            return result

    async def _execute_scatter_task(
        self, agent: Any, task: TaskSlice, agent_id: int
    ) -> Any:
        """Execute scattered task on single agent"""

        # Simulate agent processing the broadcast task
        await asyncio.sleep(0.08)  # Simulate work

        return {
            "agent_id": agent_id,
            "response": f"Agent {agent_id} response to: {task.content}",
            "confidence": 0.5 + (agent_id % 5) * 0.1,  # Simulate varying confidence
            "processing_time": 0.08,
            "timestamp": datetime.now(),
        }

    async def _gather_responses(
        self, responses: List[Any], broadcast_task: TaskSlice
    ) -> Any:
        """Gather and analyze responses"""

        # Filter successful responses
        successful_responses = [r for r in responses if not isinstance(r, Exception)]

        if not successful_responses:
            return {"error": "No successful responses"}

        # Analyze responses for consensus or patterns
        analysis = self._analyze_responses(successful_responses)

        return {
            "pattern": "scatter_gather",
            "broadcast_task": broadcast_task.content,
            "total_agents": len(responses),
            "successful_responses": len(successful_responses),
            "responses": successful_responses,
            "analysis": analysis,
            "gather_timestamp": datetime.now(),
        }

    def _analyze_responses(self, responses: List[Any]) -> Dict[str, Any]:
        """Analyze gathered responses for patterns"""

        if not responses:
            return {}

        # Calculate average confidence if available
        confidences = [r.get("confidence", 0) for r in responses if isinstance(r, dict)]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Response similarity analysis (simple)
        response_texts = [
            r.get("response", "") for r in responses if isinstance(r, dict)
        ]

        return {
            "response_count": len(responses),
            "average_confidence": avg_confidence,
            "response_diversity": len(set(response_texts)),
            "consensus_strength": 1.0 - (len(set(response_texts)) / len(response_texts))
            if response_texts
            else 0,
        }

    def register_gather_strategy(self, name: str, strategy: Callable):
        """Register custom gather strategy"""
        self.gather_strategies[name] = strategy


class SagaPattern(BaseOrchestrationPattern):
    """
    Saga Orchestration Pattern

    Transaction-like coordination with compensation actions.
    Ensures consistency in long-running workflows by providing
    rollback capabilities.
    """

    def __init__(self):
        super().__init__(OrchestrationPattern.SAGA)
        self.compensation_handlers: Dict[str, Callable] = {}

    async def execute(
        self, task_slices: List[TaskSlice], agents: List[Any]
    ) -> PatternResult:
        """Execute Saga pattern"""

        start_time = asyncio.get_event_loop().time()

        try:
            logger.info(f"📜 Starting Saga with {len(task_slices)} transaction steps")

            completed_steps = []
            compensation_actions = []

            # Execute saga steps sequentially
            for i, (task_slice, agent) in enumerate(zip(task_slices, agents)):
                step_name = f"step_{i}"

                try:
                    # Execute saga step
                    step_result = await self._execute_saga_step(
                        agent, task_slice, step_name
                    )

                    completed_steps.append(
                        {
                            "step": step_name,
                            "result": step_result,
                            "agent": str(agent),
                            "timestamp": datetime.now(),
                        }
                    )

                    # Register compensation action
                    compensation_action = await self._create_compensation_action(
                        task_slice, step_result, step_name
                    )
                    compensation_actions.append(compensation_action)

                except Exception as step_error:
                    # Saga step failed - execute compensation
                    logger.warning(f"⚠️ Saga step {step_name} failed: {step_error}")
                    await self._execute_compensation(compensation_actions)
                    raise step_error

            execution_time = asyncio.get_event_loop().time() - start_time

            result = PatternResult(
                pattern=OrchestrationPattern.SAGA,
                success=True,
                result={
                    "completed_steps": completed_steps,
                    "total_steps": len(task_slices),
                    "saga_id": str(uuid.uuid4()),
                },
                execution_time=execution_time,
                slices_processed=len(task_slices),
                agents_used=len(agents),
                metadata={
                    "steps_completed": len(completed_steps),
                    "compensation_actions_registered": len(compensation_actions),
                },
            )

            self.update_stats(result)
            return result

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time

            result = PatternResult(
                pattern=OrchestrationPattern.SAGA,
                success=False,
                execution_time=execution_time,
                error_message=str(e),
            )

            self.update_stats(result)
            return result

    async def _execute_saga_step(
        self, agent: Any, task_slice: TaskSlice, step_name: str
    ) -> Any:
        """Execute single saga step"""

        # Simulate saga step execution
        await asyncio.sleep(0.1)  # Simulate work

        # Check for registered handler
        if step_name in self.compensation_handlers:
            handler = self.compensation_handlers[step_name]
            return await handler(task_slice.content)

        return f"Saga step {step_name} completed: {task_slice.content}"

    async def _create_compensation_action(
        self, task_slice: TaskSlice, step_result: Any, step_name: str
    ) -> Callable:
        """Create compensation action for saga step"""

        async def compensate():
            logger.info(f"🔄 Compensating step {step_name}")
            # Simulate compensation logic
            await asyncio.sleep(0.05)
            return f"Compensated: {step_name}"

        return compensate

    async def _execute_compensation(self, compensation_actions: List[Callable]):
        """Execute compensation actions in reverse order"""

        logger.info(f"⏪ Executing {len(compensation_actions)} compensation actions")

        # Execute in reverse order (LIFO)
        for compensation in reversed(compensation_actions):
            try:
                await compensation()
            except Exception as comp_error:
                logger.error(f"❌ Compensation failed: {comp_error}")
                # Continue with other compensations despite failures

    def register_compensation_handler(self, step_name: str, handler: Callable):
        """Register compensation handler for specific step"""
        self.compensation_handlers[step_name] = handler


class PatternExecutor:
    """
    Central executor for orchestration patterns

    Provides unified interface for executing different orchestration
    patterns with automatic pattern selection and performance monitoring.
    """

    def __init__(self):
        self.patterns = {
            OrchestrationPattern.MAPREDUCE: MapReducePattern(),
            OrchestrationPattern.PIPELINE: PipelinePattern(),
            OrchestrationPattern.FORK_JOIN: ForkJoinPattern(),
            OrchestrationPattern.SCATTER_GATHER: ScatterGatherPattern(),
            OrchestrationPattern.SAGA: SagaPattern(),
        }

        self.execution_history = []
        self.pattern_recommendations = {}

    async def execute_pattern(
        self,
        pattern: OrchestrationPattern,
        task_slices: List[TaskSlice],
        agents: List[Any],
    ) -> PatternResult:
        """Execute specified orchestration pattern"""

        if pattern not in self.patterns:
            raise ValueError(f"Unknown pattern: {pattern}")

        pattern_executor = self.patterns[pattern]
        result = await pattern_executor.execute(task_slices, agents)

        # Record execution for analysis
        self.execution_history.append(
            {
                "pattern": pattern,
                "result": result,
                "timestamp": datetime.now(),
                "task_count": len(task_slices),
                "agent_count": len(agents),
            }
        )

        return result

    def recommend_pattern(
        self, task_slices: List[TaskSlice], agents: List[Any]
    ) -> OrchestrationPattern:
        """Recommend best pattern based on task characteristics"""

        task_count = len(task_slices)
        agent_count = len(agents)

        # Simple heuristics for pattern recommendation
        if task_count == 1 and agent_count > 1:
            # Same task to multiple agents
            return OrchestrationPattern.SCATTER_GATHER

        elif task_count > agent_count and agent_count > 1:
            # Many tasks, few agents - distribute work
            return OrchestrationPattern.MAPREDUCE

        elif task_count == agent_count and task_count > 1:
            # Sequential dependency or independent parallel work
            # Check for dependencies in task slices
            has_dependencies = any(slice_obj.dependencies for slice_obj in task_slices)
            if has_dependencies:
                return OrchestrationPattern.PIPELINE
            else:
                return OrchestrationPattern.FORK_JOIN

        elif any(
            "transaction" in slice_obj.content.lower() for slice_obj in task_slices
        ):
            # Transaction-like requirements
            return OrchestrationPattern.SAGA

        else:
            # Default to fork-join for parallel execution
            return OrchestrationPattern.FORK_JOIN

    async def execute_auto_pattern(
        self, task_slices: List[TaskSlice], agents: List[Any]
    ) -> PatternResult:
        """Execute with automatically selected pattern"""

        recommended_pattern = self.recommend_pattern(task_slices, agents)
        logger.info(f"🤖 Auto-selected pattern: {recommended_pattern.value}")

        return await self.execute_pattern(recommended_pattern, task_slices, agents)

    def get_pattern_performance(self) -> Dict[str, Any]:
        """Get performance metrics for all patterns"""

        performance_data = {}

        for pattern_type, pattern_executor in self.patterns.items():
            performance_data[
                pattern_type.value
            ] = pattern_executor.get_performance_metrics()

        return performance_data

    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent execution history"""

        return self.execution_history[-limit:] if self.execution_history else []

    def clear_history(self):
        """Clear execution history"""
        self.execution_history.clear()
