# Issue #112: Agents Misinterpret Issue Content

## Problem
Agents frequently misunderstand issue content, confusing examples with requirements and not recognizing common patterns like "Current/Should" specifications.

## Current Behavior
- Examples in issues are treated as additional requirements
- "Current state" vs "Desired state" patterns not properly parsed
- Issue intent is often misunderstood
- Agents attempt to implement example code literally

## Expected Behavior
- Recognize and differentiate between:
  - Requirements vs examples
  - Current state vs desired state
  - Problem description vs solution hints
  - Test cases vs implementation details
- Understand issue intent correctly
- Use examples for guidance, not as literal requirements

## Example Cases
1. Issue says "For example, you might..." → Agent tries to implement the example
2. Issue shows "Current: X, Should be: Y" → Agent doesn't recognize this as a change request
3. Issue includes test cases → Agent treats tests as features to implement

## Files Affected
- `agents/issue_fixer_agent.py` - IssueParserTool
- `agents/issue_decomposer_agent.py` - Issue understanding logic
- `tools/issue_parser.py` - Pattern recognition

## Priority
HIGH - Causes incorrect implementations

## Success Criteria
- [ ] Correctly identify Current/Should patterns
- [ ] Distinguish examples from requirements
- [ ] Parse issue sections semantically
- [ ] Understand issue intent accurately
- [ ] Tests for various issue formats