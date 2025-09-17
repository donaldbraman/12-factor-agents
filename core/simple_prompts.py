#!/usr/bin/env python3
"""
Simple Prompt Management - Lightweight prompt handling using file system

Instead of complex prompt management frameworks, we use simple file-based
templates with Python's built-in string formatting.

This addresses Issue #003: Implement Prompt Management (Factor 2)
"""

from pathlib import Path
from typing import Dict, Optional
from string import Template


class SimplePromptManager:
    """
    Simple prompt manager using file system and Python's Template class.

    Key principles:
    - Prompts stored as simple text files
    - Use Python's built-in Template for variable substitution
    - No complex templating engines
    - Version control through git (not custom versioning)
    """

    def __init__(self, prompts_dir: Path = None):
        self.prompts_dir = prompts_dir or Path.cwd() / "prompts"
        self.prompts_dir.mkdir(exist_ok=True)
        self._cache: Dict[str, str] = {}

        # Create default directory structure
        self._ensure_directory_structure()

    def _ensure_directory_structure(self):
        """Create the basic prompt directory structure"""

        # Create subdirectories
        (self.prompts_dir / "base").mkdir(exist_ok=True)
        (self.prompts_dir / "agents").mkdir(exist_ok=True)
        (self.prompts_dir / "workflows").mkdir(exist_ok=True)

        # Create default prompts if they don't exist
        self._create_default_prompts()

    def _create_default_prompts(self):
        """Create default prompt templates"""

        default_prompts = {
            "base/system.prompt": """You are a helpful AI assistant working with the 12-factor-agents system.

Key principles:
- Use stateless functions, not complex classes
- Leverage existing tools instead of building custom solutions
- Work WITH Claude's nature (excellent context processing, no memory)
- Keep solutions simple and maintainable

Context: $context
Task: $task""",
            "base/error.prompt": """An error occurred during execution:

Error: $error_message
Context: $context
Task: $task

Please analyze the error and suggest a simple, reliable solution.""",
            "agents/issue_analyzer.prompt": """Analyze the following issue using natural language understanding:

Issue Title: $issue_title
Issue Body: $issue_body

Please identify:
1. The core problem being described
2. The desired outcome
3. Whether this is a bug fix, feature request, documentation, or refactoring
4. Key requirements (not examples)
5. Files or components mentioned

Focus on understanding the intent rather than literal text parsing.""",
            "agents/code_generator.prompt": """Generate code to solve the following issue:

Problem: $problem_statement  
Desired Outcome: $desired_outcome
Files to Modify: $files_to_modify

Requirements:
$requirements

Guidelines:
- Use simple, stateless functions
- Leverage existing tools and libraries
- Follow the existing code style
- Make minimal, focused changes
- Ensure code is testable and maintainable""",
            "workflows/issue_to_pr.prompt": """Execute the complete issue-to-PR workflow:

Issue Number: $issue_number
Issue Analysis: $issue_analysis

Steps to complete:
1. Analyze the issue context
2. Generate appropriate code changes
3. Validate the changes
4. Create a pull request

Use simple, composable functions for each step.""",
        }

        for prompt_path, content in default_prompts.items():
            full_path = self.prompts_dir / prompt_path
            if not full_path.exists():
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, "w") as f:
                    f.write(content.strip())

    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a prompt template from file.

        Args:
            prompt_name: Name like "base/system" or "agents/issue_analyzer"
        """

        # Check cache first
        if prompt_name in self._cache:
            return self._cache[prompt_name]

        # Add .prompt extension if not present
        if not prompt_name.endswith(".prompt"):
            prompt_name += ".prompt"

        prompt_path = self.prompts_dir / prompt_name

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")

        with open(prompt_path, "r") as f:
            content = f.read()

        # Cache for future use
        self._cache[prompt_name.replace(".prompt", "")] = content
        return content

    def format_prompt(self, prompt_name: str, **variables) -> str:
        """
        Load and format a prompt with variables.

        Args:
            prompt_name: Name of the prompt template
            **variables: Variables to substitute in the template
        """

        template_content = self.load_prompt(prompt_name)
        template = Template(template_content)

        try:
            return template.substitute(**variables)
        except KeyError as e:
            # Provide helpful error message for missing variables
            raise ValueError(f"Missing variable {e} for prompt '{prompt_name}'")

    def get_available_prompts(self) -> Dict[str, str]:
        """Get list of available prompts with their descriptions"""

        prompts = {}

        for prompt_file in self.prompts_dir.rglob("*.prompt"):
            # Get relative path from prompts_dir
            relative_path = prompt_file.relative_to(self.prompts_dir)
            prompt_name = str(relative_path).replace(".prompt", "")

            # Read first line as description
            try:
                with open(prompt_file, "r") as f:
                    first_line = f.readline().strip()
                    # Use first comment or first line as description
                    if first_line.startswith("#"):
                        description = first_line[1:].strip()
                    else:
                        description = (
                            first_line[:100] + "..."
                            if len(first_line) > 100
                            else first_line
                        )

                prompts[prompt_name] = description

            except Exception:
                prompts[prompt_name] = "No description available"

        return prompts

    def create_prompt(self, prompt_name: str, content: str, overwrite: bool = False):
        """
        Create a new prompt template.

        Args:
            prompt_name: Name for the prompt (e.g., "agents/my_agent")
            content: Template content
            overwrite: Whether to overwrite existing prompts
        """

        if not prompt_name.endswith(".prompt"):
            prompt_name += ".prompt"

        prompt_path = self.prompts_dir / prompt_name

        if prompt_path.exists() and not overwrite:
            raise FileExistsError(f"Prompt already exists: {prompt_path}")

        # Create directory if needed
        prompt_path.parent.mkdir(parents=True, exist_ok=True)

        with open(prompt_path, "w") as f:
            f.write(content)

        print(f"✅ Created prompt: {prompt_name}")

    def validate_prompt(self, prompt_name: str, **test_variables) -> bool:
        """
        Validate that a prompt can be formatted with given variables.

        Args:
            prompt_name: Name of the prompt to validate
            **test_variables: Test variables for validation
        """

        try:
            formatted = self.format_prompt(prompt_name, **test_variables)
            # Check that all variables were substituted
            if "$" in formatted:
                print(
                    f"⚠️ Warning: Prompt '{prompt_name}' may have unsubstituted variables"
                )
                return False
            return True

        except Exception as e:
            print(f"❌ Prompt validation failed for '{prompt_name}': {e}")
            return False


# Global prompt manager instance
_global_prompt_manager: Optional[SimplePromptManager] = None


def get_prompt_manager() -> SimplePromptManager:
    """Get the global prompt manager instance"""
    global _global_prompt_manager

    if _global_prompt_manager is None:
        _global_prompt_manager = SimplePromptManager()

    return _global_prompt_manager


def format_prompt(prompt_name: str, **variables) -> str:
    """
    Convenience function to format a prompt.

    Usage:
        prompt = format_prompt("agents/issue_analyzer",
                              issue_title="Fix bug",
                              issue_body="Something is broken")
    """
    return get_prompt_manager().format_prompt(prompt_name, **variables)


def create_agent_prompt(agent_name: str, prompt_content: str):
    """
    Create a prompt for a specific agent.

    Usage:
        create_agent_prompt("file_validator", '''
        Validate the following file for syntax errors:

        File: $file_path
        Content: $file_content
        ''')
    """
    prompt_name = f"agents/{agent_name}"
    get_prompt_manager().create_prompt(prompt_name, prompt_content)


# Example usage and validation
if __name__ == "__main__":
    print("🧪 Simple Prompt Management Demo")

    # Create prompt manager
    pm = SimplePromptManager()

    # Test loading and formatting prompts
    try:
        system_prompt = pm.format_prompt(
            "base/system",
            context="Testing prompt system",
            task="Validate prompt management",
        )

        print("✅ System prompt formatted successfully")
        print(f"Preview: {system_prompt[:100]}...")

    except Exception as e:
        print(f"❌ Error formatting system prompt: {e}")

    # Test issue analyzer prompt
    try:
        analyzer_prompt = pm.format_prompt(
            "agents/issue_analyzer",
            issue_title="Fix file destruction bug",
            issue_body="Agents are destroying files instead of editing them safely",
        )

        print("✅ Issue analyzer prompt formatted successfully")

    except Exception as e:
        print(f"❌ Error formatting analyzer prompt: {e}")

    # Show available prompts
    available = pm.get_available_prompts()
    print(f"\n📋 Available prompts: {len(available)}")
    for name, desc in available.items():
        print(f"   • {name}: {desc[:60]}...")

    print("\n✅ Simple prompt management ready!")
    print("   - File-based templates")
    print("   - Python Template substitution")
    print("   - No complex dependencies")
    print("   - Git-based versioning")
