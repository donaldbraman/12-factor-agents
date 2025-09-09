# Issue #120: Create Actionable User Guide with No Fluff

## Description
Create a crisp, actionable user guide that shows exactly how to use the 12-Factor SmartIssueAgent system. No fluff, only actionable intelligence.

## Current Problem
The existing INTEGRATION-GUIDE.md contains outdated patterns and doesn't reflect the new SmartIssueAgent workflow with automatic complexity detection and 12-Factor decomposition.

## Required Solution
Create a new USER-GUIDE.md that demonstrates:

### 1. Quick Start (30 seconds)
```bash
# Submit ANY issue - complexity detection is automatic
uv run python bin/agent.py run SmartIssueAgent "064"
```

### 2. What Happens Automatically
- ✅ Complexity analysis (atomic → enterprise)
- ✅ Smart routing (direct handling vs decomposition)
- ✅ 12-Factor compliant sub-issue creation
- ✅ Intelligent agent assignment

### 3. Real Examples by Complexity
Show actual working examples for each complexity level:
- **Atomic**: Single typo fix
- **Simple**: README update
- **Moderate**: Multi-file update
- **Complex**: Documentation overhaul  
- **Enterprise**: System-wide changes

### 4. Understanding Results
How to read SmartIssueAgent output and next steps.

### 5. Advanced Usage
- Creating issues that decompose well
- Understanding the 12-Factor principles applied
- Custom agent assignment

## Implementation Requirements

### Files to Create
- `docs/USER-GUIDE.md` - Main actionable guide
- `examples/issue-examples/` - Working example issues

### Content Standards
- Every example must be copy-pastable and work immediately
- No theoretical explanations without practical application
- Maximum 5 minutes to productive use
- Include actual command outputs
- Test all examples before publication

## Definition of Done
- [ ] USER-GUIDE.md created with working examples
- [ ] All examples tested and verified working
- [ ] Guide takes user from 0 to productive in <5 minutes
- [ ] No fluff or unnecessary explanations
- [ ] Examples cover all complexity levels

## Type
documentation

## Priority
high

## Status
open

## Assignee
smart_issue_agent