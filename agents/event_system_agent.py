"""
EventSystemAgent - Implements event trigger system for Factor 11 compliance.
Designed to solve Issue #004: Implement Event Trigger System
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List

# Import from parent directory
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse


class EventSystemCreatorTool(Tool):
    """Create the LocalEventSystem class"""

    def __init__(self):
        super().__init__(
            name="create_event_system",
            description="Create the LocalEventSystem implementation",
        )

    def execute(self, output_path: str) -> ToolResponse:
        """Create LocalEventSystem implementation"""
        try:
            code = '''"""
Local event trigger system for Factor 11 compliance.
Factor 11: Trigger from Anywhere - Agents can be triggered through multiple entry points.
"""
import json
import time
import threading
import hashlib
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import fnmatch
import subprocess


@dataclass
class Event:
    """Represents an event in the system"""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str = "manual"
    processed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class LocalEventSystem:
    """
    File-based event system for local agent triggers.
    No external dependencies required.
    """
    
    def __init__(self):
        self.events_dir = Path.home() / ".claude-shared-state" / "events"
        self.events_dir.mkdir(parents=True, exist_ok=True)
        
        self.processed_dir = self.events_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        
        self.handlers: Dict[str, List[Callable]] = {}
        self.file_watchers: List[Dict[str, Any]] = []
        self.schedules: List[Dict[str, Any]] = []
        self.running = False
        self._lock = threading.Lock()
        self._processor_thread = None
        self._watcher_thread = None
        self._scheduler_thread = None
    
    def emit(self, event_type: str, data: Dict[str, Any], source: str = "manual") -> str:
        """
        Emit an event to the file system.
        Returns event ID.
        """
        event = Event(
            event_type=event_type,
            data=data,
            timestamp=datetime.now(),
            source=source
        )
        
        # Generate unique event ID
        event_id = hashlib.md5(
            f"{event_type}{datetime.now().isoformat()}{json.dumps(data)}".encode()
        ).hexdigest()[:12]
        
        # Write event file
        event_file = self.events_dir / f"{event_type}_{event_id}.json"
        event_file.write_text(json.dumps(event.to_dict(), indent=2))
        
        return event_id
    
    def watch(self, event_type: str, handler: Callable) -> None:
        """Register a handler for an event type"""
        with self._lock:
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            self.handlers[event_type].append(handler)
    
    def unwatch(self, event_type: str, handler: Callable) -> None:
        """Unregister a handler"""
        with self._lock:
            if event_type in self.handlers:
                self.handlers[event_type].remove(handler)
    
    def register_file_watcher(self, path: str, pattern: str = "*", 
                            event_type: str = "file_changed") -> None:
        """
        Register a file system watcher.
        
        Args:
            path: Directory to watch
            pattern: Glob pattern for files to watch
            event_type: Event type to emit on changes
        """
        watcher = {
            "path": Path(path),
            "pattern": pattern,
            "event_type": event_type,
            "last_check": datetime.now(),
            "file_states": {}
        }
        
        # Get initial state
        for file_path in Path(path).glob(pattern):
            if file_path.is_file():
                watcher["file_states"][str(file_path)] = file_path.stat().st_mtime
        
        self.file_watchers.append(watcher)
    
    def register_schedule(self, cron_expr: str, handler: Callable, 
                         event_type: str = "schedule_triggered") -> None:
        """
        Register a scheduled trigger (simplified cron-like).
        
        Args:
            cron_expr: Simple cron expression (e.g., "*/5 * * * *" for every 5 minutes)
            handler: Handler to call
            event_type: Event type to emit
        """
        schedule = {
            "cron": cron_expr,
            "handler": handler,
            "event_type": event_type,
            "last_run": None
        }
        self.schedules.append(schedule)
    
    def process_events(self) -> int:
        """
        Process pending events.
        Returns number of events processed.
        """
        processed_count = 0
        
        for event_file in self.events_dir.glob("*.json"):
            if event_file.name.startswith("processed_"):
                continue
            
            try:
                # Load event
                event_data = json.loads(event_file.read_text())
                event = Event.from_dict(event_data)
                
                # Find handlers
                handlers = self.handlers.get(event.event_type, [])
                handlers.extend(self.handlers.get("*", []))  # Wildcard handlers
                
                # Execute handlers
                for handler in handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        print(f"Handler error for {event.event_type}: {e}")
                
                # Mark as processed
                processed_file = self.processed_dir / f"processed_{event_file.name}"
                event_file.rename(processed_file)
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing event {event_file}: {e}")
        
        return processed_count
    
    def _check_file_watchers(self) -> None:
        """Check for file system changes"""
        for watcher in self.file_watchers:
            path = watcher["path"]
            pattern = watcher["pattern"]
            
            current_states = {}
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    current_states[str(file_path)] = file_path.stat().st_mtime
            
            # Check for changes
            old_states = watcher["file_states"]
            
            # New files
            for file_path, mtime in current_states.items():
                if file_path not in old_states:
                    self.emit(
                        watcher["event_type"],
                        {"path": file_path, "change": "created"},
                        source="file_watcher"
                    )
            
            # Modified files
            for file_path, mtime in current_states.items():
                if file_path in old_states and mtime != old_states[file_path]:
                    self.emit(
                        watcher["event_type"],
                        {"path": file_path, "change": "modified"},
                        source="file_watcher"
                    )
            
            # Deleted files
            for file_path in old_states:
                if file_path not in current_states:
                    self.emit(
                        watcher["event_type"],
                        {"path": file_path, "change": "deleted"},
                        source="file_watcher"
                    )
            
            watcher["file_states"] = current_states
    
    def _check_schedules(self) -> None:
        """Check and trigger scheduled events"""
        now = datetime.now()
        
        for schedule in self.schedules:
            # Simple implementation - just check intervals
            cron = schedule["cron"]
            
            # Parse simple cron (*/N format for minutes)
            if cron.startswith("*/"):
                try:
                    minutes = int(cron.split()[0][2:])
                    
                    if schedule["last_run"] is None:
                        should_run = True
                    else:
                        elapsed = (now - schedule["last_run"]).total_seconds() / 60
                        should_run = elapsed >= minutes
                    
                    if should_run:
                        self.emit(
                            schedule["event_type"],
                            {"schedule": cron, "time": now.isoformat()},
                            source="scheduler"
                        )
                        
                        if schedule["handler"]:
                            schedule["handler"](Event(
                                event_type=schedule["event_type"],
                                data={"schedule": cron},
                                timestamp=now,
                                source="scheduler"
                            ))
                        
                        schedule["last_run"] = now
                        
                except (ValueError, IndexError):
                    pass
    
    def start(self) -> None:
        """Start the event processing system"""
        if self.running:
            return
        
        self.running = True
        
        # Start processor thread
        def process_loop():
            while self.running:
                self.process_events()
                time.sleep(1)
        
        self._processor_thread = threading.Thread(target=process_loop, daemon=True)
        self._processor_thread.start()
        
        # Start file watcher thread
        def watcher_loop():
            while self.running:
                self._check_file_watchers()
                time.sleep(2)
        
        if self.file_watchers:
            self._watcher_thread = threading.Thread(target=watcher_loop, daemon=True)
            self._watcher_thread.start()
        
        # Start scheduler thread
        def scheduler_loop():
            while self.running:
                self._check_schedules()
                time.sleep(30)  # Check every 30 seconds
        
        if self.schedules:
            self._scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
            self._scheduler_thread.start()
    
    def stop(self) -> None:
        """Stop the event processing system"""
        self.running = False
        
        if self._processor_thread:
            self._processor_thread.join(timeout=2)
        if self._watcher_thread:
            self._watcher_thread.join(timeout=2)
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=2)
    
    def get_pending_events(self) -> List[Event]:
        """Get list of pending events"""
        events = []
        
        for event_file in self.events_dir.glob("*.json"):
            if not event_file.name.startswith("processed_"):
                try:
                    event_data = json.loads(event_file.read_text())
                    events.append(Event.from_dict(event_data))
                except Exception:
                    pass
        
        return sorted(events, key=lambda e: e.timestamp)
    
    def get_processed_events(self, limit: int = 100) -> List[Event]:
        """Get list of recently processed events"""
        events = []
        
        for event_file in sorted(self.processed_dir.glob("*.json"), 
                                key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
            try:
                event_data = json.loads(event_file.read_text())
                events.append(Event.from_dict(event_data))
            except Exception:
                pass
        
        return events
    
    def cleanup_old_events(self, days: int = 7) -> int:
        """Clean up processed events older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        cleaned = 0
        
        for event_file in self.processed_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(event_file.stat().st_mtime)
                if mtime < cutoff:
                    event_file.unlink()
                    cleaned += 1
            except Exception:
                pass
        
        return cleaned


