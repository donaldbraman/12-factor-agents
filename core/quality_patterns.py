#!/usr/bin/env python3
"""
Quality Pattern Management System

Central system for managing quality patterns that all agents use.
No hardcoding - everything comes from the pattern database.
Patterns evolve based on feedback and learning.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Singleton pattern manager instance
_pattern_manager_instance = None


class PatternType(Enum):
    """Types of patterns we track"""

    AVOID = "avoid_patterns"
    FOLLOW = "follow_patterns"
    CONTEXT = "context_patterns"
    LEARNED = "learned_patterns"


@dataclass
class PatternMatch:
    """Represents a pattern match in code"""

    pattern_type: PatternType
    pattern_name: str
    location: str
    description: str
    suggestion: str
    severity: str = "medium"


@dataclass
class LearnedPattern:
    """A pattern learned from experience"""

    date: str
    pattern: str
    learned_from: str
    action: str
    success_rate: float = 0.0
    usage_count: int = 0


class QualityPatternManager:
    """
    Centralized manager for quality patterns.
    All agents use this instead of hardcoding patterns.
    """

    def __init__(self, pattern_file: Optional[str] = None):
        """Initialize with pattern database"""
        self.pattern_file = Path(pattern_file or "prompts/quality_patterns.yaml")
        self.patterns = self._load_patterns()
        self._cache = {}  # Cache compiled patterns
        self._learning_enabled = True

    def _load_patterns(self) -> Dict:
        """Load patterns from YAML database"""
        if not self.pattern_file.exists():
            # Return minimal default patterns if file doesn't exist
            return {
                "avoid_patterns": {},
                "follow_patterns": {},
                "context_patterns": {},
                "learned_patterns": [],
            }

        with open(self.pattern_file, "r") as f:
            return yaml.safe_load(f)

    def reload_patterns(self):
        """Reload patterns from disk (for hot updates)"""
        self.patterns = self._load_patterns()
        self._cache.clear()
        print(f"🔄 Reloaded patterns from {self.pattern_file}")

    def get_avoid_patterns(self) -> Dict:
        """Get patterns to avoid"""
        return self.patterns.get("avoid_patterns", {})

    def get_follow_patterns(self) -> Dict:
        """Get patterns to follow"""
        return self.patterns.get("follow_patterns", {})

    def get_context_patterns(self) -> Dict:
        """Get context-specific patterns"""
        return self.patterns.get("context_patterns", {})

    def get_learned_patterns(self) -> List[Dict]:
        """Get patterns learned from experience"""
        return self.patterns.get("learned_patterns", [])

    def get_prompt_template(self, prompt_type: str) -> str:
        """Get a prompt template for generation"""
        prompts = self.patterns.get("generation_prompts", {})
        return prompts.get(prompt_type, "")

    def check_code_quality(self, code: str, filename: str = "") -> List[PatternMatch]:
        """
        Check code against all patterns.
        Returns list of pattern matches (issues found).
        """
        matches = []

        # Check avoid patterns
        for category_name, category in self.get_avoid_patterns().items():
            if "examples" in category:
                for example in category["examples"]:
                    if example["pattern"] in code:
                        matches.append(
                            PatternMatch(
                                pattern_type=PatternType.AVOID,
                                pattern_name=category_name,
                                location=f"Pattern '{example['pattern']}'",
                                description=example.get("context", "Pattern found"),
                                suggestion=example.get("better", "Improve this"),
                                severity="high"
                                if "TODO" in example["pattern"]
                                else "medium",
                            )
                        )

        # Check file placement if filename provided
        if filename:
            matches.extend(self._check_file_placement(filename))

        # Check against learned patterns
        for learned in self.get_learned_patterns():
            if self._pattern_applies(code, learned["pattern"]):
                matches.append(
                    PatternMatch(
                        pattern_type=PatternType.LEARNED,
                        pattern_name="learned_pattern",
                        location=learned["pattern"],
                        description=learned["learned_from"],
                        suggestion=learned["action"],
                        severity="medium",
                    )
                )

        return matches

    def _check_file_placement(self, filename: str) -> List[PatternMatch]:
        """Check if file is in correct location"""
        matches = []
        file_patterns = self.get_context_patterns().get("file_placement", {})

        if "rules" in file_patterns:
            for rule in file_patterns["rules"]:
                if self._filename_matches_pattern(filename, rule["pattern"]):
                    if rule["location"] not in filename:
                        matches.append(
                            PatternMatch(
                                pattern_type=PatternType.CONTEXT,
                                pattern_name="file_placement",
                                location=filename,
                                description=f"File should be in {rule['location']}",
                                suggestion=f"Move to {rule['location']}",
                                severity="high",
                            )
                        )

        return matches

    def _filename_matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches a pattern"""
        import fnmatch

        return fnmatch.fnmatch(Path(filename).name, pattern)

    def _pattern_applies(self, code: str, pattern_description: str) -> bool:
        """Check if a learned pattern applies to code"""
        # Simple keyword matching for now
        keywords = pattern_description.lower().split()
        code_lower = code.lower()

        matches = sum(1 for keyword in keywords if keyword in code_lower)
        return matches >= len(keywords) * 0.5  # Match if 50% of keywords present

    def get_generation_guidelines(self, task_type: str) -> Dict[str, Any]:
        """
        Get all guidelines for generating code of a specific type.
        This is what agents should use instead of hardcoded rules.
        """
        guidelines = {
            "must_follow": [],
            "must_avoid": [],
            "examples": [],
            "templates": {},
        }

        # Add patterns to follow
        for pattern_name, pattern_data in self.get_follow_patterns().items():
            if "guidelines" in pattern_data:
                guidelines["must_follow"].extend(pattern_data["guidelines"])
            if "template" in pattern_data:
                guidelines["templates"][pattern_name] = pattern_data["template"]

        # Add patterns to avoid
        for pattern_name, pattern_data in self.get_avoid_patterns().items():
            if "description" in pattern_data:
                guidelines["must_avoid"].append(pattern_data["description"])

        # Add specific prompt template
        if task_type in self.patterns.get("generation_prompts", {}):
            guidelines["prompt"] = self.patterns["generation_prompts"][task_type]

        # Add learned insights
        for learned in self.get_learned_patterns():
            if learned.get("success_rate", 0) > 0.7:  # Only include successful patterns
                guidelines["must_follow"].append(learned["action"])

        return guidelines

    def add_learned_pattern(self, pattern: str, learned_from: str, action: str):
        """
        Add a new learned pattern based on review feedback.
        This is how the system improves over time.
        """
        if not self._learning_enabled:
            return

        new_pattern = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "pattern": pattern,
            "learned_from": learned_from,
            "action": action,
            "success_rate": 0.0,
            "usage_count": 0,
        }

        # Add to patterns
        if "learned_patterns" not in self.patterns:
            self.patterns["learned_patterns"] = []

        self.patterns["learned_patterns"].append(new_pattern)

        # Save to file
        self._save_patterns()

        print(f"📚 Learned new pattern: {pattern}")

    def update_pattern_success(self, pattern: str, success: bool):
        """Update success rate of a pattern based on usage"""
        for learned in self.patterns.get("learned_patterns", []):
            if learned["pattern"] == pattern:
                learned["usage_count"] += 1
                # Update success rate with moving average
                current_rate = learned.get("success_rate", 0.0)
                new_rate = (
                    current_rate * (learned["usage_count"] - 1)
                    + (1.0 if success else 0.0)
                ) / learned["usage_count"]
                learned["success_rate"] = new_rate

                self._save_patterns()
                break

    def _save_patterns(self):
        """Save patterns back to YAML file"""
        try:
            with open(self.pattern_file, "w") as f:
                yaml.safe_dump(
                    self.patterns, f, default_flow_style=False, sort_keys=False
                )
        except Exception as e:
            print(f"⚠️ Could not save patterns: {e}")

    def get_quality_checklist(self) -> List[str]:
        """
        Get a checklist for quality review.
        Used by review agents.
        """
        checklist = []

        # From avoid patterns
        for category in self.get_avoid_patterns().values():
            checklist.append(f"No {category.get('description', 'issues')}")

        # From follow patterns
        for category in self.get_follow_patterns().values():
            checklist.append(category.get("description", "Follow best practices"))

        # From metrics
        for metric in self.patterns.get("quality_metrics", []):
            checklist.append(f"{metric['name']}: {metric['target']}")

        return checklist

    def generate_review_criteria(self) -> Dict[str, List[str]]:
        """
        Generate review criteria from patterns.
        This is what review agents use to evaluate code.
        """
        criteria = {"critical": [], "major": [], "minor": []}

        # Critical issues from avoid patterns
        for pattern_name, pattern_data in self.get_avoid_patterns().items():
            if "placeholder" in pattern_name or "empty" in pattern_name:
                criteria["critical"].append(
                    pattern_data.get("description", pattern_name)
                )
            elif "error_handling" in pattern_name:
                criteria["major"].append(pattern_data.get("description", pattern_name))
            else:
                criteria["minor"].append(pattern_data.get("description", pattern_name))

        return criteria


