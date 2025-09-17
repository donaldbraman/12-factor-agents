# Context Recovery Prompt for 12-Factor Validators Implementation

## SITUATION OVERVIEW
You are implementing 12-factor compliance validators for the 12-factor-agents codebase. This is a systematic effort to achieve 100% compliance with agent system best practices.

## CURRENT STATUS: Week 1, Day 1 - Factor 12 ✅ COMPLETED

### What Was Just Accomplished
- ✅ **Factor 12 Validator (Stateless Reducer)** - FULLY IMPLEMENTED
- ✅ Created Factor12Validator class in core/compliance.py
- ✅ Built @stateless decorator in core/stateless.py  
- ✅ Comprehensive test suite in tests/test_factor12_compliance.py
- ✅ Updated issue #007h to COMPLETED status
- ✅ Committed and pushed to branch `implement-factor-validators`
- ✅ Progress: 5/12 validators (42% → 50% compliance)

### Repository State
- **Current Branch**: `implement-factor-validators` 
- **Last Commit**: "Implement Factor 12 Validator: Stateless Reducer" (04552bd)
- **Remote**: Pushed and up-to-date
- **Working Directory**: Clean

## NEXT TASK: Factor 4 Validator (Structured Outputs)

### Why Factor 4 is Next
- **High Priority**: Affects ALL tools in the system
- **Architectural Impact**: Standardizes tool response formats
- **Dependency**: Other validators may rely on consistent tool outputs

### Factor 4 Requirements
**Principle**: "Tools are Structured Outputs"
**Goal**: All tools should have predictable, consistent output formats

**Validation Criteria** (4 checks × 0.25 points each):
1. **Response Consistency**: All tools return ToolResponse objects
2. **Schema Compliance**: Tools define and match output schemas  
3. **Error Handling**: Consistent error response patterns
4. **Documentation**: Each tool documents its output format

### Implementation Steps
1. **Add Factor4Validator class** to core/compliance.py (before ComplianceAuditor)
2. **Register validator** in ComplianceAuditor.__init__ (add line: `4: Factor4Validator(),`)
3. **Create test file** tests/test_factor4_compliance.py
4. **Update issue status** issues/007b-factor4-structured-outputs-validator.md
5. **Commit and push** with clear message
6. **Move to next validator** (Factor 8 - Control Flow)

## VALIDATOR IMPLEMENTATION TEMPLATE

```python
class Factor4Validator(FactorValidator):
    """Factor 4: Tools are Structured Outputs"""

    def __init__(self):
        super().__init__(4, "Tools are Structured Outputs")

    def validate(
        self, agent: BaseAgent, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceLevel, Dict[str, Any]]:
        """
        Validate that all tools have structured, predictable outputs.
        """
        details = {
            "factor": self.factor_name,
            "checks": {},
            "score": 0.0,
            "issues": [],
            "recommendations": [],
        }

        # Check 1: All tools return ToolResponse (0.25 points)
        tools_return_toolresponse = True
        if agent.tools:
            for tool in agent.tools:
                # Analyze tool implementation
                # Check if execute method returns ToolResponse
                pass
        
        details["checks"]["tools_return_toolresponse"] = tools_return_toolresponse
        if tools_return_toolresponse:
            details["score"] += 0.25

        # Check 2: Schema compliance (0.25 points)
        # Check 3: Error handling patterns (0.25 points)  
        # Check 4: Output documentation (0.25 points)

        # Provide recommendations
        if details["score"] < 1.0:
            # Add specific recommendations based on failures

        # Determine compliance level
        if details["score"] >= 0.9:
            compliance = ComplianceLevel.FULLY_COMPLIANT
        elif details["score"] >= 0.75:
            compliance = ComplianceLevel.MOSTLY_COMPLIANT
        elif details["score"] >= 0.5:
            compliance = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            compliance = ComplianceLevel.NON_COMPLIANT

        return compliance, details
```

## TESTING PATTERN

Create tests/test_factor4_compliance.py with:
- **CompliantToolAgent**: Example with proper ToolResponse usage
- **ViolatingToolAgent**: Example with inconsistent outputs
- **PartiallyCompliantAgent**: Mixed compliance
- **Test methods**: test_fully_compliant, test_violating, test_partial, test_recommendations, test_edge_cases

## REMAINING VALIDATORS (Priority Order)

