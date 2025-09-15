"""
PRReviewAgent - Automated PR review agent for GitHub pull requests.
Provides AI-powered code analysis using Claude, suggestions, and feedback.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from github import Github

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse
from core.execution_context import ExecutionContext


class FetchPRTool(Tool):
    """Fetch PR data from GitHub"""

    def __init__(self):
        super().__init__(
            name="fetch_pr", description="Fetch pull request data from GitHub"
        )

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer"},
                "repo": {"type": "string"},
            },
            "required": ["pr_number"],
        }

    def execute(self, pr_number: int, repo: str = None) -> ToolResponse:
        """Fetch PR details from GitHub"""
        try:
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                return ToolResponse(
                    success=False, error="GITHUB_TOKEN not set in environment"
                )

            g = Github(token)

            # Use provided repo or get from env
            if not repo:
                repo = os.getenv("GITHUB_DEFAULT_REPO", "donaldbraman/12-factor-agents")

            repository = g.get_repo(repo)
            pr = repository.get_pull(pr_number)

            # Get files changed
            files_changed = []
            for file in pr.get_files():
                files_changed.append(
                    {
                        "filename": file.filename,
                        "status": file.status,
                        "additions": file.additions,
                        "deletions": file.deletions,
                        "changes": file.changes,
                        "patch": file.patch if hasattr(file, "patch") else None,
                    }
                )

            pr_data = {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body or "",
                "state": pr.state,
                "user": pr.user.login,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "head": pr.head.ref,
                "base": pr.base.ref,
                "mergeable": pr.mergeable,
                "changed_files": pr.changed_files,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "files_changed": files_changed,
                "diff_url": pr.diff_url,
                "html_url": pr.html_url,
            }

            return ToolResponse(success=True, data=pr_data)

        except Exception as e:
            return ToolResponse(success=False, error=f"Failed to fetch PR: {str(e)}")


class AnalyzeCodeTool(Tool):
    """Analyze code changes using Claude"""

    def __init__(self):
        super().__init__(
            name="analyze_code", description="Analyze code changes using Claude AI"
        )

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pr_data": {"type": "object"},
                "guidelines": {"type": "string"},
            },
            "required": ["pr_data"],
        }

    def execute(self, pr_data: Dict, guidelines: str = None) -> ToolResponse:
        """Analyze PR code changes with Claude"""
        try:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return ToolResponse(
                    success=False, error="ANTHROPIC_API_KEY not set in environment"
                )

            # Load default guidelines if not provided
            if not guidelines:
                guidelines_path = (
                    Path(__file__).parent.parent / "docs" / "CODING_STANDARDS.md"
                )
                if guidelines_path.exists():
                    guidelines = guidelines_path.read_text()
                else:
                    guidelines = "Follow Python best practices and PEP 8"

            # Construct the diff content
            diff_content = self._format_diff(pr_data.get("files_changed", []))

            # Create review prompt
            prompt = self._create_review_prompt(
                pr_data=pr_data, diff=diff_content, guidelines=guidelines
            )

            # Call Claude for real analysis
            client = Anthropic(api_key=api_key)

            response = client.messages.create(
                model="claude-3-haiku-20240307",  # Fast and cost-effective
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            response_text = response.content[0].text

            # Extract JSON if wrapped in markdown blocks
            json_match = re.search(r"```json?\s*(.+?)\s*```", response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)

            # Try to parse as JSON, otherwise structure the response
            try:
                review_result = json.loads(response_text)
            except json.JSONDecodeError:
                # Structure the text response
                review_result = {
                    "summary": response_text[:500],
                    "quality_score": 7,
                    "approved": "needs review" not in response_text.lower(),
                    "issues": [],
                    "suggestions": [],
                    "needs_changes": [],
                    "positive_feedback": [],
                    "raw_analysis": response_text,
                }

            return ToolResponse(success=True, data=review_result)

        except Exception as e:
            return ToolResponse(
                success=False, error=f"Failed to analyze code: {str(e)}"
            )

    def _format_diff(self, files_changed: List[Dict]) -> str:
        """Format file changes into a diff string"""
        diff_parts = []
        for file in files_changed:
            diff_parts.append(f"\n=== {file['filename']} ===")
            diff_parts.append(f"Status: {file.get('status', 'modified')}")
            diff_parts.append(
                f"Changes: +{file.get('additions', 0)} -{file.get('deletions', 0)}"
            )
            if file.get("patch"):
                diff_parts.append(file["patch"])
        return "\n".join(diff_parts)

    def _create_review_prompt(self, pr_data: Dict, diff: str, guidelines: str) -> str:
        """Create the review prompt for Claude"""
        return f"""You are a senior code reviewer for the 12-factor-agents project.

Project Context:
- Python-based agent orchestration system  
- Follows 12-factor methodology
- Emphasizes modularity, reusability, and clean architecture

Review Guidelines:
{guidelines}

PR Information:
- Title: {pr_data.get('title', 'Untitled')}
- Description: {pr_data.get('body', 'No description')}
- Author: {pr_data.get('user', 'Unknown')}
- Files Changed: {pr_data.get('changed_files', 0)}
- Lines: +{pr_data.get('additions', 0)} -{pr_data.get('deletions', 0)}

