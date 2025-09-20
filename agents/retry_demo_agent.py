#!/usr/bin/env uv run python
"""
RetryDemoAgent - Demonstrates comprehensive retry capabilities for common agent failures.

This agent showcases all retry patterns and can be used as a template for building
resilient agents that handle transient failures gracefully.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent  # noqa: E402
from core.tools import Tool, ToolResponse  # noqa: E402
from core.execution_context import ExecutionContext  # noqa: E402
from core.retry import retry, RetryConfig  # noqa: E402
from core.retry_wrappers import (  # noqa: E402
    RetryFileOperations,
    subprocess_run,
    read_text,
    write_text,
    get_git_ops,
)
from core.telemetry import EnhancedTelemetryCollector, EventType  # noqa: E402


class RetryFileOperationsTool(Tool):
    """Demonstrates file operations with retry logic"""

    def __init__(self):
        super().__init__(
            name="retry_file_ops",
            description="Demonstrate file operations with retry logic",
        )

    def execute(
        self, operation: str, file_path: str, content: str = None
    ) -> ToolResponse:
        """Execute file operations with built-in retry logic"""
        try:
            path = Path(file_path)

            if operation == "read":
                # Read file with retry logic
                content = read_text(path)
                return ToolResponse(
                    success=True,
                    data={"operation": "read", "content": content, "file": str(path)},
                )

            elif operation == "write":
                if content is None:
                    return ToolResponse(
                        success=False, error="Content required for write operation"
                    )

                # Write file with retry logic
                write_text(path, content, create_dirs=True)
                return ToolResponse(
                    success=True,
                    data={
                        "operation": "write",
                        "file": str(path),
                        "size": len(content),
                    },
                )

            elif operation == "copy":
                # Demonstrate copy with retry logic
                dest_path = path.with_suffix(path.suffix + ".backup")
                RetryFileOperations.copy(path, dest_path)
                return ToolResponse(
                    success=True,
                    data={
                        "operation": "copy",
                        "source": str(path),
                        "dest": str(dest_path),
                    },
                )

            else:
                return ToolResponse(
                    success=False, error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "copy"],
                    "description": "File operation to perform",
                },
                "file_path": {"type": "string", "description": "Path to file"},
                "content": {
                    "type": "string",
                    "description": "Content for write operations",
                },
            },
            "required": ["operation", "file_path"],
        }


class RetryGitOperationsTool(Tool):
    """Demonstrates Git operations with retry logic"""

    def __init__(self):
        super().__init__(
            name="retry_git_ops",
            description="Demonstrate Git operations with retry logic",
        )

    def execute(self, operation: str, repo_path: str = None, **kwargs) -> ToolResponse:
        """Execute Git operations with built-in retry logic"""
        try:
            git_ops = get_git_ops(Path(repo_path) if repo_path else None)

            if operation == "status":
                # Get repository status with retry
                status = git_ops.status(porcelain=kwargs.get("porcelain", False))
                return ToolResponse(
                    success=True, data={"operation": "status", "output": status}
                )

            elif operation == "add":
                # Add files with retry
                files = kwargs.get("files", ".")
                git_ops.add(files, all_files=kwargs.get("all_files", False))
                return ToolResponse(
                    success=True, data={"operation": "add", "files": files}
                )

            elif operation == "commit":
                # Commit with retry
                message = kwargs.get("message", "Automated commit with retry logic")
                output = git_ops.commit(
                    message, allow_empty=kwargs.get("allow_empty", False)
                )
                return ToolResponse(
                    success=True,
                    data={"operation": "commit", "message": message, "output": output},
                )

            elif operation == "pull":
                # Pull with retry
                remote = kwargs.get("remote", "origin")
                branch = kwargs.get("branch")
                output = git_ops.pull(remote, branch)
                return ToolResponse(
                    success=True,
                    data={"operation": "pull", "remote": remote, "output": output},
                )

            elif operation == "push":
                # Push with retry
                remote = kwargs.get("remote", "origin")
                branch = kwargs.get("branch")
                force = kwargs.get("force", False)
                output = git_ops.push(remote, branch, force)
                return ToolResponse(
                    success=True,
                    data={"operation": "push", "remote": remote, "output": output},
                )

            else:
                return ToolResponse(
                    success=False, error=f"Unknown Git operation: {operation}"
                )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["status", "add", "commit", "pull", "push"],
                    "description": "Git operation to perform",
                },
                "repo_path": {
                    "type": "string",
                    "description": "Repository path (optional, defaults to current directory)",
                },
                "files": {
                    "type": "string",
                    "description": "Files to add (for add operation)",
                },
                "message": {
                    "type": "string",
                    "description": "Commit message (for commit operation)",
                },
                "remote": {
                    "type": "string",
                    "description": "Remote name (for push/pull operations)",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (for push/pull operations)",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force push (for push operation)",
                },
                "allow_empty": {
                    "type": "boolean",
                    "description": "Allow empty commits (for commit operation)",
                },
                "all_files": {
                    "type": "boolean",
                    "description": "Add all files (for add operation)",
                },
                "porcelain": {
                    "type": "boolean",
                    "description": "Use porcelain format (for status operation)",
                },
            },
            "required": ["operation"],
        }


class RetrySubprocessTool(Tool):
    """Demonstrates subprocess operations with retry logic"""

    def __init__(self):
        super().__init__(
            name="retry_subprocess",
            description="Demonstrate subprocess operations with retry logic",
        )

    def execute(self, command: List[str], **kwargs) -> ToolResponse:
        """Execute subprocess command with retry logic"""
        try:
            # Use retry-enabled subprocess wrapper
            result = subprocess_run(
                command,
                capture_output=kwargs.get("capture_output", True),
                text=kwargs.get("text", True),
                timeout=kwargs.get("timeout", 30),
                check=kwargs.get("check", True),
            )

            return ToolResponse(
                success=True,
                data={
                    "command": command,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Command and arguments to execute",
                },
                "capture_output": {
                    "type": "boolean",
                    "description": "Capture stdout/stderr",
                },
                "text": {
                    "type": "boolean",
                    "description": "Return strings instead of bytes",
                },
                "timeout": {
                    "type": "number",
                    "description": "Command timeout in seconds",
                },
                "check": {
                    "type": "boolean",
                    "description": "Raise exception on non-zero exit",
                },
            },
            "required": ["command"],
        }


class CustomRetryOperationTool(Tool):
    """Demonstrates custom retry policies"""

    def __init__(self):
        super().__init__(
            name="custom_retry",
            description="Demonstrate custom retry policies for specific operations",
        )

    @retry(
        RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=10.0,
            exponential_base=1.8,
            jitter=True,
            backoff_strategy="exponential",
        ),
        "custom_operation",
    )
    def _risky_operation(self, operation_type: str, failure_rate: float = 0.3) -> str:
        """Simulate a risky operation that might fail"""
        import random

        if random.random() < failure_rate:
            if operation_type == "network":
                raise ConnectionError(
                    f"Simulated network failure (rate: {failure_rate})"
                )
            elif operation_type == "filesystem":
                raise OSError(f"Simulated filesystem error (rate: {failure_rate})")
            else:
                raise Exception(
                    f"Simulated failure for {operation_type} (rate: {failure_rate})"
                )

        return f"Successfully completed {operation_type} operation!"

    def execute(self, operation_type: str, failure_rate: float = 0.3) -> ToolResponse:
        """Execute operation with custom retry policy"""
        try:
            result = self._risky_operation(operation_type, failure_rate)
            return ToolResponse(
                success=True,
                data={
                    "operation_type": operation_type,
                    "failure_rate": failure_rate,
                    "result": result,
                },
            )
        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation_type": {
                    "type": "string",
                    "enum": ["network", "filesystem", "database", "external_api"],
                    "description": "Type of operation to simulate",
                },
                "failure_rate": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Probability of failure (0.0 = never fail, 1.0 = always fail)",
                },
            },
            "required": ["operation_type"],
        }


class RetryDemoAgent(BaseAgent):
    """
    Demonstrates comprehensive retry capabilities for agent operations.

    This agent can be used to test and demonstrate:
    - File operations with retry logic
    - Git operations with specialized retry handling
    - Subprocess execution with retry capabilities
    - Custom retry policies for specific failure patterns
    """

    def __init__(self):
        super().__init__(
            name="RetryDemoAgent",
            description="Demonstrates comprehensive retry capabilities for common agent failures",
            version="1.0.0",
        )

        # Add all demonstration tools
        self.tools = [
            RetryFileOperationsTool(),
            RetryGitOperationsTool(),
            RetrySubprocessTool(),
            CustomRetryOperationTool(),
        ]

        self.telemetry = EnhancedTelemetryCollector()

    def process_issue(
        self, issue_data: Dict[str, Any], context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Process issues to demonstrate retry capabilities

        This method processes different types of issues to showcase retry logic:
        - File operation issues
        - Git operation issues
        - Subprocess execution issues
        - Custom retry scenarios
        """

        issue_title = issue_data.get("title", "").lower()
        issue_content = issue_data.get("content", "").lower()

        self.telemetry.record_workflow_event(
            EventType.AGENT_DISPATCH,
            context.current_repo,
            self.name,
            f"Processing retry demo for issue: {issue_data.get('title', 'Unknown')}",
        )

        results = {
            "agent": self.name,
            "issue_number": issue_data.get("number"),
            "demonstrations": [],
            "success": True,
            "retry_stats": {},
        }

        try:
            # Demonstrate different retry scenarios based on issue content
            if "file" in issue_title or "filesystem" in issue_content:
                self._demo_file_operations(results, context)

            if "git" in issue_title or "repository" in issue_content:
                self._demo_git_operations(results, context)

            if "subprocess" in issue_title or "command" in issue_content:
                self._demo_subprocess_operations(results, context)

            if "custom" in issue_title or "retry" in issue_content:
                self._demo_custom_retry(results, context)

            # If no specific demonstrations, run a comprehensive demo
            if not results["demonstrations"]:
                self._run_comprehensive_demo(results, context)

            self.telemetry.record_workflow_event(
                EventType.AGENT_SUCCESS,
                context.current_repo,
                self.name,
                "Successfully demonstrated retry capabilities",
            )

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)

            self.telemetry.record_workflow_event(
                EventType.AGENT_FAILURE,
                context.current_repo,
                self.name,
                f"Failed to demonstrate retry capabilities: {e}",
            )

        return results

    def _demo_file_operations(self, results: Dict, context: ExecutionContext):
        """Demonstrate file operations with retry logic"""
        demo_file = Path(context.working_directory) / "retry_demo.txt"

        # Write file with retry
        tool_response = self.tools[0].execute(
            "write",
            str(demo_file),
            "This file demonstrates retry logic for file operations.",
        )

        if tool_response.success:
            results["demonstrations"].append(
                {"type": "file_write", "result": tool_response.data}
            )

        # Read file with retry
        tool_response = self.tools[0].execute("read", str(demo_file))

        if tool_response.success:
            results["demonstrations"].append(
                {"type": "file_read", "result": tool_response.data}
            )

    def _demo_git_operations(self, results: Dict, context: ExecutionContext):
        """Demonstrate Git operations with retry logic"""
        # Git status with retry
        tool_response = self.tools[1].execute(
            "status", repo_path=str(context.working_directory), porcelain=True
        )

        if tool_response.success:
            results["demonstrations"].append(
                {"type": "git_status", "result": tool_response.data}
            )

    def _demo_subprocess_operations(self, results: Dict, context: ExecutionContext):
        """Demonstrate subprocess operations with retry logic"""
        # Simple command with retry
        tool_response = self.tools[2].execute(
            ["echo", "Retry demo subprocess execution"], capture_output=True, text=True
        )

        if tool_response.success:
            results["demonstrations"].append(
                {"type": "subprocess_echo", "result": tool_response.data}
            )

    def _demo_custom_retry(self, results: Dict, context: ExecutionContext):
        """Demonstrate custom retry policies"""
        # Test with different failure rates
        for failure_rate in [0.7, 0.5, 0.2]:
            tool_response = self.tools[3].execute("network", failure_rate=failure_rate)

            results["demonstrations"].append(
                {
                    "type": f"custom_retry_failure_rate_{failure_rate}",
                    "success": tool_response.success,
                    "result": tool_response.data
                    if tool_response.success
                    else tool_response.error,
                }
            )

    def _run_comprehensive_demo(self, results: Dict, context: ExecutionContext):
        """Run a comprehensive demonstration of all retry capabilities"""
        self._demo_file_operations(results, context)
        self._demo_git_operations(results, context)
        self._demo_subprocess_operations(results, context)
        self._demo_custom_retry(results, context)

    def get_capabilities(self) -> List[str]:
        return [
            "retry_file_operations",
            "retry_git_operations",
            "retry_subprocess_execution",
            "custom_retry_policies",
            "failure_telemetry",
            "exponential_backoff",
            "jitter_support",
            "configurable_policies",
        ]
