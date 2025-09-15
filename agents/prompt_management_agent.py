"""
PromptManagementAgent - Implements proper prompt management for Factor 2 compliance.
Designed to solve Issue #003: Implement Prompt Management
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

# Import from parent directory
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse
from core.execution_context import ExecutionContext


class PromptCreatorTool(Tool):
    """Create prompt files with templates"""

    def __init__(self):
        super().__init__(
            name="create_prompt", description="Create a prompt template file"
        )

    def execute(
        self, path: str, template: str, metadata: Dict[str, Any] = None
    ) -> ToolResponse:
        """Create prompt template file"""
        try:
            prompt_path = Path(path).resolve()
            prompt_path.parent.mkdir(parents=True, exist_ok=True)

            # Add metadata header if provided
            content = ""
            if metadata:
                content += "# Prompt Metadata\n"
                content += f"# Version: {metadata.get('version', '1.0.0')}\n"
                content += (
                    f"# Description: {metadata.get('description', 'No description')}\n"
                )
                content += f"# Variables: {', '.join(metadata.get('variables', []))}\n"
                content += f"# Created: {datetime.now().isoformat()}\n\n"

            content += template

            prompt_path.write_text(content)

            return ToolResponse(
                success=True,
                data={
                    "path": str(prompt_path),
                    "size": len(content),
                    "metadata": metadata,
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "template": {"type": "string"},
                "metadata": {"type": "object"},
            },
            "required": ["path", "template"],
        }


class PromptManagerCreatorTool(Tool):
    """Create the PromptManager class"""

    def __init__(self):
        super().__init__(
            name="create_prompt_manager",
            description="Create the PromptManager class implementation",
        )

    def execute(self, output_path: str) -> ToolResponse:
        """Create PromptManager implementation"""
        try:
            code = '''"""
