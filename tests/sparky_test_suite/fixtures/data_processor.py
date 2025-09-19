#!/usr/bin/env python3
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
    return True
