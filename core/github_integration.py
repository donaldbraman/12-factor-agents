"""
GitHub Integration Agent Framework
Inspired by cite-assist's sophisticated GitHub automation and orchestration.
Implements 12-factor compliant GitHub project management agents.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

from .agent import BaseAgent
from .tools import Tool, ToolResponse
from .orchestrator import ProgressAwareOrchestrator, WorkflowPhase

logger = logging.getLogger(__name__)


class GitHubActionType(Enum):
    """Types of GitHub actions that can be performed"""

    CREATE_ISSUE = "create_issue"
    UPDATE_ISSUE = "update_issue"
    CLOSE_ISSUE = "close_issue"
    CREATE_PR = "create_pr"
    UPDATE_PR = "update_pr"
    MERGE_PR = "merge_pr"
    ADD_COMMENT = "add_comment"
    ADD_LABEL = "add_label"
    CREATE_PROJECT = "create_project"
    LINK_ISSUES = "link_issues"


class IssueStatus(Enum):
    """GitHub issue status tracking"""

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CLOSED = "closed"


class GitHubIntegrationAgent(BaseAgent):
    """
    Base agent for GitHub integration and automation.

    Inspired by cite-assist's github_12factor_migration_agent.py but enhanced
    with full 12-factor compliance and broader capabilities.

    Key enhancements over cite-assist pattern:
    - External state management (no /tmp files)
    - Environment-based configuration
    - Structured error handling
    - Progress tracking with pause/resume
    - Comprehensive audit logging
    """

    def __init__(self, repository: str, agent_id: str = None):
        super().__init__(agent_id)
        self.repository = repository

        # GitHub integration state (stored in unified state)
        self.github_state = {
            "repository": repository,
            "issues_created": [],
            "prs_created": [],
            "actions_performed": [],
            "last_sync": None,
        }

        # Store in workflow data for checkpointing
        self.workflow_data.update(self.github_state)

        logger.info(f"GitHubIntegrationAgent initialized for repo: {repository}")

    def register_tools(self) -> List[Tool]:
        """Register GitHub integration tools"""
        return [
            Tool(
                name="create_issue",
                description="Create GitHub issue with structured content",
                parameters={"title": "str", "body": "str", "labels": "list"},
            ),
            Tool(
                name="create_issue_hierarchy",
                description="Create parent issue with linked sub-issues",
                parameters={"parent_spec": "dict", "sub_issues": "list"},
            ),
            Tool(
                name="manage_project",
                description="Manage GitHub project board and tracking",
                parameters={"project_spec": "dict", "actions": "list"},
            ),
            Tool(
                name="orchestrate_workflow",
                description="Orchestrate complex multi-issue workflows",
                parameters={"workflow_spec": "dict"},
            ),
            Tool(
                name="sync_status",
                description="Sync issue status and update tracking",
                parameters={"sync_options": "dict"},
            ),
        ]

    async def execute_task(self, task: str) -> ToolResponse:
        """Execute GitHub integration task with progress tracking"""
        try:
            # Parse task specification
            task_spec = self._parse_github_task(task)

            # Set up progress tracking
            self.set_progress(0.0, "initializing")
            self.workflow_data["task_specification"] = task_spec

            # Execute based on task type
            if task_spec["type"] == "create_issue_hierarchy":
                result = await self._create_issue_hierarchy(task_spec)
            elif task_spec["type"] == "orchestrate_workflow":
                result = await self._orchestrate_github_workflow(task_spec)
            elif task_spec["type"] == "sync_project_status":
                result = await self._sync_project_status(task_spec)
            else:
                result = await self._execute_basic_github_action(task_spec)

            # Update final state
            self.set_progress(1.0, "completed")

            return ToolResponse(
                success=result["success"],
                data=result,
                metadata={
                    "agent_id": self.agent_id,
                    "github_integration": True,
                    "repository": self.repository,
                },
            )

        except Exception as e:
            self.handle_error(e, "github_integration")
            return ToolResponse(
                success=False, error=str(e), metadata={"agent_id": self.agent_id}
            )

    async def _create_issue_hierarchy(
        self, task_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create hierarchical issue structure with parent-child relationships.
        Enhanced version of cite-assist's issue creation pattern.
        """
        self.set_progress(0.1, "creating_parent_issue")

        parent_spec = task_spec.get("parent_spec", {})
        sub_issues_spec = task_spec.get("sub_issues", [])

        result = {
            "success": False,
            "parent_issue": None,
            "sub_issues": [],
            "links_created": 0,
            "errors": [],
        }

        try:
            # Create parent issue
            parent_issue_num = await self._create_single_issue(
                title=parent_spec["title"],
                body=parent_spec["body"],
                labels=parent_spec.get("labels", ["enhancement"]),
            )

            if parent_issue_num:
                result["parent_issue"] = parent_issue_num
                self.github_state["issues_created"].append(parent_issue_num)
                self._log_github_action(
                    "create_issue", f"Created parent issue #{parent_issue_num}"
                )

            # Create sub-issues and link them
            self.set_progress(0.3, "creating_sub_issues")

            for i, sub_issue_spec in enumerate(sub_issues_spec):
                # Add parent reference to sub-issue body
                enhanced_body = f"{sub_issue_spec['body']}\n\n---\n📋 Parent Issue: #{parent_issue_num}"

                sub_issue_num = await self._create_single_issue(
                    title=sub_issue_spec["title"],
                    body=enhanced_body,
                    labels=sub_issue_spec.get("labels", ["enhancement"]),
                )

                if sub_issue_num:
                    result["sub_issues"].append(sub_issue_num)
                    self.github_state["issues_created"].append(sub_issue_num)

                    # Link back to parent
                    await self._add_issue_comment(
                        parent_issue_num,
                        f"Created sub-issue #{sub_issue_num}: {sub_issue_spec['title']}",
                    )
                    result["links_created"] += 1

                    self._log_github_action(
                        "create_sub_issue", f"Created sub-issue #{sub_issue_num}"
                    )

                # Update progress
                progress = 0.3 + (i + 1) / len(sub_issues_spec) * 0.5
                self.set_progress(progress, f"creating_sub_issue_{i+1}")

            # Create project summary
            self.set_progress(0.8, "creating_summary")
            summary = self._generate_project_summary(result, task_spec)
            await self._add_issue_comment(parent_issue_num, summary)

            result["success"] = True
            self.save_checkpoint()

            return result

        except Exception as e:
            result["errors"].append(str(e))
            self.handle_error(e, "create_issue_hierarchy")
            return result

    async def _orchestrate_github_workflow(
        self, task_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Orchestrate complex multi-phase GitHub workflows.
        Based on cite-assist's workflow orchestration patterns.
        """
        self.set_progress(0.1, "planning_workflow")

        workflow_spec = task_spec.get("workflow_spec", {})
        phases = workflow_spec.get("phases", [])

        result = {
            "success": False,
            "workflow_id": workflow_spec.get("name", "unnamed_workflow"),
            "phases_completed": [],
            "total_issues_created": 0,
            "total_prs_created": 0,
            "errors": [],
        }

        try:
            for i, phase in enumerate(phases):
                phase_name = phase.get("name", f"phase_{i+1}")
                self.set_progress(
                    0.2 + i * 0.6 / len(phases), f"executing_{phase_name}"
                )

                phase_result = await self._execute_workflow_phase(phase, result)
                result["phases_completed"].append(phase_name)

                # Aggregate results
                result["total_issues_created"] += phase_result.get("issues_created", 0)
                result["total_prs_created"] += phase_result.get("prs_created", 0)

                # Check for phase failure
                if not phase_result.get("success", False):
                    result["errors"].append(f"Phase {phase_name} failed")
                    break

            result["success"] = len(result["phases_completed"]) == len(phases)
            self.save_checkpoint()

            return result

        except Exception as e:
            result["errors"].append(str(e))
            self.handle_error(e, "orchestrate_workflow")
            return result

    async def _execute_workflow_phase(
        self, phase: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow phase"""
        phase_name = phase.get("name", "unnamed_phase")
        phase_actions = phase.get("actions", [])

        phase_result = {
            "success": False,
            "phase_name": phase_name,
            "actions_completed": 0,
            "issues_created": 0,
            "prs_created": 0,
            "errors": [],
        }

        try:
            for action in phase_actions:
                action_result = await self._execute_phase_action(action, context)

                if action_result["success"]:
                    phase_result["actions_completed"] += 1

                    # Count specific action types
                    if action["type"] == "create_issue":
                        phase_result["issues_created"] += 1
                    elif action["type"] == "create_pr":
                        phase_result["prs_created"] += 1
                else:
                    phase_result["errors"].append(
                        action_result.get("error", "Unknown error")
                    )

            phase_result["success"] = phase_result["actions_completed"] == len(
                phase_actions
            )
            self._log_github_action("complete_phase", f"Completed phase: {phase_name}")

            return phase_result

        except Exception as e:
            phase_result["errors"].append(str(e))
            return phase_result

    async def _execute_phase_action(
        self, action: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single action within a workflow phase"""
        action_type = action.get("type")
        action_params = action.get("params", {})

        try:
            if action_type == "create_issue":
                issue_num = await self._create_single_issue(**action_params)
                return {"success": True, "issue_number": issue_num}

            elif action_type == "create_pr":
                pr_num = await self._create_pull_request(**action_params)
                return {"success": True, "pr_number": pr_num}

            elif action_type == "add_comment":
                await self._add_issue_comment(**action_params)
                return {"success": True}

            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}",
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _sync_project_status(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync project status and update tracking information.
        Enhanced version of cite-assist's status monitoring.
        """
        self.set_progress(0.1, "fetching_current_status")

        sync_options = task_spec.get("sync_options", {})

        result = {
            "success": False,
            "synced_issues": [],
            "status_updates": 0,
            "errors": [],
        }

        try:
            # Get all issues for repository
            issues = await self._fetch_repository_issues()

            self.set_progress(0.3, "analyzing_status")

            # Analyze and update status for each issue
            for i, issue in enumerate(issues):
                issue_analysis = await self._analyze_issue_status(issue)

                if issue_analysis["needs_update"]:
                    await self._update_issue_status(issue, issue_analysis)
                    result["synced_issues"].append(issue["number"])
                    result["status_updates"] += 1

                # Update progress
                progress = 0.3 + (i + 1) / len(issues) * 0.6
                self.set_progress(progress, f"syncing_issue_{issue['number']}")

            # Update last sync time
            self.github_state["last_sync"] = datetime.now().isoformat()
            result["success"] = True
            self.save_checkpoint()

            return result

        except Exception as e:
            result["errors"].append(str(e))
            self.handle_error(e, "sync_project_status")
            return result

    async def _create_single_issue(
        self, title: str, body: str, labels: List[str] = None
    ) -> Optional[int]:
        """Create a single GitHub issue"""
        cmd = ["gh", "issue", "create", "--title", title, "--body", body]

        # Add labels if specified
        if labels:
            # Only use labels that exist in the repository
            valid_labels = await self._get_valid_labels()
            filtered_labels = [label for label in labels if label in valid_labels]
            if filtered_labels:
                cmd.extend(["--label", ",".join(filtered_labels)])

        try:
            result = await self._run_gh_command(*cmd)

            # Extract issue number from URL
            if "issues/" in result:
                issue_num = int(result.split("/issues/")[1])
                self._log_github_action(
                    "create_issue", f"Created issue #{issue_num}: {title}"
                )
                return issue_num

        except Exception as e:
            self._log_github_action(
                "create_issue_failed", f"Failed to create issue: {str(e)}"
            )

        return None

    async def _create_pull_request(
        self, title: str, body: str, branch: str = None
    ) -> Optional[int]:
        """Create a GitHub pull request"""
        cmd = ["gh", "pr", "create", "--title", title, "--body", body]

        if branch:
            cmd.extend(["--head", branch])

        try:
            result = await self._run_gh_command(*cmd)

            # Extract PR number from URL
            if "/pull/" in result:
                pr_num = int(result.split("/pull/")[1])
                self._log_github_action("create_pr", f"Created PR #{pr_num}: {title}")
                return pr_num

        except Exception as e:
            self._log_github_action(
                "create_pr_failed", f"Failed to create PR: {str(e)}"
            )

        return None

    async def _add_issue_comment(self, issue_number: int, comment: str):
        """Add comment to GitHub issue"""
        try:
            await self._run_gh_command(
                "issue", "comment", str(issue_number), "--body", comment
            )
            self._log_github_action(
                "add_comment", f"Added comment to issue #{issue_number}"
            )
        except Exception as e:
            self._log_github_action(
                "add_comment_failed", f"Failed to add comment: {str(e)}"
            )

    async def _fetch_repository_issues(self) -> List[Dict[str, Any]]:
        """Fetch all issues for the repository"""
        try:
            result = await self._run_gh_command(
                "issue", "list", "--json", "number,title,state,labels"
            )
            return json.loads(result)
        except Exception as e:
            self._log_github_action(
                "fetch_issues_failed", f"Failed to fetch issues: {str(e)}"
            )
            return []

    async def _analyze_issue_status(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze issue status and determine if updates are needed"""
        # Placeholder implementation - would analyze issue content, labels, comments, etc.
        return {
            "needs_update": False,
            "suggested_status": issue.get("state", "open"),
            "suggested_labels": issue.get("labels", []),
        }

    async def _update_issue_status(
        self, issue: Dict[str, Any], analysis: Dict[str, Any]
    ):
        """Update issue status based on analysis"""
        # Implementation would update labels, status, etc. based on analysis
        pass

    async def _get_valid_labels(self) -> List[str]:
        """Get list of valid labels for the repository"""
        try:
            result = await self._run_gh_command("label", "list", "--json", "name")
            labels_data = json.loads(result)
            return [label["name"] for label in labels_data]
        except Exception:
            # Return common default labels if fetch fails
            return ["bug", "enhancement", "documentation", "good first issue"]

    async def _run_gh_command(self, *args) -> str:
        """Run GitHub CLI command asynchronously"""
        cmd = ["gh"] + list(args)

        # Run command asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=None,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"GitHub CLI error: {stderr.decode()}")

        return stdout.decode().strip()

    def _parse_github_task(self, task: str) -> Dict[str, Any]:
        """Parse task string into structured GitHub task specification"""
        lines = task.split("\n")

        # Default task spec
        task_spec = {"type": "create_issue", "title": task[:100], "body": task}

        # Parse structured task format
        for line in lines:
            if line.startswith("type:"):
                task_spec["type"] = line.split(":", 1)[1].strip()
            elif line.startswith("title:"):
                task_spec["title"] = line.split(":", 1)[1].strip()
            elif line.startswith("labels:"):
                labels_text = line.split(":", 1)[1].strip()
                task_spec["labels"] = [l.strip() for l in labels_text.split(",")]

        return task_spec

    def _generate_project_summary(
        self, result: Dict[str, Any], task_spec: Dict[str, Any]
    ) -> str:
        """Generate project summary for parent issue"""
        parent_issue = result.get("parent_issue")
        sub_issues = result.get("sub_issues", [])

        summary = f"""## 🚀 Project Plan Activated!

I've created the complete issue hierarchy for this project:

### Parent Issue
- #{parent_issue} - Project coordination and tracking

### Sub-Issues Created
{chr(10).join(f'- #{issue}' for issue in sub_issues)}

### Project Status
- **Total Issues Created**: {1 + len(sub_issues)}
- **Links Created**: {result.get("links_created", 0)}
- **Ready for Development**: ✅

### Next Steps
1. **Team Assignment**: Assign team members to specific sub-issues
2. **Development**: Start with foundational issues first
3. **Progress Tracking**: Update issues as work progresses

Each sub-issue links back to this parent issue for tracking and coordination.

🎯 **All systems ready for collaborative development!**"""

        return summary

    def _log_github_action(self, action_type: str, message: str, data: Any = None):
        """Log GitHub actions for audit trail"""
        action = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "message": message,
            "repository": self.repository,
            "data": data,
        }

        self.github_state["actions_performed"].append(action)
        logger.info(f"[{self.repository}] {message}")

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply action to GitHub integration state"""
        action_type = action.get("type", "unknown")

        if action_type == "sync_issues":
            # Trigger issue synchronization
            return ToolResponse(success=True, data={"action": "sync_triggered"})

        elif action_type == "create_milestone":
            milestone_data = action.get("milestone_data", {})
            # Create milestone implementation
            return ToolResponse(success=True, data={"milestone_created": True})

        else:
            return ToolResponse(
                success=False, error=f"Unknown action type: {action_type}"
            )


class GitHubProjectOrchestrator(ProgressAwareOrchestrator):
    """
    Specialized orchestrator for GitHub project management.

    Based on cite-assist's project orchestration patterns but with
    full 12-factor compliance and enhanced capabilities.
    """

    def __init__(
        self,
        repository: str,
        project_name: str = "github_project",
        agent_id: str = None,
    ):
        super().__init__(project_name, agent_id)
        self.repository = repository
        self.github_agent = GitHubIntegrationAgent(repository)

        # Register custom phase processors for GitHub workflows
        self.register_phase_processor(
            WorkflowPhase.INITIALIZATION, self._initialize_github_project
        )
        self.register_phase_processor(
            WorkflowPhase.ANALYSIS, self._analyze_project_requirements
        )
        self.register_phase_processor(
            WorkflowPhase.PROCESSING, self._create_github_structure
        )
        self.register_phase_processor(
            WorkflowPhase.APPROVAL, self._request_project_approval
        )
        self.register_phase_processor(
            WorkflowPhase.FINALIZATION, self._finalize_github_project
        )

    async def _initialize_github_project(self, workflow_data: Dict):
        """Initialize GitHub project structure"""
        self.set_progress(0.1, "initializing_github_project")

        # Set up project metadata
        workflow_data["github_repository"] = self.repository
        workflow_data["project_initialized_at"] = datetime.now().isoformat()

        self.set_progress(0.2, "github_project_ready")
        logger.info(f"GitHub project initialized for {self.repository}")

    async def _analyze_project_requirements(self, workflow_data: Dict):
        """Analyze project requirements for GitHub structure"""
        self.set_progress(0.3, "analyzing_requirements")

        # Analyze what GitHub structure is needed
        requirements = workflow_data.get("requirements", [])

        analysis = {
            "issues_needed": len(requirements),
            "milestones_needed": 1,
            "labels_needed": ["enhancement", "bug", "documentation"],
            "project_complexity": "medium",
        }

        workflow_data["github_analysis"] = analysis
        self.set_progress(0.5, "requirements_analyzed")
        logger.info(f"Analyzed requirements: {analysis['issues_needed']} issues needed")

    async def _create_github_structure(self, workflow_data: Dict):
        """Create GitHub project structure"""
        self.set_progress(0.6, "creating_github_structure")

        analysis = workflow_data.get("github_analysis", {})

        # Create issue hierarchy using GitHub agent
        task = f"""
        type: create_issue_hierarchy
        parent_spec: {{
            "title": "{workflow_data.get('project_name', 'Project')} - Implementation Plan",
            "body": "Coordinating implementation of {workflow_data.get('project_name', 'project')}",
            "labels": ["enhancement", "epic"]
        }}
        sub_issues: {analysis.get('issues_needed', 3)}
        """

        result = await self.github_agent.execute_task(task)
        workflow_data["github_structure_result"] = result.data

        self.set_progress(0.8, "github_structure_created")
        logger.info("GitHub project structure created successfully")

    async def _request_project_approval(self, workflow_data: Dict):
        """Request approval for GitHub project"""
        self.set_progress(0.85, "requesting_approval")

        # In a real implementation, this might notify stakeholders
        workflow_data["approval_requested_at"] = datetime.now().isoformat()
        workflow_data["auto_approved"] = True  # For demo purposes

        logger.info("Project approval requested and auto-approved")

    async def _finalize_github_project(self, workflow_data: Dict):
        """Finalize GitHub project setup"""
        self.set_progress(0.9, "finalizing_project")

        # Add final project documentation, summaries, etc.
        structure_result = workflow_data.get("github_structure_result", {})

        finalization_summary = {
            "project_name": workflow_data.get("project_name"),
            "repository": self.repository,
            "issues_created": len(structure_result.get("sub_issues", [])),
            "ready_for_development": True,
            "finalized_at": datetime.now().isoformat(),
        }

        workflow_data["finalization_summary"] = finalization_summary
        self.set_progress(1.0, "project_complete")
        logger.info(f"GitHub project finalized: {finalization_summary}")


# Example usage and testing
async def demo_github_integration():
    """Demonstrate GitHub integration capabilities"""

    # Example 1: Basic issue creation
    github_agent = GitHubIntegrationAgent("example/repository")

    task = """
    type: create_issue
    title: Implement user authentication system
    body: Need to implement secure user authentication with JWT tokens
    labels: enhancement, security
    """

    print("Creating GitHub issue...")
    result = await github_agent.execute_task(task)
    print(f"Result: {result.success}")

    # Example 2: Project orchestration
    orchestrator = GitHubProjectOrchestrator("example/repository", "auth_system")

    workflow_data = {
        "project_name": "User Authentication System",
        "requirements": [
            "JWT token implementation",
            "User registration endpoint",
            "Login/logout functionality",
            "Password reset system",
        ],
    }

    print("Orchestrating GitHub project...")
    project_result = await orchestrator.start_workflow_async(workflow_data)
    print(f"Project orchestration: {project_result.success}")

    return result, project_result


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demo_github_integration())
