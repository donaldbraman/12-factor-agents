"""
Comprehensive unit tests for Background Agent Executor
Testing fire-and-forget spawning and true parallel processing
"""

import pytest
import asyncio
import tempfile
import shutil
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.background_executor import (
    BackgroundAgentExecutor,
    BackgroundEnabledAgent,
    BackgroundStatus,
    ResourceLimits,
    BackgroundAgentInfo,
    EventBus,
    EventBusMessage
)


class TestResourceLimits:
    """Test ResourceLimits configuration"""
    
    def test_default_resource_limits(self):
        """Test default resource limit values"""
        limits = ResourceLimits()
        
        assert limits.max_memory_mb == 500
        assert limits.max_cpu_percent == 50.0
        assert limits.max_execution_time_minutes == 60
        assert limits.max_disk_usage_mb == 100
    
    def test_custom_resource_limits(self):
        """Test custom resource limit configuration"""
        limits = ResourceLimits(
            max_memory_mb=1024,
            max_cpu_percent=75.0,
            max_execution_time_minutes=120,
            max_disk_usage_mb=500
        )
        
        assert limits.max_memory_mb == 1024
        assert limits.max_cpu_percent == 75.0
        assert limits.max_execution_time_minutes == 120
        assert limits.max_disk_usage_mb == 500
    
    def test_resource_limits_serialization(self):
        """Test resource limits to dict conversion"""
        limits = ResourceLimits(max_memory_mb=256, max_cpu_percent=25.0)
        limits_dict = limits.to_dict()
        
        assert limits_dict["max_memory_mb"] == 256
        assert limits_dict["max_cpu_percent"] == 25.0
        assert limits_dict["max_execution_time_minutes"] == 60  # Default
        assert limits_dict["max_disk_usage_mb"] == 100  # Default


class TestBackgroundAgentInfo:
    """Test BackgroundAgentInfo data class"""
    
    def test_create_agent_info(self):
        """Test creating agent info"""
        start_time = datetime.now()
        limits = ResourceLimits(max_memory_mb=512)
        
        info = BackgroundAgentInfo(
            agent_id="test_agent_001",
            process_id=12345,
            status=BackgroundStatus.RUNNING,
            started_at=start_time,
            completed_at=None,
            agent_class="TestAgent",
            task="test task",
            workflow_data={"test": "data"},
            resource_limits=limits,
            progress=0.5
        )
        
        assert info.agent_id == "test_agent_001"
        assert info.process_id == 12345
        assert info.status == BackgroundStatus.RUNNING
        assert info.started_at == start_time
        assert info.completed_at is None
        assert info.agent_class == "TestAgent"
        assert info.task == "test task"
        assert info.workflow_data == {"test": "data"}
        assert info.progress == 0.5
    
    def test_agent_info_serialization(self):
        """Test agent info serialization"""
        start_time = datetime.now()
        limits = ResourceLimits()
        
        info = BackgroundAgentInfo(
            agent_id="serialize_test",
            process_id=None,
            status=BackgroundStatus.SPAWNING,
            started_at=start_time,
            completed_at=None,
            agent_class="SerializeAgent",
            task="serialize task",
            workflow_data={"key": "value"},
            resource_limits=limits
        )
        
        info_dict = info.to_dict()
        
        assert info_dict["agent_id"] == "serialize_test"
        assert info_dict["process_id"] is None
        assert info_dict["status"] == "spawning"
        assert info_dict["started_at"] == start_time.isoformat()
        assert info_dict["completed_at"] is None
        assert info_dict["agent_class"] == "SerializeAgent"
        assert info_dict["task"] == "serialize task"
        assert info_dict["workflow_data"] == {"key": "value"}
        assert "resource_limits" in info_dict


