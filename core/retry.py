#!/usr/bin/env uv run python
"""
Comprehensive Retry Utilities for 12-factor-agents

Provides configurable retry logic with exponential backoff for common agent failures:
- Network/API operations
- File system operations 
- Git operations
- External process calls

Integrates with the existing telemetry system for failure tracking and analysis.
"""

import asyncio
import functools
import logging
import random
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union
import json

from core.telemetry import EnhancedTelemetryCollector, EventType


class RetryPolicy(Enum):
    """Predefined retry policies for different operation types"""

    NETWORK = "network"
    FILESYSTEM = "filesystem"
    GIT_OPERATION = "git_operation"
    SUBPROCESS = "subprocess"
    API_CALL = "api_call"
    CUSTOM = "custom"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_range: float = 0.1
    retry_exceptions: tuple = (Exception,)
    stop_exceptions: tuple = ()
    backoff_strategy: str = "exponential"  # exponential, linear, constant
    telemetry_enabled: bool = True

    def __post_init__(self):
        """Validate configuration"""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")


class RetryPolicyManager:
    """Manages predefined retry policies for different operation types"""

    def __init__(self):
        self._policies = self._create_default_policies()
        self.telemetry = EnhancedTelemetryCollector()

    def _create_default_policies(self) -> Dict[RetryPolicy, RetryConfig]:
        """Create default retry policies optimized for different operations"""
        return {
            RetryPolicy.NETWORK: RetryConfig(
                max_attempts=5,
                base_delay=1.0,
                max_delay=30.0,
                exponential_base=2.0,
                retry_exceptions=(
                    ConnectionError,
                    TimeoutError,
                    OSError,
                    subprocess.TimeoutExpired,
                ),
                stop_exceptions=(PermissionError, FileNotFoundError),
            ),
            RetryPolicy.FILESYSTEM: RetryConfig(
                max_attempts=3,
                base_delay=0.1,
                max_delay=5.0,
                exponential_base=2.0,
                retry_exceptions=(
                    OSError,
                    PermissionError,
                    FileExistsError,
                    BlockingIOError,
                ),
                stop_exceptions=(FileNotFoundError, IsADirectoryError),
            ),
            RetryPolicy.GIT_OPERATION: RetryConfig(
                max_attempts=4,
                base_delay=2.0,
                max_delay=15.0,
                exponential_base=1.5,
                retry_exceptions=(
                    subprocess.CalledProcessError,
                    subprocess.TimeoutExpired,
                    OSError,
                ),
                stop_exceptions=(),
            ),
            RetryPolicy.SUBPROCESS: RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0,
                exponential_base=2.0,
                retry_exceptions=(
                    subprocess.CalledProcessError,
                    subprocess.TimeoutExpired,
                    OSError,
                ),
                stop_exceptions=(),
            ),
            RetryPolicy.API_CALL: RetryConfig(
                max_attempts=5,
                base_delay=1.0,
                max_delay=60.0,
                exponential_base=2.0,
                retry_exceptions=(
                    ConnectionError,
                    TimeoutError,
                    OSError,
                ),
                stop_exceptions=(PermissionError,),
            ),
        }

    def get_policy(self, policy: RetryPolicy) -> RetryConfig:
        """Get retry configuration for a specific policy"""
        return self._policies[policy]

    def update_policy(self, policy: RetryPolicy, config: RetryConfig):
        """Update a retry policy configuration"""
        self._policies[policy] = config

    def load_from_file(self, config_path: Path):
        """Load retry policies from configuration file"""
        if not config_path.exists():
            return

        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)

            for policy_name, policy_config in config_data.items():
                if hasattr(RetryPolicy, policy_name.upper()):
                    policy = RetryPolicy(policy_name.lower())
                    config = RetryConfig(**policy_config)
                    self._policies[policy] = config

        except Exception as e:
            self.telemetry.record_workflow_event(
                EventType.ERROR,
                "retry_system",
                "RetryPolicyManager",
                f"Failed to load retry policies: {e}",
            )


