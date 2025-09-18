#!/usr/bin/env python3
"""
Telemetry-Based Pattern Learning System

Learns from telemetry data to identify:
- What patterns lead to failures
- What fixes actually work
- Success patterns to replicate
- Failure patterns to avoid

This keeps telemetry LOCAL to our repo while sharing learned patterns.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum

from core.telemetry import EnhancedTelemetryCollector
from core.quality_patterns import get_pattern_manager


class PatternOutcome(Enum):
    """Outcome of a pattern usage"""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass
class FailurePattern:
    """A pattern that leads to failures"""

    pattern: str
    failure_count: int
    success_count: int
    failure_rate: float
    common_errors: List[str]
    suggested_fix: str
    last_seen: str


@dataclass
class SuccessPattern:
    """A pattern that leads to success"""

    pattern: str
    success_count: int
    failure_count: int
    success_rate: float
    contexts: List[str]
    key_elements: List[str]
    last_seen: str


class TelemetryPatternLearner:
    """
    Learns patterns from telemetry data to improve code generation.
    Keeps telemetry LOCAL while sharing learned patterns.
    """

    def __init__(self, telemetry_dir: Path = None):
        """Initialize with local telemetry directory"""
        # IMPORTANT: Keep telemetry LOCAL to our repo
        self.telemetry_dir = telemetry_dir or Path("/tmp/12-factor-telemetry")

        # Local storage for learned patterns
        self.patterns_dir = Path("prompts/learned_patterns")
        self.patterns_dir.mkdir(parents=True, exist_ok=True)

        # Pattern manager integration
        self.pattern_manager = get_pattern_manager()

        # Use existing telemetry collector for strategy learning
        self.telemetry_collector = EnhancedTelemetryCollector(self.telemetry_dir)

        # In-memory caches
        self.failure_patterns = {}
        self.success_patterns = {}
        self.fix_mappings = {}  # Maps failures to successful fixes

        # Load existing patterns
        self._load_learned_patterns()

    def analyze_telemetry(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Analyze recent telemetry to identify patterns.

        Returns:
            Dictionary of learned patterns and insights
        """
        insights = {
            "failure_patterns": [],
            "success_patterns": [],
            "fix_mappings": [],
            "recommendations": [],
        }

        # Read telemetry files (LOCAL ONLY) - support both .json and .jsonl
        telemetry_files = list(self.telemetry_dir.glob("*.json")) + list(
            self.telemetry_dir.glob("*.jsonl")
        )
        recent_events = []

        cutoff_date = datetime.now() - timedelta(days=days_back)

        for file in telemetry_files:
            try:
                with open(file, "r") as f:
                    # Try JSONL format first (one JSON per line)
                    if file.suffix == ".jsonl":
                        for line in f:
                            if line.strip():
                                event = json.loads(line)
                                event_date = datetime.fromisoformat(
                                    event.get("timestamp", "")
                                )
                                if event_date >= cutoff_date:
                                    recent_events.append(event)
                    else:
                        # Regular JSON format
                        events = json.load(f)
                        # Handle both single event and list of events
                        if isinstance(events, dict):
                            events = [events]
                        # Filter recent events
                        for event in events:
                            event_date = datetime.fromisoformat(
                                event.get("timestamp", "")
                            )
                            if event_date >= cutoff_date:
                                recent_events.append(event)
            except Exception:
                continue  # Skip corrupted files

        # Analyze failure patterns
        insights["failure_patterns"] = self._analyze_failure_patterns(recent_events)

        # Analyze success patterns
        insights["success_patterns"] = self._analyze_success_patterns(recent_events)

        # Find fix mappings (what fixes what)
        insights["fix_mappings"] = self._find_fix_mappings(recent_events)

        # Generate recommendations
        insights["recommendations"] = self._generate_recommendations(insights)

        # Update pattern database
        self._update_pattern_database(insights)

        return insights

    def _analyze_failure_patterns(self, events: List[Dict]) -> List[FailurePattern]:
        """Identify patterns that commonly lead to failures"""
        failure_contexts = defaultdict(list)

        for event in events:
            # Handle different event type formats
            event_type = event.get("event_type", "").lower()
            if event_type in ["agent_failure", "error", "implementation_gap"]:
                context = event.get("context", {})

                # Extract patterns from context
                if "code_pattern" in context:
                    pattern = context["code_pattern"]
                    error = event.get("message", "Unknown error")
                    failure_contexts[pattern].append(error)

                # Look for common failure indicators
                message = event.get("message", "")
                if "placeholder" in message.lower():
                    failure_contexts["placeholder_code"].append(message)
                if "todo" in message.lower():
                    failure_contexts["todo_in_code"].append(message)
                if "not implemented" in message.lower():
                    failure_contexts["empty_implementation"].append(message)

        # Analyze patterns
        patterns = []
        for pattern, errors in failure_contexts.items():
            if len(errors) >= 2:  # At least 2 occurrences
                patterns.append(
                    FailurePattern(
                        pattern=pattern,
                        failure_count=len(errors),
                        success_count=0,  # Will be updated later
                        failure_rate=1.0,  # Will be calculated
                        common_errors=list(set(errors))[:3],
                        suggested_fix=self._suggest_fix_for_pattern(pattern),
                        last_seen=datetime.now().isoformat(),
                    )
                )

        return patterns

    def _analyze_success_patterns(self, events: List[Dict]) -> List[SuccessPattern]:
        """Identify patterns that lead to success"""
        success_contexts = defaultdict(list)

        for event in events:
            event_type = event.get("event_type", "").lower()
            if event_type in ["agent_success", "workflow_end"]:
                # Check for success indicator (might be True or implicit)
                if event.get("success") is not False:
                    context = event.get("context", {})

                    # Extract successful patterns
                    if "implementation_pattern" in context:
                        pattern = context["implementation_pattern"]
                        success_contexts[pattern].append(context)

                    # Look for success indicators
                    message = event.get("message", "")
                    if "test passed" in message.lower():
                        success_contexts["comprehensive_tests"].append(context)
                    if "quality score" in message.lower() and ">" in message:
                        success_contexts["high_quality_code"].append(context)

        # Analyze patterns
        patterns = []
        for pattern, contexts in success_contexts.items():
            if len(contexts) >= 2:
                # Extract key elements that made it successful
                key_elements = self._extract_key_elements(contexts)

                patterns.append(
                    SuccessPattern(
                        pattern=pattern,
                        success_count=len(contexts),
                        failure_count=0,
                        success_rate=1.0,
                        contexts=[str(c) for c in contexts[:3]],
                        key_elements=key_elements,
                        last_seen=datetime.now().isoformat(),
                    )
                )

        return patterns

    def _find_fix_mappings(self, events: List[Dict]) -> List[Dict]:
        """Find what fixes work for what failures"""
        fix_mappings = []

        # Group events by session/workflow
        workflows = defaultdict(list)
        for event in events:
            workflow_id = event.get("parent_event_id") or event.get("event_id")
            workflows[workflow_id].append(event)

        # Analyze each workflow
        for workflow_id, workflow_events in workflows.items():
            # Look for failure followed by success
            failure_event = None
            success_event = None

            for i, event in enumerate(workflow_events):
                if event.get("event_type") in ["AGENT_FAILURE", "ERROR"]:
                    failure_event = event
                elif event.get("event_type") in ["AGENT_SUCCESS"] and failure_event:
                    success_event = event

                    # Found a fix!
                    fix_mappings.append(
                        {
                            "failure": failure_event.get("message", ""),
                            "failure_context": failure_event.get("context", {}),
                            "fix": success_event.get("message", ""),
                            "fix_context": success_event.get("context", {}),
                            "confidence": 0.8,  # High confidence for direct fix
                        }
                    )

                    failure_event = None
                    success_event = None

        return fix_mappings

    def _suggest_fix_for_pattern(self, pattern: str) -> str:
        """Suggest a fix for a failure pattern"""
        fixes = {
            "placeholder_code": "Replace placeholder with actual implementation",
            "todo_in_code": "Complete TODO items before submission",
            "empty_implementation": "Add real business logic, not just structure",
            "missing_tests": "Add comprehensive tests with real assertions",
            "no_error_handling": "Add try/except blocks for risky operations",
        }

        return fixes.get(pattern, "Review and improve implementation")

    def _extract_key_elements(self, contexts: List[Dict]) -> List[str]:
        """Extract key elements that made implementations successful"""
        elements = []

        for context in contexts:
            # Look for common success factors
            if context.get("has_tests"):
                elements.append("comprehensive_tests")
            if context.get("error_handling"):
                elements.append("proper_error_handling")
            if context.get("quality_score", 0) > 80:
                elements.append("high_quality_score")
            if context.get("no_placeholders"):
                elements.append("complete_implementation")

        # Return unique elements
        return list(set(elements))

    def _generate_recommendations(self, insights: Dict) -> List[str]:
        """Generate actionable recommendations from insights"""
        recommendations = []

        # Based on failure patterns
        for pattern in insights["failure_patterns"]:
            if pattern.failure_rate > 0.5:
                recommendations.append(
                    f"AVOID: {pattern.pattern} (fails {pattern.failure_rate*100:.0f}% of the time)"
                )

        # Based on success patterns
        for pattern in insights["success_patterns"]:
            if pattern.success_rate > 0.8:
                recommendations.append(
                    f"USE: {pattern.pattern} (succeeds {pattern.success_rate*100:.0f}% of the time)"
                )

        # Based on fix mappings
        common_fixes = Counter()
        for mapping in insights["fix_mappings"]:
            fix_type = mapping.get("fix", "").split(":")[0]
            common_fixes[fix_type] += 1

        for fix_type, count in common_fixes.most_common(3):
            recommendations.append(f"EFFECTIVE FIX: {fix_type} (worked {count} times)")

        return recommendations

    def _update_pattern_database(self, insights: Dict):
        """Update the central pattern database with learned patterns"""

        # Add failure patterns to avoid list
        for pattern in insights["failure_patterns"]:
            if pattern.failure_rate > 0.6:  # High failure rate
                self.pattern_manager.add_learned_pattern(
                    pattern=pattern.pattern,
                    learned_from=f"Telemetry: {pattern.failure_count} failures observed",
                    action=pattern.suggested_fix,
                )

        # Add success patterns to follow list
        for pattern in insights["success_patterns"]:
            if pattern.success_rate > 0.8:  # High success rate
                self.pattern_manager.add_learned_pattern(
                    pattern=pattern.pattern,
                    learned_from=f"Telemetry: {pattern.success_count} successes observed",
                    action=f"Implement {', '.join(pattern.key_elements)}",
                )

        # Save learned patterns locally
        self._save_learned_patterns(insights)

    def _save_learned_patterns(self, insights: Dict):
        """Save learned patterns to local storage"""
        patterns_file = (
            self.patterns_dir
            / f"telemetry_patterns_{datetime.now().strftime('%Y%m%d')}.json"
        )

        with open(patterns_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "failure_patterns": [
                        {
                            "pattern": p.pattern,
                            "failure_rate": p.failure_rate,
                            "suggested_fix": p.suggested_fix,
                        }
                        for p in insights["failure_patterns"]
                    ],
                    "success_patterns": [
                        {
                            "pattern": p.pattern,
                            "success_rate": p.success_rate,
                            "key_elements": p.key_elements,
                        }
                        for p in insights["success_patterns"]
                    ],
                    "fix_mappings": insights["fix_mappings"],
                    "recommendations": insights["recommendations"],
                },
                f,
                indent=2,
            )

    def _load_learned_patterns(self):
        """Load previously learned patterns"""
        if not self.patterns_dir.exists():
            return

        # Load most recent patterns file
        pattern_files = sorted(self.patterns_dir.glob("telemetry_patterns_*.json"))
        if pattern_files:
            latest = pattern_files[-1]
            try:
                with open(latest, "r") as f:
                    json.load(f)  # Load but don't use yet
                    # Populate caches
                    # (Implementation depends on needs)
            except Exception:
                pass

    def get_pattern_recommendation(self, context: Dict) -> Optional[str]:
        """
        Get recommendation based on current context.
        Used by agents to avoid known failures.
        """
        recommendations = []

        # Check if context matches any failure pattern
        for pattern in self.failure_patterns.values():
            if self._context_matches_pattern(context, pattern):
                recommendations.append(
                    f"WARNING: This matches failure pattern '{pattern.pattern}'. {pattern.suggested_fix}"
                )

        # Get strategy recommendations from existing telemetry
        if "issue_type" in context:
            issue_type = context["issue_type"]
            best_strategy = self.telemetry_collector.select_best_strategy(issue_type)
            confidences = self.telemetry_collector.get_strategy_confidence(issue_type)

            if best_strategy != "default" and best_strategy in confidences:
                confidence = confidences[best_strategy]
                if confidence > 0.7:
                    recommendations.append(
                        f"STRATEGY: Use '{best_strategy}' strategy (confidence: {confidence*100:.0f}%)"
                    )

            # Warn about low-confidence strategies
            for strategy, confidence in confidences.items():
                if confidence < 0.3 and strategy in str(context).lower():
                    recommendations.append(
                        f"CAUTION: '{strategy}' has low success rate ({confidence*100:.0f}%)"
                    )

        # Check if we can suggest a success pattern
        for pattern in self.success_patterns.values():
            if pattern.success_rate > 0.9:
                elements_str = ", ".join(pattern.key_elements)
                recommendations.append(
                    f"TIP: Include {elements_str} for better success rate"
                )

        return " | ".join(recommendations) if recommendations else None

    def _context_matches_pattern(self, context: Dict, pattern: FailurePattern) -> bool:
        """Check if context matches a failure pattern"""
        # Simple matching for now
        context_str = json.dumps(context).lower()
        return pattern.pattern.lower() in context_str

    def export_strategy_patterns(self) -> Dict[str, Any]:
        """Export the best strategies from telemetry as patterns"""
        strategy_patterns = {}

        # Get all issue types with strategy data
        for issue_type in self.telemetry_collector.strategy_patterns:
            confidences = self.telemetry_collector.get_strategy_confidence(issue_type)

            # Only export high-confidence strategies
            high_confidence = {s: c for s, c in confidences.items() if c > 0.7}

            if high_confidence:
                best_strategy = max(high_confidence.items(), key=lambda x: x[1])
                strategy_patterns[issue_type] = {
                    "recommended_strategy": best_strategy[0],
                    "confidence": best_strategy[1],
                    "alternatives": [
                        s for s, c in high_confidence.items() if s != best_strategy[0]
                    ],
                }

        return strategy_patterns


