#!/usr/bin/env uv run python
"""
GitHub Integration Bridge for 12-factor-agents
Enables processing of GitHub issues from external repositories
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

from core.telemetry import EnhancedTelemetryCollector, EventType
from core.execution_context import ExecutionContext, create_external_context
from core.retry_wrappers import subprocess_run


@dataclass
class GitHubIssue:
    """GitHub issue data structure"""

    number: int
    title: str
    body: str
    state: str
    labels: list
    assignees: list
    repository: str


class GitHubIssueLoader:
    """
    Load and convert GitHub issues for Sparky processing
    """

    def __init__(self, repo: str = None):
        self.repo = repo or os.getenv("GITHUB_REPO", "12-factor-agents")
        self.telemetry = EnhancedTelemetryCollector()

    def fetch_issue(self, issue_number: int) -> Optional[Dict]:
        """
        Fetch issue from GitHub using gh CLI
        Returns issue data or None if failed
        """
        cmd = [
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--json",
            "number,title,body,assignees,labels,state",
            "--repo",
            self.repo,
        ]

        try:
            result = subprocess_run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                data["repository"] = self.repo
                return data
            else:
                print(f"❌ Failed to fetch issue #{issue_number}: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print(f"⏱️ Timeout fetching issue #{issue_number}")
            return None
        except Exception as e:
            print(f"❌ Error fetching issue: {e}")
            return None

    def convert_to_sparky_format(self, github_issue: Dict) -> Dict:
        """Convert GitHub issue to Sparky's expected format"""
        return {
            "number": github_issue.get("number"),
            "title": github_issue.get("title", ""),
            "content": github_issue.get("body", ""),
            "agent": self.determine_agent(github_issue),
            "labels": [
                label.get("name", "") for label in github_issue.get("labels", [])
            ],
            "state": github_issue.get("state", "open"),
            "repository": github_issue.get("repository", self.repo),
        }

    def determine_agent(self, github_issue: Dict) -> str:
        """Determine which agent should handle this issue"""
        title = github_issue.get("title", "").lower()
        body = github_issue.get("body", "").lower()
        labels = [
            label.get("name", "").lower() for label in github_issue.get("labels", [])
        ]

        # Check labels first
        if "bug" in labels:
            return "IntelligentIssueAgent"
        elif "enhancement" in labels:
            return "IntelligentIssueAgent"
        elif "documentation" in labels:
            return "DocumentationAgent"

        # Check title/body content
        if "test" in title or "test" in body:
            return "TestingAgent"
        elif "performance" in title:
            return "PerformanceAgent"
        elif "security" in title:
            return "SecurityAgent"
        else:
            return "IntelligentIssueAgent"  # Default

    def save_as_issue_file(self, issue_data: Dict) -> Path:
        """Save GitHub issue as local file for processing"""
        # Create issues directory if needed
        issues_dir = Path("issues")
        issues_dir.mkdir(exist_ok=True)

        # Generate filename
        issue_number = issue_data["number"]
        safe_title = issue_data["title"][:50].replace(" ", "-").replace("/", "-")
        issue_path = issues_dir / f"{issue_number}-github-{safe_title}.md"

        # Generate content
        content = f"""# Issue #{issue_data['number']}: {issue_data['title']}

## Description
{issue_data['content']}

## Metadata
- **Repository**: {issue_data['repository']}
- **State**: {issue_data['state']}
- **Labels**: {', '.join(issue_data['labels']) if issue_data['labels'] else 'None'}

## Agent Assignment
{issue_data['agent']}

## Status
OPEN
"""

        issue_path.write_text(content)
        print(f"📝 Saved GitHub issue to {issue_path}")
        return issue_path


