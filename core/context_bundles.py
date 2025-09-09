"""
Context Bundles System implementing Claude Code's session persistence pattern
Enables perfect agent handoffs with zero context loss
"""

import json
import hashlib
import gzip
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
from collections import OrderedDict

from .base import BaseAgent, ToolResponse


class ActionType(Enum):
    """Types of actions that can be logged"""

    TASK_EXECUTION = "task_execution"
    STATE_CHANGE = "state_change"
    CHECKPOINT = "checkpoint"
    ERROR = "error"
    DELEGATION = "delegation"
    RESULT = "result"
    HANDOFF = "handoff"


@dataclass
class TimestampedAction:
    """Action with timestamp for append-only logging"""

    timestamp: datetime
    action_type: ActionType
    action_data: Dict[str, Any]
    agent_id: str
    session_id: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type.value,
            "action_data": self.action_data,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TimestampedAction":
        """Create from dictionary"""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            action_type=ActionType(data["action_type"]),
            action_data=data["action_data"],
            agent_id=data["agent_id"],
            session_id=data["session_id"],
        )


@dataclass
class Checkpoint:
    """Workflow checkpoint for pause/resume"""

    checkpoint_id: str
    timestamp: datetime
    phase: str
    progress: float
    state: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "checkpoint_id": self.checkpoint_id,
            "timestamp": self.timestamp.isoformat(),
            "phase": self.phase,
            "progress": self.progress,
            "state": self.state,
            "metadata": self.metadata,
        }


@dataclass
class BundleMetadata:
    """Metadata for context bundle"""

    created_at: datetime
    last_modified: datetime
    version: str = "1.0"
    agent_type: str = "unknown"
    task_description: str = ""
    parent_bundle_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "version": self.version,
            "agent_type": self.agent_type,
            "task_description": self.task_description,
            "parent_bundle_id": self.parent_bundle_id,
            "tags": self.tags,
        }


@dataclass
class ContextBundle:
    """Complete context bundle for session persistence"""

    session_id: str
    actions: List[TimestampedAction]
    state: Dict[str, Any]
    metadata: BundleMetadata
    checkpoints: List[Checkpoint] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "actions": [a.to_dict() for a in self.actions],
            "state": self.state,
            "metadata": self.metadata.to_dict(),
            "checkpoints": [c.to_dict() for c in self.checkpoints],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ContextBundle":
        """Create from dictionary"""
        return cls(
            session_id=data["session_id"],
            actions=[TimestampedAction.from_dict(a) for a in data["actions"]],
            state=data["state"],
            metadata=BundleMetadata(
                created_at=datetime.fromisoformat(data["metadata"]["created_at"]),
                last_modified=datetime.fromisoformat(data["metadata"]["last_modified"]),
                version=data["metadata"]["version"],
                agent_type=data["metadata"]["agent_type"],
                task_description=data["metadata"]["task_description"],
                parent_bundle_id=data["metadata"].get("parent_bundle_id"),
                tags=data["metadata"].get("tags", []),
            ),
            checkpoints=[
                Checkpoint(
                    checkpoint_id=c["checkpoint_id"],
                    timestamp=datetime.fromisoformat(c["timestamp"]),
                    phase=c["phase"],
                    progress=c["progress"],
                    state=c["state"],
                    metadata=c.get("metadata", {}),
                )
                for c in data.get("checkpoints", [])
            ],
        )

    def get_size_bytes(self) -> int:
        """Get bundle size in bytes"""
        return len(json.dumps(self.to_dict()).encode())

    def compress(self) -> bytes:
        """Compress bundle for storage"""
        json_str = json.dumps(self.to_dict())
        return gzip.compress(json_str.encode())

    @classmethod
    def decompress(cls, compressed_data: bytes) -> "ContextBundle":
        """Decompress and restore bundle"""
        json_str = gzip.decompress(compressed_data).decode()
        data = json.loads(json_str)
        return cls.from_dict(data)