### Next 7 to Implement:
1. **🚧 Factor 4**: Tools are Structured Outputs (IN PROGRESS)
2. **Factor 8**: Own Your Control Flow (HIGH - affects agent structure)
3. **Factor 3**: Own Your Context Window (MEDIUM)
4. **Factor 5**: Unify Execution & Business State (MEDIUM)
5. **Factor 7**: Contact Humans with Tool Calls (MEDIUM)
6. **Factor 9**: Compact Errors into Context Window (MEDIUM)
7. **Factor 11**: Trigger from Anywhere (LOW)

### Already Implemented (5/12):
- ✅ Factor 1: Natural Language to Tool Calls
- ✅ Factor 2: Own Your Prompts  
- ✅ Factor 6: Launch/Pause/Resume with Simple APIs
- ✅ Factor 10: Small, Focused Agents
- ✅ Factor 12: Stateless Reducer (JUST COMPLETED)

## CRITICAL FILES TO KNOW

### Core Implementation
- **core/compliance.py**: Main validator implementations (Factor12Validator just added)
- **core/tools.py**: ToolResponse class definition (important for Factor 4)
- **core/agent.py**: BaseAgent class with abstract methods

### Issue Tracking
- **issues/007b-factor4-structured-outputs-validator.md**: Next issue to work on
- **issues/MASTER-12-FACTOR-COMPLIANCE.md**: Overall progress tracking
- **PROJECT_STATUS_SUMMARY.md**: Detailed project status

### Testing
- **tests/test_factor12_compliance.py**: Template for other validator tests
- Test pattern: CompliantAgent, ViolatingAgent, PartiallyCompliantAgent

## WORKFLOW COMMANDS

```bash
# Check current status
git status
git branch --show-current  # Should be: implement-factor-validators

# Test current compliance
uv run python -c "
from core.compliance import ComplianceAuditor
from agents.smart_issue_agent import SmartIssueAgent
auditor = ComplianceAuditor()
agent = SmartIssueAgent()
report = auditor.audit_agent(agent)
print(f'Overall compliance: {report[\"overall_compliance\"]}')
print(f'Validators available: {list(auditor.validators.keys())}')
"

# Test specific validator
uv run python tests/test_factor12_compliance.py

# After implementing Factor 4
git add -A
git commit -m "Implement Factor 4 Validator: Structured Outputs"
git push origin implement-factor-validators
```

## SPARKY ASSESSMENT (IMPORTANT)

**Sparky Status**: 🏥 NEEDS VET CARE
- ✅ Can handle simple code additions
- ❌ Can't handle complex validator implementations
- ❌ Code placement issues (appends instead of inserting properly)
- ❌ Can't find issues with non-numeric prefixes (007a, 007b, etc.)

**Decision**: Manual implementation required for all validators.

## USER PREFERENCES & CONSTRAINTS

- **Commit Strategy**: Commit and push after EVERY validator (user requested)
- **Implementation Style**: Systematic, one-by-one approach
- **Code Quality**: Pre-commit hooks must pass (black, ruff, tests)
- **Documentation**: Update issue status and project tracking files

## SUCCESS METRICS

- **Week 1 Target**: 60% compliance (7/12 factors) 
- **Week 2 Target**: 80% compliance (10/12 factors)
- **Final Target**: 100% compliance (12/12 factors)

## IMMEDIATE NEXT STEPS

1. **Read** issues/007b-factor4-structured-outputs-validator.md for requirements
2. **Implement** Factor4Validator class in core/compliance.py
3. **Add** validator to ComplianceAuditor.validators dictionary  
4. **Create** comprehensive test suite
5. **Test** implementation thoroughly
6. **Update** issue status to COMPLETED
7. **Commit and push** with clear message
8. **Move to** Factor 8 (Control Flow) next

## MOTIVATION

This systematic implementation is critical for:
- **Code Quality**: Enforcing best practices across all agents
- **Maintainability**: Consistent patterns for future development  
- **Reliability**: Predictable behavior in production systems
- **Team Onboarding**: Clear compliance standards for new developers

---

**You are currently at**: Factor 12 ✅ COMPLETED → Factor 4 🚧 NEXT
**Progress**: 5/12 validators implemented (50% compliance achieved!)
**Branch**: implement-factor-validators (clean, up-to-date)
**Ready to implement Factor 4 Validator (Structured Outputs)**