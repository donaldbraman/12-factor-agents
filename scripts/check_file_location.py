#!/usr/bin/env python3
"""Validate Python files are in correct directories."""

import sys
from pathlib import Path

ALLOWED_ROOT_FILES = {"setup.py"}
DIRECTORY_RULES = {
    "test_": "tests/",
    "_test.py": "tests/",
    "_agent.py": "agents/",
    "_agent_": "agents/",
}


def check_file_location(filepath):
    """Check if file is in correct location."""
    path = Path(filepath)

    # Skip virtual environment files
    if ".venv" in str(path) or "venv" in str(path):
        return True

    # Check root directory files
    if path.parent == Path("."):
        if path.name.endswith(".py") and path.name not in ALLOWED_ROOT_FILES:
            print(f"❌ {filepath}: Python files not allowed in root directory")
            print(
                "   Move to appropriate directory (agents/, core/, scripts/, or tests/)"
            )
            return False

    # Check test files are in tests directory
    filename = path.name
    if filename.startswith("test_") or filename.endswith("_test.py"):
        if "tests" not in str(path.parent):
            print(f"❌ {filepath}: Test file should be in tests/ directory")
            return False

    # Check agent files are in agents directory
    if "_agent" in filename or filename.endswith("_agent.py"):
        if "agents" not in str(path.parent) and "tests" not in str(path.parent):
            print(f"❌ {filepath}: Agent file should be in agents/ directory")
            return False

    return True


def main():
    """Main entry point for pre-commit hook."""
    if len(sys.argv) == 1:
        # No files provided, check entire repository
        all_valid = True
        for filepath in Path(".").rglob("*.py"):
            if not check_file_location(str(filepath)):
                all_valid = False
    else:
        # Check specific files
        all_valid = True
        for filepath in sys.argv[1:]:
            if filepath.endswith(".py"):
                if not check_file_location(filepath):
                    all_valid = False

    if not all_valid:
        print("\n💡 Tip: Use 'git mv' to move files to correct locations")

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
