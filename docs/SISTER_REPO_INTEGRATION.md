# Sister Repository Integration Guide

> **Agent-Ready Documentation**: This guide is designed to be used directly by AI agents in sister repositories for seamless 12-factor-agents framework integration.

## 🚨 CRITICAL: Common Mistakes to Avoid

**Sister repositories MUST follow the issue-orchestration pattern. Direct agent calls break the entire framework.**

### ❌ WRONG: Direct Agent Calls
```python
# NEVER DO THIS - Breaks orchestration
run_framework_agent("SmartIssueAgent", "fix the bug")
agent.execute_task("implement feature X")
subprocess.run(["python", "bin/agent.py", "run", "SomeAgent", "task"])
```

### ✅ CORRECT: Issue-Number-Only Pattern
```python
# ALWAYS DO THIS - Submit issue numbers to Sparky
from core.github_integration import ExternalIssueProcessor

processor = ExternalIssueProcessor()
result = processor.process_external_issue("your-org/your-repo", 123)
```

### Why This Matters
- **Sparky orchestrates everything**: Direct calls bypass dependency management, routing logic, and telemetry
- **Context preservation**: Only Sparky understands cross-repo relationships and issue dependencies  
- **Error handling**: Direct calls skip comprehensive error recovery and status tracking
- **Telemetry**: Direct calls break monitoring and performance analytics

### Integration Workflow (REQUIRED)
```
Sister Repo                    12-factor-agents
    |                              |
    | 1. Create GitHub issue       |
    |    with task description     |
    |                              |
    | 2. Submit issue NUMBER       |
    |    (not description!)        |
    |--------------------------->  |
    |                              | 3. ExternalIssueProcessor
    |                              |    fetches issue content
    |                              |
    |                              | 4. Sparky analyzes issue
    |                              |    and routes to agent
    |                              |
    |                              | 5. Agent executes task
    |                              |    with full context
    |                              |
    | 6. Results posted back       |
    |    to GitHub issue          |
    |<-----------------------------|
```

**KEY PRINCIPLE**: Never pass task descriptions directly. Always create GitHub issues first.

## Overview

The 12-factor-agents framework provides seamless integration for sister repositories through a standardized GitHub issue orchestration pattern. Sister repositories submit issue numbers to Sparky for intelligent agent routing and execution.

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

### A. Basic Agent Integration (CORRECT PATTERN)

Create `agents/your_agent.py` in your project:

