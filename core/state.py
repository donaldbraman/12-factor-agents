"""
Unified state management for agents.
Factor 5: Unify execution state and business state.
"""

from typing import Dict, Any, List
from datetime import datetime
from copy import deepcopy


class UnifiedState:
    """
    Unified state container that merges execution and business state.

    Execution state: Tool results, errors, system state
    Business state: Domain-specific data, user context
    """

    def __init__(self):
        self.execution_state: Dict[str, Any] = {}
        self.business_state: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
        }

    def update(self, tool_response: "ToolResponse"):
        """Update both states atomically from tool response"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "success": tool_response.success,
        }

        if tool_response.success:
            # Update business state with tool data
            if hasattr(tool_response, "data") and tool_response.data:
                self.business_state.update(tool_response.data)
                entry["data"] = tool_response.data

            # Update execution state with metadata
            if hasattr(tool_response, "metadata") and tool_response.metadata:
                self.execution_state.update(tool_response.metadata)
                entry["metadata"] = tool_response.metadata
        else:
            # Track error in execution state
            entry["error"] = getattr(tool_response, "error", "Unknown error")
            self.execution_state["last_error"] = entry["error"]
            self.execution_state["error_count"] = (
                self.execution_state.get("error_count", 0) + 1
            )

        # Add to history
        self.history.append(entry)

        # Maintain history size limit
        if len(self.history) > 100:
            self.history = self.history[-100:]

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from unified state (business state takes precedence)"""
        if key in self.business_state:
            return self.business_state[key]
        elif key in self.execution_state:
            return self.execution_state[key]
        return default

    def set(self, key: str, value: Any, state_type: str = "business"):
        """Set value in specified state"""
        if state_type == "business":
            self.business_state[key] = value
        elif state_type == "execution":
            self.execution_state[key] = value
        else:
            raise ValueError(f"Invalid state_type: {state_type}")

    def copy(self) -> "UnifiedState":
        """Create deep copy of state"""
        new_state = UnifiedState()
        new_state.execution_state = deepcopy(self.execution_state)
        new_state.business_state = deepcopy(self.business_state)
        new_state.history = deepcopy(self.history)
        new_state.metadata = deepcopy(self.metadata)
        return new_state

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary"""
        return {
            "execution_state": self.execution_state,
            "business_state": self.business_state,
            "history": self.history,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedState":
        """Deserialize state from dictionary"""
        state = cls()
        state.execution_state = data.get("execution_state", {})
        state.business_state = data.get("business_state", {})
        state.history = data.get("history", [])
        state.metadata = data.get("metadata", {})
        return state

    def get_summary(self) -> Dict[str, Any]:
        """Get concise summary of current state"""
        return {
            "business_keys": list(self.business_state.keys()),
            "execution_keys": list(self.execution_state.keys()),
            "history_length": len(self.history),
            "error_count": self.execution_state.get("error_count", 0),
            "last_update": self.history[-1]["timestamp"] if self.history else None,
        }

    def clear_errors(self):
        """Clear error state"""
        self.execution_state.pop("last_error", None)
        self.execution_state["error_count"] = 0

    def get_recent_history(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get n most recent history entries"""
        return self.history[-n:] if self.history else []
