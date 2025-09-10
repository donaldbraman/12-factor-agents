#!/usr/bin/env uv run python
"""
Test suite for error telemetry system.
Collects errors from all repos using our system to identify common issues.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import hashlib


class TelemetryCollector:
    """
    Lightweight telemetry collector that respects privacy.
    Only collects error patterns, not sensitive data.
    """

    def __init__(self, telemetry_dir: Path = None):
        # Store in shared location all repos can write to
        self.telemetry_dir = telemetry_dir or Path("/tmp/12-factor-telemetry")
        self.telemetry_dir.mkdir(exist_ok=True)

    def record_error(
        self,
        repo_name: str,
        agent_name: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict] = None,
    ) -> str:
        """
        Record an error event with privacy protection.
        Returns telemetry_id for tracking.
        """
        # Sanitize sensitive data
        safe_message = self._sanitize_message(error_message)

        # Create telemetry event
        event = {
            "timestamp": datetime.now().isoformat(),
            "repo": self._hash_if_needed(repo_name),
            "agent": agent_name,
            "error_type": error_type,
            "error_message": safe_message,
            "context": self._sanitize_context(context or {}),
        }

        # Generate unique ID
        telemetry_id = hashlib.md5(
            f"{event['timestamp']}{repo_name}{error_type}".encode()
        ).hexdigest()[:8]

        # Write to repo-specific file
        repo_file = self.telemetry_dir / f"{repo_name}_errors.jsonl"
        with open(repo_file, "a") as f:
            f.write(json.dumps(event) + "\n")

        # Also write to central file
        central_file = self.telemetry_dir / "all_errors.jsonl"
        with open(central_file, "a") as f:
            f.write(json.dumps(event) + "\n")

        return telemetry_id

    def _sanitize_message(self, message: str) -> str:
        """Remove potentially sensitive data from error messages"""
        # Remove file paths with user names
        import re

        message = re.sub(r"/Users/[^/]+/", "/Users/***/", message)
        message = re.sub(r"/home/[^/]+/", "/home/***/", message)

        # Remove potential API keys, tokens
        message = re.sub(r"[a-zA-Z0-9]{32,}", "***TOKEN***", message)

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


class TestTelemetrySystem:
    """Test the telemetry system with simulated errors"""

    def test_error_recording(self, tmp_path):
        """Test that errors are recorded correctly"""
        collector = TelemetryCollector(tmp_path)

        # Simulate error from pin-citer
        telemetry_id = collector.record_error(
            repo_name="pin-citer",
            agent_name="IssueProcessorAgent",
            error_type="FileNotFoundError",
            error_message="File not found: /Users/dbraman/Documents/citations.bib",
            context={"operation": "read", "file_type": "bib"},
        )

        assert telemetry_id
        assert (tmp_path / "pin-citer_errors.jsonl").exists()
        assert (tmp_path / "all_errors.jsonl").exists()

    def test_privacy_sanitization(self, tmp_path):
        """Test that sensitive data is sanitized"""
        collector = TelemetryCollector(tmp_path)

        # Record error with sensitive data
        collector.record_error(
            repo_name="cite-assist",
            agent_name="SmartIssueAgent",
            error_type="APIError",
            error_message="Failed with token sk-1234567890abcdef1234567890abcdef and email user@example.com",
            context={"api_key": "should_not_appear", "operation": "fetch"},
        )

        # Check sanitization
        with open(tmp_path / "all_errors.jsonl") as f:
            event = json.loads(f.read())

        assert "sk-1234567890" not in event["error_message"]
        assert "***TOKEN***" in event["error_message"]
        assert "user@example.com" not in event["error_message"]
        assert "***EMAIL***" in event["error_message"]
        assert "api_key" not in event["context"]  # Sensitive context removed
        assert event["context"]["operation"] == "fetch"  # Safe context kept

    def test_pattern_detection(self, tmp_path):
        """Test that we can detect error patterns"""
        collector = TelemetryCollector(tmp_path)

        # Simulate common errors across repos
        repos = ["pin-citer", "cite-assist", "article-analytics"]

        # File not found pattern
        for repo in repos:
            collector.record_error(
                repo_name=repo,
                agent_name="IssueProcessorAgent",
                error_type="FileNotFoundError",
                error_message=f"File not found: /path/to/{repo}/file.txt",
            )

        # Permission errors
        for repo in repos[:2]:
            collector.record_error(
                repo_name=repo,
                agent_name="FileTool",
                error_type="PermissionError",
                error_message=f"Permission denied: /path/to/{repo}/locked.txt",
            )

        # Git errors
        for repo in repos:
            collector.record_error(
                repo_name=repo,
                agent_name="GitTool",
                error_type="RuntimeError",
                error_message="fatal: Unable to create '.git/index.lock': File exists",
            )

        # Analyze patterns
        summary = collector.get_error_summary()

        assert summary["total_errors"] == 8
        assert "FileNotFoundError" in summary["by_type"]
        assert summary["by_type"]["FileNotFoundError"] == 3

        # Check patterns detected
        patterns = summary["patterns"]
        assert len(patterns) >= 2

        file_pattern = [p for p in patterns if "File not found" in p["pattern"]][0]
        assert file_pattern["count"] == 3
        assert "existence checks" in file_pattern["suggestion"]

    def test_cross_repo_insights(self, tmp_path):
        """Test insights across multiple repos"""
        collector = TelemetryCollector(tmp_path)

        # Simulate the same error happening in multiple repos
        # This suggests a systemic issue with our framework
        common_error = "AttributeError: 'IssueFixerAgent' object has no attribute '_intelligent_processing'"

        for repo in ["pin-citer", "cite-assist", "research-assist"]:
            collector.record_error(
                repo_name=repo,
                agent_name="IssueFixerAgent",
                error_type="AttributeError",
                error_message=common_error,
            )

        summary = collector.get_error_summary()

        # This error appearing in 3+ repos indicates a framework bug
        assert summary["by_type"]["AttributeError"] == 3
        assert len(summary["by_repo"]) == 3

        # We could add detection for this
        framework_bugs = [
            e
            for e in summary["by_agent"].items()
            if e[1] >= 3  # Same agent failing in 3+ places
        ]
        assert len(framework_bugs) > 0
        assert framework_bugs[0][0] == "IssueFixerAgent"


class TestTelemetryIntegration:
    """Test how telemetry integrates with our agents"""

    def test_baseagent_telemetry_hook(self, tmp_path):
        """Show how BaseAgent could automatically record errors"""

        # Mock BaseAgent with telemetry
        class BaseAgentWithTelemetry:
            def __init__(self):
                self.telemetry = TelemetryCollector(tmp_path)
                self.repo_name = self._detect_repo_name()

            def _detect_repo_name(self) -> str:
                """Auto-detect which repo we're running in"""
                cwd = Path.cwd()
                if "pin-citer" in str(cwd):
                    return "pin-citer"
                elif "cite-assist" in str(cwd):
                    return "cite-assist"
                return "unknown"

            def execute_task(self, task: str):
                """Execute with automatic error telemetry"""
                try:
                    # Simulate task execution
                    if "fail" in task:
                        raise ValueError("Task failed as requested")
                    return {"success": True}
                except Exception as e:
                    # Automatically record error
                    self.telemetry.record_error(
                        repo_name=self.repo_name,
                        agent_name=self.__class__.__name__,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        context={"task": task[:50]},  # Truncate for privacy
                    )
                    raise

        agent = BaseAgentWithTelemetry()

        # Success - no telemetry
        agent.execute_task("normal task")
        assert not (tmp_path / "all_errors.jsonl").exists()

        # Failure - telemetry recorded
        try:
            agent.execute_task("fail this task")
        except ValueError:
            pass

        assert (tmp_path / "all_errors.jsonl").exists()

        # Check telemetry
        summary = agent.telemetry.get_error_summary()
        assert summary["total_errors"] == 1
        assert "ValueError" in summary["by_type"]


if __name__ == "__main__":
    print("🔍 Testing Error Telemetry System\n")

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Test basic recording
        test = TestTelemetrySystem()
        test.test_error_recording(tmp_path)
        print("✅ Error recording works")

        # Test privacy
        test.test_privacy_sanitization(tmp_path / "privacy")
        print("✅ Privacy sanitization works")

        # Test pattern detection
        test.test_pattern_detection(tmp_path / "patterns")
        print("✅ Pattern detection works")

        # Show summary
        collector = TelemetryCollector(tmp_path / "patterns")
        summary = collector.get_error_summary()

        print("\n📊 Error Summary:")
        print(f"  Total errors: {summary['total_errors']}")
        print(f"  Error types: {summary['by_type']}")
        print(f"  Patterns detected: {len(summary['patterns'])}")
        for pattern in summary["patterns"]:
            print(f"    - {pattern['pattern']}: {pattern['count']} occurrences")
            print(f"      Suggestion: {pattern['suggestion']}")
