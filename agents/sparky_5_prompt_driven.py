#!/usr/bin/env python3
"""
SPARKY 5.0: Prompt-Driven Edition
Factor 2 Compliant: All logic driven by prompts, not hardcoded

Key improvements:
- Uses PromptManager to load prompts from files
- LLM-based issue parsing (no hardcoded if/elif chains)
- Structured action generation via prompts
- Clean separation of logic and code
"""

import json
import os
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.prompt_manager import PromptManager
from anthropic import Anthropic


class ActionType(Enum):
    """Action types SPARKY can execute"""

    ADD_COMMENT = "ADD_COMMENT"
    REPLACE_TEXT = "REPLACE_TEXT"
    REFACTOR_FUNCTION = "REFACTOR_FUNCTION"
    CREATE_FILE = "CREATE_FILE"
    ADD_ERROR_HANDLING = "ADD_ERROR_HANDLING"


@dataclass
class StructuredAction:
    """Structured action for execution"""

    action_type: ActionType
    file_path: str
    parameters: Dict[str, Any]


class PromptDrivenParser:
    """Parse issues using LLM and prompts"""

    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def parse_issue(self, issue_content: str) -> List[StructuredAction]:
        """Parse issue into structured actions using LLM"""

        # Load the issue analyzer prompt
        prompt_template = self.prompt_manager.load_prompt("sparky/issue_analyzer")
        if not prompt_template:
            raise ValueError("Could not load issue_analyzer prompt")

        # Create the full prompt with issue content
        full_prompt = f"{prompt_template}\n\nISSUE CONTENT:\n{issue_content}"

        try:
            # Call LLM to parse the issue
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Fast, cost-effective for parsing
                max_tokens=2000,
                messages=[{"role": "user", "content": full_prompt}],
            )

            # Extract JSON from response
            response_text = response.content[0].text

            # Find JSON block in response
            start = response_text.find("[")
            end = response_text.rfind("]") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON array found in response")

            json_str = response_text[start:end]
            actions_data = json.loads(json_str)

            # Convert to StructuredAction objects
            actions = []
            for action_data in actions_data:
                action = StructuredAction(
                    action_type=ActionType(action_data["action_type"]),
                    file_path=action_data["file_path"],
                    parameters=action_data.get("parameters", {}),
                )
                actions.append(action)

            return actions

        except Exception as e:
            print(f"Error parsing issue with LLM: {e}")
            # Fallback to empty actions
            return []


