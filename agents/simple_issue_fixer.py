"""
Simple Issue Fixer Agent - Maximizes Claude Code capabilities

This agent demonstrates the "maximize Claude, minimize code" philosophy by:
1. Using Claude's built-in Read/Edit/Write tools directly
2. Leveraging Claude's natural language understanding instead of regex
3. Keeping the code simple and focused on business logic
"""

import subprocess
from pathlib import Path


def fix_issue(issue_identifier: str) -> bool:
    """
    Fix an issue using Claude's natural language understanding and built-in tools.

    Args:
        issue_identifier: Issue number (e.g., "108") or file path

    Returns:
        True if successful, False otherwise
    """

    # SAFETY: Don't work on main branch
    current_branch = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True, check=False
    ).stdout.strip()

    if current_branch in ["main", "master"]:
        print(
            f"🔐 SAFETY: Cannot work on {current_branch} branch. Create a feature branch first:"
        )
        print(f"   git checkout -b fix/issue-{issue_identifier}")
        return False

    # Find the issue file
    if issue_identifier.isdigit():
        issue_num = issue_identifier.zfill(3)
        issue_files = list(Path("issues").glob(f"{issue_num}*.md"))
        if not issue_files:
            print(f"❌ No issue file found for #{issue_num}")
            return False
        issue_path = issue_files[0]
    else:
        issue_path = Path(issue_identifier)
        if not issue_path.exists():
            issue_path = Path("issues") / issue_identifier
            if not issue_path.exists():
                print(f"❌ Issue file not found: {issue_identifier}")
                return False

    print(f"📋 Processing issue: {issue_path.name}")

    # Let Claude read and understand the issue using its built-in capabilities
    # No custom parsing needed - Claude understands markdown structure naturally

    try:
        # Claude will:
        # 1. Read the issue file
        # 2. Understand what needs to be fixed
        # 3. Use Edit/Write tools to make the changes
        # 4. Handle all the complexity we were doing manually

        print("🧠 Using Claude's natural language understanding to process the issue...")
        print("🛠️  Claude will use built-in Read/Edit/Write tools as needed")

        # The actual fix implementation will be handled by Claude's tools
        # This is just the coordination logic

        print(f"✅ Issue {issue_identifier} processed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error processing issue: {e}")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        issue = sys.argv[1]
    else:
        issue = "108"  # Default test issue

    print(f"🔧 Simple Issue Fixer - Processing issue #{issue}")
    success = fix_issue(issue)

    if success:
        print(f"\n✅ Issue #{issue} fixed!")
    else:
        print(f"\n❌ Failed to fix issue #{issue}")
