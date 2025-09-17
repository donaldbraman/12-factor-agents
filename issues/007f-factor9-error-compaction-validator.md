# Issue #007f: Implement Factor 9 Validator - Compact Errors into Context Window

## Parent Issue
#MASTER-12-FACTOR-COMPLIANCE

## Description
Implement validator for Factor 9: Compact Errors into Context Window. Errors should be efficiently captured and communicated within context limits.

## Validation Criteria
The validator should check:
1. **Error Compaction**
   - Errors are summarized, not verbose
   - Stack traces are compressed
   - Redundant information removed

2. **Error Patterns**
   - Common errors have codes
   - Error patterns recognized
   - Similar errors grouped

3. **Context Efficiency**
   - Error context is relevant
   - Historical errors summarized
   - Error trends identified

## Implementation Details
```python
class Factor9Validator(FactorValidator):
    """Factor 9: Compact Errors into Context Window"""
    
    def validate(self, agent: BaseAgent, context: Dict[str, Any] = None):
        # Check error message length
        # Validate error summarization
        # Ensure error pattern recognition
        # Check context efficiency
```

## Files to Create/Modify
- core/compliance.py - Add Factor9Validator class
- core/error_compaction.py - Create error compaction utilities
- tests/test_factor9_compliance.py - Add validation tests

## Example Error Compaction
```python
# Before (verbose)
error = """
Traceback (most recent call last):
  File "/path/to/file.py", line 123, in function
    result = complex_operation()
  File "/path/to/other.py", line 456, in complex_operation
    data = fetch_data()
  File "/path/to/third.py", line 789, in fetch_data
    raise ConnectionError("Failed to connect to database")
ConnectionError: Failed to connect to database
"""

# After (compacted)
error = "ERR_DB_001: Database connection failed at fetch_data() [third.py:789]"
```

## Acceptance Criteria
- [ ] Factor9Validator class implemented
- [ ] Validates error compaction
- [ ] Checks error patterns
- [ ] Ensures context efficiency
- [ ] Tests pass with >90% coverage

## Priority
Medium - Improves context usage

## Type
enhancement

## Status
open