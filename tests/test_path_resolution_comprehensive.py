#!/usr/bin/env uv run python
"""
Comprehensive test suite for path resolution issues reported by pin-citer team.
Tests all scenarios mentioned in their feedback.
"""

import subprocess
from pathlib import Path


def test_path_resolution_scenarios():
    """Test all the path resolution scenarios from pin-citer feedback"""

    # Get the project root (where this script's parent's parent is)
    project_root = Path(__file__).parent.parent.absolute()

    print(f"🧪 Testing path resolution from project root: {project_root}")

    # Test scenarios from the feedback
    test_cases = [
        {
            "name": "From project root with wrapper script",
            "command": ["./bin/agent", "run", "SmartIssueAgent", "129"],
            "cwd": project_root,
            "expected_success": True,
        },
        {
            "name": "From project root with direct uv",
            "command": [
                "uv",
                "run",
                "python",
                "bin/agent.py",
                "run",
                "SmartIssueAgent",
                "129",
            ],
            "cwd": project_root,
            "expected_success": True,
        },
        {
            "name": "From .agents directory",
            "command": [
                "uv",
                "run",
                "python",
                "bin/agent.py",
                "run",
                "SmartIssueAgent",
                "129",
            ],
            "cwd": project_root / ".agents",
            "expected_success": True,
        },
        {
            "name": "With uv --directory from project root",
            "command": [
                "uv",
                "run",
                "--directory",
                ".agents",
                "python",
                "bin/agent.py",
                "run",
                "SmartIssueAgent",
                "129",
            ],
            "cwd": project_root,
            "expected_success": True,
        },
    ]

    results = []

    for test_case in test_cases:
        print(f"\n📋 Test: {test_case['name']}")
        print(f"   Command: {' '.join(str(c) for c in test_case['command'])}")
        print(f"   Working Dir: {test_case['cwd']}")

        if not test_case["cwd"].exists():
            print("   ❌ SKIP: Directory doesn't exist")
            results.append(
                {
                    "test": test_case["name"],
                    "status": "SKIP",
                    "reason": "Directory missing",
                }
            )
            continue

        try:
            # Run the command with timeout
            result = subprocess.run(
                test_case["command"],
                cwd=test_case["cwd"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Check for success indicators
            success_indicators = [
                "✅ Task completed successfully",
                "🎯 Complex issue orchestrated",
                "Successfully processed",
                "Issue decomposition complete",
            ]

            # Check for failure indicators
            failure_indicators = [
                "No issue file found",
                "'IssueFixerAgent' object has no attribute '_intelligent_processing'",
                "SmartIssueAgent failed:",
                "Could not determine how to fix",
            ]

            output = result.stdout + result.stderr
            has_success = any(indicator in output for indicator in success_indicators)
            has_failure = any(indicator in output for indicator in failure_indicators)

            if has_success and not has_failure:
                print("   ✅ SUCCESS")
                results.append({"test": test_case["name"], "status": "PASS"})
            elif has_failure:
                print("   ❌ FAILED")
                for indicator in failure_indicators:
                    if indicator in output:
                        print(f"      Error: {indicator}")
                results.append(
                    {
                        "test": test_case["name"],
                        "status": "FAIL",
                        "error": output[-500:],
                    }
                )
            else:
                print("   ⚠️  UNCLEAR")
                print(f"      Return code: {result.returncode}")
                print(f"      Output length: {len(output)}")
                results.append(
                    {
                        "test": test_case["name"],
                        "status": "UNCLEAR",
                        "output": output[-200:],
                    }
                )

        except subprocess.TimeoutExpired:
            print("   ⏰ TIMEOUT")
            results.append({"test": test_case["name"], "status": "TIMEOUT"})
        except Exception as e:
            print(f"   💥 ERROR: {str(e)}")
            results.append(
                {"test": test_case["name"], "status": "ERROR", "exception": str(e)}
            )

    # Summary
    print(f"\n{'='*60}")
    print("🎯 TEST SUMMARY")
    print(f"{'='*60}")

    passed = len([r for r in results if r.get("status") == "PASS"])
    failed = len([r for r in results if r.get("status") == "FAIL"])
    total = len(results)

    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {failed}/{total}")

    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for result in results:
            if result.get("status") == "FAIL":
                print(f"   - {result['test']}")
                if "error" in result:
                    print(f"     Error snippet: {result['error'][-100:]}")

    return results


def check_missing_methods():
    """Check if all agent classes have the required intelligent processing methods"""
    print("\n🔍 CHECKING FOR MISSING METHODS")
    print("=" * 60)

    agents_dir = Path(__file__).parent.parent / "agents"
    agent_files = list(agents_dir.glob("*_agent.py"))

    results = []

    for agent_file in agent_files:
        if agent_file.name.startswith("base"):
            continue

        content = agent_file.read_text()

        has_intelligent = "_intelligent_processing" in content
        has_fallback = "Could not determine how to fix" in content

        status = (
            "✅ HAS INTELLIGENT"
            if has_intelligent
            else ("⚠️ HAS FALLBACK" if has_fallback else "❌ MISSING BOTH")
        )

        print(f"   {status}: {agent_file.name}")

        results.append(
            {
                "file": agent_file.name,
                "has_intelligent": has_intelligent,
                "has_fallback": has_fallback,
            }
        )

    missing_intelligent = [r for r in results if not r["has_intelligent"]]
    if missing_intelligent:
        print("\n⚠️ AGENTS MISSING _intelligent_processing:")
        for agent in missing_intelligent:
            print(f"   - {agent['file']}")

    return results


def check_sub_issue_creation():
    """Test that sub-issues actually get created as files"""
    print("\n📁 CHECKING SUB-ISSUE FILE CREATION")
    print("=" * 60)

    project_root = Path(__file__).parent.parent.absolute()
    issues_dir = project_root / "issues"

    # Count existing issues
    before_count = len(list(issues_dir.glob("*.md")))
    print(f"📊 Issues before test: {before_count}")

    # Create a simple test issue that should decompose
    test_issue_num = "999"
    test_issue_path = issues_dir / f"{test_issue_num}-decomposition-test.md"

    test_issue_content = """# Issue #999: Test Sub-Issue Creation

## Description
Create a comprehensive authentication system with multiple components.

This is a complex issue that should decompose into planning, implementation, and validation phases.

**Requirements**:
1. User authentication with bcrypt
2. OAuth integration  
3. Session management
4. Database schema design
5. API endpoint creation
6. Comprehensive testing

## Type
feature

## Priority
high

## Status
open

## Assignee
smart_issue_agent
"""

    try:
        # Create test issue
        test_issue_path.write_text(test_issue_content)
        print(f"✅ Created test issue: {test_issue_path}")

        # Run the agent
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "bin/agent.py",
                "run",
                "SmartIssueAgent",
                test_issue_num,
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Count issues after
        after_count = len(list(issues_dir.glob("*.md")))
        created_count = after_count - before_count - 1  # -1 for the test issue itself

        print(f"📊 Issues after test: {after_count}")
        print(f"📊 New issues created: {created_count}")

        # Check if decomposition happened
        output = result.stdout + result.stderr

        if "Issue decomposition complete" in output and created_count > 0:
            print(f"✅ SUCCESS: Decomposition created {created_count} sub-issues")

            # List the new issues
            new_issues = sorted(
                [
                    f
                    for f in issues_dir.glob("*.md")
                    if f.name.startswith(("220-", "221-", "222-"))
                ]
            )
            for issue in new_issues:
                print(f"   📋 Created: {issue.name}")

        elif "Issue decomposition complete" in output and created_count == 0:
            print("❌ BUG CONFIRMED: Claims decomposition but no files created")
        else:
            print("⚠️ No decomposition detected")

    finally:
        # Cleanup
        if test_issue_path.exists():
            test_issue_path.unlink()
            print("🧹 Cleaned up test issue")

        # Clean up any created sub-issues
        cleanup_patterns = ["220-", "221-", "222-", "999-"]
        for pattern in cleanup_patterns:
            for issue_file in issues_dir.glob(f"{pattern}*.md"):
                issue_file.unlink()
                print(f"🧹 Cleaned up: {issue_file.name}")


if __name__ == "__main__":
    print("🧪 COMPREHENSIVE PATH RESOLUTION TEST SUITE")
    print("Testing pin-citer team feedback scenarios")
    print("=" * 80)

    # Run all tests
    path_results = test_path_resolution_scenarios()
    method_results = check_missing_methods()
    check_sub_issue_creation()

    print("\n🎯 OVERALL ASSESSMENT")
    print("=" * 60)

    failed_tests = len([r for r in path_results if r.get("status") == "FAIL"])
    missing_methods = len([r for r in method_results if not r["has_intelligent"]])

    if failed_tests == 0 and missing_methods == 0:
        print("✅ ALL TESTS PASSED - No issues found")
    else:
        print("❌ ISSUES FOUND:")
        if failed_tests > 0:
            print(f"   - {failed_tests} path resolution tests failed")
        if missing_methods > 0:
            print(f"   - {missing_methods} agents missing intelligent processing")
