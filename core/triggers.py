"""
Local event trigger system for Factor 11 compliance.
Factor 11: Trigger from Anywhere - Agents can be triggered through multiple entry points.
"""
import json
import time
import threading
import hashlib
from pathlib import Path
from typing import Dict, Any, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


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
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
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

    def emit(
        self, event_type: str, data: Dict[str, Any], source: str = "manual"
    ) -> str:
        """
        Emit an event to the file system.
        Returns event ID.
        """
        event = Event(
            event_type=event_type, data=data, timestamp=datetime.now(), source=source
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

    def register_file_watcher(
        self, path: str, pattern: str = "*", event_type: str = "file_changed"
    ) -> None:
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
            "file_states": {},
        }

        # Get initial state
        for file_path in Path(path).glob(pattern):
            if file_path.is_file():
                watcher["file_states"][str(file_path)] = file_path.stat().st_mtime

        self.file_watchers.append(watcher)

    def register_schedule(
        self, cron_expr: str, handler: Callable, event_type: str = "schedule_triggered"
    ) -> None:
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
            "last_run": None,
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
                        source="file_watcher",
                    )

            # Modified files
            for file_path, mtime in current_states.items():
                if file_path in old_states and mtime != old_states[file_path]:
                    self.emit(
                        watcher["event_type"],
                        {"path": file_path, "change": "modified"},
                        source="file_watcher",
                    )

            # Deleted files
            for file_path in old_states:
                if file_path not in current_states:
                    self.emit(
                        watcher["event_type"],
                        {"path": file_path, "change": "deleted"},
                        source="file_watcher",
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
                            source="scheduler",
                        )

                        if schedule["handler"]:
                            schedule["handler"](
                                Event(
                                    event_type=schedule["event_type"],
                                    data={"schedule": cron},
                                    timestamp=now,
                                    source="scheduler",
                                )
                            )

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
            self._scheduler_thread = threading.Thread(
                target=scheduler_loop, daemon=True
            )
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

        for event_file in sorted(
            self.processed_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:limit]:
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
            f"github_{event_type}", payload, source="webhook_simulator"
        )

    def listen(self) -> None:
        """Listen for webhook files"""
        self.event_system.register_file_watcher(
            str(self.webhook_dir), "*.webhook", "webhook_received"
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
