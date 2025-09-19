# Repository Architecture & Standards
**12-Factor-Agents Framework**

Version 1.0 | Last Updated: 2025-01-19

## 🎯 Purpose

This document defines the **enforceable architecture standards** for the 12-factor-agents repository. All code contributions must comply with these standards.

## 📁 Directory Structure

```
12-factor-agents/
├── agents/                 # Agent implementations
│   ├── __init__.py
│   ├── base.py            # Base agent class
│   ├── sparky*.py         # SPARKY ecosystem agents
│   └── *_agent.py         # Other specialized agents
│
├── core/                   # Core framework components
│   ├── __init__.py
│   ├── auth.py            # Authentication
│   ├── database.py        # Database interfaces
│   ├── user.py            # User management
│   ├── github_integration.py
│   ├── compliance.py      # 12-factor validators
│   ├── cache_manager.py   # Caching system
│   ├── circuit_breaker.py # Fault tolerance
│   └── metrics_collector.py
│
├── prompts/               # Externalized prompts
│   └── {agent_name}/      # Per-agent prompt directory
│       └── *.prompt       # Individual prompt files
│
├── tests/                 # Test suite
│   ├── test_*.py         # Unit tests
│   ├── sparky_test_suite/ # SPARKY integration tests
│   └── fixtures/         # Test fixtures
│
├── scripts/              # Utility scripts
│   ├── *.py             # Standalone scripts
│   └── validation/      # Validation utilities
│
├── docs/                # Documentation
│   ├── architecture/   # Architecture docs
│   ├── api/            # API documentation
│   ├── guides/         # User guides
│   └── archive/        # Historical/deprecated docs
│
├── config/             # Configuration files
│   ├── *.json         # Config files
│   └── *.yaml         # YAML configs
│
├── bin/               # Executable entry points
│   ├── __init__.py
│   └── *.py          # CLI tools
│
├── .github/          # GitHub specific
│   └── workflows/    # CI/CD workflows
│
├── archive/          # Deprecated code
│   └── deprecated_agents/
│
└── [ROOT FILES]      # Only essential files
    ├── README.md
    ├── LICENSE
    ├── .gitignore
    ├── pyproject.toml
    └── .pre-commit-config.yaml
```

## 🚫 Prohibited Practices

### ❌ NEVER Do These:

1. **Place Python files in root directory**
   - Exception: setup.py (if needed)

2. **Commit sensitive data**
   - No tokens, keys, passwords, or secrets
   - No .env files (only .env.example)

3. **Use wildcard imports**
   - Bad: `from module import *`
   - Good: `from module import specific_function`

4. **Use print() for logging**
   - Bad: `print(f"Error: {e}")`
   - Good: `logger.error(f"Error: {e}")`

5. **Use bare except clauses**
   - Bad: `except:`
   - Good: `except SpecificException:`

6. **Leave TODO comments without tracking**
   - Must create GitHub issue for TODOs

7. **Mix test and production code**
   - Tests go in tests/ directory only

8. **Create documentation without request**
   - Only create docs when explicitly needed

## ✅ Required Practices

### File Organization

```python
# Every Python file structure:
"""Module docstring."""

# Standard library imports
import os
import sys

# Third-party imports
import pytest
from pydantic import BaseModel

# Local imports
from core.base import BaseClass
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | snake_case | `github_integration.py` |
| Classes | PascalCase | `GitHubIntegration` |
| Functions | snake_case | `process_issue()` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |
| Directories | snake_case | `test_fixtures/` |

### Agent Standards

Every agent MUST:

```python
class NewAgent:
    """Agent description."""
    
    def __init__(self):
        """Initialize with required components."""
        self.github = GitHubIntegration()
        self.metrics = MetricsCollector()
        self.circuit_breaker = CircuitBreaker()
    
    async def process(self, input_data: dict) -> dict:
        """Main processing method."""
        # Implementation
        pass
```

### Test Requirements

```python
# tests/test_new_feature.py
def test_feature_happy_path():
    """Test normal operation."""
    assert expected == actual

