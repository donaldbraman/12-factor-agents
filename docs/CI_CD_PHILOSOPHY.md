# CI/CD Philosophy for 12-Factor Agents

## Core Principles

Our CI/CD is designed to be **simple**, **reliable**, and **valuable**. We learned that complex CI/CD often causes more problems than it solves.

## What We Test (and Why)

### 1. Core Functionality Only
We test what sister repositories actually need:
- **Can they import our framework?** ✓
- **Does the CLI work?** ✓  
- **Do agents execute?** ✓

That's it. Everything else is secondary.

### 2. Known-Good Tests
We only run tests we KNOW work:
- `test_quick_validation.py` - Validates core imports and basic functionality
- Specific issue fix tests that are stable
- No flaky integration tests in the critical path

### 3. Non-Blocking Health Checks
We have an optional job that shows what's broken without blocking PRs:
- Runs all tests with timeouts
- Reports failures for visibility
- Never prevents merging

## What We DON'T Do

### ❌ Don't Block on Broken Tests
If the test suite is broken, fix it separately. Don't block feature development.

### ❌ Don't Over-Engineer
No complex test matrices, staged pipelines, or elaborate retry logic. Keep it simple.

### ❌ Don't Test Everything
Test the critical path. If sister repos can use the framework, it works.

## The Two-Job Pattern

```yaml
jobs:
  validate:      # MUST PASS - Tests critical functionality
  test-health:   # OPTIONAL - Shows what needs fixing
```

## Why This Works

1. **Reliability**: Only runs tests that actually work
2. **Speed**: Focuses on critical path, runs in <1 minute
3. **Visibility**: Shows problems without blocking progress
4. **Pragmatism**: Acknowledges reality (test suite needs work)

## Lessons for Other Repos

### Start Simple
Begin with:
1. Can the code be imported?
2. Does the main entry point work?
3. Do 2-3 critical functions work?

That's often enough.

### Add Gradually
As tests become stable, move them from "health check" to "required".

### Be Honest
If your test suite is broken, don't pretend it isn't. Run what works, fix the rest gradually.

### Focus on Value
Ask: "What would actually catch a real problem?" Test that. Skip the rest.

## Example: Minimal Valuable CI

```yaml
name: Core Validation
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test Critical Path
        run: |
          # 1. Can it be imported?
          python -c "import my_package"
          
          # 2. Does the CLI work?
          python -m my_package --help
          
          # 3. Does one critical test pass?
          pytest tests/test_critical_function.py
```

This 15-line CI is often more valuable than a 500-line monster.

## Migration Path

When your test suite is broken:

1. **Week 1**: Run only what works (like above)
2. **Week 2-4**: Fix tests one by one
3. **Week 5+**: Gradually add fixed tests to CI
4. **Month 2+**: Consider coverage requirements

Don't try to fix everything at once. Progress > Perfection.

## The Bottom Line

**CI/CD should help, not hinder.**

If it's blocking development, it's too complex. If it's not catching real issues, it's too simple. Find the sweet spot for YOUR repository.

For 12-factor-agents, that sweet spot is:
- Pre-commit hooks handle code quality
- Core validation ensures critical functionality
- Health checks provide visibility
- Nothing blocks unnecessarily

This philosophy has made our development faster and less frustrating, while still maintaining quality where it matters.