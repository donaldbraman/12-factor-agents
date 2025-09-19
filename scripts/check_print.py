#!/usr/bin/env python3
"""Check for print statements in production code."""

import sys
import re
from pathlib import Path

# Directories where print statements are allowed
ALLOWED_DIRS = ["scripts", "tests", "examples", "bin"]


def is_allowed_file(filepath):
    """Check if file is allowed to have print statements."""
    path = Path(filepath)

    # Check if in allowed directory
    for allowed_dir in ALLOWED_DIRS:
        if allowed_dir in str(path.parent):
            return True

    # Allow in specific files
    allowed_files = ["setup.py", "debug.py"]
    if path.name in allowed_files:
        return True

    return False


def check_print(filepath):
    """Check for print statements in production code."""
    if is_allowed_file(filepath):
        return True

    violations = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (UnicodeDecodeError, FileNotFoundError):
        return True

    for line_num, line in enumerate(lines, 1):
        # Look for print statements (but not in comments or strings)
        if re.search(r"^\s*print\s*\(", line):
            # Check if it's commented out
            if not line.strip().startswith("#"):
                violations.append((line_num, line.strip()[:60]))

    if violations:
        print(f"\n❌ {filepath}: Print statements found in production code:")
        for line_num, line in violations:
            print(f"   Line {line_num}: {line}")
        print("   Fix: Use logging instead (import logging; logger.info(...))")
        return False

    return True


def main():
    """Main entry point."""
    if len(sys.argv) == 1:
        # Check all Python files
        all_valid = True
        for filepath in Path(".").rglob("*.py"):
            if ".venv" not in str(filepath) and "venv" not in str(filepath):
                if not check_print(str(filepath)):
                    all_valid = False
    else:
        # Check specified files
        all_valid = True
        for filepath in sys.argv[1:]:
            if filepath.endswith(".py"):
                if not check_print(filepath):
                    all_valid = False

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
