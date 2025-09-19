# Pre-Commit Hook Hygiene Enforcement Plan

## Current State Analysis

### ✅ What We Have
- **Black** - Code formatting
- **Ruff** - Linting and basic code quality
- **Quick Tests** - Basic test validation
- **Performance Check** - Regression detection

### ❌ What's Missing (Critical Gaps)
1. **No file location validation** - Can still commit Python files to root
2. **No secrets detection** - Can commit tokens, keys, passwords
3. **No architecture compliance** - Can violate directory structure
4. **No TODO tracking** - Untracked TODOs accumulate
5. **No documentation checks** - Missing docstrings go unnoticed
6. **No import validation** - Wildcard imports not caught
7. **No file naming checks** - Inconsistent naming allowed
8. **No test coverage enforcement** - Can commit untested code

## Proposed Pre-Commit Hook Architecture

### 🔒 Tier 1: Security (Block Commits)
```yaml
# Prevent secrets from being committed
- id: detect-secrets
  name: Detect Secrets
  entry: scripts/detect_secrets.py
  language: python
  pass_filenames: true
  
# Check for exposed tokens
- id: check-tokens
  name: Check for Tokens
  entry: scripts/check_tokens.py
  language: python
  files: \.(py|json|yaml|yml|txt|md)$
```

### 🏗️ Tier 2: Architecture (Block Commits)
```yaml
# Validate file locations
- id: check-file-location
  name: Check File Location
  entry: scripts/check_file_location.py
  language: python
  pass_filenames: true
  files: \.py$
  
# Validate directory structure
- id: check-architecture
  name: Check Architecture
  entry: scripts/check_architecture.py
  language: python
  always_run: true
```

### 📋 Tier 3: Code Quality (Block Commits)
```yaml
# No wildcard imports
- id: no-wildcard-imports
  name: No Wildcard Imports
  entry: scripts/check_imports.py
  language: python
  files: \.py$
  
# No print statements
- id: no-print-statements
  name: No Print Statements
  entry: scripts/check_print.py
  language: python
  files: \.py$
  exclude: ^scripts/|^tests/
  
# No bare excepts
- id: no-bare-except
  name: No Bare Except
  entry: scripts/check_except.py
  language: python
  files: \.py$
```

### 📊 Tier 4: Documentation (Warning Only)
```yaml
# Check for TODOs
- id: track-todos
  name: Track TODOs
  entry: scripts/track_todos.py
  language: python
  files: \.py$
  verbose: true
  
# Check docstrings
- id: check-docstrings
  name: Check Docstrings
  entry: scripts/check_docstrings.py
  language: python
  files: \.py$
```

## Implementation Scripts

### 1. `scripts/check_file_location.py`
```python
#!/usr/bin/env python3
"""Validate Python files are in correct directories."""

import sys
from pathlib import Path

ALLOWED_ROOT_FILES = {'setup.py'}
DIRECTORY_RULES = {
    'test_': 'tests/',
    '_agent.py': 'agents/',
    'config': 'config/',
}

def check_file_location(filepath):
    """Check if file is in correct location."""
    path = Path(filepath)
    
    # Check root directory files
    if path.parent == Path('.'):
        if path.name not in ALLOWED_ROOT_FILES:
            print(f"❌ {filepath}: Python files not allowed in root")
            return False
    
    # Check naming conventions match directories
    for pattern, expected_dir in DIRECTORY_RULES.items():
        if pattern in path.name:
            if expected_dir not in str(path.parent):
                print(f"❌ {filepath}: Should be in {expected_dir}")
                return False
    
    return True

if __name__ == "__main__":
    all_valid = True
    for filepath in sys.argv[1:]:
        if filepath.endswith('.py'):
            if not check_file_location(filepath):
                all_valid = False
    
    sys.exit(0 if all_valid else 1)
```

### 2. `scripts/detect_secrets.py`
```python
#!/usr/bin/env python3
"""Detect potential secrets in files."""

import sys
import re

SECRET_PATTERNS = [
    (r'["\']?[Aa][Pp][Ii][-_]?[Kk][Ee][Yy]["\']?\s*[:=]\s*["\'][^"\']+["\']', 'API Key'),
    (r'["\']?[Ss][Ee][Cc][Rr][Ee][Tt][-_]?[Kk][Ee][Yy]["\']?\s*[:=]\s*["\'][^"\']+["\']', 'Secret Key'),
    (r'["\']?[Tt][Oo][Kk][Ee][Nn]["\']?\s*[:=]\s*["\'][^"\']+["\']', 'Token'),
    (r'["\']?[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]["\']?\s*[:=]\s*["\'][^"\']+["\']', 'Password'),
    (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
    (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Token'),
]

def detect_secrets(filepath):
    """Check file for potential secrets."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        for pattern, secret_type in SECRET_PATTERNS:
            if re.search(pattern, content):
                # Allow environment variable references
                if not re.search(r'os\.environ|os\.getenv|ENV\[', content):
                    print(f"❌ {filepath}: Potential {secret_type} detected")
                    return False
    except:
        pass
    
    return True

if __name__ == "__main__":
    all_clean = True
    for filepath in sys.argv[1:]:
        if not detect_secrets(filepath):
            all_clean = False
    
    sys.exit(0 if all_clean else 1)
```

