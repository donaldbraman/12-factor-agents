# Issue #005: Standardize sys.path.insert Pattern

## Description
Many files have sys.path.insert but some are missing the noqa comment for consistency.

## Problem
35 files use `sys.path.insert(0, str(Path(__file__).parent.parent))` but not all have the noqa comment.

## Solution
Ensure all sys.path.insert lines have the noqa comment:
```python
sys.path.insert(0, str(Path(__file__).parent.parent))  # noqa: E402
```

## Files to Update
- Multiple agent files (need to scan all)

## Type
style

## Priority
low

## Status
open