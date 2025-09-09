# Issue #187: Standardize All Documentation to Use uv Examples

## Description
All documentation should consistently use `uv` for Python execution since we love uv! Currently there's a mix of `./bin/agent` and `uv run python bin/agent.py` patterns.

## Current Mixed Patterns
```bash
# Some places use wrapper script
./bin/agent list
./bin/agent run SmartIssueAgent "001"

# Other places use uv directly  
uv run python bin/agent.py list
cd agents-framework && uv run python bin/agent.py run SmartIssueAgent "001"
```

## Required Consistent Pattern
All examples should use the beautiful uv syntax:
```bash
# Primary pattern - from repo root with agents-framework
uv run --directory agents-framework python bin/agent.py list
uv run --directory agents-framework python bin/agent.py run SmartIssueAgent "001"

# Alternative when in agents-framework directory  
cd agents-framework
uv run python bin/agent.py list
uv run python bin/agent.py run SmartIssueAgent "001"
```

## Files to Update

### 1. docs/NEW-REPO-GUIDE.md
**Current Issues:**
- Line 21: `./bin/agent list` 
- Line 22: `./bin/agent run SmartIssueAgent "001"`
- Line 79: `uv run python bin/agent.py list`
- Line 134: `cd agents-framework && uv run python bin/agent.py run SmartIssueAgent "001"`
- Line 288: `uv run python bin/agent.py list  # Use full path`

**Should be consistently:**
```bash
uv run --directory agents-framework python bin/agent.py list
uv run --directory agents-framework python bin/agent.py run SmartIssueAgent "001"
```

### 2. docs/USER-GUIDE.md
Check for any mixed patterns and standardize to uv.

### 3. README.md  
Update any command examples to use uv.

### 4. bin/setup-new-repo.sh
Update the "Next steps" output to show uv commands.

## Benefits of uv Standardization
- ✅ **Consistent**: All examples work the same way
- ✅ **Modern**: Uses the beautiful uv tool we love  
- ✅ **Clear**: No confusion about which command to use
- ✅ **Reliable**: Works from any directory with --directory flag
- ✅ **Fast**: uv is blazingly fast for Python execution

## Success Criteria
- [ ] All documentation uses uv consistently
- [ ] No mixed command patterns in any docs
- [ ] Examples work from any directory
- [ ] Setup script outputs uv commands
- [ ] README shows uv examples

## Test Plan
1. Search all docs for old patterns
2. Replace with consistent uv usage
3. Test all examples work as documented
4. Update setup script output

## Type
enhancement

## Priority
medium

## Status  
open

## Assignee
issue_fixer_agent