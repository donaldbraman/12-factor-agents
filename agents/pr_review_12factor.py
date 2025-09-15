"""
PR Review Agent - Following 12-Factor Agent Principles
A small, focused agent (Factor 10) that can be triggered from anywhere (Factor 11)
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Factor 4: Tools are Structured Outputs
@dataclass
class PRData:
    """Structured PR data"""

    number: int
    title: str
    body: str
    author: str
    additions: int
    deletions: int
    diff: str
    url: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ReviewResult:
    """Structured review output"""

    summary: str
    quality_score: int
    approved: bool
    issues: list
    suggestions: list
    positive_feedback: list

    def to_dict(self) -> Dict:
        return asdict(self)


# Factor 1: Natural Language to Tool Calls
class PRFetchTool(Tool):
    """Fetch PR data - converts natural language to gh CLI calls"""

    def __init__(self):
        super().__init__(name="fetch_pr", description="Fetch PR data from GitHub")

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer"},
                "repo": {"type": "string"},
            },
            "required": ["pr_number"],
        }

    def execute(self, pr_number: int, repo: Optional[str] = None) -> ToolResponse:
        """Factor 9: Compact Errors into Context Window"""
        try:
            repo = repo or "donaldbraman/12-factor-agents"

            # Use gh CLI for stateless execution
            cmd = [
                "gh",
                "pr",
                "view",
                str(pr_number),
                "--repo",
                repo,
                "--json",
                "number,title,body,author,additions,deletions,url",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return ToolResponse(
                    success=False, error=f"GitHub CLI error: {result.stderr}"
                )

            data = json.loads(result.stdout)

            # Get diff separately
            diff_cmd = ["gh", "pr", "diff", str(pr_number), "--repo", repo]
            diff_result = subprocess.run(
                diff_cmd, capture_output=True, text=True, timeout=10
            )

            pr_data = PRData(
                number=data["number"],
                title=data["title"],
                body=data.get("body", ""),
                author=data.get("author", {}).get("login", "Unknown"),
                additions=data.get("additions", 0),
                deletions=data.get("deletions", 0),
                diff=diff_result.stdout[:10000] if diff_result.returncode == 0 else "",
                url=data.get("url", ""),
            )

            return ToolResponse(success=True, data=pr_data.to_dict())

        except subprocess.TimeoutExpired:
            return ToolResponse(success=False, error="GitHub API timeout")
        except Exception as e:
            return ToolResponse(success=False, error=str(e))


# Factor 7: Contact Humans with Tool Calls
class HumanReviewTool(Tool):
    """Request human review when needed"""

    def __init__(self):
        super().__init__(
            name="request_human_review",
            description="Request human intervention for complex cases",
        )

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer"},
                "reason": {"type": "string"},
            },
            "required": ["pr_number", "reason"],
        }

    def execute(self, pr_number: int, reason: str) -> ToolResponse:
        """Create a review request for human"""
        request_file = Path(f"/tmp/pr_{pr_number}_human_review.txt")
        request_file.write_text(f"PR #{pr_number} needs human review\nReason: {reason}")

        logger.info(f"Human review requested for PR #{pr_number}: {reason}")

        return ToolResponse(
            success=True, data={"requested": True, "file": str(request_file)}
        )


# Factor 12: Stateless Reducer
class AnalyzeTool(Tool):
    """Pure function for PR analysis - no side effects"""

    def __init__(self):
        super().__init__(name="analyze_pr", description="Analyze PR diff and metadata")

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"pr_data": {"type": "object"}},
            "required": ["pr_data"],
        }

    def execute(self, pr_data: Dict) -> ToolResponse:
        """Stateless analysis - pure transformation"""
        # Factor 2: Own Your Prompts - explicit analysis rules
        diff = pr_data.get("diff", "")

        issues = []
        suggestions = []
        positive = []

        # Simple heuristic analysis (in production, this would call Claude)
        if "TODO" in diff or "FIXME" in diff:
            issues.append(
                {"severity": "minor", "message": "Unresolved TODO/FIXME comments"}
            )

        if "console.log" in diff or "print(" in diff:
            suggestions.append("Replace debug output with proper logging")

        if not pr_data.get("body"):
            suggestions.append("Add detailed PR description")
        else:
            positive.append("Includes PR description")

        # Small changes are good
        if pr_data.get("additions", 0) < 200:
            positive.append("Small, focused change")
            quality_score = 8
        else:
            suggestions.append("Consider breaking into smaller PRs")
            quality_score = 6

        # Factor 5: Unify Execution and Business State
        review = ReviewResult(
            summary=f"PR #{pr_data.get('number')} by {pr_data.get('author')} - {pr_data.get('title')}",
            quality_score=quality_score,
            approved=quality_score >= 7,
            issues=issues,
            suggestions=suggestions or ["Add tests for new functionality"],
            positive_feedback=positive or ["Code is properly formatted"],
        )

        return ToolResponse(success=True, data=review.to_dict())


class PostCommentTool(Tool):
    """Post review comment to GitHub"""

    def __init__(self):
        super().__init__(name="post_comment", description="Post review comment")

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer"},
                "comment": {"type": "string"},
                "repo": {"type": "string"},
            },
            "required": ["pr_number", "comment"],
        }

    def execute(
        self, pr_number: int, comment: str, repo: Optional[str] = None
    ) -> ToolResponse:
        """Post comment using gh CLI"""
        try:
            repo = repo or "donaldbraman/12-factor-agents"

            cmd = [
                "gh",
                "pr",
                "comment",
                str(pr_number),
                "--repo",
                repo,
                "--body",
                comment,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return ToolResponse(success=False, error=result.stderr)

            return ToolResponse(success=True, data={"posted": True})

        except Exception as e:
            return ToolResponse(success=False, error=str(e))


# Factor 10: Small, Focused Agent
class TwelveFactorPRReviewAgent(BaseAgent):
    """
    Small, focused PR review agent following 12-factor principles
    Factor 6: Launch/Pause/Resume with Simple APIs (via BaseAgent)
    Factor 8: Own Your Control Flow
    """

    def __init__(self):
        self.name = "TwelveFactorPRReviewAgent"
        self.description = "12-factor compliant PR review"

        # Initialize tools
        self.fetch_tool = PRFetchTool()
        self.analyze_tool = AnalyzeTool()
        self.comment_tool = PostCommentTool()
        self.human_tool = HumanReviewTool()

        self.tools = [
            self.fetch_tool,
            self.analyze_tool,
            self.comment_tool,
            self.human_tool,
        ]

        super().__init__()

    def register_tools(self):
        """Register available tools"""
        return self.tools

    def _apply_action(self, action_name: str, **kwargs) -> Any:
        """Route action to appropriate tool"""
        tool_map = {
            "fetch_pr": self.fetch_tool,
            "analyze_pr": self.analyze_tool,
            "post_comment": self.comment_tool,
            "request_human_review": self.human_tool,
        }

        tool = tool_map.get(action_name)
        if tool:
            return tool.execute(**kwargs)
        return {"error": f"Unknown action: {action_name}"}

    def execute_task(self, task: str) -> Any:
        """
        Factor 1: Natural Language to Tool Calls
        Factor 8: Own Your Control Flow
        """
        # Parse natural language task
        import re

        pr_match = re.search(r"#?(\d+)", task)
        if not pr_match:
            return {"error": "No PR number found"}

        pr_number = int(pr_match.group(1))
        repo_match = re.search(r"in\s+([\w\-]+/[\w\-]+)", task)
        repo = repo_match.group(1) if repo_match else None

        # Factor 8: Own Your Control Flow - explicit steps
        workflow_state = {"step": "fetch", "pr_number": pr_number}

        try:
            # Step 1: Fetch PR
            logger.info(f"Fetching PR #{pr_number}...")
            fetch_result = self.fetch_tool.execute(pr_number, repo)

            if not fetch_result.success:
                # Factor 9: Compact Errors into Context
                return {"error": fetch_result.error, "step": "fetch"}

            pr_data = fetch_result.data
            workflow_state["step"] = "analyze"

            # Step 2: Analyze
            logger.info("Analyzing PR...")
            analysis = self.analyze_tool.execute(pr_data)

            if not analysis.success:
                return {"error": analysis.error, "step": "analyze"}

            review = analysis.data
            workflow_state["step"] = "decide"

            # Step 3: Decide if human review needed
            if review["quality_score"] < 5 or len(review["issues"]) > 5:
                # Factor 7: Contact Humans with Tool Calls
                self.human_tool.execute(
                    pr_number,
                    f"Low quality score ({review['quality_score']}) or many issues",
                )
                workflow_state["human_review_requested"] = True

            # Step 4: Post comment (if requested)
            if "post" in task.lower() or "comment" in task.lower():
                workflow_state["step"] = "comment"
                comment = self._format_comment(review)
                self.comment_tool.execute(pr_number, comment, repo)

            # Factor 12: Stateless Reducer - return complete state
            return {
                "pr_number": pr_number,
                "title": pr_data["title"],
                "quality_score": review["quality_score"],
                "approved": review["approved"],
                "workflow_state": workflow_state,
                "review": review,
            }

        except Exception as e:
            # Factor 9: Compact Errors into Context Window
            return {"error": str(e), "workflow_state": workflow_state}

    def _format_comment(self, review: Dict) -> str:
        """Format review as GitHub comment"""
        lines = ["## 🤖 12-Factor PR Review\n"]

        lines.append(f"**Summary:** {review['summary']}\n")

        score = review["quality_score"]
        emoji = "✅" if score >= 8 else "⚠️" if score >= 6 else "❌"
        lines.append(f"**Quality Score:** {emoji} {score}/10\n")

        if review["approved"]:
            lines.append("**Status:** ✅ Approved\n")
        else:
            lines.append("**Status:** 🔄 Changes Requested\n")

        if review["issues"]:
            lines.append("\n### Issues")
            for issue in review["issues"]:
                lines.append(f"- {issue['message']}")

        if review["suggestions"]:
            lines.append("\n### Suggestions")
            for suggestion in review["suggestions"]:
                lines.append(f"- {suggestion}")

        if review["positive_feedback"]:
            lines.append("\n### What's Good")
            for feedback in review["positive_feedback"]:
                lines.append(f"- {feedback}")

        lines.append("\n---")
        lines.append("*12-Factor Agent Review*")

        return "\n".join(lines)
