#!/usr/bin/env python3
"""
Process Issue Through Code Generation Pipeline
Test the complete issue-to-PR pipeline
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.code_generation_pipeline import CodeGenerationPipeline  # noqa: E402
from core.external_issue_processor import SimpleExternalIssueProcessor  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="Process issue through code generation pipeline"
    )
    parser.add_argument("repo", help="Repository name (e.g., pin-citer)")
    parser.add_argument("issue", type=int, help="Issue number")
    parser.add_argument(
        "--auto-merge", action="store_true", help="Auto-merge if all checks pass"
    )
    parser.add_argument(
        "--use-external", action="store_true", help="Use external issue processor"
    )

    args = parser.parse_args()

    print(f"\n🎯 Processing {args.repo} issue #{args.issue}")
    print("=" * 60)

    if args.use_external:
        # Use the existing external processor
        processor = SimpleExternalIssueProcessor()

        # Get issue content
        import subprocess
        import json

        result = subprocess.run(
            [
                "gh",
                "issue",
                "view",
                str(args.issue),
                "--repo",
                args.repo,
                "--json",
                "body",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ Failed to fetch issue: {result.stderr}")
            return 1

        issue_content = json.loads(result.stdout).get("body", "")

        # Process through external processor
        result = processor.process_cite_assist_issue(args.issue, issue_content)

        if result.get("success"):
            print("✅ Issue processed successfully")
            print(f"   Agent: {result.get('agent')}")
            return 0
        else:
            print(f"❌ Processing failed: {result.get('error')}")
            return 1

    else:
        # Use the new code generation pipeline
        pipeline = CodeGenerationPipeline()

        result = pipeline.process_issue(
            repo=args.repo, issue_number=args.issue, auto_merge=args.auto_merge
        )

        if result.success:
            print("\n✨ Success!")
            print(f"   PR: {result.pr_url}")
            print(f"   Branch: {result.branch}")
            print(f"   Duration: {result.duration_seconds:.1f}s")
            return 0
        else:
            print(f"\n❌ Failed at stage: {result.stage_failed}")
            print(f"   Error: {result.error}")
            return 1


if __name__ == "__main__":
    sys.exit(main())
