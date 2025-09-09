# Issue #131: Fix Invalid Regex Escape Sequences

## Description
Multiple SyntaxWarnings about invalid escape sequences in issue_decomposer_agent.py.

## Problem
Current regex patterns have invalid escape sequences:
```python
"###.*1\.", "###.*2\.", "###.*3\."  # SyntaxWarning: invalid escape sequence '\.'
```

## Solution
Use raw strings for regex patterns:
```python
r"###.*1\.", r"###.*2\.", r"###.*3\."  # Fixed with raw strings
```

## Files to Update
- agents/issue_decomposer_agent.py (line 70)

## Type
bug

## Priority
low

## Status
open

## Assignee
issue_fixer_agent