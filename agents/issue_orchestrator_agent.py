"""
IssueOrchestratorAgent - Orchestrates issue resolution by dispatching appropriate agents.
Meta-agent that reads issues and coordinates other agents to solve them.
"""
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import importlib.util
import inspect

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse


class IssueReaderTool(Tool):
    """Read and parse issue files"""
    
    def __init__(self):
        super().__init__(
            name="read_issue",
            description="Read and parse an issue file"
        )
    
    def execute(self, issue_path: str) -> ToolResponse:
        """Read issue from markdown file"""
        try:
            path = Path(issue_path).resolve()
            
            if not path.exists():
                return ToolResponse(
                    success=False,
                    error=f"Issue file not found: {path}"
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
                "status": "open"
            }
            
            # Extract issue number from filename
            if path.name.startswith("00"):
                issue["number"] = path.name.split("-")[0]
            
            # Parse content
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("# Issue"):
                    issue["title"] = line.replace("# Issue", "").strip()
                elif line.startswith("## Description"):
                    # Get description from next lines
                    desc_lines = []
                    for j in range(i+1, len(lines)):
                        if lines[j].startswith("##"):
                            break
                        desc_lines.append(lines[j])
                    issue["description"] = '\n'.join(desc_lines).strip()
                elif line.startswith("## Agent Assignment"):
                    if i+1 < len(lines):
                        issue["agent"] = lines[i+1].strip().replace("`", "")
                elif line.startswith("## Priority"):
                    if i+1 < len(lines):
                        issue["priority"] = lines[i+1].strip()
                elif line.startswith("- Depends on:"):
                    dep = line.replace("- Depends on:", "").strip()
                    issue["dependencies"].append(dep)
            
            # Check if already resolved
            if "status: resolved" in content.lower():
                issue["status"] = "resolved"
            
            return ToolResponse(
                success=True,
                data={"issue": issue}
            )
            
        except Exception as e:
            return ToolResponse(
                success=False,
                error=str(e)
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "issue_path": {"type": "string"}
            },
            "required": ["issue_path"]
        }


