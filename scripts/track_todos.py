#!/usr/bin/env python3
"""Track TODO comments and suggest creating issues."""

import sys
import re
from pathlib import Path
from collections import defaultdict


def track_todos(filepath):
    """Find and report TODO comments."""
    todos = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (UnicodeDecodeError, FileNotFoundError):
        return []

    todo_patterns = [
        r"#\s*TODO:?\s*(.*)",
        r"#\s*FIXME:?\s*(.*)",
        r"#\s*XXX:?\s*(.*)",
        r"#\s*HACK:?\s*(.*)",
        r"#\s*NOTE:?\s*(.*)",
    ]

    for line_num, line in enumerate(lines, 1):
        for pattern in todo_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                todo_text = match.group(1).strip()
                todo_type = pattern.split("\\s*")[1].split(":")[0]
                todos.append((line_num, todo_type, todo_text))

    return todos


def main():
    """Main entry point."""
    all_todos = defaultdict(list)

    if len(sys.argv) == 1:
        # Check all Python files
        files = Path(".").rglob("*.py")
    else:
        # Check specified files
        files = [Path(f) for f in sys.argv[1:] if f.endswith(".py")]

    for filepath in files:
        if ".venv" not in str(filepath) and "venv" not in str(filepath):
            todos = track_todos(str(filepath))
            if todos:
                all_todos[str(filepath)] = todos

    if all_todos:
        total = sum(len(todos) for todos in all_todos.values())
        print(f"\n📝 Found {total} TODO/FIXME comments in {len(all_todos)} files:")

        # Group by type
        by_type = defaultdict(int)
        for filepath, todos in all_todos.items():
            for _, todo_type, _ in todos:
                by_type[todo_type] += 1

        print("\n  Summary by type:")
        for todo_type, count in sorted(by_type.items()):
            print(f"    {todo_type}: {count}")

        # Show first few examples
        print("\n  Examples (first 5):")
        shown = 0
        for filepath, todos in list(all_todos.items())[:5]:
            for line_num, todo_type, text in todos[:1]:  # Show 1 per file
                print(f"    {filepath}:{line_num} - {todo_type}: {text[:50]}")
                shown += 1
                if shown >= 5:
                    break
            if shown >= 5:
                break

        print("\n💡 Tip: Consider creating GitHub issues for these TODOs")
        print("   This helps track technical debt properly")

    # Always exit 0 for TODO tracking (warning only, not blocking)
    sys.exit(0)


if __name__ == "__main__":
    main()
