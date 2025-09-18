"""
Rate Limiter implementation with token bucket algorithm.

This module provides thread-safe rate limiting functionality for agent calls
to external services. It implements the token bucket algorithm to handle
burst traffic gracefully while maintaining rate limits over time.

Features:
- Token bucket algorithm for burst handling
- Thread-safe implementation
- Configurable limits per service/agent
- Redis backend support for distributed scenarios
- Graceful degradation on backend failures
- Comprehensive error handling
"""

import logging
import time
import threading
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from functools import wraps
from enum import Enum

# Optional Redis support
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


logger = logging.getLogger(__name__)


class RateLimitBackend(Enum):
    """Available backends for rate limit storage."""

    MEMORY = "memory"
    REDIS = "redis"


class RateLimitError(Exception):
    """Base exception for rate limiting errors."""

    pass


class RateLimitExceeded(RateLimitError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: float, service: str = None):
        super().__init__(message)
        self.retry_after = retry_after
        self.service = service


class RateLimitBackendError(RateLimitError):
    """Raised when rate limit backend fails."""

    pass


@dataclass
class TokenBucket:
    """Token bucket for rate limiting with configurable capacity and refill rate."""

    capacity: int  # Maximum number of tokens
    refill_rate: float  # Tokens per second
    tokens: float = field(init=False)  # Current tokens available
    last_refill: float = field(init=False)  # Last refill timestamp
    lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self):
        """Initialize bucket state."""
        self.tokens = float(self.capacity)
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """
        Attempt to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            Tuple of (success, retry_after_seconds)
        """
        with self.lock:
            now = time.time()
            self._refill(now)

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0
            else:
                # Calculate how long to wait for enough tokens
                tokens_needed = tokens - self.tokens
                retry_after = tokens_needed / self.refill_rate
                return False, retry_after

    def _refill(self, now: float):
        """Refill tokens based on time elapsed since last refill."""
        time_elapsed = now - self.last_refill
        tokens_to_add = time_elapsed * self.refill_rate

        # Add tokens, but don't exceed capacity
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def remaining_tokens(self) -> int:
        """Get current number of tokens available."""
        with self.lock:
            now = time.time()
            self._refill(now)
            return int(self.tokens)


class MemoryBackend:
    """In-memory backend for rate limiting using regular dict for reliable access."""

    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def get_bucket(self, key: str, capacity: int, refill_rate: float) -> TokenBucket:
        """Get or create a token bucket for the given key."""
        with self._lock:
            if key not in self._buckets:
                bucket = TokenBucket(capacity=capacity, refill_rate=refill_rate)
                self._buckets[key] = bucket
                logger.debug(f"Created new token bucket for key: {key}")
            return self._buckets[key]

    def clear(self):
        """Clear all buckets (for testing)."""
        with self._lock:
            self._buckets.clear()


class RedisBackend:
    """Redis backend for distributed rate limiting."""

    def __init__(
        self,
        redis_client: Optional["redis.Redis"] = None,
        redis_url: str = "redis://localhost:6379/0",
    ):
        if not REDIS_AVAILABLE:
            raise RateLimitBackendError("Redis not available. Install redis package.")

        if redis_client:
            self.redis = redis_client
        else:
            try:
                self.redis = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis.ping()
            except Exception as e:
                raise RateLimitBackendError(f"Failed to connect to Redis: {e}")

        # Lua script for atomic token bucket operations
        self._consume_script = self.redis.register_script(
            """
            local key = KEYS[1]
            local capacity = tonumber(ARGV[1])
            local refill_rate = tonumber(ARGV[2])
            local tokens_requested = tonumber(ARGV[3])
            local now = tonumber(ARGV[4])
            
            -- Get current state
            local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
            local tokens = tonumber(bucket[1]) or capacity
            local last_refill = tonumber(bucket[2]) or now
            
            -- Refill tokens
            local time_elapsed = now - last_refill
            local tokens_to_add = time_elapsed * refill_rate
            tokens = math.min(capacity, tokens + tokens_to_add)
            
            -- Try to consume tokens
            local success = 0
            local retry_after = 0
            
            if tokens >= tokens_requested then
                tokens = tokens - tokens_requested
                success = 1
            else
                local tokens_needed = tokens_requested - tokens
                retry_after = tokens_needed / refill_rate
            end
            
            -- Update state
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, 3600)  -- Expire after 1 hour of inactivity
            
            return {success, retry_after, tokens}
        """
        )

    def consume_tokens(
        self, key: str, capacity: int, refill_rate: float, tokens: int = 1
    ) -> Tuple[bool, float]:
        """
        Atomically consume tokens from Redis-backed bucket.

        Returns:
            Tuple of (success, retry_after_seconds)
        """
        try:
            now = time.time()
            result = self._consume_script(
                keys=[f"rate_limit:{key}"], args=[capacity, refill_rate, tokens, now]
            )
            success = bool(result[0])
            retry_after = float(result[1])
            return success, retry_after
        except Exception as e:
            logger.error(f"Redis operation failed for key {key}: {e}")
            raise RateLimitBackendError(f"Redis backend error: {e}")

    def clear(self):
        """Clear all rate limit data (for testing)."""
        try:
            for key in self.redis.scan_iter(match="rate_limit:*"):
                self.redis.delete(key)
        except Exception as e:
            logger.error(f"Failed to clear Redis data: {e}")


