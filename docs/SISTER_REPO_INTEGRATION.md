# Sister Repository Integration Guide

> **Agent-Ready Documentation**: This guide is designed to be used directly by AI agents in sister repositories for seamless 12-factor-agents framework integration.

## Overview

The 12-factor-agents framework provides seamless integration for sister repositories through a standardized agent bridge pattern. This guide contains all the code and instructions needed for complete integration.

## Quick Setup (2 Minutes)

### 1. Directory Structure Verification
Your repositories should be structured as sister repositories:

```
parent-directory/
├── 12-factor-agents/     # The framework (this repository)
├── your-project/         # Your project (pin-citer, cite-assist, etc.)
├── another-project/      # Another project
└── more-projects/        # Additional projects
```

### 2. Copy Agent Bridge
Create `utils/agent_bridge.py` in your project with this complete implementation:

```python
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
            ("Intelligent Issue Agent", "IntelligentIssueAgent", "Fix documentation"),
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
```

### 3. Verification Commands

Test your integration:

```bash
# Test bridge functionality
cd your-project
python utils/agent_bridge.py

# Test framework access
uv run python ../12-factor-agents/bin/agent.py list

# Test running an agent
uv run python ../12-factor-agents/bin/agent.py run SmartIssueAgent "test-issue"
```

## Complete Integration Examples

### A. Basic Agent Integration

Create `agents/your_agent.py` in your project:

```python
#!/usr/bin/env python3
"""
Example agent for your project that uses 12-factor-agents framework.
"""

# Import framework bridge (auto-sets up path)
from utils.agent_bridge import get_framework_path, run_framework_agent

# Now framework imports work
from core.agent import BaseAgent
from core.tools import ToolResponse


class YourProjectAgent(BaseAgent):
    """
    Custom agent that leverages the 12-factor-agents framework.
    """

    def __init__(self):
        super().__init__(agent_id="your_project_agent")
        self.framework_path = get_framework_path()

    async def execute_task(self, task: str) -> dict:
        """
        Execute a task using both your logic and framework agents.
        """
        print(f"🤖 Executing task: {task}")
        
        # Your custom logic here
        result = {"task": task, "status": "processing"}
        
        # Delegate complex tasks to framework agents
        if "analyze" in task.lower():
            # Use SmartIssueAgent for analysis
            framework_cmd = run_framework_agent("SmartIssueAgent", task)
            print(f"🚀 Delegating to framework: {framework_cmd}")
        
        result["status"] = "completed"
        return result

    def get_available_framework_agents(self) -> list:
        """
        Get list of available framework agents.
        """
        import subprocess
        
        cmd = f"uv run python {self.framework_path}/bin/agent.py list"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # Parse agent list from output
        agents = []
        lines = result.stdout.split('\n')
        for line in lines:
            if "🤖" in line:
                agent_name = line.split("🤖")[1].strip()
                agents.append(agent_name)
        
        return agents
```

### B. Submit to Agents Helper

Create `scripts/submit_to_agents.py` in your project:

