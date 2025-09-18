"""
Essential tests for rate limiter implementation.

This module contains the core tests without external dependencies
to ensure the rate limiter works correctly in all scenarios.
"""

import threading
import time
import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rate_limiter import (  # noqa: E402
    RateLimiter,
    TokenBucket,
    RateLimitBackend,
    RateLimitExceeded,
    MemoryBackend,
    rate_limit,
    configure_global_rate_limiter,
)


class TestTokenBucketBasic(unittest.TestCase):
    """Test the core TokenBucket implementation."""

    def test_bucket_initialization(self):
        """Test bucket initializes with full capacity."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        self.assertEqual(bucket.capacity, 10)
        self.assertEqual(bucket.refill_rate, 1.0)
        self.assertEqual(bucket.tokens, 10.0)
        self.assertIsInstance(bucket.lock, threading.Lock)

    def test_basic_token_consumption(self):
        """Test basic token consumption behavior."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        # Should succeed with enough tokens
        success, retry_after = bucket.consume(5)
        self.assertTrue(success)
        self.assertEqual(retry_after, 0.0)
        self.assertEqual(bucket.remaining_tokens(), 5)

        # Should succeed with exact remaining tokens
        success, retry_after = bucket.consume(5)
        self.assertTrue(success)
        self.assertEqual(retry_after, 0.0)
        self.assertEqual(bucket.remaining_tokens(), 0)

        # Should fail with no tokens remaining
        success, retry_after = bucket.consume(1)
        self.assertFalse(success)
        self.assertGreater(retry_after, 0.0)
        self.assertAlmostEqual(
            retry_after, 1.0, places=2
        )  # 1 token / 1 token per second

    def test_token_refill_over_time(self):
        """Test that tokens refill correctly over time."""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10 tokens per second

        # Consume all tokens
        bucket.consume(10)
        self.assertEqual(bucket.remaining_tokens(), 0)

        # Wait 0.5 seconds (should add 5 tokens)
        time.sleep(0.5)
        remaining = bucket.remaining_tokens()
        self.assertGreaterEqual(remaining, 4)  # Allow for timing variance
        self.assertLessEqual(remaining, 6)

        # Wait another 0.5 seconds (should be back to capacity)
        time.sleep(0.5)
        self.assertEqual(bucket.remaining_tokens(), 10)

    def test_capacity_limit(self):
        """Test that refill doesn't exceed capacity."""
        bucket = TokenBucket(capacity=5, refill_rate=10.0)

        # Start with full bucket, wait for more time than needed to fill
        time.sleep(1.0)  # Should add 10 tokens, but capped at 5
        self.assertEqual(bucket.remaining_tokens(), 5)


