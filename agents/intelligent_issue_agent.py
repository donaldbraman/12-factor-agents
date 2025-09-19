#!/usr/bin/env python3
"""
Legacy wrapper - redirects to AsyncSparky (SPARKY 6.0).

This file exists for backwards compatibility.
All functionality has been moved to sparky_6_async.py.
"""

import sys
import asyncio
from pathlib import Path

from agents.sparky_6_async import AsyncSparky


class IntelligentIssueAgent:
    """Legacy class that redirects to AsyncSparky."""

    def __init__(self):
        print(
            "⚠️  WARNING: IntelligentIssueAgent is deprecated. Using AsyncSparky instead.",
            file=sys.stderr,
        )
        self.agent = AsyncSparky()

    def process_issue(self, issue_file: Path) -> dict:
        """Process an issue using AsyncSparky."""

        async def run():
            context = await self.agent.launch(issue_file)
            return {
                "success": context.state == "completed",
                "agent_id": context.agent_id,
                "branch": context.metadata.get("branch"),
                "result": context.result,
            }

        return asyncio.run(run())


def main():
    """Main entry point for backwards compatibility."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Legacy IntelligentIssueAgent (redirects to AsyncSparky)"
    )
    parser.add_argument(
        "--issue-file", type=Path, required=True, help="Path to issue file"
    )
    args = parser.parse_args()

    print("🔄 Redirecting to AsyncSparky...", file=sys.stderr)

    # Use AsyncSparky directly
    agent = AsyncSparky()

    async def run():
        return await agent.launch(args.issue_file)

    context = asyncio.run(run())

    if context.state == "completed":
        print(f"✅ Issue processed successfully: {context.agent_id}")
        sys.exit(0)
    else:
        print(f"❌ Issue processing failed: {context.state}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