class TestEventBus:
    """Test EventBus communication system"""
    
    @pytest.fixture
    def event_bus(self):
        """Create event bus instance"""
        return EventBus()
    
    def test_event_bus_creation(self, event_bus):
        """Test event bus initialization"""
        assert len(event_bus.subscribers) == 0
        assert len(event_bus.message_history) == 0
        assert event_bus.max_history == 1000
    
    def test_subscribe_to_events(self, event_bus):
        """Test subscribing to event types"""
        callback = Mock()
        
        event_bus.subscribe("test_event", callback)
        
        assert "test_event" in event_bus.subscribers
        assert callback in event_bus.subscribers["test_event"]
    
    @pytest.mark.asyncio
    async def test_publish_events(self, event_bus):
        """Test publishing events to subscribers"""
        callback = Mock()
        event_bus.subscribe("agent_spawned", callback)
        
        message = EventBusMessage(
            agent_id="test_agent",
            event_type="agent_spawned",
            data={"test": "data"}
        )
        
        await event_bus.publish(message)
        
        # Verify callback was called
        callback.assert_called_once_with(message)
        
        # Verify message stored in history
        assert len(event_bus.message_history) == 1
        stored_message = list(event_bus.message_history.values())[0]
        assert stored_message.agent_id == "test_agent"
        assert stored_message.event_type == "agent_spawned"
    
    @pytest.mark.asyncio
    async def test_async_event_callbacks(self, event_bus):
        """Test async event callbacks"""
        async_callback = AsyncMock()
        event_bus.subscribe("async_event", async_callback)
        
        message = EventBusMessage(
            agent_id="async_agent",
            event_type="async_event",
            data={}
        )
        
        await event_bus.publish(message)
        
        async_callback.assert_called_once_with(message)
    
    def test_get_latest_events(self, event_bus):
        """Test retrieving latest events for agent"""
        # Add multiple events
        messages = []
        for i in range(5):
            message = EventBusMessage(
                agent_id="test_agent",
                event_type="progress_update",
                data={"step": i}
            )
            messages.append(message)
            event_bus.message_history[f"test_agent_{i}"] = message
        
        # Add events for different agent
        other_message = EventBusMessage(
            agent_id="other_agent",
            event_type="progress_update",
            data={"step": 0}
        )
        event_bus.message_history["other_agent_0"] = other_message
        
        # Get latest events for test_agent
        latest = event_bus.get_latest_events("test_agent", limit=3)
        
        assert len(latest) == 3
        assert all(msg.agent_id == "test_agent" for msg in latest)
        assert latest[-1].data["step"] == 4  # Most recent


