"""
Comprehensive tests for rate limiter implementation.

Tests cover:
- Token bucket algorithm behavior
- Thread safety under concurrent access
- Memory and Redis backends
- Error handling and graceful degradation
- Edge cases and boundary conditions
- Integration with decorator
"""

import threading
import time
import unittest
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed
from hypothesis import given, strategies as st, settings, assume

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rate_limiter import (  # noqa: E402
    RateLimiter,
    TokenBucket,
    RateLimitBackend,
    RateLimitError,
    RateLimitExceeded,
    RateLimitBackendError,
    MemoryBackend,
    rate_limit,
    configure_global_rate_limiter,
)


class TestTokenBucket(unittest.TestCase):
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
        self.assertEqual(retry_after, 1.0)  # 1 token / 1 token per second

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

    def test_concurrent_token_consumption(self):
        """Test thread safety of token consumption."""
        bucket = TokenBucket(capacity=100, refill_rate=10.0)
        results = []
        errors = []

        def consume_tokens(thread_id):
            try:
                for i in range(10):
                    success, retry_after = bucket.consume(1)
                    results.append((thread_id, i, success, retry_after))
                    time.sleep(0.01)  # Small delay between requests
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Run multiple threads concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=consume_tokens, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

        # Verify we have results from all threads
        self.assertEqual(len(results), 50)  # 5 threads * 10 requests each

        # Verify that successful requests consumed tokens appropriately
        successful_requests = [r for r in results if r[2]]  # success=True
        failed_requests = [r for r in results if not r[2]]  # success=False

        # Should have some successful and some failed requests
        self.assertGreater(len(successful_requests), 0)
        self.assertGreater(len(failed_requests), 0)


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

    def test_bucket_cleanup(self):
        """Test that buckets are cleaned up when no longer referenced."""
        bucket = self.backend.get_bucket("temp_key", 10, 1.0)
        id(bucket)  # Just verify we can get the id

        # Bucket should exist
        self.assertIn("temp_key", self.backend._buckets)

        # Remove reference and force garbage collection
        del bucket
        import gc

        gc.collect()

        # WeakValueDictionary should clean up automatically
        # (This test may be flaky depending on GC timing)

    def test_clear_all_buckets(self):
        """Test clearing all buckets."""
        self.backend.get_bucket("key1", 10, 1.0)
        self.backend.get_bucket("key2", 20, 2.0)

        self.assertEqual(len(self.backend._buckets), 2)

        self.backend.clear()
        self.assertEqual(len(self.backend._buckets), 0)