class RateLimiter:
    """
    Thread-safe rate limiter with token bucket algorithm.

    Supports both in-memory and Redis backends for rate limit storage.
    Provides configurable rate limits per service and graceful degradation.
    """

    def __init__(
        self,
        backend: RateLimitBackend = RateLimitBackend.MEMORY,
        redis_client: Optional["redis.Redis"] = None,
        redis_url: str = "redis://localhost:6379/0",
        default_capacity: int = 100,
        default_refill_rate: float = 100.0 / 60.0,
    ):  # 100 per minute
        """
        Initialize rate limiter.

        Args:
            backend: Backend type for storage
            redis_client: Existing Redis client (for Redis backend)
            redis_url: Redis URL (for Redis backend if no client provided)
            default_capacity: Default bucket capacity
            default_refill_rate: Default refill rate (tokens per second)
        """
        self.backend_type = backend
        self.default_capacity = default_capacity
        self.default_refill_rate = default_refill_rate

        # Service-specific configurations
        self._service_configs: Dict[str, Dict[str, Any]] = {}
        self._config_lock = threading.Lock()

        # Initialize backend
        if backend == RateLimitBackend.MEMORY:
            self._backend = MemoryBackend()
        elif backend == RateLimitBackend.REDIS:
            self._backend = RedisBackend(redis_client, redis_url)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def configure_service(
        self,
        service: str,
        calls_per_minute: int = 100,
        burst_capacity: Optional[int] = None,
    ):
        """
        Configure rate limits for a specific service.

        Args:
            service: Service identifier
            calls_per_minute: Sustained rate limit
            burst_capacity: Maximum burst capacity (defaults to 2x rate)
        """
        if burst_capacity is None:
            burst_capacity = max(calls_per_minute * 2, 10)

        refill_rate = calls_per_minute / 60.0  # Convert to per-second

        with self._config_lock:
            self._service_configs[service] = {
                "capacity": burst_capacity,
                "refill_rate": refill_rate,
                "calls_per_minute": calls_per_minute,
            }

        logger.info(
            f"Configured service '{service}': {calls_per_minute} calls/min, "
            f"burst capacity: {burst_capacity}"
        )

    def check_rate_limit(
        self, service: str, agent_id: str = "default", tokens: int = 1
    ) -> bool:
        """
        Check if rate limit allows the request.

        Args:
            service: Service identifier
            agent_id: Agent identifier
            tokens: Number of tokens to consume

        Returns:
            True if request is allowed, False if rate limited

        Raises:
            RateLimitExceeded: When rate limit is exceeded
            RateLimitBackendError: When backend fails
        """
        key = f"{service}:{agent_id}"

        # Get configuration for service
        config = self._get_service_config(service)
        capacity = config["capacity"]
        refill_rate = config["refill_rate"]

        try:
            if self.backend_type == RateLimitBackend.MEMORY:
                bucket = self._backend.get_bucket(key, capacity, refill_rate)
                success, retry_after = bucket.consume(tokens)
            elif self.backend_type == RateLimitBackend.REDIS:
                success, retry_after = self._backend.consume_tokens(
                    key, capacity, refill_rate, tokens
                )
            else:
                raise RateLimitBackendError(
                    f"Unknown backend type: {self.backend_type}"
                )

            if not success:
                logger.warning(
                    f"Rate limit exceeded for {service}:{agent_id}, "
                    f"retry after {retry_after:.2f}s"
                )
                raise RateLimitExceeded(
                    f"Rate limit exceeded for service '{service}'. "
                    f"Retry after {retry_after:.2f} seconds.",
                    retry_after=retry_after,
                    service=service,
                )

            logger.debug(f"Rate limit check passed for {service}:{agent_id}")
            return True

        except RateLimitExceeded:
            raise
        except Exception as e:
            # Graceful degradation - log error but allow request
            logger.error(f"Rate limit backend error for {service}:{agent_id}: {e}")
            if self.backend_type == RateLimitBackend.REDIS:
                logger.warning(
                    "Falling back to allowing request due to backend failure"
                )
                return True
            raise RateLimitBackendError(f"Rate limit check failed: {e}")

    def get_status(self, service: str, agent_id: str = "default") -> Dict[str, Any]:
        """
        Get current rate limit status for service/agent.

        Returns:
            Dictionary with current status information
        """
        key = f"{service}:{agent_id}"
        config = self._get_service_config(service)

        try:
            if self.backend_type == RateLimitBackend.MEMORY:
                bucket = self._backend.get_bucket(
                    key, config["capacity"], config["refill_rate"]
                )
                remaining = bucket.remaining_tokens()
            else:
                # For Redis, we'd need to implement a separate status check
                remaining = None

            return {
                "service": service,
                "agent_id": agent_id,
                "capacity": config["capacity"],
                "refill_rate": config["refill_rate"],
                "calls_per_minute": config["calls_per_minute"],
                "remaining_tokens": remaining,
                "backend": self.backend_type.value,
            }
        except Exception as e:
            logger.error(f"Failed to get status for {service}:{agent_id}: {e}")
            return {"service": service, "agent_id": agent_id, "error": str(e)}

    def reset_limits(self, service: str = None, agent_id: str = None):
        """Reset rate limits for service/agent or all limits."""
        try:
            if self.backend_type == RateLimitBackend.MEMORY:
                if service is None and agent_id is None:
                    self._backend.clear()
                    logger.info("Cleared all rate limits")
                else:
                    # For specific service/agent, we'd need to implement selective clearing
                    logger.warning(
                        "Selective clearing not implemented for memory backend"
                    )
            elif self.backend_type == RateLimitBackend.REDIS:
                self._backend.clear()
                logger.info("Cleared all Redis rate limit data")
        except Exception as e:
            logger.error(f"Failed to reset limits: {e}")
            raise RateLimitBackendError(f"Reset failed: {e}")

    def _get_service_config(self, service: str) -> Dict[str, Any]:
        """Get configuration for service, using defaults if not configured."""
        with self._config_lock:
            if service in self._service_configs:
                return self._service_configs[service]

            # Return default configuration
            return {
                "capacity": self.default_capacity,
                "refill_rate": self.default_refill_rate,
                "calls_per_minute": int(self.default_refill_rate * 60),
            }


