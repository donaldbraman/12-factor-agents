"""
Hierarchical Agent Orchestration System - Claude Code Pattern Implementation

Implements multi-level task decomposition and coordination for handling 10x more
complex tasks through structured Primary → Secondary → Tertiary delegation.

Implements 12-Factor Agent methodology:
- Factor 8: Own Your Control Flow (hierarchical decision making)
- Factor 10: Small, Focused Agents (specialized responsibility levels)
- Factor 6: Launch/Pause/Resume APIs (orchestrated lifecycle management)
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from .base import BaseAgent, ToolResponse
from .background_executor import BackgroundAgentExecutor

logger = logging.getLogger(__name__)


class OrchestrationLevel(Enum):
    """Levels in the orchestration hierarchy"""

    PRIMARY = "primary"  # Strategic planning and validation
    SECONDARY = "secondary"  # Tactical execution and coordination
    TERTIARY = "tertiary"  # Specialized tasks and atomic operations


class OrchestrationPattern(Enum):
    """Patterns for agent coordination"""

    MAPREDUCE = "mapreduce"  # Distribute work, aggregate results
    PIPELINE = "pipeline"  # Sequential processing chain
    FORK_JOIN = "fork_join"  # Parallel execution with synchronization
    SCATTER_GATHER = "scatter_gather"  # Broadcast task, collect responses
    SAGA = "saga"  # Transaction-like coordination


class TaskComplexity(Enum):
    """Task complexity levels for decomposition decisions"""

    ATOMIC = "atomic"  # Cannot be decomposed further
    SIMPLE = "simple"  # Can be handled by single agent
    MODERATE = "moderate"  # Requires coordination
    COMPLEX = "complex"  # Requires hierarchical decomposition
    ENTERPRISE = "enterprise"  # Requires full orchestration


@dataclass
class OrchestrationTask:
    """Task in the orchestration hierarchy"""

    task_id: str
    content: str
    level: OrchestrationLevel
    complexity: TaskComplexity
    parent_id: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    pattern: Optional[OrchestrationPattern] = None
    assigned_agent: Optional[str] = None
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentInfo:
    """Information about agents in the hierarchy"""

    agent_id: str
    level: OrchestrationLevel
    current_load: int = 0
    max_capacity: int = 5
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class OrchestrationResult:
    """Result from orchestration execution"""

    task_id: str
    success: bool
    result: Any = None
    execution_time: float = 0.0
    agents_used: int = 0
    levels_deep: int = 0
    coordination_overhead: float = 0.0
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskDecomposer:
    """Intelligent task decomposition engine"""

    def __init__(self):
        self.decomposition_strategies = {
            TaskComplexity.ATOMIC: self._atomic_strategy,
            TaskComplexity.SIMPLE: self._simple_strategy,
            TaskComplexity.MODERATE: self._moderate_strategy,
            TaskComplexity.COMPLEX: self._complex_strategy,
            TaskComplexity.ENTERPRISE: self._enterprise_strategy,
        }

    def decompose(
        self, task, max_depth: int = 3, current_depth: int = 0
    ) -> OrchestrationTask:
        """Decompose task into hierarchical structure"""

        # Handle both string and dict inputs
        if isinstance(task, dict):
            task_content = task.get("description", "")
        else:
            task_content = task

        # Analyze task complexity
        complexity = self._analyze_complexity(task)

        # Create task object
        orchestration_task = OrchestrationTask(
            task_id=str(uuid.uuid4()),
            content=task_content,
            level=self._determine_level(complexity, current_depth),
            complexity=complexity,
        )

        # Apply decomposition strategy
        if current_depth < max_depth and complexity != TaskComplexity.ATOMIC:
            strategy = self.decomposition_strategies.get(
                complexity, self._simple_strategy
            )
            subtasks = strategy(task, current_depth)

            # Create subtask objects
            for subtask_content in subtasks:
                subtask = self.decompose(subtask_content, max_depth, current_depth + 1)
                subtask.parent_id = orchestration_task.task_id
                orchestration_task.subtasks.append(subtask.task_id)

        # Determine coordination pattern
        orchestration_task.pattern = self._determine_pattern(orchestration_task)

        return orchestration_task

    def _analyze_complexity(self, task: str) -> TaskComplexity:
        """Analyze task complexity using heuristics"""

        # Handle both string and dict inputs
        if isinstance(task, dict):
            # Extract description from dict format
            task_text = task.get("description", "")
        else:
            # Use string directly
            task_text = task
        
        # Simple keyword-based analysis (can be enhanced with ML)
        task_lower = task_text.lower()

        # Enterprise indicators
        enterprise_keywords = [
            "migrate",
            "refactor entire",
            "implement system",
            "architecture",
            "full stack",
            "end-to-end",
        ]
        if any(keyword in task_lower for keyword in enterprise_keywords):
            return TaskComplexity.ENTERPRISE

        # Complex indicators
        complex_keywords = [
            "multiple",
            "integrate",
            "coordinate",
            "orchestrate",
            "workflow",
            "pipeline",
            "deployment",
        ]
        if any(keyword in task_lower for keyword in complex_keywords):
            return TaskComplexity.COMPLEX

        # Moderate indicators
        moderate_keywords = ["test", "validate", "analyze", "process", "generate"]
        if any(keyword in task_lower for keyword in moderate_keywords):
            return TaskComplexity.MODERATE

        # Simple indicators
        simple_keywords = ["fix", "update", "add", "remove", "modify"]
        if any(keyword in task_lower for keyword in simple_keywords):
            return TaskComplexity.SIMPLE

        return TaskComplexity.ATOMIC

    def _determine_level(
        self, complexity: TaskComplexity, depth: int
    ) -> OrchestrationLevel:
        """Determine orchestration level based on complexity and depth"""
        if depth == 0:
            return OrchestrationLevel.PRIMARY
        elif depth == 1:
            return OrchestrationLevel.SECONDARY
        else:
            return OrchestrationLevel.TERTIARY

    def _determine_pattern(self, task: OrchestrationTask) -> OrchestrationPattern:
        """Determine best orchestration pattern for task"""

        if not task.subtasks:
            return OrchestrationPattern.FORK_JOIN  # Default for leaf tasks

        subtask_count = len(task.subtasks)

        # Pattern selection heuristics
        if "process" in task.content.lower() and subtask_count > 1:
            return OrchestrationPattern.PIPELINE
        elif "aggregate" in task.content.lower() or "collect" in task.content.lower():
            return OrchestrationPattern.MAPREDUCE
        elif subtask_count > 5:
            return OrchestrationPattern.SCATTER_GATHER
        elif "transaction" in task.content.lower():
            return OrchestrationPattern.SAGA
        else:
            return OrchestrationPattern.FORK_JOIN

    def _atomic_strategy(self, task: str, depth: int) -> List[str]:
        """No decomposition for atomic tasks"""
        return []

    def _simple_strategy(self, task: str, depth: int) -> List[str]:
        """Simple task decomposition"""
        return [f"Execute: {task}"]

    def _moderate_strategy(self, task: str, depth: int) -> List[str]:
        """Moderate complexity decomposition"""
        return [
            f"Analyze: {task}",
            f"Plan: {task}",
            f"Execute: {task}",
            f"Validate: {task}",
        ]

    def _complex_strategy(self, task: str, depth: int) -> List[str]:
        """Complex task decomposition"""
        return [
            f"Research and analyze: {task}",
            f"Design solution for: {task}",
            f"Implement core components: {task}",
            f"Integrate and test: {task}",
            f"Document and deploy: {task}",
        ]

    def _enterprise_strategy(self, task: str, depth: int) -> List[str]:
        """Enterprise-level decomposition"""
        return [
            f"Strategic planning for: {task}",
            f"Architecture design: {task}",
            f"Component development: {task}",
            f"System integration: {task}",
            f"Testing and validation: {task}",
            f"Deployment and monitoring: {task}",
            f"Documentation and training: {task}",
        ]


class WorkloadDistributor:
    """Intelligent workload distribution across agents"""

    def __init__(self):
        self.load_balancing_strategies = {
            "round_robin": self._round_robin,
            "least_loaded": self._least_loaded,
            "capability_based": self._capability_based,
            "priority_based": self._priority_based,
        }

    def distribute(
        self,
        tasks: List[OrchestrationTask],
        agents: List[AgentInfo],
        strategy: str = "least_loaded",
    ) -> Dict[str, List[str]]:
        """Distribute tasks to agents using specified strategy"""

        if strategy not in self.load_balancing_strategies:
            strategy = "least_loaded"

        distributor = self.load_balancing_strategies[strategy]
        return distributor(tasks, agents)

    def _round_robin(
        self, tasks: List[OrchestrationTask], agents: List[AgentInfo]
    ) -> Dict[str, List[str]]:
        """Round-robin task distribution"""
        distribution = {agent.agent_id: [] for agent in agents}

        for i, task in enumerate(tasks):
            agent = agents[i % len(agents)]
            distribution[agent.agent_id].append(task.task_id)

        return distribution

    def _least_loaded(
        self, tasks: List[OrchestrationTask], agents: List[AgentInfo]
    ) -> Dict[str, List[str]]:
        """Distribute to least loaded agents"""
        distribution = {agent.agent_id: [] for agent in agents}

        for task in tasks:
            # Find agent with lowest current load
            least_loaded = min(agents, key=lambda a: a.current_load)
            distribution[least_loaded.agent_id].append(task.task_id)
            least_loaded.current_load += 1

        return distribution

    def _capability_based(
        self, tasks: List[OrchestrationTask], agents: List[AgentInfo]
    ) -> Dict[str, List[str]]:
        """Distribute based on agent capabilities"""
        distribution = {agent.agent_id: [] for agent in agents}

        for task in tasks:
            # Simple capability matching (can be enhanced)
            best_agent = self._find_best_capability_match(task, agents)
            distribution[best_agent.agent_id].append(task.task_id)
            best_agent.current_load += 1

        return distribution

    def _priority_based(
        self, tasks: List[OrchestrationTask], agents: List[AgentInfo]
    ) -> Dict[str, List[str]]:
        """Distribute based on task priority"""
        distribution = {agent.agent_id: [] for agent in agents}

        # Sort tasks by complexity (proxy for priority)
        complexity_order = [
            TaskComplexity.ENTERPRISE,
            TaskComplexity.COMPLEX,
            TaskComplexity.MODERATE,
            TaskComplexity.SIMPLE,
            TaskComplexity.ATOMIC,
        ]

        sorted_tasks = sorted(tasks, key=lambda t: complexity_order.index(t.complexity))

        for task in sorted_tasks:
            # Assign to least loaded capable agent
            capable_agents = [a for a in agents if a.current_load < a.max_capacity]
            if capable_agents:
                best_agent = min(capable_agents, key=lambda a: a.current_load)
                distribution[best_agent.agent_id].append(task.task_id)
                best_agent.current_load += 1

        return distribution

    def _find_best_capability_match(
        self, task: OrchestrationTask, agents: List[AgentInfo]
    ) -> AgentInfo:
        """Find agent with best capability match for task"""

        # Simple keyword matching (can be enhanced with semantic similarity)
        task_keywords = set(task.content.lower().split())

        best_agent = agents[0]
        best_score = 0

        for agent in agents:
            if agent.current_load >= agent.max_capacity:
                continue

            # Calculate capability match score
            agent_keywords = set()
            for spec in agent.specializations:
                agent_keywords.update(spec.lower().split())

            match_score = len(task_keywords.intersection(agent_keywords))

            if match_score > best_score:
                best_score = match_score
                best_agent = agent

        return best_agent


class HierarchicalOrchestrator(BaseAgent):
    """
    Hierarchical Agent Orchestration System

    Provides multi-level task decomposition and coordination for complex projects
    through Primary → Secondary → Tertiary agent delegation with intelligent
    workload distribution and result aggregation.
    """

    def __init__(self, max_depth: int = 3, max_agents_per_level: Dict[str, int] = None):
        """
        Initialize Hierarchical Orchestrator

        Args:
            max_depth: Maximum hierarchy depth
            max_agents_per_level: Agent limits per level
        """
        super().__init__()

        self.max_depth = max_depth
        self.max_agents_per_level = max_agents_per_level or {
            "primary": 1,
            "secondary": 10,
            "tertiary": 30,
        }

        # Orchestration components
        self.task_decomposer = TaskDecomposer()
        self.workload_distributor = WorkloadDistributor()
        self.background_executor = BackgroundAgentExecutor()

        # State tracking
        self.tasks: Dict[str, OrchestrationTask] = {}
        self.agents: Dict[str, AgentInfo] = {}
        self.active_orchestrations: Dict[str, Dict[str, Any]] = {}

        # Register self as primary agent
        self.agents[self.agent_id] = AgentInfo(
            agent_id=self.agent_id, level=OrchestrationLevel.PRIMARY, max_capacity=5
        )

        # Coordination patterns
        self.coordination_patterns = {
            OrchestrationPattern.MAPREDUCE: self._execute_mapreduce,
            OrchestrationPattern.PIPELINE: self._execute_pipeline,
            OrchestrationPattern.FORK_JOIN: self._execute_fork_join,
            OrchestrationPattern.SCATTER_GATHER: self._execute_scatter_gather,
            OrchestrationPattern.SAGA: self._execute_saga,
        }

    async def orchestrate_complex_task(
        self, task: str, orchestration_id: str = None
    ) -> OrchestrationResult:
        """
        Orchestrate a complex task through hierarchical decomposition

        Args:
            task: Task description to orchestrate
            orchestration_id: Optional orchestration identifier

        Returns:
            OrchestrationResult with execution details
        """
        start_time = asyncio.get_event_loop().time()

        if not orchestration_id:
            orchestration_id = str(uuid.uuid4())

        try:
            # Phase 1: Decompose task into hierarchy
            logger.info(f"🏗️ Decomposing task: {task}")
            root_task = self.task_decomposer.decompose(task, self.max_depth)

            # Store decomposed tasks
            await self._store_task_hierarchy(root_task)

            # Phase 2: Create agent hierarchy
            logger.info(
                f"👥 Creating agent hierarchy for orchestration: {orchestration_id}"
            )
            await self._create_agent_hierarchy(root_task, orchestration_id)

            # Phase 3: Execute orchestration
            logger.info(f"🚀 Executing hierarchical orchestration: {orchestration_id}")
            result = await self._execute_orchestration(root_task, orchestration_id)

            # Phase 4: Aggregate and validate results
            logger.info(f"📊 Aggregating results for orchestration: {orchestration_id}")
            final_result = await self._aggregate_results(root_task, orchestration_id)

            execution_time = asyncio.get_event_loop().time() - start_time

            return OrchestrationResult(
                task_id=root_task.task_id,
                success=True,
                result=final_result,
                execution_time=execution_time,
                agents_used=len(
                    [a for a in self.agents.values() if a.status == "active"]
                ),
                levels_deep=self._calculate_hierarchy_depth(root_task),
                coordination_overhead=self._calculate_coordination_overhead(
                    orchestration_id
                ),
                metadata={
                    "orchestration_id": orchestration_id,
                    "root_task_id": root_task.task_id,
                    "decomposed_tasks": len(self.tasks),
                    "patterns_used": self._get_patterns_used(root_task),
                },
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"❌ Orchestration failed: {e}")

            return OrchestrationResult(
                task_id=orchestration_id,
                success=False,
                execution_time=execution_time,
                error_message=str(e),
            )

    async def _store_task_hierarchy(self, task: OrchestrationTask):
        """Recursively store task hierarchy"""
        self.tasks[task.task_id] = task

        # Store subtasks recursively (if they exist as objects)
        for subtask_id in task.subtasks:
            if subtask_id in self.tasks:
                continue
            # In a real implementation, you'd retrieve subtask objects
            # For now, we'll create placeholder tasks

    async def _create_agent_hierarchy(
        self, root_task: OrchestrationTask, orchestration_id: str
    ):
        """Create agent hierarchy based on task decomposition"""

        # Count agents needed at each level
        agents_needed = self._count_agents_needed(root_task)

        # Spawn secondary agents
        secondary_count = min(
            agents_needed.get("secondary", 0), self.max_agents_per_level["secondary"]
        )

        for i in range(secondary_count):
            agent_info = await self._spawn_agent(
                OrchestrationLevel.SECONDARY, orchestration_id
            )
            agent_info.parent_id = self.agent_id
            self.agents[self.agent_id].children.append(agent_info.agent_id)

        # Spawn tertiary agents
        tertiary_count = min(
            agents_needed.get("tertiary", 0), self.max_agents_per_level["tertiary"]
        )

        for i in range(tertiary_count):
            # Assign to random secondary parent
            secondary_agents = [
                a
                for a in self.agents.values()
                if a.level == OrchestrationLevel.SECONDARY
            ]
            if secondary_agents:
                parent = min(secondary_agents, key=lambda a: len(a.children))
                agent_info = await self._spawn_agent(
                    OrchestrationLevel.TERTIARY, orchestration_id
                )
                agent_info.parent_id = parent.agent_id
                parent.children.append(agent_info.agent_id)

    async def _spawn_agent(
        self, level: OrchestrationLevel, orchestration_id: str
    ) -> AgentInfo:
        """Spawn agent at specified level"""

        agent_id = str(uuid.uuid4())

        # In a real implementation, you'd spawn actual agent instances
        # For now, we'll create agent info objects
        agent_info = AgentInfo(
            agent_id=agent_id,
            level=level,
            max_capacity=3 if level == OrchestrationLevel.TERTIARY else 5,
        )

        self.agents[agent_id] = agent_info
        logger.info(f"🤖 Spawned {level.value} agent: {agent_id}")

        return agent_info

    def _count_agents_needed(self, task: OrchestrationTask) -> Dict[str, int]:
        """Count agents needed at each level"""
        counts = {"primary": 1, "secondary": 0, "tertiary": 0}

        def count_recursive(t: OrchestrationTask):
            if t.level == OrchestrationLevel.SECONDARY:
                counts["secondary"] += 1
            elif t.level == OrchestrationLevel.TERTIARY:
                counts["tertiary"] += 1

            # In a real implementation, you'd recursively count subtasks
            # For now, we'll use heuristics based on complexity
            if t.complexity == TaskComplexity.COMPLEX:
                counts["secondary"] += 2
                counts["tertiary"] += 4
            elif t.complexity == TaskComplexity.ENTERPRISE:
                counts["secondary"] += 5
                counts["tertiary"] += 10

        count_recursive(task)
        return counts

    async def _execute_orchestration(
        self, root_task: OrchestrationTask, orchestration_id: str
    ) -> Any:
        """Execute orchestration using appropriate pattern"""

        pattern = root_task.pattern or OrchestrationPattern.FORK_JOIN
        executor = self.coordination_patterns.get(pattern, self._execute_fork_join)

        logger.info(
            f"🎼 Executing {pattern.value} pattern for task: {root_task.task_id}"
        )

        return await executor(root_task, orchestration_id)

    async def _execute_mapreduce(
        self, task: OrchestrationTask, orchestration_id: str
    ) -> Any:
        """Execute MapReduce coordination pattern"""

        # Map phase: distribute subtasks
        logger.info(f"🗺️ MapReduce Map phase: {task.task_id}")

        subtask_results = []
        for subtask_id in task.subtasks:
            # In real implementation, execute subtask with appropriate agent
            subtask = self.tasks.get(subtask_id)
            if subtask:
                result = await self._execute_single_task(subtask, orchestration_id)
                subtask_results.append(result)

        # Reduce phase: aggregate results
        logger.info(f"📊 MapReduce Reduce phase: {task.task_id}")
        aggregated_result = await self._reduce_results(subtask_results, task)

        return aggregated_result

    async def _execute_pipeline(
        self, task: OrchestrationTask, orchestration_id: str
    ) -> Any:
        """Execute Pipeline coordination pattern"""

        logger.info(f"🔄 Pipeline execution: {task.task_id}")

        result = task.content  # Initial input

        # Sequential processing through subtasks
        for subtask_id in task.subtasks:
            subtask = self.tasks.get(subtask_id)
            if subtask:
                # Pass previous result as input to next stage
                result = await self._execute_single_task(
                    subtask, orchestration_id, result
                )

        return result

    async def _execute_fork_join(
        self, task: OrchestrationTask, orchestration_id: str
    ) -> Any:
        """Execute Fork-Join coordination pattern"""

        logger.info(f"🍴 Fork-Join execution: {task.task_id}")

        # Fork phase: parallel execution
        subtask_coroutines = []
        for subtask_id in task.subtasks:
            subtask = self.tasks.get(subtask_id)
            if subtask:
                coroutine = self._execute_single_task(subtask, orchestration_id)
                subtask_coroutines.append(coroutine)

        # Execute in parallel
        if subtask_coroutines:
            results = await asyncio.gather(*subtask_coroutines, return_exceptions=True)
        else:
            results = []

        # Join phase: synchronize and merge
        return await self._join_results(results, task)

    async def _execute_scatter_gather(
        self, task: OrchestrationTask, orchestration_id: str
    ) -> Any:
        """Execute Scatter-Gather coordination pattern"""

        logger.info(f"📡 Scatter-Gather execution: {task.task_id}")

        # Scatter: broadcast task to multiple agents
        scattered_results = []

        for subtask_id in task.subtasks:
            subtask = self.tasks.get(subtask_id)
            if subtask:
                result = await self._execute_single_task(subtask, orchestration_id)
                scattered_results.append(result)

        # Gather: collect and merge responses
        return await self._gather_results(scattered_results, task)

    async def _execute_saga(
        self, task: OrchestrationTask, orchestration_id: str
    ) -> Any:
        """Execute Saga coordination pattern"""

        logger.info(f"📜 Saga execution: {task.task_id}")

        completed_steps = []
        compensation_actions = []

        try:
            # Execute each step in the saga
            for subtask_id in task.subtasks:
                subtask = self.tasks.get(subtask_id)
                if subtask:
                    result = await self._execute_single_task(subtask, orchestration_id)
                    completed_steps.append((subtask_id, result))

                    # Register compensation action for this step
                    compensation_actions.append(
                        self._create_compensation_action(subtask, result)
                    )

            return [result for _, result in completed_steps]

        except Exception as e:
            # Execute compensation actions in reverse order
            logger.warning(f"⚠️ Saga failed, executing compensation: {e}")

            for compensation in reversed(compensation_actions):
                try:
                    await compensation()
                except Exception as comp_error:
                    logger.error(f"❌ Compensation failed: {comp_error}")

            raise e

    async def _execute_single_task(
        self, task: OrchestrationTask, orchestration_id: str, input_data: Any = None
    ) -> Any:
        """Execute a single task"""

        logger.debug(f"⚡ Executing task: {task.task_id}")

        # Simulate task execution (replace with actual agent execution)
        await asyncio.sleep(0.1)  # Simulate work

        # Update task status
        task.status = "completed"
        task.result = f"Result for: {task.content}"

        return task.result

    async def _reduce_results(self, results: List[Any], task: OrchestrationTask) -> Any:
        """Reduce/aggregate results from map phase"""

        # Simple aggregation (enhance based on task type)
        if not results:
            return None

        if all(isinstance(r, (int, float)) for r in results):
            return sum(results)
        elif all(isinstance(r, str) for r in results):
            return "\n".join(results)
        else:
            return results

    async def _join_results(self, results: List[Any], task: OrchestrationTask) -> Any:
        """Join results from fork-join execution"""

        # Filter out exceptions
        successful_results = [r for r in results if not isinstance(r, Exception)]

        if not successful_results:
            return None

        return {
            "task_id": task.task_id,
            "results": successful_results,
            "total_count": len(results),
            "success_count": len(successful_results),
        }

    async def _gather_results(self, results: List[Any], task: OrchestrationTask) -> Any:
        """Gather results from scatter-gather execution"""

        return {
            "task_id": task.task_id,
            "gathered_results": results,
            "pattern": "scatter_gather",
        }

    def _create_compensation_action(
        self, task: OrchestrationTask, result: Any
    ) -> Callable:
        """Create compensation action for saga pattern"""

        async def compensate():
            logger.info(f"🔄 Compensating task: {task.task_id}")
            # Implement task-specific compensation logic
            pass

        return compensate

    async def _aggregate_results(
        self, root_task: OrchestrationTask, orchestration_id: str
    ) -> Any:
        """Aggregate all results from orchestration"""

        return {
            "orchestration_id": orchestration_id,
            "root_task": root_task.task_id,
            "final_result": root_task.result,
            "completion_time": datetime.now(),
            "total_tasks": len(self.tasks),
            "successful_tasks": len(
                [t for t in self.tasks.values() if t.status == "completed"]
            ),
        }

    def _calculate_hierarchy_depth(self, task: OrchestrationTask) -> int:
        """Calculate maximum depth of task hierarchy"""

        # Simple depth calculation based on agent levels created
        max_depth = 0

        for agent in self.agents.values():
            if agent.level == OrchestrationLevel.PRIMARY:
                max_depth = max(max_depth, 0)
            elif agent.level == OrchestrationLevel.SECONDARY:
                max_depth = max(max_depth, 1)
            elif agent.level == OrchestrationLevel.TERTIARY:
                max_depth = max(max_depth, 2)

        return max_depth

    def _calculate_coordination_overhead(self, orchestration_id: str) -> float:
        """Calculate coordination overhead percentage"""

        # Simple estimation (enhance with actual timing data)
        total_agents = len(self.agents)
        total_tasks = len(self.tasks)

        # Estimate coordination overhead based on communication complexity
        if total_agents <= 1:
            return 0.0
        elif total_agents <= 10:
            return min(5.0, total_tasks * 0.1)
        else:
            return min(10.0, total_tasks * 0.2)

    def _get_patterns_used(self, task: OrchestrationTask) -> List[str]:
        """Get list of coordination patterns used in orchestration"""

        patterns = set()

        def collect_patterns(t: OrchestrationTask):
            if t.pattern:
                patterns.add(t.pattern.value)

            for subtask_id in t.subtasks:
                subtask = self.tasks.get(subtask_id)
                if subtask:
                    collect_patterns(subtask)

        collect_patterns(task)
        return list(patterns)

    def register_tools(self) -> Dict[str, Callable]:
        """Register orchestration tools"""
        return {
            "orchestrate_task": self.orchestrate_complex_task,
            "get_orchestration_status": self.get_orchestration_status,
            "cancel_orchestration": self.cancel_orchestration,
            "get_agent_hierarchy": self.get_agent_hierarchy,
        }

    async def get_orchestration_status(self, orchestration_id: str) -> Dict[str, Any]:
        """Get status of active orchestration"""

        if orchestration_id not in self.active_orchestrations:
            return {"error": "Orchestration not found"}

        return {
            "orchestration_id": orchestration_id,
            "active_agents": len(
                [a for a in self.agents.values() if a.status == "active"]
            ),
            "completed_tasks": len(
                [t for t in self.tasks.values() if t.status == "completed"]
            ),
            "pending_tasks": len(
                [t for t in self.tasks.values() if t.status == "pending"]
            ),
            "total_tasks": len(self.tasks),
        }

    async def cancel_orchestration(self, orchestration_id: str) -> bool:
        """Cancel active orchestration"""

        if orchestration_id in self.active_orchestrations:
            # Mark all agents as inactive
            for agent in self.agents.values():
                agent.status = "inactive"

            # Mark pending tasks as cancelled
            for task in self.tasks.values():
                if task.status == "pending":
                    task.status = "cancelled"

            del self.active_orchestrations[orchestration_id]
            return True

        return False

    async def get_agent_hierarchy(self) -> Dict[str, Any]:
        """Get current agent hierarchy structure"""

        hierarchy = {"primary": [], "secondary": [], "tertiary": []}

        for agent in self.agents.values():
            hierarchy[agent.level.value].append(
                {
                    "agent_id": agent.agent_id,
                    "current_load": agent.current_load,
                    "max_capacity": agent.max_capacity,
                    "status": agent.status,
                    "children": agent.children,
                    "parent_id": agent.parent_id,
                }
            )

        return hierarchy

    async def execute_task(self, task: str) -> ToolResponse:
        """Execute task using hierarchical orchestration"""

        try:
            result = await self.orchestrate_complex_task(task)

            return ToolResponse(
                success=result.success,
                data={
                    "orchestration_result": result,
                    "execution_time": result.execution_time,
                    "agents_used": result.agents_used,
                    "levels_deep": result.levels_deep,
                },
                message=f"Orchestration completed with {result.agents_used} agents",
            )

        except Exception as e:
            return ToolResponse(
                success=False, error=str(e), message=f"Orchestration failed: {e}"
            )
