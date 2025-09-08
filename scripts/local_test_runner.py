#!/usr/bin/env python3
"""Local test runner for hobbyist development"""
import subprocess
import sys


def run_quick_tests():
    """Run quick validation tests"""
    print("🧪 Running quick validation tests...")
    result = subprocess.run(
        ["uv", "run", "-m", "pytest", "tests/test_quick_validation.py", "-v"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ Quick tests passed!")
        return True
    else:
        print("❌ Quick tests failed:")
        print(result.stdout)
        print(result.stderr)
        return False


def run_performance_tests():
    """Run performance benchmark suite"""
    print("\n📊 Running performance tests...")
    result = subprocess.run(
        ["uv", "run", "scripts/run_performance_tests.py"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ Performance tests passed!")
        return True
    else:
        print("❌ Performance tests failed:")
        print(result.stdout)
        print(result.stderr)
        return False


def run_code_quality():
    """Run code quality checks"""
    print("\n🎨 Running code quality checks...")

    # Black formatting
    black_result = subprocess.run(
        ["uv", "run", "black", "--check", "."], capture_output=True, text=True
    )

    # Ruff linting
    ruff_result = subprocess.run(
        ["uv", "run", "ruff", "check", "."], capture_output=True, text=True
    )

    if black_result.returncode == 0 and ruff_result.returncode == 0:
        print("✅ Code quality checks passed!")
        return True
    else:
        if black_result.returncode != 0:
            print("❌ Black formatting issues:")
            print(black_result.stdout)
        if ruff_result.returncode != 0:
            print("❌ Ruff linting issues:")
            print(ruff_result.stdout)
        return False


def main():
    """Run full local test suite"""
    print("🚀 Local CI/CD Quality Gates - Running Full Suite\n")

    checks = [
        ("Quick Tests", run_quick_tests),
        ("Performance Tests", run_performance_tests),
        ("Code Quality", run_code_quality),
    ]

    failed = 0
    for name, check in checks:
        if not check():
            failed += 1

    print(f"\n{'='*50}")
    if failed == 0:
        print("🎉 All quality gates passed! Code is ready.")
        sys.exit(0)
    else:
        print(f"❌ {failed}/{len(checks)} quality gates failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
