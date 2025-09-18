# Issue #018: Implement Circuit Breaker Pattern for External Services

## Description
Add a circuit breaker pattern implementation to prevent cascading failures when external services are unavailable. This will improve system resilience and prevent resource exhaustion during outages.

## Requirements

### Core Implementation
- [ ] Create `core/circuit_breaker.py` with CircuitBreaker class
- [ ] Implement three states: CLOSED, OPEN, HALF_OPEN
- [ ] Add configurable failure thresholds and timeout periods
- [ ] Support multiple circuit breakers per service
- [ ] Include fallback mechanism when circuit is open

### State Transitions
- [ ] CLOSED → OPEN: When failure threshold exceeded
- [ ] OPEN → HALF_OPEN: After timeout period expires
- [ ] HALF_OPEN → CLOSED: On successful test request
- [ ] HALF_OPEN → OPEN: On failed test request

### Features
- [ ] Sliding window for tracking failures
- [ ] Configurable failure types (exceptions, status codes, timeouts)
- [ ] Success rate calculation over time window
- [ ] Event callbacks for state changes
- [ ] Manual circuit control (force open/close)
- [ ] Circuit breaker statistics and monitoring

### Integration
- [ ] Decorator for protecting function calls: `@circuit_breaker()`
- [ ] Integration with rate limiter for coordinated protection
- [ ] Support for async operations
- [ ] Health check endpoint for circuit status

## Example Usage

```python
from core.circuit_breaker import CircuitBreaker, circuit_breaker

# Create circuit breaker
breaker = CircuitBreaker(
    name="github_api",
    failure_threshold=5,
    recovery_timeout=30,
    expected_exception=RequestException
)

# Use as decorator
@circuit_breaker(
    failure_threshold=3,
    recovery_timeout=60,
    fallback=lambda: {"status": "service unavailable"}
)
def call_external_api():
    response = requests.get("https://api.example.com/data")
    return response.json()

# Manual usage
if breaker.call_allowed():
    try:
        result = external_service_call()
        breaker.record_success()
    except Exception as e:
        breaker.record_failure()
        result = fallback_response()
else:
    result = fallback_response()

# Check status
status = breaker.get_status()
print(f"Circuit state: {status.state}, failures: {status.failure_count}")
```

## Acceptance Criteria
- [ ] Circuit opens after 5 failures within 1 minute
- [ ] Circuit attempts recovery after 30 second timeout
- [ ] Half-open state allows single test request
- [ ] State transitions are thread-safe
- [ ] Integration tests show proper failure isolation
- [ ] Performance overhead < 0.1ms per call
- [ ] Statistics accurately track all state changes

## Technical Notes
- Use threading locks for state management
- Implement exponential backoff for recovery attempts
- Consider using time-based sliding window for failure tracking
- Add configuration for excluding certain exceptions
- Support custom health check functions