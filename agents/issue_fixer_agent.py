"""
IssueFixerAgent - Applies fixes described in issues to the codebase.
Handles documentation updates, code fixes, and test implementations.
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse


class FileEditorTool(Tool):
    """Edit files based on issue descriptions"""

    def __init__(self):
        super().__init__(name="edit_file", description="Edit a file to apply fixes")

    def execute(self, file_path: str, changes: List[Dict[str, str]]) -> ToolResponse:
        """Apply changes to a file"""
        try:
            path = Path(file_path)

            # Read current content
            if path.exists():
                content = path.read_text()
            else:
                content = ""

            # Apply each change
            for change in changes:
                if "old" in change and "new" in change:
                    content = content.replace(change["old"], change["new"])
                elif "append" in change:
                    content += "\n" + change["append"]
                elif "prepend" in change:
                    content = change["prepend"] + "\n" + content
                elif "content" in change:
                    content = change["content"]

            # Write back
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

            return ToolResponse(
                success=True, data={"file": str(path), "modified": True}
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "old": {"type": "string"},
                            "new": {"type": "string"},
                            "append": {"type": "string"},
                            "prepend": {"type": "string"},
                            "content": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["file_path", "changes"],
        }


class IssueParserTool(Tool):
    """Parse issue content to extract fixes"""

    def __init__(self):
        super().__init__(
            name="parse_issue", description="Parse issue markdown to extract fixes"
        )

    def execute(self, issue_path: str) -> ToolResponse:
        """Parse issue to extract fix information"""
        try:
            path = Path(issue_path)
            if not path.exists():
                return ToolResponse(
                    success=False, error=f"Issue file not found: {issue_path}"
                )

            content = path.read_text()

            # Extract issue number from filename
            issue_num = path.stem.split("-")[0]

            # Extract title
            title_match = re.search(
                r"^#\s+Issue\s+#\d+:\s+(.+)$", content, re.MULTILINE
            )
            title = title_match.group(1) if title_match else "Unknown"

            # Extract implementation section
            impl_match = re.search(
                r"## Implementation\n(.*?)(?=\n##|\Z)", content, re.DOTALL
            )
            implementation = impl_match.group(1) if impl_match else ""

            # Extract solution section
            solution_match = re.search(
                r"## Solution\n(.*?)(?=\n##|\Z)", content, re.DOTALL
            )
            solution = solution_match.group(1) if solution_match else ""

            # Extract code blocks
            code_blocks = re.findall(r"```(?:python)?\n(.*?)```", content, re.DOTALL)

            # Determine target file
            # Look for explicit file paths first
            file_match = re.search(
                r'[`"]?(/[/\w.-]+\.\w+)[`"]?', implementation + solution
            )
            if not file_match:
                # Try without leading slash
                file_match = re.search(
                    r'(?:Update|Create|Fix|in)\s+[`"]?([/\w.-]+\.\w+)[`"]?',
                    implementation + solution,
                )

            target_file = file_match.group(1) if file_match else None
            if target_file and target_file.startswith("/"):
                target_file = target_file[1:]  # Remove leading slash

            return ToolResponse(
                success=True,
                data={
                    "issue_number": issue_num,
                    "title": title,
                    "implementation": implementation,
                    "solution": solution,
                    "code_blocks": code_blocks,
                    "target_file": target_file,
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"issue_path": {"type": "string"}},
            "required": ["issue_path"],
        }


class TestCreatorTool(Tool):
    """Create test files based on issue descriptions"""

    def __init__(self):
        super().__init__(
            name="create_test", description="Create test file from issue description"
        )

    def execute(self, test_path: str, test_content: str) -> ToolResponse:
        """Create a test file"""
        try:
            path = Path(test_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(test_content)

            return ToolResponse(
                success=True, data={"test_file": str(path), "created": True}
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "test_path": {"type": "string"},
                "test_content": {"type": "string"},
            },
            "required": ["test_path", "test_content"],
        }


class IssueFixerAgent(BaseAgent):
    """
    Agent that applies fixes described in issue files.
    Handles documentation updates, code fixes, and test implementations.
    """

    def register_tools(self) -> List[Tool]:
        """Register fixer tools"""
        return [IssueParserTool(), FileEditorTool(), TestCreatorTool()]

    def execute_task(self, task: str) -> ToolResponse:
        """
        Execute issue fix based on issue file.
        Task format: issue number or path to issue file
        """

        # Find issue file
        if task.isdigit():
            issue_num = task.zfill(3)
            issue_files = list(Path("issues").glob(f"{issue_num}*.md"))
            if not issue_files:
                return ToolResponse(
                    success=False, error=f"No issue file found for #{issue_num}"
                )
            issue_path = issue_files[0]
        else:
            issue_path = Path(task)
            if not issue_path.exists():
                # Try in issues directory
                issue_path = Path("issues") / task
                if not issue_path.exists():
                    return ToolResponse(
                        success=False, error=f"Issue file not found: {task}"
                    )

        print(f"\n📋 Parsing issue: {issue_path.name}")

        # Parse the issue
        parser = self.tools[0]
        parse_result = parser.execute(str(issue_path))
        if not parse_result.success:
            return parse_result

        issue_data = parse_result.data
        print(f"📝 Issue #{issue_data['issue_number']}: {issue_data['title']}")

        # Apply fixes based on issue type
        if (
            "test" in issue_data["title"].lower()
            or "testing" in issue_data["title"].lower()
        ):
            # Create test file
            if issue_data["code_blocks"]:
                test_content = issue_data["code_blocks"][0]
                test_path = "tests/test_integration_guide.py"

                print(f"🧪 Creating test file: {test_path}")
                test_tool = self.tools[2]
                result = test_tool.execute(test_path, test_content)

                if result.success:
                    print(f"✅ Test file created: {test_path}")
                    self.state.set(f"issue_{issue_data['issue_number']}_resolved", True)
                    return result
                else:
                    return result

        elif (
            issue_data["target_file"]
            or "Implementation" in issue_data["implementation"]
        ):
            # Look for multiple files to update
            files_to_update = []

            # Check for explicit file paths in implementation
            impl_files = re.findall(
                r'Update\s+[`"]?([/\w.-]+\.\w+)[`"]?', issue_data["implementation"]
            )
            for f in impl_files:
                if f.startswith("/"):
                    f = f[1:]
                if f not in files_to_update:
                    files_to_update.append(f)

            # If no files found, use the target_file
            if not files_to_update and issue_data["target_file"]:
                files_to_update = [issue_data["target_file"]]

            if not files_to_update:
                return ToolResponse(success=False, error="No target files found")

            # Process each file
            results = []
            for target in files_to_update:
                if target.startswith("/"):
                    target = target[1:]  # Remove leading slash

                print(f"📝 Editing file: {target}")

            # Build changes from issue content
            changes = []

            # Look for specific old/new patterns in solution
            issue_content = Path(issue_path).read_text()  # Read full issue content

            # Pattern 1: Current/Fixed code blocks
            old_new_matches = re.findall(
                r"(?:Current broken code|Current|Problem):\s*```(?:python)?\n(.*?)```.*?(?:Fixed code|Solution|Should be):\s*```(?:python)?\n(.*?)```",
                issue_content,
                re.DOTALL | re.IGNORECASE,
            )

            for old, new in old_new_matches:
                changes.append({"old": old.strip(), "new": new.strip()})

            # Pattern 2: Simple Problem/Solution sections
            if not changes:
                problem_match = re.search(
                    r"## Problem\s*\n```(?:python)?\n(.*?)```", issue_content, re.DOTALL
                )
                solution_match = re.search(
                    r"## Solution\s*\n```(?:python)?\n(.*?)```",
                    issue_content,
                    re.DOTALL,
                )

                if problem_match and solution_match:
                    changes.append(
                        {
                            "old": problem_match.group(1).strip(),
                            "new": solution_match.group(1).strip(),
                        }
                    )

            # Pattern 3: Current/Should be patterns in numbered sections
            if not changes:
                sections = re.findall(
                    r"### \d+\.\s+[^\n]+\nCurrent[^\n]*:\s*```(?:python|bash)?\n(.*?)```\s*Should be:\s*```(?:python|bash)?\n(.*?)```",
                    issue_content,
                    re.DOTALL | re.IGNORECASE,
                )
                for old, new in sections:
                    changes.append({"old": old.strip(), "new": new.strip()})

            # If no old/new patterns, look for general fixes
            if not changes and issue_data["code_blocks"]:
                # For import issues, prepend imports
                if "import" in issue_data["title"].lower():
                    for block in issue_data["code_blocks"]:
                        if "import" in block:
                            changes.append({"prepend": block.strip()})
                            break

                if changes:
                    editor = self.tools[1]
                    result = editor.execute(target, changes)

                    if result.success:
                        print(f"✅ File updated: {target}")
                        results.append({"file": target, "status": "updated"})
                    else:
                        print(f"❌ Failed to update: {target}")
                        results.append(
                            {"file": target, "status": "failed", "error": result.error}
                        )

            # Return overall result
            if results:
                successful = [r for r in results if r["status"] == "updated"]
                if successful:
                    self.state.set(f"issue_{issue_data['issue_number']}_resolved", True)
                    return ToolResponse(
                        success=True,
                        data={"files_updated": len(successful), "results": results},
                    )
                else:
                    return ToolResponse(
                        success=False,
                        error="No files were successfully updated",
                        data={"results": results},
                    )
            else:
                return ToolResponse(
                    success=False,
                    error="Could not determine what changes to make from issue description",
                )

        return ToolResponse(
            success=False, error="Could not determine how to fix this issue"
        )

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply fix action"""
        action_type = action.get("type", "fix")

        if action_type == "fix":
            return self.execute_task(action.get("issue", ""))

        return ToolResponse(success=False, error=f"Unknown action type: {action_type}")


# Self-test when run directly
# Usage: uv run agents/issue_fixer_agent.py
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        issue = sys.argv[1]
    else:
        # Default to testing with issue 061
        issue = "061"

    print(f"🔧 Testing IssueFixerAgent with issue #{issue}...")
    agent = IssueFixerAgent()

    result = agent.execute_task(issue)

    if result.success:
        print(f"\n✅ Issue #{issue} fixed successfully!")
        print(json.dumps(result.data, indent=2))
    else:
        print(f"\n❌ Failed to fix issue #{issue}: {result.error}")
