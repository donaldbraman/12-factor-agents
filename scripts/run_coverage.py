#!/usr/bin/env python3
"""
Coverage testing script for 12-factor-agents

This script provides comprehensive coverage testing capabilities with
detailed reporting and configurable thresholds.

Usage:
    python scripts/run_coverage.py [options]

Options:
    --html         Generate HTML coverage report
    --xml          Generate XML coverage report  
    --json         Generate JSON coverage report
    --fail-under   Set minimum coverage threshold (default: 80)
    --verbose      Show detailed coverage information
    --open         Open HTML report in browser (requires --html)

Examples:
    python scripts/run_coverage.py --html --verbose
    python scripts/run_coverage.py --fail-under 85
    python scripts/run_coverage.py --html --open
"""

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path


def run_command(cmd, check=True):
    """Execute a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run test coverage analysis for 12-factor-agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--html", action="store_true", help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--xml", action="store_true", help="Generate XML coverage report"
    )
    parser.add_argument(
        "--json", action="store_true", help="Generate JSON coverage report"
    )
    parser.add_argument(
        "--fail-under",
        type=int,
        default=80,
        help="Minimum coverage threshold (default: 80)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed coverage information"
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open HTML report in browser (requires --html)",
    )

    args = parser.parse_args()

    # Build pytest command
    cmd = [
        "uv",
        "run",
        "pytest",
        "--cov=agents",
        "--cov=core",
        "--cov=bin",
        "--cov=orchestration",
        f"--cov-fail-under={args.fail_under}",
        "tests/",
    ]

    # Add report options
    if args.verbose:
        cmd.append("--cov-report=term-missing")
    else:
        cmd.append("--cov-report=term")

    if args.html:
        cmd.append("--cov-report=html")

    if args.xml:
        cmd.append("--cov-report=xml")

    if args.json:
        cmd.append("--cov-report=json")

    # Run coverage tests
    try:
        _ = run_command(cmd)

        print("\n✅ Coverage testing completed successfully!")
        print(f"Minimum threshold: {args.fail_under}%")

        if args.html:
            html_dir = Path("htmlcov")
            if html_dir.exists():
                print(f"📊 HTML report generated: {html_dir.absolute()}/index.html")

                if args.open:
                    webbrowser.open(f"file://{html_dir.absolute()}/index.html")
                    print("🌐 Opening HTML report in browser...")

        if args.xml:
            xml_file = Path("coverage.xml")
            if xml_file.exists():
                print(f"📄 XML report generated: {xml_file.absolute()}")

        if args.json:
            json_file = Path("coverage.json")
            if json_file.exists():
                print(f"📋 JSON report generated: {json_file.absolute()}")

        return 0

    except subprocess.CalledProcessError as e:
        print("\n❌ Coverage testing failed!")
        print(f"Coverage fell below minimum threshold of {args.fail_under}%")
        return e.returncode


if __name__ == "__main__":
    sys.exit(main())
