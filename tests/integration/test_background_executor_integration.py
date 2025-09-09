"""
Integration tests for Background Agent Executor.

Tests the full workflow of agent spawning, execution, monitoring, and cleanup
in realistic scenarios with multiple concurrent agents.
"""

import asyncio
import tempfile
import pytest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.background_executor import (
    BackgroundAgentExecutor,
    ResourceLimits,
    BackgroundEnabledAgent,
)
from core.base import ToolResponse


class MockLongRunningAgent(BackgroundEnabledAgent):
    """Mock agent that simulates long-running work"""

    def __init__(self, duration: float = 1.0, should_fail: bool = False):
        super().__init__()
        self.duration = duration
        self.should_fail = should_fail
        self.work_done = []

    async def execute_task(self, task: str) -> ToolResponse:
        """Simulate work with configurable duration and failure"""
        await asyncio.sleep(0.1)  # Simulate some initial work

        if self.should_fail:
            raise ValueError(f"Simulated failure in task: {task}")

        # Simulate progress updates
        for i in range(3):
            await asyncio.sleep(self.duration / 3)
            self.work_done.append(f"step_{i}")

        return ToolResponse(
            success=True,
            data={"task": task, "work_done": self.work_done},
            message=f"Completed task: {task}",
        )


class MockDataProcessingAgent(BackgroundEnabledAgent):
    """Mock agent that processes data and demonstrates resource usage"""

    def __init__(self, data_size: int = 100):
        super().__init__()
        self.data_size = data_size
        self.processed_items = []

    async def execute_task(self, task: str) -> ToolResponse:
        """Process mock data items"""
        await asyncio.sleep(0.05)  # Initial setup

        # Simulate processing data items
        for i in range(self.data_size):
            await asyncio.sleep(0.01)  # Small processing delay
            self.processed_items.append(f"item_{i}")

            # Emit progress every 25 items
            if (i + 1) % 25 == 0:
                await self.event_bus.emit(
                    "progress",
                    {
                        "agent_id": self.agent_id,
                        "progress": (i + 1) / self.data_size * 100,
                        "items_processed": i + 1,
                    },
                )

        return ToolResponse(
            success=True,
            data={"processed_items": len(self.processed_items)},
            message=f"Processed {len(self.processed_items)} items",
        )


class MockChainedAgent(BackgroundEnabledAgent):
    """Mock agent that demonstrates agent-to-agent communication"""

    def __init__(self, chain_position: int, total_chain: int):
        super().__init__()
        self.chain_position = chain_position
        self.total_chain = total_chain
        self.chain_data = []

    async def execute_task(self, task: str) -> ToolResponse:
        """Execute task as part of a chain"""
        await asyncio.sleep(0.1)

        # Add our contribution to chain data
        self.chain_data.append(f"chain_step_{self.chain_position}")

        # If not the last in chain, spawn next agent
        if self.chain_position < self.total_chain - 1:
            next_task = f"chain_task_{self.chain_position + 1}"
            await self.event_bus.emit(
                "spawn_next",
                {
                    "next_position": self.chain_position + 1,
                    "task": next_task,
                    "accumulated_data": self.chain_data.copy(),
                },
            )

        return ToolResponse(
            success=True,
            data={"chain_position": self.chain_position, "chain_data": self.chain_data},
            message=f"Completed chain step {self.chain_position}",
        )


