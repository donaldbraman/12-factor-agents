#!/usr/bin/env python3
"""
Simple Testing - Lightweight testing framework using Python's built-in capabilities

Instead of complex test frameworks that hang or timeout, we use Python's built-in
unittest and simple assertion patterns that work reliably.

This addresses Issue #153: Critical Pytest Suite Failing
"""

import unittest
import sys
from pathlib import Path
from typing import Callable, List, Dict
import traceback
import time
from dataclasses import dataclass


@dataclass
class TestResult:
    """Simple test result structure"""

    name: str
    passed: bool
    duration: float
    error_message: str = ""
    traceback_info: str = ""


class SimpleTestRunner:
    """
    Lightweight test runner that focuses on reliability over features.

    Key principles:
    - Use Python's built-in unittest
    - Simple assertions over complex matchers
    - Fast execution with timeouts
    - Clear reporting
    """

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self.results: List[TestResult] = []

    def run_test_file(self, test_file: Path) -> List[TestResult]:
        """Run all tests in a file with timeout protection"""

        print(f"🧪 Running tests in {test_file}")

        # Import and discover tests
        try:
            # Add to sys.path temporarily
            sys.path.insert(0, str(test_file.parent))

            # Import the test module
            module_name = test_file.stem
            import importlib.util

            spec = importlib.util.spec_from_file_location(module_name, test_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Discover test classes and methods
            test_methods = self._discover_test_methods(module)

            print(f"   Found {len(test_methods)} test methods")

            # Run each test with timeout
            for test_class, test_method in test_methods:
                result = self._run_single_test(test_class, test_method)
                self.results.append(result)

        except Exception as e:
            error_result = TestResult(
                name=f"{test_file}::import_error",
                passed=False,
                duration=0.0,
                error_message=str(e),
                traceback_info=traceback.format_exc(),
            )
            self.results.append(error_result)

        finally:
            # Clean up sys.path
            sys.path.pop(0)

        return self.results

    def _discover_test_methods(self, module) -> List[tuple]:
        """Discover test methods in a module"""
        test_methods = []

        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            # Look for test classes (subclass of unittest.TestCase)
            if (
                isinstance(attr, type)
                and issubclass(attr, unittest.TestCase)
                and attr != unittest.TestCase
            ):
                # Look for test methods in the class
                for method_name in dir(attr):
                    if method_name.startswith("test_"):
                        test_methods.append((attr, method_name))

        return test_methods

    def _run_single_test(self, test_class, method_name: str) -> TestResult:
        """Run a single test method with timeout"""

        test_name = f"{test_class.__name__}::{method_name}"
        start_time = time.time()

        try:
            # Create test instance
            test_instance = test_class()

            # Set up the test
            if hasattr(test_instance, "setUp"):
                test_instance.setUp()

            # Run the actual test method
            test_method = getattr(test_instance, method_name)

            # Simple timeout mechanism
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(
                    f"Test {test_name} timed out after {self.timeout_seconds}s"
                )

            # Set timeout (Unix only, but better than hanging)
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout_seconds)

                # Run the test
                test_method()

                # Clear timeout
                signal.alarm(0)

            except AttributeError:
                # Windows doesn't have SIGALRM, just run without timeout
                test_method()

            # Tear down the test
            if hasattr(test_instance, "tearDown"):
                test_instance.tearDown()

            duration = time.time() - start_time

            return TestResult(name=test_name, passed=True, duration=duration)

        except Exception as e:
            duration = time.time() - start_time

            return TestResult(
                name=test_name,
                passed=False,
                duration=duration,
                error_message=str(e),
                traceback_info=traceback.format_exc(),
            )

    def run_directory(self, test_dir: Path) -> Dict[str, List[TestResult]]:
        """Run all test files in a directory"""

        print(f"🚀 Running tests in directory: {test_dir}")

        results_by_file = {}

        # Find all test files
        test_files = list(test_dir.glob("test_*.py"))
        test_files.extend(list(test_dir.glob("**/test_*.py")))

        print(f"   Found {len(test_files)} test files")

        for test_file in test_files:
            try:
                file_results = self.run_test_file(test_file)
                results_by_file[str(test_file)] = file_results

            except Exception as e:
                print(f"❌ Failed to run tests in {test_file}: {e}")

        return results_by_file

    def print_summary(self) -> bool:
        """Print test summary and return True if all passed"""

        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.passed])
        failed_tests = total_tests - passed_tests

        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print(f"{'='*60}")

        print(f"Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")

        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result.passed:
                    print(f"   • {result.name}")
                    print(f"     Error: {result.error_message}")
                    if result.traceback_info:
                        # Show just the last few lines of traceback
                        lines = result.traceback_info.split("\n")
                        for line in lines[-3:]:
                            if line.strip():
                                print(f"     {line}")
                    print()

        print(
            f"\n{'✅ ALL TESTS PASSED' if failed_tests == 0 else '❌ SOME TESTS FAILED'}"
        )

        return failed_tests == 0


def create_simple_test_case(name: str, test_func: Callable) -> type:
    """
    Create a simple test case from a function.

    Usage:
        def test_my_function():
            assert my_function(5) == 10

        TestCase = create_simple_test_case("TestMyFunction", test_my_function)
    """

    class DynamicTestCase(unittest.TestCase):
        def test_function(self):
            test_func()

    DynamicTestCase.__name__ = name
    return DynamicTestCase


def quick_test(description: str, test_func: Callable) -> bool:
    """
    Run a quick test with minimal overhead.

    Usage:
        def test_addition():
            assert 2 + 2 == 4

        quick_test("Addition works", test_addition)
    """

    try:
        start_time = time.time()
        test_func()
        duration = time.time() - start_time
        print(f"✅ {description} ({duration:.3f}s)")
        return True

    except Exception as e:
        print(f"❌ {description}: {e}")
        return False


def validate_import(module_name: str) -> bool:
    """Test if a module can be imported successfully"""

    try:
        import importlib

        importlib.import_module(module_name)
        return True
    except Exception:
        return False


def validate_function_exists(module_name: str, function_name: str) -> bool:
    """Test if a function exists in a module"""

    try:
        import importlib

        module = importlib.import_module(module_name)
        return hasattr(module, function_name)
    except Exception:
        return False


# Example usage and validation tests
if __name__ == "__main__":
    print("🧪 Simple Testing Framework Demo")

    # Quick validation tests
    def test_math():
        assert 2 + 2 == 4

    def test_paths():
        assert Path(".").exists()

    def test_strings():
        assert "hello".upper() == "HELLO"

    quick_test("Python math works", test_math)
    quick_test("Path operations work", test_paths)
    quick_test("String operations work", test_strings)

    # Import validation
    core_modules = [
        "core.simple_validation",
        "core.simple_logging",
        "core.simple_transactions",
        "core.simple_issue_understanding",
    ]

    print("\n🔍 Validating core modules:")
    for module in core_modules:
        exists = validate_import(module)
        print(f"   {'✅' if exists else '❌'} {module}")

    print("\n✅ Simple testing framework ready!")
    print("   - Fast execution with timeouts")
    print("   - Clear error reporting")
    print("   - No complex dependencies")
    print("   - Works with existing unittest")
