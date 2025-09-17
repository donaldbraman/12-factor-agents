# Issue #115: Tight Coupling - No Agent Registry

## Problem
Agents are tightly coupled with hardcoded references to each other. There's no service registry or discovery mechanism, making the system brittle and hard to extend.

## Current Behavior
- Agents import each other directly
- Hardcoded agent names in code
- No dynamic discovery
- No interface contracts
- Circular dependencies possible
- Cannot add new agents without modifying existing code

## Expected Behavior
- Central agent registry for discovery
- Agents register their capabilities
- Dynamic agent lookup by capability
- Interface contracts/schemas
- Loose coupling through interfaces
- Plugin-style agent addition

## Example Problems
```python
# Current - Hardcoded
from agents.issue_fixer_agent import IssueFixerAgent
fixer = IssueFixerAgent()

# Desired - Registry based
fixer = agent_registry.get_agent("issue_fixer")
# or
fixer = agent_registry.get_agent_by_capability("fix_issues")
```

## Implementation Ideas
- Create AgentRegistry class
- Agents register on initialization
- Capability-based discovery
- Interface validation
- Dependency injection
- Event-based communication option

## Files Affected
- `core/agent_registry.py` - New registry implementation
- `core/agent.py` - Registration interface
- `core/agent_executor.py` - Use registry for discovery
- All agent files - Remove direct imports

## Priority
MEDIUM - Architectural improvement

## Success Criteria
- [ ] Central agent registry implemented
- [ ] Agents self-register with capabilities
- [ ] Dynamic agent discovery
- [ ] No direct agent imports
- [ ] Interface contract validation
- [ ] Tests for registration and discovery
- [ ] Documentation for adding new agents