#!/usr/bin/env python3
"""
Simple Logging - Structured logging using Python's built-in capabilities

Instead of complex logging frameworks, we use Python's built-in logging
with sensible defaults and simple configuration.

This solves Issue #085: Improve Logging Configuration
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_simple_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_style: str = "structured",
) -> logging.Logger:
    """
    Set up simple, effective logging using Python's built-in capabilities.

    Args:
        level: Log level ("DEBUG", "INFO", "WARNING", "ERROR")
        log_file: Optional file to log to (in addition to console)
        format_style: "structured" or "simple"

    Returns:
        Configured root logger
    """

    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set log level
    root_logger.setLevel(getattr(logging, level.upper()))

    # Choose format
    if format_style == "structured":
        log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    else:
        log_format = "%(asctime)s %(levelname)s: %(message)s"

    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler (always present)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module/function.

    Usage:
        logger = get_logger(__name__)
        logger.info("Task completed")
    """
    return logging.getLogger(name)


class AgentLogger:
    """
    Simple logger wrapper for agent functions.

    Provides consistent logging patterns for our stateless agent functions.
    """

    def __init__(self, agent_name: str, context_id: str = ""):
        self.agent_name = agent_name
        self.context_id = context_id
        self.logger = logging.getLogger(f"agent.{agent_name}")

    def start_operation(self, operation: str, **kwargs):
        """Log start of an operation"""
        context = f"[{self.context_id}] " if self.context_id else ""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())

        message = f"{context}🚀 Starting: {operation}"
        if extra_info:
            message += f" | {extra_info}"

        self.logger.info(message)

    def complete_operation(self, operation: str, **kwargs):
        """Log successful completion of an operation"""
        context = f"[{self.context_id}] " if self.context_id else ""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())

        message = f"{context}✅ Completed: {operation}"
        if extra_info:
            message += f" | {extra_info}"

        self.logger.info(message)

    def fail_operation(self, operation: str, error: str, **kwargs):
        """Log failed operation"""
        context = f"[{self.context_id}] " if self.context_id else ""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())

        message = f"{context}❌ Failed: {operation} | Error: {error}"
        if extra_info:
            message += f" | {extra_info}"

        self.logger.error(message)

    def info(self, message: str, **kwargs):
        """Log info message"""
        context = f"[{self.context_id}] " if self.context_id else ""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())

        full_message = f"{context}{message}"
        if extra_info:
            full_message += f" | {extra_info}"

        self.logger.info(full_message)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        context = f"[{self.context_id}] " if self.context_id else ""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())

        full_message = f"{context}⚠️ {message}"
        if extra_info:
            full_message += f" | {extra_info}"

        self.logger.warning(full_message)

    def error(self, message: str, **kwargs):
        """Log error message"""
        context = f"[{self.context_id}] " if self.context_id else ""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())

        full_message = f"{context}🔴 {message}"
        if extra_info:
            full_message += f" | {extra_info}"

        self.logger.error(full_message)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        context = f"[{self.context_id}] " if self.context_id else ""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())

        full_message = f"{context}🔍 {message}"
        if extra_info:
            full_message += f" | {extra_info}"

        self.logger.debug(full_message)


def create_agent_logger(agent_name: str, context_id: str = "") -> AgentLogger:
    """
    Create a logger for an agent function.

    Usage:
        logger = create_agent_logger("issue_analyzer", "task-123")
        logger.start_operation("Analyzing issue", issue_number=42)
        logger.complete_operation("Analyzing issue", complexity="medium")
    """
    return AgentLogger(agent_name, context_id)


# Convenience functions for simple logging
def log_agent_start(agent_name: str, operation: str, context_id: str = "", **kwargs):
    """Quick way to log agent operation start"""
    logger = create_agent_logger(agent_name, context_id)
    logger.start_operation(operation, **kwargs)


def log_agent_success(agent_name: str, operation: str, context_id: str = "", **kwargs):
    """Quick way to log agent operation success"""
    logger = create_agent_logger(agent_name, context_id)
    logger.complete_operation(operation, **kwargs)


def log_agent_failure(
    agent_name: str, operation: str, error: str, context_id: str = "", **kwargs
):
    """Quick way to log agent operation failure"""
    logger = create_agent_logger(agent_name, context_id)
    logger.fail_operation(operation, error, **kwargs)


# Initialize default logging
def init_default_logging():
    """Initialize sensible default logging for the application"""

    # Create logs directory
    logs_dir = Path.cwd() / "logs"
    log_file = logs_dir / f"12factor-agents-{datetime.now().strftime('%Y%m%d')}.log"

    # Set up structured logging
    setup_simple_logging(level="INFO", log_file=log_file, format_style="structured")

    # Log startup
    logger = get_logger("12factor-agents")
    logger.info("🚀 12-factor-agents logging initialized")
    logger.info(f"📝 Logging to: {log_file}")


# Example usage
if __name__ == "__main__":
    # Demo the logging system
    init_default_logging()

    # Example: Agent function logging
    agent_logger = create_agent_logger("issue_analyzer", "task-42")

    agent_logger.start_operation(
        "Analyzing issue", issue_number=123, complexity="medium"
    )
    agent_logger.info("Found 3 relevant files")
    agent_logger.warning("Issue description is vague", confidence=0.6)
    agent_logger.complete_operation(
        "Analyzing issue", files_found=3, analysis_time="2.3s"
    )

    # Example: Simple function logging
    logger = get_logger(__name__)
    logger.info("Demo completed successfully")

    print("\n🧪 Simple logging system ready!")
    print("✅ Uses Python's built-in logging")
    print("✅ Structured format with timestamps")
    print("✅ Agent-specific logging patterns")
    print("✅ No complex dependencies")
