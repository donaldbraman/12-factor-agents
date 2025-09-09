"""
Simple integration tests for Background Agent Executor.

Tests basic functionality without complex mock agents.
"""
import asyncio
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.background_executor import (
    BackgroundAgentExecutor,
    ResourceLimits,
)


@pytest.fixture
def executor():
    """Create executor for testing"""
    import asyncio

    executor_instance = BackgroundAgentExecutor(max_parallel_agents=5)

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
    async def test_basic_agent_spawning(self, executor):
        """Test basic agent spawning functionality"""
        # Spawn a simple agent
        agent_id = await executor.spawn_background_agent(
            agent_class="BaseAgent",
            task="simple_test_task",
            workflow_data={"test_mode": True},
        )

        # Verify agent was spawned
        assert agent_id is not None
        assert len(agent_id) > 0
        assert agent_id in executor.active_agents

        # Wait a bit and check status
        await asyncio.sleep(0.5)

        info = executor.get_agent_info(agent_id)
        assert info is not None
        assert info.agent_id == agent_id
        assert info.agent_class == "BaseAgent"
        assert info.task == "simple_test_task"

    @pytest.mark.asyncio
    async def test_multiple_agents(self, executor):
        """Test spawning multiple agents concurrently"""
        # Spawn 3 agents
        agent_ids = []
        for i in range(3):
            agent_id = await executor.spawn_background_agent(
                agent_class="BaseAgent",
                task=f"multi_test_task_{i}",
                workflow_data={"agent_number": i},
            )
            agent_ids.append(agent_id)

        # Verify all agents were spawned
        assert len(agent_ids) == 3
        assert len(executor.active_agents) == 3

        # Check each agent
        for i, agent_id in enumerate(agent_ids):
            info = executor.get_agent_info(agent_id)
            assert info is not None
            assert info.task == f"multi_test_task_{i}"

    @pytest.mark.asyncio
    async def test_resource_limits(self, executor):
        """Test agent spawning with resource limits"""
        # Create resource limits
        limits = ResourceLimits(
            max_memory_mb=256, max_cpu_percent=25.0, max_execution_time=10.0
        )

        # Spawn agent with limits
        agent_id = await executor.spawn_background_agent(
            agent_class="BaseAgent",
            task="resource_limited_task",
            resource_limits=limits,
        )

        # Verify limits were applied
        info = executor.get_agent_info(agent_id)
        assert info is not None
        assert info.resource_limits == limits

    @pytest.mark.asyncio
    async def test_execution_modes(self, executor):
        """Test different execution modes"""
        # Test thread mode
        thread_id = await executor.spawn_background_agent(
            agent_class="BaseAgent", task="thread_task", execution_mode="thread"
        )

        # Test process mode
        process_id = await executor.spawn_background_agent(
            agent_class="BaseAgent", task="process_task", execution_mode="process"
        )

        # Verify different modes
        thread_info = executor.get_agent_info(thread_id)
        process_info = executor.get_agent_info(process_id)

        assert thread_info.execution_mode == "thread"
        assert process_info.execution_mode == "process"

    @pytest.mark.asyncio
    async def test_capacity_limits(self, executor):
        """Test that executor respects capacity limits"""
        # Set low capacity
        executor.max_parallel_agents = 2

        # Try to spawn 3 agents
        agent_ids = []

        # First two should succeed
        for i in range(2):
            agent_id = await executor.spawn_background_agent(
                agent_class="BaseAgent", task=f"capacity_test_{i}"
            )
            agent_ids.append(agent_id)

        # Third should fail
        with pytest.raises(RuntimeError, match="Maximum parallel agents exceeded"):
            await executor.spawn_background_agent(
                agent_class="BaseAgent", task="capacity_test_overflow"
            )

        assert len(agent_ids) == 2
        assert len(executor.active_agents) == 2

    @pytest.mark.asyncio
    async def test_event_bus_basic(self, executor):
        """Test basic event bus functionality"""
        events_received = []

        async def test_handler(event_type: str, data: dict):
            events_received.append((event_type, data))

        # Register handler
        executor.event_bus.register_handler("test_event", test_handler)

        # Emit test event
        await executor.event_bus.emit("test_event", {"message": "test"})

        # Give time for async handling
        await asyncio.sleep(0.1)

        # Verify event was received
        assert len(events_received) == 1
        event_type, data = events_received[0]
        assert event_type == "test_event"
        assert data["message"] == "test"

    @pytest.mark.asyncio
    async def test_cleanup(self, executor):
        """Test cleanup functionality"""
        # Spawn some agents
        agent_ids = []
        for i in range(2):
            agent_id = await executor.spawn_background_agent(
                agent_class="BaseAgent", task=f"cleanup_test_{i}"
            )
            agent_ids.append(agent_id)

        # Verify agents are active
        assert len(executor.active_agents) == 2

        # Cleanup
        await executor.cleanup_all()

        # Verify cleanup
        assert len(executor.active_agents) == 0

    @pytest.mark.asyncio
    async def test_agent_info_persistence(self, executor):
        """Test that agent info is properly maintained"""
        # Spawn agent
        agent_id = await executor.spawn_background_agent(
            agent_class="BaseAgent",
            task="info_test",
            workflow_data={"test_data": "value"},
        )

        # Get info immediately
        info = executor.get_agent_info(agent_id)
        assert info is not None
        assert info.agent_id == agent_id
        assert info.agent_class == "BaseAgent"
        assert info.task == "info_test"
        assert info.workflow_data["test_data"] == "value"
        assert info.status.name in ["PENDING", "RUNNING"]
        assert isinstance(info.started_at, datetime)

        # Wait and check again
        await asyncio.sleep(0.2)

        updated_info = executor.get_agent_info(agent_id)
        assert updated_info is not None
        assert updated_info.agent_id == agent_id

    @pytest.mark.asyncio
    async def test_status_monitoring(self, executor):
        """Test status monitoring functionality"""
        # Spawn agent
        agent_id = await executor.spawn_background_agent(
            agent_class="BaseAgent", task="status_test"
        )

        # Check initial status
        status = await executor.get_agent_status(agent_id)
        assert status is not None
        assert status["agent_id"] == agent_id
        assert status["status"] in ["PENDING", "RUNNING"]
        assert "started_at" in status
        assert "progress" in status

        # Status should be non-blocking
        start_time = asyncio.get_event_loop().time()
        status = await executor.get_agent_status(agent_id)
        end_time = asyncio.get_event_loop().time()

        # Should return quickly (< 100ms)
        assert (end_time - start_time) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
