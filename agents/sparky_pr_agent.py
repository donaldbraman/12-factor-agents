#!/usr/bin/env python3
"""
Sparky PR Agent - Wrapper for IntelligentIssueAgent with PR workflow

Ensures all Sparky work goes through proper branch/PR creation instead of direct commits.
This provides the visibility and review process needed for self-improving AI changes.
"""

import re
from pathlib import Path
from typing import Dict, Optional

from core.tools import ToolResponse
from core.git_workflow import GitWorkflowManager
from agents.intelligent_issue_agent import IntelligentIssueAgent


class SparkyPRAgent:
    """
    PR-aware wrapper for Sparky that ensures all changes go through proper review process
    """

    def __init__(self):
        self.issue_agent = IntelligentIssueAgent()
        self.git_workflow = GitWorkflowManager()
        self.current_issue_number = None

    def process_issue(self, issue_file: str) -> ToolResponse:
        """
        Process an issue with full PR workflow:
        1. Extract issue number and description
        2. Create feature branch
        3. Execute issue processing
        4. Commit changes
        5. Create PR
        """
        try:
            # Extract issue info
            issue_info = self._extract_issue_info(issue_file)
            if not issue_info:
                return ToolResponse(
                    success=False,
                    error=f"Could not extract issue information from {issue_file}",
                )

            self.current_issue_number = issue_info["number"]

            # Step 1: Create feature branch
            print(f"🌿 Creating feature branch for issue #{self.current_issue_number}")
            branch_result = self.git_workflow.create_feature_branch(
                issue_number=self.current_issue_number, description=issue_info["title"]
            )

            if not branch_result.success:
                return ToolResponse(
                    success=False,
                    error=f"Failed to create feature branch: {branch_result.error}",
                )

            print(f"✅ Created branch: {branch_result.data['branch_name']}")

            # Step 2: Process the issue using existing IntelligentIssueAgent
            print("🤖 Processing issue with Sparky...")
            task = f"--issue-file {issue_file}"
            process_result = self.issue_agent.execute_task(task)

            if not process_result.success:
                print(f"❌ Issue processing failed: {process_result.error}")
                # Don't create PR on failure, but keep branch for debugging
                return ToolResponse(
                    success=False,
                    error=f"Issue processing failed: {process_result.error}",
                    data={
                        "branch": branch_result.data["branch_name"],
                        "issue_number": self.current_issue_number,
                    },
                )

            # Step 3: Commit changes
            print("📝 Committing Sparky's changes...")
            commit_message = f"fix: {issue_info['title'][:50]}..."
            if len(issue_info["title"]) > 50:
                commit_message = f"fix: {issue_info['title'][:47]}..."

            commit_result = self.git_workflow.commit_changes(commit_message)

            if not commit_result.success:
                return ToolResponse(
                    success=False,
                    error=f"Failed to commit changes: {commit_result.error}",
                    data={
                        "branch": branch_result.data["branch_name"],
                        "issue_number": self.current_issue_number,
                    },
                )

            # Step 4: Create Pull Request
            print("🔀 Creating pull request...")
            pr_title = f"fix: {issue_info['title']}"
            pr_body = f"""## Sparky Self-Improvement

**Issue**: #{self.current_issue_number} - {issue_info['title']}

**Summary**: {issue_info.get('description', 'Automated fix by Sparky')}

**Changes Made**:
{self._summarize_changes(process_result)}

**Type**: Self-improvement based on failure report
**Agent**: IntelligentIssueAgent via SparkyPRAgent"""

            pr_result = self.git_workflow.create_pull_request(
                title=pr_title, body=pr_body, issue_number=self.current_issue_number
            )

            if not pr_result.success:
                return ToolResponse(
                    success=False,
                    error=f"Failed to create PR: {pr_result.error}",
                    data={
                        "branch": branch_result.data["branch_name"],
                        "committed": True,
                        "issue_number": self.current_issue_number,
                    },
                )

            print(f"🎉 Successfully created PR: {pr_result.data['pr_url']}")

            return ToolResponse(
                success=True,
                data={
                    "pr_url": pr_result.data["pr_url"],
                    "branch": branch_result.data["branch_name"],
                    "issue_number": self.current_issue_number,
                    "title": pr_title,
                    "process_result": process_result.data,
                },
            )

        except Exception as e:
            return ToolResponse(
                success=False,
                error=f"Unexpected error in Sparky PR workflow: {str(e)}",
                data={"issue_number": self.current_issue_number, "exception": str(e)},
            )

    def _extract_issue_info(self, issue_file: str) -> Optional[Dict]:
        """Extract issue number and title from issue file"""
        try:
            # Try to extract from filename first
            file_path = Path(issue_file)
            if not file_path.exists():
                return None

            # Extract from filename pattern like "123-title.md" or "issues/123.md"
            filename = file_path.stem

            # Pattern 1: "123-title" or "123"
            match = re.match(r"^(\d+)(?:-(.+))?$", filename)
            if match:
                number = match.group(1)
                title_from_file = match.group(2) or ""
            else:
                return None

            # Read file content for title
            try:
                content = file_path.read_text()
                lines = content.split("\n")

                # Look for title in first few lines
                title = title_from_file
                description = ""

                for line in lines[:10]:
                    line = line.strip()
                    if line.startswith("# ") and not title:
                        title = line[2:].strip()
                    elif line.startswith("## Description"):
                        # Find description content
                        desc_lines = []
                        for desc_line in lines[lines.index(line) + 1 :]:
                            desc_line = desc_line.strip()
                            if desc_line.startswith("#") or not desc_line:
                                break
                            desc_lines.append(desc_line)
                        description = " ".join(desc_lines)[:200]
                        break

                return {
                    "number": number,
                    "title": title or f"Issue {number}",
                    "description": description,
                    "file": str(file_path),
                }

            except Exception:
                # Fallback to basic info
                return {
                    "number": number,
                    "title": title_from_file or f"Issue {number}",
                    "description": "",
                    "file": str(file_path),
                }

        except Exception:
            return None

    def _summarize_changes(self, process_result: ToolResponse) -> str:
        """Create a summary of changes made"""
        if not process_result.success or not process_result.data:
            return "- Processing failed, no changes made"

        operations = process_result.data.get("operations", [])
        if not operations:
            return "- No specific operations recorded"

        summary = []
        for op in operations:
            if op.get("operation") == "create":
                summary.append(f"- Created file: {op.get('path', 'unknown')}")
            elif op.get("operation") == "fix":
                summary.append(f"- Fixed file: {op.get('path', 'unknown')}")
            else:
                summary.append(f"- Modified: {op.get('path', 'unknown')}")

        return "\n".join(summary) if summary else "- Made unspecified improvements"


def main():
    """Main function for running Sparky with PR workflow"""
    import sys

    if len(sys.argv) != 2:
        print("Usage: python sparky_pr_agent.py <issue_file>")
        sys.exit(1)

    issue_file = sys.argv[1]

    print("🤖 Sparky PR Agent - Self-improving AI with proper review workflow")
    print(f"📋 Processing issue: {issue_file}")

    agent = SparkyPRAgent()
    result = agent.process_issue(issue_file)

    if result.success:
        print(f"🎉 SUCCESS: PR created at {result.data['pr_url']}")
        print(f"🔍 Review branch: {result.data['branch']}")
        print(
            "⚠️  Remember: EXTREME CARE needed when reviewing self-modifying AI changes"
        )
    else:
        print(f"❌ FAILED: {result.error}")
        if result.data:
            print(f"📊 Data: {result.data}")
        sys.exit(1)


if __name__ == "__main__":
    main()
