# Issue #129: Test Path Resolution Issue

## Description
Test case for the path resolution problem reported by pin-citer team.

**Objective**: Ensure agents can find issue files regardless of working directory.

**Test Scenarios**:
- Running from project root: `./bin/agent run SmartIssueAgent "129"`
- Running from agents-framework: `cd agents-framework && uv run python bin/agent.py run SmartIssueAgent "129"`
- Running with uv --directory: `uv run --directory agents-framework python bin/agent.py run SmartIssueAgent "129"`

**Expected Result**: All methods should successfully find this issue file.

## Type
bug

## Priority
high

## Status
open

## Assignee
smart_issue_agent