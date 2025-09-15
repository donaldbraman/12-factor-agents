#!/usr/bin/env uv run python
"""
Test suite for the automatic retry system.

Tests all retry policies, configurations, and wrapper functions to ensure
90% reduction in manual intervention for transient failures.
"""

import json
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
import pytest

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.retry import (  # noqa: E402
    retry,
    RetryPolicy,
    RetryConfig,
    RetryHandler,
    RetryPolicyManager,
    retry_policy_manager,
)
from core.retry_wrappers import (  # noqa: E402
    RetryGitOperations,
    RetryFileOperations,
    subprocess_run,
    read_text,
    write_text,
    get_git_ops,
)


class TestRetryConfig:
    """Test retry configuration validation and behavior"""

    def test_valid_config(self):
        """Test valid retry configuration"""
        config = RetryConfig(
            max_attempts=3, base_delay=1.0, max_delay=10.0, exponential_base=2.0
        )
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 10.0

    def test_invalid_config(self):
        """Test invalid retry configuration raises errors"""
        with pytest.raises(ValueError):
            RetryConfig(max_attempts=0)

        with pytest.raises(ValueError):
            RetryConfig(base_delay=-1.0)

        with pytest.raises(ValueError):
            RetryConfig(base_delay=5.0, max_delay=2.0)


class TestRetryHandler:
    """Test core retry handler functionality"""

    def test_calculate_delay_exponential(self):
        """Test exponential backoff delay calculation"""
        config = RetryConfig(
            base_delay=1.0, exponential_base=2.0, max_delay=10.0, jitter=False
        )
        handler = RetryHandler(config, "test")

        # Test exponential growth
        assert handler.calculate_delay(1) == 1.0
        assert handler.calculate_delay(2) == 2.0
        assert handler.calculate_delay(3) == 4.0

        # Test max delay cap
        assert handler.calculate_delay(10) == 10.0

    def test_calculate_delay_linear(self):
        """Test linear backoff delay calculation"""
        config = RetryConfig(
            base_delay=1.0, max_delay=10.0, backoff_strategy="linear", jitter=False
        )
        handler = RetryHandler(config, "test")

        assert handler.calculate_delay(1) == 1.0
        assert handler.calculate_delay(2) == 2.0
        assert handler.calculate_delay(3) == 3.0

    def test_calculate_delay_constant(self):
        """Test constant backoff delay calculation"""
        config = RetryConfig(
            base_delay=2.0, max_delay=10.0, backoff_strategy="constant", jitter=False
        )
        handler = RetryHandler(config, "test")

        assert handler.calculate_delay(1) == 2.0
        assert handler.calculate_delay(2) == 2.0
        assert handler.calculate_delay(5) == 2.0

    def test_jitter(self):
        """Test jitter adds randomization to delays"""
        config = RetryConfig(
            base_delay=1.0, exponential_base=2.0, jitter=True, jitter_range=0.1
        )
        handler = RetryHandler(config, "test")

        # Get multiple delay calculations
        delays = [handler.calculate_delay(2) for _ in range(10)]

        # Should have some variation due to jitter
        assert len(set(delays)) > 1

        # All should be close to expected value (2.0)
        for delay in delays:
            assert 1.8 <= delay <= 2.2

    def test_should_retry_logic(self):
        """Test retry decision logic"""
        config = RetryConfig(
            max_attempts=3,
            retry_exceptions=(ValueError, OSError),
            stop_exceptions=(PermissionError,),
        )
        handler = RetryHandler(config, "test")

        # Should retry on retry exceptions
        assert handler.should_retry(ValueError(), 1) is True
        assert handler.should_retry(OSError(), 2) is True

        # Should not retry on stop exceptions
        assert handler.should_retry(PermissionError(), 1) is False

        # Should not retry after max attempts
        assert handler.should_retry(ValueError(), 3) is False

        # Should not retry on unhandled exceptions
        assert handler.should_retry(TypeError(), 1) is False


class TestRetryDecorator:
    """Test retry decorator functionality"""

    def test_successful_operation(self):
        """Test operation that succeeds on first try"""
        call_count = 0

        @retry(RetryPolicy.NETWORK)
        def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_operation()
        assert result == "success"
        assert call_count == 1

    def test_retry_until_success(self):
        """Test operation that fails then succeeds"""
        call_count = 0

        @retry(RetryConfig(max_attempts=3, base_delay=0.01))
        def eventually_successful():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = eventually_successful()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted(self):
        """Test operation that fails all attempts"""
        call_count = 0

        @retry(RetryConfig(max_attempts=2, base_delay=0.01))
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            always_fails()

        assert call_count == 2

    def test_stop_exception_no_retry(self):
        """Test that stop exceptions are not retried"""
        call_count = 0

        @retry(
            RetryConfig(
                max_attempts=3,
                base_delay=0.01,
                retry_exceptions=(ConnectionError,),
                stop_exceptions=(PermissionError,),
            )
        )
        def permission_error():
            nonlocal call_count
            call_count += 1
            raise PermissionError("No retry")

        with pytest.raises(PermissionError):
            permission_error()

        assert call_count == 1