def test_feature_edge_case():
    """Test edge cases."""
    with pytest.raises(ExpectedException):
        trigger_edge_case()

def test_feature_error_handling():
    """Test error conditions."""
    # Test graceful failure
```

### Documentation Standards

```markdown
# Feature Name

## Overview
Brief description (1-2 sentences)

## Usage
```python
# Code example
```

## API Reference
- `function_name(param: type) -> return_type`

## Configuration
Required environment variables or configs
```

## 🔧 Enforcement Tools

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
```

### CI/CD Checks

```yaml
# .github/workflows/quality.yml
- name: Architecture Compliance
  run: |
    python scripts/check_architecture.py
    python scripts/validate_structure.py
```

### Validation Script

```python
# scripts/check_architecture.py
def validate_repository():
    """Enforce architecture rules."""
    
    # Check no Python files in root
    root_py_files = glob.glob("*.py")
    assert not root_py_files, f"Python files in root: {root_py_files}"
    
    # Check no secrets
    secret_patterns = ["API_KEY", "TOKEN", "SECRET", "PASSWORD"]
    for pattern in secret_patterns:
        assert not check_for_pattern(pattern), f"Found potential secret: {pattern}"
    
    # Check import structure
    validate_imports()
    
    # Check test coverage
    assert get_test_coverage() > 80, "Test coverage below 80%"
```

## 📊 Quality Metrics

### Required Thresholds

| Metric | Minimum | Target |
|--------|---------|--------|
| Test Coverage | 80% | 90% |
| Code Complexity | <10 | <7 |
| Documentation | 100% public APIs | All functions |
| Linting Score | 9.0/10 | 10/10 |
| Type Coverage | 85% | 95% |

### Health Indicators

```bash
# Run health check
python scripts/repo_health_check.py

# Expected output:
✅ No files in root
✅ No exposed secrets  
✅ All tests passing
✅ Documentation complete
✅ Type hints present
```

## 🚀 Migration Path

For existing code not meeting standards:

### Phase 1: Critical (Immediate)
- [ ] Remove secrets from tracking
- [ ] Move files from root
- [ ] Fix bare except clauses

### Phase 2: Important (This Week)
- [ ] Replace print() with logging
- [ ] Add type hints to public APIs
- [ ] Create missing tests

### Phase 3: Enhancement (This Sprint)
- [ ] Complete documentation
- [ ] Optimize imports
- [ ] Reduce complexity

## 🔄 Continuous Improvement

### Weekly Reviews
- Run hygiene report: `python scripts/generate_hygiene_report.py`
- Address critical issues
- Update this document as needed

### Monthly Audits
- Full architecture compliance check
- Performance benchmarks
- Dependency updates

### Quarterly Planning
- Refactor technical debt
- Update architecture patterns
- Review and revise standards

## 🎮 Quick Commands

```bash
# Check architecture compliance
make check-architecture

# Auto-fix common issues
make fix-common

# Generate hygiene report
make hygiene-report

# Run full validation
make validate-all

# Clean temporary files
make clean
```

## 📝 Enforcement Checklist

Before merging ANY pull request:

- [ ] No Python files added to root
- [ ] No secrets or tokens committed
- [ ] All tests passing
- [ ] No print() statements
- [ ] No bare except clauses
- [ ] Type hints on public functions
- [ ] Documentation for new features
- [ ] Imports properly organized
- [ ] File naming follows conventions
- [ ] Code complexity below threshold

## 🚨 Violations

Violations will result in:

1. **PR blocked** by automated checks
2. **Review required** from maintainer
3. **Must fix** before merge allowed

## 📚 References

- [12-Factor App Principles](https://12factor.net/)
- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Type Hints (PEP 484)](https://www.python.org/dev/peps/pep-0484/)
- [Project Documentation](./docs/architecture/)

---

**This document is enforceable via CI/CD.** All contributions must comply or will be automatically rejected.

Last reviewed: 2025-01-19
Next review: 2025-02-19