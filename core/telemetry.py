#!/usr/bin/env uv run python
"""
Enhanced Telemetry system for 12-factor-agents framework.
Collects comprehensive workflow data, error patterns, and performance metrics
across all sister repositories with privacy protection.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any
import hashlib
import re
from enum import Enum
from dataclasses import dataclass, field


class EventType(Enum):
    """Types of telemetry events"""

    ERROR = "error"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    AGENT_DISPATCH = "agent_dispatch"
    AGENT_SUCCESS = "agent_success"
    AGENT_FAILURE = "agent_failure"
    ISSUE_PARSED = "issue_parsed"
    ISSUE_SKIPPED = "issue_skipped"
    DEPENDENCY_CHECK = "dependency_check"
    PERFORMANCE = "performance"
    ORCHESTRATION = "orchestration"
    IMPLEMENTATION_GAP = "implementation_gap"


@dataclass
class WorkflowEvent:
    """Enhanced workflow event with rich context"""

    event_type: EventType
    timestamp: str
    repo: str
    agent: str
    event_id: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    parent_event_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedTelemetryCollector:
    """
    Enhanced telemetry collector that captures comprehensive workflow data
    while respecting privacy. Tracks the entire issue-to-implementation pipeline.
    """

    def __init__(self, telemetry_dir: Path = None):
        # Store in shared location all repos can write to
        self.telemetry_dir = telemetry_dir or Path("/tmp/12-factor-telemetry")
        self.telemetry_dir.mkdir(exist_ok=True)

        # Session tracking
        self.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        self.active_workflows = {}
        self.event_sequence = 0

        # Strategy learning storage
        self.strategy_patterns = {}

        # Issues excluded from strategy learning (avoid circular loops)
        self.EXCLUDED_FROM_STRATEGY_LEARNING = {
            "telemetry_enhancement",
            "strategy_learning",
            "meta_learning",
            "learning_intelligence",
            "bug_detection",
        }

        # Issue type patterns for classification
        self.ISSUE_TYPE_PATTERNS = {
            r"parsing|regex": "parsing_error",
            r"telemetry|tracking": "telemetry_enhancement",
            r"serialization|json": "serialization_fix",
            r"missing.*agent": "agent_creation",
            r"performance|slow": "performance_optimization",
            r"strategy.*learning": "strategy_learning",
            r"learning.*telemetry": "strategy_learning",
        }

    def record_workflow_event(
        self,
        event_type: EventType,
        repo_name: str,
        agent_name: str,
        message: str,
        context: Optional[Dict] = None,
        duration_ms: Optional[float] = None,
        success: Optional[bool] = None,
        parent_event_id: Optional[str] = None,
    ) -> str:
        """
        Record a workflow event with privacy protection.
        Returns event_id for tracking.
        """
        # Generate unique event ID
        self.event_sequence += 1
        event_id = f"{self.session_id}_{self.event_sequence:04d}"

        # Sanitize sensitive data
        safe_message = self._sanitize_message(message)

        # Create enhanced workflow event
        event = WorkflowEvent(
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            repo=self._hash_if_needed(repo_name),
            agent=agent_name,
            event_id=event_id,
            message=safe_message,
            context=self._sanitize_context(context or {}),
            duration_ms=duration_ms,
            success=success,
            parent_event_id=parent_event_id,
            metadata={
                "session_id": self.session_id,
                "sequence": self.event_sequence,
            },
        )

        # Convert to dict for JSON serialization
        event_dict = {
            "event_type": event.event_type.value,
            "timestamp": event.timestamp,
            "repo": event.repo,
            "agent": event.agent,
            "event_id": event.event_id,
            "message": event.message,
            "context": event.context,
            "duration_ms": event.duration_ms,
            "success": event.success,
            "parent_event_id": event.parent_event_id,
            "metadata": event.metadata,
        }

        # Write to repo-specific file
        repo_file = self.telemetry_dir / f"{repo_name}_workflow.jsonl"
        with open(repo_file, "a") as f:
            f.write(json.dumps(event_dict) + "\n")

        # Also write to central workflow file
        central_file = self.telemetry_dir / "all_workflow_events.jsonl"
        with open(central_file, "a") as f:
            f.write(json.dumps(event_dict) + "\n")

        return event_id

    def _sanitize_message(self, message: str) -> str:
        """Remove potentially sensitive data from error messages"""
        # Remove file paths with user names
        message = re.sub(r"/Users/[^/]+/", "/Users/***/", message)
        message = re.sub(r"/home/[^/]+/", "/home/***/", message)

        # Remove potential API keys, tokens
        message = re.sub(r"[a-zA-Z0-9]{32,}", "***TOKEN***", message)
        message = re.sub(
            r"sk-[a-zA-Z0-9]+", "***TOKEN***", message
        )  # OpenAI-style keys
        message = re.sub(r"Bearer\s+[a-zA-Z0-9\-_]+", "Bearer ***TOKEN***", message)

        # Remove email addresses
        message = re.sub(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "***EMAIL***", message
        )

        return message

    def _sanitize_context(self, context: Dict) -> Dict:
        """Sanitize context data"""
        safe_context = {}
        allowed_keys = ["operation", "file_type", "retry_count", "duration_ms"]

        for key in allowed_keys:
            if key in context:
                safe_context[key] = context[key]

        return safe_context

    def _hash_if_needed(self, repo_name: str) -> str:
        """Hash repo name if user wants privacy"""
        # Could check a privacy setting
        if "private" in repo_name.lower():
            return hashlib.md5(repo_name.encode()).hexdigest()[:8]
        return repo_name

    def record_error(
        self,
        repo_name: str,
        agent_name: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict] = None,
    ) -> str:
        """
        Record an error event (backward compatibility method).
        Returns event_id for tracking.
        """
        return self.record_workflow_event(
            EventType.ERROR,
            repo_name,
            agent_name,
            f"{error_type}: {error_message}",
            context,
        )

    def start_workflow(
        self, repo_name: str, workflow_name: str, total_issues: int, context: Dict
    ) -> str:
        """Start workflow tracking and return workflow_id"""
        return self.record_workflow_event(
            EventType.WORKFLOW_START,
            repo_name,
            "IssueOrchestratorAgent",
            f"Starting workflow: {workflow_name} with {total_issues} issues",
            context,
        )

    def end_workflow(
        self,
        workflow_id: str,
        repo_name: str,
        workflow_name: str,
        success: bool,
        results: Dict,
    ) -> str:
        """End workflow tracking"""
        return self.record_workflow_event(
            EventType.WORKFLOW_END,
            repo_name,
            "IssueOrchestratorAgent",
            f"Completed workflow: {workflow_name} - Success: {success}",
            results,
            success=success,
            parent_event_id=workflow_id,
        )

    def record_issue_processing(
        self,
        repo_name: str,
        issue_number: str,
        issue_title: str,
        agent_name: str,
        status: str,
        context: Dict,
        parent_workflow_id: str,
    ) -> str:
        """Record issue processing event"""
        return self.record_workflow_event(
            EventType.ISSUE_PARSED,
            repo_name,
            agent_name,
            f"Processing issue #{issue_number}: {issue_title} - Status: {status}",
            context,
            parent_event_id=parent_workflow_id,
        )

    def record_agent_dispatch(
        self,
        repo_name: str,
        agent_name: str,
        issue_number: str,
        task_description: str,
        context: Dict,
        parent_workflow_id: str,
    ) -> str:
        """Record agent dispatch event"""
        return self.record_workflow_event(
            EventType.AGENT_DISPATCH,
            repo_name,
            agent_name,
            f"Dispatching to {agent_name} for issue #{issue_number}: {task_description}",
            context,
            parent_event_id=parent_workflow_id,
        )

    def record_agent_result(
        self,
        repo_name: str,
        agent_name: str,
        issue_number: str,
        success: bool,
        result_data: Dict = None,
        error_message: str = None,
        duration_ms: float = None,
        parent_workflow_id: str = None,
    ) -> str:
        """Record agent result event and update strategy learning patterns"""
        event_type = EventType.AGENT_SUCCESS if success else EventType.AGENT_FAILURE
        message = f"Agent {agent_name} completed issue #{issue_number}"
        if error_message:
            message += f" with error: {error_message}"

        # Extract strategy learning data
        if result_data:
            issue_title = result_data.get("issue_title", f"Issue #{issue_number}")
            strategy = result_data.get("strategy", "unknown")

            # Extract issue type and update patterns
            issue_type = self._extract_issue_type(issue_title)
            if strategy != "unknown":
                self._update_strategy_patterns(
                    issue_type, strategy, success, duration_ms
                )

                # Add learning info to context
                context = result_data.copy()
                context.update(
                    {
                        "issue_type": issue_type,
                        "strategy_learning_applied": self._should_apply_strategy_learning(
                            issue_type
                        ),
                    }
                )
            else:
                context = result_data
        else:
            context = {}

        return self.record_workflow_event(
            event_type,
            repo_name,
            agent_name,
            message,
            context,
            duration_ms=duration_ms,
            success=success,
            parent_event_id=parent_workflow_id,
        )

    def record_implementation_gap(
        self,
        repo_name: str,
        agent_name: str,
        gap_type: str,
        description: str,
        context: Dict,
    ) -> str:
        """Record implementation gap detection"""
        return self.record_workflow_event(
            EventType.IMPLEMENTATION_GAP,
            repo_name,
            agent_name,
            f"Implementation gap detected ({gap_type}): {description}",
            context,
        )

    def _extract_issue_type(self, issue_title: str) -> str:
        """Extract issue type from title using regex patterns"""
        for pattern, issue_type in self.ISSUE_TYPE_PATTERNS.items():
            if re.search(pattern, issue_title, re.IGNORECASE):
                return issue_type
        return "generic"

    def _should_apply_strategy_learning(self, issue_type: str) -> bool:
        """Check if issue type should participate in strategy learning"""
        return issue_type not in self.EXCLUDED_FROM_STRATEGY_LEARNING

    def _update_strategy_patterns(
        self, issue_type: str, strategy: str, success: bool, duration_ms: float = None
    ):
        """Update strategy success patterns for learning"""
        if not self._should_apply_strategy_learning(issue_type):
            return

        if issue_type not in self.strategy_patterns:
            self.strategy_patterns[issue_type] = {}

        if strategy not in self.strategy_patterns[issue_type]:
            self.strategy_patterns[issue_type][strategy] = {
                "successes": 0,
                "failures": 0,
                "total_duration": 0,
                "count": 0,
            }

        pattern = self.strategy_patterns[issue_type][strategy]
        if success:
            pattern["successes"] += 1
        else:
            pattern["failures"] += 1

        pattern["count"] += 1
        if duration_ms:
            pattern["total_duration"] += duration_ms

    def get_strategy_confidence(self, issue_type: str) -> Dict[str, float]:
        """Get confidence scores for strategies for a given issue type"""
        if issue_type not in self.strategy_patterns:
            return {}

        confidences = {}
        for strategy, pattern in self.strategy_patterns[issue_type].items():
            total = pattern["count"]
            if total == 0:
                confidences[strategy] = 0.5  # neutral
            else:
                success_rate = pattern["successes"] / total
                # Adjust confidence based on sample size (more samples = more confident)
                confidence_adjustment = min(
                    total / 10.0, 1.0
                )  # max confidence at 10+ samples
                confidences[strategy] = success_rate * confidence_adjustment

        return confidences

    def select_best_strategy(
        self, issue_type: str, available_strategies: List[str] = None
    ) -> str:
        """Select best strategy based on historical patterns"""
        if not self._should_apply_strategy_learning(issue_type):
            return "default"

        confidences = self.get_strategy_confidence(issue_type)
        if not confidences:
            return "generic_implementation"  # fallback

        # Filter to available strategies if provided
        if available_strategies:
            confidences = {
                s: c for s, c in confidences.items() if s in available_strategies
            }

        if not confidences:
            return "generic_implementation"

        # Return strategy with highest confidence
        best_strategy = max(confidences.items(), key=lambda x: x[1])
        return best_strategy[0]

    def get_error_summary(self) -> Dict:
        """Analyze collected errors to find patterns"""
        central_file = self.telemetry_dir / "all_errors.jsonl"
        if not central_file.exists():
            return {"total_errors": 0, "patterns": []}

        errors = []
        with open(central_file) as f:
            for line in f:
                errors.append(json.loads(line))

        # Analyze patterns
        error_types = {}
        agent_errors = {}
        repo_errors = {}

        for error in errors:
            # Count by error type
            err_type = error["error_type"]
            error_types[err_type] = error_types.get(err_type, 0) + 1

            # Count by agent
            agent = error["agent"]
            agent_errors[agent] = agent_errors.get(agent, 0) + 1

            # Count by repo
            repo = error["repo"]
            repo_errors[repo] = repo_errors.get(repo, 0) + 1

        # Find most common patterns
        patterns = []

        # Pattern: File not found errors
        file_not_found = [
            e for e in errors if "not found" in e["error_message"].lower()
        ]
        if len(file_not_found) > 2:
            patterns.append(
                {
                    "pattern": "File not found errors",
                    "count": len(file_not_found),
                    "suggestion": "Add file existence checks before operations",
                }
            )

        # Pattern: Permission errors
        permission_errors = [
            e for e in errors if "permission" in e["error_message"].lower()
        ]
        if len(permission_errors) > 2:
            patterns.append(
                {
                    "pattern": "Permission denied errors",
                    "count": len(permission_errors),
                    "suggestion": "Add retry logic for locked files",
                }
            )

        # Pattern: Git conflicts
        git_errors = [e for e in errors if "git" in e["error_message"].lower()]
        if len(git_errors) > 2:
            patterns.append(
                {
                    "pattern": "Git operation failures",
                    "count": len(git_errors),
                    "suggestion": "Add git index.lock handling",
                }
            )

        return {
            "total_errors": len(errors),
            "by_type": error_types,
            "by_agent": agent_errors,
            "by_repo": repo_errors,
            "patterns": patterns,
            "top_errors": sorted(error_types.items(), key=lambda x: x[1], reverse=True)[
                :5
            ],
        }


# Backward compatibility alias
TelemetryCollector = EnhancedTelemetryCollector


def main():
    """Test the enhanced telemetry collector"""
    print("🔍 Testing Enhanced Telemetry Collector")

    collector = EnhancedTelemetryCollector()

    # Test recording an error
    telemetry_id = collector.record_error(
        repo_name="12-factor-agents",
        agent_name="TestAgent",
        error_type="TestError",
        error_message="Test error with /Users/testuser/secret and token sk-1234567890abcdef",
        context={"operation": "test", "secret_key": "should_not_appear"},
    )

    print(f"✅ Recorded error with ID: {telemetry_id}")

    # Test analysis
    summary = collector.get_error_summary()
    print(f"📊 Total errors: {summary['total_errors']}")
    print(f"📈 Error types: {summary['by_type']}")

    # Show sanitization worked
    with open(collector.telemetry_dir / "all_errors.jsonl") as f:
        event = json.loads(f.read())

    print(f"🔒 Sanitized message: {event['error_message']}")
    print(f"🔒 Safe context: {event['context']}")


if __name__ == "__main__":
    main()