def analyze_and_learn():
    """Run telemetry analysis and update patterns"""
    learner = TelemetryPatternLearner()

    print("📊 Analyzing telemetry data...")
    insights = learner.analyze_telemetry(days_back=7)

    # Also get strategy insights from existing telemetry
    strategy_patterns = learner.export_strategy_patterns()

    print(f"\n🔍 Found {len(insights['failure_patterns'])} failure patterns")
    for pattern in insights["failure_patterns"][:3]:
        print(f"   ❌ {pattern.pattern}: {pattern.failure_rate*100:.0f}% failure rate")
        print(f"      Fix: {pattern.suggested_fix}")

    print(f"\n✅ Found {len(insights['success_patterns'])} success patterns")
    for pattern in insights["success_patterns"][:3]:
        print(f"   ✓ {pattern.pattern}: {pattern.success_rate*100:.0f}% success rate")
        print(f"      Key: {', '.join(pattern.key_elements)}")

    print("\n🎯 Strategy recommendations from telemetry:")
    for issue_type, strategy_info in list(strategy_patterns.items())[:3]:
        print(
            f"   {issue_type}: Use '{strategy_info['recommended_strategy']}' "
            f"(confidence: {strategy_info['confidence']*100:.0f}%)"
        )

    print(f"\n🔧 Found {len(insights['fix_mappings'])} fix mappings")

    print("\n📝 Recommendations:")
    for rec in insights["recommendations"][:5]:
        print(f"   • {rec}")

    return insights


if __name__ == "__main__":
    # Run analysis
    analyze_and_learn()