class TestBackgroundAgentExecutor:
    """Test BackgroundAgentExecutor main functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def executor(self, temp_dir):
        """Create background executor instance"""
        return BackgroundAgentExecutor(max_parallel_agents=5, temp_dir=temp_dir)
    
    def test_executor_initialization(self, executor, temp_dir):
        """Test executor initialization"""
        assert executor.max_parallel_agents == 5
        assert executor.temp_dir == temp_dir
        assert len(executor.active_agents) == 0
        assert len(executor.completed_agents) == 0
        assert executor.event_bus is not None
    
    def test_executor_statistics(self, executor):
        """Test executor statistics"""
        stats = executor.get_statistics()
        
        assert stats["max_parallel_agents"] == 5
        assert stats["active_agents"] == 0
        assert stats["completed_agents"] == 0
        assert stats["total_spawned"] == 0
        assert stats["capacity_used"] == 0.0
        assert "temp_dir" in stats
        assert "event_bus_messages" in stats
    
    @pytest.mark.asyncio
    async def test_spawn_background_agent_capacity_check(self, executor):
        """Test capacity checking when spawning agents"""
        # Mock active agents to simulate full capacity
        for i in range(5):  # Max capacity
            executor.active_agents[f"agent_{i}"] = Mock()
        
        # Try to spawn one more (should fail)
        with pytest.raises(RuntimeError, match="Maximum parallel agents"):
            await executor.spawn_background_agent("TestAgent", "test task")
    
    @pytest.mark.asyncio
    async def test_agent_creation_script_generation(self, executor):
        """Test agent script creation"""
        start_time = datetime.now()
        limits = ResourceLimits()
        
        agent_info = BackgroundAgentInfo(
            agent_id="script_test_agent",
            process_id=None,
            status=BackgroundStatus.SPAWNING,
            started_at=start_time,
            completed_at=None,
            agent_class="TestAgent",
            task="test script generation",
            workflow_data={"script": "test"},
            resource_limits=limits,
            output_file=executor.temp_dir / "script_test_agent_output.json",
            error_file=executor.temp_dir / "script_test_agent_error.json"
        )
        
        # Create script
        script_path = await executor._create_agent_script(agent_info)
        
        # Verify script created
        assert script_path.exists()
        assert script_path.is_file()
        assert script_path.stat().st_mode & 0o755  # Executable
        
        # Verify script content
        script_content = script_path.read_text()
        assert "script_test_agent" in script_content
        assert "test script generation" in script_content
        assert str(agent_info.output_file) in script_content
    
    @pytest.mark.asyncio
    async def test_agent_status_tracking(self, executor):
        """Test agent status tracking and retrieval"""
        # Create mock agent info
        start_time = datetime.now()
        agent_info = BackgroundAgentInfo(
            agent_id="status_test_agent",
            process_id=None,
            status=BackgroundStatus.RUNNING,
            started_at=start_time,
            completed_at=None,
            agent_class="StatusAgent",
            task="status test",
            workflow_data={"status": "test"},
            resource_limits=ResourceLimits(),
            progress=0.75
        )
        
        executor.active_agents["status_test_agent"] = agent_info
        
        # Get agent status
        status = await executor.get_agent_status("status_test_agent")
        
        assert status is not None
        assert status["agent_id"] == "status_test_agent"
        assert status["status"] == "running"
        assert status["started_at"] == start_time.isoformat()
        assert status["progress"] == 0.75
    
    @pytest.mark.asyncio
    async def test_nonexistent_agent_status(self, executor):
        """Test getting status of non-existent agent"""
        status = await executor.get_agent_status("nonexistent_agent")
        assert status is None
    
    @pytest.mark.asyncio
    async def test_get_all_agents_status(self, executor):
        """Test getting status of all agents"""
        # Add mock active agent
        active_agent = BackgroundAgentInfo(
            agent_id="active_agent",
            process_id=None,
            status=BackgroundStatus.RUNNING,
            started_at=datetime.now(),
            completed_at=None,
            agent_class="ActiveAgent",
            task="active task",
            workflow_data={},
            resource_limits=ResourceLimits()
        )
        executor.active_agents["active_agent"] = active_agent
        
        # Add mock completed agent
        completed_agent = BackgroundAgentInfo(
            agent_id="completed_agent",
            process_id=None,
            status=BackgroundStatus.COMPLETED,
            started_at=datetime.now() - timedelta(minutes=5),
            completed_at=datetime.now(),
            agent_class="CompletedAgent",
            task="completed task",
            workflow_data={},
            resource_limits=ResourceLimits()
        )
        executor.completed_agents["completed_agent"] = completed_agent
        
        # Get all status
        all_status = await executor.get_all_agents_status()
        
        assert len(all_status) >= 2
        assert "active_agent" in all_status
        assert "completed_agent" in all_status
        assert all_status["active_agent"]["status"] == "running"
        assert all_status["completed_agent"]["status"] == "completed"
    
    def test_static_agent_script_execution(self, executor):
        """Test static agent script execution method"""
        # Create a simple test script
        script_content = '''#!/usr/bin/env python3
import sys
import json
from pathlib import Path

output_file = Path("/tmp/test_output.json")
result = {"success": True, "message": "Test script executed"}

with open(output_file, 'w') as f:
    json.dump(result, f)

print("Script executed successfully")
exit(0)
'''
        
        test_script = executor.temp_dir / "test_script.py"
        test_script.write_text(script_content)
        test_script.chmod(0o755)
        
        # Execute script
        result = BackgroundAgentExecutor._execute_agent_script(
            str(test_script), 
            ResourceLimits(max_execution_time_minutes=1)
        )
        
        assert result["success"] is True
        assert result["return_code"] == 0
        assert "Script executed successfully" in result["stdout"]
    
    def test_thread_agent_execution(self, executor):
        """Test agent execution in thread"""
        agent_info = BackgroundAgentInfo(
            agent_id="thread_test_agent",
            process_id=None,
            status=BackgroundStatus.SPAWNING,
            started_at=datetime.now(),
            completed_at=None,
            agent_class="ThreadAgent",
            task="thread test",
            workflow_data={"thread": True},
            resource_limits=ResourceLimits(),
            output_file=executor.temp_dir / "thread_test_output.json",
            error_file=executor.temp_dir / "thread_test_error.json"
        )
        
        # Execute in thread
        result = executor._execute_agent_in_thread(agent_info)
        
        assert result["success"] is True
        assert result["mode"] == "thread"
        
        # Verify output file created
        assert agent_info.output_file.exists()
        
        output_data = json.loads(agent_info.output_file.read_text())
        assert output_data["agent_id"] == "thread_test_agent"
        assert output_data["status"] == "completed"


class TestBackgroundEnabledAgent:
    """Test BackgroundEnabledAgent integration"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def background_executor(self, temp_dir):
        """Create background executor"""
        return BackgroundAgentExecutor(max_parallel_agents=3, temp_dir=temp_dir)
    
    @pytest.fixture
    def agent(self, background_executor):
        """Create background-enabled agent"""
        return BackgroundEnabledAgent("test_agent", background_executor)
    
    def test_agent_initialization(self, agent, background_executor):
        """Test agent initialization with background executor"""
        assert agent.agent_id == "test_agent"
        assert agent.background_executor is background_executor
        assert len(agent.spawned_agents) == 0
    
    @pytest.mark.asyncio
    async def test_spawn_background_task(self, agent):
        """Test spawning background tasks"""
        # Mock the spawn method to avoid actual process creation
        with patch.object(agent.background_executor, 'spawn_background_agent') as mock_spawn:
            mock_spawn.return_value = "bg_agent_123"
            
            # Spawn background task
            bg_agent_id = await agent.spawn_background_task(
                task="background test task",
                workflow_data={"bg": True}
            )
            
            assert bg_agent_id == "bg_agent_123"
            assert bg_agent_id in agent.spawned_agents
            
            # Verify spawn was called correctly
            mock_spawn.assert_called_once()
            call_args = mock_spawn.call_args
            assert call_args[1]["task"] == "background test task"
            assert call_args[1]["workflow_data"] == {"bg": True}
    
    @pytest.mark.asyncio
    async def test_check_background_status(self, agent):
        """Test checking background agent status"""
        # Mock status check
        with patch.object(agent.background_executor, 'get_agent_status') as mock_status:
            mock_status.return_value = {
                "agent_id": "bg_agent_123",
                "status": "running",
                "progress": 0.5
            }
            
            status = await agent.check_background_status("bg_agent_123")
            
            assert status["agent_id"] == "bg_agent_123"
            assert status["status"] == "running"
            assert status["progress"] == 0.5
            
            mock_status.assert_called_once_with("bg_agent_123")
    
    @pytest.mark.asyncio
    async def test_wait_for_completion(self, agent):
        """Test waiting for background agent completion"""
        # Mock status progression
        status_sequence = [
            {"status": "running", "progress": 0.3},
            {"status": "running", "progress": 0.7},
            {"status": "completed", "progress": 1.0}
        ]
        
        with patch.object(agent, 'check_background_status') as mock_status:
            mock_status.side_effect = status_sequence
            
            final_status = await agent.wait_for_background_completion("bg_agent_123")
            
            assert final_status["status"] == "completed"
            assert final_status["progress"] == 1.0
            assert mock_status.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_timeout(self, agent):
        """Test waiting with timeout"""
        # Mock never-completing status
        with patch.object(agent, 'check_background_status') as mock_status:
            mock_status.return_value = {"status": "running", "progress": 0.5}
            
            start_time = time.time()
            result = await agent.wait_for_background_completion("bg_agent_123", timeout=0.1)
            elapsed = time.time() - start_time
            
            assert "error" in result
            assert "Timeout" in result["error"]
            assert elapsed >= 0.1
            assert elapsed < 0.5  # Should not wait much longer than timeout
    
    @pytest.mark.asyncio
    async def test_get_all_background_status(self, agent):
        """Test getting status of all spawned agents"""
        # Setup spawned agents
        agent.spawned_agents = ["bg_agent_1", "bg_agent_2", "bg_agent_3"]
        
        # Mock status responses
        status_responses = {
            "bg_agent_1": {"status": "running", "progress": 0.3},
            "bg_agent_2": {"status": "completed", "progress": 1.0},
            "bg_agent_3": None  # Agent not found
        }
        
        with patch.object(agent, 'check_background_status') as mock_status:
            mock_status.side_effect = lambda aid: status_responses.get(aid)
            
            all_status = await agent.get_all_background_status()
            
            assert len(all_status) == 2  # Only found agents
            assert "bg_agent_1" in all_status
            assert "bg_agent_2" in all_status
            assert "bg_agent_3" not in all_status
            
            assert all_status["bg_agent_1"]["status"] == "running"
            assert all_status["bg_agent_2"]["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_terminate_background_agent(self, agent):
        """Test terminating background agents"""
        # Add agent to spawned list
        agent.spawned_agents = ["bg_agent_123"]
        
        # Mock termination
        with patch.object(agent.background_executor, 'terminate_agent') as mock_terminate:
            mock_terminate.return_value = True
            
            success = await agent.terminate_background_agent("bg_agent_123", force=True)
            
            assert success is True
            assert "bg_agent_123" not in agent.spawned_agents
            
            mock_terminate.assert_called_once_with("bg_agent_123", True)


class TestResourceMonitoring:
    """Test resource monitoring and limits"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def executor(self, temp_dir):
        """Create executor with short monitoring interval"""
        executor = BackgroundAgentExecutor(temp_dir=temp_dir)
        executor.monitor_interval = 0.1  # Very short for testing
        return executor
    
    @pytest.mark.asyncio
    async def test_resource_usage_tracking(self, executor):
        """Test resource usage tracking"""
        # Create mock agent with process ID
        agent_info = BackgroundAgentInfo(
            agent_id="resource_test_agent",
            process_id=os.getpid(),  # Use current process
            status=BackgroundStatus.RUNNING,
            started_at=datetime.now(),
            completed_at=None,
            agent_class="ResourceAgent",
            task="resource test",
            workflow_data={},
            resource_limits=ResourceLimits()
        )
        
        # Get resource usage
        usage = await executor._get_resource_usage(agent_info)
        
        # Should have resource data for current process
        assert isinstance(usage.get("cpu_percent", 0), (int, float))
        assert isinstance(usage.get("memory_mb", 0), (int, float))
        assert isinstance(usage.get("num_threads", 0), int)
        assert usage["memory_mb"] > 0  # Current process should use some memory
    
    @pytest.mark.asyncio
    async def test_resource_usage_nonexistent_process(self, executor):
        """Test resource usage for non-existent process"""
        agent_info = BackgroundAgentInfo(
            agent_id="nonexistent_agent",
            process_id=999999,  # Very unlikely to exist
            status=BackgroundStatus.RUNNING,
            started_at=datetime.now(),
            completed_at=None,
            agent_class="NonExistentAgent",
            task="nonexistent test",
            workflow_data={},
            resource_limits=ResourceLimits()
        )
        
        usage = await executor._get_resource_usage(agent_info)
        
        # Should return empty dict for non-existent process
        assert usage == {}


class TestExecutorCleanup:
    """Test executor cleanup and shutdown"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def executor(self, temp_dir):
        """Create executor"""
        return BackgroundAgentExecutor(temp_dir=temp_dir)
    
    @pytest.mark.asyncio
    async def test_executor_shutdown(self, executor):
        """Test graceful executor shutdown"""
        # Add mock active agents
        for i in range(3):
            agent_info = BackgroundAgentInfo(
                agent_id=f"shutdown_agent_{i}",
                process_id=None,
                status=BackgroundStatus.RUNNING,
                started_at=datetime.now(),
                completed_at=None,
                agent_class="ShutdownAgent",
                task="shutdown test",
                workflow_data={},
                resource_limits=ResourceLimits()
            )
            executor.active_agents[f"shutdown_agent_{i}"] = agent_info
        
        # Mock terminate agent to avoid actual process operations
        with patch.object(executor, 'terminate_agent') as mock_terminate:
            mock_terminate.return_value = True
            
            await executor.shutdown()
            
            # Should have attempted to terminate all agents
            assert mock_terminate.call_count >= 3


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def executor(self, temp_dir):
        """Create executor"""
        return BackgroundAgentExecutor(temp_dir=temp_dir)
    
    @pytest.mark.asyncio
    async def test_error_writing(self, executor):
        """Test error writing to files"""
        agent_info = BackgroundAgentInfo(
            agent_id="error_test_agent",
            process_id=None,
            status=BackgroundStatus.FAILED,
            started_at=datetime.now(),
            completed_at=None,
            agent_class="ErrorAgent",
            task="error test",
            workflow_data={},
            resource_limits=ResourceLimits(),
            error_file=executor.temp_dir / "error_test_error.json"
        )
        
        # Write error
        await executor._write_error(agent_info, "Test error message")
        
        # Verify error file created
        assert agent_info.error_file.exists()
        
        error_data = json.loads(agent_info.error_file.read_text())
        assert error_data["agent_id"] == "error_test_agent"
        assert error_data["error"] == "Test error message"
        assert error_data["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_pause_resume_nonexistent_agent(self, executor):
        """Test pause/resume on non-existent agents"""
        # Try to pause non-existent agent
        pause_result = await executor.pause_agent("nonexistent_agent")
        assert pause_result is False
        
        # Try to resume non-existent agent
        resume_result = await executor.resume_agent("nonexistent_agent")
        assert resume_result is False
    
    @pytest.mark.asyncio
    async def test_terminate_nonexistent_agent(self, executor):
        """Test terminating non-existent agent"""
        terminate_result = await executor.terminate_agent("nonexistent_agent")
        assert terminate_result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])