```python
#!/usr/bin/env python3
"""
Utility script for submitting tasks to 12-factor-agents from your project.

This script provides a convenient interface for running framework agents
from within your project directory structure.
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Import framework bridge
sys.path.append(str(Path(__file__).parent.parent))
from utils.agent_bridge import get_framework_path, verify_framework_access


def submit_to_agent(agent_name: str, task: str, show_output: bool = True) -> bool:
    """
    Submit a task to a framework agent.
    
    Args:
        agent_name: Name of the agent to run
        task: Task description
        show_output: Whether to show agent output
    
    Returns:
        bool: True if agent execution succeeded
    """
    try:
        framework_path = get_framework_path()
        cmd = [
            "uv", "run", "python", 
            str(framework_path / "bin" / "agent.py"), 
            "run", agent_name, task
        ]
        
        print(f"🚀 Submitting to {agent_name}: {task}")
        print(f"📋 Command: {' '.join(cmd)}")
        
        if show_output:
            result = subprocess.run(cmd, check=True)
            return result.returncode == 0
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Task completed successfully")
                return True
            else:
                print(f"❌ Task failed: {result.stderr}")
                return False
                
    except Exception as e:
        print(f"❌ Error submitting task: {e}")
        return False


def list_available_agents() -> list:
    """
    Get list of available framework agents.
    """
    try:
        framework_path = get_framework_path()
        cmd = ["uv", "run", "python", str(framework_path / "bin" / "agent.py"), "list"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout.split('\n')
        else:
            print(f"❌ Error listing agents: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"❌ Error listing agents: {e}")
        return []


def main():
    """
    Command-line interface for submitting tasks to agents.
    """
    parser = argparse.ArgumentParser(
        description="Submit tasks to 12-factor-agents framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/submit_to_agents.py SmartIssueAgent "Fix bug #123"
  python scripts/submit_to_agents.py --list
  python scripts/submit_to_agents.py --verify
  python scripts/submit_to_agents.py IntelligentIssueAgent "Create API docs" --quiet
        """
    )
    
    parser.add_argument("agent", nargs="?", help="Agent name to run")
    parser.add_argument("task", nargs="?", help="Task description")
    parser.add_argument("--list", "-l", action="store_true", help="List available agents")
    parser.add_argument("--verify", "-v", action="store_true", help="Verify framework access")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode (no output)")
    
    args = parser.parse_args()
    
    # Verify framework access first
    status = verify_framework_access()
    if not status["accessible"]:
        print("❌ Framework not accessible:")
        if "error" in status:
            print(f"   Error: {status['error']}")
        return 1
    
    if args.verify:
        print("✅ Framework access verified")
        print(f"📁 Framework path: {status['framework_path']}")
        return 0
    
    if args.list:
        print("📦 Available agents:")
        agents = list_available_agents()
        for line in agents:
            if "🤖" in line:
                print(f"  {line}")
        return 0
    
    if not args.agent or not args.task:
        parser.print_help()
        return 1
    
    # Submit task to agent
    success = submit_to_agent(args.agent, args.task, not args.quiet)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
```

### C. Integration Test Example

Create `tests/test_framework_integration.py` in your project:

```python
#!/usr/bin/env python3
"""
Integration tests for 12-factor-agents framework access.
"""

import pytest
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.agent_bridge import (
    setup_agent_framework,
    get_framework_path,
    verify_framework_access,
    run_framework_agent
)


class TestFrameworkIntegration:
    """Test framework integration functionality."""
    
    def test_framework_path_exists(self):
        """Test that framework path can be found."""
        framework_path = get_framework_path()
        assert framework_path.exists()
        assert framework_path.is_dir()
        assert (framework_path / "core").exists()
        assert (framework_path / "agents").exists()
    
    def test_setup_agent_framework(self):
        """Test framework setup."""
        result = setup_agent_framework()
        assert result is True
        
        # Test that framework path is in sys.path
        framework_path = str(get_framework_path())
        assert framework_path in sys.path
    
    def test_verify_framework_access(self):
        """Test framework access verification."""
        status = verify_framework_access()
        
        assert status["accessible"] is True
        assert status["framework_path"] is not None
        assert len(status["missing_components"]) == 0
        assert status["python_path_setup"] is True
    
    def test_run_framework_agent_command_generation(self):
        """Test framework agent command generation."""
        cmd = run_framework_agent("SmartIssueAgent", "test task")
        
        assert "uv run python" in cmd
        assert "bin/agent.py run SmartIssueAgent" in cmd
        assert "test task" in cmd
    
    def test_framework_cli_accessible(self):
        """Test that framework CLI is accessible."""
        framework_path = get_framework_path()
        cmd = ["uv", "run", "python", str(framework_path / "bin" / "agent.py"), "list"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Should not error out (framework should be accessible)
        assert result.returncode == 0
        assert "Available Agents" in result.stdout or "agents found" in result.stdout.lower()
    
    def test_framework_imports_work(self):
        """Test that framework imports work after setup."""
        # Setup framework
        setup_agent_framework()
        
        # Test imports
        try:
            from core.agent import BaseAgent
            from core.tools import ToolResponse
            assert BaseAgent is not None
        except ImportError as e:
            pytest.fail(f"Framework imports failed: {e}")
    
    @pytest.mark.integration
    def test_run_actual_framework_agent(self):
        """Integration test: Actually run a framework agent."""
        framework_path = get_framework_path()
        cmd = [
            "uv", "run", "python", 
            str(framework_path / "bin" / "agent.py"), 
            "run", "SmartIssueAgent", "test integration"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Agent should execute without critical errors
        # (may have warnings, but shouldn't crash)
        assert result.returncode in [0, 1]  # 1 might be expected for test task
        assert "Error executing agent" not in result.stdout


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
```

