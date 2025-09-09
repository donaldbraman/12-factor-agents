# Circuit Breaker Design for Agent Loop Prevention

## Problem
Research issues created by FailureAnalysisAgent could be re-submitted to SmartIssueAgent, creating infinite loops:
```
Task → Fail → Research Issue → Task → Fail → Research Issue → ∞
```

## Solution: Single-Loop Circuit Breaker

### Core Principle
Each issue gets **exactly one retry opportunity** through the research path.

### Implementation Strategy

1. **Failure Tracking**: Track which issues have already been through failure analysis
2. **Circuit Breaker**: Block re-processing of issues that have already failed once
3. **Human Handoff**: Route blocked issues to human agents for final resolution

### Metadata Tracking
```python
# In issue metadata
parent_issue: str           # Original issue number  
failed_sub_issue: str       # Sub-issue that failed
failure_generation: int     # How many failure cycles (max 1)
```

### Decision Logic
```python
def should_allow_retry(issue_number: str) -> bool:
    """Allow maximum one failure recovery cycle"""
    # Check if this is already a research issue
    if is_research_issue(issue_number):
        return False  # Research issues go to humans, not back to agents
    
    # Check failure generation in metadata
    failure_count = get_failure_generation(issue_number) 
    return failure_count == 0  # Only allow if never failed before
```

### Updated Workflow
```
1. Task → SmartIssueAgent
2. If fails → FailureAnalysisAgent (failure_generation = 1)  
3. Research Issue → Human Agent (STOP - no more automation)
4. Human completes research → Creates new actionable issue
5. New issue → SmartIssueAgent (failure_generation = 0)
```

### Benefits
- **No infinite loops**: Hard limit of 1 retry per issue
- **Human intelligence**: Complex failures get human research
- **Clean separation**: Automated vs human-assisted workflows
- **12-Factor compliance**: Own Your Control Flow with clear boundaries

## Implementation Requirements
1. Add failure tracking to issue metadata
2. Update SmartIssueAgent with circuit breaker check
3. Route research issues to human agents only
4. Update FailureAnalysisAgent to mark failure generation