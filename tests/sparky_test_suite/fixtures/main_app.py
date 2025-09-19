#!/usr/bin/env python3
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
    main()
