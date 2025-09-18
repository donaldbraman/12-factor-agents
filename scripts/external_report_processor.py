#!/usr/bin/env python3
"""
External Report Processor

Monitors incoming_reports/pending for new reports from external repositories
and automatically processes them through the quality flywheel system.
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



class ExternalReportProcessor:
    """Processes reports from external repositories"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.pending_dir = self.base_dir / "incoming_reports" / "pending"
        self.processed_dir = self.base_dir / "incoming_reports" / "processed"
        self.failed_dir = self.base_dir / "incoming_reports" / "failed"

        # Ensure directories exist
        for dir_path in [self.pending_dir, self.processed_dir, self.failed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def scan_for_reports(self) -> List[Path]:
        """Scan for new reports in the pending directory"""
        return list(self.pending_dir.glob("*.json"))

    def validate_report(self, report_path: Path) -> bool:
        """Validate that a report has the required format"""
        try:
            with open(report_path, "r") as f:
                data = json.load(f)

            # Required fields
            required = ["repo", "timestamp", "report_type"]
            if not all(field in data for field in required):
                print(f"❌ Missing required fields in {report_path.name}")
                return False

            # Valid report types
            valid_types = ["analysis", "issue_list", "performance", "quality"]
            if data["report_type"] not in valid_types:
                print(
                    f"❌ Invalid report_type in {report_path.name}: {data['report_type']}"
                )
                return False

            return True

        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in {report_path.name}")
            return False
        except Exception as e:
            print(f"❌ Error validating {report_path.name}: {e}")
            return False

    def process_analysis_report(self, data: Dict) -> bool:
        """Process an analysis report from external repo"""
        try:
            print(f"📊 Processing analysis report from {data['repo']}")

            # Extract issues from the report
            issues = data.get("issues", [])
            patterns = data.get("patterns", [])
            recommendations = data.get("recommendations", [])

            # Create GitHub issues for high-priority items
            created_issues = []

            for issue in issues:
                if issue.get("priority", "low") in ["high", "critical"]:
                    title = f"External Report: {issue.get('title', 'Issue from ' + data['repo'])}"
                    body = self._create_issue_body(issue, data)

                    if self._create_github_issue(title, body):
                        created_issues.append(title)

            # Log the processing results
            print(f"✅ Created {len(created_issues)} GitHub issues from analysis")
            return True

        except Exception as e:
            print(f"❌ Error processing analysis report: {e}")
            return False

    def process_issue_list_report(self, data: Dict) -> bool:
        """Process a list of issues from external repo"""
        try:
            print(f"📋 Processing issue list from {data['repo']}")

            issues = data.get("issues", [])
            if not issues:
                print("ℹ️  No issues in report")
                return True

            # Group by priority
            high_priority = [i for i in issues if i.get("priority") == "high"]
            medium_priority = [i for i in issues if i.get("priority") == "medium"]

            print(
                f"📊 Found {len(high_priority)} high priority, {len(medium_priority)} medium priority issues"
            )

            # Create GitHub issues for high priority items
            for issue in high_priority[:5]:  # Limit to 5 to avoid spam
                title = (
                    f"High Priority: {issue.get('title', 'Issue from ' + data['repo'])}"
                )
                body = self._create_issue_body(issue, data)
                self._create_github_issue(title, body)

            return True

        except Exception as e:
            print(f"❌ Error processing issue list: {e}")
            return False

    def process_quality_report(self, data: Dict) -> bool:
        """Process a quality report from external repo"""
        try:
            print(f"🔍 Processing quality report from {data['repo']}")

            quality_score = data.get("quality_score", 0)
            issues = data.get("quality_issues", [])

            if quality_score < 70:  # Low quality threshold
                title = f"Quality Alert: {data['repo']} score {quality_score}/100"
                body = f"""# Quality Alert from {data['repo']}

**Quality Score:** {quality_score}/100
**Generated:** {data.get('timestamp')}

## Quality Issues Found:
"""
                for issue in issues[:10]:  # Top 10 issues
                    body += f"- **{issue.get('type', 'Unknown')}**: {issue.get('description', 'No description')}\n"

                body += f"""
## Recommendations:
{chr(10).join(f"- {rec}" for rec in data.get('recommendations', [])[:5])}

---
*Automated quality alert from external repository*
"""

                self._create_github_issue(title, body)

            return True

        except Exception as e:
            print(f"❌ Error processing quality report: {e}")
            return False

    def _create_issue_body(self, issue: Dict, report_data: Dict) -> str:
        """Create a formatted issue body"""
        body = f"""# Issue from {report_data['repo']}

**Source:** {report_data['repo']}
**Report Time:** {report_data.get('timestamp')}
**Priority:** {issue.get('priority', 'medium')}

## Description
{issue.get('description', 'No description provided')}

## Details
"""

        if "file" in issue:
            body += f"**File:** {issue['file']}\n"
        if "line" in issue:
            body += f"**Line:** {issue['line']}\n"
        if "category" in issue:
            body += f"**Category:** {issue['category']}\n"

        if "context" in issue:
            body += f"\n## Context\n```\n{issue['context']}\n```\n"

        body += "\n---\n*Automatically generated from external report*"
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

    def process_report(self, report_path: Path) -> bool:
        """Process a single report file"""
        try:
            print(f"\n🔄 Processing {report_path.name}")

            if not self.validate_report(report_path):
                return False

            with open(report_path, "r") as f:
                data = json.load(f)

            # Process based on report type
            report_type = data["report_type"]

            if report_type == "analysis":
                success = self.process_analysis_report(data)
            elif report_type == "issue_list":
                success = self.process_issue_list_report(data)
            elif report_type == "quality":
                success = self.process_quality_report(data)
            elif report_type == "performance":
                # For now, just log performance reports
                print(
                    f"📈 Performance report from {data['repo']}: {data.get('summary', 'No summary')}"
                )
                success = True
            else:
                print(f"❓ Unknown report type: {report_type}")
                success = False

            return success

        except Exception as e:
            print(f"❌ Error processing {report_path.name}: {e}")
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

        print(f"\n✅ Processed {len(reports)} reports")

    def watch_for_reports(self, interval: int = 30):
        """Watch for new reports and process them automatically"""
        print(f"👀 Watching for reports every {interval} seconds...")
        print("Press Ctrl+C to stop")

        try:
            while True:
                self.process_all_pending()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Stopping report watcher")


def main():
    """Main execution function"""
    processor = ExternalReportProcessor()

    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        # Watch mode
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        processor.watch_for_reports(interval)
    else:
        # One-time processing
        processor.process_all_pending()


if __name__ == "__main__":
    main()
