# Issue #015: Implement Rate Limiter for Agent Calls

## Problem
Agents can currently make unlimited calls to external services, which could lead to rate limit violations or excessive costs.

## Requirements
The system should limit agent calls to external services.
It must track call rates per service and per agent.
When rate limits are exceeded, the system should return a clear error with retry-after information.
Ensure that burst traffic is handled gracefully with token bucket algorithm.

## Technical Specifications
- Implement RateLimiter class in core/rate_limiter.py
- Support configurable limits per service (e.g., 100 calls/minute for GitHub API)
- Use token bucket algorithm for burst handling
- Store rate limit state in memory with option for Redis backend
- Include decorator for easy integration: @rate_limit(calls=10, period=60)

## Success Criteria
- Rate limiter prevents excessive calls
- Clear error messages when limits exceeded
- Graceful degradation under load
- Thread-safe implementation
- Comprehensive test coverage including edge cases

## Edge Cases
- Handle concurrent requests from multiple threads
- Deal with clock drift and time zone changes
- Support rate limit headers from external APIs
- Handle Redis connection failures gracefully
- Test with very long strings and null values