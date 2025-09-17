# Issue #009: Improve Error Compaction (Factor 9)

## Description
Current error handling is verbose and doesn't efficiently compact errors into the context window, violating Factor 9.

## Problems
- Full stack traces included in many places
- No error summarization
- Redundant error information
- Missing error pattern recognition

## Affected Areas
- agents/intelligent_issue_agent.py - verbose error messages
- agents/issue_fixer_agent.py - full stack traces
- core/retry.py - could compact retry history
- All agent execute_task methods

## Solution
1. Create error compaction utility in core/
2. Summarize stack traces to key information
3. Group similar errors together
4. Provide error codes for common failures
5. Include only relevant context in error messages

## Priority
Medium - Improves context efficiency

## Type
enhancement

## Status
open