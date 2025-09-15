# 12-Factor Agents User Guide

A comprehensive guide for using the 12-Factor Agents framework for intelligent issue resolution and agent system management.

## Table of Contents
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Using the Intelligent System](#using-the-intelligent-system)
- [Sister Repository Integration](#sister-repository-integration)
- [CLI Commands Reference](#cli-commands-reference)
- [Background Research Agents](#background-research-agents)
- [Examples by Project Type](#examples-by-project-type)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

This system uses **uv** for Python management, which provides:
- ✅ **Fast execution** - Much faster than traditional Python
- ✅ **Automatic dependency management** - No virtual env setup needed
- ✅ **Consistent environments** - Same Python version everywhere
- ✅ **Direct script execution** - `uv run` handles everything

Install uv if you don't have it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 30-Second Start

```bash
# Submit ANY issue - complexity detection is automatic
cd /path/to/12-factor-agents
uv run python bin/agent.py run SmartIssueAgent "issue-number"
```

**That's it.** The system handles everything else automatically.

## Installation

1. Run setup: `./setup.sh`
2. Clone/place the framework as a sister repository to your projects
3. Run agents: `uv run python ../12-factor-agents/bin/agent.py <name> "<task>"`

## Using the Intelligent System

### How It Works

When you submit an issue, SmartIssueAgent:
1. **Analyzes complexity** (atomic → enterprise)  
2. **Routes intelligently** (direct handling vs decomposition)
3. **Creates 12-Factor compliant sub-issues** if needed
4. **Assigns appropriate agents** automatically
5. **Orchestrates execution** across all sub-tasks

You never think about which agent to use or how complex your issue is.

### What the Intelligent Agent Does

1. **Understands Natural Language** - Just describe what you want
2. **Extracts Intent** - Knows if you want to fix, create, update, etc.
3. **Identifies Files** - Finds file paths in your description
4. **Determines Complexity** - Simple tasks run directly, complex tasks are parallelized
5. **Routes to Tools** - Uses FileTool for files, Orchestrator for parallel work

### Real Examples by Complexity

#### Atomic (Handled Directly)
```bash
# Simple typo fix
uv run python bin/agent.py run SmartIssueAgent "088"
```
**Output:** Direct fix applied immediately.

#### Simple (Handled Directly)  
```bash
# Single file update
uv run python bin/agent.py run SmartIssueAgent "086"
```
**Output:** File updated, task completed.

#### Moderate (Auto-Decomposed)
```bash
# Multi-file changes
uv run python bin/agent.py run SmartIssueAgent "083" 
```
**Output:** 
```
🧩 Issue decomposed into 3 sub-issues
🚀 Processing sub-issues...
   ✅ Update testing_agent.py
   ✅ Update benchmarks.py  
   ✅ Update test.yml
📊 Overall result: 3/3 sub-issues completed
```

#### Complex (Auto-Decomposed)
```bash
# Documentation overhaul with numbered sections
uv run python bin/agent.py run SmartIssueAgent "064"
```
**Output:**
```
🔍 Analyzing complexity...
📊 Complexity: complex (confidence: 80.0%)
🧩 Issue decomposed into 4 sub-issues
   📋 Fix CLI Commands in README
   📋 Fix Pipeline Example in INTEGRATION-GUIDE.md  
   📋 Add Complete Imports Section
   📋 Add IssueFixerAgent Documentation
```

#### Enterprise (Auto-Decomposed)
```bash  
# System-wide changes
uv run python bin/agent.py run SmartIssueAgent "080"
```
**Output:** 
```
📊 Complexity: enterprise (confidence: 90.0%)
🧩 Issue decomposed into 6 sub-issues
   📋 Create Core framework foundation
   📋 Implement Database schema changes
   📋 Design and implement API redesign
   [... 3 more focused tasks]
```

## Sister Repository Integration

The 12-Factor Agents framework works as a sister repository alongside your project repos, accessing them via relative paths from your mutual parent directory.

### Directory Structure
```
parent-directory/
├── 12-factor-agents/     # Main framework
├── your-project-1/       # Sister repo 1
├── your-project-2/       # Sister repo 2
└── other-projects/       # Other sister repos
```

### For Sister Repositories (pin-citer, cite-assist, etc.)

**You already have the new intelligent system!** The relative path integration automatically provides access to our latest code. No updates needed on your end.

The framework gives you everything:
```
parent-directory/
  ├── 12-factor-agents/  # Framework with IntelligentIssueAgent and all core functionality
  └── your-project/      # Your project automatically accesses framework via relative paths
  └── framework -> ../../12-factor-agents      # Everything
```

When we update 12-factor-agents, you instantly get the updates. No pulling, no updating - it just works!

### Integration Methods

#### Method 1: Direct Relative Path Access
```bash
# From your project directory
cd /path/to/parent-directory/your-project

# Run framework on your issues
uv run python ../12-factor-agents/bin/agent.py run IntelligentIssueAgent "Process issue #123"
```

#### Method 2: Symlink Setup (Recommended)
```bash
cd /path/to/your-project

# Verify framework is accessible
ls ../12-factor-agents

# Test it works
uv run python ../12-factor-agents/bin/agent.py list
```

## CLI Commands Reference

### Basic Commands
```bash
# List all available agents
uv run python bin/agent.py list

# Get detailed information about an agent
uv run python bin/agent.py info SmartIssueAgent

# Run an agent with a task
uv run python bin/agent.py run AgentName "task description"

# Run orchestration pipelines
uv run python bin/agent.py orchestrate issue-pipeline
```

### Sister Repository Commands
```bash
# From sister repo - use framework to process your issues
cd /path/to/parent-directory/your-project
uv run python ../12-factor-agents/bin/agent.py run IntelligentIssueAgent "Process issue #123"
uv run python ../12-factor-agents/bin/agent.py run SmartIssueAgent "123"  # Auto-decomposition

# From framework directory itself
cd /path/to/parent-directory/12-factor-agents
uv run python bin/agent.py run AgentName "task" # Execute agent
```

### Testing Commands
```bash
# Run full test suite (from framework directory)
make test

# Quick validation
make quick-test

# Format code
make format

# Lint code
make lint
```

## Background Research Agents

### Launch True Parallel Research
The system can now spawn research agents that run **completely in the background** without blocking:

```bash
# Launch background research (returns immediately!)
/path/to/12-factor-agents/bin/launch_background.sh "research topic"

# Returns:
# TASK_ID:research_20250910_070253_4841
# CHECK:cat /tmp/12-factor-agents-background/research_..._status.json
# RESULTS:cat /tmp/12-factor-agents-background/research_..._output.json
```

### Using BackgroundResearchAgent

```python
# From Python/Claude
from agents.background_research_agent import BackgroundResearchAgent

agent = BackgroundResearchAgent()
result = agent.execute("Research quantum computing applications")
# Returns immediately with task_id

# Check status later
status = agent.check_status(result["task_id"])

# Get results when complete
findings = agent.get_results(result["task_id"])
```

### Command Line Usage

```bash
# Launch research
uv run python agents/background_research_agent.py launch --task "research AI safety"

# Check status
uv run python agents/background_research_agent.py status --task-id research_20250910_070253_4841

# Get results
uv run python agents/background_research_agent.py results --task-id research_20250910_070253_4841

# List all active research
uv run python agents/background_research_agent.py list
```

### Key Features
- **Fire-and-forget**: Launches and returns immediately
- **True parallelism**: Run 10+ research agents simultaneously  
- **No blocking**: System stays responsive during research
- **Persistent results**: Findings stored in `/tmp/12-factor-agents-background/`
- **Multiple launch methods**: Uses disown, nohup, screen, or at

## Examples by Project Type

### Simple Example

Create a file `test_intelligent_agent.py` in your project:

```python
#!/usr/bin/env uv run python
"""Test the intelligent agent system"""

import sys
sys.path.insert(0, '.agents')

from agents.intelligent_issue_agent import IntelligentIssueAgent

# Create the intelligent agent
agent = IntelligentIssueAgent()

# Example 1: Process a GitHub issue
result = agent.execute_task("Fix issue #123")
print(f"Result: {result.success}")

# Example 2: Create files using natural language
result = agent.execute_task("Create a configuration file at config/settings.yaml")

# Example 3: Process a local issue file
with open("test_issue.md", "w") as f:
    f.write("""
    # Bug Report
    Fix the authentication bug in src/auth.py
    Add tests for the login function
    Update README.md with the changes
    """)

result = agent.execute_task("Process test_issue.md")
print(f"Processed: {result.success}")
```

Run it:
```bash
uv run test_intelligent_agent.py
```

### Real-World Example for pin-citer

```python
#!/usr/bin/env uv run python
"""Process citations with intelligent understanding"""

import sys
sys.path.insert(0, '.agents')

from agents.intelligent_issue_agent import IntelligentIssueAgent

def process_citation_request(request_text):
    """
    Process natural language citation requests
    
    Examples:
        "Fix formatting issues in references.bib"
        "Create a new citation template at templates/apa.yaml"
        "Update all citations in chapter-3.md and add missing DOIs"
    """
    agent = IntelligentIssueAgent()
    
    # The agent understands natural language!
    result = agent.execute_task(request_text)
    
    if result.success:
        print(f"✅ Completed: {request_text}")
        if result.data:
            # Check what the agent understood
            intent = result.data.get('intent', {})
            print(f"   Actions taken: {intent.get('actions', [])}")
            print(f"   Files affected: {intent.get('files_mentioned', [])}")
    else:
        print(f"❌ Failed: {result.error}")
    
    return result

# Example usage
if __name__ == "__main__":
    # Process various citation tasks
    tasks = [
        "Fix the broken citation in paper.md",
        "Create a bibliography file at refs/sources.bib",
        "Update all citations in the manuscript folder"
    ]
    
    for task in tasks:
        process_citation_request(task)
```

### Real-World Example for cite-assist

```python
#!/usr/bin/env uv run python
"""Legal document processing with intelligence"""

import sys
sys.path.insert(0, '.agents')

from agents.intelligent_issue_agent import IntelligentIssueAgent

class LegalDocumentProcessor:
    def __init__(self):
        self.agent = IntelligentIssueAgent()
    
    def process_legal_request(self, request):
        """
        Handle legal document requests in natural language
        
        Examples:
            "Create a contract template at templates/nda.md"
            "Fix citations in brief.docx"
            "Review and update all case references in chapter-2"
        """
        # Create an issue file for complex requests
        issue_path = "temp_legal_issue.md"
        with open(issue_path, "w") as f:
            f.write(f"# Legal Document Request\n\n{request}")
        
        # Process with intelligence
        result = self.agent.execute_task(f"Handle {issue_path}")
        
        # The agent automatically:
        # - Understands the request
        # - Identifies files mentioned
        # - Determines if tasks can run in parallel
        # - Routes to appropriate tools
        
        return result

# Example usage
processor = LegalDocumentProcessor()

# Complex multi-step request - automatically parallelized!
result = processor.process_legal_request("""
    Fix all citation formatting in the Smith v. Jones brief.
    Create a summary document at summaries/smith-jones.md.
    Update the case index with new page numbers.
""")

if result.success:
    print("✅ Legal documents processed successfully")
    # Check if it ran in parallel
    if result.data.get('parallel_execution'):
        print("   Tasks were automatically parallelized for speed!")
```

## Understanding Results

### Success (Direct Handling)
```
✅ Issue is simple - handling directly
✅ Task completed successfully
```
→ **Done.** Your issue was fixed immediately.

### Success (Decomposed)
```
🧩 Issue decomposed into N sub-issues
📊 Overall result: N/N sub-issues completed  
✅ Complex issue orchestrated successfully
```
→ **Done.** All sub-tasks completed successfully.

### Partial Success
```
📊 Overall result: 2/4 sub-issues completed
❌ Some sub-issues failed
```
→ **Check the details.** Some tasks succeeded, others need attention.

## Writing Issues That Decompose Well

### ✅ Good Issue Structure
```markdown
# Issue: Update Documentation with Correct Usage

## Description  
Multiple files need updates to fix CLI commands.

### 1. Fix CLI Commands in README
Current:
```bash
uv run agent list
```

Should be:
```bash  
uv run python bin/agent.py list
```

### 2. Update Integration Guide
Add missing imports to all examples.

## Files to Update
- README.md
- docs/INTEGRATION-GUIDE.md
```

**Why this works:**
- Numbered sections → automatic sub-issue creation
- Current/Should patterns → actionable changes  
- Explicit file lists → clear targets
- Specific requirements → executable tasks

### ❌ Poor Issue Structure  
```markdown
# Issue: Make everything better

Please improve the system somehow.
```

**Why this fails:**
- Vague requirements → no actionable tasks
- No specific files → unclear targets
- No current/should patterns → no clear changes

## Testing Your Setup

Quick test to verify everything works:

**Save as `verify_intelligent_system.py`:**

```python
#!/usr/bin/env uv run python
"""Verify intelligent system is available"""

import sys
sys.path.insert(0, '.agents')

try:
    from agents.intelligent_issue_agent import IntelligentIssueAgent
    agent = IntelligentIssueAgent()
    print("✅ Intelligent system is ready!")
    print(f"   Available tools: {[t.name for t in agent.tools]}")
    print(f"   Has orchestrator: {hasattr(agent, 'orchestrator')}")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("   Make sure 12-factor-agents is accessible at ../12-factor-agents")
```

Run it:
```bash
uv run verify_intelligent_system.py
```

## Troubleshooting

### Issue Not Found
```
❌ No issue file found for #123
```
→ **Check:** Issue file exists in `issues/` directory

### Agent Failed
```
❌ Task failed: Could not determine what changes to make
```  
→ **Fix:** Add more specific Current/Should code blocks to your issue

### Complexity Misdetection
```
📊 Complexity: enterprise (expected: simple)
```
→ **Normal:** System errs on the side of caution. Still handles correctly.

### Import Errors
→ **Solution:** Ensure 12-factor-agents is placed as a sister repository

### Agent Not Found
→ **Solution:** Check agent class name matches file name

### Checkpoint Failures
→ **Solution:** Verify CHECKPOINT_DIR exists and is writable

### Performance Issues
→ **Solution:** Use pipeline stages to parallelize work

### Test Failures
→ **Solution:** Run `make format` to fix formatting issues

## 12-Factor Principles Applied

SmartIssueAgent follows [12-Factor Agent](https://github.com/humanlayer/12-factor-agents) principles:

- **Factor 1**: Natural Language → Tool Calls (issue → actions)
- **Factor 4**: Structured Outputs (clear sub-issues)  
- **Factor 8**: Own Your Control Flow (explicit steps)
- **Factor 10**: Small, Focused Agents (atomic sub-tasks)
- **Factor 12**: Stateless Reducer (clear input/output)

This ensures reliable, predictable, production-ready agent behavior.

## Why uv?

- 🚀 **10-100x faster** than pip/python
- 🔧 **Zero configuration** - Just works
- 📦 **Automatic dependencies** - No virtual envs needed
- ✅ **Consistent execution** - Same environment everywhere
- 🎯 **Modern Python** - Always uses current stable version

## No Configuration Needed

The relative path integration already provides:
- ✅ `IntelligentIssueAgent` - The new smart layer
- ✅ `FileTool` - File operations
- ✅ `HierarchicalOrchestrator` - Parallel execution
- ✅ All other agents - Still available

## That's It!

No setup, no configuration, no updates needed. The relative path integration gives you everything automatically. Just use `uv run` and the intelligent agent!

**You now know everything needed to be productive with the 12-Factor Agents framework.**

Submit issues, get results. The system handles all complexity automatically.

---

**Remember**: When we update 12-factor-agents, you get the improvements instantly through the relative path integration. Zero deployment with maximum performance through uv!

*Built with 12-Factor Agent principles for production reliability.*