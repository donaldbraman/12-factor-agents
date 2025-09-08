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
        
        # Enhanced progress tracking (pin-citer pattern)
        self.progress = 0.0
        self.current_stage = None
        self.total_stages = 1
        self.workflow_data = {}
        self.error_context = None
        self.files_modified = []
        self.branch = None
        self.issue_number = None
        
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
        """
        Save enhanced agent state to disk for persistence.
        Based on pin-citer's sophisticated checkpoint system.
        """
        checkpoint = {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "status": self.status,
            "progress": self.progress,
            "current_stage": self.current_stage,
            "total_stages": self.total_stages,
            "state": self.state.to_dict(),
            "workflow_data": self.workflow_data,
            "files_modified": self.files_modified,
            "branch": self.branch,
            "issue_number": self.issue_number,
            "created_at": self.created_at.isoformat(),
            "last_checkpoint": datetime.now().isoformat()
        }
        
        # Add error context if present (pin-citer pattern)
        if self.error_context:
            checkpoint["error"] = self.error_context
            checkpoint["error_details"] = {
                "timestamp": datetime.now().isoformat(),
                "stage": self.current_stage,
                "progress": self.progress,
                "context": getattr(self, '_last_operation', 'Unknown operation')
            }
        
        self.checkpoint_path.write_text(
            json.dumps(checkpoint, indent=2)
        )
    
    def load_checkpoint(self) -> bool:
        """
        Restore enhanced agent state from disk.
        Compatible with pin-citer's checkpoint format.
        """
        if not self.checkpoint_path.exists():
            return False
            
        try:
            data = json.loads(self.checkpoint_path.read_text())
            
            # Core fields
            self.agent_id = data["agent_id"]
            self.status = data["status"]
            self.state = UnifiedState.from_dict(data["state"])
            self.created_at = datetime.fromisoformat(data["created_at"])
            
            # Enhanced fields (with backward compatibility)
            self.progress = data.get("progress", 0.0)
            self.current_stage = data.get("current_stage", None)
            self.total_stages = data.get("total_stages", 1)
            self.workflow_data = data.get("workflow_data", {})
            self.files_modified = data.get("files_modified", [])
            self.branch = data.get("branch", None)
            self.issue_number = data.get("issue_number", None)
            self.error_context = data.get("error", None)
            
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
        """Get enhanced agent status for monitoring (pin-citer pattern)"""
        status = {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "status": self.status,
            "progress": self.progress,
            "current_stage": self.current_stage,
            "total_stages": self.total_stages,
            "created_at": self.created_at.isoformat(),
            "state_summary": self.state.get_summary()
        }
        
        # Add workflow-specific data if available
        if self.workflow_data:
            status["workflow_data"] = self.workflow_data
        if self.files_modified:
            status["files_modified"] = self.files_modified
        if self.branch:
            status["branch"] = self.branch
        if self.issue_number:
            status["issue_number"] = self.issue_number
        if self.error_context:
            status["error"] = self.error_context
            
        return status
    
    # Progress tracking methods (inspired by pin-citer)
    def set_progress(self, progress: float, stage: str = None):
        """Update agent progress (0.0 to 1.0)"""
        self.progress = max(0.0, min(1.0, progress))
        if stage:
            self.current_stage = stage
        self.save_checkpoint()
    
    def increment_progress(self, increment: float = None):
        """Increment progress by stage amount or custom increment"""
        if increment is None:
            increment = 1.0 / self.total_stages if self.total_stages > 0 else 0.1
        self.set_progress(self.progress + increment)
    
    def set_workflow_stages(self, stages: List[str]):
        """Set up multi-stage workflow (pin-citer pipeline pattern)"""
        self.total_stages = len(stages)
        self.workflow_data["stages"] = stages
        self.workflow_data["stage_index"] = 0
        self.progress = 0.0
        self.current_stage = stages[0] if stages else None
        self.save_checkpoint()
    
    def advance_stage(self):
        """Advance to next workflow stage"""
        if "stages" in self.workflow_data:
            current_index = self.workflow_data.get("stage_index", 0)
            stages = self.workflow_data["stages"]
            
            if current_index < len(stages) - 1:
                current_index += 1
                self.workflow_data["stage_index"] = current_index
                self.current_stage = stages[current_index]
                self.progress = current_index / len(stages)
                self.save_checkpoint()
                return True
        return False
    
    def add_file_modified(self, file_path: str):
        """Track files modified during agent execution"""
        if file_path not in self.files_modified:
            self.files_modified.append(file_path)
            self.save_checkpoint()
    
    def set_git_context(self, branch: str = None, issue_number: int = None):
        """Set Git/GitHub context for workflow tracking"""
        if branch:
            self.branch = branch
        if issue_number:
            self.issue_number = issue_number
        self.save_checkpoint()
    
    def handle_error(self, error: Exception, operation: str = None):
        """Enhanced error handling with context (pin-citer pattern)"""
        self.error_context = str(error)
        self.status = "failed"
        self._last_operation = operation or "Unknown operation"
        
        # Add error to state for history tracking
        self.state.set("last_error", {
            "message": str(error),
            "operation": operation,
            "stage": self.current_stage,
            "progress": self.progress,
            "timestamp": datetime.now().isoformat()
        }, "execution")
        
        self.save_checkpoint()
    
    def clear_error(self):
        """Clear error state for retry attempts"""
        self.error_context = None
        self.status = "running"
        self.state.clear_errors()
        self.save_checkpoint()
    
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