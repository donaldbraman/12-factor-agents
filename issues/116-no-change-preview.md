# Issue #116: No Change Preview Before Applying

## Problem
Changes are applied immediately without showing the user what will be modified. This makes it impossible to review and approve changes before they happen.

## Current Behavior
- Changes applied directly to files
- No preview or dry-run mode
- User sees changes only after execution
- No approval mechanism
- Cannot abort problematic changes

## Expected Behavior
- Show preview of all changes before applying
- Diff view of modifications
- Dry-run mode for testing
- User approval step (optional)
- Ability to abort before changes are made
- Summary of what will be affected

## Preview Should Include
1. **File Changes**
   - List of files to be modified
   - Diff for each file
   - New files to be created
   - Files to be deleted

2. **System Changes**
   - Git operations (branches, commits)
   - External API calls
   - Database modifications

3. **Risk Assessment**
   - Severity of changes
   - Potential impact
   - Reversibility

## Implementation Ideas
- Add `--dry-run` flag to CLI
- Preview mode in agents
- Change collection before execution
- Interactive approval prompt
- Change summary generation

## Files Affected
- `core/agent.py` - Preview mode support
- `agents/smart_issue_agent.py` - Collect changes before applying
- `cli/agent.py` - Add preview flags
- `tools/file_editor.py` - Preview capability

## Priority
MEDIUM - Important for safety and user confidence

## Success Criteria
- [ ] Dry-run mode implemented
- [ ] Change preview with diffs
- [ ] Optional approval step
- [ ] Clear change summaries
- [ ] Ability to abort changes
- [ ] Tests for preview mode