class ActionExecutor:
    """Execute structured actions on the file system"""

    def execute(self, action: StructuredAction) -> Dict[str, Any]:
        """Execute a single action"""

        handlers = {
            ActionType.ADD_COMMENT: self._add_comment,
            ActionType.REPLACE_TEXT: self._replace_text,
            ActionType.REFACTOR_FUNCTION: self._refactor_function,
            ActionType.CREATE_FILE: self._create_file,
            ActionType.ADD_ERROR_HANDLING: self._add_error_handling,
        }

        handler = handlers.get(action.action_type)
        if not handler:
            return {
                "success": False,
                "error": f"No handler for action type {action.action_type}",
            }

        return handler(action)

    def _add_comment(self, action: StructuredAction) -> Dict[str, Any]:
        """Add a comment to a file"""
        file_path = Path(action.file_path)

        if not file_path.exists():
            return {"success": False, "error": f"File {file_path} not found"}

        params = action.parameters
        line_number = params.get("line_number", 1)
        comment_text = params.get("comment_text", "# Comment added by SPARKY")

        lines = file_path.read_text().splitlines(keepends=True)
        lines.insert(line_number - 1, f"    {comment_text}\n")
        file_path.write_text("".join(lines))

        return {
            "success": True,
            "action": "add_comment",
            "file": str(file_path),
            "line": line_number,
        }

    def _replace_text(self, action: StructuredAction) -> Dict[str, Any]:
        """Replace text in a file"""
        file_path = Path(action.file_path)

        if not file_path.exists():
            return {"success": False, "error": f"File {file_path} not found"}

        params = action.parameters
        old_text = params.get("old_text", "")
        new_text = params.get("new_text", "")

        content = file_path.read_text()
        if old_text not in content:
            return {"success": False, "error": "Text to replace not found"}

        updated_content = content.replace(old_text, new_text, 1)
        file_path.write_text(updated_content)

        return {"success": True, "action": "replace_text", "file": str(file_path)}

    def _refactor_function(self, action: StructuredAction) -> Dict[str, Any]:
        """Refactor a function name across files"""
        params = action.parameters
        old_name = params.get("old_name", "")
        new_name = params.get("new_name", "")

        # Find all Python files
        py_files = list(Path(".").glob("**/*.py"))
        modified_files = []

        for py_file in py_files:
            content = py_file.read_text()
            if old_name in content:
                updated_content = content.replace(old_name, new_name)
                py_file.write_text(updated_content)
                modified_files.append(str(py_file))

        return {
            "success": True,
            "action": "refactor_function",
            "modified_files": modified_files,
        }

    def _create_file(self, action: StructuredAction) -> Dict[str, Any]:
        """Create a new file"""
        file_path = Path(action.file_path)
        params = action.parameters
        content = params.get("content", "")

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content)

        return {"success": True, "action": "create_file", "file": str(file_path)}

    def _add_error_handling(self, action: StructuredAction) -> Dict[str, Any]:
        """Add error handling to a function"""
        file_path = Path(action.file_path)

        if not file_path.exists():
            return {"success": False, "error": f"File {file_path} not found"}

        params = action.parameters
        function_name = params.get("function_name", "")

        content = file_path.read_text()
        lines = content.splitlines()

        # Find the function
        func_start = None
        for i, line in enumerate(lines):
            if f"def {function_name}(" in line:
                func_start = i
                break

        if func_start is None:
            return {"success": False, "error": f"Function {function_name} not found"}

        # Find function body
        indent = len(lines[func_start]) - len(lines[func_start].lstrip())
        func_body_start = func_start + 1

        # Add try/except
        new_lines = lines[:func_body_start]
        new_lines.append(" " * (indent + 4) + "try:")

        # Indent existing function body
        for i in range(func_body_start, len(lines)):
            if lines[i].strip() and not lines[i].startswith(" " * (indent + 4)):
                break
            if lines[i].strip():
                new_lines.append(" " * 4 + lines[i])
            else:
                new_lines.append(lines[i])

        # Add except block
        new_lines.append(" " * (indent + 4) + "except Exception as e:")
        new_lines.append(
            " " * (indent + 8) + f"print(f'Error in {function_name}: {{e}}')"
        )
        new_lines.append(" " * (indent + 8) + "raise")

        file_path.write_text("\n".join(new_lines))

        return {
            "success": True,
            "action": "add_error_handling",
            "file": str(file_path),
            "function": function_name,
        }


class Sparky5PromptDriven:
    """SPARKY 5.0 - Fully prompt-driven agent"""

    def __init__(self):
        self.prompt_manager = PromptManager()
        self.parser = PromptDrivenParser(self.prompt_manager)
        self.executor = ActionExecutor()

    def process_issue(self, issue_file: Path) -> Dict[str, Any]:
        """Process an issue file"""

        # Read issue content
        if not issue_file.exists():
            return {"success": False, "error": f"Issue file {issue_file} not found"}

        issue_content = issue_file.read_text()

        # Parse issue into actions using LLM
        print("🧠 Parsing issue with LLM...")
        actions = self.parser.parse_issue(issue_content)

        if not actions:
            return {"success": False, "error": "No actions generated from issue"}

        print(f"📋 Generated {len(actions)} actions")

        # Execute actions
        results = []
        for action in actions:
            print(f"⚡ Executing {action.action_type.value} on {action.file_path}")
            result = self.executor.execute(action)
            results.append(result)

        # Create PR with changes
        branch_name = (
            f"sparky5/{issue_file.stem}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )

        try:
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)
            subprocess.run(["git", "add", "."], check=True)

            commit_msg = f"SPARKY 5.0: Process {issue_file.name} (Factor 2 Compliant)"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)

            # Create PR
            pr_body = "Automated changes from SPARKY 5.0 (Prompt-Driven)\n\nFactor 2 Compliant: Logic driven by prompts, not code"
            subprocess.run(
                ["gh", "pr", "create", "--title", commit_msg, "--body", pr_body],
                check=True,
            )

        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            return {"success": False, "error": str(e)}

        return {
            "success": True,
            "branch": branch_name,
            "actions_executed": len(actions),
            "results": results,
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python sparky_5_prompt_driven.py <issue_file>")
        sys.exit(1)

    issue_file = Path(sys.argv[1])

    sparky = Sparky5PromptDriven()
    result = sparky.process_issue(issue_file)

    print("\n✨ SPARKY 5.0 Complete!")
    print(json.dumps(result, indent=2, default=str))
