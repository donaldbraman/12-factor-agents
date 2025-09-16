# Issue #098: Add integration testing pipeline after modifications

## Problem
When agents modify code in sister repositories, there's no automatic testing to verify the changes work. This means:
- Syntax errors only discovered when users run code
- Breaking changes not caught before completion
- No verification that fixes actually solve the problem
- Sister repos may have different test frameworks/commands

## Current State
- TestingAgent exists but isn't integrated with orchestrator
- No automatic test execution after modifications
- No handling of sister repo test configurations
- Changes marked "complete" without verification

## Desired Behavior
The orchestrator should automatically run tests after code review:

```
1. Agent modifies files
2. Code review passes
3. Orchestrator triggers TestingAgent with:
   - Target repository context
   - Appropriate test command discovery
   - Focused test execution (affected files)
4. If tests fail → hand back to SAME agent with test results:
   - Agent gets test failure output
   - Agent analyzes failure and adjusts fix
   - Agent resubmits modifications
   - Repeat until tests pass or max retries
5. If tests pass → mark complete
6. Report test results in telemetry
```

## Implementation Strategy

### 1. Test Discovery
```python
def _discover_test_command(self, repo_path: Path) -> str:
    """Discover appropriate test command for repository"""
    # Check for common test configurations
    if (repo_path / "Makefile").exists():
        # Check for test target in Makefile
        return "make test"
    elif (repo_path / "pyproject.toml").exists():
        # Check for pytest configuration
        return "uv run pytest"
    elif (repo_path / "package.json").exists():
        # Node.js project
        return "npm test"
    # Default Python
    return "python -m pytest"
```

### 2. Focused Testing
```python
def _run_focused_tests(self, modified_files: List[str], repo_context: ExecutionContext):
    """Run tests related to modified files"""
    test_files = self._find_related_tests(modified_files)
    if test_files:
        return self._execute_tests(test_files, repo_context)
    else:
        # Run all tests if can't determine specific ones
        return self._run_all_tests(repo_context)
```

### 3. Integration with Orchestrator
```python
# In IssueOrchestratorAgent
if review_result["passed"]:
    test_result = self._run_integration_tests(
        modified_files=result.get("files_modified"),
        context=context
    )
    if not test_result["passed"]:
        # Hand back to the SAME agent with test results
        retry_result = agent.execute_task(
            task=original_task,
            context=context,
            test_failures=test_result["failures"],
            previous_attempt=result
        )
        return self._process_retry_result(retry_result)
```

### 4. Agent Enhancement for Test Feedback
```python
# In IntelligentIssueAgent
def execute_task(self, task: str, context: ExecutionContext, 
                 test_failures: List[Dict] = None, 
                 previous_attempt: Dict = None):
    """Enhanced to handle test failure feedback"""
    if test_failures:
        # Analyze test failures and adjust approach
        self._analyze_test_failures(test_failures)
        # Use failure info to guide fixes
        return self._fix_based_on_test_results(
            task, test_failures, previous_attempt
        )
    # Normal execution path
    return self._normal_execution(task, context)
```

## Success Criteria
- [ ] Tests automatically run after code review passes
- [ ] Test discovery works across different repo configurations
- [ ] Focused test execution for modified files
- [ ] Test failures trigger retry mechanism
- [ ] Sister repo test configurations respected
- [ ] Test results in telemetry and reporting

## Configuration Support
Support for repository-specific test configurations via:
- `.12factor/test-config.yml`
- `Makefile` test targets
- `pyproject.toml` pytest settings
- `package.json` test scripts
- CLAUDE.md test instructions

## Example Case
For pin-citer issue #144:
1. Would have run `uv run pytest tests/unit/orchestration/test_citation_patterns.py`
2. Would have caught the IndentationError immediately
3. Would have triggered automatic fix attempt
4. Would have verified fix works before marking complete

## Priority
Critical - This ensures modifications actually work before completion

## Agent Assignment
IssueOrchestratorAgent, TestingAgent