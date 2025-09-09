"""
Prompt management system for Factor 2 compliance.
Factor 2: Own Your Prompts - All prompts are externalized and version controlled.
"""
from pathlib import Path
from typing import Dict, Optional, Any, List
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
            for line in content.split("\n"):
                if not line.startswith("#"):
                    template_lines.append(line)

            template_text = "\n".join(template_lines).strip()

            # Store relative to prompts directory
            rel_path = path.relative_to(self.prompts_dir)
            name = str(rel_path.with_suffix(""))

            self.templates[name] = string.Template(template_text)
            self.metadata[name] = metadata

        except Exception as e:
            print(f"Warning: Failed to load prompt {path}: {e}")

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from prompt file comments"""
        metadata = {}

        for line in content.split("\n"):
            if line.startswith("# "):
                if ":" in line:
                    key, value = line[2:].split(":", 1)
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
            return self.templates.get(name, {}).get("template")

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
                for subdir in ["base", "specialized", "custom"]:
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

    def register_prompt(
        self, name: str, template: str, metadata: Dict[str, Any] = None
    ):
        """Register a new prompt template programmatically"""
        self.templates[name] = string.Template(template)
        if metadata:
            self.metadata[name] = metadata

    def get_version(self, name: str) -> Optional[str]:
        """Get version of a prompt template"""
        if name in self.metadata:
            return self.metadata[name].get("version", "unknown")
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
        if "/" in name:
            prompt_path = self.prompts_dir / f"{name}.prompt"
        else:
            prompt_path = self.prompts_dir / "custom" / f"{name}.prompt"

        prompt_path.parent.mkdir(parents=True, exist_ok=True)

        # Build content
        content = ""
        if metadata:
            content += f"# Version: {metadata.get('version', '1.0.0')}\n"
            content += f"# Description: {metadata.get('description', '')}\n"
            content += f"# Variables: {', '.join(metadata.get('variables', []))}\n"
            content += f"# Modified: {datetime.now().isoformat()}\n\n"

        content += template

        prompt_path.write_text(content)

        # Reload to update cache
        self._load_prompt_file(prompt_path)

    def clear_cache(self):
        """Clear the prompt cache"""
        self._cache = {}
