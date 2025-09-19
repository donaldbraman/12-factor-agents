#!/usr/bin/env python3
"""
Test the new lean agent architecture
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.issue_router import IssueRouter


def main():
    """Test the lean agent system"""

    router = IssueRouter()

    # Test with simple bug issue
    print("Testing with bug issue...")
    result = router.process_issue("test-simple.md")
    print(f"Result: {result.success}")
    if result.data:
        print(f"Data: {result.data}")

    print("\n" + "=" * 50 + "\n")

    # Test with quality issue
    print("Testing with quality issue...")
    result = router.process_issue("122.md")
    print(f"Result: {result.success}")
    if result.data:
        print(f"Data: {result.data}")


if __name__ == "__main__":
    main()