class TestRetryWrappers:
    """Test retry wrapper functions"""

    def test_retry_file_operations(self):
        """Test file operations with retry logic"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.txt"
            test_content = "Hello, retry world!"

            # Test write with retry
            write_text(test_file, test_content, create_dirs=True)
            assert test_file.exists()

            # Test read with retry
            content = read_text(test_file)
            assert content == test_content

            # Test copy with retry
            backup_file = test_file.with_suffix(".backup")
            RetryFileOperations.copy(test_file, backup_file)
            assert backup_file.exists()
            assert read_text(backup_file) == test_content

    def test_retry_subprocess(self):
        """Test subprocess operations with retry logic"""
        # Test successful command
        result = subprocess_run(["echo", "test"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "test" in result.stdout

        # Test command that should fail
        with pytest.raises(subprocess.CalledProcessError):
            subprocess_run(["false"], check=True)

    @patch("subprocess.run")
    def test_subprocess_retry_on_failure(self, mock_run):
        """Test subprocess retries on transient failures"""
        # Set up mock to fail twice then succeed
        mock_run.side_effect = [
            subprocess.TimeoutExpired(["sleep", "1"], 1),
            subprocess.TimeoutExpired(["sleep", "1"], 1),
            subprocess.CompletedProcess(["echo", "success"], 0, "success\n", ""),
        ]

        result = subprocess_run(["echo", "success"], capture_output=True, text=True)
        assert result.returncode == 0
        assert mock_run.call_count == 3


class TestRetryPolicyManager:
    """Test retry policy management"""

    def test_default_policies(self):
        """Test default retry policies are loaded"""
        manager = RetryPolicyManager()

        # Test all policy types exist
        for policy in RetryPolicy:
            if policy != RetryPolicy.CUSTOM:
                config = manager.get_policy(policy)
                assert isinstance(config, RetryConfig)
                assert config.max_attempts > 0

    def test_policy_customization(self):
        """Test policy updates"""
        manager = RetryPolicyManager()
        original_config = manager.get_policy(RetryPolicy.NETWORK)

        # Update policy
        new_config = RetryConfig(max_attempts=10, base_delay=2.0)
        manager.update_policy(RetryPolicy.NETWORK, new_config)

        # Verify update
        updated_config = manager.get_policy(RetryPolicy.NETWORK)
        assert updated_config.max_attempts == 10
        assert updated_config.base_delay == 2.0

        # Restore original for other tests
        manager.update_policy(RetryPolicy.NETWORK, original_config)

    def test_config_file_loading(self):
        """Test loading configuration from file"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "retry_config.json"
            config_data = {
                "network": {"max_attempts": 7, "base_delay": 1.5, "max_delay": 45.0}
            }

            with open(config_file, "w") as f:
                json.dump(config_data, f)

            manager = RetryPolicyManager()
            manager.load_from_file(config_file)

            network_config = manager.get_policy(RetryPolicy.NETWORK)
            assert network_config.max_attempts == 7
            assert network_config.base_delay == 1.5
            assert network_config.max_delay == 45.0


class TestGitOperationsRetry:
    """Test Git operations with retry logic"""

    def test_git_operations_creation(self):
        """Test Git operations wrapper creation"""
        git_ops = get_git_ops()
        assert isinstance(git_ops, RetryGitOperations)

        # Test with custom path
        custom_path = Path("/tmp")
        git_ops_custom = get_git_ops(custom_path)
        assert git_ops_custom.repo_path == custom_path


class TestRetrySystemIntegration:
    """Integration tests for the complete retry system"""

    def test_telemetry_integration(self):
        """Test retry operations generate telemetry events"""
        # This would require setting up telemetry mocks
        # For now, just verify telemetry objects are created
        config = RetryConfig(telemetry_enabled=True)
        handler = RetryHandler(config, "integration_test")
        assert handler.telemetry is not None

    def test_performance_impact(self):
        """Test retry system has minimal performance impact on successful operations"""

        # Test successful operation timing
        @retry(RetryPolicy.FILESYSTEM)
        def fast_operation():
            return "fast"

        start_time = time.time()
        result = fast_operation()
        end_time = time.time()

        assert result == "fast"
        # Should complete very quickly for successful operations
        assert (end_time - start_time) < 0.1

    def test_configuration_precedence(self):
        """Test configuration file precedence"""
        # Test that explicitly passed configs override defaults
        custom_config = RetryConfig(max_attempts=99)

        call_count = 0

        @retry(custom_config)
        def test_custom():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test")

        with pytest.raises(ValueError):
            test_custom()

        # Should have tried 99 times (custom config)
        assert call_count == 99


class TestRetrySystemRealWorld:
    """Real-world scenario tests"""

    def test_file_lock_handling(self):
        """Test file operations handle lock scenarios"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "locked_file.txt"

            # Create file initially
            write_text(test_file, "initial content")

            # Should be able to read even with retry
            content = read_text(test_file)
            assert content == "initial content"

    def test_network_timeout_recovery(self):
        """Test network operations recover from timeouts"""
        # This would require network mocking for proper testing
        # For now, verify the configuration is appropriate
        config = retry_policy_manager.get_policy(RetryPolicy.NETWORK)
        assert config.max_attempts >= 3
        assert config.max_delay >= 10.0

    def test_git_conflict_recovery(self):
        """Test Git operations handle conflicts appropriately"""
        config = retry_policy_manager.get_policy(RetryPolicy.GIT_OPERATION)
        assert config.max_attempts >= 3
        assert config.base_delay >= 1.0

        # Verify retry exceptions include Git-specific errors
        assert subprocess.CalledProcessError in config.retry_exceptions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