```python
#!/usr/bin/env python3
"""
CORRECT: Sister repository agent using issue-orchestration pattern.

This agent creates GitHub issues and submits them to Sparky for processing.
NEVER calls framework agents directly - always goes through orchestration.
"""

# Import framework bridge (auto-sets up path)
from utils.agent_bridge import get_framework_path
import subprocess
import sys
from pathlib import Path

# Add framework to path for imports
sys.path.insert(0, str(get_framework_path()))
from core.github_integration import ExternalIssueProcessor
from core.agent import BaseAgent


class YourProjectAgent(BaseAgent):
    """
    Custom agent that uses CORRECT 12-factor-agents integration pattern.
    
    Key principles:
    - Never calls agents directly
    - Always creates GitHub issues first  
    - Submits issue numbers to ExternalIssueProcessor
    - Lets Sparky orchestrate execution
    """

    def __init__(self):
        super().__init__(agent_id="your_project_agent")
        self.framework_path = get_framework_path()
        self.external_processor = ExternalIssueProcessor()

    async def execute_task(self, task: str) -> dict:
        """
        Execute task using CORRECT orchestration pattern.
        
        Steps:
        1. Create GitHub issue with task description
        2. Submit issue number to ExternalIssueProcessor
        3. Let Sparky handle agent routing and execution
        """
        print(f"🤖 Processing task: {task}")
        
        # Step 1: Create GitHub issue (you would implement this)
        issue_number = self.create_github_issue(task)
        
        if not issue_number:
            return {"status": "failed", "error": "Could not create GitHub issue"}
        
        # Step 2: Submit to Sparky via ExternalIssueProcessor
        print(f"🚀 Submitting issue #{issue_number} to Sparky for orchestration")
        
        result = self.external_processor.process_external_issue(
            repo=self.get_repo_name(),
            issue_number=issue_number
        )
        
        if result.get("success"):
            print(f"✅ Task completed via issue #{issue_number}")
            print(f"🎯 Agent used: {result.get('issue', {}).get('agent', 'Unknown')}")
            return {
                "status": "completed",
                "issue_number": issue_number,
                "agent_used": result.get('issue', {}).get('agent'),
                "result": result.get('result')
            }
        else:
            print(f"❌ Task failed: {result.get('error')}")
            return {
                "status": "failed", 
                "issue_number": issue_number,
                "error": result.get('error')
            }

    def create_github_issue(self, task_description: str) -> int:
        """
        Create GitHub issue with task description.
        
        Returns issue number if successful, None if failed.
        """
        try:
            # Use GitHub CLI to create issue
            cmd = [
                "gh", "issue", "create",
                "--title", f"Agent Task: {task_description[:50]}...",
                "--body", f"Task: {task_description}\n\nCreated by YourProjectAgent"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Extract issue number from output
                # gh creates output like: "https://github.com/org/repo/issues/123"
                output = result.stdout.strip()
                issue_number = int(output.split("/")[-1])
                print(f"📝 Created GitHub issue #{issue_number}")
                return issue_number
            else:
                print(f"❌ Failed to create GitHub issue: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating GitHub issue: {e}")
            return None

    def get_repo_name(self) -> str:
        """Get current repository name in org/repo format."""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                if "github.com" in url:
                    parts = url.split("/")[-2:]
                    return f"{parts[0]}/{parts[1].replace('.git', '')}"
        except:
            pass
        return "your-org/your-repo"  # Fallback
```

### B. Submit to Agents Helper (CORRECT PATTERN)

Create `scripts/submit_to_agents.py` in your project:

```python
#!/usr/bin/env python3
"""
CRITICAL: Sister Repository Issue Submission Script

This script enforces the CORRECT integration pattern:
- NEVER calls agents directly 
- ONLY submits GitHub issue numbers to ExternalIssueProcessor
- Lets Sparky orchestrate all agent routing and execution

Usage:
  python scripts/submit_to_agents.py 123  # Submit issue #123
  python scripts/submit_to_agents.py 456 --repo your-org/your-repo
"""

import argparse
import sys
import re
from pathlib import Path

# Import framework bridge  
sys.path.append(str(Path(__file__).parent.parent))
from utils.agent_bridge import get_framework_path, verify_framework_access

def validate_issue_number(issue_str: str) -> int:
    """
    Validate that input is a GitHub issue number (not a task description).
    
    Args:
        issue_str: Input string that should be an issue number
        
    Returns:
        int: Valid issue number
        
    Raises:
        ValueError: If input is not a valid issue number
    """
    # Remove common prefixes
    clean_str = issue_str.strip().replace("#", "").replace("issue", "").strip()
    
    if not clean_str.isdigit():
        raise ValueError(
            f"❌ INVALID INPUT: '{issue_str}' is not an issue number.\n"
            f"\n🚨 SISTER REPOSITORIES MUST ONLY SUBMIT ISSUE NUMBERS!\n"
            f"\n✅ CORRECT: python submit_to_agents.py 123"
            f"\n❌ WRONG:   python submit_to_agents.py 'fix the bug'"
            f"\n❌ WRONG:   Direct agent calls break Sparky orchestration!"
        )
    
    issue_num = int(clean_str)
    if issue_num <= 0:
        raise ValueError("Issue number must be positive")
        
    return issue_num

def detect_task_description(input_str: str) -> bool:
    """
    Detect if input looks like a task description rather than issue number.
    
    Returns True if input appears to be a task description.
    """
    # Common task description patterns
    task_indicators = [
        r'\b(fix|create|implement|update|add|remove|refactor|test)\b',
        r'\b(bug|feature|documentation|api|ui|database)\b', 
        r'\s+(the|a|an)\s+',  # Articles suggest descriptions
        r'[.!?]',  # Punctuation suggests sentences
        r'\s+.*\s+',  # Multiple words with spaces
    ]
    
    input_lower = input_str.lower()
    return any(re.search(pattern, input_lower) for pattern in task_indicators)

def submit_issue_to_sparky(issue_number: int, repo: str = None) -> bool:
    """
    Submit GitHub issue number to Sparky via ExternalIssueProcessor.
    
    Args:
        issue_number: GitHub issue number
        repo: Repository in format "org/repo" (optional)
    
    Returns:
        bool: True if submission succeeded
    """
    try:
        # Import ExternalIssueProcessor from framework
        framework_path = get_framework_path()
        sys.path.insert(0, str(framework_path))
        from core.github_integration import ExternalIssueProcessor
        
        processor = ExternalIssueProcessor()
        
        # Determine repository
        if not repo:
            # Try to auto-detect from git remote
            import subprocess
            try:
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"], 
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    # Extract org/repo from git URL
                    url = result.stdout.strip()
                    if "github.com" in url:
                        parts = url.split("/")[-2:]
                        repo = f"{parts[0]}/{parts[1].replace('.git', '')}"
            except:
                pass
        
        if not repo:
            repo = "current-repository"  # Fallback
            
        print(f"🚀 Submitting issue #{issue_number} from {repo} to Sparky")
        print(f"🤖 Sparky will determine agent routing and orchestration")
        
        # Submit to ExternalIssueProcessor
        result = processor.process_external_issue(repo, issue_number)
        
        if result.get("success"):
            print(f"✅ Issue #{issue_number} processed successfully")
            print(f"🎯 Agent used: {result.get('issue', {}).get('agent', 'Unknown')}")
            return True
        else:
            print(f"❌ Failed to process issue #{issue_number}")
            if result.get("error"):
                print(f"   Error: {result['error']}")
            return False
            
    except ImportError as e:
        print(f"❌ Framework integration error: {e}")
        print("   Make sure 12-factor-agents is set up as sister repository")
        return False
    except Exception as e:
        print(f"❌ Error submitting to Sparky: {e}")
        return False

def main():
    """
    Command-line interface enforcing issue-number-only pattern.
    """
    parser = argparse.ArgumentParser(
        description="Submit GitHub issue numbers to 12-factor-agents Sparky",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚨 CRITICAL: Sister repositories MUST only submit issue numbers!

✅ CORRECT Examples:
  python scripts/submit_to_agents.py 123
  python scripts/submit_to_agents.py 456 --repo your-org/your-repo
  python scripts/submit_to_agents.py "#789"

❌ WRONG Examples (will be rejected):
  python scripts/submit_to_agents.py "fix the bug"      # Task description
  python scripts/submit_to_agents.py "create feature"   # Task description
  
Integration Pattern:
  1. Create GitHub issue in your repository  
  2. Submit ONLY the issue number to this script
  3. Sparky orchestrates agent selection and execution
  4. Never call agents directly - breaks orchestration!
        """
    )
    
    parser.add_argument("issue", help="GitHub issue number (REQUIRED)")
    parser.add_argument("--repo", "-r", help="Repository in format 'org/repo'")
    parser.add_argument("--verify", "-v", action="store_true", help="Verify framework access")
    
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
        print("🤖 ExternalIssueProcessor integration ready")
        return 0
    
    # Validate input is an issue number (not task description)
    try:
        if detect_task_description(args.issue):
            print(f"❌ DETECTED TASK DESCRIPTION: '{args.issue}'")
            print(f"\n🚨 SISTER REPOSITORIES CANNOT SUBMIT TASK DESCRIPTIONS!")
            print(f"\n✅ CORRECT PATTERN:")
            print(f"   1. Create GitHub issue with your task description")
            print(f"   2. Submit the issue NUMBER: python submit_to_agents.py 123")
            print(f"   3. Let Sparky orchestrate agent selection")
            print(f"\n❌ Direct agent calls break the entire framework!")
            return 1
            
        issue_number = validate_issue_number(args.issue)
        
    except ValueError as e:
        print(str(e))
        return 1
    
    # Submit issue number to Sparky
    success = submit_issue_to_sparky(issue_number, args.repo)
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

## Project-Specific Examples (CORRECT PATTERNS)

### Pin-Citer Integration

For citation management projects like pin-citer:

```python
# pin_citer/agents/citation_agent.py
from utils.agent_bridge import get_framework_path
import sys
sys.path.insert(0, str(get_framework_path()))
from core.github_integration import ExternalIssueProcessor
from core.agent import BaseAgent

