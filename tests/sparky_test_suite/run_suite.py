#!/usr/bin/env python3
"""
SPARKY Test Suite Runner
Executes standardized test issues to validate SPARKY performance across complexity levels
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
from agents.sparky_6_async import AsyncSparky


class SPARKYTestSuite:
    """Comprehensive test suite for SPARKY validation"""

    def __init__(self):
        self.sparky = AsyncSparky()
        self.suite_dir = Path(__file__).parent
        self.results = {
            "level_1_basic": [],
            "level_2_intermediate": [],
            "level_3_advanced": [],
            "level_4_integration": [],
        }
        self.start_time = time.time()

    def reset_test_environment(self):
        """Reset all fixtures to clean state"""
        print("🔄 Preparing test environment...")

        # Ensure fixture files exist
        fixtures_dir = self.suite_dir / "fixtures"
        if not fixtures_dir.exists():
            fixtures_dir.mkdir(parents=True, exist_ok=True)

        # Create fixture files if they don't exist
        self._ensure_fixture_files()

        # Clean any generated test files (but not the fixtures themselves)
        generated_dirs = [
            self.suite_dir / "fixtures" / "cache",
            self.suite_dir / "fixtures" / "logs",
        ]

        for gen_dir in generated_dirs:
            if gen_dir.exists():
                import shutil

                shutil.rmtree(gen_dir)

        print("  ✅ Test environment ready")

    def _ensure_fixture_files(self):
        """Ensure fixture files exist for testing"""
        fixtures_dir = self.suite_dir / "fixtures"

        # Create simple_function.py if missing
        simple_func = fixtures_dir / "simple_function.py"
        if not simple_func.exists():
            simple_func.write_text(
                '''#!/usr/bin/env python3
"""
Simple function for SPARKY testing
"""

def process_input(data):
    # Line 5 - target for comment insertion
    result = data.upper()
    return result

def helper_function():
    return "helper"'''
            )

        # Create data_processor.py if missing
        data_proc = fixtures_dir / "data_processor.py"
        if not data_proc.exists():
            data_proc.write_text(
                '''#!/usr/bin/env python3
"""
Data processor for SPARKY testing
Target for refactoring and error handling tests
"""

def process_data(input_data):
    """Process the input data"""
    cleaned = input_data.strip()
    transformed = cleaned.upper()
    return transformed

def validate_data(data):
    """Validate input data"""
    if not data:
        return False
    return True'''
            )

        # Create main_app.py if missing
        main_app = fixtures_dir / "main_app.py"
        if not main_app.exists():
            main_app.write_text(
                '''#!/usr/bin/env python3
"""
Main application using data processor
Target for refactoring tests - contains function calls to update
"""

from data_processor import process_data

def main():
    """Main application entry point"""
    user_input = "hello world"
    
    # First call site - should be updated in refactoring test
    result1 = process_data(user_input)
    print(f"Result 1: {result1}")
    
    # Second call site - should be updated in refactoring test  
    result2 = process_data("test data")
    print(f"Result 2: {result2}")
    
    return result1, result2

if __name__ == "__main__":
    main()'''
            )

    def discover_test_issues(self) -> Dict[str, List[Path]]:
        """Discover all test issues organized by complexity level"""
        issues = {}

        for level_dir in self.suite_dir.glob("issues/level_*"):
            level_name = level_dir.name
            issues[level_name] = sorted(level_dir.glob("*.md"))

        return issues

    def run_single_test(self, issue_path: Path) -> Dict[str, Any]:
        """Run a single test issue and measure results"""
        print(f"\n🧪 Testing: {issue_path.name}")

        start = time.time()

        try:
            # Execute the issue with SPARKY
            async def run_test():
                context = await self.sparky.launch(issue_path)
                return {
                    "success": context.state == "completed",
                    "actions_executed": len(context.metadata.get("actions", [])),
                    "total_changes": context.metadata.get("changes", 0),
                    "error": context.error,
                }

            result = asyncio.run(run_test())

            duration = time.time() - start

            test_result = {
                "issue": issue_path.name,
                "success": result["success"],
                "duration": duration,
                "actions": result.get("actions_executed", 0),
                "changes": result.get("total_changes", 0),
                "error": result.get("error") if not result["success"] else None,
            }

            if result["success"]:
                print(
                    f"  ✅ Success: {result['actions_executed']} actions, {result['total_changes']} changes ({duration:.2f}s)"
                )
            else:
                print(
                    f"  ❌ Failed: {result.get('error', 'Unknown error')} ({duration:.2f}s)"
                )

            return test_result

        except Exception as e:
            duration = time.time() - start
            print(f"  💥 Exception: {str(e)} ({duration:.2f}s)")

            return {
                "issue": issue_path.name,
                "success": False,
                "duration": duration,
                "actions": 0,
                "changes": 0,
                "error": f"Exception: {str(e)}",
            }

    def run_level(self, level_name: str, issues: List[Path]) -> Dict[str, Any]:
        """Run all tests in a complexity level"""
        print(f"\n{'='*60}")
        print(f"🎯 LEVEL: {level_name.upper()}")
        print(f"{'='*60}")

        level_results = []

        for issue_path in issues:
            result = self.run_single_test(issue_path)
            level_results.append(result)
            self.results[level_name].append(result)

        # Level summary
        successful = sum(1 for r in level_results if r["success"])
        total_actions = sum(r["actions"] for r in level_results)
        total_time = sum(r["duration"] for r in level_results)

        print(f"\n📊 {level_name} Summary:")
        print(
            f"  Success Rate: {successful}/{len(level_results)} ({successful/len(level_results)*100:.1f}%)"
        )
        print(f"  Total Actions: {total_actions}")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Avg Time/Test: {total_time/len(level_results):.2f}s")

        return {
            "level": level_name,
            "tests": len(level_results),
            "successful": successful,
            "total_actions": total_actions,
            "total_time": total_time,
            "results": level_results,
        }

    def generate_report(self, level_summaries: List[Dict]) -> str:
        """Generate comprehensive test report"""
        total_time = time.time() - self.start_time

        report = f"""
{'='*80}
🚀 SPARKY TEST SUITE REPORT
{'='*80}

