#!/usr/bin/env python3
"""
Test suite to demonstrate the value of retry logic for failed operations.
We'll test both WITH and WITHOUT retry to show the improvement.
"""

import pytest
import time

from core.tools import ToolResponse


class TestRetryLogicValue:
    """Demonstrate how retry logic improves reliability"""

    def test_intermittent_network_failure_without_retry(self):
        """Show how operations fail without retry logic"""
        # Simulate an API or network tool that fails intermittently
        call_count = 0

        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fails first 2 times
                raise ConnectionError("Network timeout")
            return {"success": True, "data": "Finally worked!"}

        # Without retry - fails immediately
        with pytest.raises(ConnectionError):
            result = flaky_operation()

        assert call_count == 1  # Only tried once

    def test_intermittent_network_failure_with_retry(self):
        """Show how retry logic handles transient failures"""
        call_count = 0

        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fails first 2 times
                raise ConnectionError("Network timeout")
            return {"success": True, "data": "Finally worked!"}

        # With retry logic (simulated)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = flaky_operation()
                break
            except ConnectionError:
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.1 * (2**attempt))  # Exponential backoff

        assert call_count == 3  # Tried 3 times
        assert result["success"] == True

    def test_file_lock_contention_without_retry(self):
        """Show how file operations fail when file is temporarily locked"""

        class FileToolWithoutRetry:
            def write(self, path: str, content: str) -> ToolResponse:
                # Simulate file being locked by another process
                raise PermissionError("File is locked by another process")

        tool = FileToolWithoutRetry()

        # Without retry - fails immediately
        with pytest.raises(PermissionError):
            tool.write("/tmp/test.txt", "content")

    def test_file_lock_contention_with_retry(self):
        """Show how retry logic handles temporary file locks"""

        class FileToolWithRetry:
            def __init__(self):
                self.attempts = 0

            def write(
                self, path: str, content: str, max_retries: int = 3
            ) -> ToolResponse:
                for attempt in range(max_retries):
                    try:
                        self.attempts += 1
                        if self.attempts < 3:
                            # Simulate file being locked first 2 attempts
                            raise PermissionError("File is locked")
                        # Third attempt succeeds
                        return ToolResponse(success=True, data={"written": True})
                    except PermissionError as e:
                        if attempt == max_retries - 1:
                            return ToolResponse(success=False, error=str(e))
                        time.sleep(0.1 * (2**attempt))

        tool = FileToolWithRetry()
        result = tool.write("/tmp/test.txt", "content")

        assert result.success == True
        assert tool.attempts == 3

    def test_git_operation_race_condition(self):
        """Show how retry helps with git operations that can race"""

        class GitToolWithoutRetry:
            def commit(self, message: str) -> ToolResponse:
                # Simulate git index.lock exists
                raise RuntimeError(
                    "fatal: Unable to create '.git/index.lock': File exists"
                )

        class GitToolWithRetry:
            def __init__(self):
                self.attempts = 0

            def commit(self, message: str, max_retries: int = 3) -> ToolResponse:
                for attempt in range(max_retries):
                    try:
                        self.attempts += 1
                        if self.attempts < 2:
                            raise RuntimeError(
                                "fatal: Unable to create '.git/index.lock': File exists"
                            )
                        return ToolResponse(success=True, data={"committed": True})
                    except RuntimeError as e:
                        if attempt == max_retries - 1:
                            return ToolResponse(success=False, error=str(e))
                        time.sleep(0.5)  # Wait for lock to clear

        # Without retry
        tool_no_retry = GitToolWithoutRetry()
        with pytest.raises(RuntimeError):
            tool_no_retry.commit("test commit")

        # With retry
        tool_with_retry = GitToolWithRetry()
        result = tool_with_retry.commit("test commit")
        assert result.success == True
        assert tool_with_retry.attempts == 2

    def test_api_rate_limiting(self):
        """Show how exponential backoff helps with rate limits"""

        class APITool:
            def __init__(self):
                self.last_call = 0
                self.min_interval = 1.0  # 1 second rate limit

            def call_api_without_retry(self):
                now = time.time()
                if now - self.last_call < self.min_interval:
                    raise RuntimeError("Rate limit exceeded")
                self.last_call = now
                return {"data": "success"}

            def call_api_with_retry(self, max_retries: int = 3):
                for attempt in range(max_retries):
                    try:
                        return self.call_api_without_retry()
                    except RuntimeError:
                        if attempt == max_retries - 1:
                            raise
                        # Exponential backoff: 0.5s, 1s, 2s
                        time.sleep(0.5 * (2**attempt))

        tool = APITool()

        # First call succeeds
        tool.call_api_without_retry()

        # Immediate second call fails without retry
        with pytest.raises(RuntimeError):
            tool.call_api_without_retry()

        # Reset
        tool.last_call = time.time()

        # With retry and backoff, it eventually succeeds
        result = tool.call_api_with_retry()
        assert result == {"data": "success"}

    def test_retry_metrics(self):
        """Show how we can track retry success rates for monitoring"""

        class RetryMetrics:
            def __init__(self):
                self.total_operations = 0
                self.retry_needed = 0
                self.retry_succeeded = 0
                self.retry_failed = 0

            def execute_with_retry(self, operation, max_retries: int = 3):
                self.total_operations += 1

                for attempt in range(max_retries):
                    try:
                        result = operation()
                        if attempt > 0:
                            self.retry_succeeded += 1
                        return result
                    except Exception:
                        if attempt == 0:
                            self.retry_needed += 1
                        if attempt == max_retries - 1:
                            self.retry_failed += 1
                            raise
                        time.sleep(0.1 * (2**attempt))

            def success_rate(self):
                if self.retry_needed == 0:
                    return 100.0
                return (self.retry_succeeded / self.retry_needed) * 100

        metrics = RetryMetrics()

        # Simulate various operations
        def always_works():
            return "success"

        def works_second_time():
            if not hasattr(works_second_time, "called"):
                works_second_time.called = True
                raise ValueError("First attempt fails")
            return "success"

        def works_third_time():
            if not hasattr(works_third_time, "count"):
                works_third_time.count = 0
            works_third_time.count += 1
            if works_third_time.count < 3:
                raise ValueError(f"Attempt {works_third_time.count} fails")
            return "success"

        # Execute operations
        metrics.execute_with_retry(always_works)
        metrics.execute_with_retry(works_second_time)
        metrics.execute_with_retry(works_third_time)

        # Check metrics
        assert metrics.total_operations == 3
        assert metrics.retry_needed == 2  # 2 operations needed retry
        assert metrics.retry_succeeded == 2  # Both succeeded after retry
        assert metrics.retry_failed == 0
        assert metrics.success_rate() == 100.0

        print("\nRetry Metrics:")
        print(f"  Total operations: {metrics.total_operations}")
        print(f"  Needed retry: {metrics.retry_needed}")
        print(f"  Retry success rate: {metrics.success_rate():.1f}%")


