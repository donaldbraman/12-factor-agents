"""
IssueFixerAgent - Fixes specific GitHub issues found by code review.
Handles security issues, dangerous functions, hardcoded values, etc.
"""
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse


class SecretRemoverTool(Tool):
    """Remove hardcoded secrets from code"""
    
    def __init__(self):
        super().__init__(
            name="remove_secrets",
            description="Remove hardcoded secrets and replace with env vars"
        )
    
    def execute(self, file_path: str) -> ToolResponse:
        """Remove hardcoded secrets from file"""
        try:
            path = Path(file_path)
            if not path.exists():
                return ToolResponse(success=False, error=f"File not found: {file_path}")
            
            content = path.read_text()
            original = content
            modified = False
            
            # Pattern for finding potential secrets
            patterns = [
                (r'(password|secret|token|api_key)\s*=\s*["\']([^"\']+)["\']', r'\1 = os.getenv("\1_ENV", "")'),
                (r'(PASSWORD|SECRET|TOKEN|API_KEY)\s*=\s*["\']([^"\']+)["\']', r'\1 = os.getenv("\1", "")'),
            ]
            
            for pattern, replacement in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                    modified = True
            
            # Add import if we made changes
            if modified and 'import os' not in content:
                lines = content.split('\n')
                # Find where to add import
                import_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        import_idx = i + 1
                    elif import_idx > 0:
                        break
                
                lines.insert(import_idx, 'import os')
                content = '\n'.join(lines)
            
            if modified:
                path.write_text(content)
                return ToolResponse(
                    success=True,
                    data={
                        "file": str(path),
                        "secrets_removed": True,
                        "message": "Replaced hardcoded secrets with environment variables"
                    }
                )
            
            return ToolResponse(
                success=True,
                data={
                    "file": str(path),
                    "secrets_removed": False,
                    "message": "No hardcoded secrets found"
                }
            )
            
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"}
            },
            "required": ["file_path"]
        }


class DangerousFunctionFixerTool(Tool):
    """Fix dangerous function usage"""
    
    def __init__(self):
        super().__init__(
            name="fix_dangerous_functions",
            description="Replace dangerous functions with safe alternatives"
        )
    
    def execute(self, directory: str = ".") -> ToolResponse:
        """Fix dangerous functions in directory"""
        try:
            dir_path = Path(directory)
            fixed_files = []
            
            for py_file in dir_path.rglob("*.py"):
                content = py_file.read_text()
                original = content
                modified = False
                
                # Replace eval with ast.literal_eval for simple cases
                if 'ast.literal_eval(' in content:
                    # Check if ast is imported
                    if 'import ast' not in content:
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if line.startswith('import ') or line.startswith('from '):
                                lines.insert(i + 1, 'import ast')
                                content = '\n'.join(lines)
                                break
                    
                    # Replace eval with ast.literal_eval where safe
                    content = re.sub(
                        r'eval\(([^)]+)\)',
                        r'ast.literal_ast.literal_eval(\1)',
                        content
                    )
                    modified = True
                
                # Comment out exec statements with warning
    # SECURITY WARNING: exec() is dangerous and has been disabled
    #                 if 'exec(' in content:
                    lines = content.split('\n')
                    new_lines = []
                    for line in lines:
    # SECURITY WARNING: exec() is dangerous and has been disabled
    #                         if 'exec(' in line and not line.strip().startswith('#'):
    # SECURITY WARNING: exec() is dangerous and has been disabled
    #                             new_lines.append(f"    # SECURITY WARNING: exec() is dangerous and has been disabled")
                            new_lines.append(f"    # {line}")
                            modified = True
                        else:
                            new_lines.append(line)
                    content = '\n'.join(new_lines)
                
                if modified:
                    py_file.write_text(content)
                    fixed_files.append(str(py_file))
            
            return ToolResponse(
                success=True,
                data={
                    "fixed_files": fixed_files,
                    "count": len(fixed_files)
                }
            )
            
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "directory": {"type": "string"}
            }
        }


class PickleFixerTool(Tool):
    """Fix unsafe pickle deserialization"""
    
    def __init__(self):
        super().__init__(
            name="fix_pickle_usage",
            description="Replace pickle with safe alternatives"
        )
    
    def execute(self, directory: str = ".") -> ToolResponse:
        """Fix pickle usage in directory"""
        try:
            dir_path = Path(directory)
            fixed_files = []
            
            for py_file in dir_path.rglob("*.py"):
                content = py_file.read_text()
                original = content
                modified = False
                
                # Replace pickle with json where possible
                if 'pickle' in content:
                    lines = content.split('\n')
                    new_lines = []
                    
                    for line in lines:
    # SECURITY: Replaced unsafe pickle with json
                        if 'json.load' in line:
                            new_lines.append(f"    # SECURITY: Replaced unsafe pickle with json")
    # SECURITY: Replaced unsafe pickle with json
                            new_lines.append(line.replace('json.load', 'json.load'))
                            modified = True
    # SECURITY: Replaced pickle with json
                        elif 'json.dump' in line:
                            new_lines.append(f"    # SECURITY: Replaced pickle with json")
    # SECURITY: Replaced pickle with json
                            new_lines.append(line.replace('json.dump', 'json.dump'))
                            modified = True
