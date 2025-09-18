#!/usr/bin/env python3
"""
Validation script for Sparky's output.

This script validates Sparky's generated code to ensure it meets our quality standards.
Our code is precious - this tool helps protect it from common Sparky mistakes.

Usage:
    uv run python scripts/validate_sparky_output.py --branch <branch_name>
    uv run python scripts/validate_sparky_output.py --issue <issue_number>
    uv run python scripts/validate_sparky_output.py --files <file1> <file2> ...

Examples:
    # Validate current branch changes
    uv run python scripts/validate_sparky_output.py --branch feat/new-feature
    
    # Validate implementation for issue #123
    uv run python scripts/validate_sparky_output.py --issue 123
    
    # Validate specific files
    uv run python scripts/validate_sparky_output.py --files core/new_module.py tests/test_new_module.py
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from core.sparky_validator import SparkySelfValidator

# Add parent directory to path for imports if needed
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class ValidationReport:
    """Report of validation results."""

    timestamp: str
    branch: Optional[str]
    issue_number: Optional[int]
    files_analyzed: List[str]
    validation_results: Dict[str, Any]
    quality_score: float
    success: bool
    recommendations: List[str]


class SparkyOutputValidator:
    """Validates Sparky's output from different sources."""

    def __init__(self):
        self.validator = SparkySelfValidator()
        self.repo_root = Path(__file__).parent.parent

    def validate_branch(self, branch_name: str) -> ValidationReport:
        """Validate all changes in a branch compared to main."""
        print(f"🔍 Validating branch: {branch_name}")

        # Get changed files
        cmd = f"git diff --name-only main...{branch_name}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Error getting changed files: {result.stderr}")
            sys.exit(1)

        changed_files = (
            result.stdout.strip().split("\n") if result.stdout.strip() else []
        )

        # Get diff content
        cmd = f"git diff main...{branch_name}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        diff_content = result.stdout

        # Build implementation dict from git data
        implementation = self._build_implementation_from_diff(
            changed_files, diff_content
        )

        # Run validation
        issue_info = {"number": 0, "title": f"Branch: {branch_name}"}
        validation_result = self.validator.validate_implementation(
            implementation, issue_info
        )

        # Create report
        report = ValidationReport(
            timestamp=datetime.now().isoformat(),
            branch=branch_name,
            issue_number=None,
            files_analyzed=changed_files,
            validation_results=validation_result,
            quality_score=validation_result.get("quality_score", 0.0),
            success=validation_result.get("success", False),
            recommendations=self._generate_recommendations(validation_result),
        )

        return report

    def validate_issue(self, issue_number: int) -> ValidationReport:
        """Validate implementation for a specific issue."""
        print(f"🔍 Validating issue #{issue_number}")

        # Find branch for this issue
        cmd = f"git branch -a | grep -i issue-{issue_number:03d}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0 or not result.stdout.strip():
            print(f"❌ No branch found for issue #{issue_number}")
            sys.exit(1)

        branch = result.stdout.strip().split("/")[-1]
        report = self.validate_branch(branch)
        report.issue_number = issue_number

        return report

    def validate_files(self, file_paths: List[str]) -> ValidationReport:
        """Validate specific files."""
        print(f"🔍 Validating {len(file_paths)} files")

        # Read file contents
        implementation = self._build_implementation_from_files(file_paths)

        # Run validation
        issue_info = {"number": 0, "title": f"Files: {', '.join(file_paths)}"}
        validation_result = self.validator.validate_implementation(
            implementation, issue_info
        )

        # Create report
        report = ValidationReport(
            timestamp=datetime.now().isoformat(),
            branch=None,
            issue_number=None,
            files_analyzed=file_paths,
            validation_results=validation_result,
            quality_score=validation_result.get("quality_score", 0.0),
            success=validation_result.get("success", False),
            recommendations=self._generate_recommendations(validation_result),
        )

        return report

    def _build_implementation_from_diff(
        self, files: List[str], diff_content: str
    ) -> Dict:
        """Build implementation dict from git diff."""
        implementation = {
            "files_modified": [],
            "files_created": [],
            "class_names": [],
            "method_names": [],
            "code_content": diff_content,
            "methods": [],
            "has_tests": False,
            "has_error_handling": False,
            "has_logging": False,
            "has_type_hints": False,
        }

        # Categorize files
        for file in files:
            if not file:  # Skip empty strings
                continue
            file_path = self.repo_root / file
            if file_path.exists():
                implementation["files_modified"].append(file)
            else:
                implementation["files_created"].append(file)

            # Check for test files
            if "test" in file.lower():
                implementation["has_tests"] = True

        # Extract class and method names from diff
        import re

        # Find class definitions
        class_pattern = r"^\+\s*class\s+(\w+)"
        for match in re.finditer(class_pattern, diff_content, re.MULTILINE):
            implementation["class_names"].append(match.group(1))

        # Find method definitions
        method_pattern = r"^\+\s*def\s+(\w+)"
        for match in re.finditer(method_pattern, diff_content, re.MULTILINE):
            method_name = match.group(1)
            implementation["method_names"].append(method_name)

            # Simple method analysis
            implementation["methods"].append(
                {
                    "name": method_name,
                    "params": [],  # Would need more parsing for exact params
                    "has_docstring": '"""' in diff_content or "'''" in diff_content,
                }
            )

        # Check for error handling, logging, type hints
        if "try:" in diff_content or "except" in diff_content:
            implementation["has_error_handling"] = True
        if "logging" in diff_content or "logger" in diff_content.lower():
            implementation["has_logging"] = True
        if "->" in diff_content or ": " in diff_content:
            implementation["has_type_hints"] = True

        return implementation

    def _build_implementation_from_files(self, file_paths: List[str]) -> Dict:
        """Build implementation dict from specific files."""
        implementation = {
            "files_modified": file_paths,
            "files_created": [],
            "class_names": [],
            "method_names": [],
            "code_content": "",
            "methods": [],
            "has_tests": any("test" in f.lower() for f in file_paths),
            "has_error_handling": False,
            "has_logging": False,
            "has_type_hints": False,
        }

        import re

        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                path = self.repo_root / file_path

            if path.exists() and path.suffix == ".py":
                content = path.read_text()
                implementation["code_content"] += f"\n# File: {file_path}\n{content}\n"

                # Extract classes
                for match in re.finditer(r"^class\s+(\w+)", content, re.MULTILINE):
                    implementation["class_names"].append(match.group(1))

                # Extract methods with docstring detection
                for match in re.finditer(
                    r"^def\s+(\w+)\((.*?)\):", content, re.MULTILINE
                ):
                    method_name = match.group(1)
                    params_str = match.group(2)
                    implementation["method_names"].append(method_name)

                    # Parse parameters
                    params = [
                        p.strip().split(":")[0].strip()
                        for p in params_str.split(",")
                        if p.strip()
                    ]

                    # Check for docstring after method definition
                    method_start = match.end()
                    next_lines = content[
                        method_start : method_start + 200
                    ]  # Check next ~4 lines
                    has_docstring = bool(
                        re.search(
                            r'^\s*""".*?"""', next_lines, re.DOTALL | re.MULTILINE
                        )
                    )

                    implementation["methods"].append(
                        {
                            "name": method_name,
                            "params": params,
                            "has_docstring": has_docstring,
                        }
                    )

                # Check features
                if "try:" in content or "except" in content:
                    implementation["has_error_handling"] = True
                if "logging" in content or "logger" in content.lower():
                    implementation["has_logging"] = True
                if "->" in content or re.search(r":\s*\w+\s*=", content):
                    implementation["has_type_hints"] = True

        return implementation

    def _generate_recommendations(self, validation_result: Dict) -> List[str]:
        """Generate recommendations from validation results."""
        recommendations = []

        if not validation_result.get("success"):
            recommendations.append("❌ Validation failed - manual review required")

            errors = validation_result.get("validation_errors", [])
            for error in errors[:3]:  # Top 3 errors
                if not error.startswith("Fix:"):
                    recommendations.append(f"  • {error}")
        else:
            quality = validation_result.get("quality_score", 0)
            if quality == 1.0:
                recommendations.append("✅ Perfect implementation!")
            elif quality >= 0.95:
                recommendations.append("✅ High quality implementation")
            else:
                recommendations.append(
                    f"⚠️ Quality score: {quality:.1%} - consider improvements"
                )

        iterations = validation_result.get("iterations", 1)
        if iterations > 1:
            recommendations.append(f"📝 Required {iterations} iterations to pass")

        return recommendations

    def print_report(self, report: ValidationReport):
        """Print a formatted validation report."""
        print("\n" + "=" * 60)
        print("SPARKY VALIDATION REPORT")
        print("=" * 60)

        print(f"\n📊 Quality Score: {report.quality_score:.1%}")
        print(f"✅ Success: {'Yes' if report.success else 'No'}")

        if report.branch:
            print(f"🌿 Branch: {report.branch}")
        if report.issue_number:
            print(f"🎯 Issue: #{report.issue_number}")

        print(f"\n📁 Files Analyzed ({len(report.files_analyzed)}):")
        for file in report.files_analyzed[:10]:  # Show first 10
            print(f"  • {file}")
        if len(report.files_analyzed) > 10:
            print(f"  ... and {len(report.files_analyzed) - 10} more")

        print("\n💡 Recommendations:")
        for rec in report.recommendations:
            print(f"  {rec}")

        # Detailed validation results
        if not report.success:
            print("\n⚠️ Validation Details:")
            details = report.validation_results
            if "validation_errors" in details:
                for i, error in enumerate(details["validation_errors"][:5], 1):
                    if not error.startswith("Fix:"):
                        print(f"  {i}. {error}")

        print("\n" + "=" * 60)

    def save_report(self, report: ValidationReport, output_file: Optional[str] = None):
        """Save report to JSON file."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"validation_report_{timestamp}.json"

        output_path = Path(output_file)

        # Convert report to dict
        report_dict = asdict(report)

        # Save as JSON
        with open(output_path, "w") as f:
            json.dump(report_dict, f, indent=2, default=str)

        print(f"\n💾 Report saved to: {output_path}")


def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(
        description="Validate Sparky's output - protect our precious code!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate current branch against main
  %(prog)s --branch feat/new-feature
  
  # Validate implementation for issue #123
  %(prog)s --issue 123
  
  # Validate specific files
  %(prog)s --files core/new_module.py tests/test_new_module.py
        """,
    )

    # Add mutually exclusive group for input source
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--branch", "-b", help="Validate changes in a git branch")
    group.add_argument(
        "--issue", "-i", type=int, help="Validate implementation for an issue number"
    )
    group.add_argument("--files", "-f", nargs="+", help="Validate specific files")

    # Additional options
    parser.add_argument("--output", "-o", help="Save report to JSON file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")

    args = parser.parse_args()

    # Create validator
    validator = SparkyOutputValidator()

    try:
        # Run validation based on input source
        if args.branch:
            report = validator.validate_branch(args.branch)
        elif args.issue:
            report = validator.validate_issue(args.issue)
        else:  # args.files
            report = validator.validate_files(args.files)

        # Output results
        if not args.quiet:
            validator.print_report(report)
        else:
            # Minimal output for quiet mode
            status = "PASS" if report.success else "FAIL"
            print(f"{status}: {report.quality_score:.1%}")

        # Save report if requested
        if args.output:
            validator.save_report(report, args.output)

        # Exit with appropriate code
        sys.exit(0 if report.success else 1)

    except KeyboardInterrupt:
        print("\n⚠️ Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
