# Issue #074: Fix CLI Commands in README

## Description
Fix CLI Commands in README

Specific changes needed:
Current broken:
```bash
uv run agent list
uv run agent run <name> "<task>"
```

Should be:
```bash
uv run python bin/agent.py list
uv run python bin/agent.py run <name> "<task>"
uv run python bin/agent.py info <name>
uv run python bin/agent.py orchestrate <pipeline>
```

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
