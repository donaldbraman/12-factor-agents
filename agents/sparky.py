"""
SPARKY - Systematic Programmatic Agentic issue Resolver for KrazY-fast production

The ultimate lean issue processing system that combines:
- Lean agent architecture (81% less code!)
- Prompt-driven intelligence
- KrazY-fast execution
- Zero bloat philosophy
"""

from pathlib import Path
from typing import Dict, List
from agents.issue_router import IssueRouter
import time


class SPARKY:
    """The leanest, meanest issue processing machine"""

    def __init__(self):
        self.router = IssueRouter()
        self.processed = []
        self.start_time = time.time()

    def process_batch(self, issue_paths: List[str]) -> Dict:
        """Process multiple issues KrazY-fast"""
        results = {"success": [], "failed": [], "total_time": 0}

        print("⚡ SPARKY ACTIVATED - Processing issues KrazY-fast! ⚡")
        print("=" * 50)

        for issue_path in issue_paths:
            print(f"\n🎯 Processing: {issue_path}")
            try:
                result = self.router.process_issue(issue_path)
                if result.success:
                    results["success"].append(issue_path)
                    print("  ✅ Success!")
                else:
                    results["failed"].append(issue_path)
                    print(f"  ❌ Failed: {result.error}")
            except Exception as e:
                results["failed"].append(issue_path)
                print(f"  ❌ Error: {str(e)}")

        results["total_time"] = time.time() - self.start_time

        print("\n" + "=" * 50)
        print("⚡ SPARKY RESULTS ⚡")
        print(f"✅ Successful: {len(results['success'])}")
        print(f"❌ Failed: {len(results['failed'])}")
        print(f"⏱️  Time: {results['total_time']:.2f}s")
        print("🚀 Speed: KrazY-fast!")

        return results

    def find_issues(self, directory: str = "issues") -> List[str]:
        """Find all issues to process"""
        issue_dir = Path(directory)
        if not issue_dir.exists():
            return []

        issues = []
        for file in issue_dir.glob("*.md"):
            if not file.name.startswith("."):
                issues.append(str(file))

        return sorted(issues)

    def run(self, auto_find: bool = True):
        """Main SPARKY execution"""
        if auto_find:
            issues = self.find_issues()
            if issues:
                print(f"🔍 Found {len(issues)} issues to process")
                return self.process_batch(issues)
            else:
                print("❌ No issues found in issues/ directory")
                return {"success": [], "failed": [], "total_time": 0}


# Example usage
if __name__ == "__main__":
    sparky = SPARKY()
    sparky.run()

# 88 lines of pure SPARKY power!
