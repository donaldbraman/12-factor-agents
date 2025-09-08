"""
UvMigrationAgent - Migrates all Python operations to use uv.
Designed to solve Issue #009: Migrate All Python Operations to UV
"""
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
import json

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse


class FileUpdaterTool(Tool):
    """Update files with uv-specific changes"""
    
    def __init__(self):
        super().__init__(
            name="update_file",
            description="Update a file with uv-specific changes"
        )
    
    def execute(self, file_path: str, replacements: List[Tuple[str, str]]) -> ToolResponse:
        """Update file with multiple replacements"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return ToolResponse(
                    success=False,
                    error=f"File not found: {file_path}"
                )
            
            content = path.read_text()
            original_content = content
            changes_made = []
            
            for old_pattern, new_pattern in replacements:
                if old_pattern in content:
                    content = content.replace(old_pattern, new_pattern)
                    changes_made.append(f"Replaced '{old_pattern[:30]}...' with '{new_pattern[:30]}...'")
            
            if content != original_content:
                path.write_text(content)
                return ToolResponse(
                    success=True,
                    data={
                        "file": str(path),
                        "changes": changes_made,
                        "modified": True
                    }
                )
            else:
                return ToolResponse(
                    success=True,
                    data={
                        "file": str(path),
                        "changes": [],
                        "modified": False,
                        "message": "No changes needed"
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
                "file_path": {"type": "string"},
                "replacements": {"type": "array"}
            },
            "required": ["file_path", "replacements"]
        }


class ShebangUpdaterTool(Tool):
    """Update Python shebangs to use uv"""
    
    def __init__(self):
        super().__init__(
            name="update_shebangs",
            description="Update Python shebangs in files to use uv"
        )
    
    def execute(self, directory: str, pattern: str = "*.py") -> ToolResponse:
        """Update shebangs in Python files"""
        try:
            base_path = Path(directory)
            updated_files = []
            
            for file_path in base_path.rglob(pattern):
                if file_path.is_file():
                    content = file_path.read_text()
                    lines = content.split('\n')
                    
                    if lines and lines[0].startswith('#!/usr/bin/env python'):
                        # Update shebang
                        lines[0] = '#!/usr/bin/env uv run python'
                        new_content = '\n'.join(lines)
                        file_path.write_text(new_content)
                        updated_files.append(str(file_path))
            
            return ToolResponse(
                success=True,
                data={
                    "updated_files": updated_files,
                    "count": len(updated_files)
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
                "directory": {"type": "string"},
                "pattern": {"type": "string"}
            },
            "required": ["directory"]
        }


class DocumentationUpdaterTool(Tool):
    """Update documentation to use uv commands"""
    
    def __init__(self):
        super().__init__(
            name="update_docs",
            description="Update documentation files with uv commands"
        )
    
    def execute(self, doc_path: str) -> ToolResponse:
        """Update documentation with uv commands"""
        try:
            path = Path(doc_path)
            
            if not path.exists():
                return ToolResponse(
                    success=False,
                    error=f"Documentation file not found: {doc_path}"
                )
            
            content = path.read_text()
            original = content
            
            # Common replacements for documentation
            replacements = [
                # Python execution
                ('python3 ', 'uv run '),
                ('python ', 'uv run python '),
                ('`python3', '`uv run'),
                ('`python ', '`uv run python '),
                
                # Pip commands
                ('pip install', 'uv pip install'),
                ('pip3 install', 'uv pip install'),
                
                # Script execution in markdown
                ('```bash\npython3', '```bash\nuv run'),
                ('```sh\npython3', '```sh\nuv run'),
                
                # Specific patterns
                ('Path.home() / "Documents" / "GitHub"/12-factor-agents/bin/agent', 'uv run Path.home() / "Documents" / "GitHub"/12-factor-agents/bin/agent'),
                ('./bin/agent', 'uv run bin/agent'),
                ('bin/agent', 'uv run bin/agent'),
                
                # sys.executable in code blocks
                ('[sys.executable,', '["uv", "run",'),
                
                # Virtual environment
                ('python -m venv', 'uv venv'),
                ('virtualenv', 'uv venv'),
            ]
            
            changes = []
            for old, new in replacements:
                if old in content and new not in content:
                    content = content.replace(old, new)
                    changes.append(f"{old} -> {new}")
            
            # Fix double uv run (in case of multiple replacements)
            content = content.replace('uv run uv run', 'uv run')
            content = content.replace('uv run python3', 'uv run')
            
            if content != original:
                path.write_text(content)
                return ToolResponse(
                    success=True,
                    data={
                        "file": str(path),
                        "changes": changes,
                        "modified": True
                    }
                )
            else:
                return ToolResponse(
                    success=True,
                    data={
                        "file": str(path),
                        "modified": False,
                        "message": "Already up to date"
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
                "doc_path": {"type": "string"}
            },
            "required": ["doc_path"]
        }


class UvMigrationAgent(BaseAgent):
    """
    Agent responsible for migrating all Python operations to use uv.
    Handles Issue #009: Migrate All Python Operations to UV
    """
    
    def register_tools(self) -> List[Tool]:
        """Register migration tools"""
        return [
            FileUpdaterTool(),
            ShebangUpdaterTool(),
            DocumentationUpdaterTool()
        ]
    
    def execute_task(self, task: str) -> ToolResponse:
        """
        Execute uv migration across the codebase.
        Expected task: "migrate to uv" or "solve issue #009"
        """
        
        base_path = Path.home() / "Documents" / "GitHub" / "12-factor-agents"
        results = []
        
        # Step 1: Update shebangs in Python files
        shebang_tool = self.tools[1]
        shebang_result = shebang_tool.execute(
            directory=str(base_path),
            pattern="*.py"
        )
        results.append(("shebangs", shebang_result))
        
        # Step 2: Update bin/event shebang specifically
        file_tool = self.tools[0]
        event_result = file_tool.execute(
            file_path=str(base_path / "bin" / "event"),
            replacements=[
                ("#!/usr/bin/env python3", "#!/usr/bin/env uv run python"),
                ("[sys.executable,", '["uv", "run",'),
            ]
        )
        results.append(("bin/event", event_result))
        
        # Step 3: Update all agent files with uv run comments
        agents_dir = base_path / "agents"
        for agent_file in agents_dir.glob("*.py"):
            agent_result = file_tool.execute(
                file_path=str(agent_file),
                replacements=[
                    ("# Self-test when run directly\nif __name__", 
                     f"# Self-test when run directly\n# Usage: uv run {agent_file.relative_to(base_path)}\nif __name__"),
                    ('["uv", "run", str(script_path)]', '["uv", "run", str(script_path)]'),
                    ('subprocess.Popen(\n                    [sys.executable,', 
                     'subprocess.Popen(\n                    ["uv", "run",'),
                ]
            )
            results.append((f"agent/{agent_file.name}", agent_result))
        
        # Step 4: Update documentation files
        doc_tool = self.tools[2]
        doc_files = [
            "README.md",
            "IMPLEMENTATION-PLAN.md", 
            "12-FACTOR-LOCAL-ARCHITECTURE.md",
            "12-FACTOR-DOGFOODING-REPORT.md"
        ]
        
        for doc_file in doc_files:
            doc_path = base_path / doc_file
            if doc_path.exists():
                doc_result = doc_tool.execute(doc_path=str(doc_path))
                results.append((doc_file, doc_result))
        
        # Step 5: Update example files
        examples_dir = base_path / "examples" / "triggers"
        if examples_dir.exists():
            for example_file in examples_dir.glob("*.py"):
                example_result = file_tool.execute(
                    file_path=str(example_file),
                    replacements=[
                        ("#!/usr/bin/env python3", "#!/usr/bin/env uv run python"),
                        ("python3 ", "uv run "),
                    ]
                )
                results.append((f"example/{example_file.name}", example_result))
        
        # Step 6: Update core/triggers.py for subprocess calls
        triggers_file = base_path / "core" / "triggers.py"
        if triggers_file.exists():
            triggers_result = file_tool.execute(
                file_path=str(triggers_file),
                replacements=[
                    ('["uv", "run", str(script_path)]', '["uv", "run", str(script_path)]'),
                    ('subprocess.Popen(\n        [sys.executable,', 
                     'subprocess.Popen(\n        ["uv", "run",'),
                ]
            )
            results.append(("core/triggers.py", triggers_result))
        
        # Step 7: Create pyproject.toml if it doesn't exist
        pyproject_path = base_path / "pyproject.toml"
        if not pyproject_path.exists():
            pyproject_content = """[project]
