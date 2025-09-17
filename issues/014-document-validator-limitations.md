# Issue: Document Known Validator Limitations in README

## Problem
The 12-factor validators have some known limitations that cause false negatives. These should be documented so users understand when low scores may not indicate actual problems.

## Documentation Needed

Add a new section to README.md:

```markdown
## Known Validator Limitations

The 12-factor compliance validators are comprehensive but have some known limitations that may cause false negatives:

### Factor 2: Own Your Prompts (70% typical)
**False Negative**: Detects environment variable fallback strings as "hardcoded"
- Example: `os.getenv("PROMPT_START", "Starting: {task}")` 
- The fallback string is flagged even though it's a best practice
- **Reality**: Agents using PromptManager with fallbacks ARE compliant

### Factor 7: Contact Humans with Tool Calls (75% possible)
**Validation Issue**: May not recognize all valid tool patterns
- Tools that return ToolResponse and have proper error handling may still score <100%
- Validator has overly specific expectations about implementation details
- **Reality**: If human interaction tools exist and work, the agent IS compliant

### Factor 10: Small, Focused Agents (50% typical)
**Inheritance Counting**: Counts ALL methods including inherited from BaseAgent
- An agent with only 15 own methods shows ~30-50 total methods
- BaseAgent provides ~20 necessary framework methods
- **Reality**: Agents with <20 own methods ARE properly focused

### Factor 11: Trigger from Anywhere (naming sensitivity)
**Method Naming**: Validator looks for specific method names
- Fixed to recognize both `get_triggers()` and `get_trigger_info()`
- May not recognize other valid documentation method names
- **Reality**: If trigger documentation exists, the agent IS compliant

## Practical Compliance

Due to these limitations, consider:
- **90%+ compliance**: Excellent, essentially fully compliant
- **85-90% compliance**: Very good, likely has only validator false negatives
- **80-85% compliance**: Good, may have minor real issues or multiple false negatives
- **<80% compliance**: Needs improvement in actual compliance

The validators are guides to help ensure best practices, not absolute arbiters of code quality.
```

## Additional Documentation

Also update the compliance audit output to note when common false negatives are detected:

```python
# In ComplianceAuditor.audit_agent(), add context about known limitations
if report["overall_score"] >= 0.85:
    report["note"] = "Score >85% indicates strong compliance. Lower scores on Factors 2, 7, 10, or 11 may be false negatives. See README for details."
```

## Benefits
- Sets proper expectations about validator limitations
- Helps users understand when "non-compliance" isn't actually a problem
- Documents the practical vs. theoretical compliance distinction
- Reduces confusion about inheritance and naming issues