#!/usr/bin/env python3
"""
SPARKY LEAN - Even leaner, no dependencies on complex base classes
Pure Python power!
"""

from pathlib import Path
from typing import Dict, List
import time


class SPARKYLean:
    """The leanest SPARKY - no inheritance, just pure logic"""

    def __init__(self):
        self.start_time = time.time()

    def process_issue(self, issue_path: str) -> Dict:
        """Process a single issue"""
        # Read issue
        content = self._read_issue(issue_path)
        if not content:
            return {"success": False, "error": f"Cannot read {issue_path}"}

        # Classify issue
        issue_type = self._classify(content)

        # Process based on type (placeholder for now)
        return {
            "success": True,
            "issue": issue_path,
            "type": issue_type,
            "action": f"Would process as {issue_type}",
        }

    def _read_issue(self, path: str) -> str:
        """Read issue file"""
        try:
            p = Path(path)
            if not p.exists():
                # Try in issues directory
                p = Path("issues") / Path(path).name
            if p.exists():
                return p.read_text()
        except:
            pass
        return ""

    def _classify(self, content: str) -> str:
        """Simple classification"""
        content_lower = content.lower()
        if any(w in content_lower for w in ["bug", "fix", "error", "broken"]):
            return "bug"
        elif any(w in content_lower for w in ["feature", "implement", "add", "create"]):
            return "feature"
        elif any(w in content_lower for w in ["quality", "analysis", "pattern"]):
            return "quality"
        elif any(w in content_lower for w in ["remove", "delete", "cleanup"]):
            return "cleanup"
        else:
            return "unknown"

    def process_batch(self, issues: List[str]) -> Dict:
        """Process multiple issues"""
        print("⚡ SPARKY LEAN ACTIVATED ⚡")
        print("=" * 50)

        results = {"success": [], "failed": [], "by_type": {}}

        for issue in issues:
            print(f"\n🎯 Processing: {issue}")
            result = self.process_issue(issue)

            if result["success"]:
                results["success"].append(issue)
                issue_type = result.get("type", "unknown")
                if issue_type not in results["by_type"]:
                    results["by_type"][issue_type] = []
                results["by_type"][issue_type].append(issue)
                print(f"  ✅ Success! Type: {issue_type}")
            else:
                results["failed"].append(issue)
                print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")

        elapsed = time.time() - self.start_time

        print("\n" + "=" * 50)
        print("📊 SPARKY LEAN RESULTS")
        print(f"✅ Successful: {len(results['success'])}")
        print(f"❌ Failed: {len(results['failed'])}")
        print(f"⏱️  Time: {elapsed:.2f}s")

        if results["by_type"]:
            print("\n📁 Issues by Type:")
            for issue_type, issues in results["by_type"].items():
                print(f"  • {issue_type}: {len(issues)} issues")

        return results


# Even leaner! Just 94 lines of pure SPARKY power!

if __name__ == "__main__":
    sparky = SPARKYLean()

    # Test with a few issues
    test_issues = [
        "issues/test-simple.md",
        "issues/122.md",
        "issues/001-add-noqa-to-code-review-agent.md",
    ]

    sparky.process_batch(test_issues)
