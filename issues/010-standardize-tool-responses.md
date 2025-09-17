# Issue #010: Standardize Tool Response Structure (Factor 4)

## Description
Tool responses are inconsistent across different tools, violating Factor 4: Tools are Structured Outputs.

## Problems
- Some tools return ToolResponse objects
- Others return plain dictionaries
- Inconsistent error reporting
- Missing standardized fields

## Examples of Inconsistency
- FileEditorTool returns different structure than GitTool
- Some tools use 'success' field, others use 'status'
- Error messages in different formats
- Data payload structure varies

## Solution
1. Enforce ToolResponse class usage for all tools
2. Standardize response fields:
   - success: boolean
   - data: dict (payload)
   - error: str (if failed)
   - metadata: dict (optional)
3. Create response validation
4. Update all existing tools

## Priority
High - Core infrastructure consistency

## Type
refactoring

## Status
open