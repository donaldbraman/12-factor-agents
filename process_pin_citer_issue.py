#!/usr/bin/env python3
"""Process pin-citer issue #145 using AsyncSparky."""

import sys
from pathlib import Path
from core.external_issue_processor import SimpleExternalIssueProcessor


def main():
    print("🎯 Processing pin-citer issue #145...")
    print("-" * 60)

    # Read issue content
    issue_file = Path("/tmp/issue_145_content.txt")
    if not issue_file.exists():
        print("❌ Issue content file not found")
        return False

    issue_content = issue_file.read_text()

    processor = SimpleExternalIssueProcessor()

    # Process the issue as a cite-assist issue (same repo family)
    result = processor.process_cite_assist_issue(145, issue_content)

    print("\n📊 Results:")
    print(f"  Agent used: {result.get('agent', 'Unknown')}")
    print(f"  Confidence: {result.get('confidence', 0):.1%}")
    print(f"  Status: {result.get('status', 'Unknown')}")

    if result.get("fix_applied"):
        print("\n✅ Fix applied successfully!")
        print(f"  Branch: {result.get('branch', 'Unknown')}")
        print(f"  PR: {result.get('pr_url', 'Not created')}")
    else:
        print("\n❌ Fix not applied")
        print(f"  Reason: {result.get('reason', 'Unknown')}")

    if result.get("validation_results"):
        print("\n🧪 Validation:")
        for test, status in result["validation_results"].items():
            emoji = "✅" if status == "passed" else "❌"
            print(f"  {emoji} {test}: {status}")

    return result.get("success", False)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
