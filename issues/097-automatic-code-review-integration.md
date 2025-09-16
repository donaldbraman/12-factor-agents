# Issue #097: Integrate automatic code review after modifications

## Problem
Currently, when agents modify code, there's no automatic code review stage. This led to syntax errors slipping through (like the IndentationError in pin-citer issue #144) because:
- Pre-write validation only checks new content in isolation
- No verification that modifications make sense in context
- No check for code duplication or quality issues

## Current State
- CodeReviewAgent exists but isn't automatically triggered
- Validation system only does basic syntax checking
- No post-modification review before marking issues complete

## Desired Behavior
The orchestrator should automatically trigger CodeReviewAgent after any code modifications:

```
1. Agent modifies files
2. Orchestrator triggers CodeReviewAgent
3. Review checks for:
   - Syntax errors in full context
   - Code duplication
   - Indentation issues
   - Logic errors
   - Best practices
4. If review fails → retry with fixes
5. If review passes → proceed to testing
```

## Implementation Strategy
1. Modify IssueOrchestratorAgent to add review stage
2. Create review pipeline in orchestration flow:
   ```python
   # After agent completes modifications
   if result.get("files_modified"):
       review_result = self._run_code_review(result)
       if not review_result["passed"]:
           return self._handle_review_failure(review_result)
   ```
3. Integrate with IntelligentValidationRetry for auto-fixes
4. Add telemetry for review metrics

## Success Criteria
- [ ] Code review automatically runs after modifications
- [ ] Review failures trigger retry mechanism
- [ ] Context-aware validation (not just isolated snippets)
- [ ] Duplicate code detection
- [ ] Indentation verification in context
- [ ] Review metrics in telemetry

## Example Case
The pin-citer issue #144 that introduced:
- Duplicate `if result is not None:` blocks
- IndentationError in context
- Would have been caught by automatic review

## Priority
Critical - This prevents syntax errors and code quality issues from reaching production

## Agent Assignment
IssueOrchestratorAgent, CodeReviewAgent