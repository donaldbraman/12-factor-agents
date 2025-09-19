#!/usr/bin/env python3
"""
SPARKY Test Suite Runner - Async Edition
Tests SPARKY 6.0 with standardized issues
"""

import asyncio
import json
import time
from pathlib import Path
import subprocess
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.sparky_6_async import AsyncSparky


class AsyncTestRunner:
    """Run test suite with async SPARKY"""

    def __init__(self):
        self.sparky = AsyncSparky()
        self.results = []
        self.issues_dir = Path(__file__).parent / "issues"

    async def run_test(self, issue_file: Path, level: str) -> dict:
        """Run a single test with async handling"""
        print(f"\n{'='*60}")
        print(f"Testing: {issue_file.name} (Level {level})")
        print("=" * 60)

        start_time = time.time()

        try:
            # Launch the agent
            context = await self.sparky.launch(issue_file)

            # Handle different states
            while context.current_state.name in [
                "PAUSED",
                "WAITING_FOR_TESTS",
                "WAITING_FOR_APPROVAL",
            ]:
                if context.current_state.name == "WAITING_FOR_TESTS":
                    # Simulate test results
                    print("📊 Simulating test results...")
                    await asyncio.sleep(0.5)  # Simulate test delay

                    test_results = {
                        "test_results": {
                            "passed": 10,
                            "failed": 0,
                            "skipped": 0,
                            "duration_seconds": 12.5,
                            "coverage_percent": 92.0,
                        }
                    }

                    context = await self.sparky.resume(context.agent_id, test_results)

                elif context.current_state.name == "WAITING_FOR_APPROVAL":
                    # Auto-approve for testing
                    print("✅ Auto-approving for test suite...")
                    context = await self.sparky.resume(
                        context.agent_id, {"approved": True}
                    )

                else:
                    # Generic resume
                    context = await self.sparky.resume(context.agent_id)

            elapsed = time.time() - start_time

            result = {
                "test": issue_file.name,
                "level": level,
                "status": "PASSED"
                if context.current_state.name == "COMPLETED"
                else "FAILED",
                "agent_id": context.agent_id,
                "actions_completed": len(context.actions_completed),
                "time_seconds": round(elapsed, 2),
                "insights": len(context.learning_insights),
            }

            print(f"\n✅ Test completed in {elapsed:.2f}s")
            print(f"   Actions: {len(context.actions_completed)}")
            print(f"   Insights: {len(context.learning_insights)}")

        except Exception as e:
            result = {
                "test": issue_file.name,
                "level": level,
                "status": "ERROR",
                "error": str(e),
                "time_seconds": round(time.time() - start_time, 2),
            }
            print(f"❌ Error: {e}")

        return result

    async def run_suite(self):
        """Run the complete test suite"""
        print("\n" + "=" * 60)
        print(" SPARKY 6.0 ASYNC TEST SUITE")
        print("=" * 60)

        # Reset fixtures first
        print("\n🔄 Resetting test fixtures...")
        subprocess.run(
            ["python", "reset_suite.py"], cwd=Path(__file__).parent, check=True
        )

        # Test levels
        test_levels = [
            ("level_1_basic", "1"),
            ("level_2_intermediate", "2"),
            ("level_3_advanced", "3"),
            ("level_4_integration", "4"),
        ]

        total_start = time.time()

        for level_dir, level_num in test_levels:
            level_path = self.issues_dir / level_dir

            if not level_path.exists():
                print(f"⚠️  Skipping {level_dir} - directory not found")
                continue

            for issue_file in sorted(level_path.glob("*.md")):
                result = await self.run_test(issue_file, level_num)
                self.results.append(result)

                # Reset fixtures between tests
                print("\n♻️  Resetting fixtures...")
                subprocess.run(
                    ["python", "reset_suite.py"],
                    cwd=Path(__file__).parent,
                    capture_output=True,
                    check=True,
                )

        # Summary
        total_time = time.time() - total_start
        self.print_summary(total_time)
        self.save_results()

    def print_summary(self, total_time: float):
        """Print test summary"""
        print("\n" + "=" * 60)
        print(" TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.results if r["status"] == "PASSED")
        failed = sum(1 for r in self.results if r["status"] == "FAILED")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")

        print("\n📊 Results:")
        print(f"   Total: {len(self.results)} tests")
        print(f"   Passed: {passed} ✅")
        print(f"   Failed: {failed} ❌")
        print(f"   Errors: {errors} 🔥")
        print(f"   Time: {total_time:.2f}s")

        if self.results:
            avg_time = sum(r["time_seconds"] for r in self.results) / len(self.results)
            print(f"   Avg time: {avg_time:.2f}s per test")

        # Details by level
        for level in ["1", "2", "3", "4"]:
            level_results = [r for r in self.results if r.get("level") == level]
            if level_results:
                level_passed = sum(1 for r in level_results if r["status"] == "PASSED")
                print(f"\n   Level {level}: {level_passed}/{len(level_results)} passed")
                for r in level_results:
                    status_icon = "✅" if r["status"] == "PASSED" else "❌"
                    print(
                        f"      {status_icon} {r['test']}: {r.get('actions_completed', 0)} actions, {r['time_seconds']}s"
                    )

        # Learning insights
        total_insights = sum(r.get("insights", 0) for r in self.results)
        if total_insights > 0:
            print(f"\n🧠 Learning Insights Generated: {total_insights}")

        # Success rate
        if self.results:
            success_rate = (passed / len(self.results)) * 100
            print(f"\n🎯 Success Rate: {success_rate:.1f}%")

    def save_results(self):
        """Save results to file"""
        timestamp = int(time.time())
        results_file = Path(__file__).parent / f"test_results_async_{timestamp}.json"

        with open(results_file, "w") as f:
            json.dump(
                {
                    "sparky_version": "6.0-async",
                    "timestamp": timestamp,
                    "results": self.results,
                },
                f,
                indent=2,
            )

        print(f"\n💾 Results saved to: {results_file.name}")


async def main():
    """Run the async test suite"""
    runner = AsyncTestRunner()
    await runner.run_suite()


if __name__ == "__main__":
    asyncio.run(main())
