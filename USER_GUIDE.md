# 12-Factor Agents User Guide - Intelligent System

## For Sister Repositories (pin-citer, cite-assist, etc.)

**You already have the new intelligent system!** Your symlinks automatically point to our latest code. No updates needed on your end.

## Prerequisites

This system uses **uv** for Python management, which provides:
- ✅ **Fast execution** - Much faster than traditional Python
- ✅ **Automatic dependency management** - No virtual env setup needed
- ✅ **Consistent environments** - Same Python version everywhere
- ✅ **Direct script execution** - `uv run` handles everything

Install uv if you don't have it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## How It Works

Your symlinks give you everything:
```
your-project/.agents/
  ├── agents -> ../../12-factor-agents/agents  # Automatically includes IntelligentIssueAgent
  ├── core -> ../../12-factor-agents/core      # All core functionality
  └── framework -> ../../12-factor-agents      # Everything
```

When we update 12-factor-agents, you instantly get the updates. No pulling, no updating - it just works!

## Using the Intelligent Agent

### Simple Example

Create a file `test_intelligent_agent.py` in your project:

```python
#!/usr/bin/env uv run python
"""Test the new intelligent agent system"""

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

## What the Intelligent Agent Does

1. **Understands Natural Language** - Just describe what you want
2. **Extracts Intent** - Knows if you want to fix, create, update, etc.
3. **Identifies Files** - Finds file paths in your description
4. **Determines Complexity** - Simple tasks run directly, complex tasks are parallelized
5. **Routes to Tools** - Uses FileTool for files, Orchestrator for parallel work

## No Configuration Needed

Your existing symlinks already provide:
- ✅ `IntelligentIssueAgent` - The new smart layer
- ✅ `FileTool` - File operations
- ✅ `HierarchicalOrchestrator` - Parallel execution
- ✅ All other agents - Still available

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
    print("   Make sure your symlinks point to 12-factor-agents")
```

Run it:
```bash
uv run verify_intelligent_system.py
```

## Quick Commands Reference

All commands use **uv** for optimal performance:

### Test the system:
```bash
uv run verify_intelligent_system.py
```

### Process a single issue:
```bash
uv run -c "
from agents.intelligent_issue_agent import IntelligentIssueAgent
agent = IntelligentIssueAgent()
result = agent.execute_task('Fix the broken citation in paper.md')
print(f'Success: {result.success}')
"
```

### Run the full orchestrator:
```bash
cd /path/to/12-factor-agents
uv run agents/issue_orchestrator_agent.py
```

### Create and run a custom script:
```bash
# Create your script with #!/usr/bin/env uv run python
# Then just run it directly:
uv run your_script.py
```

## Why uv?

- 🚀 **10-100x faster** than pip/python
- 🔧 **Zero configuration** - Just works
- 📦 **Automatic dependencies** - No virtual envs needed
- ✅ **Consistent execution** - Same environment everywhere
- 🎯 **Modern Python** - Always uses current stable version

## That's It!

No setup, no configuration, no updates needed. Your symlinks give you everything automatically. Just use `uv run` and the intelligent agent!

---

**Remember**: When we update 12-factor-agents, you get the improvements instantly through your symlinks. Zero deployment with maximum performance through uv!