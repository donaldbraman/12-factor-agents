# Issue #228: User Guide References Non-Existent Agents

## Problem
The ROLLBACK_USER_GUIDE.md references agents that don't exist in the rollback-to-stable branch, causing confusion for users.

## Issues Found During Testing

### 1. Wrong Agent Names
The guide references:
- ❌ `IssueFixerAgent` - doesn't exist
- ❌ `IssueDecomposerAgent` - doesn't exist  
- ❌ `RefactoringAgent` - doesn't exist
- ❌ `QAAgent` - doesn't exist

Actual agents available:
- ✅ `IssueProcessorAgent` - processes issues
- ✅ `IssueOrchestratorAgent` - orchestrates issue workflows
- ✅ `SimpleIssueCloser` - closes resolved issues
- ✅ `CodeReviewAgent` - reviews code
- ✅ `TestingAgent` - generates tests
- ✅ `ComponentMigrationAgent` - migrates components
- ✅ `EnhancedWorkflowAgent` - complex workflows
- ✅ `RepositorySetupAgent` - sets up repos
- ✅ `PromptManagementAgent` - manages prompts
- ✅ `EventSystemAgent` - event handling
- ✅ `UvMigrationAgent` - UV migrations

### 2. No Dependency Installation Needed
Users don't need to install anything in their projects. The symlinks provide everything needed. The guide should clarify this.

### 3. Test Command Errors
The test command in Step 3 uses wrong imports:
```python
# WRONG (in guide)
from .agents.agents.issue_fixer_agent import IssueFixerAgent

# CORRECT
from agents.issue_processor_agent import IssueProcessorAgent
```

## Fixes Needed

### Update Step 3 Test
```python
# Quick test in your project
cd your-project
uv run python -c "
import sys
sys.path.insert(0, '.agents')
from core.hierarchical_orchestrator import HierarchicalOrchestrator
from agents.issue_processor_agent import IssueProcessorAgent
print('✅ Agents are working!')
"
```

### Update Agent List
Replace the incorrect agent list with the actual available agents.

### Update Usage Examples
Replace all `IssueFixerAgent` references with `IssueProcessorAgent`.

### Clarify Dependencies
Add note: "No installation needed in your project - symlinks provide everything."

## Testing Performed
1. ✅ Switched to rollback-to-stable branch
2. ✅ Verified symlinks exist in pin-citer
3. ✅ Tested imports - found wrong agent names
4. ✅ Listed actual available agents
5. ✅ Confirmed working with correct names

## Priority
**HIGH** - Users can't follow the guide successfully

## Type
documentation

## Labels
bug, documentation, user-guide, rollback-branch