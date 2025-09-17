# Issue #111: Critical - Agents Destroy Files Instead of Editing

## Problem
Agents are using "create" operations instead of "edit" operations, causing complete file overwrites even for simple changes. This destroys all existing content when making small modifications.

## Current Behavior
When IssueFixerAgent or other agents need to modify a file:
- They use FileEditorTool with "create" mode
- This completely replaces the file content
- All existing code/content is lost
- Only the new content remains

## Expected Behavior
Agents should:
- Use "edit" or "modify" operations to preserve existing content
- Only change the specific parts that need updating
- Maintain file structure and other content
- Use diff-based editing for safety

## Example
When fixing a typo in README.md:
- **Current**: Entire README.md is replaced with just the fixed line
- **Expected**: Only the typo is corrected, rest of file unchanged

## Files Affected
- `agents/issue_fixer_agent.py` - FileEditorTool usage
- `tools/file_editor.py` - Needs edit vs create logic
- `agents/code_generation_agent.py` - File modification logic

## Priority
CRITICAL - This is causing data loss

## Success Criteria
- [ ] Agents use edit operations by default
- [ ] Create is only used for new files
- [ ] Existing content is preserved during modifications
- [ ] Diff-based editing is implemented
- [ ] Tests verify content preservation