#!/usr/bin/env python3
"""
Telemetry system for 12-factor-agents framework.
Collects error patterns across all sister repositories with privacy protection.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import hashlib
import re


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
        message = re.sub(r"/Users/[^/]+/", "/Users/***/", message)
        message = re.sub(r"/home/[^/]+/", "/home/***/", message)

        # Remove potential API keys, tokens
        message = re.sub(r"[a-zA-Z0-9]{32,}", "***TOKEN***", message)
        message = re.sub(r"sk-[a-zA-Z0-9]+", "***TOKEN***", message)  # OpenAI-style keys
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


def main():
    """Test the telemetry collector"""
    print("🔍 Testing Telemetry Collector")
    
    collector = TelemetryCollector()
    
    # Test recording an error
    telemetry_id = collector.record_error(
        repo_name="12-factor-agents",
        agent_name="TestAgent",
        error_type="TestError",
        error_message="Test error with /Users/testuser/secret and token sk-1234567890abcdef",
        context={"operation": "test", "secret_key": "should_not_appear"}
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