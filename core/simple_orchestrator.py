#!/usr/bin/env python3
"""
Simple Orchestrator - Smart context preparation and agent coordination

This is where complexity belongs: preparing complete context for stateless agent functions
and coordinating handoffs between them.

Key insight: Claude agents are stateless functions, so the orchestrator handles:
1. Context discovery and preparation
2. Agent function coordination  
3. Error recovery and retries
4. Result aggregation and handoffs
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
import json
import subprocess
from datetime import datetime


@dataclass
class TaskContext:
    """Complete context for a task - everything an agent function needs"""

    task_id: str
    task_type: str  # "fix_issue", "create_pr", "review_code", etc.

    # Repository context
    repo_path: Path
    repo_name: str
    current_branch: str

    # Issue/PR context (if applicable)
    issue_number: Optional[int] = None
    issue_data: Dict[str, Any] = field(default_factory=dict)
    pr_number: Optional[int] = None
    pr_data: Dict[str, Any] = field(default_factory=dict)

    # File context
    files_to_process: List[str] = field(default_factory=list)
    changes_to_apply: List[Dict] = field(default_factory=list)

    # Analysis context
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    test_results: Dict[str, Any] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationResult:
    """Result of orchestrated task execution"""

    success: bool
    task_id: str
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    steps_completed: List[str] = field(default_factory=list)
    context: Optional[TaskContext] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return {
            "success": self.success,
            "task_id": self.task_id,
            "results": self.results,
            "errors": self.errors,
            "steps_completed": self.steps_completed,
            "context": {
                "task_id": self.context.task_id,
                "task_type": self.context.task_type,
                "issue_number": self.context.issue_number,
                "pr_number": self.context.pr_number,
                "files_to_process": self.context.files_to_process,
                "metadata": self.context.metadata,
            }
            if self.context
            else None,
        }


class SimpleOrchestrator:
    """
    Smart orchestrator that prepares context and coordinates simple agent functions.

    This is the ONE place where we handle complexity - everything else should be
    simple, stateless functions.
    """

    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or Path.cwd()
        self.agent_functions: Dict[str, Callable] = {}
        self.task_history: List[OrchestrationResult] = []

    def register_agent_function(self, name: str, func: Callable):
        """Register a simple agent function"""
        self.agent_functions[name] = func

    def prepare_issue_context(self, issue_number: int) -> TaskContext:
        """
        Prepare complete context for issue processing.

        This is where we do the complex work of gathering ALL the context
        that agent functions will need.
        """
        print(f"🔍 Preparing context for issue #{issue_number}")

        # Create base context
        context = TaskContext(
            task_id=f"issue-{issue_number}-{int(datetime.now().timestamp())}",
            task_type="fix_issue",
            repo_path=self.repo_path,
            repo_name=self.repo_path.name,
            current_branch=self._get_current_branch(),
            issue_number=issue_number,
        )

        # Gather issue data via GitHub CLI
        try:
            issue_data = self._fetch_issue_data(issue_number)
            context.issue_data = issue_data
            print(f"  ✅ Fetched issue data: {issue_data.get('title', 'No title')[:50]}")
        except Exception as e:
            print(f"  ⚠️ Could not fetch issue data: {e}")

        # Discover relevant files
        try:
            relevant_files = self._discover_relevant_files(context.issue_data)
            context.files_to_process = relevant_files
            print(f"  ✅ Discovered {len(relevant_files)} relevant files")
        except Exception as e:
            print(f"  ⚠️ Could not discover files: {e}")

        # Analyze codebase state
        try:
            analysis = self._analyze_codebase_state(context)
            context.analysis_results = analysis
            print("  ✅ Analyzed codebase state")
        except Exception as e:
            print(f"  ⚠️ Could not analyze codebase: {e}")

        print(f"✅ Context prepared for issue #{issue_number}")
        return context

    def execute_issue_fix_workflow(self, issue_number: int) -> OrchestrationResult:
        """
        Orchestrate complete issue fix workflow using simple agent functions.

        This coordinates multiple simple functions, each with complete context.
        """
        result = OrchestrationResult(
            success=False, task_id=f"issue-{issue_number}-workflow"
        )

        try:
            # Step 1: Prepare complete context (this is the complex part)
            print(f"🚀 Starting issue fix workflow for #{issue_number}")
            context = self.prepare_issue_context(issue_number)
            result.context = context

            # Step 2: Analyze issue (simple function with complete context)
            if "analyze_issue" in self.agent_functions:
                print("🔍 Analyzing issue...")
                analysis_result = self.agent_functions["analyze_issue"](context)
                if analysis_result.get("success"):
                    context.analysis_results.update(analysis_result.get("data", {}))
                    result.steps_completed.append("analyze_issue")
                    print("  ✅ Issue analysis completed")
                else:
                    result.errors.append(
                        f"Issue analysis failed: {analysis_result.get('error')}"
                    )
                    return result

            # Step 3: Generate code changes (simple function with complete context)
            if "generate_code_changes" in self.agent_functions:
                print("💻 Generating code changes...")
                changes_result = self.agent_functions["generate_code_changes"](context)
                if changes_result.get("success"):
                    context.changes_to_apply = changes_result.get("changes", [])
                    result.steps_completed.append("generate_code_changes")
                    print(f"  ✅ Generated {len(context.changes_to_apply)} changes")
                else:
                    result.errors.append(
                        f"Code generation failed: {changes_result.get('error')}"
                    )
                    return result

            # Step 4: Validate changes (simple function with complete context)
            if "validate_changes" in self.agent_functions:
                print("🔍 Validating changes...")
                validation_result = self.agent_functions["validate_changes"](context)
                if validation_result.get("success"):
                    context.validation_results = validation_result.get("data", {})
                    result.steps_completed.append("validate_changes")
                    print("  ✅ Changes validated")
                else:
                    result.errors.append(
                        f"Validation failed: {validation_result.get('error')}"
                    )
                    return result

            # Step 5: Create PR (simple function with complete context)
            if "create_pull_request" in self.agent_functions:
                print("📝 Creating pull request...")
                pr_result = self.agent_functions["create_pull_request"](context)
                if pr_result.get("success"):
                    result.results["pr_number"] = pr_result.get("pr_number")
                    result.results["pr_url"] = pr_result.get("pr_url")
                    result.steps_completed.append("create_pull_request")
                    print(f"  ✅ Created PR: {pr_result.get('pr_url')}")
                else:
                    result.errors.append(
                        f"PR creation failed: {pr_result.get('error')}"
                    )
                    return result

            # Success!
            result.success = True
            result.results["issue_number"] = issue_number
            result.results["context_id"] = context.task_id

            print("🎉 Issue fix workflow completed successfully!")

        except Exception as e:
            result.errors.append(f"Workflow failed: {e}")
            print(f"❌ Workflow failed: {e}")

        # Record result
        self.task_history.append(result)
        return result

    def handoff_context(
        self, from_context: TaskContext, to_task_type: str, additional_data: Dict = None
    ) -> TaskContext:
        """
        Create new context for handoff between agent functions.

        This is how we pass context between different types of operations.
        """
        new_context = TaskContext(
            task_id=f"{to_task_type}-{int(datetime.now().timestamp())}",
            task_type=to_task_type,
            repo_path=from_context.repo_path,
            repo_name=from_context.repo_name,
            current_branch=from_context.current_branch,
            issue_number=from_context.issue_number,
            issue_data=from_context.issue_data.copy(),
            pr_number=from_context.pr_number,
            pr_data=from_context.pr_data.copy(),
            files_to_process=from_context.files_to_process.copy(),
            changes_to_apply=from_context.changes_to_apply.copy(),
            analysis_results=from_context.analysis_results.copy(),
            test_results=from_context.test_results.copy(),
            validation_results=from_context.validation_results.copy(),
            metadata=from_context.metadata.copy(),
        )

        # Add any additional data
        if additional_data:
            new_context.metadata.update(additional_data)

        return new_context

    def _get_current_branch(self) -> str:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return "main"

    def _fetch_issue_data(self, issue_number: int) -> Dict[str, Any]:
        """Fetch issue data via GitHub CLI"""
        try:
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "view",
                    str(issue_number),
                    "--json",
                    "title,body,labels,state",
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)
        except Exception:
            # Fallback to basic data
            return {
                "title": f"Issue #{issue_number}",
                "body": "Could not fetch issue details",
                "labels": [],
                "state": "open",
            }

    def _discover_relevant_files(self, issue_data: Dict) -> List[str]:
        """
        Discover files relevant to the issue.

        This is where we can add sophisticated file discovery logic.
        """
        # Simple implementation - could be made much smarter
        relevant_files = []

        # Look for files mentioned in issue body
        issue_text = f"{issue_data.get('title', '')} {issue_data.get('body', '')}"

        # Find Python files in repo
        python_files = list(self.repo_path.glob("**/*.py"))

        # Simple heuristic: include files mentioned or in common directories
        for py_file in python_files:
            if (
                py_file.name in issue_text
                or "agents" in str(py_file)
                or "core" in str(py_file)
            ):
                relevant_files.append(str(py_file.relative_to(self.repo_path)))

        return relevant_files[:10]  # Limit to avoid overwhelming context

    def _analyze_codebase_state(self, context: TaskContext) -> Dict[str, Any]:
        """Analyze current codebase state for context"""
        analysis = {
            "repo_health": "unknown",
            "test_status": "unknown",
            "file_count": len(context.files_to_process),
            "branch_status": "unknown",
        }

        try:
            # Check git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=context.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            analysis["branch_status"] = (
                "clean" if not result.stdout.strip() else "dirty"
            )

        except Exception:
            pass

        return analysis


# Example usage and demo
if __name__ == "__main__":
    # Demo the orchestrator
    orchestrator = SimpleOrchestrator()

    # Example of registering simple agent functions
    def dummy_analyze_issue(context: TaskContext) -> Dict[str, Any]:
        """Example simple agent function"""
        return {
            "success": True,
            "data": {"analysis": "Issue analyzed successfully", "complexity": "medium"},
        }

    orchestrator.register_agent_function("analyze_issue", dummy_analyze_issue)

    print("🧪 Simple Orchestrator ready!")
    print("✅ This is where complexity belongs - smart context preparation")
    print("✅ Agent functions stay simple and stateless")
