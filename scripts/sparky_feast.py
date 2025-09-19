#!/usr/bin/env python3
"""
SPARKY FEAST - Feed SPARKY a full course meal of issues!
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.sparky_lean import SPARKYLean


def main():
    """Give SPARKY a feast of issues"""

    print("🍽️  SPARKY FEAST - All You Can Process Buffet! 🍽️")
    print("=" * 60)

    sparky = SPARKYLean()

    # Find ALL issues
    issues_dir = Path("issues")
    all_issues = sorted([str(f) for f in issues_dir.glob("*.md")])

    print(f"\n🎉 Found {len(all_issues)} delicious issues for SPARKY!")
    print("🍖 Let's see how fast SPARKY can devour them all...")
    print()

    # Process first 10 as appetizer
    appetizer = all_issues[:10]
    print(f"🥗 APPETIZER: First {len(appetizer)} issues")
    print("-" * 40)

    results = sparky.process_batch(appetizer)

    print("\n" + "=" * 60)
    print("🎆 SPARKY FEAST COMPLETE! 🎆")
    print("=" * 60)
    print(f"🍽️  Issues served: {len(appetizer)}")
    print(f"✅ Fully digested: {len(results['success'])}")
    print(f"❌ Too spicy: {len(results['failed'])}")
    print(f"🏆 Success rate: {len(results['success'])/len(appetizer)*100:.1f}%")

    print("\n📊 Menu Breakdown:")
    for issue_type, issues in results["by_type"].items():
        print(f"  {issue_type.upper()}: {len(issues)} dishes")
        for issue in issues[:2]:  # Show first 2 of each type
            print(f"    • {Path(issue).name}")

    print("\n🎯 SPARKY Status: WELL FED AND HAPPY!")
    print("💪 Ready for more? Run with --all flag for the full buffet!")


if __name__ == "__main__":
    main()
