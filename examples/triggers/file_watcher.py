#!/usr/bin/env uv run python
"""
Example: Watch for Python file changes and run tests
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.triggers import LocalEventSystem
from agents.test_runner_agent import TestRunnerAgent

def on_file_changed(event):
    """Handler for file change events"""
    if event.data.get("path", "").endswith(".py"):
        print(f"Python file changed: {event.data['path']}")
        
        # Run tests
        agent = TestRunnerAgent()
        result = agent.execute_task(f"test {event.data['path']}")
        print(f"Test result: {result.success}")

# Setup watcher
event_system = LocalEventSystem()
event_system.register_file_watcher("src/", "*.py", "python_file_changed")
event_system.watch("python_file_changed", on_file_changed)

# Start processing
event_system.start()
print("Watching for Python file changes in src/...")
print("Press Ctrl+C to stop")

try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    event_system.stop()
    print("\nStopped")