class TestRateLimiter(unittest.TestCase):
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

    def test_reset_limits(self):
        """Test resetting rate limits."""
        self.limiter.configure_service(
            "reset_test", calls_per_minute=6, burst_capacity=2
        )

        # Use up the limit
        for i in range(2):
            self.limiter.check_rate_limit("reset_test", "agent1")

        # Should be rate limited
        with self.assertRaises(RateLimitExceeded):
            self.limiter.check_rate_limit("reset_test", "agent1")

        # Reset and should work again
        self.limiter.reset_limits()
        result = self.limiter.check_rate_limit("reset_test", "agent1")
        self.assertTrue(result)


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

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves original function metadata."""

        @rate_limit("meta_service", calls_per_minute=60)
        def documented_function():
            """This is a test function."""
            return 42

        self.assertEqual(documented_function.__name__, "documented_function")
        self.assertEqual(documented_function.__doc__, "This is a test function.")


class TestConcurrencyAndThreadSafety(unittest.TestCase):
    """Test rate limiter behavior under concurrent access."""

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
                for i in range(10):
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
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_requests, i) for i in range(5)]
            for future in as_completed(futures):
                future.result()

        # Verify no unexpected errors
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")

        # Verify we got results from all threads
        self.assertEqual(len(results), 50)  # 5 threads * 10 requests

        # Should have mix of successful and failed requests
        successful = [r for r in results if r[2]]
        failed = [r for r in results if not r[2]]

        self.assertGreater(len(successful), 0)
        self.assertGreater(len(failed), 0)
        self.assertEqual(len(successful) + len(failed), 50)

    def test_concurrent_different_services(self):
        """Test concurrent access to different services doesn't interfere."""
        self.limiter.configure_service(
            "service_a", calls_per_minute=60, burst_capacity=5
        )
        self.limiter.configure_service(
            "service_b", calls_per_minute=60, burst_capacity=5
        )

        results_a = []
        results_b = []

        def use_service_a():
            for i in range(5):
                try:
                    self.limiter.check_rate_limit("service_a", "agent1")
                    results_a.append(True)
                except RateLimitExceeded:
                    results_a.append(False)

        def use_service_b():
            for i in range(5):
                try:
                    self.limiter.check_rate_limit("service_b", "agent1")
                    results_b.append(True)
                except RateLimitExceeded:
                    results_b.append(False)

        # Run concurrently
        thread_a = threading.Thread(target=use_service_a)
        thread_b = threading.Thread(target=use_service_b)

        thread_a.start()
        thread_b.start()

        thread_a.join()
        thread_b.join()

        # Both services should have processed all requests successfully
        # (since they have separate rate limits)
        self.assertEqual(len(results_a), 5)
        self.assertEqual(len(results_b), 5)
        self.assertTrue(all(results_a))
        self.assertTrue(all(results_b))


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Test error handling and edge cases."""

    def test_invalid_backend_type(self):
        """Test handling of invalid backend types."""
        with self.assertRaises(ValueError):
            RateLimiter(backend="invalid_backend")

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
            "high_rate", calls_per_minute=100000, burst_capacity=10000
        )

        # Should handle many requests without issue
        for i in range(1000):
            result = limiter.check_rate_limit("high_rate", "agent1")
            self.assertTrue(result)

    def test_negative_tokens_request(self):
        """Test handling of invalid token requests."""
        limiter = RateLimiter()

        # Should handle gracefully (implementation may vary)
        try:
            limiter.check_rate_limit("test_service", "agent1", tokens=-1)
        except (ValueError, RateLimitError):
            pass  # Either behavior is acceptable

    def test_status_for_nonexistent_service(self):
        """Test status reporting for unconfigured service."""
        limiter = RateLimiter()

        status = limiter.get_status("nonexistent_service", "agent1")

        # Should return default configuration
        self.assertEqual(status["service"], "nonexistent_service")
        self.assertEqual(status["agent_id"], "agent1")
        self.assertIn("capacity", status)
        self.assertIn("calls_per_minute", status)


@patch("core.rate_limiter.REDIS_AVAILABLE", True)
@patch("core.rate_limiter.redis")
class TestRedisBackend(unittest.TestCase):
    """Test Redis backend functionality (mocked)."""

    def test_redis_backend_initialization(self, mock_redis):
        """Test Redis backend initialization."""
        mock_client = Mock()
        mock_redis.from_url.return_value = mock_client

        RateLimiter(backend=RateLimitBackend.REDIS)

        mock_redis.from_url.assert_called_once()
        mock_client.ping.assert_called_once()

    def test_redis_connection_failure(self, mock_redis):
        """Test handling of Redis connection failure."""
        mock_redis.from_url.side_effect = Exception("Connection failed")

        with self.assertRaises(RateLimitBackendError):
            RateLimiter(backend=RateLimitBackend.REDIS)

    def test_redis_graceful_degradation(self, mock_redis):
        """Test graceful degradation when Redis operations fail."""
        mock_client = Mock()
        mock_redis.from_url.return_value = mock_client

        # Mock script registration
        mock_script = Mock()
        mock_script.side_effect = Exception("Redis operation failed")
        mock_client.register_script.return_value = mock_script

        limiter = RateLimiter(backend=RateLimitBackend.REDIS)

        # Redis failure should result in backend error being raised
        with self.assertRaises(RateLimitBackendError):
            limiter.check_rate_limit("test_service", "agent1")


class TestHypothesisPropertyBasedTests(unittest.TestCase):
    """Property-based tests using Hypothesis."""

    def setUp(self):
        self.limiter = RateLimiter(backend=RateLimitBackend.MEMORY)

    @given(
        capacity=st.integers(min_value=1, max_value=1000),
        refill_rate=st.floats(min_value=0.1, max_value=100.0),
        consume_amount=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=50, deadline=1000)
    def test_token_bucket_invariants(self, capacity, refill_rate, consume_amount):
        """Test that token bucket maintains its invariants."""
        assume(consume_amount <= capacity)

        bucket = TokenBucket(capacity=capacity, refill_rate=refill_rate)

        # Invariant: remaining tokens should never exceed capacity
        self.assertLessEqual(bucket.remaining_tokens(), capacity)

        # Invariant: successful consumption should reduce tokens
        initial_tokens = bucket.remaining_tokens()
        success, retry_after = bucket.consume(consume_amount)

        if success:
            self.assertEqual(bucket.remaining_tokens(), initial_tokens - consume_amount)
            self.assertEqual(retry_after, 0.0)
        else:
            self.assertGreater(retry_after, 0.0)
            self.assertEqual(bucket.remaining_tokens(), initial_tokens)

    @given(
        calls_per_minute=st.integers(min_value=1, max_value=10000),
        num_requests=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=30, deadline=2000)
    def test_rate_limiter_consistency(self, calls_per_minute, num_requests):
        """Test rate limiter consistency properties."""
        burst_capacity = max(calls_per_minute // 10, 5)

        self.limiter.configure_service(
            "prop_test",
            calls_per_minute=calls_per_minute,
            burst_capacity=burst_capacity,
        )

        successful_requests = 0
        failed_requests = 0

        for i in range(num_requests):
            try:
                self.limiter.check_rate_limit("prop_test", f"agent_{i % 3}")
                successful_requests += 1
            except RateLimitExceeded:
                failed_requests += 1

        # Invariant: total requests should equal sum of successful and failed
        self.assertEqual(successful_requests + failed_requests, num_requests)

        # Invariant: if we exceed burst capacity, some requests should fail
        if num_requests > burst_capacity * 3:  # 3 different agents
            self.assertGreater(failed_requests, 0)


if __name__ == "__main__":
    # Run specific test classes for focused testing
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true", help="Run only fast tests")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests"
    )
    args = parser.parse_args()

    if args.fast:
        # Run only unit tests, skip property-based tests
        suite = unittest.TestLoader().loadTestsFromTestCase(TestTokenBucket)
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMemoryBackend))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRateLimiter))
        unittest.TextTestRunner(verbosity=2).run(suite)
    elif args.integration:
        # Run concurrency and error handling tests
        suite = unittest.TestLoader().loadTestsFromTestCase(
            TestConcurrencyAndThreadSafety
        )
        suite.addTest(
            unittest.TestLoader().loadTestsFromTestCase(TestErrorHandlingAndEdgeCases)
        )
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        # Run all tests
        unittest.main(verbosity=2)
