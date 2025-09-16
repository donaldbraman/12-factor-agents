# Issue #100: CodeGenerationAgent Must Modify Actual Target Files, Not Just Create Tests

## Problem
When processing issues, the CodeGenerationAgent creates test files but doesn't actually modify the target files specified in the issue. For example, when fixing agents/code_generation_agent.py, it only creates tests/test_issue_X_fix.py instead of modifying the actual agent file.

## Current Behavior
```python
# What happens now:
1. Issue says: "Fix agents/code_generation_agent.py"
2. Agent reads the file
3. Agent generates a test file: tests/test_issue_97_fix.py
4. Agent does NOT modify agents/code_generation_agent.py
5. PR only contains test file, actual bug remains unfixed
```

## Expected Behavior
```python
# What should happen:
1. Issue says: "Fix agents/code_generation_agent.py"  
2. Agent reads the file
3. Agent modifies agents/code_generation_agent.py with actual fix
4. Agent optionally creates test file if needed
5. PR contains both the fix and tests
```

## Root Cause
In the execute_task method, the agent loops through affected_files but the fix methods return unchanged content. The agent needs to actually apply the generated fixes to the files.

## Affected Files
- agents/code_generation_agent.py (execute_task method, lines 110-159)

## Success Criteria
- Agent modifies the actual files listed in issue's affected_files
- Generated code changes are non-empty when a fix is needed
- PR contains modifications to target files, not just tests
- File changes pass validation and tests

## Implementation Fix
The issue is in execute_task around line 137-139:
```python
# Current broken logic:
modified_content = self._apply_generic_fix(
    original_content, file_path, analysis, solution
)
# Returns unchanged content, so no actual fix applied!
```

The fix methods need to:
1. Actually parse and understand the issue requirements
2. Generate real code changes based on the analysis
3. Return modified content that differs from original

## Test Command
```bash
# Process this very issue to test self-modification
python bin/process_issue.py 12-factor-agents 100

# Verify actual files were modified
git diff --name-only HEAD~1 | grep -v test_
```

## Priority
CRITICAL - Without this, the entire pipeline is useless as it never fixes anything!