# Global policy manager instance
retry_policy_manager = RetryPolicyManager()


class RetryHandler:
    """Handles retry logic with telemetry integration"""

    def __init__(self, config: RetryConfig, operation_name: str = "unknown"):
        self.config = config
        self.operation_name = operation_name
        self.telemetry = EnhancedTelemetryCollector()
        self.logger = logging.getLogger(__name__)

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt"""
        if self.config.backoff_strategy == "constant":
            delay = self.config.base_delay
        elif self.config.backoff_strategy == "linear":
            delay = self.config.base_delay * attempt
        else:  # exponential
            delay = self.config.base_delay * (
                self.config.exponential_base ** (attempt - 1)
            )

        # Apply jitter if enabled
        if self.config.jitter:
            jitter = random.uniform(-self.config.jitter_range, self.config.jitter_range)
            delay = delay * (1 + jitter)

        # Ensure delay is within bounds
        return min(max(delay, 0), self.config.max_delay)

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if operation should be retried"""
        # Check if we've exceeded max attempts
        if attempt >= self.config.max_attempts:
            return False

        # Check for stop exceptions (never retry these)
        if isinstance(exception, self.config.stop_exceptions):
            return False

        # Check if exception is in retry list
        return isinstance(exception, self.config.retry_exceptions)

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                # Record attempt if telemetry enabled
                if self.config.telemetry_enabled:
                    self.telemetry.record_workflow_event(
                        EventType.WORKFLOW_START,
                        "retry_system",
                        f"RetryHandler-{self.operation_name}",
                        f"Attempt {attempt}/{self.config.max_attempts}",
                        context={"attempt": attempt, "function": func.__name__},
                    )

                # Execute the function
                result = func(*args, **kwargs)

                # Record success
                if self.config.telemetry_enabled:
                    self.telemetry.record_workflow_event(
                        EventType.WORKFLOW_END,
                        "retry_system",
                        f"RetryHandler-{self.operation_name}",
                        f"Success on attempt {attempt}",
                        context={"attempt": attempt, "success": True},
                    )

                return result

            except Exception as e:
                last_exception = e

                # Log the attempt failure
                self.logger.debug(
                    f"Attempt {attempt} failed for {self.operation_name}: {e}"
                )

                # Record failure
                if self.config.telemetry_enabled:
                    self.telemetry.record_workflow_event(
                        EventType.ERROR,
                        "retry_system",
                        f"RetryHandler-{self.operation_name}",
                        f"Attempt {attempt} failed: {str(e)}",
                        context={
                            "attempt": attempt,
                            "exception_type": type(e).__name__,
                            "exception_message": str(e),
                        },
                    )

                # Check if we should retry
                if not self.should_retry(e, attempt):
                    break

                # Calculate and wait for retry delay
                if attempt < self.config.max_attempts:
                    delay = self.calculate_delay(attempt)
                    self.logger.debug(f"Retrying {self.operation_name} in {delay:.2f}s")
                    time.sleep(delay)

        # All attempts failed
        if self.config.telemetry_enabled:
            self.telemetry.record_workflow_event(
                EventType.AGENT_FAILURE,
                "retry_system",
                f"RetryHandler-{self.operation_name}",
                f"All {self.config.max_attempts} attempts failed",
                context={"final_exception": str(last_exception)},
            )

        raise last_exception


