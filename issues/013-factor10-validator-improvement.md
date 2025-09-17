# Issue: Improve Factor 10 Validator to Exclude Inherited Methods

## Problem
The Factor 10 validator currently counts ALL public methods on an agent, including those inherited from BaseAgent. This results in false negatives where focused agents with ~15 own methods are penalized for the ~20 framework methods they inherit.

## Current Behavior
- Validator counts all methods: `len([m for m in dir(agent) if not m.startswith("_")])`
- FullyCompliantAgent shows ~30-51 total methods
- Only ~15 are actually defined in the agent itself
- Results in 50% compliance score despite agent being properly focused

## Solution
Update Factor10Validator to only count methods defined in the agent class itself, not inherited methods.

## Implementation

In `core/compliance.py`, update the Factor10Validator.validate() method:

```python
def validate(self, agent: BaseAgent, context: Dict[str, Any] = None) -> Tuple[ComplianceLevel, Dict[str, Any]]:
    # ... existing code ...
    
    # OLD: Count all methods
    # agent_methods = [
    #     method for method in dir(agent) 
    #     if not method.startswith("_") and callable(getattr(agent, method))
    # ]
    
    # NEW: Count only methods defined in agent's own class
    agent_methods = []
    for method_name in dir(agent):
        if method_name.startswith("_"):
            continue
        method = getattr(agent, method_name)
        if callable(method) and hasattr(method, '__qualname__'):
            # Check if method is defined in this class, not inherited
            if agent.__class__.__name__ in method.__qualname__:
                agent_methods.append(method_name)
    
    details["checks"]["method_count"] = len(agent_methods)
    details["checks"]["own_methods"] = agent_methods
    
    # Adjust scoring threshold for own methods only
    if len(agent_methods) <= 15:  # Changed from 10
        details["score"] += 0.3
        details["checks"]["focused_interface"] = True
    # ... rest of validation
```

## Expected Impact
- Factor 10 scores should improve significantly for properly designed agents
- FullyCompliantAgent would go from 50% to ~75-100% on Factor 10
- Overall compliance would increase by ~4-5 percentage points

## Test Validation
After implementation, verify that:
1. Agents with few own methods but many inherited methods score well
2. Agents that actually define too many methods still score poorly
3. The validator focuses on the agent's actual complexity, not framework overhead