## Project-Specific Examples

### Pin-Citer Integration

For citation management projects like pin-citer:

```python
# pin_citer/agents/citation_agent.py
from utils.agent_bridge import run_framework_agent, get_framework_path
from core.agent import BaseAgent

class PinCiterAgent(BaseAgent):
    """Citation processing agent with framework integration."""
    
    async def process_citations(self, document_path: str) -> dict:
        """Process citations using framework agents."""
        
        # Use SmartIssueAgent for complex citation analysis
        analysis_task = f"analyze citations in {document_path}"
        analysis_cmd = run_framework_agent("SmartIssueAgent", analysis_task)
        
        # Use IntelligentIssueAgent for validation
        validation_task = f"validate citation format in {document_path}"
        validation_cmd = run_framework_agent("IntelligentIssueAgent", validation_task)
        
        return {
            "analysis_command": analysis_cmd,
            "validation_command": validation_cmd,
            "status": "ready"
        }
```

### Cite-Assist Integration

For legal document processing projects:

```python
# cite_assist/agents/legal_agent.py
from utils.agent_bridge import run_framework_agent
from core.agent import BaseAgent

class LegalCitationAgent(BaseAgent):
    """Legal citation processing with framework support."""
    
    async def process_legal_document(self, case_file: str) -> dict:
        """Process legal documents using framework agents."""
        
        # Use framework for issue decomposition
        complex_task = f"analyze legal citations and format according to Bluebook rules in {case_file}"
        decomposition_cmd = run_framework_agent("SmartIssueAgent", complex_task)
        
        return {
            "framework_command": decomposition_cmd,
            "document": case_file,
            "processing_status": "delegated_to_framework"
        }
```

### Development Project Integration

For software development projects:

```python
# dev_project/agents/code_agent.py
from utils.agent_bridge import run_framework_agent
from core.agent import BaseAgent

class CodeAnalysisAgent(BaseAgent):
    """Code analysis with framework integration."""
    
    async def analyze_codebase(self, repo_path: str) -> dict:
        """Analyze codebase using framework agents."""
        
        # Use framework for code review
        review_task = f"perform comprehensive code review of {repo_path}"
        review_cmd = run_framework_agent("CodeReviewAgent", review_task)
        
        # Use framework for testing
        test_task = f"analyze and improve test coverage in {repo_path}"
        test_cmd = run_framework_agent("TestingAgent", test_task)
        
        return {
            "review_command": review_cmd,
            "test_command": test_cmd,
            "repository": repo_path
        }
```

## Verification Checklist

Use this checklist to verify your integration:

### ✅ Basic Setup
- [ ] Sister repository structure created
- [ ] `utils/agent_bridge.py` file copied to your project
- [ ] Bridge test runs successfully: `python utils/agent_bridge.py`
- [ ] Framework CLI accessible: `uv run python ../12-factor-agents/bin/agent.py list`

### ✅ Integration Tests
- [ ] Framework path resolution works
- [ ] Framework imports work after bridge setup
- [ ] Agent commands can be generated
- [ ] At least one framework agent can be executed
- [ ] Integration test suite passes

### ✅ Project Customization
- [ ] Custom agent created that uses framework
- [ ] `submit_to_agents.py` script created and tested
- [ ] Project-specific framework integration working
- [ ] Documentation updated with integration details

### ✅ Production Ready
- [ ] Error handling implemented
- [ ] Framework version compatibility verified
- [ ] Integration tests added to CI/CD pipeline
- [ ] Team trained on framework usage

## Troubleshooting

### Common Issues and Solutions

#### Issue: "12-factor-agents framework not found"

**Symptoms:**
```
ImportError: 12-factor-agents framework not found at expected location
```

