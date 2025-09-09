# Usage Guide

## Issue Implementation Pattern
1. Use `/docs/AGENT-ISSUE-TEMPLATE.md`
2. Create autonomous agent script
3. Launch with `run_in_background=True`
4. Monitor via status files

## Performance Validation
- Run `make perf-test` to validate claims
- All metrics proven in production
- 0.2% overhead maintained

## Local Development
- `make install-hooks` - One-time setup
- `make test` - Full quality gates
- Pre-commit hooks prevent regressions
