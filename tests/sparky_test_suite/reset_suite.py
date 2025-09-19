#!/usr/bin/env python3
"""
SPARKY Test Suite Reset
Restores all fixtures to clean state for repeated testing
"""

import shutil
import subprocess
from pathlib import Path


def reset_test_suite():
    """Reset test suite to clean state"""
    suite_dir = Path(__file__).parent

    print("🔄 Resetting SPARKY Test Suite...")

    # 1. Reset git state for fixtures
    fixtures_dir = suite_dir / "fixtures"
    try:
        subprocess.run(["git", "checkout", "HEAD", str(fixtures_dir)], check=False)
        print("  ✅ Git state reset")
    except:
        print("  ⚠️  Git reset skipped")

    # 2. Remove generated directories
    generated_dirs = [
        fixtures_dir / "cache",
        fixtures_dir / "logs",
        fixtures_dir / "temp",
        suite_dir / "test_reports",
    ]

    for gen_dir in generated_dirs:
        if gen_dir.exists():
            shutil.rmtree(gen_dir)
            print(f"  🗑️  Removed {gen_dir.name}")

    # 3. Remove generated files
    generated_files = [
        fixtures_dir / "logger.py",
        fixtures_dir / "test_error_handling.py",
        fixtures_dir / "test_cache.py",
        fixtures_dir / "docker-compose.yml",
    ]

    for gen_file in generated_files:
        if gen_file.exists():
            gen_file.unlink()
            print(f"  🗑️  Removed {gen_file.name}")

    # 4. Reset modified files to original state
    original_files = {
        "simple_function.py": '''#!/usr/bin/env python3
"""
Simple function for SPARKY testing
"""

def process_input(data):
    # Line 5 - target for comment insertion
    result = data.upper()
    return result

def helper_function():
    return "helper"''',
        "data_processor.py": '''#!/usr/bin/env python3
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
    return True''',
        "main_app.py": '''#!/usr/bin/env python3
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
    main()''',
    }

    for filename, content in original_files.items():
        file_path = fixtures_dir / filename
        file_path.write_text(content)
        print(f"  ♻️  Reset {filename}")

    # 5. Clean test reports
    for report in suite_dir.glob("test_report_*.txt"):
        report.unlink()
        print(f"  🗑️  Removed {report.name}")

    print("✅ Test suite reset complete - ready for fresh testing!")


if __name__ == "__main__":
    reset_test_suite()
