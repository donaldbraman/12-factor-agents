"""Unified Status Manager - Factor 5: Unify State"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class StatusManager:
    """Centralized status management for all agents"""

    _instances: Dict[str, "StatusManager"] = {}

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.status_file = Path(f"/tmp/{agent_id}_status.json")
        self.history = []

    @classmethod
    def get_instance(cls, agent_id: str) -> "StatusManager":
        """Get or create status manager instance"""
        if agent_id not in cls._instances:
            cls._instances[agent_id] = cls(agent_id)
        return cls._instances[agent_id]

    def update(
        self, progress: int, message: str, data: Optional[Dict[str, Any]] = None
    ):
        """Update agent status with unified state"""
        status = {
            "agent_id": self.agent_id,
            "progress": progress,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
        }

        # Persist to file
        self.status_file.write_text(json.dumps(status, indent=2))

        # Keep history
        self.history.append(status)

        return status

    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        if self.status_file.exists():
            return json.loads(self.status_file.read_text())
        return {"progress": 0, "message": "Not started"}

    @classmethod
    def get_all_statuses(cls) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents"""
        statuses = {}
        for status_file in Path("/tmp").glob("*_status.json"):
            try:
                agent_id = status_file.stem.replace("_status", "")
                statuses[agent_id] = json.loads(status_file.read_text())
            except:
                pass
        return statuses