class PinCiterAgent(BaseAgent):
    """
    CORRECT: Citation processing using issue-orchestration pattern.
    """
    
    def __init__(self):
        super().__init__(agent_id="pin_citer_agent")
        self.external_processor = ExternalIssueProcessor()
    
    async def process_citations(self, document_path: str) -> dict:
        """
        Process citations using CORRECT orchestration pattern.
        
        Steps:
        1. Create GitHub issue with citation analysis request
        2. Submit issue number to Sparky
        3. Let Sparky route to appropriate agent
        """
        
        # Create GitHub issue for citation analysis
        issue_number = self.create_citation_issue(document_path)
        
        if not issue_number:
            return {"status": "failed", "error": "Could not create GitHub issue"}
        
        # Submit to Sparky for orchestration
        result = self.external_processor.process_external_issue(
            repo="your-org/pin-citer",
            issue_number=issue_number
        )
        
        return {
            "status": "completed" if result.get("success") else "failed",
            "issue_number": issue_number,
            "document": document_path,
            "agent_used": result.get('issue', {}).get('agent'),
            "sparky_handled": True  # Key indicator of correct pattern
        }
    
    def create_citation_issue(self, document_path: str) -> int:
        """Create GitHub issue for citation processing."""
        # Implementation to create GitHub issue
        # Returns issue number
        pass
```

### Cite-Assist Integration

For legal document processing projects:

```python
# cite_assist/agents/legal_agent.py
from utils.agent_bridge import get_framework_path
import sys
sys.path.insert(0, str(get_framework_path()))
from core.github_integration import ExternalIssueProcessor
from core.agent import BaseAgent

class LegalCitationAgent(BaseAgent):
    """
    CORRECT: Legal citation processing using issue-orchestration pattern.
    """
    
    def __init__(self):
        super().__init__(agent_id="legal_citation_agent")
        self.external_processor = ExternalIssueProcessor()
    
    async def process_legal_document(self, case_file: str) -> dict:
        """
        Process legal documents using CORRECT orchestration pattern.
        
        Never calls agents directly - always creates issues first.
        """
        
        # Create detailed GitHub issue for legal citation analysis
        issue_title = f"Legal Citation Analysis: {case_file}"
        issue_body = f"""
        Analyze legal citations and format according to Bluebook rules in {case_file}
        
        Requirements:
        - Validate all case citations
        - Check citation format compliance
        - Ensure proper legal citation structure
        - Generate correction recommendations
        """
        
        issue_number = self.create_legal_issue(issue_title, issue_body)
        
        # Submit to Sparky (never call agents directly!)
        result = self.external_processor.process_external_issue(
            repo="your-org/cite-assist", 
            issue_number=issue_number
        )
        
        return {
            "status": "orchestrated_via_sparky",
            "issue_number": issue_number,
            "case_file": case_file,
            "framework_handles_execution": True
        }
