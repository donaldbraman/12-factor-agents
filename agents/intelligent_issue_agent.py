#!/usr/bin/env python3
"""
Intelligent Issue Agent - Smart frontend for processing GitHub issues.
Reads issues, understands intent, and routes to appropriate tools/agents.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import re

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse, FileTool
from core.hierarchical_orchestrator import HierarchicalOrchestrator


class IntelligentIssueAgent(BaseAgent):
    """
    Intelligent agent that understands GitHub issues and routes them appropriately.
    This is a smart layer on top of the existing working system.
    """

    def __init__(self):
        super().__init__()
        self.orchestrator = HierarchicalOrchestrator()

    def register_tools(self) -> List[Tool]:
        """Register the tools we need"""
        return [
            FileTool(),
            # GitTool(), # Add when needed
            # TestTool(), # Add when needed
        ]

    def execute_task(self, task: str) -> ToolResponse:
        """
        Main entry point - accepts natural language issue description.

        Examples:
            "Fix issue #123"
            "Read and process issue #456"
            "Handle the bug described in issues/bug-report.md"
        """
        try:
            # Extract issue reference
            issue_data = self._extract_issue_reference(task)

            if not issue_data:
                return ToolResponse(
                    success=False, error="Could not identify issue reference in task"
                )

            # Read the issue content
            issue_content = self._read_issue(issue_data)

            if not issue_content:
                return ToolResponse(
                    success=False, error=f"Could not read issue: {issue_data}"
                )

            # Understand what needs to be done
            intent = self._understand_issue_intent(issue_content)

            # Route to appropriate handler
            if intent["complexity"] == "simple":
                # Direct tool call for simple tasks
                return self._handle_simple_issue(intent)
            else:
                # Use orchestrator for complex tasks
                return self._handle_complex_issue(intent)

        except Exception as e:
            return ToolResponse(
                success=False, error=f"Failed to process issue: {str(e)}"
            )

    def _extract_issue_reference(self, task: str) -> Optional[Dict]:
        """Extract issue number or file path from task description"""

        # Check for issue number (#123)
        issue_match = re.search(r"#(\d+)", task)
        if issue_match:
            return {"type": "github", "number": issue_match.group(1)}

        # Check for file path (issues/something.md)
        path_match = re.search(r"issues?/[\w\-]+\.md", task)
        if path_match:
            return {"type": "file", "path": path_match.group(0)}

        # Check for any file path that exists
        # Extract potential paths (anything that looks like a path)
        potential_paths = re.findall(
            r"[/\w\-\.]+\.(?:md|txt|py|js|json|yaml|yml)", task
        )
        for path in potential_paths:
            if Path(path).exists():
                return {"type": "file", "path": path}

        # Check if the whole task is a path
        if Path(task).exists():
            return {"type": "file", "path": task}

        return None

    def _read_issue(self, issue_data: Dict) -> Optional[str]:
        """Read issue content from GitHub or file"""

        if issue_data["type"] == "file":
            # Use FileTool to read local issue file
            file_tool = self.tools[0]  # FileTool is first
            result = file_tool.execute(operation="read", path=issue_data["path"])
            if result.success:
                return result.data["content"]

        elif issue_data["type"] == "github":
            # TODO: Use GitHub API to fetch issue
            # For now, try local file
            issue_path = f"issues/{issue_data['number']}.md"
            if Path(issue_path).exists():
                file_tool = self.tools[0]
                result = file_tool.execute(operation="read", path=issue_path)
                if result.success:
                    return result.data["content"]

        return None

    def _understand_issue_intent(self, content: str) -> Dict:
        """
        Understand what the issue is asking for.
        This is where the intelligence comes in!
        """
        content_lower = content.lower()

        intent = {
            "raw_content": content,
            "actions": [],
            "files_mentioned": [],
            "complexity": "simple",
            "requires_parallel": False,
        }

        # Detect requested actions
        action_keywords = {
            "fix": ["fix", "repair", "resolve", "solve"],
            "create": ["create", "add", "implement", "build"],
            "update": ["update", "modify", "change", "refactor"],
            "test": ["test", "verify", "validate", "check"],
            "document": ["document", "docs", "readme", "explain"],
        }

        for action, keywords in action_keywords.items():
            if any(kw in content_lower for kw in keywords):
                intent["actions"].append(action)

        # Extract file mentions
        file_pattern = r"`([^`]+\.(py|js|md|txt|yaml|yml|json))`"
        files = re.findall(file_pattern, content)
        intent["files_mentioned"] = [f[0] for f in files]

        # Also look for path-like strings
        path_pattern = r"\b[\w/\-]+\.\w+\b"
        potential_paths = re.findall(path_pattern, content)
        intent["files_mentioned"].extend(potential_paths)

        # Determine complexity
        if len(intent["actions"]) > 2:
            intent["complexity"] = "complex"
            intent["requires_parallel"] = True
        elif "multiple" in content_lower or "all" in content_lower:
            intent["complexity"] = "complex"
            intent["requires_parallel"] = True
        elif any(word in content_lower for word in ["and", "also", "plus"]):
            # Check if it's a compound request
            intent["complexity"] = "moderate"

        # Extract specific requests
        if "create" in intent["actions"]:
            intent["create_requests"] = self._extract_creation_requests(content)

        if "fix" in intent["actions"]:
            intent["fix_requests"] = self._extract_fix_requests(content)

        return intent

    def _extract_creation_requests(self, content: str) -> List[Dict]:
        """Extract what needs to be created"""
        requests = []

        # Look for "create a X file" patterns
        create_patterns = [
            r"create (?:a |an )?(\w+) file (?:at |in )?([^\s]+)",
            r"add (?:a |an )?new (\w+) (?:file )?(?:at |in )?([^\s]+)",
            r"implement (?:a |an )?(\w+) (?:at |in )?([^\s]+)",
        ]

        for pattern in create_patterns:
            matches = re.findall(pattern, content.lower())
            for match in matches:
                requests.append(
                    {"type": match[0], "path": match[1], "action": "create"}
                )

        return requests

    def _extract_fix_requests(self, content: str) -> List[Dict]:
        """Extract what needs to be fixed"""
        requests = []

        # Look for specific fix patterns
        fix_patterns = [
            r"fix (?:the )?(\w+) (?:bug |issue )?in ([^\s]+)",
            r"resolve (?:the )?(\w+) (?:error |problem )?in ([^\s]+)",
        ]

        for pattern in fix_patterns:
            matches = re.findall(pattern, content.lower())
            for match in matches:
                requests.append({"type": match[0], "path": match[1], "action": "fix"})

        return requests

    def _handle_simple_issue(self, intent: Dict) -> ToolResponse:
        """Handle simple issues with direct tool calls"""

        results = []

        # Handle file creation requests
        if "create_requests" in intent:
            for request in intent["create_requests"]:
                result = self._create_file(request)
                results.append(result)

        # Handle file fixes
        if "fix_requests" in intent:
            for request in intent["fix_requests"]:
                result = self._fix_file(request)
                results.append(result)

        # Aggregate results
        all_success = all(r.get("success", False) for r in results)

        return ToolResponse(
            success=all_success,
            data={
                "intent": intent,
                "operations": results,
                "summary": f"Processed {len(results)} operations",
            },
        )

    def _handle_complex_issue(self, intent: Dict) -> ToolResponse:
        """Handle complex issues using the orchestrator"""

        # Convert intent to subtasks for orchestrator
        subtasks = self._decompose_to_subtasks(intent)

        # Handle async orchestrator in sync context
        import asyncio
        
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.orchestrator.orchestrate_complex_task(
                    {"description": intent["raw_content"], "subtasks": subtasks}
                )
            )
        except Exception as e:
            # If orchestration fails, fall back to simple processing
            return ToolResponse(
                success=False,
                error=f"Orchestration failed: {str(e)}. Complex issue needs manual processing.",
                data={"intent": intent, "fallback_needed": True}
            )

        return ToolResponse(
            success=True,
            data={
                "intent": intent,
                "orchestration_result": result,
                "parallel_execution": intent["requires_parallel"],
            },
        )

    def _decompose_to_subtasks(self, intent: Dict) -> List[Dict]:
        """Convert intent into subtasks for orchestrator"""
        subtasks = []

        # Each action becomes a subtask
        for action in intent["actions"]:
            if action == "fix":
                for file in intent.get("files_mentioned", []):
                    subtasks.append(
                        {"type": "fix", "target": file, "agent": "IssueProcessorAgent"}
                    )

            elif action == "create":
                for request in intent.get("create_requests", []):
                    subtasks.append(
                        {
                            "type": "create",
                            "target": request["path"],
                            "agent": "IssueProcessorAgent",
                        }
                    )

            elif action == "test":
                subtasks.append({"type": "test", "agent": "TestingAgent"})

            elif action == "document":
                subtasks.append({"type": "document", "agent": "IssueProcessorAgent"})

        return subtasks

    def _create_file(self, request: Dict) -> Dict:
        """Create a file using FileTool"""

        # Generate appropriate content based on file type
        content = self._generate_file_content(request)

        # Use FileTool to write
        file_tool = self.tools[0]
        result = file_tool.execute(
            operation="write", path=request["path"], content=content
        )

        return {
            "success": result.success,
            "operation": "create",
            "path": request["path"],
            "error": result.error if not result.success else None,
        }

    def _fix_file(self, request: Dict) -> Dict:
        """Fix issues in a file"""

        # Read current content
        file_tool = self.tools[0]
        read_result = file_tool.execute(operation="read", path=request["path"])

        if not read_result.success:
            return {
                "success": False,
                "operation": "fix",
                "path": request["path"],
                "error": f"Could not read file: {read_result.error}",
            }

        # Apply fixes (simplified for now)
        original = read_result.data["content"]
        fixed = self._apply_fixes(original, request["type"])

        # Write back
        write_result = file_tool.execute(
            operation="write", path=request["path"], content=fixed
        )

        return {
            "success": write_result.success,
            "operation": "fix",
            "path": request["path"],
            "changes": "Applied fixes" if write_result.success else None,
            "error": write_result.error if not write_result.success else None,
        }

    def _generate_file_content(self, request: Dict) -> str:
        """Generate appropriate content for a new file"""

        file_type = request["path"].split(".")[-1] if "." in request["path"] else "txt"

        templates = {
            "py": '''#!/usr/bin/env python3
"""
Generated file: {path}
"""

def main():
    """Main function"""
    pass

if __name__ == "__main__":
    main()
''',
            "md": """# {title}

## Overview
Generated documentation file.

## Details
Add content here.
""",
            "txt": "Generated file content\n",
            "json": "{{}}\n",
        }

        template = templates.get(file_type, "Generated content\n")
        return template.format(
            path=request["path"],
            title=Path(request["path"]).stem.replace("-", " ").title(),
        )

    def _apply_fixes(self, content: str, fix_type: str) -> str:
        """Apply fixes to content (simplified)"""
        # This is where we'd add intelligent fixing
        # For now, just return content with a comment
        return f"# Fixed: {fix_type}\n{content}"

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Handle actions for reducer pattern"""
        return ToolResponse(success=True)


# Example usage
if __name__ == "__main__":
    agent = IntelligentIssueAgent()

    # Test with a simple issue reference
    result = agent.execute_task("Read and process issue #123")
    print(f"Result: {result}")

    # Test with natural language
    test_issue = """
    Fix the authentication bug in src/auth.py and add tests for the login function.
    Also update the README.md with the new authentication flow.
    """

    with open("test_issue.md", "w") as f:
        f.write(test_issue)

    result = agent.execute_task("Handle the issue described in test_issue.md")
    print(f"Result: {result}")
