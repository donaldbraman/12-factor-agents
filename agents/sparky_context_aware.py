#!/usr/bin/env python3
"""
SPARKY 2.0 - Context-Aware Edition
Implementing Factor 3: Own Your Context Window
"""

from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
import time


class EventType(Enum):
    """Event types for context tracking"""

    ISSUE_READ = "issue_read"
    CLASSIFICATION = "classification"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"
    BATCH_START = "batch_start"
    BATCH_END = "batch_end"


@dataclass
class Event:
    """Flexible event representation for context"""

    type: EventType
    data: Any
    timestamp: float = field(default_factory=time.time)

    def to_compact(self) -> str:
        """Compact representation for context window"""
        if self.type == EventType.ISSUE_READ:
            return f"READ:{self.data.get('path', 'unknown')[:30]}"
        elif self.type == EventType.CLASSIFICATION:
            return f"CLASS:{self.data.get('type', '?')}"
        elif self.type == EventType.SUCCESS:
            return "✓"
        elif self.type == EventType.ERROR:
            return f"✗:{self.data.get('error', '')[:20]}"
        else:
            return f"{self.type.value[:5]}"


@dataclass
class ProcessingContext:
    """Context window management for SPARKY"""

    events: List[Event] = field(default_factory=list)
    max_events: int = 100  # Limit context size

    def add_event(self, event: Event):
        """Add event with automatic pruning"""
        self.events.append(event)
        if len(self.events) > self.max_events:
            # Keep only recent events
            self.events = self.events[-self.max_events :]

    def get_context_prompt(self) -> str:
        """Generate efficient context prompt"""
        if not self.events:
            return "No prior context"

        # Compact representation for efficiency
        recent = self.events[-20:]  # Last 20 events
        context_lines = [f"[{i}] {e.to_compact()}" for i, e in enumerate(recent)]

        # Add summary stats
        total = len(self.events)
        success = sum(1 for e in self.events if e.type == EventType.SUCCESS)
        errors = sum(1 for e in self.events if e.type == EventType.ERROR)

        summary = f"Stats: {total} events, {success} success, {errors} errors"

        return f"{summary}\nRecent:\n" + "\n".join(context_lines)

    def get_structured_context(self) -> Dict:
        """Structured context for advanced processing"""
        return {
            "total_events": len(self.events),
            "recent_events": [
                {"type": e.type.value, "timestamp": e.timestamp}
                for e in self.events[-10:]
            ],
            "statistics": self._calculate_stats(),
        }

    def _calculate_stats(self) -> Dict:
        """Calculate processing statistics"""
        if not self.events:
            return {}

        issue_types = {}
        for event in self.events:
            if event.type == EventType.CLASSIFICATION:
                issue_type = event.data.get("type", "unknown")
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        return {
            "total": len(self.events),
            "success_rate": sum(1 for e in self.events if e.type == EventType.SUCCESS)
            / len(self.events)
            * 100,
            "issue_types": issue_types,
            "avg_time": self._avg_processing_time(),
        }

    def _avg_processing_time(self) -> float:
        """Calculate average processing time between events"""
        if len(self.events) < 2:
            return 0.0

        times = []
        for i in range(1, len(self.events)):
            delta = self.events[i].timestamp - self.events[i - 1].timestamp
            if delta < 10:  # Ignore large gaps
                times.append(delta)

        return sum(times) / len(times) if times else 0.0