def get_pattern_manager() -> QualityPatternManager:
    """
    Get the singleton pattern manager instance.
    All agents should use this instead of creating their own.
    """
    global _pattern_manager_instance

    if _pattern_manager_instance is None:
        _pattern_manager_instance = QualityPatternManager()

    return _pattern_manager_instance


def reload_patterns():
    """Force reload of patterns from disk"""
    manager = get_pattern_manager()
    manager.reload_patterns()


# Example usage for agents
class PatternAwareAgent:
    """Example of how agents should use the pattern system"""

    def __init__(self):
        # Use the central pattern manager
        self.patterns = get_pattern_manager()

    def generate_code(self, task: str) -> str:
        """Generate code using patterns from database"""
        # Get guidelines from pattern database
        guidelines = self.patterns.get_generation_guidelines("code_implementation")

        # Use the prompt template
        prompt = guidelines.get("prompt", "").format(feature=task)

        # Generate code following the guidelines
        code = self._generate_with_guidelines(prompt, guidelines)

        # Check quality before returning
        issues = self.patterns.check_code_quality(code)

        if issues:
            # Fix issues based on patterns
            code = self._fix_issues(code, issues)

        return code

    def _generate_with_guidelines(self, prompt: str, guidelines: Dict) -> str:
        """Generate following guidelines"""
        # Implementation would use guidelines["must_follow"]
        # and avoid guidelines["must_avoid"]
        return "# Generated code following patterns"

    def _fix_issues(self, code: str, issues: List[PatternMatch]) -> str:
        """Fix issues found in code"""
        for issue in issues:
            # Apply fixes based on issue suggestions
            pass
        return code


if __name__ == "__main__":
    # Demo the pattern system
    manager = get_pattern_manager()

    print("📊 Quality Pattern System")
    print(f"   Avoid patterns: {len(manager.get_avoid_patterns())}")
    print(f"   Follow patterns: {len(manager.get_follow_patterns())}")
    print(f"   Learned patterns: {len(manager.get_learned_patterns())}")

    # Test code checking
    test_code = """
    def process():
        # Implementation completed
        pass
    
    def test_something():
        self.assertTrue(True)  # placeholder
    """

    issues = manager.check_code_quality(test_code)
    print(f"\n🔍 Found {len(issues)} issues in test code:")
    for issue in issues:
        print(f"   - {issue.pattern_name}: {issue.description}")
        print(f"     Suggestion: {issue.suggestion}")

    # Show guidelines for generation
    guidelines = manager.get_generation_guidelines("test_generation")
    print("\n📋 Generation Guidelines:")
    print(f"   Must follow: {len(guidelines['must_follow'])} rules")
    print(f"   Must avoid: {len(guidelines['must_avoid'])} patterns")
