# Issue #004: Remove Unused Agent Files

## Description
Several agent files appear to be unused and can be safely removed to clean up the codebase.

## Files to Remove
- agents/pr_review_12factor.py (not imported anywhere)
- agents/retry_demo_agent.py (not imported anywhere)  
- agents/simple_issue_closer.py (not imported anywhere)

## Verification
Confirmed these files have no imports or references in the codebase.

## Type
cleanup

## Priority
low

## Status
open