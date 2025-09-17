# PHASE 2: Refactoring for Compliance

## Parent Issue
#MASTER-12-FACTOR-COMPLIANCE

## Overview
Clean up existing violations and improve compliance across the codebase.

## Timeline
Target: 1 week (after Phase 1)

## Prerequisites
- [ ] Phase 1 complete
- [ ] All validators implemented
- [ ] Compliance baseline established

## Issues in this Phase

### Week 2 Sprint
**Day 1-2: Prompt Externalization**
- [ ] #008: Externalize hardcoded prompts
  - Move all prompts to prompts/agents/
  - Update agents to use format_prompt()
  - Create prompt versioning system

**Day 3: Error Compaction**
- [ ] #009: Improve error compaction
  - Create error_compaction.py utility
  - Update all agents to use compacted errors
  - Add error pattern recognition

**Day 4-5: Agent Splitting**
- [ ] #011: Split large agents
  - Break down intelligent_issue_agent.py
  - Refactor issue_fixer_agent.py
  - Ensure each agent <200 lines

## Refactoring Priority
1. **High Impact Files** (most violations)
   - agents/intelligent_issue_agent.py (1155 lines!)
   - agents/issue_fixer_agent.py (500+ lines)
   - agents/issue_orchestrator_agent.py

2. **Core Infrastructure**
   - core/tools.py (standardize responses)
   - core/agent.py (add validation hooks)

3. **Supporting Files**
   - Update tests for refactored code
   - Update documentation

## Migration Strategy
```python
# Before: Hardcoded prompt
prompt = f"Analyze this issue: {issue_title}\n{issue_body}"

# After: Externalized prompt
prompt = format_prompt("agents/issue_analyzer",
                      issue_title=issue_title,
                      issue_body=issue_body)
```

## Success Criteria
- [ ] Zero hardcoded prompts in agents/
- [ ] All errors compacted to <100 chars
- [ ] No agent exceeds 200 lines
- [ ] All tools return standardized ToolResponse
- [ ] Compliance audit shows >85% overall compliance

## Testing After Refactoring
```bash
# Verify no functionality broken
uv run pytest tests/

# Check compliance improvement
uv run python core/compliance.py audit --before-after

# Validate all agents still work
uv run python scripts/validate_all_agents.py
```

## Risks & Mitigation
- **Risk**: Breaking existing functionality
  - **Mitigation**: Comprehensive test coverage before refactoring
  
- **Risk**: Performance degradation
  - **Mitigation**: Benchmark before/after

## Notes
- Use feature branches for each major refactoring
- Get code review before merging
- Update tests alongside refactoring
- Document breaking changes

## Tracking
Label: `phase-2-refactoring`
Milestone: `Phase 2: Refactoring`