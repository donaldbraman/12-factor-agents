"""
Unified Status Management System
Single source of truth for all agent status tracking
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


class TaskStatus(Enum):
    """Unified status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass
class StatusUpdate:
    """Unified status update structure"""

    status: TaskStatus
    timestamp: datetime = field(default_factory=datetime.now)
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    progress_percent: int = 0


class UnifiedStatusManager:
    """
    Single status manager for all agents to eliminate scattered implementations
    """

    def __init__(self):
        self.statuses: Dict[str, StatusUpdate] = {}
        self.history: Dict[str, list] = {}

    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        message: str = "",
        progress: int = 0,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Update task status"""
        update = StatusUpdate(
            status=status,
            message=message,
            metadata=metadata or {},
            progress_percent=max(0, min(100, progress)),
        )

        # Store current status
        self.statuses[task_id] = update

        # Add to history
        if task_id not in self.history:
            self.history[task_id] = []
        self.history[task_id].append(update)

        # Limit history to last 10 updates
        if len(self.history[task_id]) > 10:
            self.history[task_id] = self.history[task_id][-10:]

    def get_status(self, task_id: str) -> Optional[StatusUpdate]:
        """Get current status of task"""
        return self.statuses.get(task_id)

    def get_history(self, task_id: str) -> list:
        """Get status history for task"""
        return self.history.get(task_id, [])

    def is_complete(self, task_id: str) -> bool:
        """Check if task is complete"""
        status = self.get_status(task_id)
        return status and status.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]

    def get_all_active(self) -> Dict[str, StatusUpdate]:
        """Get all active (non-complete) tasks"""
        return {
            task_id: status
            for task_id, status in self.statuses.items()
            if not self.is_complete(task_id)
        }

    def cleanup_completed(self, older_than_hours: int = 24) -> int:
        """Clean up completed tasks older than specified hours"""
        cutoff = datetime.now() - datetime.timedelta(hours=older_than_hours)
        removed = 0

        to_remove = []
        for task_id, status in self.statuses.items():
            if self.is_complete(task_id) and status.timestamp < cutoff:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.statuses[task_id]
            if task_id in self.history:
                del self.history[task_id]
            removed += 1

        return removed

    def to_dict(self) -> Dict[str, Any]:
        """Export status data for persistence"""
        return {
            "statuses": {
                task_id: {
                    "status": status.status.value,
                    "timestamp": status.timestamp.isoformat(),
                    "message": status.message,
                    "metadata": status.metadata,
                    "progress_percent": status.progress_percent,
                }
                for task_id, status in self.statuses.items()
            }
        }


# Global instance for shared use
GLOBAL_STATUS_MANAGER = UnifiedStatusManager()


def get_status_manager() -> UnifiedStatusManager:
    """Get the global status manager instance"""
    return GLOBAL_STATUS_MANAGER
