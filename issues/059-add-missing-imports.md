# Issue #059: Add missing imports to guide examples

## Description
Several examples in the Integration Guide are missing required imports for standalone execution.

## Problems Found
1. Pipeline example needs `import asyncio`
2. Advanced Features section examples need context setup
3. Some examples reference undefined methods

## Solution Needed
- Ensure every code example is self-contained
- Add all necessary imports at the top of each example
- Test each example can be copied and run independently

## Files to Fix
- /docs/INTEGRATION-GUIDE.md (multiple sections)

## Type
documentation

## Priority
medium

## Status
open