name = "12-factor-agents"
version = "1.0.0"
description = "12-Factor compliant AI agent framework"
requires-python = ">=3.9"
dependencies = [
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
    "ruff>=0.1",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0",
]
"""
            pyproject_path.write_text(pyproject_content)
            results.append(("pyproject.toml", ToolResponse(
                success=True,
                data={"created": "pyproject.toml", "message": "Created pyproject.toml for uv"}
            )))
        
        # Compile results
        total_files = len(results)
        modified_files = sum(1 for _, r in results if r.success and r.data.get("modified", False))
        
        self.state.set("issue_009_status", "resolved")
        self.state.set("uv_migration_complete", True)
        
        return ToolResponse(
            success=True,
            data={
                "total_files_checked": total_files,
                "files_modified": modified_files,
                "migration_complete": True,
                "issue": "#009",
                "status": "resolved",
                "details": [
                    {"file": name, "modified": r.data.get("modified", False)}
                    for name, r in results if r.success
                ]
            }
        )
    
    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply migration action"""
        action_type = action.get("type", "migrate")
        
        if action_type == "migrate":
            return self.execute_task(action.get("task", "migrate to uv"))
        elif action_type == "verify":
            # Check if uv is being used
            base_path = Path.home() / "Documents" / "GitHub" / "12-factor-agents"
            
            checks = []
            # Check setup.sh
            setup_sh = base_path / "setup.sh"
            if setup_sh.exists():
                content = setup_sh.read_text()
                checks.append(("setup.sh uses uv", "uv venv" in content))
            
            # Check an agent file
            agent_file = base_path / "agents" / "repository_setup_agent.py"
            if agent_file.exists():
                content = agent_file.read_text()
                checks.append(("agents have uv usage comments", "uv run" in content))
            
            return ToolResponse(
                success=all(check[1] for check in checks),
                data={"checks": dict(checks)}
            )
        
        return ToolResponse(
            success=False,
            error=f"Unknown action type: {action_type}"
        )


# Self-test when run directly
# Usage: uv run agents/uv_migration_agent.py
if __name__ == "__main__":
    print("Testing UvMigrationAgent...")
    agent = UvMigrationAgent()
    
    # First verify current state
    verify_result = agent._apply_action({"type": "verify"})
    print(f"Pre-migration state: {verify_result.data}")
    
    # Run migration
    print("\nRunning uv migration...")
    result = agent.execute_task("migrate all Python operations to use uv")
    
    if result.success:
        print("✅ UV migration successful!")
        print(f"Files modified: {result.data['files_modified']}/{result.data['total_files_checked']}")
        print("\nModified files:")
        for detail in result.data.get("details", []):
            if detail["modified"]:
                print(f"  - {detail['file']}")
    else:
        print(f"❌ Migration failed: {result.error}")