class TestRateLimiterBasic(unittest.TestCase):
    """Test the main RateLimiter class."""

    def setUp(self):
        self.limiter = RateLimiter(backend=RateLimitBackend.MEMORY)

    def test_default_configuration(self):
        """Test rate limiter with default configuration."""
        # Should allow requests within default limits
        for i in range(10):
            result = self.limiter.check_rate_limit("test_service", "agent1")
            self.assertTrue(result)

    def test_service_configuration(self):
        """Test configuring specific service limits."""
        self.limiter.configure_service(
            "github_api", calls_per_minute=60, burst_capacity=120
        )

        # Verify configuration was stored
        config = self.limiter._get_service_config("github_api")
        self.assertEqual(config["calls_per_minute"], 60)
        self.assertEqual(config["capacity"], 120)
        self.assertEqual(config["refill_rate"], 1.0)  # 60/60 = 1 per second

    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded behavior."""
        # Configure tight limits for testing
        self.limiter.configure_service(
            "strict_service", calls_per_minute=6, burst_capacity=3
        )

        # First few requests should succeed
        for i in range(3):
            result = self.limiter.check_rate_limit("strict_service", "agent1")
            self.assertTrue(result)

        # Next request should fail
        with self.assertRaises(RateLimitExceeded) as cm:
            self.limiter.check_rate_limit("strict_service", "agent1")

        # Verify exception details
        exception = cm.exception
        self.assertGreater(exception.retry_after, 0)
        self.assertEqual(exception.service, "strict_service")
        self.assertIn("Rate limit exceeded", str(exception))

    def test_different_agents_separate_limits(self):
        """Test that different agents have separate rate limits."""
        self.limiter.configure_service(
            "shared_service", calls_per_minute=6, burst_capacity=3
        )

        # Agent 1 uses up its limit
        for i in range(3):
            result = self.limiter.check_rate_limit("shared_service", "agent1")
            self.assertTrue(result)

        # Agent 1 should be rate limited
        with self.assertRaises(RateLimitExceeded):
            self.limiter.check_rate_limit("shared_service", "agent1")

        # Agent 2 should still be able to make requests
        for i in range(3):
            result = self.limiter.check_rate_limit("shared_service", "agent2")
            self.assertTrue(result)

    def test_status_reporting(self):
        """Test rate limit status reporting."""
        self.limiter.configure_service(
            "status_test", calls_per_minute=60, burst_capacity=10
        )

        status = self.limiter.get_status("status_test", "agent1")

        self.assertEqual(status["service"], "status_test")
        self.assertEqual(status["agent_id"], "agent1")
        self.assertEqual(status["capacity"], 10)
        self.assertEqual(status["calls_per_minute"], 60)
        self.assertEqual(status["remaining_tokens"], 10)
        self.assertEqual(status["backend"], "memory")


class TestRateLimitDecorator(unittest.TestCase):
    """Test the rate_limit decorator functionality."""

    def setUp(self):
        # Configure a clean global rate limiter for testing
        configure_global_rate_limiter(backend=RateLimitBackend.MEMORY)
        self.call_count = 0

    def test_basic_decorator_usage(self):
        """Test basic decorator functionality."""

        @rate_limit("test_service", calls_per_minute=60, burst_capacity=5)
        def test_function():
            self.call_count += 1
            return "success"

        # Should work for first few calls
        for i in range(5):
            result = test_function()
            self.assertEqual(result, "success")

        # Should raise exception on rate limit
        with self.assertRaises(RateLimitExceeded):
            test_function()

        self.assertEqual(self.call_count, 5)

    def test_decorator_with_arguments(self):
        """Test decorator works with function arguments."""

        @rate_limit("arg_service", calls_per_minute=60, burst_capacity=3)
        def add_numbers(a, b, multiplier=1):
            return (a + b) * multiplier

        # Should work normally with arguments
        result = add_numbers(2, 3, multiplier=2)
        self.assertEqual(result, 10)

        # Should still respect rate limits
        add_numbers(1, 1)
        add_numbers(2, 2)

        with self.assertRaises(RateLimitExceeded):
            add_numbers(3, 3)


class TestConcurrencyBasic(unittest.TestCase):
    """Test basic thread safety."""

    def setUp(self):
        self.limiter = RateLimiter(backend=RateLimitBackend.MEMORY)
        self.limiter.configure_service(
            "concurrent_test", calls_per_minute=120, burst_capacity=20
        )

    def test_concurrent_requests_same_service(self):
        """Test concurrent requests to the same service."""
        results = []
        errors = []

        def make_requests(thread_id):
            thread_results = []
            try:
                for i in range(5):
                    try:
                        self.limiter.check_rate_limit("concurrent_test", "shared_agent")
                        thread_results.append((thread_id, i, True, None))
                    except RateLimitExceeded as e:
                        thread_results.append((thread_id, i, False, e.retry_after))
                    time.sleep(0.01)  # Small delay
            except Exception as e:
                errors.append((thread_id, str(e)))

            results.extend(thread_results)

        # Run multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_requests, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no unexpected errors
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")

        # Verify we got results from all threads
        self.assertEqual(len(results), 15)  # 3 threads * 5 requests

        # Should have mix of successful and failed requests
        successful = [r for r in results if r[2]]
        failed = [r for r in results if not r[2]]

        self.assertGreater(len(successful), 0)
        self.assertEqual(len(successful) + len(failed), 15)


class TestEdgeCases(unittest.TestCase):
    """Test error handling and edge cases."""

    def test_zero_capacity_handling(self):
        """Test behavior with zero capacity."""
        limiter = RateLimiter()
        limiter.configure_service("zero_cap", calls_per_minute=60, burst_capacity=0)

        # Should always fail with zero capacity
        with self.assertRaises(RateLimitExceeded):
            limiter.check_rate_limit("zero_cap", "agent1")

    def test_very_high_rate_limits(self):
        """Test behavior with very high rate limits."""
        limiter = RateLimiter()
        limiter.configure_service(
            "high_rate", calls_per_minute=10000, burst_capacity=1000
        )

        # Should handle many requests without issue
        for i in range(100):
            result = limiter.check_rate_limit("high_rate", "agent1")
            self.assertTrue(result)

    def test_status_for_nonexistent_service(self):
        """Test status reporting for unconfigured service."""
        limiter = RateLimiter()

        status = limiter.get_status("nonexistent_service", "agent1")

        # Should return default configuration
        self.assertEqual(status["service"], "nonexistent_service")
        self.assertEqual(status["agent_id"], "agent1")
        self.assertIn("capacity", status)
        self.assertIn("calls_per_minute", status)


class TestMemoryBackend(unittest.TestCase):
    """Test the memory-based rate limiting backend."""

    def setUp(self):
        self.backend = MemoryBackend()

    def test_bucket_creation_and_reuse(self):
        """Test that buckets are created and reused correctly."""
        # First access creates bucket
        bucket1 = self.backend.get_bucket("test_key", 10, 1.0)
        self.assertIsInstance(bucket1, TokenBucket)
        self.assertEqual(bucket1.capacity, 10)
        self.assertEqual(bucket1.refill_rate, 1.0)

        # Second access returns same bucket
        bucket2 = self.backend.get_bucket("test_key", 10, 1.0)
        self.assertIs(bucket1, bucket2)

        # Different key creates different bucket
        bucket3 = self.backend.get_bucket("other_key", 5, 2.0)
        self.assertIsNot(bucket1, bucket3)
        self.assertEqual(bucket3.capacity, 5)
        self.assertEqual(bucket3.refill_rate, 2.0)

    def test_clear_all_buckets(self):
        """Test clearing all buckets."""
        self.backend.get_bucket("key1", 10, 1.0)
        self.backend.get_bucket("key2", 20, 2.0)

        self.assertEqual(len(self.backend._buckets), 2)

        self.backend.clear()
        self.assertEqual(len(self.backend._buckets), 0)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
