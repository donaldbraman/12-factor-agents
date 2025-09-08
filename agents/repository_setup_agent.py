"""
RepositorySetupAgent - Handles repository initialization and setup tasks.
Designed to solve Issue #001: Core Repository Setup
"""
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime

# Import from parent directory since we're bootstrapping
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse


class GitInitTool(Tool):
    """Initialize git repository"""
    
    def __init__(self):
        super().__init__(
            name="git_init",
            description="Initialize a git repository"
        )
    
    def execute(self, path: str = ".") -> ToolResponse:
        """Initialize git in specified directory"""
        try:
            repo_path = Path(path).resolve()
            
            # Check if already a git repo
            if (repo_path / ".git").exists():
                return ToolResponse(
                    success=True,
                    data={"message": "Repository already initialized", "path": str(repo_path)}
                )
            
            # Initialize git
            result = subprocess.run(
                ["git", "init"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return ToolResponse(
                    success=True,
                    data={"message": "Git repository initialized", "path": str(repo_path)}
                )
            else:
                return ToolResponse(
                    success=False,
                    error=result.stderr
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
                "path": {"type": "string", "description": "Repository path"}
            }
        }


class DirectoryCreatorTool(Tool):
    """Create directory structure"""
    
    def __init__(self):
        super().__init__(
            name="create_directories",
            description="Create directory structure for repository"
        )
    
    def execute(self, base_path: str, directories: List[str]) -> ToolResponse:
        """Create directory structure"""
        try:
            base = Path(base_path).resolve()
            created = []
            
            for dir_name in directories:
                dir_path = base / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                created.append(str(dir_path))
            
            return ToolResponse(
                success=True,
                data={
                    "created_directories": created,
                    "count": len(created)
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
                "base_path": {"type": "string"},
                "directories": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["base_path", "directories"]
        }


class FileCreatorTool(Tool):
    """Create files with content"""
    
    def __init__(self):
        super().__init__(
            name="create_file",
            description="Create a file with specified content"
        )
    
    def execute(self, path: str, content: str) -> ToolResponse:
        """Create file with content"""
        try:
            file_path = Path(path).resolve()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            
            return ToolResponse(
                success=True,
                data={
                    "file": str(file_path),
                    "size": len(content)
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
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }


class RepositorySetupAgent(BaseAgent):
    """
    Agent responsible for setting up the 12-factor-agents repository.
    Handles Issue #001: Core Repository Setup
    """
    
    def register_tools(self) -> List[Tool]:
        """Register repository setup tools"""
        return [
            GitInitTool(),
            DirectoryCreatorTool(),
            FileCreatorTool()
        ]
    
    def execute_task(self, task: str) -> ToolResponse:
        """
        Execute repository setup based on issue requirements.
        Expected task format: "setup repository at <path>" or "solve issue #001"
        """
        # Determine repository path
        if "at" in task:
            repo_path = task.split("at")[-1].strip()
        else:
            repo_path = str(Path.home() / "Documents" / "GitHub" / "12-factor-agents")
        
        repo_path = Path(repo_path).resolve()
        
        # Update state
        self.state.set("repo_path", str(repo_path))
        
        results = []
        
        # Step 1: Create directories
        directories = [
            "core",
            "agents", 
            "bin",
            "shared-state",
            "orchestration",
            "docs",
            "prompts/base",
            "prompts/specialized",
            "tests",
            "examples"
        ]
        
        dir_tool = self.tools[1]  # DirectoryCreatorTool
        dir_result = dir_tool.execute(
            base_path=str(repo_path),
            directories=directories
        )
        results.append(("directories", dir_result))
        
        if not dir_result.success:
            return dir_result
        
        # Step 2: Initialize git
        git_tool = self.tools[0]  # GitInitTool
        git_result = git_tool.execute(path=str(repo_path))
        results.append(("git", git_result))
        
        # Step 3: Create README.md
        readme_content = """# 12-Factor Agents Framework

A local-first, multi-repository AI agent system following the 12-factor methodology.

## Features
- ✅ 100% local operation
- ✅ Cross-repository agent sharing
- ✅ No external dependencies
- ✅ Git-friendly configuration
- ✅ Full 12-factor compliance

## Quick Start

1. Run setup: `./setup.sh`
2. Link in your project: `ln -s ../12-factor-agents/core .claude/agents`
3. Run agents: `bin/agent <name> "<task>"`

## Structure

```
12-factor-agents/
├── core/           # Base classes and interfaces
├── agents/         # Reusable agent implementations
├── bin/           # CLI tools
├── shared-state/  # Cross-repo state management
├── orchestration/ # Multi-agent pipelines
├── prompts/       # Externalized prompts
├── docs/          # Documentation
└── tests/         # Test suite
```

## Documentation

See [docs/](docs/) for detailed documentation.

## License

MIT
"""
        
        file_tool = self.tools[2]  # FileCreatorTool
        readme_result = file_tool.execute(
            path=str(repo_path / "README.md"),
            content=readme_content
        )
        results.append(("readme", readme_result))
        
        # Step 4: Create .gitignore
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
.env

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Agent-specific
*.pid
*.log
.claude-shared-state/
tmp/
temp/

# Test coverage
htmlcov/
.coverage
.pytest_cache/
"""
        
        gitignore_result = file_tool.execute(
            path=str(repo_path / ".gitignore"),
            content=gitignore_content
        )
        results.append(("gitignore", gitignore_result))
        
        # Step 5: Create setup.sh
        setup_content = """#!/bin/bash
# Setup script for 12-factor-agents framework

echo "🚀 Setting up 12-factor-agents framework..."

# Create shared state directory
mkdir -p ~/.claude-shared-state/{global,by-repo,locks,history,events,pids}

# Make CLI executable
chmod +x bin/agent 2>/dev/null || true

# Create initial registry
echo '{"agents": {}}' > ~/.claude-shared-state/agent-registry.json

# Install Python dependencies (if any)
if [ -f requirements.txt ]; then
    echo "📦 Installing Python dependencies..."
    uv pip install -r requirements.txt
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. In your project: ln -s $(pwd)/core .claude/agents"
echo "2. Run an agent: ./bin/agent list"
echo ""
"""
        
        setup_result = file_tool.execute(
            path=str(repo_path / "setup.sh"),
            content=setup_content
        )
        results.append(("setup", setup_result))
        
        # Make setup.sh executable
        try:
            os.chmod(repo_path / "setup.sh", 0o755)
        except:
            pass
        
        # Step 6: Create LICENSE
        license_content = """MIT License

Copyright (c) 2024 12-Factor Agents Framework

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
        
        license_result = file_tool.execute(
            path=str(repo_path / "LICENSE"),
            content=license_content
        )
        results.append(("license", license_result))
        
        # Step 7: Create __init__.py files
        for module_dir in ["core", "agents", "shared-state", "orchestration"]:
            init_result = file_tool.execute(
                path=str(repo_path / module_dir / "__init__.py"),
                content=f'"""{module_dir} module for 12-factor-agents framework."""\n'
            )
            results.append((f"init_{module_dir}", init_result))
        
        # Compile results
        all_success = all(r[1].success for r in results)
        
        if all_success:
            # Mark issue as resolved
            self.state.set("issue_001_status", "resolved")
            self.state.set("repository_initialized", True)
            
            return ToolResponse(
                success=True,
                data={
                    "repository": str(repo_path),
                    "directories_created": len(directories),
                    "files_created": len([r for r in results if "file" in r[0] or "readme" in r[0]]),
                    "git_initialized": git_result.success,
                    "setup_complete": True,
                    "issue": "#001",
                    "status": "resolved"
                }
            )
        else:
            failed = [r[0] for r in results if not r[1].success]
            return ToolResponse(
                success=False,
                error=f"Failed steps: {', '.join(failed)}",
                data={"failed_steps": failed}
            )
    
    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply repository setup action"""
        action_type = action.get("type", "setup")
        
        if action_type == "setup":
            return self.execute_task(action.get("task", "setup repository"))
        elif action_type == "verify":
            # Verify repository setup
            repo_path = Path(self.state.get("repo_path", "."))
            checks = {
                "git": (repo_path / ".git").exists(),
                "core": (repo_path / "core").exists(),
                "readme": (repo_path / "README.md").exists(),
                "setup": (repo_path / "setup.sh").exists()
            }
            
            return ToolResponse(
                success=all(checks.values()),
                data={"checks": checks}
            )
        
        return ToolResponse(
            success=False,
            error=f"Unknown action type: {action_type}"
        )


# Self-test when run directly
# Usage: uv run agents/repository_setup_agent.py
if __name__ == "__main__":
    print("Testing RepositorySetupAgent...")
    agent = RepositorySetupAgent()
    
    # Test on the actual 12-factor-agents directory
    result = agent.execute_task('setup repository at /Users/dbraman/Documents/GitHub/12-factor-agents')
    
    if result.success:
        print("✅ Repository setup successful!")
        print(json.dumps(result.data, indent=2))
    else:
        print(f"❌ Setup failed: {result.error}")