# Global rate limiter instance
_global_rate_limiter: Optional[RateLimiter] = None
_limiter_lock = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _global_rate_limiter

    if _global_rate_limiter is None:
        with _limiter_lock:
            if _global_rate_limiter is None:
                _global_rate_limiter = RateLimiter()

    return _global_rate_limiter


def configure_global_rate_limiter(
    backend: RateLimitBackend = RateLimitBackend.MEMORY, **kwargs
):
    """Configure the global rate limiter."""
    global _global_rate_limiter

    with _limiter_lock:
        _global_rate_limiter = RateLimiter(backend=backend, **kwargs)


def rate_limit(
    service: str,
    calls_per_minute: int = 100,
    burst_capacity: Optional[int] = None,
    agent_id: str = "default",
):
    """
    Decorator for rate limiting function calls.

    Args:
        service: Service identifier
        calls_per_minute: Rate limit
        burst_capacity: Burst capacity
        agent_id: Agent identifier

    Example:
        @rate_limit("github_api", calls_per_minute=60)
        def make_github_request():
            # API call here
            pass
    """

    def decorator(func):
        # Configure service on first use
        limiter = get_rate_limiter()
        limiter.configure_service(service, calls_per_minute, burst_capacity)

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                limiter.check_rate_limit(service, agent_id)
                return func(*args, **kwargs)
            except RateLimitExceeded as e:
                logger.warning(f"Rate limit exceeded in {func.__name__}: {e}")
                raise

        return wrapper

    return decorator
