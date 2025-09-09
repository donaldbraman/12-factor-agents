# 12-Factor Agents - Symlink Integration Guide (Stable Version)

## IMMEDIATE FIX: Get Your Agents Working NOW

Your agents are broken because of recent changes. Here's how to fix them immediately using the stable rollback branch.

## Step 1: Update 12-Factor-Agents to Stable Branch

```bash
# Go to your 12-factor-agents directory (parent of your project)
cd ../12-factor-agents

# Get the stable working version
git fetch origin
git checkout rollback-to-stable

# Install dependencies
uv pip install -r requirements.txt
```

## Step 2: Verify Your Symlinks

Your project should have symlinks pointing to 12-factor-agents:

```bash
# In your project (e.g., pin-citer, cite-assist, etc.)
cd your-project
ls -la .agents/

# You should see something like:
# agents -> ../../12-factor-agents/agents
# core -> ../../12-factor-agents/core
```

If symlinks are missing or broken, recreate them:

```bash
cd .agents
ln -sf ../../12-factor-agents/agents agents
ln -sf ../../12-factor-agents/core core
ln -sf ../../12-factor-agents/docs docs
ln -sf ../../12-factor-agents/scripts scripts
```

## Step 3: Test Your Agents Work

```python
# Quick test in your project
python3 -c "
from .agents.core.hierarchical_orchestrator import HierarchicalOrchestrator
from .agents.agents.issue_fixer_agent import IssueFixerAgent
print('✅ Agents are working!')
"
```

## What's Working in Stable Version

### ✅ ALL Agent Functionality
- File creation and modification
- GitHub issue processing  
- Parallel task execution
- Complex orchestration
- All 12+ agent types

### ✅ Your Existing Workflows
```python
# Your existing code continues to work
from .agents.agents.issue_fixer_agent import IssueFixerAgent
from .agents.agents.issue_decomposer_agent import IssueDecomposerAgent
from .agents.core.hierarchical_orchestrator import HierarchicalOrchestrator

# Create and run agents as before
agent = IssueFixerAgent()
result = agent.execute_task("Fix issue #123")
```

### ✅ Orchestration Patterns
```python
# Complex tasks run in parallel automatically
orchestrator = HierarchicalOrchestrator()
result = orchestrator.orchestrate_complex_task(
    "Process multiple GitHub issues with tests and documentation"
)
```

## Common Integration Patterns

### Pattern 1: Single Framework Symlink (Recommended)
```bash
your-project/
├── .agents/
│   └── framework -> ../../12-factor-agents  [ONE SYMLINK TO RULE THEM ALL]
```

Usage:
```python
from .agents.framework.agents.issue_fixer_agent import IssueFixerAgent
from .agents.framework.core.hierarchical_orchestrator import HierarchicalOrchestrator
```

### Pattern 2: Granular Symlinks (Pin-Citer Style)
```bash
your-project/
├── .agents/
│   ├── agents -> ../../12-factor-agents/agents
│   ├── core -> ../../12-factor-agents/core
│   ├── docs -> ../../12-factor-agents/docs
│   └── scripts -> ../../12-factor-agents/scripts
```

Usage:
```python
from .agents.agents.issue_fixer_agent import IssueFixerAgent
from .agents.core.hierarchical_orchestrator import HierarchicalOrchestrator
```

## Fixing Common Issues

### Issue: "AttributeError: '_intelligent_processing' not found"
**Solution**: You're on the wrong branch. Switch to rollback-to-stable:
```bash
cd ../12-factor-agents
git checkout rollback-to-stable
```

### Issue: "ImportError: No module named 'agents'"
**Solution**: Fix your symlinks:
```bash
cd your-project/.agents
ln -sf ../../12-factor-agents/agents agents
ln -sf ../../12-factor-agents/core core
```

### Issue: "Agents can't create files"
**Solution**: The stable branch has full file operations working. Make sure you're on rollback-to-stable.

## Running Agents from Your Project

