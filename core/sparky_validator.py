#!/usr/bin/env python3
"""
Sparky Self-Validation System - Quality-First Protection for Our Precious Codebase

This validator ensures Sparky's output meets our quality standards.
Our code is precious - every line matters.

Implementation of issue #030: Sparky Testing Enhancement
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a validation check."""

    passed: bool
    message: str
    quality_score: float
    fix_instructions: str = ""


class SparkySelfValidator:
    """
    Quality-first validation of Sparky's output.
    Protects our precious codebase from common failure patterns.

    Key principle: Quality over speed. Our code is precious!
    """

    def __init__(self):
        """Initialize the validator with quality-first settings."""
        self.max_iterations = 3  # Will retry up to 3 times to get it right
        self.quality_threshold = 0.95  # Must pass 95% of checks

        # Critical files that must never be damaged
        self.critical_files = [
            "collections_setup.py",
            "config.py",
            "settings.py",
            "core/__init__.py",
            "setup.py",
            "pyproject.toml",
        ]

    def validate_implementation(
        self, implementation: Dict[str, Any], issue: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main validation entry point with quality-first approach and retry mechanism.

        Args:
            implementation: Dict containing implementation details
            issue: Dict with issue information (number, title, body)

        Returns:
            Dict with validation results including success, quality_score, iterations
        """
        for iteration in range(1, self.max_iterations + 1):
            # Run all validation checks
            validation_results = [
                self._check_file_protection(implementation),
                self._check_naming_conventions(implementation),
                self._check_no_placeholders(implementation),
                self._check_method_signatures(implementation),
                self._check_basic_functionality(implementation),
            ]

            # Calculate quality score
            total_score = sum(r.quality_score for r in validation_results)
            quality_score = total_score / len(validation_results)

            # Check if we pass threshold
            all_passed = all(r.passed for r in validation_results)
            success = all_passed and quality_score >= self.quality_threshold

            if success:
                return {
                    "success": True,
                    "quality_score": quality_score,
                    "iterations": iteration,
                    "validation_results": validation_results,
                }

            # If not the last iteration, try to fix
            if iteration < self.max_iterations:
                implementation = self.fix_implementation(
                    implementation, validation_results
                )

        # Failed after all iterations
        return {
            "success": False,
            "quality_score": quality_score,
            "iterations": self.max_iterations,
            "validation_errors": self._extract_errors(validation_results),
            "validation_results": validation_results,
        }

    def _check_file_protection(self, implementation: Dict) -> ValidationResult:
        """Ensure critical files weren't overwritten or damaged."""
        files_modified = implementation.get("files_modified", []) or []

        for file in files_modified:
            for critical in self.critical_files:
                if critical in file:
                    return ValidationResult(
                        passed=False,
                        message=f"Critical file modified: {file}",
                        quality_score=0.0,
                        fix_instructions=f"Do not modify {critical} - it's a critical system file",
                    )

        return ValidationResult(
            passed=True, message="File protection check passed", quality_score=1.0
        )

    def _check_naming_conventions(self, implementation: Dict) -> ValidationResult:
        """Verify proper CamelCase naming - catches Sparky's biggest weakness."""
        class_names = implementation.get("class_names", []) or []
        if not class_names:
            return ValidationResult(
                passed=True, message="No classes to check", quality_score=1.0
            )

        bad_names = []
        for name in class_names:
            # Check if it's all lowercase (Sparky's signature mistake)
            if name.islower() and len(name) > 10:
                bad_names.append(name)
            # Check for missing CamelCase
            elif not re.search(r"[a-z][A-Z]", name) and len(name) > 5:
                bad_names.append(name)

        if bad_names:
            fixed_names = [self._fix_camel_case(name) for name in bad_names]
            return ValidationResult(
                passed=False,
                message=f"Bad naming: {', '.join(bad_names)}",
                quality_score=1.0 - (len(bad_names) / len(class_names)),
                fix_instructions=f"Fix names: {', '.join(f'{b} -> {f}' for b, f in zip(bad_names, fixed_names))}",
            )

        return ValidationResult(
            passed=True, message="All names follow conventions", quality_score=1.0
        )

    def _check_no_placeholders(self, implementation: Dict) -> ValidationResult:
        """Ensure no placeholder implementations - our code deserves real logic."""
        code_content = implementation.get("code_content", "") or ""

        issues = []
        if "TODO" in code_content:
            issues.append("TODO comments")
        if "NotImplementedError" in code_content:
            issues.append("NotImplementedError")
        if "Unknown Feature" in code_content:
            issues.append("Unknown Feature placeholder")

        # Check for excessive pass statements
        pass_count = len(re.findall(r"^\s+pass\s*$", code_content, re.MULTILINE))
        if pass_count > 2:
            issues.append(f"{pass_count} pass statements")

        if issues:
            return ValidationResult(
                passed=False,
                message=f"Found placeholders: {', '.join(issues)}",
                quality_score=max(0, 1.0 - (len(issues) * 0.25)),
                fix_instructions="Replace all placeholders with real implementation",
            )

        return ValidationResult(
            passed=True, message="No placeholders found", quality_score=1.0
        )

    def _check_method_signatures(self, implementation: Dict) -> ValidationResult:
        """Verify method signatures are meaningful and complete."""
        methods = implementation.get("methods", [])
        if not methods:
            return ValidationResult(
                passed=True, message="No methods to check", quality_score=1.0
            )

        issues = []
        for method in methods:
            method_name = method.get("name", "")

            # Check for minimal signatures (except __init__)
            if not method.get("params") or len(method.get("params", [])) == 0:
                if method_name != "__init__":
                    issues.append(f"{method_name} has no parameters")

            # Check for missing docstrings
            if not method.get("has_docstring"):
                issues.append(f"{method_name}: Missing docstring")

        if issues:
            quality = max(0, 1.0 - (len(issues) / len(methods)))
            return ValidationResult(
                passed=False,
                message=f"Method issues: {'; '.join(issues[:3])}",
                quality_score=quality,
                fix_instructions="Add parameters and docstrings to all methods",
            )

        return ValidationResult(
            passed=True, message="Method signatures look good", quality_score=1.0
        )

    def _check_basic_functionality(self, implementation: Dict) -> ValidationResult:
        """Check if basic functionality is present."""
        checks = {
            "has_tests": implementation.get("has_tests", False),
            "has_error_handling": implementation.get("has_error_handling", False),
            "has_logging": implementation.get("has_logging", False),
            "has_type_hints": implementation.get("has_type_hints", False),
        }

        missing = [k for k, v in checks.items() if not v]

        if missing:
            quality = 1.0 - (len(missing) * 0.25)
            readable_missing = [
                m.replace("has_", "").replace("_", " ") for m in missing
            ]
            return ValidationResult(
                passed=False,
                message=f"Missing {', '.join(readable_missing)}",
                quality_score=max(0, quality),
                fix_instructions=f"Add {', '.join(readable_missing)}",
            )

        return ValidationResult(
            passed=True, message="All basic functionality present", quality_score=1.0
        )

    def _fix_camel_case(self, name: str) -> str:
        """Convert Sparky's bad naming to proper CamelCase."""
        # Handle common Sparky patterns we've seen
        if name.lower() == "backgroundexecutor":
            return "BackgroundExecutor"
        if "sentenceboundary" in name.lower():
            return "SentenceBoundaryChunker"
        if name.lower() == "testrunner":
            return "TestRunner"
        if name.lower() == "apiclient":
            return "APIClient"
        if name.lower() == "xmlparser":
            return "XMLParser"

        # Generic fix for all-lowercase names
        if name.islower():
            # Common word patterns for splitting
            words = []
            patterns = [
                "background",
                "executor",
                "sentence",
                "boundary",
                "chunking",
                "impl",
                "test",
                "runner",
                "api",
                "client",
                "xml",
                "parser",
                "handler",
                "manager",
                "processor",
                "analyzer",
                "validator",
                "service",
            ]

            remaining = name.lower()
            while remaining:
                found = False
                for pattern in patterns:
                    if remaining.startswith(pattern):
                        words.append(pattern.capitalize())
                        remaining = remaining[len(pattern) :]
                        found = True
                        break

                if not found:
                    # Capitalize what's left
                    words.append(remaining.capitalize())
                    break

            return "".join(words)

        # Already has some capitals, just ensure first is capital
        return name[0].upper() + name[1:] if name else name

    def fix_implementation(
        self, implementation: Dict, validation_results: List[ValidationResult]
    ) -> Dict:
        """Attempt to fix implementation based on validation results."""
        # In a real scenario, this would trigger Sparky to regenerate
        # For testing, we'll just return the implementation as-is
        return implementation

    def _extract_errors(self, validation_results: List[ValidationResult]) -> List[str]:
        """Extract error messages from validation results."""
        errors = []
        for result in validation_results:
            if not result.passed:
                errors.append(result.message)
                if result.fix_instructions:
                    errors.append(f"Fix: {result.fix_instructions}")
        return errors


# Self-test when run directly
if __name__ == "__main__":
    print("🧪 Testing SparkySelfValidator...")

    # Test with typical Sparky mistakes
    test_implementation = {
        "files_modified": ["src/chunker.py"],
        "files_created": ["tests/test_chunker.py"],
        "class_names": ["sentenceboundarychunker"],  # Bad naming!
        "method_names": ["execute"],
        "code_content": """
class sentenceboundarychunker:
    def execute(self):
        # TODO: implement this
        pass
""",
        "methods": [{"name": "execute", "params": [], "has_docstring": False}],
        "has_tests": False,
        "has_error_handling": False,
        "has_logging": False,
        "has_type_hints": False,
    }

    validator = SparkySelfValidator()
    result = validator.validate_implementation(
        test_implementation, {"number": 999, "title": "Test Issue"}
    )

    print(f"\n📊 Validation {'PASSED ✅' if result['success'] else 'FAILED ❌'}")
    print(f"Quality Score: {result['quality_score']:.2%}")
    print(f"Iterations: {result['iterations']}")

    if not result["success"]:
        print("\nValidation Errors:")
        for error in result.get("validation_errors", []):
            print(f"  ❌ {error}")

    print("\n✨ SparkySelfValidator is ready to protect our precious code!")