**Solution:**
```bash
# Verify directory structure
cd your-project
ls ../12-factor-agents  # Should show framework contents

# If framework missing, clone it:
cd ..
git clone https://github.com/donaldbraman/12-factor-agents.git
cd your-project

# Test again
python utils/agent_bridge.py
```

#### Issue: "uv command not found"

**Symptoms:**
```bash
uv: command not found
```

**Solution:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal

# Verify installation
uv --version

# Test framework access
uv run python ../12-factor-agents/bin/agent.py list
```

#### Issue: Framework imports fail

**Symptoms:**
```python
ImportError: No module named 'core.agent'
```

**Solution:**
```python
# Ensure bridge is imported first
from utils.agent_bridge import setup_agent_framework

# Verify setup worked
status = verify_framework_access()
print(status)

# Then import framework components
from core.agent import BaseAgent
```

#### Issue: Agent execution fails

**Symptoms:**
```
❌ Agent 'SomeAgent' not found
```

**Solution:**
```bash
# List available agents
uv run python ../12-factor-agents/bin/agent.py list

# Get detailed info about an agent
uv run python ../12-factor-agents/bin/agent.py info SmartIssueAgent

# Use exact agent name from list
uv run python ../12-factor-agents/bin/agent.py run SmartIssueAgent "your task"
```

#### Issue: Permission errors

**Symptoms:**
```
Permission denied: ../12-factor-agents/bin/agent.py
```

**Solution:**
```bash
# Make agent script executable
chmod +x ../12-factor-agents/bin/agent.py

# Or run with python directly
uv run python ../12-factor-agents/bin/agent.py list
```

#### Issue: Python path conflicts

**Symptoms:**
```
ModuleNotFoundError: No module named 'agents.your_module'
```

**Solution:**
```python
# Use explicit path setup
import sys
from pathlib import Path

# Add your project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add framework to path
from utils.agent_bridge import setup_agent_framework
setup_agent_framework()

# Now both imports work
from your_module import YourClass
from core.agent import BaseAgent
```

### Testing Framework Access

Use this diagnostic script to test your integration:

```python
#!/usr/bin/env python3
"""
Diagnostic script for testing 12-factor-agents integration.
"""

