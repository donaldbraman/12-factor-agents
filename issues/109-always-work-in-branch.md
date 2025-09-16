# Issue #109: CRITICAL: Agents Must Always Work in Feature Branches

## Problem
**The agent system can destroy your project by modifying files directly on main!**

When SmartIssueAgent runs, it calls IssueFixerAgent which directly modifies files on the current branch. If you're on main, it destroys your main branch. The PR creation happens AFTER the damage is done.

## Current Flow (DANGEROUS)
1. SmartIssueAgent starts (on current branch, often main)
2. Decomposes issue
3. Calls IssueFixerAgent 
4. **IssueFixerAgent modifies files directly on current branch** ← DESTROYS MAIN
5. Later, PR agent creates a branch (too late, damage done)

## Required Flow (SAFE)
1. SmartIssueAgent starts
2. **IMMEDIATELY creates a feature branch**
3. All work happens in feature branch
4. If successful, creates PR
5. If failed, can safely delete branch

## Critical Changes Needed

### 1. SmartIssueAgent
Must create a branch BEFORE any file operations:
```python
def execute_task(self, task: str) -> ToolResponse:
    # FIRST THING: Create feature branch
    branch_name = f"agent/issue-{issue_num}-{timestamp}"
    subprocess.run(["git", "checkout", "-b", branch_name])
    
    # NOW safe to proceed with changes
    ...
```

### 2. IssueFixerAgent  
Should verify it's NOT on main before modifying files:
```python
def execute_task(self, task: str) -> ToolResponse:
    # Safety check
    current_branch = subprocess.run(["git", "branch", "--show-current"], ...)
    if current_branch.stdout.strip() in ["main", "master"]:
        return ToolResponse(
            success=False,
            error="SAFETY: Cannot modify files on main branch. Create a feature branch first."
        )
```

### 3. Add --dry-run Flag
For extra safety, add dry-run mode that shows what would be changed without doing it.

## Files to Modify
- agents/smart_issue_agent.py - Add branch creation at start
- agents/issue_fixer_agent.py - Add safety check
- core/base.py - Add branch management utilities

## Success Criteria
- No agent can EVER modify files on main/master
- All agent work happens in feature branches
- Clear error if someone tries to run on main
- Branch name includes issue number and timestamp
- Failed runs leave branch for debugging

## Test
```bash
# This should create a branch, not destroy main
git checkout main
uv run python bin/agent.py run SmartIssueAgent "108"
git branch --show-current  # Should NOT be main
```

## Priority
**CRITICAL** - This is a data loss bug that can destroy entire projects.