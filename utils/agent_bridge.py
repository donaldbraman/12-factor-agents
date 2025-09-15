#!/usr/bin/env python3
"""
Standard bridge to 12-factor-agents framework for sister repositories.

This module provides a consistent way for sister repositories to access
the 12-factor-agents framework using relative paths. Copy this file to
your project's utils/ directory for standardized integration.

Usage:
    # In your project's agent files
    from utils.agent_bridge import setup_agent_framework
    
    # Framework is now available
    from core.agent import BaseAgent
    from core.tools import ToolResponse

Example Directory Structure:
    parent-directory/
    ├── 12-factor-agents/     # The framework
    ├── your-project/         # Your project
    │   ├── utils/
    │   │   └── agent_bridge.py  # This file (copied)
    │   └── agents/
    │       └── your_agent.py
    └── other-projects/
"""

import sys
from pathlib import Path
import os


def setup_agent_framework() -> bool:
    """
    Setup path to 12-factor-agents framework using relative paths.

    This function automatically detects the framework location and adds it
    to sys.path for imports. It assumes the standard sister repository layout.

    Returns:
        bool: True if framework was found and added to path, False otherwise

    Raises:
        ImportError: If framework cannot be found at expected location
    """
    # Calculate relative path to framework from this file's location
    # utils/agent_bridge.py -> ../12-factor-agents
    framework_path = Path(__file__).parent.parent.parent / "12-factor-agents"

    if framework_path.exists() and framework_path.is_dir():
        framework_str = str(framework_path.resolve())
        if framework_str not in sys.path:
            sys.path.insert(0, framework_str)
        return True
    else:
        raise ImportError(
            f"12-factor-agents framework not found at expected location: {framework_path}\n"
            f"Expected directory structure:\n"
            f"  parent-directory/\n"
            f"  ├── 12-factor-agents/  # Framework repository\n"
            f"  └── your-project/      # Your project (current location)\n"
            f"\nPlease ensure the framework is cloned as a sister repository."
        )


def get_framework_path() -> Path:
    """
    Get absolute path to the 12-factor-agents framework.

    Returns:
        Path: Absolute path to the framework directory

    Raises:
        ImportError: If framework cannot be found
    """
    framework_path = Path(__file__).parent.parent.parent / "12-factor-agents"
    if not framework_path.exists():
        raise ImportError(f"Framework not found at {framework_path}")
    return framework_path.resolve()


def verify_framework_access() -> dict:
    """
    Verify that the framework is accessible and return status information.

    Returns:
        dict: Status information about framework access
    """
    try:
        framework_path = get_framework_path()

        # Check for key framework components
        key_components = [
            framework_path / "core" / "agent.py",
            framework_path / "bin" / "agent.py",
            framework_path / "agents",
            framework_path / "docs",
        ]

        missing_components = [
            str(comp.relative_to(framework_path))
            for comp in key_components
            if not comp.exists()
        ]

        return {
            "framework_path": str(framework_path),
            "accessible": len(missing_components) == 0,
            "missing_components": missing_components,
            "python_path_setup": str(framework_path) in sys.path,
        }

    except ImportError as e:
        return {
            "framework_path": None,
            "accessible": False,
            "error": str(e),
            "python_path_setup": False,
        }


def run_framework_agent(agent_name: str, task: str) -> str:
    """
    Helper to run framework agents from sister repositories.

    Args:
        agent_name: Name of the agent to run (e.g., 'SmartIssueAgent')
        task: Task description or issue number

    Returns:
        str: Command to execute the agent
    """
    framework_path = get_framework_path()
    return f'uv run python {framework_path}/bin/agent.py run {agent_name} "{task}"'


# Auto-setup when imported (can be disabled by setting SKIP_AUTO_SETUP=1)

if not os.environ.get("SKIP_AUTO_SETUP"):
    setup_agent_framework()


if __name__ == "__main__":
    """
    Command-line interface for testing framework access.
    """
    import json

    print("🔍 12-Factor Agents Framework Bridge")
    print("=" * 40)

    # Test framework access
    status = verify_framework_access()

    if status["accessible"]:
        print("✅ Framework is accessible")
        print(f"📁 Framework path: {status['framework_path']}")
        print(f"🐍 Python path setup: {status['python_path_setup']}")

        # Show example commands
        print("\n🚀 Example commands:")
        examples = [
            ("Smart Issue Agent", "SmartIssueAgent", "123"),
            ("File Tool", "FileTool", "analyze src/"),
            ("List agents", "list", ""),
        ]

        for desc, agent, task in examples:
            if task:
                cmd = run_framework_agent(agent, task)
            else:
                cmd = f"uv run python {status['framework_path']}/bin/agent.py {agent}"
            print(f"  {desc}: {cmd}")

    else:
        print("❌ Framework is not accessible")
        if "error" in status:
            print(f"💥 Error: {status['error']}")
        if status["missing_components"]:
            print(f"📋 Missing components: {', '.join(status['missing_components'])}")

    print("\n📊 Full status:")
    print(json.dumps(status, indent=2))
