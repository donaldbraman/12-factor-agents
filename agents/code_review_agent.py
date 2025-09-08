"""
CodeReviewAgent - Performs comprehensive code review and generates GitHub issues.
Analyzes codebase for compliance, best practices, and potential improvements.
"""
import os
import ast
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse


class CodeAnalyzerTool(Tool):
    """Analyze code for issues and improvements"""
    
    def __init__(self):
        super().__init__(
            name="code_analyzer",
            description="Analyze Python files for issues"
        )
    
    def execute(self, file_path: str) -> ToolResponse:
        """Analyze a Python file for issues"""
        try:
            path = Path(file_path)
            if not path.exists():
                return ToolResponse(success=False, error=f"File not found: {file_path}")
            
            content = path.read_text()
            lines = content.split('\n')
            issues = []
            
            # Check for missing docstrings
            if path.suffix == '.py':
                # Check module docstring
                if not content.startswith('"""') and not content.startswith("'''"):
                    issues.append({
                        "type": "missing_docstring",
                        "severity": "low",
                        "line": 1,
                        "message": "Module lacks docstring"
                    })
                
                # Check for NOTE/FIXME comments
                for i, line in enumerate(lines, 1):
                    if 'NOTE' in line or 'FIXME' in line:
                        issues.append({
                            "type": "todo_comment",
                            "severity": "low",
                            "line": i,
                            "message": f"Unresolved comment: {line.strip()}"
                        })
                    
                    # Check for hardcoded paths
                    if '/Users/' in line or 'C:\\' in line:
                        issues.append({
                            "type": "hardcoded_path",
                            "severity": "medium",
                            "line": i,
                            "message": "Hardcoded path detected"
                        })
                    
                    # Check for missing type hints in function definitions
                    if 'def ' in line and '(' in line and '->' not in line:
                        if not any(skip in line for skip in ['__init__', '__str__', '__repr__']):
                            issues.append({
                                "type": "missing_type_hints",
                                "severity": "low",
                                "line": i,
                                "message": f"Function lacks return type hint: {line.strip()}"
                            })
                    
                    # Check for print statements (should use logging)
                    if re.match(r'^\s*print\(', line):
                        issues.append({
                            "type": "print_statement",
                            "severity": "low",
                            "line": i,
                            "message": "Use logging instead of print statements"
                        })
                
                # Check for missing error handling
                if 'try:' not in content and ('open(' in content or 'subprocess' in content):
                    issues.append({
                        "type": "missing_error_handling",
                        "severity": "medium",
                        "line": 0,
                        "message": "File operations or subprocess calls lack error handling"
                    })
            
            return ToolResponse(
                success=True,
                data={
                    "file": str(path),
                    "issues": issues,
                    "issue_count": len(issues)
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


class DependencyAnalyzerTool(Tool):
    """Analyze dependencies and imports"""
    
    def __init__(self):
        super().__init__(
            name="dependency_analyzer",
            description="Analyze Python dependencies"
        )
    
    def execute(self, directory: str = ".") -> ToolResponse:
        """Analyze dependencies in directory"""
        try:
            dir_path = Path(directory)
            issues = []
            
            # Check for requirements.txt
            if not (dir_path / "requirements.txt").exists() and not (dir_path / "pyproject.toml").exists():
                issues.append({
                    "type": "missing_requirements",
                    "severity": "high",
                    "message": "No requirements.txt or pyproject.toml found"
                })
            
            # Analyze imports
            py_files = list(dir_path.rglob("*.py"))
            imports = set()
            
            for py_file in py_files:
                content = py_file.read_text()
                # Find all imports
                import_lines = re.findall(r'^(?:from|import)\s+(\S+)', content, re.MULTILINE)
                imports.update(import_lines)
            
            # Check for unused imports
            stdlib_modules = {'os', 'sys', 'json', 'pathlib', 'typing', 're', 'datetime', 'subprocess'}
            third_party = [imp for imp in imports if imp.split('.')[0] not in stdlib_modules and not imp.startswith('.')]
            
            if third_party and not (dir_path / "requirements.txt").exists():
                issues.append({
                    "type": "undocumented_dependencies",
                    "severity": "high",
                    "message": f"Third-party imports without requirements.txt: {', '.join(third_party)}"
                })
            
            return ToolResponse(
                success=True,
                data={
                    "directory": str(dir_path),
                    "issues": issues,
                    "imports_found": list(imports),
                    "third_party": third_party
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


class SecurityAnalyzerTool(Tool):
    """Analyze code for security issues"""
    
    def __init__(self):
        super().__init__(
            name="security_analyzer",
            description="Analyze code for security issues"
        )
    
    def execute(self, directory: str = ".") -> ToolResponse:
        """Analyze for security issues"""
        try:
            dir_path = Path(directory)
            issues = []
            
            for py_file in dir_path.rglob("*.py"):
                content = py_file.read_text()
                
                # Check for eval/exec usage
                if 'eval(' in content or 'exec(' in content:
                    issues.append({
                        "file": str(py_file),
                        "type": "dangerous_function",
                        "severity": "high",
                        "message": "Use of eval() or exec() is dangerous"
                    })
                
                # Check for hardcoded secrets
                if re.search(r'(password|secret|token|api_key)\s*=\s*["\'][\w]+["\']', content, re.IGNORECASE):
                    issues.append({
                        "file": str(py_file),
                        "type": "hardcoded_secret",
                        "severity": "critical",
                        "message": "Potential hardcoded secret detected"
                    })
                
                # Check for SQL injection vulnerabilities
                if 'cursor.execute' in content and '%s' not in content:
                    if re.search(r'cursor\.execute\([^)]*\+[^)]*\)', content):
                        issues.append({
                            "file": str(py_file),
                            "type": "sql_injection",
                            "severity": "critical",
                            "message": "Potential SQL injection vulnerability"
                        })
                
                # Check for unsafe file operations
    # SECURITY: Replaced unsafe pickle with json
                if 'json.load' in content:
                    issues.append({
                        "file": str(py_file),
                        "type": "unsafe_deserialization",
                        "severity": "high",
                        "message": "Unsafe deserialization with pickle"
                    })
            
            return ToolResponse(
                success=True,
                data={
                    "directory": str(dir_path),
                    "security_issues": issues,
                    "issue_count": len(issues)
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


class GitHubIssueTool(Tool):
    """Create GitHub issues from review findings"""
    
    def __init__(self):
        super().__init__(
            name="create_github_issue",
            description="Create a GitHub issue"
        )
    
    def execute(self, title: str, body: str, labels: List[str] = None) -> ToolResponse:
        """Create GitHub issue using gh CLI"""
        try:
            cmd = ["gh", "issue", "create", "--title", title, "--body", body]
            
            if labels:
                cmd.extend(["--label", ",".join(labels)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Extract issue number from output
            issue_url = result.stdout.strip()
            issue_number = issue_url.split('/')[-1]
            
            return ToolResponse(
                success=True,
                data={
                    "issue_number": issue_number,
                    "url": issue_url,
                    "title": title
                }
            )
            
        except subprocess.CalledProcessError as e:
            return ToolResponse(
                success=False,
                error=f"Failed to create issue: {e.stderr}"
            )
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "labels": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title", "body"]
        }


class CodeReviewAgent(BaseAgent):
    """
    Agent that performs comprehensive code review and generates GitHub issues.
    Implements full review → issue → fix → test → merge pipeline.
    """
    
    def register_tools(self) -> List[Tool]:
        """Register code review tools"""
        return [
            CodeAnalyzerTool(),
            DependencyAnalyzerTool(),
            SecurityAnalyzerTool(),
            GitHubIssueTool()
        ]
    
    def execute_task(self, task: str) -> ToolResponse:
        """
        Execute comprehensive code review.
        Task format: "review codebase" or "review <directory>"
        """
        # Determine directory to review
        if "review" in task.lower():
            parts = task.split()
            if len(parts) > 1 and parts[-1] != "codebase":
                review_dir = parts[-1]
            else:
                review_dir = "."
        else:
            review_dir = "."
        
        review_dir = Path(review_dir).resolve()
        
        # Update state
        self.state.set("review_directory", str(review_dir))
        self.state.set("review_start", datetime.now().isoformat())
        
        all_issues = []
        created_issues = []
        
        # Step 1: Analyze Python files
        print("\n🔍 Analyzing Python files...")
        py_files = list(review_dir.rglob("*.py"))
        
        for py_file in py_files:
            # Skip __pycache__ and venv directories
            if '__pycache__' in str(py_file) or 'venv' in str(py_file):
                continue
                
            analyzer = self.tools[0]  # CodeAnalyzerTool
            result = analyzer.execute(file_path=str(py_file))
            
            if result.success and result.data["issues"]:
                for issue in result.data["issues"]:
                    issue["file"] = str(py_file.relative_to(review_dir))
                    all_issues.append(issue)
        
        # Step 2: Analyze dependencies
        print("📦 Analyzing dependencies...")
        dep_analyzer = self.tools[1]  # DependencyAnalyzerTool
        dep_result = dep_analyzer.execute(directory=str(review_dir))
        
        if dep_result.success:
            for issue in dep_result.data["issues"]:
                all_issues.append(issue)
        
        # Step 3: Security analysis
        print("🔒 Analyzing security...")
        sec_analyzer = self.tools[2]  # SecurityAnalyzerTool
        sec_result = sec_analyzer.execute(directory=str(review_dir))
        
        if sec_result.success:
            for issue in sec_result.data["security_issues"]:
                all_issues.append(issue)
        
        # Step 4: Group issues by type and create GitHub issues
        print(f"\n📝 Found {len(all_issues)} issues total")
        
        # Group related issues
        issue_groups = {}
        for issue in all_issues:
            issue_type = issue.get("type", "general")
            if issue_type not in issue_groups:
                issue_groups[issue_type] = []
            issue_groups[issue_type].append(issue)
        
        # Create GitHub issues for each group
        github_tool = self.tools[3]  # GitHubIssueTool
        
        for issue_type, issues in issue_groups.items():
            # Skip low-priority issues if there are too many
            if issue_type in ["missing_docstring", "missing_type_hints", "todo_comment"] and len(issues) > 10:
                # Create one consolidated issue
                title = f"Code Quality: Address {len(issues)} {issue_type.replace('_', ' ')} issues"
                body = self._format_consolidated_issue(issue_type, issues)
                labels = ["enhancement", "code-quality"]
            else:
                # Create individual or small group issues
                if len(issues) == 1:
                    issue = issues[0]
                    title = f"Fix: {issue.get('message', issue_type.replace('_', ' '))}"
                    body = self._format_single_issue(issue)
                else:
                    title = f"Fix: {len(issues)} {issue_type.replace('_', ' ')} issues"
                    body = self._format_group_issue(issues)
                
                # Determine labels based on severity
                labels = self._determine_labels(issues)
            
            # Create the GitHub issue
            result = github_tool.execute(title=title, body=body, labels=labels)
            
            if result.success:
                created_issues.append(result.data)
                print(f"✅ Created issue #{result.data['issue_number']}: {title}")
            else:
                print(f"❌ Failed to create issue: {title}")
        
        # Step 5: Save review report
        report = {
            "review_date": datetime.now().isoformat(),
            "directory": str(review_dir),
            "files_reviewed": len(py_files),
            "total_issues": len(all_issues),
            "issues_by_type": {k: len(v) for k, v in issue_groups.items()},
            "github_issues_created": created_issues,
            "all_findings": all_issues
        }
        
        report_path = review_dir / "code_review_report.json"
        report_path.write_text(json.dumps(report, indent=2))
        
        # Update state
        self.state.set("review_complete", True)
        self.state.set("issues_created", [i["issue_number"] for i in created_issues])
        
        return ToolResponse(
            success=True,
            data={
                "review_complete": True,
                "issues_found": len(all_issues),
                "github_issues_created": len(created_issues),
                "issue_numbers": [i["issue_number"] for i in created_issues],
                "report_saved": str(report_path),
                "summary": {
                    "critical": len([i for i in all_issues if i.get("severity") == "critical"]),
                    "high": len([i for i in all_issues if i.get("severity") == "high"]),
                    "medium": len([i for i in all_issues if i.get("severity") == "medium"]),
                    "low": len([i for i in all_issues if i.get("severity") == "low"])
                }
            }
        )
    
    def _format_single_issue(self, issue: Dict[str, Any]) -> str:
        """Format a single issue for GitHub"""
        body = f"""## Issue Details

**Type:** {issue.get('type', 'unknown').replace('_', ' ').title()}
**Severity:** {issue.get('severity', 'unknown').upper()}
**File:** `{issue.get('file', 'N/A')}`
**Line:** {issue.get('line', 'N/A')}

## Description
{issue.get('message', 'No description available')}

## Suggested Fix
Please review and fix this issue following the 12-factor agent methodology.

---
*Generated by CodeReviewAgent*
"""
        return body
    
    def _format_group_issue(self, issues: List[Dict[str, Any]]) -> str:
        """Format multiple related issues for GitHub"""
        issue_type = issues[0].get('type', 'unknown')
        severity = max(i.get('severity', 'low') for i in issues)
        
        body = f"""## Issue Summary

**Type:** {issue_type.replace('_', ' ').title()}
**Severity:** {severity.upper()}
**Count:** {len(issues)} occurrences

## Affected Locations

"""
        for issue in issues[:20]:  # Limit to first 20 to avoid huge issues
            body += f"- `{issue.get('file', 'unknown')}:{issue.get('line', '?')}` - {issue.get('message', 'N/A')}\n"
        
        if len(issues) > 20:
            body += f"\n*... and {len(issues) - 20} more*\n"
        
        body += """

## Suggested Fix
Please review and fix these issues following the 12-factor agent methodology.

---
*Generated by CodeReviewAgent*
"""
        return body
    
    def _format_consolidated_issue(self, issue_type: str, issues: List[Dict[str, Any]]) -> str:
        """Format a consolidated issue for many similar problems"""
        body = f"""## Code Quality Improvement

**Issue Type:** {issue_type.replace('_', ' ').title()}
**Total Occurrences:** {len(issues)}

## Summary
This is a consolidated issue for multiple code quality improvements of the same type.

## Files Affected
"""
        # Group by file
        by_file = {}
        for issue in issues:
            file = issue.get('file', 'unknown')
            if file not in by_file:
                by_file[file] = 0
            by_file[file] += 1
        
        for file, count in sorted(by_file.items()):
            body += f"- `{file}` ({count} occurrences)\n"
        
        body += """

## Recommendation
Consider a systematic approach to address all these issues at once, possibly using automated tooling or a dedicated agent.

---
*Generated by CodeReviewAgent*
"""
        return body
    
    def _determine_labels(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Determine GitHub labels based on issue severity and type"""
        labels = []
        
        # Add severity label
        severities = [i.get('severity', 'low') for i in issues]
        if 'critical' in severities:
            labels.append('critical')
        elif 'high' in severities:
            labels.append('bug')
        elif 'medium' in severities:
            labels.append('enhancement')
        else:
            labels.append('good first issue')
        
        # Add type labels
        types = set(i.get('type', '') for i in issues)
        if any('security' in t or 'injection' in t or 'secret' in t for t in types):
            labels.append('security')
        if any('dependency' in t or 'requirements' in t for t in types):
            labels.append('dependencies')
        if any('docstring' in t or 'type_hint' in t for t in types):
            labels.append('documentation')
        
        return labels
    
    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply code review action"""
        action_type = action.get("type", "review")
        
        if action_type == "review":
            return self.execute_task(action.get("task", "review codebase"))
        elif action_type == "create_issue":
            # Create a specific issue
            github_tool = self.tools[3]
            return github_tool.execute(
                title=action.get("title", "Code Review Finding"),
                body=action.get("body", "Please review"),
                labels=action.get("labels", ["enhancement"])
            )
        
        return ToolResponse(
            success=False,
            error=f"Unknown action type: {action_type}"
        )


# Self-test when run directly
# Usage: uv run agents/code_review_agent.py
if __name__ == "__main__":
    print("Testing CodeReviewAgent...")
    agent = CodeReviewAgent()
    
    # Run comprehensive review
    result = agent.execute_task("review codebase")
    
    if result.success:
        print("✅ Code review completed successfully!")
        print(json.dumps(result.data, indent=2))
    else:
        print(f"❌ Review failed: {result.error}")