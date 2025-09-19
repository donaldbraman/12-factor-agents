#!/usr/bin/env python3
"""Check for problematic import patterns."""

import sys
import re
from pathlib import Path


def check_imports(filepath):
    """Check for wildcard imports and other import issues."""
    violations = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (UnicodeDecodeError, FileNotFoundError):
        return True

    for line_num, line in enumerate(lines, 1):
        # Check for wildcard imports
        if re.match(r"^from .+ import \*", line.strip()):
            violations.append((line_num, "Wildcard import", line.strip()))

        # Check for importing everything from a module
        elif re.match(r"^import \*", line.strip()):
            violations.append((line_num, "Import * not allowed", line.strip()))

    if violations:
        print(f"\n❌ {filepath}: Import violations found:")
        for line_num, issue, line in violations:
            print(f"   Line {line_num}: {issue}")
            print(f"      {line}")
        print("   Fix: Import specific items instead of using '*'")
        return False

    return True


def main():
    """Main entry point."""
    if len(sys.argv) == 1:
        # Check all Python files
        all_valid = True
        for filepath in Path(".").rglob("*.py"):
            if ".venv" not in str(filepath) and "venv" not in str(filepath):
                if not check_imports(str(filepath)):
                    all_valid = False
    else:
        # Check specified files
        all_valid = True
        for filepath in sys.argv[1:]:
            if filepath.endswith(".py"):
                if not check_imports(filepath):
                    all_valid = False

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