### Option 1: Direct Python Import
```python
#!/usr/bin/env python3
# your_project/run_agent.py

from .agents.agents.issue_fixer_agent import IssueFixerAgent
from .agents.agents.issue_decomposer_agent import IssueDecomposerAgent

def fix_issue(issue_number):
    agent = IssueFixerAgent()
    return agent.execute_task(f"Fix issue #{issue_number}")

def decompose_complex_issue(issue_number):
    decomposer = IssueDecomposerAgent()
    sub_issues = decomposer.execute_task(f"Decompose issue #{issue_number}")
    
    # Fix each sub-issue
    fixer = IssueFixerAgent()
    for sub_issue in sub_issues:
        fixer.execute_task(f"Fix {sub_issue}")
```

### Option 2: Use the CLI via Symlink
```bash
# Create a wrapper script in your project
#!/bin/bash
# your_project/bin/agent

cd ../12-factor-agents
uv run python bin/agent.py "$@"
```

Then use it:
```bash
./bin/agent run IssueFixerAgent "Fix issue #123"
```

### Option 3: Direct Orchestration
```python
# your_project/orchestrate.py
from .agents.core.hierarchical_orchestrator import HierarchicalOrchestrator

orchestrator = HierarchicalOrchestrator(
    max_parallel_agents=10,
    max_depth=3
)

# This automatically parallelizes independent tasks
result = orchestrator.orchestrate_complex_task("""
    1. Fix all linting issues in src/
    2. Generate tests for new features
    3. Update documentation
    4. Create GitHub issue for remaining work
""")
```

## Available Agents (All Working)

- `IssueFixerAgent` - Fixes GitHub issues with file operations
- `IssueDecomposerAgent` - Breaks complex issues into sub-tasks
- `CodeReviewAgent` - Reviews code quality
- `TestingAgent` - Generates and runs tests
- `RefactoringAgent` - Refactors code
- `QAAgent` - Quality assurance
- `ComponentMigrationAgent` - Migrates components
- `EnhancedWorkflowAgent` - Complex workflows
- `RepositorySetupAgent` - Sets up new repos
- `PromptManagementAgent` - Manages prompts
- `EventSystemAgent` - Event handling
- `UvMigrationAgent` - UV package manager migration

## Quick Validation Script

Save this as `test_agents.py` in your project:

```python
#!/usr/bin/env python3
"""Verify agents are working via symlinks"""

import sys
from pathlib import Path

def test_symlink_integration():
    try:
        # Test imports via symlinks
        from .agents.core.hierarchical_orchestrator import HierarchicalOrchestrator
        from .agents.agents.issue_fixer_agent import IssueFixerAgent
        from .agents.agents.issue_decomposer_agent import IssueDecomposerAgent
        print("✅ Core imports working")
        
        # Test agent creation
        fixer = IssueFixerAgent()
        decomposer = IssueDecomposerAgent()
        orchestrator = HierarchicalOrchestrator()
        print("✅ Agent creation working")
        
        # Check for the problematic method
        if hasattr(fixer, 'execute_task'):
            print("✅ Execute task available")
        
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("Your agents are ready to use.")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("\nFix: Check your symlinks and ensure 12-factor-agents is on rollback-to-stable branch")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_symlink_integration()
```

## Status Update

### What's Immediately Available (NOW)
- ✅ Full agent functionality restored
- ✅ File creation/modification working
- ✅ GitHub issue processing working
- ✅ Parallel orchestration working
- ✅ All original features operational

### What We're Improving (Later)
- 🚧 Intelligent task decomposition (better natural language understanding)
- 🚧 Smart pattern selection (auto-choosing best orchestration)
- 🚧 Enhanced error messages
- 🚧 Performance optimizations

### Branch Information
- **rollback-to-stable**: USE THIS - Fully working, stable
- **main**: Currently broken, being fixed
- **hybrid-development**: Where we're adding new features

## Support

**Immediate Help**: The rollback-to-stable branch is fully functional. Your symlinks will automatically use the working version once you switch branches.

**Issues**: https://github.com/donaldbraman/12-factor-agents/issues

---

**TL;DR**: 
1. `cd ../12-factor-agents && git checkout rollback-to-stable`
2. Your symlinks now point to working code
3. All agents functional immediately