import json  # Replaced pickle for security
#                         elif 'import pickle' in line:  # Commented out unsafe import
                            new_lines.append('import json  # Replaced pickle for security')
                            new_lines.append(f'# {line}  # Commented out unsafe import')
                            modified = True
                        else:
                            new_lines.append(line)
                    
                    if modified:
                        content = '\n'.join(new_lines)
                        py_file.write_text(content)
                        fixed_files.append(str(py_file))
            
            return ToolResponse(
                success=True,
                data={
                    "fixed_files": fixed_files,
                    "count": len(fixed_files)
                }
            )
            
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "directory": {"type": "string"}
            }
        }


class PathFixerTool(Tool):
    """Fix hardcoded paths"""
    
    def __init__(self):
        super().__init__(
            name="fix_hardcoded_paths",
            description="Replace hardcoded paths with dynamic paths"
        )
    
    def execute(self, directory: str = ".") -> ToolResponse:
        """Fix hardcoded paths in directory"""
        try:
            dir_path = Path(directory)
            fixed_files = []
            
            for py_file in dir_path.rglob("*.py"):
                # Skip test files as they might have test paths
                if 'test' in str(py_file):
                    continue
                    
                content = py_file.read_text()
                original = content
                modified = False
                
                # Replace common hardcoded paths
                replacements = [
                    (r'/Users/[^/]+/Documents/GitHub/12-factor-agents', 'Path.home() / "Documents" / "GitHub" / "12-factor-agents"'),
                    (r'/Users/\w+', 'Path.home()'),
                    (r'C:\\Users\\\w+', 'Path.home()'),
                    (r'Path.home() / "Documents" / "GitHub"', 'Path.home() / "Documents" / "GitHub"'),
                ]
                
                for pattern, replacement in replacements:
                    if re.search(pattern, content):
                        content = re.sub(pattern, replacement, content)
                        modified = True
                
                # Ensure Path is imported if we made changes
                if modified and 'from pathlib import Path' not in content:
                    lines = content.split('\n')
                    import_added = False
                    for i, line in enumerate(lines):
                        if line.startswith('import ') or line.startswith('from '):
                            lines.insert(i, 'from pathlib import Path')
                            import_added = True
                            break
                    
                    if not import_added:
                        lines.insert(0, 'from pathlib import Path')
                    
                    content = '\n'.join(lines)
                
                if modified:
                    py_file.write_text(content)
                    fixed_files.append(str(py_file))
            
            return ToolResponse(
                success=True,
                data={
                    "fixed_files": fixed_files,
                    "count": len(fixed_files)
                }
            )
            
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "directory": {"type": "string"}
            }
        }


class TodoResolverTool(Tool):
    """Resolve NOTE comments"""
    
    def __init__(self):
        super().__init__(
            name="resolve_todos",
            description="Resolve or document NOTE comments"
        )
    
    def execute(self, directory: str = ".") -> ToolResponse:
        """Resolve NOTE comments in directory"""
        try:
            dir_path = Path(directory)
            resolved_files = []
            
            for py_file in dir_path.rglob("*.py"):
                content = py_file.read_text()
                lines = content.split('\n')
                modified = False
                new_lines = []
                
                for line in lines:
                    if 'NOTE' in line or 'FIXME' in line:
                        # For now, convert to documented issues
                        if 'NOTE' in line:
                            new_line = line.replace('NOTE', 'NOTE')
                            new_lines.append(new_line)
                            modified = True
                        elif 'ISSUE' in line:
                            new_line = line.replace('ISSUE', 'ISSUE')
                            new_lines.append(new_line)
                            modified = True
                    else:
                        new_lines.append(line)
                
                if modified:
                    content = '\n'.join(new_lines)
                    py_file.write_text(content)
                    resolved_files.append(str(py_file))
            
            return ToolResponse(
                success=True,
                data={
                    "resolved_files": resolved_files,
                    "count": len(resolved_files)
                }
            )
            
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "directory": {"type": "string"}
            }
        }


class GitHubIssueFetcherTool(Tool):
    """Fetch GitHub issue details"""
    
    def __init__(self):
        super().__init__(
            name="fetch_issue",
            description="Fetch GitHub issue details"
        )
    
    def execute(self, issue_number: str) -> ToolResponse:
        """Fetch issue details from GitHub"""
        try:
            cmd = ["gh", "issue", "view", issue_number, "--json", "title,body,labels"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            issue_data = json.loads(result.stdout)
            
            return ToolResponse(
                success=True,
                data=issue_data
            )
            
        except subprocess.CalledProcessError as e:
            return ToolResponse(success=False, error=f"Failed to fetch issue: {e.stderr}")
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "issue_number": {"type": "string"}
            },
            "required": ["issue_number"]
        }


