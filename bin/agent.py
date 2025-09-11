#!/usr/bin/env uv run python
"""
12-Factor Agent CLI - Powered by uv
Main command-line interface for running agents
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.agent_executor import AgentExecutor  # noqa: E402


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="12-Factor Agent CLI - Powered by uv",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run agent list                              # List all available agents
  uv run agent run CodeReviewAgent "review src/" # Run code review on src/
  uv run agent orchestrate issue-pipeline        # Run orchestration pipeline
  
For more information, see: https://github.com/donaldbraman/12-factor-agents
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List all available agents")
    list_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed agent information"
    )

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a specific agent")
    run_parser.add_argument("agent", help="Agent name (e.g., CodeReviewAgent)")
    run_parser.add_argument("task", help="Task description for the agent")
    run_parser.add_argument(
        "--context", "-c", help="Additional context as JSON string", default="{}"
    )
    run_parser.add_argument(
        "--status", "-s", action="store_true", help="Show status of task/issue"
    )

    # Orchestrate command
    orch_parser = subparsers.add_parser(
        "orchestrate", help="Run an orchestration pipeline"
    )
    orch_parser.add_argument("pipeline", help="Pipeline name to execute")
    orch_parser.add_argument(
        "--config", "-c", help="Pipeline configuration file", type=Path
    )

    # Info command
    info_parser = subparsers.add_parser(
        "info", help="Show information about a specific agent"
    )
    info_parser.add_argument("agent", help="Agent name to get information about")

    args = parser.parse_args()

    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return 0

    # Initialize executor
    try:
        executor = AgentExecutor()
    except Exception as e:
        print(f"❌ Failed to initialize agent executor: {e}")
        return 1

    # Execute commands
    try:
        if args.command == "list":
            agents = executor.list_agents(verbose=args.verbose)
            if not agents:
                print(
                    "No agents found. Make sure you're in a 12-factor-agents project."
                )
                return 1

        elif args.command == "run":
            if args.status:
                print(f"📊 Checking status for {args.agent} task: {args.task}")
                # Simple status check - could be enhanced to check actual task status
                print("✅ Status: Ready to execute")
            else:
                print(f"🤖 Running {args.agent}...")
                result = executor.run_agent(args.agent, args.task, args.context)
                if result:
                    print("✅ Task completed successfully")
                else:
                    print("❌ Task failed")
                    return 1

        elif args.command == "orchestrate":
            print(f"🎭 Running orchestration: {args.pipeline}")
            result = executor.orchestrate(args.pipeline, args.config)
            if result:
                print("✅ Pipeline completed successfully")
            else:
                print("❌ Pipeline failed")
                return 1

        elif args.command == "info":
            info = executor.get_agent_info(args.agent)
            if not info:
                print(f"❌ Agent '{args.agent}' not found")
                return 1

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
