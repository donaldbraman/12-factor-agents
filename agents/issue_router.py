"""
Lean Issue Router - Routes issues to specialized agents
Following 12-factor principles: Simple, prompt-driven
"""

from pathlib import Path
from typing import Optional, Dict, Any
from core.agent import BaseAgent
from core.tools import Tool, ToolResponse
from core.prompt_manager import PromptManager
from agents.bug_fix_agent import BugFixAgent
from agents.feature_builder_agent import FeatureBuilderAgent


class IssueRouter(BaseAgent):
    """Ultra-lean router that dispatches to specialized agents"""

    def __init__(self):
        super().__init__("IssueRouter")
        self.prompt_manager = PromptManager()

        # Initialize specialized agents
        self.bug_fixer = BugFixAgent()
        self.feature_builder = FeatureBuilderAgent()

    def register_tools(self):
        return [
            Tool(
                name="process_issue",
                description="Route an issue to the appropriate specialized agent",
                func=self.process_issue,
                args=["issue_path"],
            )
        ]

    def process_issue(self, issue_path: str) -> ToolResponse:
        """Read issue and route to appropriate agent"""

        # Read the issue
        content = self._read_issue(issue_path)
        if not content:
            return ToolResponse(success=False, error=f"Cannot read: {issue_path}")

        # Use prompt to classify the issue
        classification = self._classify_issue(content)

        # Route to appropriate agent
        if classification == "bug":
            return self.bug_fixer.fix_bug(issue_path)
        elif classification == "feature":
            return self.feature_builder.build_feature(issue_path)
        elif classification == "quality":
            # Quality analyst would go here
            return ToolResponse(
                success=True,
                data={
                    "issue": issue_path,
                    "type": "quality",
                    "status": "Quality analysis pending",
                },
            )
        else:
            return ToolResponse(
                success=False, error=f"Unknown issue type: {classification}"
            )

    def _classify_issue(self, content: str) -> str:
        """Use prompt to classify issue type"""
        # In real implementation, this would call the prompt library
        # For now, simple keyword detection
        content_lower = content.lower()

        if any(
            word in content_lower for word in ["bug", "error", "fix", "broken", "crash"]
        ):
            return "bug"
        elif any(
            word in content_lower
            for word in ["feature", "implement", "add", "create new"]
        ):
            return "feature"
        elif any(
            word in content_lower
            for word in ["quality", "analysis", "pattern", "metrics"]
        ):
            return "quality"
        else:
            return "unknown"

    def _read_issue(self, issue_path: str) -> Optional[str]:
        """Read issue file from common locations"""
        path = Path(issue_path)

        # Try common locations
        for base in ["issues", ".", "docs"]:
            full_path = Path(base) / path
            if full_path.exists():
                return full_path.read_text()

        if path.exists():
            return path.read_text()

        return None

    def execute_task(self, task: str) -> ToolResponse:
        """Main task execution entry point"""
        # Extract issue path from task
        if "issues/" in task:
            issue_path = task.split("issues/")[-1]
            issue_path = f"issues/{issue_path.split()[0]}"
        else:
            issue_path = task

        return self.process_issue(issue_path)

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply an action (required by BaseAgent)"""
        return ToolResponse(success=True, data=action)


# 87 lines! The router is simple and delegates to specialized agents
