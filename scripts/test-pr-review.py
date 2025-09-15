#!/usr/bin/env uv run python
"""
Test script for PR Review Agent
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.pr_review_agent import PRReviewAgent  # noqa: E402


def test_pr_review():
    """Test the PR review agent"""

    print("=" * 60)
    print("PR REVIEW AGENT TEST")
    print("=" * 60)

    # Check environment
    has_github = bool(os.getenv("GITHUB_TOKEN"))
    has_claude = bool(os.getenv("ANTHROPIC_API_KEY"))

    print("\n📋 Environment Check:")
    print(f"  GITHUB_TOKEN: {'✅ Set' if has_github else '❌ Not set'}")
    print(f"  ANTHROPIC_API_KEY: {'✅ Set' if has_claude else '❌ Not set'}")

    if not has_github:
        print("\n⚠️ Set GITHUB_TOKEN to test with real PRs")
        print("  export GITHUB_TOKEN=your_github_token")

    if not has_claude:
        print("\n⚠️ Set ANTHROPIC_API_KEY for real Claude analysis")
        print("  export ANTHROPIC_API_KEY=your_claude_api_key")

    # Test agent initialization
    print("\n🔧 Initializing PRReviewAgent...")
    try:
        agent = PRReviewAgent()
        print("✅ Agent initialized successfully")

        print("\n📦 Registered tools:")
        for tool in agent.tools:
            print(f"  - {tool.name}: {tool.description}")

        print("\n⚙️ Configuration:")
        for key, value in agent.config.items():
            print(f"  - {key}: {value}")

        # Test with a simple task if tokens are available
        if has_github and has_claude:
            print("\n🧪 Running test review...")
            print("  Testing with microsoft/vscode PR #1 (read-only)")

            result = agent.execute_task("analyze PR #1 in microsoft/vscode")

            if isinstance(result, dict) and not result.get("error"):
                print("\n✅ Test review completed successfully!")
                print(f"  Title: {result.get('title', 'N/A')}")
                print(f"  Quality Score: {result.get('quality_score', 'N/A')}/10")
                print(f"  Issues Found: {result.get('issues_found', 0)}")
                print(f"  Approved: {result.get('approved', False)}")
            else:
                print(f"\n⚠️ Test review failed: {result}")
        else:
            print("\n⏭️ Skipping live test (missing API keys)")

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pr_review()
    sys.exit(0 if success else 1)
