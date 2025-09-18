#!/usr/bin/env python3
"""
External Report Submission Script

This script can be used by external repositories (like cite-assist) to submit
reports to the 12-factor-agents quality flywheel system.

Usage examples:
  # Submit an analysis report
  python submit_external_report.py --type analysis --file analysis.json
  
  # Submit a quality report directly
  python submit_external_report.py --type quality --score 85 --issues issues.json
  
  # Submit via GitHub (clone, add report, commit, push)
  python submit_external_report.py --type analysis --file analysis.json --submit-via-git
"""

import json
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def create_analysis_report(
    repo_name: str, issues: List[Dict], patterns: List[Dict] = None
) -> Dict:
    """Create a standardized analysis report"""
    return {
        "repo": repo_name,
        "timestamp": datetime.now().isoformat(),
        "report_type": "analysis",
        "issues": issues,
        "patterns": patterns or [],
        "recommendations": generate_recommendations(issues),
        "metadata": {"generated_by": "external_report_submission", "version": "1.0"},
    }


def create_quality_report(
    repo_name: str, quality_score: int, quality_issues: List[Dict]
) -> Dict:
    """Create a standardized quality report"""
    return {
        "repo": repo_name,
        "timestamp": datetime.now().isoformat(),
        "report_type": "quality",
        "quality_score": quality_score,
        "quality_issues": quality_issues,
        "recommendations": generate_quality_recommendations(
            quality_score, quality_issues
        ),
        "metadata": {"generated_by": "external_report_submission", "version": "1.0"},
    }


def create_issue_list_report(repo_name: str, issues: List[Dict]) -> Dict:
    """Create a standardized issue list report"""
    return {
        "repo": repo_name,
        "timestamp": datetime.now().isoformat(),
        "report_type": "issue_list",
        "issues": issues,
        "summary": {
            "total_issues": len(issues),
            "high_priority": len([i for i in issues if i.get("priority") == "high"]),
            "medium_priority": len(
                [i for i in issues if i.get("priority") == "medium"]
            ),
            "low_priority": len([i for i in issues if i.get("priority") == "low"]),
        },
        "metadata": {"generated_by": "external_report_submission", "version": "1.0"},
    }


def generate_recommendations(issues: List[Dict]) -> List[str]:
    """Generate recommendations based on issues"""
    recommendations = []

    # Count issue types
    types = {}
    for issue in issues:
        issue_type = issue.get("type", "unknown")
        types[issue_type] = types.get(issue_type, 0) + 1

    # Generate recommendations based on patterns
    if types.get("placeholder", 0) > 3:
        recommendations.append("Replace placeholder implementations with real code")

    if types.get("todo", 0) > 5:
        recommendations.append("Complete TODO items before release")

    if types.get("test", 0) > 2:
        recommendations.append("Add comprehensive test coverage")

    if types.get("documentation", 0) > 2:
        recommendations.append("Improve code documentation and comments")

    return recommendations


def generate_quality_recommendations(score: int, issues: List[Dict]) -> List[str]:
    """Generate quality-specific recommendations"""
    recommendations = []

    if score < 50:
        recommendations.append(
            "URGENT: Quality score critically low - immediate attention required"
        )
    elif score < 70:
        recommendations.append(
            "Quality score below acceptable threshold - improvement needed"
        )

    # Group issues by category
    categories = {}
    for issue in issues:
        cat = issue.get("category", "other")
        categories[cat] = categories.get(cat, 0) + 1

    # Recommendations based on issue categories
    if categories.get("complexity", 0) > 5:
        recommendations.append("Refactor complex functions to improve maintainability")

    if categories.get("duplication", 0) > 3:
        recommendations.append("Remove code duplication through refactoring")

    if categories.get("security", 0) > 0:
        recommendations.append("CRITICAL: Address security vulnerabilities immediately")

    return recommendations


def submit_via_file(report: Dict, output_file: Path = None) -> bool:
    """Submit report by writing to local file"""
    try:
        if output_file is None:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            repo_name = report["repo"].replace("/", "_")
            output_file = Path(f"{repo_name}_{report['report_type']}_{timestamp}.json")

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"✅ Report saved to: {output_file}")
        print(
            "📋 Next step: Copy this file to 12-factor-agents/incoming_reports/pending/"
        )
        return True

    except Exception as e:
        print(f"❌ Error saving report: {e}")
        return False


def submit_via_git(
    report: Dict, target_repo: str = "donaldbraman/12-factor-agents"
) -> bool:
    """Submit report via git (clone, commit, push)"""
    try:
        print(f"🔄 Submitting report via Git to {target_repo}")

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        repo_name = report["repo"].replace("/", "_")
        filename = f"{repo_name}_{report['report_type']}_{timestamp}.json"

        # Create temporary directory
        temp_dir = Path(f"/tmp/12factor_report_{timestamp}")
        temp_dir.mkdir(exist_ok=True)

        try:
            # Clone the repository
            print("📥 Cloning repository...")
            subprocess.run(
                [
                    "git",
                    "clone",
                    f"https://github.com/{target_repo}.git",
                    str(temp_dir / "repo"),
                ],
                check=True,
                capture_output=True,
            )

            repo_dir = temp_dir / "repo"
            report_file = repo_dir / "incoming_reports" / "pending" / filename

            # Ensure directory exists
            report_file.parent.mkdir(parents=True, exist_ok=True)

            # Write the report
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

            # Git operations
            subprocess.run(["git", "add", str(report_file)], cwd=repo_dir, check=True)
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"feat: Add external report from {report['repo']}\n\nReport type: {report['report_type']}\nGenerated: {report['timestamp']}",
                ],
                cwd=repo_dir,
                check=True,
            )

            subprocess.run(["git", "push"], cwd=repo_dir, check=True)

            print("✅ Report submitted successfully via Git")
            print(f"📁 File: incoming_reports/pending/{filename}")
            return True

        finally:
            # Cleanup
            subprocess.run(["rm", "-rf", str(temp_dir)], check=False)

    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error submitting via Git: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Submit external reports to 12-factor-agents quality flywheel"
    )

    parser.add_argument(
        "--repo",
        required=True,
        help="Source repository name (e.g., donaldbraman/cite-assist)",
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["analysis", "quality", "issue_list"],
        help="Report type",
    )
    parser.add_argument("--file", help="Input file with issues/data (JSON format)")
    parser.add_argument("--output", help="Output file path (default: auto-generate)")
    parser.add_argument(
        "--submit-via-git",
        action="store_true",
        help="Submit via Git (clone, commit, push)",
    )

    # Quality report specific
    parser.add_argument(
        "--score", type=int, help="Quality score (0-100) for quality reports"
    )

    args = parser.parse_args()

    # Load input data if provided
    input_data = []
    if args.file:
        try:
            with open(args.file, "r") as f:
                input_data = json.load(f)
        except Exception as e:
            print(f"❌ Error reading input file: {e}")
            return 1

    # Create report based on type
    if args.type == "analysis":
        if not input_data:
            print("❌ Analysis reports require --file with issues data")
            return 1
        report = create_analysis_report(args.repo, input_data)

    elif args.type == "quality":
        if args.score is None:
            print("❌ Quality reports require --score")
            return 1
        report = create_quality_report(args.repo, args.score, input_data)

    elif args.type == "issue_list":
        if not input_data:
            print("❌ Issue list reports require --file with issues data")
            return 1
        report = create_issue_list_report(args.repo, input_data)

    # Submit the report
    if args.submit_via_git:
        success = submit_via_git(report)
    else:
        output_file = Path(args.output) if args.output else None
        success = submit_via_file(report, output_file)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
