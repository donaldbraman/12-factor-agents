# Issue #085: Improve Logging Configuration

## Description
Update the logging configuration to use structured logging with timestamps and log levels.

## Problem
Current logging is basic print statements.

## Solution
Replace print statements with proper logging:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Task completed successfully")
```

## Files to Update
- core/agent.py
- agents/smart_issue_agent.py

## Type
improvement  

## Priority
low

## Status
open

## Assignee
smart_issue_agent