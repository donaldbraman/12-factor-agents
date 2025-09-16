#!/usr/bin/env python3
"""
CI Monitoring Agent - Monitors PR CI/CD status and triggers recovery
Part of the Issue-to-PR Pipeline Stage 7
"""

import time
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from core.agent import BaseAgent
from core.tools import ToolResponse
from core.smart_state import SmartStateManager, StateType
from core.telemetry import TelemetryCollector


@dataclass
class CICheckResult:
    """Result of a CI check"""

    name: str
    status: str  # 'completed', 'in_progress', 'queued'
    conclusion: str  # 'success', 'failure', 'neutral', 'cancelled'
    details_url: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class CIMonitoringResult:
    """Result of CI monitoring"""

    pr_number: int
    all_passed: bool
    checks: List[CICheckResult]
    recovery_attempted: bool = False
    recovery_succeeded: bool = False
    duration_seconds: float = 0


class CIMonitoringAgent(BaseAgent):
    """
    Monitors CI/CD status for PRs and triggers recovery for failures.

    Key capabilities:
    - Polls GitHub checks API
    - Categorizes CI failures
    - Triggers auto-recovery for simple issues
    - Reports status back to issue
    """

    def __init__(self):
        super().__init__(agent_id="ci_monitoring_agent")
        self.state_manager = SmartStateManager()
        self.telemetry = TelemetryCollector()
        self.repo_base = Path.home() / "Documents" / "GitHub"

    def register_tools(self):
        """Register tools for the agent"""
        pass  # Uses subprocess for gh CLI

    def _apply_action(self, action: str, params: dict) -> ToolResponse:
        """Apply an action - not used for this agent"""
        return ToolResponse(success=True, data={}, metadata={})

    def execute_task(self, task_data: Dict[str, Any]) -> ToolResponse:
        """
        Monitor CI/CD for a PR and attempt recovery if needed.

        Expected task_data:
        - pr_number: PR number to monitor
        - repo: Repository name
        - timeout: Max time to wait for CI (default 600 seconds)
        - auto_fix: Whether to attempt auto-recovery (default True)
        """
        try:
            # Create execution state
            state_id = self.state_manager.create_state(
                StateType.AGENT_EXECUTION,
                {
                    "agent": "CIMonitoringAgent",
                    "task": task_data,
                    "phase": "initialization",
                },
            )

            pr_number = task_data.get("pr_number")
            repo = task_data.get("repo", "12-factor-agents")
            timeout = task_data.get("timeout", 600)
            auto_fix = task_data.get("auto_fix", True)

            print(f"📊 Monitoring CI/CD for PR #{pr_number}")

            # Monitor CI checks
            start_time = time.time()
            checks = self._monitor_pr_checks(repo, pr_number, timeout)

            # Analyze results
            all_passed = all(
                check.conclusion == "success"
                for check in checks
                if check.status == "completed"
            )

            failures = [check for check in checks if check.conclusion == "failure"]

            recovery_attempted = False
            recovery_succeeded = False

            # Attempt recovery if needed
            if failures and auto_fix:
                print(f"   🔧 Attempting to fix {len(failures)} failures...")
                recovery_attempted = True
                recovery_succeeded = self._attempt_recovery(repo, pr_number, failures)

                if recovery_succeeded:
                    print("   ✅ Recovery successful, re-running checks...")
                    # Re-monitor after fix
                    checks = self._monitor_pr_checks(repo, pr_number, 120)
                    all_passed = all(
                        check.conclusion == "success"
                        for check in checks
                        if check.status == "completed"
                    )

            duration = time.time() - start_time

            result = CIMonitoringResult(
                pr_number=pr_number,
                all_passed=all_passed,
                checks=checks,
                recovery_attempted=recovery_attempted,
                recovery_succeeded=recovery_succeeded,
                duration_seconds=duration,
            )

            # Update state
            self.state_manager.update_state(
                state_id,
                {
                    "phase": "completed",
                    "all_passed": all_passed,
                    "recovery_attempted": recovery_attempted,
                },
            )

            # Report results
            print("\n📈 CI Monitoring Complete:")
            print(f"   PR: #{result.pr_number}")
            print(
                f"   Status: {'✅ All checks passed' if result.all_passed else '❌ Some checks failed'}"
            )
            print(f"   Duration: {result.duration_seconds:.1f}s")

            if result.recovery_attempted:
                print(
                    f"   Recovery: {'✅ Succeeded' if result.recovery_succeeded else '❌ Failed'}"
                )

            return ToolResponse(
                success=True,
                data={
                    "pr_number": result.pr_number,
                    "all_passed": result.all_passed,
                    "checks": [self._serialize_check(c) for c in result.checks],
                    "recovery_attempted": result.recovery_attempted,
                    "recovery_succeeded": result.recovery_succeeded,
                    "duration_seconds": result.duration_seconds,
                    "state_id": state_id,
                },
                metadata={
                    "agent": "CIMonitoringAgent",
                    "pr_number": pr_number,
                    "repo": repo,
                },
            )

        except Exception as e:
            print(f"❌ CI monitoring failed: {e}")
            return ToolResponse(
                success=False,
                error=str(e),
                data={},
                metadata={"agent": "CIMonitoringAgent"},
            )

    def _monitor_pr_checks(
        self, repo: str, pr_number: int, timeout: int
    ) -> List[CICheckResult]:
        """Monitor PR checks until completion or timeout"""

        start_time = time.time()
        checks = []

        while time.time() - start_time < timeout:
            # Get check status using gh CLI
            try:
                result = subprocess.run(
                    [
                        "gh",
                        "pr",
                        "checks",
                        str(pr_number),
                        "--repo",
                        repo,
                        "--json",
                        "name,status,conclusion,detailsUrl",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                check_data = json.loads(result.stdout)
                checks = [
                    CICheckResult(
                        name=check.get("name", "Unknown"),
                        status=check.get("status", "unknown"),
                        conclusion=check.get("conclusion", ""),
                        details_url=check.get("detailsUrl"),
                    )
                    for check in check_data
                ]

                # Check if all are completed
                all_completed = all(check.status == "completed" for check in checks)

                if all_completed:
                    break

                # Show progress
                in_progress = sum(
                    1 for check in checks if check.status == "in_progress"
                )
                if in_progress > 0:
                    print(f"   ⏳ {in_progress} checks still running...")

                time.sleep(10)  # Wait 10 seconds before next check

            except subprocess.CalledProcessError as e:
                print(f"   ⚠️ Failed to get check status: {e}")
                break

        return checks

    def _attempt_recovery(
        self, repo: str, pr_number: int, failures: List[CICheckResult]
    ) -> bool:
        """Attempt to recover from CI failures"""

        # Categorize failures
        formatting_failures = [
            f
            for f in failures
            if "format" in f.name.lower() or "black" in f.name.lower()
        ]

        linting_failures = [
            f for f in failures if "lint" in f.name.lower() or "ruff" in f.name.lower()
        ]

        recovered = False

        # Fix formatting issues
        if formatting_failures:
            print("   🎨 Fixing formatting issues...")
            if self._fix_formatting(repo, pr_number):
                recovered = True

        # Fix linting issues
        if linting_failures:
            print("   🔍 Fixing linting issues...")
            if self._fix_linting(repo, pr_number):
                recovered = True

        return recovered

    def _fix_formatting(self, repo: str, pr_number: int) -> bool:
        """Fix formatting issues in PR"""

        try:
            # Get PR branch
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "view",
                    str(pr_number),
                    "--repo",
                    repo,
                    "--json",
                    "headRefName",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            branch = json.loads(result.stdout).get("headRefName")

            if not branch:
                return False

            repo_path = self.repo_base / repo

            # Checkout branch
            subprocess.run(["git", "checkout", branch], cwd=repo_path, check=True)

            # Run formatter
            subprocess.run(["black", "."], cwd=repo_path, check=True)

            # Commit and push if changes
            subprocess.run(["git", "add", "-A"], cwd=repo_path)

            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"], cwd=repo_path
            )

            if result.returncode != 0:
                # There are changes to commit
                subprocess.run(
                    ["git", "commit", "-m", "🎨 Auto-fix: Apply Black formatting"],
                    cwd=repo_path,
                    check=True,
                )

                subprocess.run(["git", "push"], cwd=repo_path, check=True)

                print("   ✅ Formatting fixed and pushed")
                return True

        except Exception as e:
            print(f"   ❌ Failed to fix formatting: {e}")

        return False

    def _fix_linting(self, repo: str, pr_number: int) -> bool:
        """Fix linting issues in PR"""

        try:
            # Similar to formatting but with ruff
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "view",
                    str(pr_number),
                    "--repo",
                    repo,
                    "--json",
                    "headRefName",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            branch = json.loads(result.stdout).get("headRefName")

            if not branch:
                return False

            repo_path = self.repo_base / repo

            # Checkout branch
            subprocess.run(["git", "checkout", branch], cwd=repo_path, check=True)

            # Run linter with fix
            subprocess.run(["ruff", "--fix", "."], cwd=repo_path)

            # Commit and push if changes
            subprocess.run(["git", "add", "-A"], cwd=repo_path)

            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"], cwd=repo_path
            )

            if result.returncode != 0:
                subprocess.run(
                    ["git", "commit", "-m", "🔍 Auto-fix: Apply Ruff linting fixes"],
                    cwd=repo_path,
                    check=True,
                )

                subprocess.run(["git", "push"], cwd=repo_path, check=True)

                print("   ✅ Linting fixed and pushed")
                return True

        except Exception as e:
            print(f"   ❌ Failed to fix linting: {e}")

        return False

    def _serialize_check(self, check: CICheckResult) -> Dict:
        """Serialize CI check result for JSON"""
        return {
            "name": check.name,
            "status": check.status,
            "conclusion": check.conclusion,
            "details_url": check.details_url,
            "error_message": check.error_message,
        }