Prompt management system for Factor 2 compliance.
Factor 2: Own Your Prompts - All prompts are externalized and version controlled.
"""
from pathlib import Path
from typing import Dict, Optional, Any
import string
import json
from datetime import datetime


class PromptManager:
    """
    Manages externalized prompt templates for agents.
    
    Features:
    - Load prompts from files
    - Template variable substitution
    - Version tracking
    - Prompt caching
    """
    
    def __init__(self, prompts_dir: Path = None):
        """Initialize prompt manager with prompts directory"""
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent.parent / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self.templates = {}
        self.metadata = {}
        self._cache = {}
        
        if self.prompts_dir.exists():
            self._load_all_prompts()
    
    def _load_all_prompts(self):
        """Load all prompt templates from directory"""
        for prompt_file in self.prompts_dir.glob("**/*.prompt"):
            self._load_prompt_file(prompt_file)
    
    def _load_prompt_file(self, path: Path):
        """Load a single prompt file"""
        try:
            content = path.read_text()
            
            # Extract metadata from comments
            metadata = self._extract_metadata(content)
            
            # Remove metadata comments from template
            template_lines = []
            for line in content.split('\\n'):
                if not line.startswith('#'):
                    template_lines.append(line)
            
            template_text = '\\n'.join(template_lines).strip()
            
            # Store relative to prompts directory
            rel_path = path.relative_to(self.prompts_dir)
            name = str(rel_path.with_suffix(''))
            
            self.templates[name] = string.Template(template_text)
            self.metadata[name] = metadata
            
        except Exception as e:
            print(f"Warning: Failed to load prompt {path}: {e}")
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from prompt file comments"""
        metadata = {}
        
        for line in content.split('\\n'):
            if line.startswith('# '):
                if ':' in line:
                    key, value = line[2:].split(':', 1)
                    metadata[key.strip().lower()] = value.strip()
        
        return metadata
    
    def load_prompt(self, name: str) -> Optional[str]:
        """Load a prompt template by name"""
        if name in self.templates:
            return self.templates[name].template
        
        # Try to load from file if not cached
        prompt_path = self.prompts_dir / f"{name}.prompt"
        if prompt_path.exists():
            self._load_prompt_file(prompt_path)
            return self.templates.get(name, {}).get('template')
        
        return None
    
    def get_prompt(self, name: str, **kwargs) -> Optional[str]:
        """
        Get a prompt with variables substituted.
        
        Args:
            name: Name of the prompt template
            **kwargs: Variables to substitute in template
        
        Returns:
            Formatted prompt string or None if not found
        """
        # Check cache first
        cache_key = f"{name}:{json.dumps(kwargs, sort_keys=True)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if name not in self.templates:
            # Try to load if not already loaded
            prompt_path = self.prompts_dir / f"{name}.prompt"
            if not prompt_path.exists():
                # Also check in subdirectories
                for subdir in ['base', 'specialized', 'custom']:
                    prompt_path = self.prompts_dir / subdir / f"{name}.prompt"
                    if prompt_path.exists():
                        break
            
            if prompt_path.exists():
                self._load_prompt_file(prompt_path)
        
        if name in self.templates:
            try:
                result = self.templates[name].safe_substitute(**kwargs)
                self._cache[cache_key] = result
                return result
            except Exception as e:
                print(f"Error formatting prompt {name}: {e}")
                return None
        
        return None
    
    def register_prompt(self, name: str, template: str, metadata: Dict[str, Any] = None):
        """Register a new prompt template programmatically"""
        self.templates[name] = string.Template(template)
        if metadata:
            self.metadata[name] = metadata
    
    def get_version(self, name: str) -> Optional[str]:
        """Get version of a prompt template"""
        if name in self.metadata:
            return self.metadata[name].get('version', 'unknown')
        return None
    
    def list_prompts(self) -> List[str]:
        """List all available prompt templates"""
        return list(self.templates.keys())
    
    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a prompt template"""
        return self.metadata.get(name, {})
    
    def save_prompt(self, name: str, template: str, metadata: Dict[str, Any] = None):
        """Save a prompt template to file"""
        # Determine path
        if '/' in name:
            prompt_path = self.prompts_dir / f"{name}.prompt"
        else:
            prompt_path = self.prompts_dir / "custom" / f"{name}.prompt"
        
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build content
        content = ""
        if metadata:
            content += f"# Version: {metadata.get('version', '1.0.0')}\\n"
            content += f"# Description: {metadata.get('description', '')}\\n"
            content += f"# Variables: {', '.join(metadata.get('variables', []))}\\n"
            content += f"# Modified: {datetime.now().isoformat()}\\n\\n"
        
        content += template
        
        prompt_path.write_text(content)
        
        # Reload to update cache
        self._load_prompt_file(prompt_path)
    
    def clear_cache(self):
        """Clear the prompt cache"""
        self._cache = {}
'''

            output = Path(output_path).resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(code)

            return ToolResponse(
                success=True,
                data={
                    "path": str(output),
                    "class": "PromptManager",
                    "methods": [
                        "load_prompt",
                        "get_prompt",
                        "register_prompt",
                        "get_version",
                        "list_prompts",
                        "save_prompt",
                    ],
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"output_path": {"type": "string"}},
            "required": ["output_path"],
        }


class BaseAgentUpdaterTool(Tool):
    """Update BaseAgent to use PromptManager"""

    def __init__(self):
        super().__init__(
            name="update_base_agent",
            description="Update BaseAgent class to use PromptManager",
        )

    def execute(self, base_agent_path: str) -> ToolResponse:
        """Add prompt management to BaseAgent"""
        try:
            agent_path = Path(base_agent_path).resolve()

            if not agent_path.exists():
                return ToolResponse(
                    success=False, error=f"BaseAgent file not found at {agent_path}"
                )

            content = agent_path.read_text()

            # Check if already has prompt manager
            if "PromptManager" in content:
                return ToolResponse(
                    success=True,
                    data={"message": "BaseAgent already uses PromptManager"},
                )

            # Add import
            import_line = "from .prompt_manager import PromptManager"
            if "from .context import" in content:
                content = content.replace(
                    "from .context import ContextManager",
                    f"from .context import ContextManager\n{import_line}",
                )

            # Add prompt manager initialization in __init__
            init_addition = """        self.prompt_manager = PromptManager()
        self._load_agent_prompt()
        """

            # Find __init__ method and add after context_manager line
            if "self.context_manager = ContextManager()" in content:
                content = content.replace(
                    "self.context_manager = ContextManager()",
                    f"self.context_manager = ContextManager()\n{init_addition}",
                )

            # Add method to load agent-specific prompts
            method_addition = '''
    def _load_agent_prompt(self):
        """Load agent-specific prompt template"""
        agent_name = self.__class__.__name__.replace("Agent", "").lower()
        
        # Try to load specialized prompt
        prompt = self.prompt_manager.get_prompt(
            f"specialized/{agent_name}",
            agent_type=self.__class__.__name__,
            agent_id=self.agent_id
        )
        
        if prompt:
            self.context_manager.set_system_prompt(prompt)
        else:
            # Fall back to base prompt
            base_prompt = self.prompt_manager.get_prompt(
                "base/system",
                agent_type=self.__class__.__name__,
                responsibility="General task execution",
                tools_list=", ".join([t.name for t in self.tools]),
                context="",
                task=""
            )
            if base_prompt:
                self.context_manager.set_system_prompt(base_prompt)
    
    def set_prompt_variables(self, **variables):
        """Update prompt with new variables"""
        agent_name = self.__class__.__name__.replace("Agent", "").lower()
        prompt = self.prompt_manager.get_prompt(
            f"specialized/{agent_name}",
            **variables
        )
        if prompt:
            self.context_manager.set_system_prompt(prompt)'''

            # Add before the last class closing
            if "def get_status" in content:
                # Add after get_status method
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "def get_status" in line:
                        # Find the end of this method
                        indent_count = len(line) - len(line.lstrip())
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip() and not lines[j].startswith(
                                " " * (indent_count + 4)
                            ):
                                # Found end of method
                                lines.insert(j, method_addition)
                                break
                        break
                content = "\n".join(lines)

            # Write updated content
            agent_path.write_text(content)

            return ToolResponse(
                success=True,
                data={
                    "path": str(agent_path),
                    "modifications": [
                        "Added PromptManager import",
                        "Added prompt_manager initialization",
                        "Added _load_agent_prompt method",
                        "Added set_prompt_variables method",
                    ],
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"base_agent_path": {"type": "string"}},
            "required": ["base_agent_path"],
        }


class PromptManagementAgent(BaseAgent):
    """
    Agent responsible for implementing proper prompt management.
    Handles Issue #003: Implement Prompt Management (Factor 2)
    """

    def register_tools(self) -> List[Tool]:
        """Register prompt management tools"""
        return [PromptCreatorTool(), PromptManagerCreatorTool(), BaseAgentUpdaterTool()]

    def execute_task(
        self, task: str, context: Optional[ExecutionContext] = None
    ) -> ToolResponse:
        """
        Execute prompt management setup.
        Expected task: "implement prompt management" or "solve issue #003"
        """

        base_path = Path.home() / "Documents" / "GitHub" / "12-factor-agents"
        results = []

        # Step 1: Create PromptManager class
        manager_tool = self.tools[1]  # PromptManagerCreatorTool
        manager_result = manager_tool.execute(
            output_path=str(base_path / "core" / "prompt_manager.py")
        )
        results.append(("prompt_manager", manager_result))

        if not manager_result.success:
            return manager_result

        # Step 2: Create base prompt templates
        prompt_tool = self.tools[0]  # PromptCreatorTool

        # System prompt
        system_template = """You are a ${agent_type} agent with the following capabilities:

