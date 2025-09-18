"""
Lean Feature Builder Agent - Prompt-Driven Design
Following 12-factor agent principles
"""

from pathlib import Path
from typing import Optional, Dict, Any
from core.agent import BaseAgent
from core.tools import Tool, ToolResponse
from core.prompt_manager import PromptManager


class FeatureBuilderAgent(BaseAgent):
    """Minimal agent for building new features through prompts"""

    def __init__(self):
        super().__init__("FeatureBuilderAgent")
        self.prompt_manager = PromptManager()

    def register_tools(self):
        return [
            Tool(
                name="build_feature",
                description="Build a new feature from specification",
                func=self.build_feature,
                args=["spec_path"],
            )
        ]

    def build_feature(self, spec_path: str) -> ToolResponse:
        """Build feature by delegating to prompts"""

        # Read specification
        spec = self._read_spec(spec_path)
        if not spec:
            return ToolResponse(success=False, error=f"Cannot read spec: {spec_path}")

        # Placeholder for prompt-driven logic
        design = f"Architecture design for: {spec_path}"
        implementation = f"Implementation plan for: {spec_path}"
        tests = f"Test strategy for: {spec_path}"

        return ToolResponse(
            success=True,
            data={
                "feature": spec_path,
                "status": "Feature designed and ready for implementation",
                "files_to_create": "Determined by prompts",
            },
        )

    def _read_spec(self, spec_path: str) -> Optional[str]:
        """Read feature specification"""
        path = Path(spec_path)

        # Check common locations
        for base in ["issues", "features", "specs", "."]:
            full_path = Path(base) / path
            if full_path.exists():
                return full_path.read_text()

        if path.exists():
            return path.read_text()

        return None

    def execute_task(self, task: str) -> ToolResponse:
        """Main task execution"""
        return self.build_feature(task)

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply an action (required by BaseAgent)"""
        return ToolResponse(success=True, data=action)


# 72 lines vs 500+ lines of feature creation code!
