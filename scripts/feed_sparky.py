#!/usr/bin/env python3
"""
Feed SPARKY - Give our lean machine some issues to chew on!
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.sparky import SPARKY


def main():
    """Feed SPARKY with a selection of issues"""

    print("🍖 FEEDING SPARKY - Let's see what our lean machine can do!")
    print("=" * 60)

    # Create SPARKY instance
    sparky = SPARKY()

    # Feed specific test issues first
    test_issues = [
        "issues/test-simple.md",  # Our simple bug fix test
        "issues/122.md",  # Quality analysis report
        "issues/001-add-noqa-to-code-review-agent.md",  # Real bug
        "issues/004-remove-unused-agents.md",  # Cleanup task
    ]

    print(f"\n🎯 Feeding SPARKY {len(test_issues)} hand-picked issues...")
    results = sparky.process_batch(test_issues)

    print("\n" + "=" * 60)
    print("📊 SPARKY DIGEST REPORT")
    print("=" * 60)
    print(f"🍖 Issues consumed: {len(test_issues)}")
    print(f"✅ Successfully digested: {len(results['success'])}")
    print(f"❌ Indigestion on: {len(results['failed'])}")
    print(f"⚡ Processing speed: KrazY-fast ({results['total_time']:.2f}s)")
    print(f"📈 Success rate: {len(results['success'])/len(test_issues)*100:.1f}%")

    if results["success"]:
        print("\n✅ SPARKY successfully processed:")
        for issue in results["success"]:
            print(f"   • {issue}")

    if results["failed"]:
        print("\n❌ SPARKY choked on:")
        for issue in results["failed"]:
            print(f"   • {issue}")

    print("\n" + "=" * 60)
    print("🎆 SPARKY Status: FED AND HAPPY! 🎆")
    print("=" * 60)


if __name__ == "__main__":
    main()