@pytest.fixture
def executor():
    """Create executor for testing"""
    import asyncio

    executor_instance = BackgroundAgentExecutor(max_parallel_agents=10)

    yield executor_instance

    # Cleanup in event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule cleanup
            asyncio.create_task(executor_instance.cleanup_all())
        else:
            loop.run_until_complete(executor_instance.cleanup_all())
    except Exception:
        # Fallback cleanup without await
        pass


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestBackgroundAgentExecutorIntegration:
    """Integration tests for Background Agent Executor"""

    @pytest.mark.asyncio
    async def test_concurrent_agent_execution(self, executor):
        """Test multiple agents running concurrently"""
        # Spawn 5 concurrent agents with different durations
        agent_ids = []
        tasks = [
            ("fast_task", 0.2),
            ("medium_task_1", 0.5),
            ("medium_task_2", 0.5),
            ("slow_task", 1.0),
            ("another_fast_task", 0.3),
        ]

        for task, duration in tasks:
            agent_id = await executor.spawn_background_agent(
                agent_class="MockLongRunningAgent",
                task=task,
                workflow_data={"duration": duration},
            )
            agent_ids.append(agent_id)

        # Verify all agents are active
        assert len(executor.active_agents) == 5

        # Wait for all agents to complete
        await asyncio.sleep(2.0)

        # Check results
        completed_count = 0
        for agent_id in agent_ids:
            info = executor.get_agent_info(agent_id)
            if info and info.status == "completed":
                completed_count += 1

        assert (
            completed_count == 5
        ), f"Expected 5 completed agents, got {completed_count}"

    @pytest.mark.asyncio
    async def test_resource_limits_enforcement(self, executor):
        """Test that resource limits are properly enforced"""
        # Create resource limits
        limits = ResourceLimits(
            max_memory_mb=512, max_cpu_percent=50.0, max_execution_time=30.0
        )

        # Spawn agent with resource limits
        agent = MockDataProcessingAgent(data_size=50)
        agent_id = await executor.spawn_background_agent(
            agent_class="MockDataProcessingAgent",
            task="process_data_with_limits",
            resource_limits=limits,
            agent_instance=agent,
        )

        # Monitor resource usage
        await asyncio.sleep(0.5)

        info = executor.get_agent_info(agent_id)
        assert info is not None
        assert info.resource_limits == limits

        # Wait for completion
        await asyncio.sleep(2.0)

        info = executor.get_agent_info(agent_id)
        assert info.status == "completed"

    @pytest.mark.asyncio
    async def test_event_bus_communication(self, executor):
        """Test inter-agent communication via event bus"""
        events_received = []

        async def event_handler(event_type: str, data: dict):
            events_received.append((event_type, data))

        # Register event handler
        executor.event_bus.register_handler("progress", event_handler)

        # Spawn data processing agent
        agent = MockDataProcessingAgent(data_size=100)
        agent_id = await executor.spawn_background_agent(
            agent_class="MockDataProcessingAgent",
            task="process_with_events",
            agent_instance=agent,
        )

        # Wait for processing to complete
        await asyncio.sleep(2.0)

        # Check that progress events were received
        progress_events = [e for e in events_received if e[0] == "progress"]
        assert len(progress_events) == 4  # Should emit at 25, 50, 75, 100

        # Verify event data structure
        for event_type, data in progress_events:
            assert "agent_id" in data
            assert "progress" in data
            assert "items_processed" in data
            assert data["agent_id"] == agent_id

    @pytest.mark.asyncio
    async def test_agent_failure_handling(self, executor):
        """Test proper handling of agent failures"""
        # Spawn failing agent
        failing_agent = MockLongRunningAgent(duration=0.5, should_fail=True)
        agent_id = await executor.spawn_background_agent(
            agent_class="MockLongRunningAgent",
            task="failing_task",
            agent_instance=failing_agent,
        )

        # Wait for failure
        await asyncio.sleep(1.5)

        # Check that failure was handled properly
        info = executor.get_agent_info(agent_id)
        assert info is not None
        assert info.status == "failed"
        assert "Simulated failure" in str(info.error)

        # Verify executor is still functional
        success_agent = MockLongRunningAgent(duration=0.3)
        success_id = await executor.spawn_background_agent(
            agent_class="MockLongRunningAgent",
            task="success_task",
            agent_instance=success_agent,
        )

        await asyncio.sleep(1.0)
        success_info = executor.get_agent_info(success_id)
        assert success_info.status == "completed"

    @pytest.mark.asyncio
    async def test_capacity_management(self, executor):
        """Test that executor properly manages capacity"""
        # Set low capacity limit
        executor.max_parallel_agents = 3

        # Try to spawn 5 agents
        agent_ids = []
        for i in range(5):
            try:
                agent = MockLongRunningAgent(duration=2.0)
                agent_id = await executor.spawn_background_agent(
                    agent_class="MockLongRunningAgent",
                    task=f"capacity_test_{i}",
                    agent_instance=agent,
                )
                agent_ids.append(agent_id)
            except RuntimeError as e:
                # Should fail when capacity exceeded
                assert "Maximum parallel agents exceeded" in str(e)
                break

        # Should have spawned exactly 3 agents
        assert len(agent_ids) == 3
        assert len(executor.active_agents) == 3

    @pytest.mark.asyncio
    async def test_agent_chaining_workflow(self, executor):
        """Test complex workflow with agent chaining"""
        chain_events = []

        async def chain_handler(event_type: str, data: dict):
            chain_events.append(data)

        executor.event_bus.register_handler("spawn_next", chain_handler)

        # Start chain with first agent
        first_agent = MockChainedAgent(chain_position=0, total_chain=3)
        agent_id = await executor.spawn_background_agent(
            agent_class="MockChainedAgent",
            task="start_chain",
            agent_instance=first_agent,
        )

        # Wait for chain to complete
        await asyncio.sleep(1.5)

        # Verify chain events were emitted
        assert len(chain_events) >= 1
        first_event = chain_events[0]
        assert first_event["next_position"] == 1
        assert "accumulated_data" in first_event

    @pytest.mark.asyncio
    async def test_cleanup_and_resource_management(self, executor):
        """Test proper cleanup of resources"""
        # Spawn multiple agents
        agent_ids = []
        for i in range(3):
            agent = MockLongRunningAgent(duration=1.5)
            agent_id = await executor.spawn_background_agent(
                agent_class="MockLongRunningAgent",
                task=f"cleanup_test_{i}",
                agent_instance=agent,
            )
            agent_ids.append(agent_id)

        # Verify agents are active
        assert len(executor.active_agents) == 3

        # Cleanup all
        await executor.cleanup_all()

        # Verify cleanup
        assert len(executor.active_agents) == 0

        # Verify agent infos are properly marked
        for agent_id in agent_ids:
            info = executor.get_agent_info(agent_id)
            assert info is not None
            # Should be either completed or cancelled
            assert info.status in ["completed", "cancelled", "failed"]

    @pytest.mark.asyncio
    async def test_stress_test_many_agents(self, executor):
        """Stress test with many concurrent agents"""
        # Increase capacity for stress test
        executor.max_parallel_agents = 20

        # Spawn 15 quick agents
        agent_ids = []
        for i in range(15):
            agent = MockLongRunningAgent(duration=0.2)
            agent_id = await executor.spawn_background_agent(
                agent_class="MockLongRunningAgent",
                task=f"stress_test_{i}",
                agent_instance=agent,
            )
            agent_ids.append(agent_id)

        # Verify all spawned
        assert len(executor.active_agents) == 15

        # Wait for completion
        await asyncio.sleep(1.0)

        # Check completion rate
        completed_count = 0
        for agent_id in agent_ids:
            info = executor.get_agent_info(agent_id)
            if info and info.status == "completed":
                completed_count += 1

        # Should have high success rate
        assert (
            completed_count >= 12
        ), f"Expected at least 12 completed, got {completed_count}"

    @pytest.mark.asyncio
    async def test_mixed_execution_modes(self, executor):
        """Test mixing process and thread execution modes"""
        # Spawn agents in different execution modes
        thread_agent = MockLongRunningAgent(duration=0.5)
        thread_id = await executor.spawn_background_agent(
            agent_class="MockLongRunningAgent",
            task="thread_task",
            execution_mode="thread",
            agent_instance=thread_agent,
        )

        process_agent = MockLongRunningAgent(duration=0.5)
        process_id = await executor.spawn_background_agent(
            agent_class="MockLongRunningAgent",
            task="process_task",
            execution_mode="process",
            agent_instance=process_agent,
        )

        # Wait for completion
        await asyncio.sleep(1.5)

        # Both should complete successfully
        thread_info = executor.get_agent_info(thread_id)
        process_info = executor.get_agent_info(process_id)

        assert thread_info.status == "completed"
        assert process_info.status == "completed"

        # Verify different execution modes were used
        assert thread_info.execution_mode == "thread"
        assert process_info.execution_mode == "process"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
