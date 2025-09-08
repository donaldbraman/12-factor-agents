#!/usr/bin/env uv run python
"""
Example: Schedule daily code review
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.triggers import LocalEventSystem
from agents.code_review_agent import CodeReviewAgent

def daily_review(event):
    """Handler for scheduled review"""
    print("Running daily code review...")
    
    agent = CodeReviewAgent()
    result = agent.execute_task("review all Python files")
    print(f"Review complete: {result.data}")

# Setup schedule
event_system = LocalEventSystem()
event_system.register_schedule("*/1440 * * * *", daily_review, "daily_review")  # Every 1440 minutes (24 hours)

# Start processing
event_system.start()
print("Daily code review scheduled")
print("Press Ctrl+C to stop")

try:
    import time
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    event_system.stop()
    print("\nStopped")
