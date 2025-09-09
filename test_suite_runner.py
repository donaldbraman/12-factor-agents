#!/usr/bin/env uv run python
"""
Comprehensive Test Suite Runner for SmartIssueAgent
Tests 10 issues across the complexity spectrum to assess functionality.
"""

import sys
import time
import json
from pathlib import Path
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.smart_issue_agent import SmartIssueAgent


@dataclass
class TestResult:
    """Result from testing a single issue"""

    issue_number: str
    expected_complexity: str
    actual_complexity: str
    strategy_used: str
    success: bool
    execution_time: float
    sub_issues_created: int
    error_message: str = ""


def run_test_suite():
    """Run comprehensive test suite on 10 issues"""

    # Test issues in complexity order (high to low)
    test_issues = [
        {
            "number": "080",
            "expected": "enterprise",
            "description": "Complete AI system migration",
        },
        {
            "number": "081",
            "expected": "complex",
            "description": "Multi-agent coordination system",
        },
        {"number": "082", "expected": "complex", "description": "Pipeline integration"},
        {
            "number": "083",
            "expected": "moderate",
            "description": "Testing framework enhancement",
        },
        {"number": "084", "expected": "moderate", "description": "CLI enhancements"},
        {"number": "085", "expected": "simple", "description": "Logging improvement"},
        {"number": "086", "expected": "simple", "description": "README update"},
        {"number": "087", "expected": "simple", "description": "Version bump"},
        {"number": "088", "expected": "atomic", "description": "Typo fix"},
        {"number": "089", "expected": "atomic", "description": "Comment addition"},
    ]

    print("🧪 SmartIssueAgent Comprehensive Test Suite")
    print("=" * 60)
    print(f"Testing {len(test_issues)} issues across complexity spectrum")
    print()

    agent = SmartIssueAgent()
    results = []

    for i, test_case in enumerate(test_issues, 1):
        issue_num = test_case["number"]
        expected = test_case["expected"]
        description = test_case["description"]

        print(f"🔍 Test {i}/10: Issue #{issue_num} ({expected}) - {description}")

        start_time = time.time()

        try:
            result = agent.execute_task(issue_num)
            execution_time = time.time() - start_time

            if result.success:
                strategy = result.data.get("strategy", "unknown")
                complexity_data = result.data.get("complexity", {})
                actual_complexity = complexity_data.get("complexity", "unknown")

                # Count sub-issues if decomposed
                sub_issues = 0
                if strategy == "decomposition_and_orchestration":
                    sub_issues = result.data.get("total_sub_issues", 0)

                test_result = TestResult(
                    issue_number=issue_num,
                    expected_complexity=expected,
                    actual_complexity=actual_complexity,
                    strategy_used=strategy,
                    success=True,
                    execution_time=execution_time,
                    sub_issues_created=sub_issues,
                )

                # Determine if complexity detection was accurate
                complexity_match = actual_complexity == expected
                status = "✅" if complexity_match else "⚠️"

                print(
                    f"   {status} Detected: {actual_complexity} | Strategy: {strategy}"
                )
                if sub_issues > 0:
                    print(f"   🧩 Decomposed into {sub_issues} sub-issues")
                print(f"   ⏱️  Execution time: {execution_time:.2f}s")

            else:
                test_result = TestResult(
                    issue_number=issue_num,
                    expected_complexity=expected,
                    actual_complexity="unknown",
                    strategy_used="failed",
                    success=False,
                    execution_time=execution_time,
                    sub_issues_created=0,
                    error_message=result.error or "Unknown error",
                )

                print(f"   ❌ Failed: {result.error}")

        except Exception as e:
            execution_time = time.time() - start_time
            test_result = TestResult(
                issue_number=issue_num,
                expected_complexity=expected,
                actual_complexity="error",
                strategy_used="exception",
                success=False,
                execution_time=execution_time,
                sub_issues_created=0,
                error_message=str(e),
            )

            print(f"   💥 Exception: {str(e)}")

        results.append(test_result)
        print()

    # Generate comprehensive report
    print("📊 TEST SUITE RESULTS")
    print("=" * 60)

    # Overall statistics
    total_tests = len(results)
    successful_tests = len([r for r in results if r.success])
    total_time = sum(r.execution_time for r in results)

    print(
        f"Overall Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)"
    )
    print(f"Total Execution Time: {total_time:.2f}s")
    print(f"Average Time per Issue: {total_time/total_tests:.2f}s")
    print()

    # Complexity detection accuracy
    print("🎯 Complexity Detection Accuracy:")
    complexity_matches = 0
    for result in results:
        if result.success:
            match = result.actual_complexity == result.expected_complexity
            if match:
                complexity_matches += 1
            status = "✅" if match else "❌"
            print(
                f"   {status} #{result.issue_number}: Expected {result.expected_complexity}, Got {result.actual_complexity}"
            )
        else:
            print(f"   ⚠️  #{result.issue_number}: Failed to analyze")

    print(
        f"\nComplexity Accuracy: {complexity_matches}/{successful_tests} ({complexity_matches/max(successful_tests,1)*100:.1f}%)"
    )
    print()

    # Strategy distribution
    print("🔄 Strategy Distribution:")
    strategy_counts = {}
    for result in results:
        strategy = result.strategy_used
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

    for strategy, count in strategy_counts.items():
        print(f"   {strategy}: {count} issues")
    print()

    # Decomposition statistics
    total_sub_issues = sum(r.sub_issues_created for r in results)
    decomposed_issues = len([r for r in results if r.sub_issues_created > 0])

    print("🧩 Decomposition Statistics:")
    print(f"   Issues decomposed: {decomposed_issues}/{total_tests}")
    print(f"   Total sub-issues created: {total_sub_issues}")
    if decomposed_issues > 0:
        print(
            f"   Average sub-issues per decomposed issue: {total_sub_issues/decomposed_issues:.1f}"
        )
    print()

    # Performance analysis
    print("⚡ Performance Analysis:")
    if results:
        fastest = min(results, key=lambda r: r.execution_time)
        slowest = max(results, key=lambda r: r.execution_time)
        print(f"   Fastest: #{fastest.issue_number} ({fastest.execution_time:.2f}s)")
        print(f"   Slowest: #{slowest.issue_number} ({slowest.execution_time:.2f}s)")

        # Performance by complexity
        perf_by_complexity = {}
        for result in results:
            if result.success:
                complexity = result.actual_complexity
                if complexity not in perf_by_complexity:
                    perf_by_complexity[complexity] = []
                perf_by_complexity[complexity].append(result.execution_time)

        print("   Average time by complexity:")
        for complexity, times in perf_by_complexity.items():
            avg_time = sum(times) / len(times)
            print(f"     {complexity}: {avg_time:.2f}s")
    print()

    # Failure analysis
    failures = [r for r in results if not r.success]
    if failures:
        print("❌ Failure Analysis:")
        for failure in failures:
            print(
                f"   #{failure.issue_number} ({failure.expected_complexity}): {failure.error_message}"
            )
        print()

    # Save detailed results
    results_file = Path("test_suite_results.json")
    results_data = {
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests * 100,
            "total_execution_time": total_time,
            "complexity_accuracy": complexity_matches / max(successful_tests, 1) * 100,
            "total_sub_issues_created": total_sub_issues,
        },
        "detailed_results": [
            {
                "issue_number": r.issue_number,
                "expected_complexity": r.expected_complexity,
                "actual_complexity": r.actual_complexity,
                "strategy_used": r.strategy_used,
                "success": r.success,
                "execution_time": r.execution_time,
                "sub_issues_created": r.sub_issues_created,
                "error_message": r.error_message,
            }
            for r in results
        ],
    }

    results_file.write_text(json.dumps(results_data, indent=2))
    print(f"📄 Detailed results saved to: {results_file}")

    # Overall assessment
    print("\n🏆 OVERALL ASSESSMENT:")
    if successful_tests >= 8:
        print("   ✅ EXCELLENT: SmartIssueAgent is highly functional")
    elif successful_tests >= 6:
        print("   👍 GOOD: SmartIssueAgent is mostly functional with minor issues")
    elif successful_tests >= 4:
        print("   ⚠️  FAIR: SmartIssueAgent works but needs improvement")
    else:
        print("   ❌ POOR: SmartIssueAgent needs significant work")

    print(
        f"\nSmartIssueAgent processed {successful_tests}/{total_tests} issues successfully"
    )
    print(
        f"Complexity detection accuracy: {complexity_matches/max(successful_tests,1)*100:.1f}%"
    )
    print(f"Created {total_sub_issues} sub-issues through intelligent decomposition")

    return results


if __name__ == "__main__":
    run_test_suite()
