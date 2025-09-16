# Complete Pipeline Handoff Documentation

## Overview
This document maps every handoff point in the agent pipeline, including conditions for handoff and state passed.

---

## 1. ENTRY: User/Sister Repo → IssueOrchestratorAgent (Sparky)

### Trigger Conditions
- User runs: `python scripts/submit_to_agents.py <issue_number>`
- Sister repo calls ExternalIssueProcessor
- Direct invocation via CLI

### State Passed (Current)
```python
{
    "task": "Issue #123 from repo-name",
    "context": ExecutionContext(
        repo_name="sister-repo",
        repo_path=Path("/path/to/sister/repo"),
        is_external=True
    )
}
```

### State Missing
- Previous attempts on this issue
- User preferences/constraints
- Success criteria

### Handoff Decision
- **Always** goes to Sparky first (central orchestration)

---

## 2. ROUTING: Sparky → Specialized Agent

### Current Routing Logic
```python
# From issue_orchestrator_agent.py
if "documentation" in task_lower:
    agent_name = "DocumentationAgent"
elif "test" in task_lower:
    agent_name = "TestingAgent"
elif "review" in task_lower:
    agent_name = "CodeReviewAgent"
elif validation_results:  # Has validation issues
    agent_name = "ValidationAgent"
else:
    agent_name = "IntelligentIssueAgent"  # Default
```

### Trigger Conditions for Each Agent

#### → IntelligentIssueAgent
- **Condition**: Default for general issues
- **Keywords**: fix, bug, error, implement, feature
- **State Passed**:
  ```python
  {
      "task": "Original task description",
      "context": ExecutionContext,
      "issue_content": "Full issue text"
  }
  ```

#### → DocumentationAgent
- **Condition**: "documentation" in task
- **State Passed**: Same as above

#### → TestingAgent  
- **Condition**: "test" in task
- **State Passed**: Same as above

#### → CodeReviewAgent
- **Condition**: "review" in task
- **State Passed**: Same as above

#### → ValidationAgent
- **Condition**: Previous validation errors exist
- **State Passed**: 
  ```python
  {
      "task": "Original task",
      "context": ExecutionContext,
      "validation_errors": [...],
      "previous_attempt": {...}
  }
  ```

### Handoff Decision Point
```python
if result["success"]:
    return to_user(result)
else:
    if should_retry():
        handoff_to_same_agent_with_feedback()
    else:
        return_failure_to_user()
```

---

## 3. EXECUTION: Agent → Back to Sparky

### Success Conditions (Return to Sparky)
```python
{
    "success": True,
    "files_modified": ["path/to/file.py"],
    "lines_changed": 150,
    "concrete_work": True
}
```
**Next**: Sparky → User (SUCCESS)

### Failure Conditions

#### Validation Failure
```python
{
    "success": False,
    "validation_errors": [
        {"file": "path.py", "error": "SyntaxError"}
    ]
}
```
**Next**: Sparky → ValidationAgent (if exists) OR Same Agent (retry)

#### No Files Found
```python
{
    "success": True,
    "files_modified": [],
    "concrete_work": False,
    "reason": "No files matched issue description"
}
```
**Next**: Sparky → User (PARTIAL SUCCESS)

#### Feature Request (New)
```python
{
    "success": True,
    "feature_created": True,
    "files_created": ["new_feature.py"],
    "needs_review": True
}
```
**Next**: Should go to → CodeReviewAgent → TestingAgent

---

## 4. REVIEW STAGE (Not Yet Implemented)

### Should Trigger When
- `files_modified` > 0
- `files_created` > 0
- `needs_review` flag is True

### Handoff: Sparky → CodeReviewAgent

### State Needed
```python
{
    "files_to_review": ["path/to/modified.py"],
    "original_issue": "Issue description",
    "changes_made": {...},
    "pipeline_state": PipelineState
}
```

### Review Results → Decision

#### Review Passed
```python
{
    "review_passed": True,
    "findings": [],
    "quality_score": 95
}
```
**Next**: → TestingAgent

#### Review Failed (Minor)
```python
{
    "review_passed": False,
    "findings": [
        {"severity": "minor", "issue": "Missing docstring"}
    ],
    "can_auto_fix": True
}
```
**Next**: → Same Agent (with review feedback)

#### Review Failed (Major)
```python
{
    "review_passed": False,
    "findings": [
        {"severity": "major", "issue": "Logic error"}
    ],
    "can_auto_fix": False
}
```
**Next**: → User (MANUAL INTERVENTION NEEDED)

---

## 5. TESTING STAGE (Not Yet Implemented)

### Should Trigger When
- Review passed
- `concrete_work` is True
- Test command discovered

### Handoff: Sparky → TestingAgent

### State Needed
```python
{
    "test_command": "pytest tests/",
    "modified_files": [...],
    "test_strategy": "focused",  # or "full"
    "pipeline_state": PipelineState
}
```