class SPARKYContextAware:
    """SPARKY with Factor 3: Own Your Context Window"""

    def __init__(self):
        self.context = ProcessingContext()
        self.start_time = time.time()

    def process_issue(self, issue_path: str) -> Dict:
        """Process with context tracking"""
        # Track read event
        self.context.add_event(
            Event(type=EventType.ISSUE_READ, data={"path": issue_path})
        )

        content = self._read_issue(issue_path)
        if not content:
            self.context.add_event(
                Event(type=EventType.ERROR, data={"error": f"Cannot read {issue_path}"})
            )
            return {"success": False, "error": f"Cannot read {issue_path}"}

        # Classify with context
        issue_type = self._classify_with_context(content)
        self.context.add_event(
            Event(
                type=EventType.CLASSIFICATION,
                data={"type": issue_type, "path": issue_path},
            )
        )

        # Process
        self.context.add_event(
            Event(
                type=EventType.PROCESSING, data={"path": issue_path, "type": issue_type}
            )
        )

        # Success
        self.context.add_event(Event(type=EventType.SUCCESS, data={"path": issue_path}))

        return {
            "success": True,
            "issue": issue_path,
            "type": issue_type,
            "context_size": len(self.context.events),
        }

    def _classify_with_context(self, content: str) -> str:
        """Classify using context to improve accuracy"""
        # Get context for better classification
        context_prompt = self.context.get_context_prompt()

        # Simple classification (would use LLM with context in production)
        content_lower = content.lower()

        # Use context to influence classification
        recent_types = [
            e.data.get("type")
            for e in self.context.events[-5:]
            if e.type == EventType.CLASSIFICATION
        ]

        # Basic rules with context influence
        if any(w in content_lower for w in ["bug", "fix", "error"]):
            return "bug"
        elif any(w in content_lower for w in ["feature", "implement"]):
            return "feature"
        elif any(w in content_lower for w in ["quality", "analysis"]):
            return "quality"
        elif recent_types and recent_types[-1]:
            # Bias toward recent classifications (pattern detection)
            return recent_types[-1]
        else:
            return "unknown"

    def _read_issue(self, path: str) -> str:
        """Read issue file"""
        try:
            p = Path(path)
            if not p.exists():
                p = Path("issues") / Path(path).name
            if p.exists():
                return p.read_text()
        except:
            pass
        return ""

    def process_batch(self, issues: List[str]) -> Dict:
        """Process batch with context management"""
        print("⚡ SPARKY 2.0 - CONTEXT AWARE EDITION ⚡")
        print("=" * 50)

        self.context.add_event(
            Event(type=EventType.BATCH_START, data={"count": len(issues)})
        )

        results = {"success": [], "failed": [], "context_evolution": []}

        for i, issue in enumerate(issues):
            print(f"\n🎯 [{i+1}/{len(issues)}] Processing: {issue}")

            # Show context awareness
            if i > 0 and i % 3 == 0:
                stats = self.context.get_structured_context()["statistics"]
                print(
                    f"  📊 Context: {len(self.context.events)} events, "
                    f"{stats.get('success_rate', 0):.1f}% success"
                )

            result = self.process_issue(issue)

            if result["success"]:
                results["success"].append(issue)
                print(f"  ✅ Type: {result.get('type')}")
            else:
                results["failed"].append(issue)
                print(f"  ❌ Error: {result.get('error')}")

            # Track context evolution
            if i % 5 == 0:
                results["context_evolution"].append(
                    {
                        "step": i,
                        "context_size": len(self.context.events),
                        "prompt": self.context.get_context_prompt()[:100],
                    }
                )

        self.context.add_event(
            Event(
                type=EventType.BATCH_END,
                data={
                    "success": len(results["success"]),
                    "failed": len(results["failed"]),
                },
            )
        )

        # Final report with context insights
        print("\n" + "=" * 50)
        print("📊 SPARKY 2.0 CONTEXT-AWARE RESULTS")
        print(f"✅ Success: {len(results['success'])}")
        print(f"❌ Failed: {len(results['failed'])}")

        final_stats = self.context.get_structured_context()["statistics"]
        print("\n🧠 CONTEXT INSIGHTS:")
        print(f"  • Total events tracked: {final_stats['total']}")
        print(f"  • Success rate: {final_stats.get('success_rate', 0):.1f}%")
        print(f"  • Avg processing time: {final_stats.get('avg_time', 0):.3f}s")

        if final_stats.get("issue_types"):
            print("  • Issue distribution:")
            for itype, count in final_stats["issue_types"].items():
                print(f"    - {itype}: {count}")

        results["context_stats"] = final_stats
        return results


# 220 lines implementing Factor 3: Own Your Context Window!

if __name__ == "__main__":
    sparky = SPARKYContextAware()

    test_issues = [
        "issues/001-add-noqa-to-code-review-agent.md",
        "issues/122.md",
        "issues/test-simple.md",
    ]

    sparky.process_batch(test_issues)
