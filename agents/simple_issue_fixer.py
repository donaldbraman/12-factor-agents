#!/usr/bin/env python3
"""
Simple Issue Fixer - A lightweight agent that fixes issues using simple patterns.

Following our architecture: stateless functions, existing tools, minimal complexity.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tools import ToolResponse  # noqa: E402


def fix_simple_issue(issue_number: str) -> ToolResponse:
    """
    Fix an issue using simple, direct patterns.

    This is a stateless function that:
    1. Reads the issue file
    2. Extracts file and change information
    3. Applies changes directly
    4. Returns clear success/error status
    """

    # Find issue file
    issue_path = None
    for file in Path("issues").glob(f"{issue_number}*.md"):
        issue_path = file
        break

    if not issue_path:
        return ToolResponse(
            success=False, error=f"Issue file not found for issue {issue_number}"
        )

    try:
        content = issue_path.read_text()

        # Extract basic info
        title_match = re.search(r"^# Issue #\d+:\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else "Unknown"

        print(f"📝 Processing: {title}")

        # Extract file to update (multiple patterns for flexibility)
        file_to_update = None

        # Pattern 1: "Files to Update" section
        files_match = re.search(
            r"## Files to Update\s*\n[-*]\s+([^\s\n]+)", content, re.MULTILINE
        )
        if files_match:
            file_to_update = files_match.group(1).strip()
            # Clean up the file path
            file_to_update = re.sub(
                r"\s*\(.*?\)\s*$", "", file_to_update
            )  # Remove (line X) annotations

        # Pattern 2: Look in Solution section
        if not file_to_update:
            solution_match = re.search(
                r"(?:file|path)[:\s]+([/\w.-]+\.\w+)", content, re.IGNORECASE
            )
            if solution_match:
                file_to_update = solution_match.group(1)

        if not file_to_update:
            return ToolResponse(
                success=False, error="Could not determine which file to update"
            )

        print(f"📄 File to update: {file_to_update}")

        # Extract what to do (look for code blocks in Solution section)
        solution_code = None
        solution_match = re.search(
            r"## Solution.*?```(?:python|javascript|typescript|bash)?\n(.*?)```",
            content,
            re.DOTALL | re.IGNORECASE,
        )

        if solution_match:
            solution_code = solution_match.group(1).strip()

        if not solution_code:
            # Try simpler pattern
            code_match = re.search(r"```(?:python)?\n(.*?)```", content, re.DOTALL)
            if code_match:
                solution_code = code_match.group(1).strip()

        if not solution_code:
            return ToolResponse(
                success=False, error="Could not find code to add/modify in the issue"
            )

        # Determine operation type
        operation = "unknown"

        # Check if it's an addition (has line number or "add" keyword)
        if re.search(
            r"line \d+|add.*comment|add.*import|prepend|append", content, re.IGNORECASE
        ):
            operation = "add"
        # Check if it's a replacement
        elif re.search(
            r"change|replace|fix|should be|instead of", content, re.IGNORECASE
        ):
            operation = "replace"
        else:
            # Default to add if we have simple code
            if len(solution_code.splitlines()) <= 5:
                operation = "add"

        print(f"🔧 Operation: {operation}")

        # Apply the fix
        file_path = Path(file_to_update)

        if not file_path.exists():
            return ToolResponse(
                success=False, error=f"File not found: {file_to_update}"
            )

        current_content = file_path.read_text()

        if operation == "add":
            # Simple addition - add after imports or at top
            if "import" in solution_code or solution_code.startswith("#"):
                # Add near the top
                lines = current_content.splitlines()
                # Find where to insert (after initial comments/imports)
                insert_index = 0
                for i, line in enumerate(lines):
                    if (
                        line
                        and not line.startswith("#")
                        and not line.startswith("import")
                        and not line.startswith("from")
                    ):
                        insert_index = i
                        break

                # Insert the code
                lines.insert(insert_index, solution_code)
                new_content = "\n".join(lines)
            else:
                # Just append for now
                new_content = current_content + "\n" + solution_code

            file_path.write_text(new_content)
            print(f"✅ Added code to {file_to_update}")

            return ToolResponse(
                success=True,
                data={
                    "action": "added",
                    "file": file_to_update,
                    "code": solution_code[:100] + "..."
                    if len(solution_code) > 100
                    else solution_code,
                },
            )

        elif operation == "replace":
            # For replace, we need old and new patterns
            # Try to find them in the issue
            old_new_match = re.search(
                r"(?:current|old|problem).*?```.*?\n(.*?)```.*?(?:should be|new|solution).*?```.*?\n(.*?)```",
                content,
                re.DOTALL | re.IGNORECASE,
            )

            if old_new_match:
                old_text = old_new_match.group(1).strip()
                new_text = old_new_match.group(2).strip()

                if old_text in current_content:
                    new_content = current_content.replace(old_text, new_text)
                    file_path.write_text(new_content)
                    print(f"✅ Replaced text in {file_to_update}")

                    return ToolResponse(
                        success=True,
                        data={
                            "action": "replaced",
                            "file": file_to_update,
                            "old": old_text[:50] + "..."
                            if len(old_text) > 50
                            else old_text,
                            "new": new_text[:50] + "..."
                            if len(new_text) > 50
                            else new_text,
                        },
                    )
                else:
                    return ToolResponse(
                        success=False,
                        error=f"Could not find text to replace in {file_to_update}",
                    )
            else:
                # Fallback: just add the code if we can't find old/new
                new_content = current_content + "\n" + solution_code
                file_path.write_text(new_content)
                print(f"✅ Added code to {file_to_update} (fallback)")

                return ToolResponse(
                    success=True,
                    data={
                        "action": "added (fallback)",
                        "file": file_to_update,
                        "code": solution_code[:100] + "..."
                        if len(solution_code) > 100
                        else solution_code,
                    },
                )

        return ToolResponse(success=False, error=f"Unknown operation type: {operation}")

    except Exception as e:
        return ToolResponse(success=False, error=f"Error processing issue: {str(e)}")


# Test if run directly
if __name__ == "__main__":
    if len(sys.argv) > 1:
        issue_num = sys.argv[1]
        result = fix_simple_issue(issue_num)

        if result.success:
            print(f"✅ Success: {result.data}")
        else:
            print(f"❌ Failed: {result.error}")
    else:
        print("Usage: python simple_issue_fixer.py <issue_number>")
