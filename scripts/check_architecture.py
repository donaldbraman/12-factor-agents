#!/usr/bin/env python3
"""Validate repository architecture compliance."""

import sys
from pathlib import Path


def check_architecture():
    """Validate overall repository structure."""
    violations = []

    # Check for Python files in root (excluding allowed ones)
    allowed_root_files = {"setup.py"}
    root_py = [f for f in Path(".").glob("*.py") if f.is_file()]
    for file in root_py:
        if file.name not in allowed_root_files:
            violations.append(
                f"Python file in root: {file.name} (move to appropriate directory)"
            )

    # Check for required directories
    required_dirs = {
        "agents": "Agent implementations",
        "core": "Core framework components",
        "tests": "Test files",
        "scripts": "Utility scripts",
        "docs": "Documentation",
    }

    for dir_name, purpose in required_dirs.items():
        if not Path(dir_name).exists():
            violations.append(f"Missing required directory: {dir_name}/ ({purpose})")

    # Check for build artifacts that shouldn't be committed
    artifacts_patterns = [
        ("*.egg-info", "Python build artifact"),
        ("__pycache__", "Python cache"),
        ("*.pyc", "Python compiled file"),
        ("*.pyo", "Python optimized file"),
        (".coverage", "Coverage report"),
        ("htmlcov", "HTML coverage report"),
        ("dist", "Distribution directory"),
        ("build", "Build directory"),
        ("*.log", "Log file"),
        (".DS_Store", "macOS metadata"),
        ("Thumbs.db", "Windows metadata"),
        ("token.json", "Token file - should use .env"),
    ]

    for pattern, description in artifacts_patterns:
        found_files = list(Path(".").rglob(pattern))
        if found_files:
            # Exclude .venv and similar directories
            found_files = [
                f
                for f in found_files
                if ".venv" not in str(f)
                and "venv" not in str(f)
                and "site-packages" not in str(f)
            ]
            if found_files:
                violations.append(
                    f"{description} found: {pattern} ({len(found_files)} file(s))"
                )

    # Check for test files outside tests directory
    test_files_outside = []
    for py_file in Path(".").rglob("*.py"):
        if ".venv" not in str(py_file) and "venv" not in str(py_file):
            if py_file.name.startswith("test_") or py_file.name.endswith("_test.py"):
                if "tests" not in str(py_file.parent):
                    test_files_outside.append(str(py_file))

    if test_files_outside:
        violations.append(
            f"Test files outside tests/: {', '.join(test_files_outside[:3])}"
        )

    # Check for common security files that shouldn't be committed
    security_files = [".env", "credentials.json", "secrets.yaml", "*.pem", "*.key"]
    for pattern in security_files:
        found = list(Path(".").rglob(pattern))
        # .env.example is OK, and exclude virtual environments
        found = [
            f
            for f in found
            if not str(f).endswith(".example")
            and not str(f).endswith(".sample")
            and ".venv" not in str(f)
            and "venv" not in str(f)
            and "site-packages" not in str(f)
        ]
        if found:
            violations.append(
                f"Security file found: {pattern} - use .env.example pattern instead"
            )

    # Report violations
    if violations:
        print("❌ Architecture violations found:\n")
        for i, violation in enumerate(violations, 1):
            print(f"  {i}. {violation}")

        print("\n💡 How to fix:")
        print("  - Move Python files to appropriate directories")
        print("  - Add build artifacts to .gitignore")
        print("  - Run 'make clean' to remove temporary files")
        print("  - Use environment variables for secrets")
        return False

    print("✅ Repository architecture is compliant")
    return True


def main():
    """Main entry point."""
    sys.exit(0 if check_architecture() else 1)


if __name__ == "__main__":
    main()