def run_diagnostics():
    """Run comprehensive integration diagnostics."""
    print("🔍 12-Factor Agents Integration Diagnostics")
    print("=" * 50)
    
    # Test 1: Bridge import
    try:
        from utils.agent_bridge import verify_framework_access, get_framework_path
        print("✅ Bridge import successful")
    except ImportError as e:
        print(f"❌ Bridge import failed: {e}")
        return
    
    # Test 2: Framework access
    status = verify_framework_access()
    if status["accessible"]:
        print("✅ Framework accessible")
        print(f"   Path: {status['framework_path']}")
    else:
        print("❌ Framework not accessible")
        if "error" in status:
            print(f"   Error: {status['error']}")
        if status["missing_components"]:
            print(f"   Missing: {', '.join(status['missing_components'])}")
        return
    
    # Test 3: Framework imports
    try:
        from core.agent import BaseAgent
        print("✅ Framework imports working")
    except ImportError as e:
        print(f"❌ Framework imports failed: {e}")
        return
    
    # Test 4: CLI access
    import subprocess
    try:
        framework_path = get_framework_path()
        cmd = ["uv", "run", "python", str(framework_path / "bin" / "agent.py"), "list"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ CLI access working")
        else:
            print("⚠️  CLI access issues (but framework may still work)")
            print(f"   Error: {result.stderr}")
    
    except Exception as e:
        print(f"⚠️  CLI test failed: {e}")
    
    print("\n🎉 Integration diagnostics complete")
    print("💡 If all tests pass, your integration is ready!")

if __name__ == "__main__":
    run_diagnostics()
```

## Error Message Reference

### Bridge Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ImportError: 12-factor-agents framework not found` | Framework directory missing | Clone framework as sister repository |
| `No module named 'utils.agent_bridge'` | Bridge file not copied | Copy `agent_bridge.py` to `utils/` directory |
| `Permission denied` | Script permissions issue | Run `chmod +x` on agent scripts |

### Framework Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `No module named 'core.agent'` | Framework not in Python path | Import bridge before framework imports |
| `Agent 'AgentName' not found` | Invalid agent name | Use `uv run python ../12-factor-agents/bin/agent.py list` |
| `uv: command not found` | uv package manager not installed | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

### Integration Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` in tests | Path setup issue | Add both project and framework to Python path |
| `subprocess.TimeoutExpired` | Agent execution timeout | Increase timeout or check agent task complexity |
| `JSON decode error` | Invalid agent response | Check agent output format and error handling |

## Advanced Integration Patterns

### Pattern 1: Background Agent Execution

```python
import asyncio
import subprocess
from utils.agent_bridge import get_framework_path

class BackgroundAgentRunner:
    """Run framework agents in background."""
    
    @staticmethod
    async def run_agent_background(agent_name: str, task: str) -> str:
        """Run agent in background and return process ID."""
        framework_path = get_framework_path()
        cmd = [
            "uv", "run", "python",
            str(framework_path / "bin" / "agent.py"),
            "run", agent_name, task
        ]
        
        # Start process in background
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        return f"background_agent_{process.pid}"
```

### Pattern 2: Agent Result Processing

```python
from utils.agent_bridge import run_framework_agent
import subprocess
import json

class AgentResultProcessor:
    """Process and parse framework agent results."""
    
    @staticmethod
    def run_agent_with_result(agent_name: str, task: str) -> dict:
        """Run agent and parse structured result."""
        framework_path = get_framework_path()
        cmd = [
            "uv", "run", "python",
            str(framework_path / "bin" / "agent.py"),
            "run", agent_name, task
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "agent": agent_name,
            "task": task
        }
```

### Pattern 3: Multi-Agent Coordination

```python
from typing import List, Dict
import asyncio
from utils.agent_bridge import get_framework_path

class MultiAgentCoordinator:
    """Coordinate multiple framework agents."""
    
    async def coordinate_agents(self, agent_tasks: List[Dict]) -> List[Dict]:
        """Run multiple agents concurrently."""
        tasks = []
        
        for config in agent_tasks:
            task = self._create_agent_task(
                config["agent"], 
                config["task"]
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def _create_agent_task(self, agent_name: str, task: str):
        """Create async task for agent execution."""
        framework_path = get_framework_path()
        cmd = [
            "uv", "run", "python",
            str(framework_path / "bin" / "agent.py"),
            "run", agent_name, task
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        return {
            "agent": agent_name,
            "task": task,
            "success": process.returncode == 0,
            "output": stdout.decode(),
            "error": stderr.decode()
        }
```

## Framework Updates

### Staying Updated

The framework is actively developed. Stay updated with:

```bash
# Update framework
cd ../12-factor-agents
git pull origin main

# Verify updates
uv run python bin/agent.py list

# Test your integration still works
cd ../your-project
python utils/agent_bridge.py
```

### Breaking Change Management

If framework updates cause integration issues:

1. **Check compatibility**: Review framework CHANGELOG.md
2. **Update bridge**: Copy latest `utils/agent_bridge.py` 
3. **Update imports**: Check for changed module paths
4. **Test thoroughly**: Run full integration test suite
5. **Update dependencies**: Check if new framework dependencies needed

### Version Pinning

For production stability, consider pinning framework version:

```bash
# Pin to specific commit
cd ../12-factor-agents
git checkout v1.2.3  # or specific commit hash

# Create version lock file in your project
echo "12-factor-agents-commit: $(git rev-parse HEAD)" > framework-version.lock
```

## Summary

This integration guide provides everything needed for sister repositories to seamlessly access the 12-factor-agents framework. The key components are:

1. **Agent Bridge**: Copy `utils/agent_bridge.py` for path resolution
2. **Submit Script**: Use `scripts/submit_to_agents.py` for task submission  
3. **Integration Tests**: Implement `tests/test_framework_integration.py`
4. **Verification**: Follow the checklist and run diagnostics
5. **Troubleshooting**: Use the error reference for quick fixes

The framework provides powerful agent capabilities with zero configuration - just clone as a sister repository and start using relative paths for access.

**Next Steps:**
1. Copy the agent bridge to your project
2. Run verification commands  
3. Create your first integrated agent
4. Add integration tests
5. Start leveraging framework agents for complex tasks

For additional examples and documentation, explore the framework's `docs/` directory using relative paths from your project.