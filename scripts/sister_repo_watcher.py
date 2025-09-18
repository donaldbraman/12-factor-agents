#!/usr/bin/env python3
"""
Sister Repository Watcher

Simple local file watcher for sister repositories like cite-assist.
Just watches sister_repos/*/  for new JSON files and processes them.
"""

import json
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class SisterRepoWatcher:
    """Watches sister repo directories for new reports"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.sister_dir = self.base_dir / "sister_repos"
        self.processed_dir = self.sister_dir / "processed"
        self.failed_dir = self.sister_dir / "failed"

        # Ensure directories exist
        for dir_path in [self.processed_dir, self.failed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def scan_for_reports(self) -> List[Path]:
        """Scan for new JSON reports in sister repo directories"""
        reports = []

        # Look in each repo subdirectory (but not processed/failed)
        for repo_dir in self.sister_dir.iterdir():
            if repo_dir.is_dir() and repo_dir.name not in ["processed", "failed"]:
                reports.extend(repo_dir.glob("*.json"))

        return reports

    def validate_report(self, report_path: Path) -> bool:
        """Basic validation of report format"""
        try:
            with open(report_path, "r") as f:
                data = json.load(f)

            # Just need basic structure
            if "repo" not in data or "data" not in data:
                print(f"❌ Missing required fields in {report_path.name}")
                return False

            return True

        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in {report_path.name}")
            return False
        except Exception as e:
            print(f"❌ Error validating {report_path.name}: {e}")
            return False

    def process_report(self, report_path: Path) -> bool:
        """Process a single report file"""
        try:
            print(f"🔄 Processing {report_path.name}")

            if not self.validate_report(report_path):
                return False

            with open(report_path, "r") as f:
                data = json.load(f)

            repo_name = data.get("repo", "unknown")
            report_data = data.get("data", [])

            if not report_data:
                print("ℹ️  No data in report")
                return True

            # Create GitHub issues for high priority items
            created_issues = 0

            for item in report_data:
                priority = item.get("priority", "low")
                if priority in ["high", "critical"]:
                    title = (
                        f"Sister Repo: {item.get('title', 'Issue from ' + repo_name)}"
                    )
                    body = self._create_issue_body(item, data)

                    if self._create_github_issue(title, body):
                        created_issues += 1

            print(f"✅ Created {created_issues} GitHub issues")
            return True

        except Exception as e:
            print(f"❌ Error processing {report_path.name}: {e}")
            return False

    def _create_issue_body(self, item: Dict, report_data: Dict) -> str:
        """Create a formatted issue body"""
        repo_name = report_data.get("repo", "unknown")

        body = f"""# Issue from {repo_name}

**Source:** {repo_name}
**Priority:** {item.get('priority', 'medium')}

## Description
{item.get('description', 'No description provided')}

## Details
"""

        if "file" in item:
            body += f"**File:** {item['file']}\\n"
        if "line" in item:
            body += f"**Line:** {item['line']}\\n"
        if "type" in item:
            body += f"**Type:** {item['type']}\\n"

        if "context" in item:
            body += f"\\n## Context\\n```\\n{item['context']}\\n```\\n"

        body += "\\n---\\n*Sister repository integration*"
        return body

    def _create_github_issue(self, title: str, body: str) -> bool:
        """Create a GitHub issue"""
        try:
            cmd = ["gh", "issue", "create", "--title", title, "--body", body]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            issue_url = result.stdout.strip()
            print(f"✅ Created issue: {issue_url}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create GitHub issue: {e}")
            return False

    def move_report(self, report_path: Path, success: bool):
        """Move processed report to appropriate directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = report_path.stem

        if success:
            dest = self.processed_dir / f"{base_name}_{timestamp}.json"
            print(f"✅ Moving to processed: {dest.name}")
        else:
            dest = self.failed_dir / f"{base_name}_{timestamp}.json"
            print(f"❌ Moving to failed: {dest.name}")

        report_path.rename(dest)

    def process_all_pending(self):
        """Process all pending reports"""
        reports = self.scan_for_reports()

        if not reports:
            print("ℹ️  No pending reports found")
            return

        print(f"🔍 Found {len(reports)} pending reports")

        for report_path in reports:
            success = self.process_report(report_path)
            self.move_report(report_path, success)

        print(f"\\n✅ Processed {len(reports)} reports")

    def watch_for_reports(self, interval: int = 10):
        """Watch for new reports and process them automatically"""
        print(f"👀 Watching sister_repos/ every {interval} seconds...")
        print("Press Ctrl+C to stop")

        try:
            while True:
                self.process_all_pending()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\\n🛑 Stopping sister repo watcher")


def main():
    """Main execution function"""
    watcher = SisterRepoWatcher()

    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        # Watch mode
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        watcher.watch_for_reports(interval)
    else:
        # One-time processing
        watcher.process_all_pending()


if __name__ == "__main__":
    main()
