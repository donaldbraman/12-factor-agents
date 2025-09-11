"""
Simplified Orchestration - Only Fork-Join Pattern
Streamlined for 12-factor compliance and performance
"""

import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TaskSlice:
    """A slice of work for parallel execution"""

    slice_id: str
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ForkJoinResult:
    """Result from Fork-Join execution"""

    success: bool
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    execution_time: float = 0.0
    completed_tasks: int = 0


class SimplifiedForkJoinOrchestrator:
    """
    Simplified Fork-Join orchestration - the only pattern we actually use.

    Fork: Split work into parallel tasks
    Join: Wait for all tasks to complete and aggregate results
    """

    def __init__(self, max_parallelism: int = 5):
        self.max_parallelism = max_parallelism
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def execute(
        self,
        tasks: List[TaskSlice],
        executor_func: callable,
        timeout_per_task: float = 30.0,
    ) -> ForkJoinResult:
        """
        Execute tasks in parallel with Fork-Join pattern

        Args:
            tasks: List of tasks to execute in parallel
            executor_func: Function to execute each task slice
            timeout_per_task: Timeout for each individual task

        Returns:
            ForkJoinResult with aggregated results
        """
        start_time = datetime.now()

        # Fork: Create semaphore to limit parallelism
        semaphore = asyncio.Semaphore(self.max_parallelism)

        async def execute_with_semaphore(task_slice: TaskSlice):
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        executor_func(task_slice), timeout=timeout_per_task
                    )
                    return task_slice.slice_id, result, None
                except Exception as e:
                    self.logger.error(f"Task {task_slice.slice_id} failed: {e}")
                    return task_slice.slice_id, None, str(e)

        # Fork: Launch all tasks
        task_futures = [execute_with_semaphore(task) for task in tasks]

        # Join: Wait for all tasks to complete
        completed_tasks = await asyncio.gather(*task_futures, return_exceptions=True)

        # Aggregate results
        results = {}
        errors = {}
        successful_count = 0

        for task_result in completed_tasks:
            if isinstance(task_result, Exception):
                errors[f"unknown_{len(errors)}"] = str(task_result)
            else:
                task_id, result, error = task_result
                if error:
                    errors[task_id] = error
                else:
                    results[task_id] = result
                    successful_count += 1

        execution_time = (datetime.now() - start_time).total_seconds()

        return ForkJoinResult(
            success=len(errors) == 0,
            results=results,
            errors=errors,
            execution_time=execution_time,
            completed_tasks=successful_count,
        )


# Simple factory function
def create_orchestrator() -> SimplifiedForkJoinOrchestrator:
    """Create the simplified orchestrator"""
    return SimplifiedForkJoinOrchestrator()