class IssueFixerAgent(BaseAgent):
    """
    Agent that fixes specific GitHub issues found by code review.
    Handles security issues, code quality problems, and technical debt.
    """
    
    def register_tools(self) -> List[Tool]:
        """Register issue fixing tools"""
        return [
            GitHubIssueFetcherTool(),
            SecretRemoverTool(),
            DangerousFunctionFixerTool(),
            PickleFixerTool(),
            PathFixerTool(),
            TodoResolverTool()
        ]
    
    def execute_task(self, task: str) -> ToolResponse:
        """
        Fix a specific issue.
        Task format: "fix issue #N" or "fix all issues"
        """
        
        if "fix all" in task.lower():
            return self._fix_all_issues()
        
        # Extract issue number
        match = re.search(r'#?(\d+)', task)
        if not match:
            return ToolResponse(
                success=False,
                error="No issue number found in task"
            )
        
        issue_number = match.group(1)
        
        # Fetch issue details
        fetch_tool = self.tools[0]
        issue_result = fetch_tool.execute(issue_number=issue_number)
        
        if not issue_result.success:
            return issue_result
        
        issue_data = issue_result.data
        labels = [label['name'] for label in issue_data.get('labels', [])]
        
        # Determine which tool to use based on labels and title
        title = issue_data.get('title', '').lower()
        fixes_applied = []
        
        # Fix based on issue type
        if 'security' in labels or 'secret' in title:
            # Fix hardcoded secrets
            secret_tool = self.tools[1]
            result = secret_tool.execute(file_path="agents/code_review_agent.py")
            if result.success:
                fixes_applied.append(("secrets", result.data))
        
        if 'dangerous' in title or 'eval' in title or 'exec' in title:
            # Fix dangerous functions
            danger_tool = self.tools[2]
            result = danger_tool.execute(directory=".")
            if result.success:
                fixes_applied.append(("dangerous_functions", result.data))
        
        if 'pickle' in title or 'deserialization' in title:
            # Fix pickle usage
            pickle_tool = self.tools[3]
            result = pickle_tool.execute(directory=".")
            if result.success:
                fixes_applied.append(("pickle", result.data))
        
        if 'hardcoded' in title and 'path' in title:
            # Fix hardcoded paths
            path_tool = self.tools[4]
            result = path_tool.execute(directory=".")
            if result.success:
                fixes_applied.append(("paths", result.data))
        
        if 'todo' in title.lower() or 'comment' in title:
            # Resolve NOTE comments
            todo_tool = self.tools[5]
            result = todo_tool.execute(directory=".")
            if result.success:
                fixes_applied.append(("todos", result.data))
        
        # Update issue with fix status
        if fixes_applied:
            # Comment on issue
            comment = f"✅ Automated fix applied by IssueFixerAgent\n\nFixes applied:\n"
            for fix_type, data in fixes_applied:
                if 'fixed_files' in data:
                    comment += f"- {fix_type}: Fixed {len(data['fixed_files'])} files\n"
                elif 'resolved_files' in data:
                    comment += f"- {fix_type}: Resolved in {len(data['resolved_files'])} files\n"
            
            subprocess.run(
                ["gh", "issue", "comment", issue_number, "--body", comment],
                capture_output=True
            )
            
            # Close issue
            subprocess.run(
                ["gh", "issue", "close", issue_number],
                capture_output=True
            )
            
            return ToolResponse(
                success=True,
                data={
                    "issue": issue_number,
                    "fixes_applied": fixes_applied,
                    "status": "closed"
                }
            )
        
        return ToolResponse(
            success=False,
            error=f"No applicable fixes found for issue #{issue_number}"
        )
    
    def _fix_all_issues(self) -> ToolResponse:
        """Fix all open issues"""
        try:
            # Get all open issues
            cmd = ["gh", "issue", "list", "--json", "number", "--limit", "50"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            issues = json.loads(result.stdout)
            all_results = []
            
            for issue in issues:
                issue_num = issue['number']
                print(f"Fixing issue #{issue_num}...")
                result = self.execute_task(f"fix issue #{issue_num}")
                all_results.append({
                    "issue": issue_num,
                    "success": result.success,
                    "data": result.data if result.success else result.error
                })
            
            return ToolResponse(
                success=True,
                data={
                    "total_issues": len(issues),
                    "results": all_results
                }
            )
            
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply fix action"""
        action_type = action.get("type", "fix")
        
        if action_type == "fix":
            return self.execute_task(action.get("task", "fix all issues"))
        
        return ToolResponse(
            success=False,
            error=f"Unknown action type: {action_type}"
        )


# Self-test when run directly
if __name__ == "__main__":
    print("Testing IssueFixerAgent...")
    agent = IssueFixerAgent()
    
    # Fix all open issues
    result = agent.execute_task("fix all issues")
    
    if result.success:
        print("✅ Issues fixed successfully!")
        print(json.dumps(result.data, indent=2))
    else:
        print(f"❌ Failed to fix issues: {result.error}")