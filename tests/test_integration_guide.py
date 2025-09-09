"""Test all code examples from the Integration Guide"""


def extract_code_blocks(markdown_file):
    """Extract all Python code blocks from markdown"""
    with open(markdown_file) as f:
        content = f.read()

    # Find all
