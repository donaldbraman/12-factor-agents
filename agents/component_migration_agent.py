"""
ComponentMigrationAgent - Migrates existing components to new structure.
Designed to solve Issue #002: Migrate Existing Base Components
"""
import shutil
from pathlib import Path
from typing import Dict, Any, List
import json

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse


class FileMigrationTool(Tool):
    """Migrate files from source to destination"""
    
    def __init__(self):
        super().__init__(
            name="migrate_file",
            description="Copy or move a file to new location"
        )
    
    def execute(self, source: str, destination: str, operation: str = "copy") -> ToolResponse:
        """Migrate a file"""
        try:
            src = Path(source)
            dst = Path(destination)
            
            # Check source exists
            if not src.exists():
                # Try relative to .claude directory
                alt_src = Path.home() / "Documents" / "GitHub" / ".claude" / source
                if alt_src.exists():
                    src = alt_src
                else:
                    return ToolResponse(
                        success=False,
                        error=f"Source file not found: {source}"
                    )
            
            # Ensure destination directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            if operation == "copy":
                shutil.copy2(src, dst)
            elif operation == "move":
                shutil.move(str(src), str(dst))
            else:
                return ToolResponse(
                    success=False,
                    error=f"Unknown operation: {operation}"
                )
            
            return ToolResponse(
                success=True,
                data={
                    "source": str(src),
                    "destination": str(dst),
                    "operation": operation,
                    "size": dst.stat().st_size if dst.exists() else 0
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
                "source": {"type": "string"},
                "destination": {"type": "string"},
                "operation": {"type": "string", "enum": ["copy", "move"]}
            },
            "required": ["source", "destination"]
        }


class ComponentVerificationTool(Tool):
    """Verify components are properly migrated"""
    
    def __init__(self):
        super().__init__(
            name="verify_components",
            description="Verify migrated components exist and are functional"
        )
    
    def execute(self, base_path: str) -> ToolResponse:
        """Verify component migration"""
        try:
            base = Path(base_path)
            
            # Check core components
            required_files = [
                "core/agent.py",
                "core/state.py",
                "core/context.py",
                "core/tools.py",
                "core/__init__.py"
            ]
            
            missing = []
            present = []
            
            for file_path in required_files:
                full_path = base / file_path
                if full_path.exists():
                    present.append(str(file_path))
                else:
                    missing.append(str(file_path))
            
            # Check imports work
            can_import = True
            try:
                sys.path.insert(0, str(base))
                from core import BaseAgent, UnifiedState, ContextManager, Tool
                from core import ToolResponse as TR  # Avoid shadowing
            except ImportError as e:
                can_import = False
                import_error = str(e)
            else:
                import_error = None
            
            return ToolResponse(
                success=len(missing) == 0 and can_import,
                data={
                    "present": present,
                    "missing": missing,
                    "can_import": can_import,
                    "import_error": import_error,
                    "migration_complete": len(missing) == 0
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
                "base_path": {"type": "string"}
            },
            "required": ["base_path"]
        }


class ComponentMigrationAgent(BaseAgent):
    """
    Agent responsible for migrating existing base components.
    Handles Issue #002: Migrate Existing Base Components
    """
    
    def register_tools(self) -> List[Tool]:
        """Register migration tools"""
        return [
            FileMigrationTool(),
            ComponentVerificationTool()
        ]
    
    def execute_task(self, task: str) -> ToolResponse:
        """
        Execute component migration.
        Expected task: "migrate components" or "solve issue #002"
        """
        
        base_path = Path.home() / "Documents" / "GitHub" / "12-factor-agents"
        
        # First verify if migration is needed
        verify_tool = self.tools[1]  # ComponentVerificationTool
        verify_result = verify_tool.execute(base_path=str(base_path))
        
        if verify_result.success and verify_result.data["migration_complete"]:
            # Already migrated
            return ToolResponse(
                success=True,
                data={
                    "status": "already_migrated",
                    "components": verify_result.data["present"],
                    "message": "All components already present in core/",
                    "issue": "#002",
                    "status": "resolved"
                }
            )
        
        # Perform migration if needed
        migrate_tool = self.tools[0]  # FileMigrationTool
        results = []
        
        # Map of files to migrate
        migrations = [
            ("agents/base/agent.py", "core/agent.py"),
            ("agents/base/state.py", "core/state.py"),
            ("agents/base/context.py", "core/context.py"),
            ("agents/base/tools.py", "core/tools.py"),
            ("agents/base/__init__.py", "core/__init__.py")
        ]
        
        for source, destination in migrations:
            # Check if destination already exists
            dst_path = base_path / destination
            if dst_path.exists():
                results.append({
                    "file": destination,
                    "status": "already_exists",
                    "skipped": True
                })
                continue
            
            # Try to migrate
            result = migrate_tool.execute(
                source=source,
                destination=str(dst_path),
                operation="copy"
            )
            
            if result.success:
                results.append({
                    "file": destination,
                    "status": "migrated",
                    "from": source
                })
            else:
                results.append({
                    "file": destination,
                    "status": "failed",
                    "error": result.error
                })
        
        # Verify final state
        final_verify = verify_tool.execute(base_path=str(base_path))
        
        if final_verify.success:
            self.state.set("issue_002_status", "resolved")
            self.state.set("components_migrated", True)
            
            return ToolResponse(
                success=True,
                data={
                    "migrations": results,
                    "components_present": final_verify.data["present"],
                    "can_import": final_verify.data["can_import"],
                    "issue": "#002",
                    "status": "resolved"
                }
            )
        else:
            return ToolResponse(
                success=False,
                error="Migration completed but verification failed",
                data={
                    "migrations": results,
                    "verification": final_verify.data
                }
            )
    
    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply migration action"""
        action_type = action.get("type", "migrate")
        
        if action_type == "migrate":
            return self.execute_task(action.get("task", "migrate components"))
        elif action_type == "verify":
            base_path = Path.home() / "Documents" / "GitHub" / "12-factor-agents"
            verify_tool = self.tools[1]
            return verify_tool.execute(base_path=str(base_path))
        
        return ToolResponse(
            success=False,
            error=f"Unknown action type: {action_type}"
        )


# Self-test when run directly
# Usage: uv run agents/component_migration_agent.py
if __name__ == "__main__":
    print("Testing ComponentMigrationAgent...")
    agent = ComponentMigrationAgent()
    
    # First verify current state
    verify_result = agent._apply_action({"type": "verify"})
    print(f"Current state: {verify_result.data}")
    
    # Run migration
    result = agent.execute_task("migrate base components for issue #002")
    
    if result.success:
        print("✅ Component migration successful!")
        print(json.dumps(result.data, indent=2))
    else:
        print(f"❌ Migration failed: {result.error}")
        if hasattr(result, 'data'):
            print(json.dumps(result.data, indent=2))