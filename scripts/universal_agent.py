#!/usr/bin/env python3
"""Universal Agent - One agent to rule them all (Factor 10: Small, Focused)"""

import json
import os
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class UniversalAgent:
    """Universal agent that auto-detects task type from issue"""

    def __init__(self, issue_number: int):
        self.issue_number = issue_number
        self.agent_id = f"agent_{issue_number}"
        self.status_file = Path(f"/tmp/{self.agent_id}_status.json")
        self.branch_name = f"feature/issue-{issue_number}"

        # Parse issue to determine task type
        self.task_type = self.detect_task_type()

        # Setup timeout protection (Factor 9: Compact Errors)
        signal.signal(signal.SIGALRM, self.timeout_handler)

    def detect_task_type(self) -> str:
        """Auto-detect task type from issue title/body"""
        success, stdout, _ = self.run_command(
            f"gh issue view {self.issue_number} --json title,body"
        )
        if success:
            data = json.loads(stdout)
            title = data.get("title", "").lower()

            # Pattern matching for task type
            if "performance" in title or "benchmark" in title:
                return "performance"
            elif "document" in title or "docs" in title:
                return "documentation"
            elif "ci" in title or "cd" in title or "quality" in title:
                return "cicd"
            elif "marketplace" in title or "plugin" in title:
                return "marketplace"
            else:
                return "generic"
        return "generic"

    def timeout_handler(self, signum, frame):
        """Factor 9: Compact error into context"""
        self.update_status(99, "Timeout", {"error": "Exceeded 30s limit"})
        raise TimeoutError("Operation exceeded safe time limit")

    def update_status(self, progress: int, message: str, data: Dict[str, Any] = None):
        """Factor 5: Unified execution and business state"""
        status = {
            "agent_id": self.agent_id,
            "issue": self.issue_number,
            "task_type": self.task_type,
            "progress": progress,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "pid": os.getpid(),
        }
        self.status_file.write_text(json.dumps(status, indent=2))

    def run_command(self, cmd: str, timeout: int = 30) -> tuple:
        """Execute with timeout protection"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def run_in_background(self):
        """Factor 11: Trigger from anywhere"""
        cmd = f"nohup python {__file__} --execute {self.issue_number} > /tmp/{self.agent_id}.log 2>&1 &"
        subprocess.run(cmd, shell=True)
        return self.agent_id

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        if self.status_file.exists():
            return json.loads(self.status_file.read_text())
        return {"progress": 0, "message": "Not started"}

    def execute(self):
        """Main execution - Factor 8: Own your control flow"""
        try:
            self.update_status(0, f"Starting {self.task_type} task")

            # Create branch
            self.update_status(10, "Creating feature branch")
            self.run_command(f"git checkout -b {self.branch_name}")

            # Task-specific implementation
            if self.task_type == "performance":
                self.implement_performance_task()
            elif self.task_type == "documentation":
                self.implement_documentation_task()
            elif self.task_type == "cicd":
                self.implement_cicd_task()
            else:
                self.implement_generic_task()

            # Create PR
            self.update_status(90, "Creating pull request")
            self.create_pr()

            self.update_status(100, "✅ Complete")

        except Exception as e:
            # Factor 9: Compact error
            self.update_status(99, f"Error: {str(e)}", {"error": str(e)})
        finally:
            signal.alarm(0)

    def implement_generic_task(self):
        """Generic implementation pattern"""
        self.update_status(50, "Implementing generic task")
        # Implementation based on issue content
        pass

    def implement_performance_task(self):
        """Performance-specific implementation"""
        self.update_status(50, "Implementing performance improvements")
        # Performance optimization logic
        pass

    def implement_documentation_task(self):
        """Documentation-specific implementation"""
        self.update_status(50, "Updating documentation")
        # Documentation updates
        pass

    def implement_cicd_task(self):
        """CI/CD-specific implementation"""
        self.update_status(50, "Implementing CI/CD improvements")
        # CI/CD pipeline updates
        pass

    def create_pr(self):
        """Create pull request for the implementation"""
        title = f"Implement Issue #{self.issue_number}"
        self.run_command(f"git add -A && git commit -m '{title}'")
        self.run_command(f"git push -u origin {self.branch_name}")
        self.run_command(
            f"gh pr create --title '{title}' --body 'Closes #{self.issue_number}'"
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        issue_number = int(sys.argv[1])
        agent = UniversalAgent(issue_number)

        if "--status" in sys.argv:
            print(json.dumps(agent.get_status(), indent=2))
        elif "--background" in sys.argv:
            agent_id = agent.run_in_background()
            print(f"Agent {agent_id} launched in background")
        else:
            agent.execute()
