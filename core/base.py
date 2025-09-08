"""
Base classes for 12-factor agents framework
Provides foundation for all agent implementations
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json
import asyncio
from datetime import datetime


@dataclass
class ToolResponse:
    """Structured response from tool execution"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentState(Enum):
    """Agent lifecycle states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseAgent:
    """
    Base class for all 12-factor compliant agents
    Implements core functionality for state management and workflow execution
    """
    
    def __init__(self, agent_id: str = None):
        """Initialize base agent with unique ID"""
        self.agent_id = agent_id or self._generate_agent_id()
        self.state = AgentState.IDLE
        self.workflow_data = {}
        self.checkpoints = []
        self.context = {}
        self.logs = []
        
    def _generate_agent_id(self) -> str:
        """Generate unique agent ID"""
        import hashlib
        timestamp = datetime.now().isoformat()
        return f"agent_{hashlib.md5(timestamp.encode()).hexdigest()[:8]}"
    
    async def execute_task(self, task: str) -> ToolResponse:
        """Execute a task - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement execute_task")
    
    def set_context(self, context: Dict[str, Any]):
        """Set agent context"""
        self.context = context
        self.workflow_data.update(context)
    
    async def get_current_context(self) -> Dict[str, Any]:
        """Get current agent context"""
        return self.workflow_data
    
    def set_progress(self, progress: float, phase: str = None):
        """Set workflow progress"""
        self.workflow_data["progress"] = progress
        if phase:
            self.workflow_data["current_phase"] = phase
        self.log_info(f"Progress: {progress*100:.1f}% - {phase or 'Processing'}")
    
    def log_info(self, message: str):
        """Log information message"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": message,
            "agent_id": self.agent_id
        }
        self.logs.append(log_entry)
        print(f"[{self.agent_id}] {message}")
    
    def log_error(self, message: str, error: Exception = None):
        """Log error message"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "ERROR",
            "message": message,
            "agent_id": self.agent_id,
            "error": str(error) if error else None
        }
        self.logs.append(log_entry)
        print(f"[{self.agent_id}] ERROR: {message}")
    
    async def checkpoint(self) -> str:
        """Create workflow checkpoint"""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "state": self.state.value,
            "workflow_data": self.workflow_data.copy(),
            "context": self.context.copy()
        }
        self.checkpoints.append(checkpoint)
        return f"checkpoint_{len(self.checkpoints)}"
    
    async def restore_checkpoint(self, checkpoint_id: str):
        """Restore from checkpoint"""
        # Find checkpoint by ID or index
        if checkpoint_id.startswith("checkpoint_"):
            index = int(checkpoint_id.split("_")[1]) - 1
            if 0 <= index < len(self.checkpoints):
                checkpoint = self.checkpoints[index]
                self.workflow_data = checkpoint["workflow_data"].copy()
                self.context = checkpoint["context"].copy()
                self.state = AgentState(checkpoint["state"])
                return True
        return False
    
    async def pause(self):
        """Pause agent execution"""
        self.state = AgentState.PAUSED
        await self.checkpoint()
        self.log_info("Agent paused")
    
    async def resume(self):
        """Resume agent execution"""
        if self.state == AgentState.PAUSED:
            self.state = AgentState.RUNNING
            self.log_info("Agent resumed")
    
    async def persist_state(self):
        """Persist agent state - placeholder for external state management"""
        # This would connect to external state store (Redis, etc.)
        state_data = {
            "agent_id": self.agent_id,
            "state": self.state.value,
            "workflow_data": self.workflow_data,
            "checkpoints": self.checkpoints
        }
        # For now, just return the state
        return state_data
    
    def is_stateless_reducer(self) -> bool:
        """Check if agent follows stateless reducer pattern"""
        # Agents should not maintain internal state beyond workflow data
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "state": self.state.value,
            "progress": self.workflow_data.get("progress", 0),
            "current_phase": self.workflow_data.get("current_phase", "idle"),
            "checkpoints": len(self.checkpoints),
            "logs": len(self.logs)
        }


class AgentError(Exception):
    """Custom exception for agent errors"""
    def __init__(self, message: str, context: Dict[str, Any] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)