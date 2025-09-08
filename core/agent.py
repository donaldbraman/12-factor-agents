"""
Base Agent class implementing 12-factor methodology.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
from datetime import datetime

from .state import UnifiedState
from .context import ContextManager
from .prompt_manager import PromptManager
from .tools import Tool, ToolResponse


class BaseAgent(ABC):
    """
    Base class for all 12-factor agents.
    
    Implements core functionality:
    - State management (Factor 5)
    - Context window management (Factor 3)
    - Checkpoint/resume (Factor 6)
    - Structured tool responses (Factor 4)
    - Control flow ownership (Factor 8)
    """
    
    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or self._generate_id()
        self.state = UnifiedState()
        self.context_manager = ContextManager()
        self.prompt_manager = PromptManager()
        self.tools = self.register_tools()
        self.checkpoint_path = Path(f".claude/agents/checkpoints/{self.agent_id}.json")
        self.status = "idle"
        self.created_at = datetime.now()
        
        # Load prompts after tools are registered
        self._load_agent_prompt()
        
        # Ensure checkpoint directory exists
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        
    def _generate_id(self) -> str:
        """Generate unique agent ID"""
        from uuid import uuid4
        return f"{self.__class__.__name__}_{uuid4().hex[:8]}"
    
    @abstractmethod
    def register_tools(self) -> List[Tool]:
        """
        Register agent-specific tools.
        Factor 4: Tools are structured outputs.
        """
        pass
    
    @abstractmethod
    def execute_task(self, task: str) -> ToolResponse:
        """
        Execute the agent's primary task.
        Factor 10: Small, focused agents with single responsibility.
        """
        pass
    
    def launch(self, task: str) -> ToolResponse:
        """
        Launch agent execution.
        Factor 6: Simple launch API.
        """
        self.status = "running"
        self.save_checkpoint()
        
        try:
            result = self.execute_task(task)
            self.status = "completed"
            return result
        except Exception as e:
            self.status = "error"
            return ToolResponse(
                success=False,
                error=str(e),
                metadata={"agent_id": self.agent_id}
            )
        finally:
            self.save_checkpoint()
    
    def pause(self):
        """
        Pause agent execution.
        Factor 6: Simple pause API.
        """
        self.status = "paused"
        self.save_checkpoint()
    
    def resume(self) -> bool:
        """
        Resume agent execution.
        Factor 6: Simple resume API.
        """
        if self.load_checkpoint():
            self.status = "running"
            return True
        return False
    
    def save_checkpoint(self):
        """Save agent state to disk for persistence"""
        checkpoint = {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "status": self.status,
            "state": self.state.to_dict(),
            "created_at": self.created_at.isoformat(),
            "last_checkpoint": datetime.now().isoformat()
        }
        
        self.checkpoint_path.write_text(
            json.dumps(checkpoint, indent=2)
        )
    
    def load_checkpoint(self) -> bool:
        """Restore agent state from disk"""
        if not self.checkpoint_path.exists():
            return False
            
        try:
            data = json.loads(self.checkpoint_path.read_text())
            self.agent_id = data["agent_id"]
            self.status = data["status"]
            self.state = UnifiedState.from_dict(data["state"])
            self.created_at = datetime.fromisoformat(data["created_at"])
            return True
        except Exception:
            return False
    
    def add_context(self, content: str, priority: int = 5):
        """
        Add information to context window.
        Factor 3: Own your context window.
        """
        self.context_manager.add_context(content, priority)
    
    def get_prompt(self) -> str:
        """Build complete prompt with managed context"""
        return self.context_manager.build_prompt()
    
    def reduce(self, action: Dict[str, Any]) -> ToolResponse:
        """
        Stateless reducer pattern.
        Factor 12: Implement as predictable state transformer.
        """
        old_state = self.state.copy()
        
        try:
            # Apply action to state
            result = self._apply_action(action)
            
            # Update state based on result
            self.state.update(result)
            
            return result
        except Exception as e:
            # Restore old state on error
            self.state = old_state
            return ToolResponse(
                success=False,
                error=str(e)
            )
    
    @abstractmethod
    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply action and return result"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status for monitoring"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "state_summary": self.state.get_summary()
        }
    
    def _load_agent_prompt(self):
        """Load agent-specific prompt template"""
        agent_name = self.__class__.__name__.replace("Agent", "").lower()
        
        # Try to load specialized prompt
        prompt = self.prompt_manager.get_prompt(
            f"specialized/{agent_name}",
            agent_type=self.__class__.__name__,
            agent_id=self.agent_id
        )
        
        if prompt:
            self.context_manager.set_system_prompt(prompt)
        else:
            # Fall back to base prompt
            base_prompt = self.prompt_manager.get_prompt(
                "base/system",
                agent_type=self.__class__.__name__,
                responsibility="General task execution",
                tools_list=", ".join([t.name for t in self.tools]) if self.tools else "",
                context="",
                task=""
            )
            if base_prompt:
                self.context_manager.set_system_prompt(base_prompt)
    
    def set_prompt_variables(self, **variables):
        """Update prompt with new variables"""
        agent_name = self.__class__.__name__.replace("Agent", "").lower()
        prompt = self.prompt_manager.get_prompt(
            f"specialized/{agent_name}",
            **variables
        )
        if prompt:
            self.context_manager.set_system_prompt(prompt)