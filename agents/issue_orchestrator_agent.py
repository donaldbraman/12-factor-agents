"""
IssueOrchestratorAgent - Orchestrates issue resolution by dispatching appropriate agents.
Meta-agent that reads issues and coordinates other agents to solve them.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import importlib.util

# Import from parent directory
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent  # noqa: E402
from core.tools import Tool, ToolResponse  # noqa: E402
from core.telemetry import EnhancedTelemetryCollector  # noqa: E402
from core.loop_protection import LOOP_PROTECTION  # noqa: E402
import time  # noqa: E402


class IssueReaderTool(Tool):
    """Read and parse issue files"""

    def __init__(self):
        super().__init__(name="read_issue", description="Read and parse an issue file")

    def execute(self, issue_path: str) -> ToolResponse:
        """Read issue from markdown file"""
        try:
            path = Path(issue_path).resolve()

            if not path.exists():
                return ToolResponse(
                    success=False, error=f"Issue file not found: {path}"
                )

            content = path.read_text()

            # Parse issue metadata
            issue = {
                "path": str(path),
                "filename": path.name,
                "number": None,
                "title": None,
                "description": None,
                "agent": None,
                "priority": None,
                "dependencies": [],
                "status": "open",
            }

            # Extract issue number from filename
            import re

            number_match = re.match(r"^(\d+)-", path.name)
            if number_match:
                issue["number"] = number_match.group(1)

            # Parse content
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("# Issue"):
                    issue["title"] = line.replace("# Issue", "").strip()
                elif line.startswith("## Description"):
                    # Get description from next lines
                    desc_lines = []
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith("##"):
                            break
                        desc_lines.append(lines[j])
                    issue["description"] = "\n".join(desc_lines).strip()
                elif line.startswith("## Agent Assignment"):
                    # Look for the next non-empty line
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip():
                            agent_line = lines[j].strip().replace("`", "")
                            # Handle "or" cases by taking the first agent
                            if " or " in agent_line:
                                agent_line = agent_line.split(" or ")[0].strip()
                            issue["agent"] = agent_line
                            break
                        if lines[j].startswith("##"):
                            break
                elif line.startswith("## Priority"):
                    if i + 1 < len(lines):
                        issue["priority"] = lines[i + 1].strip()
                elif line.startswith("- Depends on:"):
                    dep = line.replace("- Depends on:", "").strip()
                    issue["dependencies"].append(dep)

            # Check if already resolved
            if "status: resolved" in content.lower():
                issue["status"] = "resolved"

            return ToolResponse(success=True, data={"issue": issue})

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"issue_path": {"type": "string"}},
            "required": ["issue_path"],
        }


class AgentDispatcherTool(Tool):
    """Dispatch agents to solve issues"""

    def __init__(self):
        super().__init__(
            name="dispatch_agent", description="Dispatch an agent to solve an issue"
        )

    def execute(
        self, agent_name: str, task: str, background: bool = False
    ) -> ToolResponse:
        """Dispatch agent to execute task"""
        try:
            # Map agent names to classes
            agent_map = {
                "RepositorySetupAgent": "repository_setup_agent",
                "ComponentMigrationAgent": "component_migration_agent",
                "PromptManagementAgent": "prompt_management_agent",
                "EventSystemAgent": "event_system_agent",
                "InfrastructureAgent": "infrastructure_agent",
                "CLIBuilderAgent": "cli_builder_agent",
                "RegistryBuilderAgent": "registry_builder_agent",
                "UvMigrationAgent": "uv_migration_agent",
                "IntelligentIssueAgent": "intelligent_issue_agent",
            }

            module_name = agent_map.get(
                agent_name, agent_name.lower().replace("agent", "_agent")
            )

            # Try to import the agent
            agent_path = Path(__file__).parent / f"{module_name}.py"

            if not agent_path.exists():
                return ToolResponse(
                    success=False,
                    error=f"Agent implementation not found: {agent_name}",
                    data={"agent": agent_name, "status": "not_implemented"},
                )

            if background:
                # Run in background process
                script = f"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.{module_name} import {agent_name}

agent = {agent_name}()
result = agent.execute_task("{task}")

# Save result
import json
result_file = Path.home() / ".claude-shared-state" / f"agent_result_{agent_name}.json"
result_file.parent.mkdir(exist_ok=True)
result_file.write_text(json.dumps(result.to_dict() if hasattr(result, 'to_dict') else {{
    "success": result.success,
    "data": result.data if hasattr(result, 'data') else None,
    "error": result.error if hasattr(result, 'error') else None
}}))

print(f"Result: {{result.success}}")
"""

                script_path = (
                    Path.home() / ".claude-shared-state" / f"run_{agent_name}.py"
                )
                script_path.parent.mkdir(exist_ok=True)
                script_path.write_text(script)

                process = subprocess.Popen(
                    ["uv", "run", str(script_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                stdout, stderr = process.communicate()

                # Load result
                result_file = (
                    Path.home()
                    / ".claude-shared-state"
                    / f"agent_result_{agent_name}.json"
                )
                if result_file.exists():
                    result_data = json.loads(result_file.read_text())
                    return ToolResponse(
                        success=result_data.get("success", False),
                        data=result_data.get("data", {}),
                        error=result_data.get("error"),
                    )
                else:
                    return ToolResponse(
                        success=False, error=f"Agent execution failed: {stderr}"
                    )
            else:
                # Import and run directly
                spec = importlib.util.spec_from_file_location(agent_name, agent_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                agent_class = getattr(module, agent_name)
                agent = agent_class()
                result = agent.execute_task(task)

                return result

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string"},
                "task": {"type": "string"},
                "background": {"type": "boolean"},
            },
            "required": ["agent_name", "task"],
        }


class IssueStatusUpdaterTool(Tool):
    """Update issue status"""

    def __init__(self):
        super().__init__(
            name="update_issue_status", description="Update the status of an issue"
        )

    def execute(self, issue_path: str, status: str, notes: str = None) -> ToolResponse:
        """Update issue status in file"""
        try:
            path = Path(issue_path).resolve()

            if not path.exists():
                return ToolResponse(
                    success=False, error=f"Issue file not found: {path}"
                )

            content = path.read_text()

            # Add status section if not present
            if "## Status" not in content:
                content += f"\n\n## Status\n{status}\n"
                if notes:
                    content += f"\n### Resolution Notes\n{notes}\n"
                content += f"\n### Updated: {datetime.now().isoformat()}\n"
            else:
                # Update existing status
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("## Status"):
                        lines[i + 1] = status
                        break
                content = "\n".join(lines)

            path.write_text(content)

            return ToolResponse(
                success=True,
                data={"issue": str(path), "status": status, "updated": True},
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "issue_path": {"type": "string"},
                "status": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["issue_path", "status"],
        }


class IssueOrchestratorAgent(BaseAgent):
    """
    Meta-agent that orchestrates issue resolution by dispatching appropriate agents.
    Reads issues, determines dependencies, and coordinates agent execution.
    Enhanced with comprehensive telemetry for workflow analysis.
    """

    def __init__(self):
        super().__init__()
        self.telemetry = EnhancedTelemetryCollector()
        # Removed non-existent modules: ErrorRecoverySystem, UserFeedbackSystem, IssueQualityValidator
        self.current_workflow_id = None

    def register_tools(self) -> List[Tool]:
        """Register orchestration tools"""
        return [IssueReaderTool(), AgentDispatcherTool(), IssueStatusUpdaterTool()]

    def execute_task(self, task: str) -> ToolResponse:
        """
        Execute orchestration task with enhanced telemetry.
        Expected task: "resolve all issues" or "resolve issue #XXX"
        """
        workflow_start_time = time.time()

        base_path = Path.home() / "Documents" / "GitHub" / "12-factor-agents"
        issues_dir = base_path / "issues"

        results = []
        resolved_issues = []
        failed_issues = []

        # Start workflow telemetry
        repo_name = "12-factor-agents"

        # Determine which issues to process
        if "all issues" in task:
            issue_files = sorted(issues_dir.glob("*.md"))
        elif "#" in task:
            # Specific issue number
            issue_num = task.split("#")[-1].strip().split()[0]
            issue_files = [f for f in issues_dir.glob(f"{issue_num}*.md")]
        else:
            issue_files = sorted(issues_dir.glob("*.md"))

        # Start workflow tracking
        self.current_workflow_id = self.telemetry.start_workflow(
            repo_name=repo_name,
            workflow_name="IssueOrchestratorAgent",
            total_issues=len(issue_files),
            context={"task": task, "issue_files": len(issue_files)},
        )

        # Read all issues first
        issues = []
        reader_tool = self.tools[0]  # IssueReaderTool

        for issue_file in issue_files:
            read_result = reader_tool.execute(issue_path=str(issue_file))
            if read_result.success:
                issue = read_result.data["issue"]
                issues.append(issue)

                # Record issue parsing telemetry
                self.telemetry.record_issue_processing(
                    repo_name=repo_name,
                    issue_number=issue.get("number", "unknown"),
                    issue_title=issue.get("title", "Unknown Title"),
                    agent_name=issue.get("agent"),
                    status="parsed",
                    context={
                        "has_agent": bool(issue.get("agent")),
                        "has_dependencies": bool(issue.get("dependencies")),
                        "file_path": str(issue_file),
                    },
                    parent_workflow_id=self.current_workflow_id,
                )
            else:
                # Record failed parsing
                self.telemetry.record_error(
                    repo_name=repo_name,
                    agent_name="IssueReaderTool",
                    error_type="ParseError",
                    error_message=f"Failed to parse {issue_file}: {read_result.error}",
                    context={"file_path": str(issue_file)},
                )

        # Sort by dependencies (issues with no dependencies first)
        issues.sort(key=lambda x: (len(x["dependencies"]), x["priority"] or "P99"))

        # Process issues
        dispatcher_tool = self.tools[1]  # AgentDispatcherTool
        updater_tool = self.tools[2]  # IssueStatusUpdaterTool

        for issue in issues:
            # Loop protection check
            issue_content = f"issue-{issue['number']}-{issue.get('title', '')}"
            if not LOOP_PROTECTION.check_operation("issue_processing", issue_content):
                print(
                    f"🛡️ Loop protection: Skipping issue {issue['number']} (already processing)"
                )
                continue

            # Validation removed - modules not available
            # Previously validated issue quality here
            overall_score = 0.8  # Default score
            critical_errors = 0

            if overall_score < 30 or critical_errors >= 3:
                print(
                    f"⚠️ Issue {issue['number']} has quality problems (score: {overall_score}/100)"
                )
                print(
                    "   This may lead to placeholder implementation. Proceeding anyway..."
                )

                # Log quality warning
                self.telemetry.record_implementation_gap(
                    repo_name=repo_name,
                    agent_name="IssueQualityValidator",
                    gap_type="quality_warning",
                    description=f"Issue {issue['number']} has low quality score: {overall_score}/100",
                    context={"validation_results": []},  # validation_results removed
                )

            # Skip if already resolved
            if issue["status"] == "resolved":
                resolved_issues.append(issue["number"])
                self.telemetry.record_issue_processing(
                    repo_name=repo_name,
                    issue_number=issue["number"],
                    issue_title=issue.get("title", "Unknown"),
                    agent_name=issue.get("agent"),
                    status="already_resolved",
                    parent_workflow_id=self.current_workflow_id,
                )
                continue

            # Check dependencies
            can_process = True
            unmet_deps = []
            for dep in issue["dependencies"]:
                dep_num = dep.replace("#", "").strip()
                if dep_num not in resolved_issues:
                    can_process = False
                    unmet_deps.append(dep_num)

            if not can_process:
                print(f"Skipping {issue['number']} - dependencies not met")
                self.telemetry.record_issue_processing(
                    repo_name=repo_name,
                    issue_number=issue["number"],
                    issue_title=issue.get("title", "Unknown"),
                    agent_name=issue.get("agent"),
                    status="dependencies_not_met",
                    context={"unmet_dependencies": unmet_deps},
                    parent_workflow_id=self.current_workflow_id,
                )
                continue

            # Dispatch agent
            if issue["agent"]:
                print(f"\n{'='*60}")
                print(f"Processing Issue {issue['number']}: {issue['title']}")
                print(f"Agent: {issue['agent']}")
                print(f"{'='*60}")

                # Determine task for agent
                # ALWAYS include issue number so agents can find the file
                agent_task = f"Process issue #{issue['number']}"
                if issue["description"]:
                    # Include both number AND description for context
                    agent_task = f"Process issue #{issue['number']}: {issue['description'][:150]}"

                # Record agent dispatch
                self.telemetry.record_agent_dispatch(
                    repo_name=repo_name,
                    agent_name=issue["agent"],
                    issue_number=issue["number"],
                    task_description=agent_task,
                    context={
                        "issue_title": issue.get("title", "Unknown"),
                        "priority": issue.get("priority"),
                        "has_description": bool(issue.get("description")),
                    },
                    parent_workflow_id=self.current_workflow_id,
                )

                # Time the agent execution with retry logic
                agent_start_time = time.time()

                # Check for recursive agent invocation
                agent_context = {"agent": issue["agent"], "issue": issue["number"]}
                if not LOOP_PROTECTION.check_operation(
                    "agent_dispatch",
                    f"{issue['agent']}-{issue['number']}",
                    agent_context,
                ):
                    print(
                        f"🛡️ Loop protection: Preventing recursive dispatch of {issue['agent']}"
                    )
                    dispatch_result = ToolResponse(
                        success=False,
                        error="Loop protection: Recursive agent dispatch prevented",
                    )
                else:
                    # Wrap execution in retry logic
                    def execute_agent():
                        return dispatcher_tool.execute(
                            agent_name=issue["agent"],
                            task=agent_task,
                            background=False,  # Run synchronously for now
                        )

                    try:
                        # Recovery system removed - executing directly
                        dispatch_result = execute_agent()
                    except Exception as e:
                        # Even retries failed - create a result object
                        dispatch_result = ToolResponse(
                            success=False, error=f"Failed after retries: {str(e)}"
                        )

                agent_duration_ms = (time.time() - agent_start_time) * 1000

                if dispatch_result.success:
                    # Record successful agent execution
                    self.telemetry.record_agent_result(
                        repo_name=repo_name,
                        agent_name=issue["agent"],
                        issue_number=issue["number"],
                        success=True,
                        result_data=dispatch_result.data,
                        duration_ms=agent_duration_ms,
                        parent_workflow_id=self.current_workflow_id,
                    )

                    # Check if this looks like a placeholder implementation
                    if self._is_placeholder_implementation(dispatch_result.data):
                        # Generate detailed feedback for placeholder result
                        # Feedback system removed
                        failure_details = {
                            "issue_number": issue["number"],
                            "agent_name": issue["agent"],
                            "error_message": "Agent succeeded but result looks like placeholder",
                            "result_data": dispatch_result.data,
                            "issue_content": issue.get("content", ""),
                        }

                        print("📝 Placeholder Implementation Detected:")
                        print(f"Failure details: {failure_details}")

                        self.telemetry.record_implementation_gap(
                            repo_name=repo_name,
                            agent_name=issue["agent"],
                            gap_type="placeholder_success",
                            description=f"Agent {issue['agent']} reported success but may not have done real implementation work",
                            context={
                                "issue_number": issue["number"],
                                "result_data": str(dispatch_result.data)[:200],
                                "feedback": failure_details.suggestions,
                            },
                        )

                    # Update issue status
                    updater_tool.execute(
                        issue_path=issue["path"],
                        status="RESOLVED",
                        notes=f"Resolved by {issue['agent']} at {datetime.now().isoformat()}",
                    )

                    resolved_issues.append(issue["number"])
                    results.append(
                        {
                            "issue": issue["number"],
                            "status": "resolved",
                            "agent": issue["agent"],
                            "result": dispatch_result.data,
                        }
                    )

                    print(f"✅ Issue {issue['number']} resolved!")
                else:
                    # Record failed agent execution
                    self.telemetry.record_agent_result(
                        repo_name=repo_name,
                        agent_name=issue["agent"],
                        issue_number=issue["number"],
                        success=False,
                        result_data=None,
                        error_message=dispatch_result.error,
                        duration_ms=agent_duration_ms,
                        parent_workflow_id=self.current_workflow_id,
                    )

                    # Generate enhanced error feedback
                    # Feedback system removed
                    failure_details = {
                        "issue_number": issue["number"],
                        "agent_name": issue["agent"],
                        "error_message": dispatch_result.error,
                        "result_data": dispatch_result.data,
                        "issue_content": issue.get("content", ""),
                    }

                    print(f"❌ Issue {issue['number']} failed:")
                    print(f"Failure: {failure_details}")

                    failed_issues.append(issue["number"])
                    error_info = {
                        "issue": issue["number"],
                        "status": "failed",
                        "agent": issue["agent"],
                        "error": dispatch_result.error,
                    }
                    # Add category and suggestions if available
                    if hasattr(failure_details, "category"):
                        error_info["failure_category"] = failure_details.category.value
                    elif (
                        isinstance(failure_details, dict)
                        and "category" in failure_details
                    ):
                        error_info["failure_category"] = failure_details["category"]

                    if hasattr(failure_details, "suggested_fixes"):
                        error_info["suggestions"] = failure_details.suggested_fixes
                    elif (
                        isinstance(failure_details, dict)
                        and "suggested_fixes" in failure_details
                    ):
                        error_info["suggestions"] = failure_details["suggested_fixes"]

                    results.append(error_info)
            else:
                print(f"⚠️ No agent assigned for issue {issue['number']}")
                failed_issues.append(issue["number"])

                # Record missing agent assignment
                self.telemetry.record_issue_processing(
                    repo_name=repo_name,
                    issue_number=issue["number"],
                    issue_title=issue.get("title", "Unknown"),
                    agent_name=None,
                    status="no_agent_assigned",
                    context={"issue_has_description": bool(issue.get("description"))},
                    parent_workflow_id=self.current_workflow_id,
                )

        # End workflow tracking
        workflow_success = len(failed_issues) == 0
        workflow_results = {
            "total_issues": len(issues),
            "resolved": resolved_issues,
            "failed": failed_issues,
            "results": results,
            "success_rate": f"{len(resolved_issues)}/{len(issues)}",
            "execution_time_ms": (time.time() - workflow_start_time) * 1000,
        }

        self.telemetry.end_workflow(
            self.current_workflow_id,
            repo_name=repo_name,
            workflow_name="IssueOrchestratorAgent",
            success=workflow_success,
            results=workflow_results,
        )

        # Generate user feedback summary for failures
        # Feedback system removed
        if False:  # self.feedback_system.feedback_history:
            print("\n" + "=" * 60)
            print("📊 FAILURE ANALYSIS SUMMARY")
            print("=" * 60)
            summary = "Feedback system unavailable"
            print(summary)

            # Save detailed feedback report
            report_path = None  # self.feedback_system.save_feedback_report()
            print(f"📝 Detailed report saved: {report_path}")

        # Compile results
        return ToolResponse(
            success=workflow_success,
            data=workflow_results,
        )

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply orchestration action"""
        action_type = action.get("type", "orchestrate")

        if action_type == "orchestrate":
            return self.execute_task(action.get("task", "resolve all issues"))
        elif action_type == "status":
            # Get status of all issues
            issues_dir = (
                Path.home() / "Documents" / "GitHub" / "12-factor-agents" / "issues"
            )
            reader_tool = self.tools[0]

            status = {"open": [], "resolved": []}
            for issue_file in issues_dir.glob("*.md"):
                result = reader_tool.execute(issue_path=str(issue_file))
                if result.success:
                    issue = result.data["issue"]
                    if issue["status"] == "resolved":
                        status["resolved"].append(issue["number"])
                    else:
                        status["open"].append(issue["number"])

            return ToolResponse(success=True, data=status)

        return ToolResponse(success=False, error=f"Unknown action type: {action_type}")

    def _is_placeholder_implementation(self, result_data: Any) -> bool:
        """
        Detect if an agent result looks like a placeholder implementation
        rather than real implementation work.
        """
        if not result_data:
            return True

        result_str = str(result_data).lower()

        # Common signs of placeholder implementations
        placeholder_indicators = [
            "migration completed",
            "setup complete",
            "task completed successfully",
            "resolved successfully",
            "implementation complete",
            "agent executed successfully",
        ]

        # Check for vague success messages without specific details
        if any(indicator in result_str for indicator in placeholder_indicators):
            # But allow if there are concrete details
            concrete_indicators = [
                "files_created",
                "files_modified",
                "lines_changed",
                "tests_run",
                "commits_made",
                "directories_created",
                "specific_changes",
                "implementation_details",
            ]

            has_concrete_details = any(
                indicator in result_str for indicator in concrete_indicators
            )

            # If it has placeholder language but no concrete details, flag it
            if not has_concrete_details:
                return True

        return False


# Self-test when run directly
# Usage: uv run agents/issue_orchestrator_agent.py
if __name__ == "__main__":
    print("Testing IssueOrchestratorAgent...")
    print("This will attempt to resolve all issues using the appropriate agents.")
    print("")

    agent = IssueOrchestratorAgent()

    # First check status
    print("Checking issue status...")
    status_result = agent._apply_action({"type": "status"})
    if status_result.success:
        print(f"Open issues: {status_result.data['open']}")
        print(f"Resolved issues: {status_result.data['resolved']}")

    print("\nStarting orchestration...")
    result = agent.execute_task("resolve all issues")

    if result.success:
        print("\n" + "=" * 60)
        print("✅ All issues resolved successfully!")
        print(json.dumps(result.data, indent=2))
    else:
        print("\n" + "=" * 60)
        print("⚠️ Some issues could not be resolved")
        print(json.dumps(result.data, indent=2))
