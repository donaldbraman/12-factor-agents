# Issue #188: uv --directory Command Can't Find Issues in Local Repository

## Description
When using the beautiful `uv run --directory agents-framework python bin/agent.py` command pattern, the agents can't find issues in the local repository's issues/ directory.

## Problem Found During New User Testing

### What Works ✅
- **Setup script**: Works perfectly, creates all files
- **Agent listing**: `uv run --directory agents-framework python bin/agent.py list` shows all agents
- **Agent info**: `uv run --directory agents-framework python bin/agent.py info SmartIssueAgent` works
- **Beautiful uv syntax**: Commands execute without errors

### What Doesn't Work ❌  
- **Issue processing**: `uv run --directory agents-framework python bin/agent.py run SmartIssueAgent "001"` fails
- **Error**: "No issue file found for #001" even though `issues/001-test-setup.md` exists
- **Path context**: Agent runs from agents-framework directory, looks for issues there

## Root Cause Analysis
```bash
# Current working directory context issue:
cd /tmp/new-repo
ls issues/001-test-setup.md  # ✅ File exists here

uv run --directory agents-framework python bin/agent.py run SmartIssueAgent "001" 
# ❌ Agent looks in agents-framework/issues/ instead of ../issues/
```

## Impact for New Users
- **Expectation**: Beautiful uv commands should work as documented  
- **Reality**: Commands execute but can't find local repository issues
- **User experience**: Confusion - "Why can't it find my issue files?"
- **Workflow broken**: Can't actually process any issues despite perfect setup

## Current vs Required

### Current Behavior
```bash
# User runs from repo root
uv run --directory agents-framework python bin/agent.py run SmartIssueAgent "001"
# Agent searches: agents-framework/issues/001*.md (❌ doesn't exist)
```

### Required Behavior  
```bash
# User runs from repo root
uv run --directory agents-framework python bin/agent.py run SmartIssueAgent "001"
# Agent searches: ../issues/001*.md (✅ should find local repo issues)
```

## Technical Solutions

### Option 1: Fix Agent Path Resolution
Update agents to detect when running with --directory and adjust paths:
```python
# In agent code
if running_with_directory_flag:
    issues_path = Path("../issues")  # Go up from agents-framework
else:
    issues_path = Path("issues")     # Standard path
```

### Option 2: Update Documentation Pattern  
Change guide to use wrapper script instead of direct uv:
```bash
# Instead of: uv run --directory agents-framework python bin/agent.py run SmartIssueAgent "001"
# Use: ./bin/agent run SmartIssueAgent "001"  # Wrapper handles paths correctly
```

### Option 3: Environment Variable Solution
```bash
# Set working directory for issue resolution
REPO_ROOT=/path/to/repo uv run --directory agents-framework python bin/agent.py run SmartIssueAgent "001"
```

## Recommended Fix
**Option 2** - Update documentation to use wrapper script as primary method:

```bash
# Primary method (works reliably)
./bin/agent run SmartIssueAgent "001"

# Advanced method (for direct uv lovers)  
cd agents-framework
uv run python bin/agent.py run SmartIssueAgent "001"
```

## Files to Update
- docs/NEW-REPO-GUIDE.md (revert to wrapper script examples)  
- bin/setup-new-repo.sh (suggest wrapper script commands)
- Or fix agent path resolution logic

## Success Criteria
- [ ] New users can successfully process issues after setup
- [ ] Beautiful uv commands work end-to-end  
- [ ] No confusion about file paths or working directories
- [ ] Guide examples work exactly as documented

## Type
bug

## Priority
high

## Status
open

## Assignee
smart_issue_agent