### 3. `scripts/check_architecture.py`
```python
#!/usr/bin/env python3
"""Validate repository architecture compliance."""

import sys
from pathlib import Path

def check_architecture():
    """Validate overall repository structure."""
    violations = []
    
    # Check for Python files in root
    root_py = list(Path('.').glob('*.py'))
    allowed = {'setup.py'}
    for file in root_py:
        if file.name not in allowed:
            violations.append(f"Python file in root: {file}")
    
    # Check for required directories
    required_dirs = ['agents', 'core', 'tests', 'scripts', 'docs']
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            violations.append(f"Missing required directory: {dir_name}/")
    
    # Check for build artifacts
    artifacts = ['*.egg-info', '__pycache__', '*.pyc', 'token.json']
    for pattern in artifacts:
        if list(Path('.').rglob(pattern)):
            violations.append(f"Build artifact found: {pattern}")
    
    if violations:
        print("❌ Architecture violations found:")
        for v in violations:
            print(f"  - {v}")
        return False
    
    return True

if __name__ == "__main__":
    sys.exit(0 if check_architecture() else 1)
```

## Updated `.pre-commit-config.yaml`

```yaml
# Repository Hygiene Enforcement
repos:
  # Existing hooks
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3
        args: [--line-length=88]
        
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
  
  # Security hooks
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: .*\.lock|package-lock\.json
  
  # Architecture enforcement
  - repo: local
    hooks:
      # Security
      - id: check-secrets
        name: Check for Secrets
        entry: python scripts/detect_secrets.py
        language: system
        pass_filenames: true
        
      # Architecture
      - id: check-file-location
        name: Check File Location
        entry: python scripts/check_file_location.py
        language: system
        pass_filenames: true
        files: \.py$
        
      - id: check-architecture
        name: Check Architecture Compliance
        entry: python scripts/check_architecture.py
        language: system
        always_run: true
        pass_filenames: false
        
      # Code quality
      - id: no-wildcard-imports
        name: No Wildcard Imports
        entry: grep -H "from .* import \*"
        language: system
        files: \.py$
        types: [python]
        
      - id: no-print-statements
        name: No Print Statements
        entry: grep -H "print("
        language: system
        files: \.py$
        exclude: ^(scripts|tests)/
        
      # Documentation
      - id: track-todos
        name: Track TODOs
        entry: python scripts/track_todos.py
        language: system
        files: \.py$
        verbose: true
        
      # Existing hooks
      - id: quick-tests
        name: Quick Test Suite
        entry: uv run -m pytest tests/test_quick_validation.py -v
        language: system
        pass_filenames: false
        always_run: true
        
      - id: performance-check
        name: Performance Regression Check
        entry: uv run scripts/quick_performance_check.py
        language: system
        pass_filenames: false
        always_run: true
```

## Enforcement Levels

### 🔴 Block Commit (Exit 1)
- Secrets detected
- Files in wrong location
- Architecture violations
- Wildcard imports
- Print statements in production code

### 🟡 Warning Only (Exit 0 with message)
- TODO without issue number
- Missing docstrings
- Low test coverage

### 🟢 Pass
- All checks pass
- Clean commit allowed

## Rollout Plan

### Phase 1: Foundation (Week 1)
1. Create validation scripts
2. Test locally with `pre-commit run --all-files`
3. Fix existing violations

### Phase 2: Soft Launch (Week 2)
1. Enable warnings only
2. Team education
3. Gradual fixes

### Phase 3: Enforcement (Week 3)
1. Enable blocking hooks
2. Monitor and adjust
3. Add to CI/CD

## Benefits

### Immediate
- **Prevent security leaks** - No secrets committed
- **Enforce structure** - Files in correct places
- **Maintain quality** - Consistent code standards

### Long-term
- **Reduce review time** - Automated checks
- **Prevent technical debt** - Catch issues early
- **Improve onboarding** - Clear standards

## Success Metrics

| Metric | Target | Measure |
|--------|--------|---------|
| Security violations | 0 | Secrets detected |
| Architecture violations | 0 | Files misplaced |
| Code quality issues | <5 per PR | Linting errors |
| Pre-commit pass rate | >95% | Successful commits |
| Developer satisfaction | >4/5 | Survey score |

## Next Steps

1. **Review this plan** with team
2. **Create validation scripts** in `scripts/`
3. **Update `.pre-commit-config.yaml`**
4. **Test with existing codebase**
5. **Roll out in phases**

---

This plan ensures every commit maintains repository hygiene through automated enforcement.