```

### Development Project Integration

For software development projects:

```python
# dev_project/agents/code_agent.py
from utils.agent_bridge import get_framework_path
import sys
sys.path.insert(0, str(get_framework_path()))
from core.github_integration import ExternalIssueProcessor
from core.agent import BaseAgent

class CodeAnalysisAgent(BaseAgent):
    """
    CORRECT: Code analysis using issue-orchestration pattern.
    """
    
    def __init__(self):
        super().__init__(agent_id="code_analysis_agent")
        self.external_processor = ExternalIssueProcessor()
    
    async def analyze_codebase(self, repo_path: str) -> dict:
        """
        Analyze codebase using CORRECT orchestration pattern.
        
        Creates comprehensive GitHub issue and lets Sparky handle routing.
        """
        
        # Create comprehensive GitHub issue
        issue_body = f"""
        Comprehensive codebase analysis for {repo_path}
        
        Analysis Requirements:
        - Code quality assessment
        - Security vulnerability scan  
        - Performance bottleneck identification
        - Test coverage analysis
        - Documentation completeness review
        
        Let Sparky determine which specialized agents handle each aspect.
        """
        
        issue_number = self.create_analysis_issue(repo_path, issue_body)
        
        # Submit to Sparky for intelligent agent routing
        result = self.external_processor.process_external_issue(
            repo="your-org/dev-project",
            issue_number=issue_number
        )
        
        return {
            "status": "submitted_to_sparky",
            "issue_number": issue_number,
            "repository": repo_path,
            "orchestration_complete": result.get("success", False),
            "agents_called_directly": False  # This should ALWAYS be False!
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

### CRITICAL: Integration Pattern Issues

#### ❌ Issue: "My agents aren't working correctly"

**Symptoms:**
- Inconsistent results
- Missing context
- Broken dependencies
- Poor error handling

**Root Cause:** Calling agents directly instead of using orchestration

**Solution:**
```python
# ❌ WRONG - Direct agent calls
run_framework_agent("SmartIssueAgent", "task description")

# ✅ CORRECT - Issue orchestration  
processor = ExternalIssueProcessor()
result = processor.process_external_issue("your-repo", 123)
```

#### ❌ Issue: "Sister repo integration is unreliable"

**Symptoms:**
- Random failures
- Inconsistent behavior
- Missing telemetry data

**Root Cause:** Bypassing Sparky orchestration

**Solution:**
1. Always create GitHub issues first
2. Submit issue numbers (not descriptions)
3. Let Sparky handle all agent routing
4. Never call `bin/agent.py run` directly

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

## Advanced Integration Patterns (CORRECT)

### Pattern 1: Batch Issue Processing

```python
import asyncio
from utils.agent_bridge import get_framework_path
import sys
sys.path.insert(0, str(get_framework_path()))
from core.github_integration import ExternalIssueProcessor

class BatchIssueProcessor:
    """
    CORRECT: Process multiple GitHub issues via Sparky orchestration.
    Never calls agents directly.
    """
    
    def __init__(self, repo: str):
        self.repo = repo
        self.external_processor = ExternalIssueProcessor()
    
    async def process_issue_batch(self, issue_numbers: List[int]) -> List[Dict]:
        """Process multiple issues through Sparky orchestration."""
        tasks = []
        
        for issue_number in issue_numbers:
            task = self._create_issue_task(issue_number)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def _create_issue_task(self, issue_number: int):
        """Create async task for issue processing via Sparky."""
        return await asyncio.to_thread(
            self.external_processor.process_external_issue,
            self.repo, 
            issue_number
        )
```

### Pattern 2: Issue Status Monitoring

```python
from utils.agent_bridge import get_framework_path
import sys
sys.path.insert(0, str(get_framework_path()))
from core.github_integration import ExternalIssueProcessor

class IssueStatusMonitor:
    """
    CORRECT: Monitor issue processing through GitHub API.
    Uses only orchestration pattern.
    """
    
    def __init__(self, repo: str):
        self.repo = repo
        self.external_processor = ExternalIssueProcessor()
    
    def submit_and_monitor(self, issue_number: int) -> Dict:
        """Submit issue to Sparky and monitor progress."""
        
        print(f"🚀 Submitting issue #{issue_number} to Sparky")
        
        # Submit via ExternalIssueProcessor (CORRECT way)
        result = self.external_processor.process_external_issue(
            self.repo, issue_number
        )
        
        if result.get("success"):
            print(f"✅ Issue #{issue_number} processed successfully")
            return {
                "status": "completed",
                "issue_number": issue_number,
                "agent_used": result.get('issue', {}).get('agent'),
                "orchestrated_by_sparky": True
            }
        else:
            print(f"❌ Issue processing failed: {result.get('error')}")
            return {
                "status": "failed",
                "issue_number": issue_number,
                "error": result.get('error'),
                "orchestrated_by_sparky": True
            }
```

### Pattern 3: Multi-Repository Coordination

```python
from typing import List, Dict
from utils.agent_bridge import get_framework_path
import sys
sys.path.insert(0, str(get_framework_path()))
from core.github_integration import ExternalIssueProcessor

class MultiRepoCoordinator:
    """
    CORRECT: Coordinate issues across multiple repositories.
    All processing goes through Sparky orchestration.
    """
    
    def __init__(self):
        self.external_processor = ExternalIssueProcessor()
    
    async def coordinate_cross_repo_issues(self, repo_issues: List[Dict]) -> List[Dict]:
        """
        Process issues across multiple repositories via Sparky.
        
        Args:
            repo_issues: List of {"repo": "org/repo", "issue": 123}
        """
        tasks = []
        
        for config in repo_issues:
            task = self._create_cross_repo_task(
                config["repo"], 
                config["issue"]
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def _create_cross_repo_task(self, repo: str, issue_number: int):
        """Create task for cross-repo issue processing."""
        return await asyncio.to_thread(
            self.external_processor.process_external_issue,
            repo,
            issue_number
        )
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

This integration guide provides the CORRECT pattern for sister repositories to integrate with 12-factor-agents. The critical components are:

## 🚨 REMEMBER: Issue-Orchestration Pattern ONLY

**NEVER call agents directly. ALWAYS use GitHub issues + Sparky orchestration.**

### Key Integration Components:

1. **GitHub Issues First**: Always create GitHub issues with task descriptions
2. **ExternalIssueProcessor**: Submit issue numbers (not descriptions) to Sparky  
3. **Agent Bridge**: Copy `utils/agent_bridge.py` for framework access
4. **Correct Submit Script**: Use updated `scripts/submit_to_agents.py` with validation
5. **Integration Tests**: Verify orchestration pattern works correctly

### The ONLY Correct Pattern:
```python
# 1. Create GitHub issue (with gh CLI or GitHub web interface)
# 2. Submit issue number to Sparky
from core.github_integration import ExternalIssueProcessor
processor = ExternalIssueProcessor()
result = processor.process_external_issue("your-org/your-repo", 123)
```

### What This Fixes:
- **Sister repo confusion**: Clear distinction between direct calls (wrong) vs orchestration (right)
- **Broken integrations**: pin-citer and other repos were calling agents directly
- **Missing context**: Sparky provides full issue context and intelligent routing
- **Poor error handling**: Direct calls skip comprehensive error recovery
- **No telemetry**: Direct calls break monitoring and analytics

**Next Steps:**
1. Copy the corrected agent bridge to your project
2. Use the validated submit script that prevents direct calls
3. Create GitHub issues for all tasks  
4. Submit issue numbers (not task descriptions) to ExternalIssueProcessor
5. Let Sparky handle all agent routing and execution

**Critical Reminder**: If you're calling `run_framework_agent()` or `bin/agent.py run` directly, you're doing it wrong. Create GitHub issues and submit the numbers to Sparky instead.

For additional examples, see the corrected patterns throughout this document.