class ContextBundleManager:
    """
    Manages context bundles for session persistence and perfect handoffs
    Implements Claude Code's append-only logging pattern
    """

    def __init__(self, session_id: str = None, storage_backend: str = "memory"):
        """
        Initialize bundle manager

        Args:
            session_id: Unique session identifier
            storage_backend: Storage type ("memory", "filesystem", "redis")
        """
        self.session_id = session_id or self.generate_session_id()
        self.storage_backend = storage_backend
        self.append_log: List[TimestampedAction] = []
        self.current_state: Dict[str, Any] = {}
        self.checkpoints: List[Checkpoint] = []
        self.metadata = BundleMetadata(
            created_at=datetime.now(), last_modified=datetime.now()
        )

        # Storage configuration
        if storage_backend == "filesystem":
            self.storage_path = Path(f"/tmp/context_bundles/{self.session_id}")
            self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory storage for quick access
        self._bundle_cache: OrderedDict[str, ContextBundle] = OrderedDict()
        self._max_cache_size = 10

    def generate_session_id(self) -> str:
        """Generate unique session ID with timestamp"""
        timestamp = datetime.now().isoformat()
        random_data = f"{timestamp}-{id(self)}"
        return hashlib.md5(random_data.encode()).hexdigest()[:16]

    def append_action(
        self,
        action_type: ActionType,
        action_data: Dict[str, Any],
        agent_id: str = "unknown",
    ):
        """
        Append action to log (append-only)

        Args:
            action_type: Type of action
            action_data: Action details
            agent_id: ID of agent performing action
        """
        action = TimestampedAction(
            timestamp=datetime.now(),
            action_type=action_type,
            action_data=action_data,
            agent_id=agent_id,
            session_id=self.session_id,
        )

        self.append_log.append(action)
        self.metadata.last_modified = datetime.now()

        # Auto-persist if using filesystem
        if self.storage_backend == "filesystem":
            self._persist_action(action)

    def _persist_action(self, action: TimestampedAction):
        """Persist single action to storage"""
        if self.storage_backend == "filesystem":
            action_file = self.storage_path / f"action_{len(self.append_log)}.json"
            with open(action_file, "w") as f:
                json.dump(action.to_dict(), f)

    def update_state(self, state_updates: Dict[str, Any]):
        """
        Update current state

        Args:
            state_updates: State changes to apply
        """
        self.current_state.update(state_updates)
        self.append_action(
            ActionType.STATE_CHANGE,
            {"state_updates": state_updates},
            agent_id="bundle_manager",
        )

    def create_checkpoint(
        self, phase: str, progress: float, metadata: Dict[str, Any] = None
    ) -> str:
        """
        Create workflow checkpoint

        Args:
            phase: Current workflow phase
            progress: Progress percentage (0.0 - 1.0)
            metadata: Additional checkpoint metadata

        Returns:
            Checkpoint ID
        """
        checkpoint_id = f"checkpoint_{len(self.checkpoints) + 1}"

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now(),
            phase=phase,
            progress=progress,
            state=self.current_state.copy(),
            metadata=metadata or {},
        )

        self.checkpoints.append(checkpoint)

        self.append_action(
            ActionType.CHECKPOINT,
            {"checkpoint_id": checkpoint_id, "phase": phase, "progress": progress},
            agent_id="bundle_manager",
        )

        return checkpoint_id

    def create_bundle_snapshot(self) -> ContextBundle:
        """
        Create immutable context bundle snapshot

        Returns:
            ContextBundle snapshot
        """
        bundle = ContextBundle(
            session_id=self.session_id,
            actions=self.append_log.copy(),
            state=self.current_state.copy(),
            metadata=self.metadata,
            checkpoints=self.checkpoints.copy(),
        )

        # Cache bundle
        self._bundle_cache[self.session_id] = bundle
        if len(self._bundle_cache) > self._max_cache_size:
            self._bundle_cache.popitem(last=False)

        return bundle

    async def save_bundle(self, bundle: ContextBundle = None) -> bool:
        """
        Save bundle to storage

        Args:
            bundle: Bundle to save (or create snapshot)

        Returns:
            Success status
        """
        if bundle is None:
            bundle = self.create_bundle_snapshot()

        try:
            if self.storage_backend == "memory":
                self._bundle_cache[bundle.session_id] = bundle

            elif self.storage_backend == "filesystem":
                bundle_file = self.storage_path / "bundle.json.gz"
                compressed = bundle.compress()
                with open(bundle_file, "wb") as f:
                    f.write(compressed)

            elif self.storage_backend == "redis":
                # Redis implementation would go here
                pass

            return True

        except Exception as e:
            print(f"Failed to save bundle: {e}")
            return False

    async def load_bundle(self, session_id: str) -> Optional[ContextBundle]:
        """
        Load bundle from storage

        Args:
            session_id: Session ID to load

        Returns:
            ContextBundle or None if not found
        """
        try:
            # Check cache first
            if session_id in self._bundle_cache:
                return self._bundle_cache[session_id]

            if self.storage_backend == "memory":
                return self._bundle_cache.get(session_id)

            elif self.storage_backend == "filesystem":
                bundle_path = Path(f"/tmp/context_bundles/{session_id}/bundle.json.gz")
                if bundle_path.exists():
                    with open(bundle_path, "rb") as f:
                        compressed = f.read()
                    bundle = ContextBundle.decompress(compressed)
                    self._bundle_cache[session_id] = bundle
                    return bundle

            elif self.storage_backend == "redis":
                # Redis implementation would go here
                pass

        except Exception as e:
            print(f"Failed to load bundle: {e}")

        return None

    async def remount_context(self, bundle: ContextBundle) -> bool:
        """
        Re-mount context from bundle (perfect restoration)

        Args:
            bundle: Bundle to remount

        Returns:
            Success status
        """
        try:
            # Restore all state
            self.session_id = bundle.session_id
            self.append_log = bundle.actions.copy()
            self.current_state = bundle.state.copy()
            self.metadata = bundle.metadata
            self.checkpoints = bundle.checkpoints.copy()

            # Log remount action
            self.append_action(
                ActionType.STATE_CHANGE,
                {"event": "context_remounted", "from_session": bundle.session_id},
                agent_id="bundle_manager",
            )

            return True

        except Exception as e:
            print(f"Failed to remount context: {e}")
            return False

    def get_action_history(
        self, action_type: ActionType = None, limit: int = None
    ) -> List[TimestampedAction]:
        """
        Get action history

        Args:
            action_type: Filter by action type
            limit: Maximum number of actions

        Returns:
            List of actions
        """
        actions = self.append_log

        if action_type:
            actions = [a for a in actions if a.action_type == action_type]

        if limit:
            actions = actions[-limit:]

        return actions

    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """Get most recent checkpoint"""
        return self.checkpoints[-1] if self.checkpoints else None

    def restore_from_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Restore state from checkpoint

        Args:
            checkpoint_id: Checkpoint to restore

        Returns:
            Success status
        """
        for checkpoint in self.checkpoints:
            if checkpoint.checkpoint_id == checkpoint_id:
                self.current_state = checkpoint.state.copy()

                self.append_action(
                    ActionType.STATE_CHANGE,
                    {
                        "event": "restored_from_checkpoint",
                        "checkpoint_id": checkpoint_id,
                    },
                    agent_id="bundle_manager",
                )

                return True

        return False

    def get_bundle_stats(self) -> Dict[str, Any]:
        """Get bundle statistics"""
        bundle = self.create_bundle_snapshot()

        return {
            "session_id": self.session_id,
            "total_actions": len(self.append_log),
            "total_checkpoints": len(self.checkpoints),
            "size_bytes": bundle.get_size_bytes(),
            "size_mb": bundle.get_size_bytes() / (1024 * 1024),
            "created_at": self.metadata.created_at.isoformat(),
            "last_modified": self.metadata.last_modified.isoformat(),
            "action_types": self._count_action_types(),
            "latest_checkpoint": self.get_latest_checkpoint().checkpoint_id
            if self.checkpoints
            else None,
        }

    def _count_action_types(self) -> Dict[str, int]:
        """Count actions by type"""
        counts = {}
        for action in self.append_log:
            action_type = action.action_type.value
            counts[action_type] = counts.get(action_type, 0) + 1
        return counts

    def cleanup_old_bundles(self, max_age_hours: int = 24):
        """
        Clean up old bundles

        Args:
            max_age_hours: Maximum age in hours
        """
        if self.storage_backend == "filesystem":
            base_path = Path("/tmp/context_bundles")
            if base_path.exists():
                for session_path in base_path.iterdir():
                    if session_path.is_dir():
                        bundle_file = session_path / "bundle.json.gz"
                        if bundle_file.exists():
                            age_hours = (
                                datetime.now()
                                - datetime.fromtimestamp(bundle_file.stat().st_mtime)
                            ).total_seconds() / 3600
                            if age_hours > max_age_hours:
                                import shutil

                                shutil.rmtree(session_path)


class BundleEnabledAgent(BaseAgent):
    """
    Agent with integrated Context Bundle support for perfect handoffs
    """

    def __init__(self, agent_id: str = None, session_id: str = None):
        """Initialize agent with bundle support"""
        super().__init__(agent_id)
        self.bundle_manager = ContextBundleManager(
            session_id=session_id, storage_backend="filesystem"
        )
        self.bundle_manager.metadata.agent_type = self.__class__.__name__

    async def execute_task(self, task: str) -> ToolResponse:
        """Execute task with bundle tracking"""
        # Log task execution
        self.bundle_manager.append_action(
            ActionType.TASK_EXECUTION,
            {"task": task, "start_time": datetime.now().isoformat()},
            self.agent_id,
        )

        try:
            # Create initial checkpoint
            checkpoint_id = self.bundle_manager.create_checkpoint(
                phase="task_started", progress=0.0, metadata={"task": task}
            )

            # Execute task (to be implemented by subclasses)
            result = await self._execute_task_impl(task)

            # Log result
            self.bundle_manager.append_action(
                ActionType.RESULT,
                {"result": result.data if isinstance(result, ToolResponse) else result},
                self.agent_id,
            )

            # Final checkpoint
            self.bundle_manager.create_checkpoint(
                phase="task_completed",
                progress=1.0,
                metadata={"result_summary": "success"},
            )

            # Save bundle
            await self.bundle_manager.save_bundle()

            return result

        except Exception as e:
            # Log error
            self.bundle_manager.append_action(
                ActionType.ERROR, {"error": str(e), "task": task}, self.agent_id
            )

            # Error checkpoint
            self.bundle_manager.create_checkpoint(
                phase="task_failed",
                progress=self.workflow_data.get("progress", 0),
                metadata={"error": str(e)},
            )

            await self.bundle_manager.save_bundle()
            raise

    async def _execute_task_impl(self, task: str) -> ToolResponse:
        """Task implementation (override in subclasses)"""
        raise NotImplementedError

    async def create_handoff(
        self, target_agent_id: str, handoff_data: Dict[str, Any]
    ) -> str:
        """
        Create handoff bundle for another agent

        Args:
            target_agent_id: Target agent ID
            handoff_data: Data to include in handoff

        Returns:
            Handoff bundle session ID
        """
        # Log handoff
        self.bundle_manager.append_action(
            ActionType.HANDOFF,
            {
                "from_agent": self.agent_id,
                "to_agent": target_agent_id,
                "handoff_data": handoff_data,
            },
            self.agent_id,
        )

        # Update metadata
        self.bundle_manager.metadata.task_description = f"Handoff to {target_agent_id}"
        self.bundle_manager.metadata.tags.append("handoff")

        # Create and save bundle
        bundle = self.bundle_manager.create_bundle_snapshot()
        await self.bundle_manager.save_bundle(bundle)

        return bundle.session_id

    async def receive_handoff(self, handoff_session_id: str) -> bool:
        """
        Receive handoff from another agent

        Args:
            handoff_session_id: Session ID of handoff bundle

        Returns:
            Success status
        """
        # Load handoff bundle
        bundle = await self.bundle_manager.load_bundle(handoff_session_id)

        if bundle:
            # Remount context
            success = await self.bundle_manager.remount_context(bundle)

            if success:
                # Log receipt
                self.bundle_manager.append_action(
                    ActionType.HANDOFF,
                    {
                        "event": "handoff_received",
                        "from_session": handoff_session_id,
                        "to_agent": self.agent_id,
                    },
                    self.agent_id,
                )

                # Update workflow data
                self.workflow_data.update(bundle.state)

                return True

        return False

    def get_handoff_summary(self) -> Dict[str, Any]:
        """Get summary for handoff documentation"""
        stats = self.bundle_manager.get_bundle_stats()
        latest_checkpoint = self.bundle_manager.get_latest_checkpoint()

        return {
            "session_id": self.bundle_manager.session_id,
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "total_actions": stats["total_actions"],
            "checkpoints": stats["total_checkpoints"],
            "current_phase": latest_checkpoint.phase
            if latest_checkpoint
            else "unknown",
            "progress": latest_checkpoint.progress if latest_checkpoint else 0,
            "state_summary": {
                k: type(v).__name__
                for k, v in self.bundle_manager.current_state.items()
            },
            "action_summary": stats["action_types"],
            "created_at": stats["created_at"],
            "last_modified": stats["last_modified"],
        }