### Test Results → Decision

#### Tests Passed
```python
{
    "tests_passed": True,
    "coverage": 85,
    "test_output": "All tests passed"
}
```
**Next**: → User (COMPLETE SUCCESS)

#### Tests Failed (Can Retry)
```python
{
    "tests_passed": False,
    "failed_tests": ["test_function_x"],
    "error_type": "AssertionError",
    "can_retry": True
}
```
**Next**: → Original Agent (with test output)

#### Tests Failed (Can't Retry)
```python
{
    "tests_passed": False,
    "error_type": "ImportError",
    "can_retry": False,
    "reason": "Missing dependency"
}
```
**Next**: → User (BLOCKED)

---

## 6. RETRY LOGIC

### Current Retry Conditions
1. **Validation Errors** → IntelligentValidationRetry
2. **Test Failures** → Should retry with test context
3. **Review Failures** → Should retry with review context

### Retry State Progression
```python
# First Attempt
{
    "attempt": 1,
    "strategy": "direct_fix",
    "previous_errors": []
}

# Second Attempt  
{
    "attempt": 2,
    "strategy": "mechanical_fix",
    "previous_errors": ["SyntaxError at line 47"],
    "avoided_patterns": ["incorrect_indentation"]
}

# Third Attempt
{
    "attempt": 3,
    "strategy": "simplified_approach",
    "previous_errors": [...],
    "avoided_patterns": [...],
    "simplification_level": "high"
}

# Final Attempt
{
    "attempt": 4,
    "strategy": "minimal_safe_fix",
    "escalate_if_fails": True
}
```

### Max Retries Reached → User
```python
{
    "success": False,
    "attempts": 4,
    "all_errors": [...],
    "recommendation": "Manual intervention required",
    "partial_fixes": [...]  # What did work
}
```

---

## 7. SPECIAL HANDOFFS

### Cross-Repository Handoff
**Sister Repo Issue** → **ExternalIssueProcessor** → **Sparky**
```python
{
    "source_repo": "pin-citer",
    "issue_number": "144",
    "issue_content": "Full issue text",
    "repo_context": ExecutionContext(is_external=True)
}
```

### Decomposition Handoff (SmartIssueAgent)
**Complex Issue** → **Decompose** → **Multiple Sub-Issues**
```python
for sub_issue in decomposed_issues:
    handoff_to_sparky({
        "parent_issue": original_issue_id,
        "sub_issue": sub_issue,
        "order": index,
        "dependencies": [...]
    })
```

### Escalation Handoff
**Blocked Agent** → **User Notification**
```python
{
    "escalation": True,
    "reason": "Cannot proceed without human input",
    "specific_need": "Please resolve merge conflict in file.py",
    "context": full_pipeline_state
}
```

---

## 8. RETURN TO USER CONDITIONS

### Success Returns
1. **Complete Success**: All files modified, tests pass, review passes
2. **Partial Success**: Some files fixed, others need manual work
3. **Feature Created**: New files created, ready for review

### Failure Returns
1. **Cannot Find Issue**: No matching issue file/content
2. **No Files to Fix**: Issue doesn't map to code changes
3. **Max Retries Exceeded**: Tried all strategies, still failing
4. **Blocked**: Missing dependencies, merge conflicts, etc.
5. **Manual Review Needed**: Changes too risky for auto-merge

### State Returned to User
```python
{
    "pipeline_id": "uuid",
    "final_status": "success|partial|failed|blocked",
    "work_completed": {
        "files_modified": [...],
        "lines_changed": 150,
        "tests_passed": True,
        "review_passed": True
    },
    "issues_remaining": [...],
    "manual_steps_needed": [...],
    "execution_time": 45.2,
    "cost_estimate": "$0.03"
}
```

---

## 9. CRITICAL GAPS IN CURRENT SYSTEM

### Missing Handoffs
1. **No automatic Review handoff** after modifications
2. **No automatic Test handoff** after review  
3. **No feedback loop** from tests to agent
4. **No state preservation** across handoffs

### Missing State
1. **Pipeline State object** to carry context
2. **Retry history** for learning
3. **Confidence scores** for decisions
4. **Time/cost tracking** for optimization

### Missing Decision Points
1. **When to escalate** vs retry
2. **When to decompose** vs handle directly
3. **When to simplify** vs abandon
4. **When to request human input**

---

## Proposed Ideal Pipeline

```
Entry → Route → Execute → Review → Test → Verify → Complete
  ↓       ↓        ↓        ↓       ↓       ↓        ↓
  └───────────── PipelineState flows through all ─────────┘
                           ↓
                    On any failure:
                    Retry with context
                           ↓
                    Max retries → User
```

Each handoff would include:
- Full PipelineState
- Specific handoff reason
- Success criteria for next stage
- Rollback instructions if needed