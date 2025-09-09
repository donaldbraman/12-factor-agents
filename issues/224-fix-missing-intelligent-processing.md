# Issue #224: Phase 1 - Add `_intelligent_processing` to BaseAgent Class

## Description
**Critical Infrastructure Fix**: Add the `_intelligent_processing` method to the `BaseAgent` class so all agents inherit intelligent contextual processing capabilities.

**Impact**: Currently 13 out of 14 agents are missing this method, causing AttributeError failures when SmartIssueAgent tries to execute sub-issues.

## Root Cause
During migration from regex patterns to intelligent processing, the method was only added to `IssueFixerAgent` but not made available to all agents via inheritance.

**Test Evidence:**
```
⚠️ AGENTS MISSING _intelligent_processing:
   - smart_issue_agent.py
   - code_review_agent.py  
   - testing_agent.py
   - [and 10 more...]
```

## Implementation Plan

### **Note: Cannot Roll Back - This is New Functionality**
The `_intelligent_processing` method was never in BaseAgent or other agents. It only exists in IssueFixerAgent (added in commit cd3cd66).

### **Add to BaseAgent (core/agent.py):**
```python
from pathlib import Path
from typing import Dict, Any

class BaseAgent:
    def _intelligent_processing(self, issue_path: Path, issue_data: Dict[str, Any]) -> ToolResponse:
        """
        Base intelligent processing for contextual issues.
        Provides default implementation that agents can override.
        """
        # Copy implementation from agents/issue_fixer_agent.py
        # Lines 386-809 contain the full implementation
        # Make it generic enough for all agents to use
```

### **Core Method Capabilities:**
- [ ] Extract file mentions from natural language
- [ ] Detect creation needs (create, add, new, implement, build)
- [ ] Detect modification needs (update, fix, change, modify)
- [ ] Generate appropriate file content based on context
- [ ] Provide fallback for unknown/unsupported operations

### **Default Behavior:**
- [ ] If agent can't handle task, return clear error (not AttributeError)
- [ ] Log what type of task was attempted for debugging
- [ ] Suggest which agent type might be better suited

## Success Criteria
- [ ] `_intelligent_processing` method exists in BaseAgent
- [ ] All agents inherit the method automatically
- [ ] No more AttributeError when calling missing method
- [ ] Default implementation handles basic file operations
- [ ] Agents can still override for specialization

## Test Validation
```python
# This should work for ALL agents:
agent = AnyAgent()
result = agent._intelligent_processing(issue_path, issue_data)
assert hasattr(result, 'success')  # Returns ToolResponse, not AttributeError
```

## Dependencies
- **Parent Epic**: Issue #223 (Hybrid Architecture Master Plan)
- **Blocks**: Issue #225 (Phase 2 - Agent Specialization)

## Priority
**Critical** - Immediate blocker for multi-agent workflows

## Type
bug

## Status
open

## Assignee
infrastructure_team

## Labels
critical, phase-1, infrastructure, base-agent