class CrossRepoContextManager:
    """
    Manage context switching between repositories
    """

    def __init__(self):
        self.original_cwd = os.getcwd()
        self.original_env = dict(os.environ)
        self.contexts = {}

    def switch_to_repo(self, repo_path: str) -> bool:
        """
        Switch working directory to target repository
        Returns True if successful
        """
        repo_path = Path(repo_path).expanduser().resolve()

        if not repo_path.exists():
            print(f"❌ Repository not found: {repo_path}")
            return False

        if not repo_path.is_dir():
            print(f"❌ Not a directory: {repo_path}")
            return False

        # Save current context
        self.contexts[self.original_cwd] = {"env": dict(os.environ), "cwd": os.getcwd()}

        # Switch to new repo
        try:
            os.chdir(repo_path)
            os.environ["GITHUB_REPO"] = repo_path.name
            print(f"📂 Switched to repository: {repo_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to switch context: {e}")
            return False

    def restore_context(self):
        """Restore original working context"""
        try:
            os.chdir(self.original_cwd)
            os.environ.clear()
            os.environ.update(self.original_env)
            print(f"📂 Restored context to: {self.original_cwd}")
        except Exception as e:
            print(f"⚠️ Error restoring context: {e}")


class ExternalIssueProcessor:
    """
    Process GitHub issues from external repositories
    """

    def __init__(self):
        self.telemetry = EnhancedTelemetryCollector()

    def process_external_issue(
        self, repo: str, issue_number: int, repo_path: Optional[str] = None
    ) -> Dict:
        """
        Full pipeline for external issue processing

        Args:
            repo: GitHub repository (e.g., "donaldbraman/cite-assist")
            issue_number: Issue number to process
            repo_path: Optional local path to repository

        Returns:
            Processing result dictionary
        """
        print(f"\n🚀 Processing external issue: {repo}#{issue_number}")

        # Record external issue received event
        external_issue_event_id = self.telemetry.record_workflow_event(
            EventType.EXTERNAL_ISSUE_RECEIVED,
            repo.split("/")[-1],  # Extract repo name
            "ExternalIssueProcessor",
            f"Received external issue #{issue_number} from {repo}",
            {"repo": repo, "issue_number": issue_number, "repo_path": repo_path},
        )

        # 1. Load issue from GitHub
        loader = GitHubIssueLoader(repo)
        github_issue = loader.fetch_issue(issue_number)

        if not github_issue:
            # Record failure
            self.telemetry.record_workflow_event(
                EventType.EXTERNAL_ISSUE_COMPLETED,
                repo.split("/")[-1],
                "ExternalIssueProcessor",
                f"Failed to fetch external issue #{issue_number} from {repo}",
                {"success": False, "error": "Could not fetch issue"},
                success=False,
                parent_event_id=external_issue_event_id,
            )
            return {
                "success": False,
                "error": f"Could not fetch issue #{issue_number} from {repo}",
            }

        # 2. Convert to Sparky format
        sparky_issue = loader.convert_to_sparky_format(github_issue)
        print(f"📋 Issue: {sparky_issue['title']}")
        print(f"🤖 Agent: {sparky_issue['agent']}")

        # 3. Save as local issue file
        issue_file = loader.save_as_issue_file(sparky_issue)

        # 4. Create execution context for external repository
        if repo_path:
            repo_path_obj = Path(repo_path).expanduser().resolve()
            if not repo_path_obj.exists():
                # Record failure
                self.telemetry.record_workflow_event(
                    EventType.EXTERNAL_ISSUE_COMPLETED,
                    repo.split("/")[-1],
                    "ExternalIssueProcessor",
                    f"Repository path does not exist: {repo_path}",
                    {"success": False, "error": "Invalid repo path"},
                    success=False,
                    parent_event_id=external_issue_event_id,
                )
                return {
                    "success": False,
                    "error": f"Repository path does not exist: {repo_path}",
                }

            # Record context switch event
            self.telemetry.record_workflow_event(
                EventType.CROSS_REPO_CONTEXT_SWITCH,
                repo.split("/")[-1],
                "ExternalIssueProcessor",
                f"Switching context to external repo: {repo_path}",
                {"source_repo": repo, "target_path": str(repo_path_obj)},
                parent_event_id=external_issue_event_id,
            )

            # Create external execution context
            context = create_external_context(
                repo=repo, repo_path=repo_path_obj, issue_number=issue_number
            )
            print(f"🔧 Created execution context: {context}")
        else:
            # Create context for current directory (fallback)
            context = ExecutionContext(
                repo_name=repo.split("/")[-1],
                source_repo=repo,
                issue_number=issue_number,
                is_external=True,
            )

        # 5. Route through Sparky (IssueOrchestratorAgent) instead of direct agent call
        # Import here to avoid circular dependency
        from agents.issue_orchestrator_agent import IssueOrchestratorAgent

        sparky = IssueOrchestratorAgent()

        try:
            # Process the issue through Sparky with execution context
            task_description = f"Process external issue #{issue_number} from {repo}"
            result = sparky.execute_task(task_description, context=context)

            if result.success:
                print(f"✅ Successfully processed {repo}#{issue_number}")

                # Record successful completion
                self.telemetry.record_workflow_event(
                    EventType.EXTERNAL_ISSUE_COMPLETED,
                    repo.split("/")[-1],
                    "ExternalIssueProcessor",
                    f"Successfully processed external issue #{issue_number} from {repo}",
                    {
                        "success": True,
                        "issue_title": sparky_issue["title"],
                        "agent": sparky_issue["agent"],
                    },
                    success=True,
                    parent_event_id=external_issue_event_id,
                )

                # Update GitHub issue with comment (optional)
                self.add_github_comment(
                    repo,
                    issue_number,
                    "🤖 Processed by 12-factor-agents via Sparky orchestrator. Result: Success",
                )
            else:
                print(f"❌ Failed to process: {result.error}")

                # Record failure
                self.telemetry.record_workflow_event(
                    EventType.EXTERNAL_ISSUE_COMPLETED,
                    repo.split("/")[-1],
                    "ExternalIssueProcessor",
                    f"Failed to process external issue #{issue_number}: {result.error}",
                    {"success": False, "error": result.error},
                    success=False,
                    parent_event_id=external_issue_event_id,
                )

            return {
                "success": result.success,
                "issue": sparky_issue,
                "result": result.data if result.success else None,
                "error": result.error if not result.success else None,
                "context": context.to_dict(),  # Include context info for debugging
            }

        except Exception as e:
            print(f"❌ Error during processing: {e}")

            # Record exception
            self.telemetry.record_workflow_event(
                EventType.EXTERNAL_ISSUE_COMPLETED,
                repo.split("/")[-1],
                "ExternalIssueProcessor",
                f"Exception during processing of external issue #{issue_number}: {str(e)}",
                {"success": False, "error": str(e), "exception_type": type(e).__name__},
                success=False,
                parent_event_id=external_issue_event_id,
            )

            return {
                "success": False,
                "error": f"Processing failed: {str(e)}",
                "issue": sparky_issue,
                "context": context.to_dict() if "context" in locals() else None,
            }

    def add_github_comment(self, repo: str, issue_number: int, comment: str):
        """Add a comment to GitHub issue (optional feedback)"""
        try:
            cmd = [
                "gh",
                "issue",
                "comment",
                str(issue_number),
                "--repo",
                repo,
                "--body",
                comment,
            ]
            subprocess.run(cmd, capture_output=True, timeout=5)
        except Exception:
            pass  # Optional, don't fail if comment fails


def main():
    """Test GitHub integration"""
    print("🔧 Testing GitHub Integration Bridge")

    # Test 1: Load a GitHub issue
    print("\n1. Testing GitHub issue loading:")
    loader = GitHubIssueLoader("12-factor-agents")

    # Try to fetch a test issue (might not exist)
    issue_data = loader.fetch_issue(1)
    if issue_data:
        print(f"   Loaded issue: {issue_data.get('title', 'Unknown')}")
        sparky_format = loader.convert_to_sparky_format(issue_data)
        print(f"   Agent assignment: {sparky_format['agent']}")
    else:
        print("   No issue #1 found (expected if doesn't exist)")

    # Test 2: Context switching
    print("\n2. Testing context switching:")
    context = CrossRepoContextManager()
    original = os.getcwd()

    # Try switching to parent directory
    if context.switch_to_repo(".."):
        print(f"   Current dir: {os.getcwd()}")
        context.restore_context()
        print(f"   Restored to: {os.getcwd()}")
        assert os.getcwd() == original, "Context not restored properly!"

    print("\n✅ GitHub integration ready!")


if __name__ == "__main__":
    main()
