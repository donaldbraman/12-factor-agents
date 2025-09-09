# Issue #206: Fix Async Orchestration Bug in IntelligentIssueAgent

## Problem
During dogfooding of issue #205, we discovered that complex issues processed by IntelligentIssueAgent produce a RuntimeWarning:

```
RuntimeWarning: coroutine 'HierarchicalOrchestrator.orchestrate_complex_task' was never awaited
```

This prevents complex issues from being properly orchestrated and results in no actual work being performed.

## Root Cause Analysis
The issue occurs in `agents/intelligent_issue_agent.py` at line 258:

```python
def _handle_complex_issue(self, intent: Dict) -> ToolResponse:
    # Convert intent to subtasks for orchestrator
    subtasks = self._decompose_to_subtasks(intent)
    
    # BUG: This line calls async method without await
    result = self.orchestrator.orchestrate_complex_task({
        "description": intent["raw_content"], 
        "subtasks": subtasks
    })
```

The `HierarchicalOrchestrator.orchestrate_complex_task()` method is async, but we're calling it from a sync method without proper async handling.

## Solution Options

### Option 1: Make IntelligentIssueAgent Async (Recommended)
Convert the agent to support async operations:

```python
class IntelligentIssueAgent(BaseAgent):
    async def execute_task(self, task: str) -> ToolResponse:
        # ... existing logic ...
        if intent["complexity"] == "simple":
            return self._handle_simple_issue(intent)
        else:
            return await self._handle_complex_issue(intent)
    
    async def _handle_complex_issue(self, intent: Dict) -> ToolResponse:
        subtasks = self._decompose_to_subtasks(intent)
        result = await self.orchestrator.orchestrate_complex_task({
            "description": intent["raw_content"],
            "subtasks": subtasks
        })
        return ToolResponse(success=True, data={...})
```

### Option 2: Sync Wrapper for Orchestrator
Create a sync wrapper that runs async code:

```python
import asyncio

def _handle_complex_issue(self, intent: Dict) -> ToolResponse:
    subtasks = self._decompose_to_subtasks(intent)
    
    # Run async code in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(
        self.orchestrator.orchestrate_complex_task({
            "description": intent["raw_content"],
            "subtasks": subtasks
        })
    )
    
    return ToolResponse(success=True, data={...})
```

## Requirements

1. **Fix the async warning** - No more RuntimeWarnings
2. **Maintain backward compatibility** - Don't break existing sync code
3. **Test both simple and complex issues** - Ensure both work
4. **Update CLI wrapper if needed** - Handle async calls from command line

## Files to Modify

### Primary Changes
- `agents/intelligent_issue_agent.py` - Fix async handling
- `bin/agent.py` - Update CLI to handle async if needed

### Testing
- `tests/test_intelligent_issue_agent.py` - Add async tests
- Add test for complex issue orchestration

## Test Cases

### 1. Simple Issue (Should Still Work)
```python
def test_simple_issue_sync():
    agent = IntelligentIssueAgent()
    result = agent.execute_task("Create a test file at test.py")
    assert result.success == True
```

### 2. Complex Issue (Should Work Without Warning)
```python 
async def test_complex_issue_async():
    agent = IntelligentIssueAgent()
    result = await agent.execute_task(
        "Fix bugs in auth.py, create tests, and update docs"
    )
    assert result.success == True
    assert "orchestration_result" in result.data
```

### 3. No Runtime Warnings
```python
import warnings

def test_no_async_warnings():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        agent = IntelligentIssueAgent()
        # This should not produce warnings
        result = process_complex_issue(agent)
        
        # Check no RuntimeWarnings about coroutines
        runtime_warnings = [warn for warn in w 
                          if issubclass(warn.category, RuntimeWarning)
                          and "coroutine" in str(warn.message)]
        assert len(runtime_warnings) == 0
```

## Implementation Steps

1. **Choose approach** - Decide between Option 1 (full async) or Option 2 (sync wrapper)
2. **Update IntelligentIssueAgent** - Fix the async handling
3. **Test simple issues** - Ensure backward compatibility
4. **Test complex issues** - Verify orchestration works
5. **Update CLI if needed** - Handle async from command line
6. **Run comprehensive tests** - No warnings, full functionality

## Success Criteria

1. ✅ **No RuntimeWarnings** about unawaited coroutines
2. ✅ **Complex issues work** - Orchestration actually happens
3. ✅ **Simple issues still work** - Backward compatibility maintained
4. ✅ **Tests pass** - All existing tests continue to pass
5. ✅ **Dogfooding works** - Issue #205 can be fully processed

## Testing the Fix

After implementation, test with the exact scenario that revealed the bug:

```bash
# This should work without warnings
uv run python -c "
import sys
sys.path.insert(0, 'agents')
sys.path.insert(0, 'core')

from agents.intelligent_issue_agent import IntelligentIssueAgent

agent = IntelligentIssueAgent()
result = agent.execute_task('Process issues/205-error-telemetry-system.md')

print(f'Success: {result.success}')
print(f'Complex issue handled: {\"orchestration_result\" in result.data}')
"
```

Expected output:
- No RuntimeWarning
- Success: True  
- Complex issue handled: True

---

**Type**: bug
**Priority**: high
**Assignee**: IntelligentIssueAgent
**Labels**: async, orchestration, bug-fix

**Discovered during**: Dogfooding issue #205
**Impact**: Complex issues fail silently