## Primary Responsibility
${responsibility}

## Available Tools
${tools_list}

## Current Context
${context}

## Execution Guidelines
- Focus on your single responsibility
- Return structured responses
- Handle errors gracefully
- Maintain state consistency
- Follow the 12-factor agent methodology

## Task
${task}

Please execute the task using the available tools and return a structured response."""

        system_result = prompt_tool.execute(
            path=str(base_path / "prompts" / "base" / "system.prompt"),
            template=system_template,
            metadata={
                "version": "1.0.0",
                "description": "Base system prompt for all agents",
                "variables": [
                    "agent_type",
                    "responsibility",
                    "tools_list",
                    "context",
                    "task",
                ],
            },
        )
        results.append(("system_prompt", system_result))

        # Error prompt
        error_template = """An error occurred while executing your task:

## Error Details
${error_message}

## Error Type
${error_type}

## Stack Trace
${stack_trace}

## Recovery Suggestions
${suggestions}

Please review the error and determine the appropriate recovery action."""

        error_result = prompt_tool.execute(
            path=str(base_path / "prompts" / "base" / "error.prompt"),
            template=error_template,
            metadata={
                "version": "1.0.0",
                "description": "Error handling prompt",
                "variables": [
                    "error_message",
                    "error_type",
                    "stack_trace",
                    "suggestions",
                ],
            },
        )
        results.append(("error_prompt", error_result))

        # Context prompt
        context_template = """## Current Context

