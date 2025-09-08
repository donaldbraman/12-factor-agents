"""
Comprehensive unit tests for Context Bundles System
Testing session persistence, perfect handoffs, and zero context loss
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.context_bundles import (
    ContextBundleManager,
    ContextBundle,
    TimestampedAction,
    ActionType,
    Checkpoint,
    BundleMetadata,
    BundleEnabledAgent
)
from core.base import ToolResponse


class TestTimestampedAction:
    """Test TimestampedAction class"""
    
    def test_create_timestamped_action(self):
        """Test creating a timestamped action"""
        timestamp = datetime.now()
        action = TimestampedAction(
            timestamp=timestamp,
            action_type=ActionType.TASK_EXECUTION,
            action_data={"task": "test task"},
            agent_id="agent_1",
            session_id="session_1"
        )
        
        assert action.timestamp == timestamp
        assert action.action_type == ActionType.TASK_EXECUTION
        assert action.action_data == {"task": "test task"}
        assert action.agent_id == "agent_1"
        assert action.session_id == "session_1"
    
    def test_action_serialization(self):
        """Test action serialization and deserialization"""
        action = TimestampedAction(
            timestamp=datetime.now(),
            action_type=ActionType.STATE_CHANGE,
            action_data={"changes": {"key": "value"}},
            agent_id="agent_2",
            session_id="session_2"
        )
        
        # Serialize to dict
        action_dict = action.to_dict()
        assert action_dict["action_type"] == "state_change"
        assert action_dict["agent_id"] == "agent_2"
        
        # Deserialize from dict
        restored_action = TimestampedAction.from_dict(action_dict)
        assert restored_action.action_type == ActionType.STATE_CHANGE
        assert restored_action.agent_id == "agent_2"
        assert restored_action.action_data == {"changes": {"key": "value"}}


class TestCheckpoint:
    """Test Checkpoint functionality"""
    
    def test_create_checkpoint(self):
        """Test checkpoint creation"""
        checkpoint = Checkpoint(
            checkpoint_id="cp_1",
            timestamp=datetime.now(),
            phase="implementation",
            progress=0.5,
            state={"current_task": "coding", "files_modified": 3}
        )
        
        assert checkpoint.checkpoint_id == "cp_1"
        assert checkpoint.phase == "implementation"
        assert checkpoint.progress == 0.5
        assert checkpoint.state["current_task"] == "coding"
    
    def test_checkpoint_serialization(self):
        """Test checkpoint serialization"""
        checkpoint = Checkpoint(
            checkpoint_id="cp_2",
            timestamp=datetime.now(),
            phase="testing",
            progress=0.8,
            state={"tests_passed": 15, "tests_failed": 2},
            metadata={"notes": "Almost done"}
        )
        
        checkpoint_dict = checkpoint.to_dict()
        assert checkpoint_dict["checkpoint_id"] == "cp_2"
        assert checkpoint_dict["phase"] == "testing"
        assert checkpoint_dict["progress"] == 0.8
        assert checkpoint_dict["metadata"]["notes"] == "Almost done"


class TestContextBundle:
    """Test ContextBundle creation and operations"""
    
    @pytest.fixture
    def sample_bundle(self):
        """Create sample context bundle"""
        actions = [
            TimestampedAction(
                timestamp=datetime.now(),
                action_type=ActionType.TASK_EXECUTION,
                action_data={"task": "implement feature"},
                agent_id="agent_1",
                session_id="session_1"
            ),
            TimestampedAction(
                timestamp=datetime.now(),
                action_type=ActionType.STATE_CHANGE,
                action_data={"progress": 0.3},
                agent_id="agent_1", 
                session_id="session_1"
            )
        ]
        
        checkpoints = [
            Checkpoint(
                checkpoint_id="cp_1",
                timestamp=datetime.now(),
                phase="started",
                progress=0.0,
                state={"initialized": True}
            )
        ]
        
        metadata = BundleMetadata(
            created_at=datetime.now(),
            last_modified=datetime.now(),
            agent_type="TestAgent",
            task_description="Test implementation"
        )
        
        return ContextBundle(
            session_id="session_1",
            actions=actions,
            state={"current_phase": "implementation", "progress": 0.3},
            metadata=metadata,
            checkpoints=checkpoints
        )
    
    def test_bundle_creation(self, sample_bundle):
        """Test context bundle creation"""
        assert sample_bundle.session_id == "session_1"
        assert len(sample_bundle.actions) == 2
        assert len(sample_bundle.checkpoints) == 1
        assert sample_bundle.state["current_phase"] == "implementation"
        assert sample_bundle.metadata.agent_type == "TestAgent"
    
    def test_bundle_serialization(self, sample_bundle):
        """Test bundle serialization and deserialization"""
        # Serialize to dict
        bundle_dict = sample_bundle.to_dict()
        assert bundle_dict["session_id"] == "session_1"
        assert len(bundle_dict["actions"]) == 2
        assert len(bundle_dict["checkpoints"]) == 1
        
        # Deserialize from dict
        restored_bundle = ContextBundle.from_dict(bundle_dict)
        assert restored_bundle.session_id == "session_1"
        assert len(restored_bundle.actions) == 2
        assert restored_bundle.state["current_phase"] == "implementation"
        assert restored_bundle.metadata.agent_type == "TestAgent"
    
    def test_bundle_compression(self, sample_bundle):
        """Test bundle compression and decompression"""
        # Compress bundle
        compressed = sample_bundle.compress()
        assert isinstance(compressed, bytes)
        assert len(compressed) > 0
        
        # Decompress bundle
        decompressed = ContextBundle.decompress(compressed)
        assert decompressed.session_id == sample_bundle.session_id
        assert len(decompressed.actions) == len(sample_bundle.actions)
        assert decompressed.state == sample_bundle.state
    
    def test_bundle_size_calculation(self, sample_bundle):
        """Test bundle size calculation"""
        size_bytes = sample_bundle.get_size_bytes()
        assert isinstance(size_bytes, int)
        assert size_bytes > 0
        
        # Size should be reasonable (not too large)
        assert size_bytes < 10000  # Less than 10KB for small bundle


class TestContextBundleManager:
    """Test ContextBundleManager functionality"""
    
    @pytest.fixture
    def manager(self):
        """Create context bundle manager"""
        return ContextBundleManager(session_id="test_session")
    
    @pytest.fixture
    def filesystem_manager(self):
        """Create filesystem-based manager with temp directory"""
        temp_dir = tempfile.mkdtemp()
        
        # Patch the storage path to use temp directory
        with patch('core.context_bundles.ContextBundleManager.__init__') as mock_init:
            def init_with_temp(self, session_id=None, storage_backend="memory"):
                self.session_id = session_id or "test_session"
                self.storage_backend = storage_backend
                self.append_log = []
                self.current_state = {}
                self.checkpoints = []
                self.metadata = BundleMetadata(
                    created_at=datetime.now(),
                    last_modified=datetime.now()
                )
                
                if storage_backend == "filesystem":
                    self.storage_path = Path(temp_dir) / self.session_id
                    self.storage_path.mkdir(parents=True, exist_ok=True)
                
                from collections import OrderedDict
                self._bundle_cache = OrderedDict()
                self._max_cache_size = 10
            
            mock_init.side_effect = init_with_temp
            manager = ContextBundleManager(storage_backend="filesystem")
            
        yield manager, temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_session_id_generation(self):
        """Test unique session ID generation"""
        manager1 = ContextBundleManager()
        manager2 = ContextBundleManager()
        
        assert manager1.session_id != manager2.session_id
        assert len(manager1.session_id) == 16
        assert all(c in "0123456789abcdef" for c in manager1.session_id)
    
    def test_append_only_logging(self, manager):
        """Test append-only action logging"""
        # Append first action
        manager.append_action(
            ActionType.TASK_EXECUTION,
            {"task": "start implementation"},
            "agent_1"
        )
        
        assert len(manager.append_log) == 1
        assert manager.append_log[0].action_type == ActionType.TASK_EXECUTION
        assert manager.append_log[0].agent_id == "agent_1"
        
        # Append second action
        manager.append_action(
            ActionType.STATE_CHANGE,
            {"progress": 0.2},
            "agent_1"
        )
        
        assert len(manager.append_log) == 2
        assert manager.append_log[1].action_type == ActionType.STATE_CHANGE
        
        # Verify timestamps are in order
        assert manager.append_log[0].timestamp <= manager.append_log[1].timestamp
    
    def test_state_updates(self, manager):
        """Test state update tracking"""
        # Update state
        manager.update_state({"current_task": "coding", "progress": 0.3})
        
        assert manager.current_state["current_task"] == "coding"
        assert manager.current_state["progress"] == 0.3
        
        # Verify state change was logged
        state_changes = [a for a in manager.append_log if a.action_type == ActionType.STATE_CHANGE]
        assert len(state_changes) == 1
        assert state_changes[0].action_data["state_updates"]["current_task"] == "coding"
        
        # Update again
        manager.update_state({"progress": 0.7, "files_modified": 5})
        
        assert manager.current_state["progress"] == 0.7
        assert manager.current_state["files_modified"] == 5
        assert manager.current_state["current_task"] == "coding"  # Preserved
    
    def test_checkpoint_creation(self, manager):
        """Test checkpoint creation and management"""
        # Set some initial state
        manager.update_state({"task": "implementation", "progress": 0.1})
        
        # Create checkpoint
        checkpoint_id = manager.create_checkpoint(
            phase="implementation_started",
            progress=0.1,
            metadata={"notes": "Starting implementation phase"}
        )
        
        assert checkpoint_id == "checkpoint_1"
        assert len(manager.checkpoints) == 1
        
        checkpoint = manager.checkpoints[0]
        assert checkpoint.phase == "implementation_started"
        assert checkpoint.progress == 0.1
        assert checkpoint.state["task"] == "implementation"
        assert checkpoint.metadata["notes"] == "Starting implementation phase"
        
        # Create second checkpoint
        manager.update_state({"progress": 0.5})
        checkpoint_id_2 = manager.create_checkpoint("implementation_halfway", 0.5)
        
        assert checkpoint_id_2 == "checkpoint_2"
        assert len(manager.checkpoints) == 2
        
        # Verify checkpoint was logged
        checkpoint_actions = [a for a in manager.append_log if a.action_type == ActionType.CHECKPOINT]
        assert len(checkpoint_actions) == 2
    
    def test_bundle_snapshot_creation(self, manager):
        """Test creating bundle snapshots"""
        # Set up some state and actions
        manager.update_state({"task": "test", "progress": 0.5})
        manager.append_action(ActionType.TASK_EXECUTION, {"task": "test"}, "agent_1")
        manager.create_checkpoint("testing", 0.5)
        
        # Create snapshot
        bundle = manager.create_bundle_snapshot()
        
        assert isinstance(bundle, ContextBundle)
        assert bundle.session_id == manager.session_id
        assert len(bundle.actions) >= 2  # At least state update and task execution
        assert bundle.state == manager.current_state
        assert len(bundle.checkpoints) == 1
    
    @pytest.mark.asyncio
    async def test_memory_storage(self, manager):
        """Test memory-based bundle storage"""
        # Set up bundle
        manager.update_state({"test": "data"})
        bundle = manager.create_bundle_snapshot()
        
        # Save bundle
        success = await manager.save_bundle(bundle)
        assert success
        
        # Load bundle
        loaded_bundle = await manager.load_bundle(bundle.session_id)
        assert loaded_bundle is not None
        assert loaded_bundle.session_id == bundle.session_id
        assert loaded_bundle.state == bundle.state
    
    def test_context_remounting(self, manager):
        """Test perfect context remounting"""
        # Create initial state
        manager.update_state({"initial": "state", "progress": 0.3})
        manager.append_action(ActionType.TASK_EXECUTION, {"task": "original"}, "agent_1")
        manager.create_checkpoint("original_phase", 0.3)
        
        # Create bundle
        original_bundle = manager.create_bundle_snapshot()
        
        # Modify state (simulate different agent)
        manager.update_state({"different": "data", "progress": 0.8})
        manager.create_checkpoint("different_phase", 0.8)
        
        # Verify state changed
        assert manager.current_state.get("initial") != "state"
        assert manager.current_state["progress"] == 0.8
        
        # Remount original context
        import asyncio
        success = asyncio.run(manager.remount_context(original_bundle))
        assert success
        
        # Verify perfect restoration
        assert manager.current_state["initial"] == "state"
        assert manager.current_state["progress"] == 0.3
        assert len([a for a in manager.append_log if a.action_data.get("task") == "original"]) >= 1
        assert manager.checkpoints[0].phase == "original_phase"
    
    def test_action_history_filtering(self, manager):
        """Test action history filtering and retrieval"""
        # Create various action types
        manager.append_action(ActionType.TASK_EXECUTION, {"task": "1"}, "agent_1")
        manager.append_action(ActionType.STATE_CHANGE, {"state": "1"}, "agent_1")
        manager.append_action(ActionType.TASK_EXECUTION, {"task": "2"}, "agent_1")
        manager.append_action(ActionType.ERROR, {"error": "test"}, "agent_1")
        manager.append_action(ActionType.CHECKPOINT, {"cp": "1"}, "agent_1")
        
        # Get all actions
        all_actions = manager.get_action_history()
        assert len(all_actions) == 5
        
        # Filter by action type
        task_actions = manager.get_action_history(ActionType.TASK_EXECUTION)
        assert len(task_actions) == 2
        assert all(a.action_type == ActionType.TASK_EXECUTION for a in task_actions)
        
        # Limit results
        limited_actions = manager.get_action_history(limit=3)
        assert len(limited_actions) == 3
        
        # Combined filter and limit
        limited_task_actions = manager.get_action_history(ActionType.TASK_EXECUTION, limit=1)
        assert len(limited_task_actions) == 1
        assert limited_task_actions[0].action_type == ActionType.TASK_EXECUTION
    
    def test_checkpoint_restoration(self, manager):
        """Test restoring from specific checkpoints"""
        # Create initial state and checkpoint
        manager.update_state({"phase": "initial", "progress": 0.1})
        cp1_id = manager.create_checkpoint("phase_1", 0.1)
        
        # Advance state and create second checkpoint
        manager.update_state({"phase": "advanced", "progress": 0.7})
        cp2_id = manager.create_checkpoint("phase_2", 0.7)
        
        # Verify current state
        assert manager.current_state["phase"] == "advanced"
        assert manager.current_state["progress"] == 0.7
        
        # Restore from first checkpoint
        success = manager.restore_from_checkpoint(cp1_id)
        assert success
        
        # Verify restoration
        assert manager.current_state["phase"] == "initial"
        assert manager.current_state["progress"] == 0.1
        
        # Try invalid checkpoint
        success = manager.restore_from_checkpoint("invalid_checkpoint")
        assert not success
    
    def test_bundle_statistics(self, manager):
        """Test bundle statistics generation"""
        # Create some activity
        manager.update_state({"test": "data"})
        manager.append_action(ActionType.TASK_EXECUTION, {"task": "1"}, "agent_1")
        manager.append_action(ActionType.STATE_CHANGE, {"change": "1"}, "agent_1")
        manager.create_checkpoint("test_phase", 0.5)
        
        # Get statistics
        stats = manager.get_bundle_stats()
        
        assert stats["session_id"] == manager.session_id
        assert stats["total_actions"] >= 3  # At least state update, task, state change
        assert stats["total_checkpoints"] == 1
        assert stats["size_bytes"] > 0
        assert stats["size_mb"] > 0
        assert "created_at" in stats
        assert "last_modified" in stats
        assert "action_types" in stats
        assert stats["latest_checkpoint"] == "checkpoint_1"
        
        # Verify action type counts
        action_counts = stats["action_types"]
        assert action_counts.get("task_execution", 0) >= 1
        assert action_counts.get("state_change", 0) >= 2  # Manual + checkpoint


class TestBundleEnabledAgent:
    """Test BundleEnabledAgent functionality"""
    
    class TestAgent(BundleEnabledAgent):
        """Test implementation of BundleEnabledAgent"""
        
        async def _execute_task_impl(self, task: str) -> ToolResponse:
            """Simple test implementation"""
            return ToolResponse(
                success=True,
                data={"result": f"Completed task: {task}"}
            )
    
    @pytest.fixture
    def agent(self):
        """Create test agent"""
        return self.TestAgent(agent_id="test_agent")
    
    @pytest.mark.asyncio
    async def test_task_execution_with_bundles(self, agent):
        """Test task execution with bundle tracking"""
        task = "implement feature X"
        
        # Execute task
        result = await agent.execute_task(task)
        
        # Verify result
        assert result.success
        assert "Completed task" in result.data["result"]
        
        # Verify bundle tracking
        bundle_stats = agent.bundle_manager.get_bundle_stats()
        assert bundle_stats["total_actions"] >= 2  # Task execution + result
        assert bundle_stats["total_checkpoints"] >= 2  # Start + completion
        
        # Verify action types
        action_types = bundle_stats["action_types"]
        assert "task_execution" in action_types
        assert "result" in action_types
        assert "checkpoint" in action_types
    
    @pytest.mark.asyncio
    async def test_handoff_creation(self, agent):
        """Test creating handoffs to other agents"""
        # Set up some state
        agent.bundle_manager.update_state({"current_work": "implementation", "progress": 0.6})
        
        # Create handoff
        handoff_data = {
            "work_summary": "Implemented core features",
            "next_steps": ["Add tests", "Update docs"],
            "blockers": ["Need design review"]
        }
        
        handoff_session_id = await agent.create_handoff("target_agent", handoff_data)
        
        # Verify handoff created
        assert handoff_session_id
        assert len(handoff_session_id) > 0
        
        # Verify handoff was logged
        handoff_actions = agent.bundle_manager.get_action_history(ActionType.HANDOFF)
        assert len(handoff_actions) >= 1
        
        handoff_action = handoff_actions[-1]
        assert handoff_action.action_data["from_agent"] == "test_agent"
        assert handoff_action.action_data["to_agent"] == "target_agent"
        assert handoff_action.action_data["handoff_data"] == handoff_data
        
        # Verify metadata updated
        assert "handoff" in agent.bundle_manager.metadata.tags
    
    @pytest.mark.asyncio
    async def test_handoff_reception(self, agent):
        """Test receiving handoffs from other agents"""
        # Create a handoff bundle from another agent
        source_agent = self.TestAgent(agent_id="source_agent", session_id="source_session")
        source_agent.bundle_manager.update_state({
            "completed_work": "database schema",
            "progress": 0.4,
            "files_modified": ["models.py", "migrations.py"]
        })
        
        handoff_data = {"work_done": "Created database models"}
        handoff_session_id = await source_agent.create_handoff("test_agent", handoff_data)
        
        # Receive handoff
        success = await agent.receive_handoff(handoff_session_id)
        assert success
        
        # Verify context was received
        assert agent.workflow_data["completed_work"] == "database schema"
        assert agent.workflow_data["progress"] == 0.4
        assert "models.py" in agent.workflow_data["files_modified"]
        
        # Verify handoff receipt was logged
        handoff_actions = agent.bundle_manager.get_action_history(ActionType.HANDOFF)
        receipt_actions = [a for a in handoff_actions if a.action_data.get("event") == "handoff_received"]
        assert len(receipt_actions) >= 1
    
    def test_handoff_summary(self, agent):
        """Test handoff summary generation"""
        # Set up agent state
        agent.bundle_manager.update_state({"task": "implementation", "progress": 0.75})
        agent.bundle_manager.create_checkpoint("implementation_phase", 0.75)
        
        # Get handoff summary
        summary = agent.get_handoff_summary()
        
        # Verify summary contents
        assert summary["session_id"] == agent.bundle_manager.session_id
        assert summary["agent_id"] == "test_agent"
        assert summary["agent_type"] == "TestAgent"
        assert summary["total_actions"] >= 1
        assert summary["checkpoints"] >= 1
        assert summary["current_phase"] == "implementation_phase"
        assert summary["progress"] == 0.75
        assert "state_summary" in summary
        assert "action_summary" in summary
        assert "created_at" in summary
        assert "last_modified" in summary


class TestBundlePerformance:
    """Performance tests for Context Bundles"""
    
    def test_large_bundle_performance(self):
        """Test performance with large bundles"""
        import time
        manager = ContextBundleManager()
        
        # Create large amount of data
        start_time = time.time()
        
        for i in range(1000):
            manager.append_action(
                ActionType.TASK_EXECUTION,
                {"task": f"task_{i}", "data": f"data_{i}" * 10},
                f"agent_{i % 10}"
            )
            
            if i % 100 == 0:
                manager.create_checkpoint(f"phase_{i // 100}", i / 1000)
        
        # Create bundle
        bundle_creation_time = time.time()
        bundle = manager.create_bundle_snapshot()
        bundle_created_time = time.time()
        
        # Verify performance
        total_time = bundle_created_time - start_time
        bundle_time = bundle_created_time - bundle_creation_time
        
        assert total_time < 5.0  # Should complete in under 5 seconds
        assert bundle_time < 1.0  # Bundle creation should be under 1 second
        
        # Verify bundle size is reasonable
        size_mb = bundle.get_size_bytes() / (1024 * 1024)
        assert size_mb < 10  # Should be under 10MB
    
    def test_compression_efficiency(self):
        """Test bundle compression efficiency"""
        manager = ContextBundleManager()
        
        # Create repetitive data (should compress well)
        for i in range(100):
            manager.append_action(
                ActionType.STATE_CHANGE,
                {"repeated_data": "This is repeated data " * 20},
                "agent_1"
            )
        
        bundle = manager.create_bundle_snapshot()
        
        # Test compression
        uncompressed_size = bundle.get_size_bytes()
        compressed_data = bundle.compress()
        compressed_size = len(compressed_data)
        
        # Verify compression ratio
        compression_ratio = compressed_size / uncompressed_size
        assert compression_ratio < 0.5  # Should compress to less than 50%
        
        # Verify decompression works
        decompressed_bundle = ContextBundle.decompress(compressed_data)
        assert decompressed_bundle.session_id == bundle.session_id
        assert len(decompressed_bundle.actions) == len(bundle.actions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])