def retry(
    policy: Union[RetryPolicy, RetryConfig] = RetryPolicy.NETWORK,
    operation_name: Optional[str] = None,
):
    """
    Decorator for adding retry logic to functions

    Args:
        policy: Either a RetryPolicy enum or custom RetryConfig
        operation_name: Name for telemetry (defaults to function name)

    Example:
        @retry(RetryPolicy.GIT_OPERATION)
        def git_clone(repo_url, dest_path):
            subprocess.run(['git', 'clone', repo_url, dest_path], check=True)

        @retry(RetryConfig(max_attempts=5, base_delay=2.0))
        def custom_operation():
            # Your code here
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determine retry configuration
            if isinstance(policy, RetryPolicy):
                config = retry_policy_manager.get_policy(policy)
            else:
                config = policy

            # Determine operation name
            op_name = operation_name or func.__name__

            # Create retry handler and execute
            handler = RetryHandler(config, op_name)
            return handler.execute_with_retry(func, *args, **kwargs)

        return wrapper

    return decorator


async def async_retry(
    policy: Union[RetryPolicy, RetryConfig] = RetryPolicy.NETWORK,
    operation_name: Optional[str] = None,
):
    """
    Async version of retry decorator

    Example:
        @async_retry(RetryPolicy.API_CALL)
        async def fetch_data(url):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Determine retry configuration
            if isinstance(policy, RetryPolicy):
                config = retry_policy_manager.get_policy(policy)
            else:
                config = policy

            # Determine operation name
            op_name = operation_name or func.__name__

            handler = RetryHandler(config, op_name)
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    # Record attempt if telemetry enabled
                    if config.telemetry_enabled:
                        handler.telemetry.record_workflow_event(
                            EventType.WORKFLOW_START,
                            "retry_system",
                            f"AsyncRetryHandler-{op_name}",
                            f"Attempt {attempt}/{config.max_attempts}",
                            context={"attempt": attempt, "function": func.__name__},
                        )

                    # Execute the async function
                    result = await func(*args, **kwargs)

                    # Record success
                    if config.telemetry_enabled:
                        handler.telemetry.record_workflow_event(
                            EventType.WORKFLOW_END,
                            "retry_system",
                            f"AsyncRetryHandler-{op_name}",
                            f"Success on attempt {attempt}",
                            context={"attempt": attempt, "success": True},
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # Record failure
                    if config.telemetry_enabled:
                        handler.telemetry.record_workflow_event(
                            EventType.ERROR,
                            "retry_system",
                            f"AsyncRetryHandler-{op_name}",
                            f"Attempt {attempt} failed: {str(e)}",
                            context={
                                "attempt": attempt,
                                "exception_type": type(e).__name__,
                                "exception_message": str(e),
                            },
                        )

                    # Check if we should retry
                    if not handler.should_retry(e, attempt):
                        break

                    # Calculate and wait for retry delay
                    if attempt < config.max_attempts:
                        delay = handler.calculate_delay(attempt)
                        await asyncio.sleep(delay)

            # All attempts failed
            if config.telemetry_enabled:
                handler.telemetry.record_workflow_event(
                    EventType.AGENT_FAILURE,
                    "retry_system",
                    f"AsyncRetryHandler-{op_name}",
                    f"All {config.max_attempts} attempts failed",
                    context={"final_exception": str(last_exception)},
                )

            raise last_exception

        return wrapper

    return decorator


def load_retry_config(config_path: Optional[Path] = None) -> None:
    """
    Load retry configuration from file

    Config file format (JSON):
    {
        "network": {
            "max_attempts": 5,
            "base_delay": 1.0,
            "max_delay": 30.0,
            "exponential_base": 2.0
        },
        "git_operation": {
            "max_attempts": 4,
            "base_delay": 2.0,
            "max_delay": 15.0
        }
    }
    """
    if config_path is None:
        # Look for config in standard locations
        possible_paths = [
            Path("config/retry_policies.json"),
            Path.home() / ".config" / "12-factor-agents" / "retry_policies.json",
            Path("/etc/12-factor-agents/retry_policies.json"),
        ]

        for path in possible_paths:
            if path.exists():
                config_path = path
                break

    if config_path and config_path.exists():
        retry_policy_manager.load_from_file(config_path)


# Initialize configuration on module import
load_retry_config()


def get_retry_stats() -> Dict[str, Any]:
    """Get retry statistics from telemetry data"""
    # This would analyze telemetry data to provide retry statistics
    # Implementation would depend on the specific telemetry storage format
    return {
        "retry_policies_loaded": len(retry_policy_manager._policies),
        "default_policies": list(retry_policy_manager._policies.keys()),
        "telemetry_enabled": True,
    }
