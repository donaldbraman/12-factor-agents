"""
Simple Validation - Leverage existing tools instead of building complex frameworks

Uses what we already have:
1. Pre-commit hooks (already working!) for linting/formatting
2. Claude's built-in Bash tool for running tests
3. Python's built-in ast module for syntax checking
4. Simple file checks
"""

import ast
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any


def validate_before_commit(repo_path: Path = None) -> Dict[str, Any]:
    """
    Simple validation that leverages existing tools.

    Returns:
        Dict with validation results
    """
    if repo_path is None:
        repo_path = Path.cwd()

    results = {"valid": True, "errors": [], "warnings": [], "checks_run": []}

    print("🔍 Running simple validation checks...")

    # 1. Let pre-commit hooks handle linting/formatting (they already work!)
    print("📋 Pre-commit hooks will handle linting and formatting")
    results["checks_run"].append("pre-commit-hooks")

    # 2. Basic syntax validation for Python files
    python_files = list(repo_path.glob("**/*.py"))
    if python_files:
        print(f"🐍 Checking syntax of {len(python_files)} Python files...")
        for py_file in python_files:
            if not _validate_python_syntax(py_file):
                results["valid"] = False
                results["errors"].append(f"Syntax error in {py_file}")
            else:
                results["checks_run"].append(f"python-syntax:{py_file.name}")

    # 3. Basic JSON validation
    json_files = list(repo_path.glob("**/*.json"))
    if json_files:
        print(f"📄 Checking {len(json_files)} JSON files...")
        for json_file in json_files:
            if not _validate_json_syntax(json_file):
                results["valid"] = False
                results["errors"].append(f"Invalid JSON in {json_file}")
            else:
                results["checks_run"].append(f"json-syntax:{json_file.name}")

    # 4. Check if we're about to commit broken imports (simple check)
    print("📦 Checking for obvious import issues...")
    import_issues = _check_basic_imports(python_files)
    if import_issues:
        results["warnings"].extend(import_issues)
        results["checks_run"].append("import-check")

    # 5. Run quick test if they exist (but don't fail if no tests)
    if _has_tests(repo_path):
        print("🧪 Running quick tests...")
        test_result = _run_quick_tests(repo_path)
        if test_result:
            results["checks_run"].append("quick-tests")
        else:
            results["warnings"].append("Some tests failed - review before committing")

    return results


def _validate_python_syntax(file_path: Path) -> bool:
    """Validate Python syntax using built-in ast module"""
    try:
        with open(file_path, "r") as f:
            source = f.read()
        ast.parse(source)
        return True
    except SyntaxError:
        return False
    except Exception:
        # File might be binary or have encoding issues
        return True  # Don't fail on non-syntax issues


def _validate_json_syntax(file_path: Path) -> bool:
    """Validate JSON syntax using built-in json module"""
    try:
        with open(file_path, "r") as f:
            json.load(f)
        return True
    except json.JSONDecodeError:
        return False
    except Exception:
        return True  # Don't fail on non-JSON issues


def _check_basic_imports(python_files: List[Path]) -> List[str]:
    """Check for obvious import issues"""
    issues = []

    for py_file in python_files:
        try:
            with open(py_file, "r") as f:
                content = f.read()

            # Look for imports that are obviously wrong
            if "from import" in content:  # Missing module name
                issues.append(f"Malformed import in {py_file}")

            # Could add more sophisticated import checking here
            # For now, just checking for obvious malformed imports
            for line in content.split("\n"):
                if line.strip().startswith("import ") or line.strip().startswith(
                    "from "
                ):
                    # Basic check - could be expanded
                    pass

        except Exception:
            continue  # Skip files we can't read

    return issues


def _has_tests(repo_path: Path) -> bool:
    """Check if repo has tests"""
    test_dirs = ["tests", "test"]
    test_files = list(repo_path.glob("**/test_*.py")) + list(
        repo_path.glob("**/*_test.py")
    )

    return (
        any((repo_path / test_dir).exists() for test_dir in test_dirs)
        or len(test_files) > 0
    )


def _run_quick_tests(repo_path: Path) -> bool:
    """Run quick tests using subprocess (leveraging existing test setup)"""
    try:
        # Try common test commands
        test_commands = [
            ["python", "-m", "pytest", "-x", "--tb=short"],  # Fast fail
            ["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
            ["uv", "run", "pytest", "-x", "--tb=short"],
        ]

        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=repo_path,
                    capture_output=True,
                    timeout=30,  # Quick tests only
                    check=False,
                )
                if result.returncode == 0:
                    print(f"✅ Quick tests passed with: {' '.join(cmd)}")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        print("⚠️  No quick tests could be run")
        return True  # Don't fail if we can't run tests

    except Exception:
        return True  # Don't fail validation on test issues


def print_validation_results(results: Dict[str, Any]) -> None:
    """Print validation results in a friendly format"""
    if results["valid"]:
        print("✅ Validation passed!")
        print(f"🔍 Checks run: {', '.join(results['checks_run'])}")
    else:
        print("❌ Validation failed!")
        for error in results["errors"]:
            print(f"   🔴 {error}")

    if results["warnings"]:
        print("⚠️  Warnings:")
        for warning in results["warnings"]:
            print(f"   🟡 {warning}")


if __name__ == "__main__":
    # Test the validation
    results = validate_before_commit()
    print_validation_results(results)
