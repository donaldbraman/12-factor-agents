# Chaos Test: State Corruption Recovery

## Type
bug

## Description
Fix state corruption where SPARKY's serialized execution context becomes corrupted mid-execution. Agent must detect corruption, recover gracefully, and continue execution without losing critical progress.

## Current State
- Agent state file corrupted at 60% completion
- Pickle deserialization fails with binary corruption
- JSON backup partially truncated during write
- Learning insights lost due to corruption
- Resume token invalid after corruption
- Action history incomplete/inconsistent
- Test results lost requiring full re-execution

## Expected Behavior
Agent detects corruption, recovers to last known good state, and continues execution.

## Constraints
- State corruption occurs at random execution points
- Multiple corruption types: binary, JSON, filesystem
- Limited backup history (last 3 checkpoints)
- Corruption may affect multiple state components
- Recovery must preserve action progress
- No external state validation available
- Agent crash may occur during recovery

## Success Criteria
1. Detect state corruption within 1 checkpoint cycle
2. Recover to last known good checkpoint automatically
3. Resume execution without data loss
4. Preserve learning insights across recovery
5. Maintain action completion history
6. Handle partial file corruption gracefully
7. Log corruption incidents for analysis

## Chaos Factors
- Random state corruption (15% chance per checkpoint)
- Simulated disk full during state save (5% chance)
- File system race conditions during backup
- Memory corruption simulation before serialization
- Interrupted write operations (power loss simulation)
- Multiple simultaneous corruption sources
- Recovery failure simulation (corrupt backups)