class AgentDispatcherTool(Tool):
    """Dispatch agents to solve issues"""
    
    def __init__(self):
        super().__init__(
            name="dispatch_agent",
            description="Dispatch an agent to solve an issue"
        )
    
    def execute(self, agent_name: str, task: str, background: bool = False) -> ToolResponse:
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
                "UvMigrationAgent": "uv_migration_agent"
            }
            
            module_name = agent_map.get(agent_name, agent_name.lower().replace("agent", "_agent"))
            
            # Try to import the agent
            agent_path = Path(__file__).parent / f"{module_name}.py"
            
            if not agent_path.exists():
                return ToolResponse(
                    success=False,
                    error=f"Agent implementation not found: {agent_name}",
                    data={"agent": agent_name, "status": "not_implemented"}
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
                
                script_path = Path.home() / ".claude-shared-state" / f"run_{agent_name}.py"
                script_path.parent.mkdir(exist_ok=True)
                script_path.write_text(script)
                
                process = subprocess.Popen(
                    ["uv", "run", str(script_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate()
                
                # Load result
                result_file = Path.home() / ".claude-shared-state" / f"agent_result_{agent_name}.json"
                if result_file.exists():
                    result_data = json.loads(result_file.read_text())
                    return ToolResponse(
                        success=result_data.get("success", False),
                        data=result_data.get("data", {}),
                        error=result_data.get("error")
                    )
                else:
                    return ToolResponse(
                        success=False,
                        error=f"Agent execution failed: {stderr}"
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
            return ToolResponse(
                success=False,
                error=str(e)
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string"},
                "task": {"type": "string"},
                "background": {"type": "boolean"}
            },
            "required": ["agent_name", "task"]
        }


class IssueStatusUpdaterTool(Tool):
    """Update issue status"""
    
    def __init__(self):
        super().__init__(
            name="update_issue_status",
            description="Update the status of an issue"
        )
    
    def execute(self, issue_path: str, status: str, notes: str = None) -> ToolResponse:
        """Update issue status in file"""
        try:
            path = Path(issue_path).resolve()
            
            if not path.exists():
                return ToolResponse(
                    success=False,
                    error=f"Issue file not found: {path}"
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
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith("## Status"):
                        lines[i+1] = status
                        break
                content = '\n'.join(lines)
            
            path.write_text(content)
            
            return ToolResponse(
                success=True,
                data={
                    "issue": str(path),
                    "status": status,
                    "updated": True
                }
            )
            
        except Exception as e:
            return ToolResponse(
                success=False,
                error=str(e)
            )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "issue_path": {"type": "string"},
                "status": {"type": "string"},
                "notes": {"type": "string"}
            },
            "required": ["issue_path", "status"]
        }


class IssueOrchestratorAgent(BaseAgent):
    """
    Meta-agent that orchestrates issue resolution by dispatching appropriate agents.
    Reads issues, determines dependencies, and coordinates agent execution.
    """
    
    def register_tools(self) -> List[Tool]:
        """Register orchestration tools"""
        return [
            IssueReaderTool(),
            AgentDispatcherTool(),
            IssueStatusUpdaterTool()
        ]
    
    def execute_task(self, task: str) -> ToolResponse:
        """
        Execute orchestration task.
        Expected task: "resolve all issues" or "resolve issue #XXX"
        """
        
        base_path = Path.home() / "Documents" / "GitHub" / "12-factor-agents"
        issues_dir = base_path / "issues"
        
        results = []
        resolved_issues = []
        failed_issues = []
        
        # Determine which issues to process
        if "all issues" in task:
            issue_files = sorted(issues_dir.glob("*.md"))
        elif "#" in task:
            # Specific issue number
            issue_num = task.split("#")[-1].strip().split()[0]
            issue_files = [f for f in issues_dir.glob(f"{issue_num}*.md")]
        else:
            issue_files = sorted(issues_dir.glob("*.md"))
        
        # Read all issues first
        issues = []
        reader_tool = self.tools[0]  # IssueReaderTool
        
        for issue_file in issue_files:
            read_result = reader_tool.execute(issue_path=str(issue_file))
            if read_result.success:
                issues.append(read_result.data["issue"])
        
        # Sort by dependencies (issues with no dependencies first)
        issues.sort(key=lambda x: (len(x["dependencies"]), x["priority"] or "P99"))
        
        # Process issues
        dispatcher_tool = self.tools[1]  # AgentDispatcherTool
        updater_tool = self.tools[2]  # IssueStatusUpdaterTool
        
        for issue in issues:
            # Skip if already resolved
            if issue["status"] == "resolved":
                resolved_issues.append(issue["number"])
                continue
            
            # Check dependencies
            can_process = True
            for dep in issue["dependencies"]:
                dep_num = dep.replace("#", "").strip()
                if dep_num not in resolved_issues:
                    can_process = False
                    break
            
            if not can_process:
                print(f"Skipping {issue['number']} - dependencies not met")
                continue
            
            # Dispatch agent
            if issue["agent"]:
                print(f"\n{'='*60}")
                print(f"Processing Issue {issue['number']}: {issue['title']}")
                print(f"Agent: {issue['agent']}")
                print(f"{'='*60}")
                
                # Determine task for agent
                agent_task = f"solve issue {issue['number']}"
                if issue["description"]:
                    agent_task = issue["description"][:200]  # Use description as task
                
                dispatch_result = dispatcher_tool.execute(
                    agent_name=issue["agent"],
                    task=agent_task,
                    background=False  # Run synchronously for now
                )
                
                if dispatch_result.success:
                    # Update issue status
                    update_result = updater_tool.execute(
                        issue_path=issue["path"],
                        status="RESOLVED",
                        notes=f"Resolved by {issue['agent']} at {datetime.now().isoformat()}"
                    )
                    
                    resolved_issues.append(issue["number"])
                    results.append({
                        "issue": issue["number"],
                        "status": "resolved",
                        "agent": issue["agent"],
                        "result": dispatch_result.data
                    })
                    
                    print(f"✅ Issue {issue['number']} resolved!")
                else:
                    failed_issues.append(issue["number"])
                    results.append({
                        "issue": issue["number"],
                        "status": "failed",
                        "agent": issue["agent"],
                        "error": dispatch_result.error
                    })
                    
                    print(f"❌ Issue {issue['number']} failed: {dispatch_result.error}")
            else:
                print(f"⚠️ No agent assigned for issue {issue['number']}")
                failed_issues.append(issue["number"])
        
        # Compile results
        return ToolResponse(
            success=len(failed_issues) == 0,
            data={
                "total_issues": len(issues),
                "resolved": resolved_issues,
                "failed": failed_issues,
                "results": results,
                "success_rate": f"{len(resolved_issues)}/{len(issues)}"
            }
        )
    
    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply orchestration action"""
        action_type = action.get("type", "orchestrate")
        
        if action_type == "orchestrate":
            return self.execute_task(action.get("task", "resolve all issues"))
        elif action_type == "status":
            # Get status of all issues
            issues_dir = Path.home() / "Documents" / "GitHub" / "12-factor-agents" / "issues"
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
            
            return ToolResponse(
                success=True,
                data=status
            )
        
        return ToolResponse(
            success=False,
            error=f"Unknown action type: {action_type}"
        )


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
        print("\n" + "="*60)
        print("✅ All issues resolved successfully!")
        print(json.dumps(result.data, indent=2))
    else:
        print("\n" + "="*60)
        print(f"⚠️ Some issues could not be resolved")
        print(json.dumps(result.data, indent=2))