Total Execution Time: {total_time:.2f}s
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}

LEVEL SUMMARIES:
"""

        total_tests = 0
        total_successful = 0
        total_actions = 0

        for summary in level_summaries:
            total_tests += summary["tests"]
            total_successful += summary["successful"]
            total_actions += summary["total_actions"]

            success_rate = summary["successful"] / summary["tests"] * 100

            report += f"""
{summary['level'].upper()}:
  Tests: {summary['tests']}
  Success: {summary['successful']} ({success_rate:.1f}%)
  Actions: {summary['total_actions']}
  Time: {summary['total_time']:.2f}s
"""

        overall_success = total_successful / total_tests * 100

        report += f"""
OVERALL RESULTS:
  Total Tests: {total_tests}
  Overall Success Rate: {total_successful}/{total_tests} ({overall_success:.1f}%)
  Total Actions Executed: {total_actions}
  Actions/Minute: {total_actions / (total_time / 60):.1f}

PERFORMANCE BENCHMARKS:
  Level 1 (Basic): {level_summaries[0]['total_time']/level_summaries[0]['tests']:.2f}s avg
  Level 2 (Intermediate): {level_summaries[1]['total_time']/level_summaries[1]['tests']:.2f}s avg
  Level 3 (Advanced): {level_summaries[2]['total_time']/level_summaries[2]['tests']:.2f}s avg
  Level 4 (Integration): {level_summaries[3]['total_time']/level_summaries[3]['tests']:.2f}s avg

{'='*80}
"""

        return report

    def run_full_suite(self):
        """Execute complete test suite"""
        print("🚀 SPARKY COMPREHENSIVE TEST SUITE")
        print("Testing AsyncSparky (Factor 6 Launch/Pause/Resume Implementation)")
        print("=" * 80)

        # Reset environment
        self.reset_test_environment()

        # Discover tests
        test_issues = self.discover_test_issues()
        total_issues = sum(len(issues) for issues in test_issues.values())
        print(
            f"📋 Discovered {total_issues} test issues across {len(test_issues)} complexity levels"
        )

        # Run each level
        level_summaries = []
        for level_name, issues in test_issues.items():
            if issues:  # Only run if issues exist
                summary = self.run_level(level_name, issues)
                level_summaries.append(summary)

        # Generate and display report
        report = self.generate_report(level_summaries)
        print(report)

        # Save report
        report_path = self.suite_dir / f"test_report_{int(time.time())}.txt"
        report_path.write_text(report)
        print(f"📄 Report saved: {report_path}")

        return level_summaries


def main():
    """Run SPARKY test suite"""
    suite = SPARKYTestSuite()
    results = suite.run_full_suite()

    # Exit with appropriate code
    overall_success = all(
        summary["successful"] == summary["tests"] for summary in results
    )

    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()