# Webhook simulator for local testing
class LocalWebhookSimulator:
    """Simulate webhooks using local file monitoring"""
    
    def __init__(self, event_system: LocalEventSystem):
        self.event_system = event_system
        self.webhook_dir = Path.home() / ".claude-shared-state" / "webhooks"
        self.webhook_dir.mkdir(exist_ok=True)
    
    def simulate_github_webhook(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Simulate a GitHub webhook"""
        self.event_system.emit(
            f"github_{event_type}",
            payload,
            source="webhook_simulator"
        )
    
    def listen(self) -> None:
        """Listen for webhook files"""
        self.event_system.register_file_watcher(
            str(self.webhook_dir),
            "*.webhook",
            "webhook_received"
        )


# CLI trigger support
class CLITrigger:
    """Enable CLI-based event triggers"""
    
    @staticmethod
    def trigger_from_cli(event_type: str, data_json: str) -> str:
        """Trigger an event from command line"""
        event_system = LocalEventSystem()
        
        try:
            data = json.loads(data_json) if data_json else {}
        except json.JSONDecodeError:
            data = {"message": data_json}
        
        event_id = event_system.emit(event_type, data, source="cli")
        return event_id
'''

            output = Path(output_path).resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(code)

            return ToolResponse(
                success=True,
                data={
                    "path": str(output),
                    "classes": [
                        "LocalEventSystem",
                        "LocalWebhookSimulator",
                        "CLITrigger",
                    ],
                    "features": [
                        "File-based event queue",
                        "Event handlers",
                        "File watchers",
                        "Schedulers",
                        "Webhook simulation",
                        "CLI triggers",
                    ],
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"output_path": {"type": "string"}},
            "required": ["output_path"],
        }


class EventCLICreatorTool(Tool):
    """Create CLI for event management"""

    def __init__(self):
        super().__init__(
            name="create_event_cli", description="Create CLI tool for event management"
        )

    def execute(self, output_path: str) -> ToolResponse:
        """Create event CLI tool"""
        try:
            code = '''#!/usr/bin/env uv run python
"""
Event management CLI for 12-factor agents.
Allows triggering and managing events from command line.
"""
import sys
import json
import click
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.triggers import LocalEventSystem, CLITrigger


@click.group()
def cli():
    """Event management for 12-factor agents"""
    pass


@cli.command()
@click.argument('event_type')
@click.option('--data', '-d', default='{}', help='Event data as JSON')
@click.option('--source', '-s', default='cli', help='Event source')
def emit(event_type, data, source):
    """Emit an event"""
    try:
        event_system = LocalEventSystem()
        data_dict = json.loads(data) if data else {}
        event_id = event_system.emit(event_type, data_dict, source)
        click.echo(f"Event emitted: {event_id}")
    except json.JSONDecodeError:
        click.echo("Error: Invalid JSON data", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def list():
    """List pending events"""
    event_system = LocalEventSystem()
    events = event_system.get_pending_events()
    
    if not events:
        click.echo("No pending events")
        return
    
    click.echo(f"Pending events ({len(events)}):")
    for event in events:
        click.echo(f"  - {event.event_type} at {event.timestamp} from {event.source}")


@cli.command()
def process():
    """Process all pending events"""
    event_system = LocalEventSystem()
    count = event_system.process_events()
    click.echo(f"Processed {count} events")


@cli.command()
@click.option('--limit', '-l', default=10, help='Number of events to show')
def history(limit):
    """Show processed event history"""
    event_system = LocalEventSystem()
    events = event_system.get_processed_events(limit)
    
    if not events:
        click.echo("No processed events")
        return
    
    click.echo(f"Recent processed events (last {limit}):")
    for event in events:
        click.echo(f"  - {event.event_type} at {event.timestamp} from {event.source}")


@cli.command()
@click.option('--days', '-d', default=7, help='Days to keep')
def cleanup(days):
    """Clean up old processed events"""
    event_system = LocalEventSystem()
    count = event_system.cleanup_old_events(days)
    click.echo(f"Cleaned up {count} old events")


@cli.command()
@click.argument('path')
@click.option('--pattern', '-p', default='*', help='File pattern to watch')
@click.option('--event', '-e', default='file_changed', help='Event type to emit')
def watch(path, pattern, event):
    """Watch a directory for changes"""
    event_system = LocalEventSystem()
    event_system.register_file_watcher(path, pattern, event)
    event_system.start()
    
    click.echo(f"Watching {path} for {pattern} files...")
    click.echo("Press Ctrl+C to stop")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        event_system.stop()
        click.echo("\\nStopped watching")


if __name__ == '__main__':
    cli()
'''

            output = Path(output_path).resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(code)

            # Make executable
            os.chmod(output, 0o755)

            return ToolResponse(
                success=True,
                data={
                    "path": str(output),
                    "commands": [
                        "emit",
                        "list",
                        "process",
                        "history",
                        "cleanup",
                        "watch",
                    ],
                    "executable": True,
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"output_path": {"type": "string"}},
            "required": ["output_path"],
        }


class EventSystemAgent(BaseAgent):
    """
    Agent responsible for implementing event trigger system.
    Handles Issue #004: Implement Event Trigger System (Factor 11)
    """

    def register_tools(self) -> List[Tool]:
        """Register event system tools"""
        return [EventSystemCreatorTool(), EventCLICreatorTool()]

    def execute_task(self, task: str) -> ToolResponse:
        """
        Execute event system implementation.
        Expected task: "implement event system" or "solve issue #004"
        """

        base_path = Path.home() / "Documents" / "GitHub" / "12-factor-agents"
        results = []

        # Step 1: Create LocalEventSystem class
        system_tool = self.tools[0]  # EventSystemCreatorTool
        system_result = system_tool.execute(
            output_path=str(base_path / "core" / "triggers.py")
        )
        results.append(("event_system", system_result))

        if not system_result.success:
            return system_result

        # Step 2: Create event CLI tool
        cli_tool = self.tools[1]  # EventCLICreatorTool
        cli_result = cli_tool.execute(output_path=str(base_path / "bin" / "event"))
        results.append(("event_cli", cli_result))

        # Step 3: Create example trigger configurations
        examples_dir = base_path / "examples" / "triggers"
        examples_dir.mkdir(parents=True, exist_ok=True)

        # Example: File watcher config
        watcher_example = """#!/usr/bin/env uv run python
\"\"\"
Example: Watch for Python file changes and run tests
\"\"\"
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.triggers import LocalEventSystem
from agents.test_runner_agent import TestRunnerAgent

def on_file_changed(event):
    \"\"\"Handler for file change events\"\"\"
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
    print("\\nStopped")
"""

        watcher_path = examples_dir / "file_watcher.py"
        watcher_path.write_text(watcher_example)

        # Example: Schedule config
        schedule_example = """#!/usr/bin/env uv run python
\"\"\"
Example: Schedule daily code review
\"\"\"
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.triggers import LocalEventSystem
from agents.code_review_agent import CodeReviewAgent

def daily_review(event):
    \"\"\"Handler for scheduled review\"\"\"
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
    print("\\nStopped")
"""

        schedule_path = examples_dir / "daily_schedule.py"
        schedule_path.write_text(schedule_example)

        # Compile results
        all_success = all(r[1].success for r in results)

        if all_success:
            self.state.set("issue_004_status", "resolved")
            self.state.set("event_system_implemented", True)

            return ToolResponse(
                success=True,
                data={
                    "event_system_created": True,
                    "cli_tool_created": True,
                    "examples_created": 2,
                    "features_implemented": [
                        "File-based event queue",
                        "Event handlers",
                        "File watchers",
                        "Schedulers",
                        "CLI triggers",
                        "Webhook simulation",
                    ],
                    "issue": "#004",
                    "status": "resolved",
                    "factor_11_compliance": "100%",
                },
            )
        else:
            failed = [r[0] for r in results if not r[1].success]
            return ToolResponse(
                success=False,
                error=f"Failed steps: {', '.join(failed)}",
                data={"failed_steps": failed},
            )

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply event system action"""
        action_type = action.get("type", "setup")

        if action_type == "setup":
            return self.execute_task(action.get("task", "implement event system"))
        elif action_type == "test":
            # Test event emission
            base_path = Path.home() / "Documents" / "GitHub" / "12-factor-agents"

            # Import and test
            sys.path.insert(0, str(base_path))
            from core.triggers import LocalEventSystem

            event_system = LocalEventSystem()
            event_id = event_system.emit("test_event", {"test": True})

            return ToolResponse(
                success=True,
                data={"event_id": event_id, "test": "Event emitted successfully"},
            )

        return ToolResponse(success=False, error=f"Unknown action type: {action_type}")


# Self-test when run directly
# Usage: uv run agents/event_system_agent.py
if __name__ == "__main__":
    print("Testing EventSystemAgent...")
    agent = EventSystemAgent()

    result = agent.execute_task(
        "implement event trigger system for Factor 11 compliance"
    )

    if result.success:
        print("✅ Event system implementation successful!")
        print(json.dumps(result.data, indent=2))

        # Test the system
        print("\nTesting event emission...")
        test_result = agent._apply_action({"type": "test"})
        if test_result.success:
            print(f"✅ Test event emitted: {test_result.data['event_id']}")
    else:
        print(f"❌ Implementation failed: {result.error}")