class TestRetryConfiguration:
    """Test different retry configurations for different scenarios"""

    def test_configurable_retry_strategies(self):
        """Show how different operations need different retry strategies"""

        strategies = {
            "file_operation": {
                "max_retries": 3,
                "base_delay": 0.1,
                "max_delay": 1.0,
                "exponential": True,
            },
            "network_operation": {
                "max_retries": 5,
                "base_delay": 1.0,
                "max_delay": 30.0,
                "exponential": True,
            },
            "git_operation": {
                "max_retries": 3,
                "base_delay": 0.5,
                "max_delay": 2.0,
                "exponential": False,  # Linear backoff for git locks
            },
            "critical_operation": {
                "max_retries": 1,  # Don't retry dangerous operations
                "base_delay": 0,
                "max_delay": 0,
                "exponential": False,
            },
        }

        def calculate_delay(strategy: dict, attempt: int) -> float:
            if attempt == 0:
                return 0

            if strategy["exponential"]:
                delay = strategy["base_delay"] * (2 ** (attempt - 1))
            else:
                delay = strategy["base_delay"] * attempt

            return min(delay, strategy["max_delay"])

        # Test file operation delays (fast, short backoff)
        file_delays = [
            calculate_delay(strategies["file_operation"], i) for i in range(4)
        ]
        assert file_delays == [0, 0.1, 0.2, 0.4]

        # Test network operation delays (slower, longer backoff)
        net_delays = [
            calculate_delay(strategies["network_operation"], i) for i in range(4)
        ]
        assert net_delays == [0, 1.0, 2.0, 4.0]

        # Test git operation delays (linear)
        git_delays = [calculate_delay(strategies["git_operation"], i) for i in range(4)]
        assert git_delays == [0, 0.5, 1.0, 1.5]

        # Test critical operation (no retry)
        crit_delays = [
            calculate_delay(strategies["critical_operation"], i) for i in range(2)
        ]
        assert crit_delays == [0, 0]


if __name__ == "__main__":
    # Run the tests to show the value
    print("🧪 Testing Retry Logic Value...\n")

    # Show the difference
    test = TestRetryLogicValue()

    print("❌ Without Retry:")
    try:
        test.test_intermittent_network_failure_without_retry()
        print("   Failed on first network error")
    except AssertionError:
        pass

    print("\n✅ With Retry:")
    test.test_intermittent_network_failure_with_retry()
    print("   Succeeded after 3 attempts")

    print("\n📊 Retry Metrics Example:")
    test.test_retry_metrics()

    print("\n⚙️ Configuration Strategies:")
    config_test = TestRetryConfiguration()
    config_test.test_configurable_retry_strategies()
    print("   Different retry strategies for different operations")
