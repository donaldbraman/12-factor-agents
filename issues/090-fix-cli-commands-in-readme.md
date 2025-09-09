# Issue #090: Fix CLI Commands in README

## Description
Fix CLI Commands in README

## Problem
The current code needs updating to fix functionality.

## Current Code
```
bash
uv run agent list
uv run agent run <name> "<task>"
```

## Required Change
```  
bash
uv run python bin/agent.py list
uv run python bin/agent.py run <name> "<task>"
uv run python bin/agent.py info <name>
uv run python bin/agent.py orchestrate <pipeline>
```

## Actionable Steps (Factor 8: Own Your Control Flow)
1. Locate the target file: bin/agent.py
2. Find the current code block
3. Replace with the new implementation
4. Verify the change works correctly

## Definition of Done
- [ ] Code replacement completed
- [ ] No syntax errors
- [ ] Functionality verified

## Files to Update
- bin/agent.py

## Parent Issue
064

## Type
bug

## Priority
high

## Status
open

## Assignee
issue_fixer_agent

## Target File
bin/agent.py