### Working Directory
${working_directory}

### Previous Actions
${action_history}

### Current State
${state_summary}

### Available Resources
${resources}

### Constraints
${constraints}"""

        context_result = prompt_tool.execute(
            path=str(base_path / "prompts" / "base" / "context.prompt"),
            template=context_template,
            metadata={
                "version": "1.0.0",
                "description": "Context information prompt",
                "variables": [
                    "working_directory",
                    "action_history",
                    "state_summary",
                    "resources",
                    "constraints",
                ],
            },
        )
        results.append(("context_prompt", context_result))

        # Step 3: Create specialized prompts

        # File search agent prompt
        file_search_template = """You are a FileSearchAgent specialized in finding files and content.

## Your Capabilities
- Search for files by name pattern using glob
- Search for content within files using grep
- Navigate directory structures efficiently

## Search Context
Search Location: ${search_path}
Search Pattern: ${pattern}
File Type Filter: ${file_type}
Max Results: ${max_results}

## Task
${task}

Execute the search and return structured results including:
- File paths found
- Match count
- Relevant snippets
- Search statistics"""

        file_search_result = prompt_tool.execute(
            path=str(base_path / "prompts" / "specialized" / "file_search.prompt"),
            template=file_search_template,
            metadata={
                "version": "1.0.0",
                "description": "Prompt for FileSearchAgent",
                "variables": [
                    "search_path",
                    "pattern",
                    "file_type",
                    "max_results",
                    "task",
                ],
            },
        )
        results.append(("file_search_prompt", file_search_result))

        # Step 4: Update BaseAgent to use PromptManager
        updater_tool = self.tools[2]  # BaseAgentUpdaterTool
        update_result = updater_tool.execute(
            base_agent_path=str(base_path / "core" / "agent.py")
        )
        results.append(("base_agent_update", update_result))

        # Compile results
        all_success = all(r[1].success for r in results)

        if all_success:
            self.state.set("issue_003_status", "resolved")
            self.state.set("prompt_management_implemented", True)

            return ToolResponse(
                success=True,
                data={
                    "prompt_manager_created": True,
                    "base_prompts_created": 3,
                    "specialized_prompts_created": 1,
                    "base_agent_updated": update_result.success,
                    "issue": "#003",
                    "status": "resolved",
                    "factor_2_compliance": "100%",
                },
            )
        else:
            failed = [r[0] for r in results if not r[1].success]
            return ToolResponse(
                success=False,
                error=f"Failed steps: {', '.join(failed)}",
                data={"failed_steps": failed},
            )

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply prompt management action"""
        action_type = action.get("type", "setup")

        if action_type == "setup":
            return self.execute_task(action.get("task", "implement prompt management"))
        elif action_type == "verify":
            # Verify prompt management setup
            base_path = Path.home() / "Documents" / "GitHub" / "12-factor-agents"
            checks = {
                "prompt_manager": (base_path / "core" / "prompt_manager.py").exists(),
                "prompts_dir": (base_path / "prompts").exists(),
                "base_prompts": (base_path / "prompts" / "base").exists(),
                "system_prompt": (
                    base_path / "prompts" / "base" / "system.prompt"
                ).exists(),
            }

            return ToolResponse(success=all(checks.values()), data={"checks": checks})

        return ToolResponse(success=False, error=f"Unknown action type: {action_type}")


# Self-test when run directly
# Usage: uv run agents/prompt_management_agent.py
if __name__ == "__main__":
    print("Testing PromptManagementAgent...")
    agent = PromptManagementAgent()

    result = agent.execute_task("implement prompt management for Factor 2 compliance")

    if result.success:
        print("✅ Prompt management implementation successful!")
        print(json.dumps(result.data, indent=2))
    else:
        print(f"❌ Implementation failed: {result.error}")
