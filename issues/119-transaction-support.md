# Issue #119: Add Transaction Support with Rollback

## Problem
Complex operations involving multiple steps have no transaction support. If any step fails, previous steps cannot be rolled back, leaving the system in an inconsistent state.

## Current Behavior
- No transaction boundaries
- Partial failures leave partial changes
- No automatic rollback
- Manual cleanup required
- State inconsistencies after failures

## Expected Behavior
- Transaction boundaries for operations
- Automatic rollback on failure
- Nested transaction support
- Savepoints for partial rollback
- Consistent state guaranteed
- Transaction logs for debugging

## Transaction Requirements
1. **ACID Properties**
   - Atomicity: All or nothing
   - Consistency: Valid state transitions
   - Isolation: Concurrent operation safety
   - Durability: Changes persist properly

2. **Transaction Operations**
   - Begin transaction
   - Commit changes
   - Rollback on failure
   - Savepoints
   - Nested transactions

3. **Scope**
   - File system changes
   - Git operations
   - State modifications
   - External API calls

## Implementation Ideas
```python
# Example transaction usage
with TransactionContext() as tx:
    tx.checkpoint("start")
    
    # Make changes
    file_changes = modify_files()
    tx.track_changes(file_changes)
    
    tx.checkpoint("files_modified")
    
    # More operations
    run_tests()
    
    if test_failed:
        tx.rollback_to("files_modified")
    
    tx.commit()  # All successful
```

## Saga Pattern for Distributed Transactions
- Compensating transactions
- Forward recovery
- Backward recovery
- Transaction coordinator
- State machine for transaction flow

## Files Affected
- `core/transaction.py` - Transaction manager (new)
- `core/orchestrator.py` - Transaction boundaries
- `core/agent.py` - Transaction support
- `tools/file_editor.py` - Transactional file operations
- `core/state_manager.py` - Transactional state

## Priority
MEDIUM - Critical for reliability

## Success Criteria
- [ ] Transaction context manager implemented
- [ ] Automatic rollback on exceptions
- [ ] File system rollback working
- [ ] Git operations rollback
- [ ] State rollback functioning
- [ ] Nested transactions supported
- [ ] Transaction logs available
- [ ] Tests for failure scenarios
- [ ] Performance impact acceptable