Code Changes:
{diff[:8000] if diff else 'No diff available'}

Provide a detailed code review in JSON format:
{{
    "summary": "Executive summary of the changes (1 paragraph)",
    "quality_score": 8,  // 1-10 scale
    "approved": true,  // or false
    "issues": [
        {{
            "severity": "critical|major|minor",
            "category": "bug|security|performance|style|architecture",
            "file": "path/to/file.py",
            "line": 42,  // or null if general
            "message": "Specific issue description",
            "suggestion": "How to fix it"
        }}
    ],
    "suggestions": [
        "General improvement suggestion 1",
        "General improvement suggestion 2"
    ],
    "needs_changes": [
        "Required change 1 before approval",
        "Required change 2 before approval"
    ],
    "positive_feedback": [
        "Well-implemented feature or pattern",
        "Good practice that was followed"
    ]
}}

Be specific, actionable, and constructive in your feedback."""


class PostCommentTool(Tool):
    """Post review comments to PR"""

    def __init__(self):
        super().__init__(
            name="post_comment", description="Post review comment to GitHub PR"
        )

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

    def execute(self, pr_number: int, comment: str, repo: str = None) -> ToolResponse:
        """Post a comment to the PR"""
        try:
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                return ToolResponse(
                    success=False, error="GITHUB_TOKEN not set in environment"
                )

            g = Github(token)

            if not repo:
                repo = os.getenv("GITHUB_DEFAULT_REPO", "donaldbraman/12-factor-agents")

            repository = g.get_repo(repo)
            pr = repository.get_pull(pr_number)

            # Post the comment
            comment_obj = pr.create_issue_comment(comment)

            return ToolResponse(
                success=True,
                data={
                    "comment_id": comment_obj.id,
                    "comment_url": comment_obj.html_url,
                    "created_at": comment_obj.created_at.isoformat(),
                },
            )

        except Exception as e:
            return ToolResponse(
                success=False, error=f"Failed to post comment: {str(e)}"
            )


class UpdatePRDescriptionTool(Tool):
    """Update PR description with enhanced content"""

    def __init__(self):
        super().__init__(
            name="update_pr_description",
            description="Update PR description with AI-enhanced content",
        )

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer"},
                "enhanced_description": {"type": "string"},
                "repo": {"type": "string"},
            },
            "required": ["pr_number", "enhanced_description"],
        }

    def execute(
        self, pr_number: int, enhanced_description: str, repo: str = None
    ) -> ToolResponse:
        """Update the PR description"""
        try:
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                return ToolResponse(
                    success=False, error="GITHUB_TOKEN not set in environment"
                )

            g = Github(token)

            if not repo:
                repo = os.getenv("GITHUB_DEFAULT_REPO", "donaldbraman/12-factor-agents")

            repository = g.get_repo(repo)
            pr = repository.get_pull(pr_number)

            # Preserve original description and add enhanced section
            original = pr.body or ""
            if "## AI Review Summary" not in original:
                new_description = (
                    f"{original}\n\n## AI Review Summary\n\n{enhanced_description}"
                )
            else:
                # Replace existing AI section
                parts = original.split("## AI Review Summary")
                new_description = (
                    f"{parts[0]}## AI Review Summary\n\n{enhanced_description}"
                )

            pr.edit(body=new_description)

            return ToolResponse(
                success=True, data={"updated": True, "pr_number": pr_number}
            )

        except Exception as e:
            return ToolResponse(
                success=False, error=f"Failed to update PR description: {str(e)}"
            )


class PRReviewAgent(BaseAgent):
    """Agent for automated pull request reviews using Claude"""

    def __init__(self):
        self.name = "PRReviewAgent"
        self.description = "Automated PR review with Claude AI analysis"

        # Create tools first
        self.fetch_tool = FetchPRTool()
        self.analyze_tool = AnalyzeCodeTool()
        self.comment_tool = PostCommentTool()
        self.update_tool = UpdatePRDescriptionTool()

        self.tools = [
            self.fetch_tool,
            self.analyze_tool,
            self.comment_tool,
            self.update_tool,
        ]

        # Now call super init
        super().__init__()

        # Load configuration
        self.config = self._load_config()

    def register_tools(self):
        """Register agent tools"""
        return self.tools

    def _apply_action(self, action_name: str, **kwargs) -> Any:
        """Apply an action (used by base class)"""
        if action_name == "fetch_pr":
            return self.fetch_tool.execute(**kwargs)
        elif action_name == "analyze_code":
            return self.analyze_tool.execute(**kwargs)
        elif action_name == "post_comment":
            return self.comment_tool.execute(**kwargs)
        elif action_name == "update_pr_description":
            return self.update_tool.execute(**kwargs)
        else:
            return {"error": f"Unknown action: {action_name}"}

    def _load_config(self) -> Dict:
        """Load agent configuration"""
        config_path = Path(__file__).parent.parent / "config" / "pr_review_config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {
            "auto_approve_threshold": 8,
            "post_comments": True,
            "update_description": True,
        }

    def execute_task(
        self, task: str, context: Optional[ExecutionContext] = None
    ) -> Any:
        """Execute PR review task"""
        print(f"🔍 PRReviewAgent executing: {task}")

        # Parse task to extract PR number and repo
        import re

        pr_match = re.search(r"#?(\d+)", task)
        if not pr_match:
            return {"error": "No PR number found in task"}

        pr_number = int(pr_match.group(1))

        # Extract repo if specified
        repo_match = re.search(
            r"(?:in|repo:|repository:)\s*([\w\-]+/[\w\-]+)", task, re.IGNORECASE
        )
        repo = repo_match.group(1) if repo_match else None

        # Step 1: Fetch PR data
        print(f"📥 Fetching PR #{pr_number}...")
        fetch_result = self.fetch_tool.execute(pr_number=pr_number, repo=repo)

        if not fetch_result.success:
            return {"error": fetch_result.error}

        pr_data = fetch_result.data
        print(f"✅ Fetched PR: {pr_data['title']}")

        # Step 2: Analyze code with Claude
        print("🤖 Analyzing code with Claude...")
        analysis_result = self.analyze_tool.execute(pr_data=pr_data)

        if not analysis_result.success:
            return {"error": analysis_result.error}

        review_data = analysis_result.data
        print(
            f"✅ Analysis complete. Quality score: {review_data.get('quality_score', 'N/A')}/10"
        )

        # Step 3: Format review comment
        comment = self._format_review_comment(review_data)

        # Step 4: Post comment if configured
        if self.config.get("post_comments", True) and "analyze" not in task.lower():
            print("💬 Posting review comment...")
            comment_result = self.comment_tool.execute(
                pr_number=pr_number, comment=comment, repo=repo
            )

            if comment_result.success:
                print(f"✅ Comment posted: {comment_result.data.get('comment_url', '')}")
            else:
                print(f"⚠️ Failed to post comment: {comment_result.error}")

        # Step 5: Update PR description if configured
        if self.config.get("update_description", True) and review_data.get("summary"):
            print("📝 Updating PR description...")
            summary = f"**Review Score:** {review_data.get('quality_score', 'N/A')}/10\n\n{review_data['summary']}"
            update_result = self.update_tool.execute(
                pr_number=pr_number, enhanced_description=summary, repo=repo
            )

            if update_result.success:
                print("✅ PR description updated")

        # Return review results
        return {
            "pr_number": pr_number,
            "title": pr_data["title"],
            "review_completed": True,
            "quality_score": review_data.get("quality_score"),
            "approved": review_data.get("approved"),
            "issues_found": len(review_data.get("issues", [])),
            "summary": review_data.get("summary", "Review completed"),
            "comment_posted": self.config.get("post_comments", False),
        }

    def _format_review_comment(self, review_data: Dict) -> str:
        """Format review data into a GitHub comment"""
        lines = ["## 🤖 Automated Code Review by Claude\n"]

        # Summary
        if review_data.get("summary"):
            lines.append(f"**Summary:** {review_data['summary']}\n")

        # Quality score
        score = review_data.get("quality_score", 0)
        emoji = "✅" if score >= 8 else "⚠️" if score >= 6 else "❌"
        lines.append(f"**Quality Score:** {emoji} {score}/10\n")

        # Approval status
        if review_data.get("approved"):
            lines.append("**Status:** ✅ Approved\n")
        else:
            lines.append("**Status:** 🔄 Changes Requested\n")

        # Issues found
        issues = review_data.get("issues", [])
        if issues:
            lines.append("\n### 🐛 Issues Found\n")
            for issue in issues:
                severity_emoji = {"critical": "🔴", "major": "🟠", "minor": "🟡"}.get(
                    issue.get("severity", "minor"), "⚪"
                )
                lines.append(
                    f"- {severity_emoji} **{issue.get('severity', 'minor').title()}:** {issue.get('message', 'Issue found')}"
                )
                if issue.get("file"):
                    lines.append(f"  - File: `{issue['file']}`")
                if issue.get("line"):
                    lines.append(f"  - Line: {issue['line']}")
                if issue.get("suggestion"):
                    lines.append(f"  - Suggestion: {issue['suggestion']}")
                lines.append("")

        # Required changes
        needs_changes = review_data.get("needs_changes", [])
        if needs_changes:
            lines.append("\n### 🔧 Required Changes\n")
            for change in needs_changes:
                lines.append(f"- {change}")
            lines.append("")

        # Suggestions
        suggestions = review_data.get("suggestions", [])
        if suggestions:
            lines.append("\n### 💡 Suggestions\n")
            for suggestion in suggestions:
                lines.append(f"- {suggestion}")
            lines.append("")

        # Positive feedback
        positive = review_data.get("positive_feedback", [])
        if positive:
            lines.append("\n### 👍 What's Good\n")
            for feedback in positive:
                lines.append(f"- {feedback}")
            lines.append("")

        # Footer
        lines.append("\n---")
        lines.append(
            "*This review was generated automatically by the PRReviewAgent using Claude AI.*"
        )

        return "\n".join(lines)
