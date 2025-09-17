# Issue #118: Add Message Bus for Agent Communication

## Problem
Agents communicate through direct method calls and file system, creating tight coupling and making it difficult to trace, monitor, or modify communication patterns.

## Current Behavior
- Direct agent-to-agent calls
- File system as communication medium
- No message routing
- No communication monitoring
- Cannot intercept or modify messages
- Synchronous coupling

## Expected Behavior
- Central message bus for all agent communication
- Publish/subscribe patterns
- Message routing based on capabilities
- Asynchronous communication options
- Message history and tracing
- Ability to intercept/modify messages

## Message Bus Features
1. **Core Functionality**
   - Message publishing
   - Topic-based routing
   - Request/response patterns
   - Event broadcasting

2. **Advanced Features**
   - Message persistence
   - Retry logic
   - Dead letter queues
   - Message transformation
   - Priority queues

3. **Monitoring**
   - Message tracing
   - Performance metrics
   - Error tracking
   - Communication visualization

## Implementation Ideas
- Event-driven architecture
- Topic-based pub/sub
- Message queue implementation
- Optional persistence layer
- WebSocket for real-time updates
- REST API for external integration

## Example Usage
```python
# Current - Direct coupling
result = IssueFixerAgent().execute_task(task)

# Desired - Message bus
bus.publish("task.execute", {
    "agent": "issue_fixer",
    "task": task
})
result = bus.wait_for_response()
```

## Files Affected
- `core/message_bus.py` - New message bus implementation
- `core/agent.py` - Message bus integration
- `core/events.py` - Event definitions (new)
- All agents - Convert to message-based communication

## Priority
LOW - Long-term architectural improvement

## Success Criteria
- [ ] Message bus implemented
- [ ] Pub/sub patterns working
- [ ] All agents use message bus
- [ ] Message tracing available
- [ ] Asynchronous communication supported
- [ ] Performance acceptable
- [ ] Tests for message patterns
- [ ] Documentation for message formats