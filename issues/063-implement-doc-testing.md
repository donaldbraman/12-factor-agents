# Issue #063: Implement Automated Testing for Documentation Examples

## Description
Create automated testing to validate all code examples in documentation remain functional.

## Implementation Plan

### 1. Create Test File
Create `tests/test_integration_guide.py`:

```python
"""Test all code examples from the Integration Guide"""
import sys
import re
from pathlib import Path
import subprocess
import tempfile

def extract_code_blocks(markdown_file):
    """Extract all Python code blocks from markdown"""
    with open(markdown_file) as f:
        content = f.read()
    
    # Find all ```python blocks
    pattern = r'```python\n(.*?)```'
    return re.findall(pattern, content, re.DOTALL)

def test_code_block(code, block_num):
    """Test a single code block"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            ['uv', 'run', 'python', temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)
    finally:
        Path(temp_file).unlink(missing_ok=True)

def test_integration_guide():
    """Test all examples in the Integration Guide"""
    guide_path = Path(__file__).parent.parent / 'docs' / 'INTEGRATION-GUIDE.md'
    code_blocks = extract_code_blocks(guide_path)
    
    results = []
    for i, block in enumerate(code_blocks, 1):
        # Skip blocks that are clearly incomplete snippets
        if 'from' not in block and 'import' not in block:
            continue
            
        success, error = test_code_block(block, i)
        results.append({
            'block': i,
            'success': success,
            'error': error if not success else None
        })
    
    # Report results
    failed = [r for r in results if not r['success']]
    if failed:
        print(f"Failed blocks: {[r['block'] for r in failed]}")
        for r in failed:
            print(f"Block {r['block']}: {r['error']}")
        assert False, f"{len(failed)} code blocks failed"
    
    print(f"✅ All {len(results)} code blocks passed!")

if __name__ == '__main__':
    test_integration_guide()
```

### 2. Add to CI Pipeline
Update `.github/workflows/test.yml`:

```yaml
- name: Test Documentation Examples
  run: |
    uv run python tests/test_integration_guide.py
```

### 3. Add Pre-commit Hook
Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: test-docs
        name: Test Documentation Examples
        entry: uv run python tests/test_integration_guide.py
        language: system
        files: docs/.*\.md$
```

## Benefits
- Ensures documentation stays accurate
- Catches breaking changes early  
- Improves developer confidence
- Prevents regression of fixed examples

## Type
testing

## Priority
high

## Status
open

## Assignee
issue_fixer_agent