#!/usr/bin/env uv run python
"""
Loop Protection System for preventing infinite loops and recursive execution
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib


class LoopProtection:
    """
    Protects against infinite loops and recursive execution patterns
    """

    def __init__(self, max_iterations: int = 5, time_window_minutes: int = 10):
        self.max_iterations = max_iterations
        self.time_window = timedelta(minutes=time_window_minutes)
        self.operation_history: Dict[str, list] = {}
        self.operation_counts: Dict[str, int] = {}

    def check_operation(
        self,
        operation_type: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Check if an operation should be allowed to proceed
        Returns True if safe, False if loop detected
        """
        # Generate unique key for this operation
        operation_key = (
            f"{operation_type}:{hashlib.md5(content.encode()).hexdigest()[:8]}"
        )

        current_time = datetime.now()

        # Initialize if first time
        if operation_key not in self.operation_history:
            self.operation_history[operation_key] = []
            self.operation_counts[operation_key] = 0

        # Clean old entries outside time window
        self.operation_history[operation_key] = [
            timestamp
            for timestamp in self.operation_history[operation_key]
            if current_time - timestamp < self.time_window
        ]

        # Check if we've exceeded max iterations
        recent_count = len(self.operation_history[operation_key])
        if recent_count >= self.max_iterations:
            return False  # Loop detected!

        # Record this operation
        self.operation_history[operation_key].append(current_time)
        self.operation_counts[operation_key] += 1

        return True  # Safe to proceed

    def reset(self):
        """Reset all loop protection state"""
        self.operation_history.clear()
        self.operation_counts.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about loop protection"""
        return {
            "total_operations": sum(self.operation_counts.values()),
            "unique_operations": len(self.operation_counts),
            "most_repeated": max(self.operation_counts.items(), key=lambda x: x[1])
            if self.operation_counts
            else None,
        }


# Global instance for shared use
LOOP_PROTECTION = LoopProtection()
