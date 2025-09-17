# Issue #007b: Implement Factor 4 Validator - Tools are Structured Outputs

## Parent Issue
#MASTER-12-FACTOR-COMPLIANCE

## Description
Implement validator for Factor 4: Tools are Structured Outputs. All tools should have predictable, consistent output formats.

## Validation Criteria
The validator should check:
1. **Response Consistency**
   - All tools return ToolResponse objects
   - Consistent field names across tools
   - Predictable error formats

2. **Schema Compliance**
   - Tools define output schemas
   - Responses match defined schemas
   - Type validation on outputs

3. **Documentation**
   - Each tool documents its output format
   - Examples provided for each tool
   - Clear error response patterns

## Implementation Details
```python
class Factor4Validator(FactorValidator):
    """Factor 4: Tools are Structured Outputs"""
    
    def validate(self, agent: BaseAgent, context: Dict[str, Any] = None):
        # Check all tools return ToolResponse
        # Validate response schema consistency
        # Ensure error handling patterns
        # Check for output documentation
```

## Files to Create/Modify
- core/compliance.py - Add Factor4Validator class
- core/tools.py - Enforce ToolResponse usage
- core/schemas.py - Create output schema definitions
- tests/test_factor4_compliance.py - Add validation tests

## Acceptance Criteria
- [ ] Factor4Validator class implemented
- [ ] Validates all tools return ToolResponse
- [ ] Checks schema compliance
- [ ] Detects inconsistent responses
- [ ] Tests pass with >90% coverage

## Priority
High - Affects all tool implementations

## Type
enhancement

## Status
open