# Issue #099: Comprehensive pipeline state management across agent operations

## Problem
State is currently fragmented across the agent pipeline. When an issue goes through multiple stages (modify → review → test → retry), there's no unified state management system. This causes:
- Loss of context between stages
- No memory of previous attempts
- Can't track what's been tried
- No learning from failures
- Duplicate work across retries

## Current State Management (Fragmented)
```
1. ExecutionContext - Basic repo/path info only
2. Return values - Each agent returns dict, but not preserved
3. File system - .claude-shared-state (crude persistence)
4. Telemetry - Write-only event log
```

## The Complete Pipeline & State Needs

### Stage 1: Issue Submission (Sister Repo → Sparky)
**Current State:**
- ExecutionContext created with repo info
- Issue content passed as string

**Missing State:**
- Previous attempts on this issue
- Related issues already fixed
- Repository-specific patterns/preferences

### Stage 2: Agent Selection (Sparky → Agent)
**Current State:**
- Agent name selected
- Task passed as string

**Missing State:**
- Why this agent was selected
- Alternative agents if this fails
- Confidence score in selection

### Stage 3: Implementation (Agent Work)
**Current State:**
- Files modified returned in dict
- Lines changed count

**Missing State:**
- Reasoning for each change
- Alternatives considered
- Confidence in fixes
- Patterns detected

### Stage 4: Code Review
**Current State:**
- None (not implemented)

**Needed State:**
- Review findings
- Severity of issues
- Suggested fixes
- Quality metrics

### Stage 5: Testing
**Current State:**
- None (not implemented)

**Needed State:**
- Test results
- Failed test output
- Coverage changes
- Performance impact

### Stage 6: Retry on Failure
**Current State:**
- No memory of previous attempt
- Start from scratch

**Needed State:**
- Previous attempts
- What failed and why
- Strategies already tried
- Test/review feedback

## Proposed Solution: PipelineState Class

```python
@dataclass
class PipelineState:
    """Unified state management for agent pipeline"""
    
    # Identity
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    issue_id: str = None
    workflow_id: str = None
    
    # Context
    execution_context: ExecutionContext = None
    original_task: str = None
    current_stage: str = "submitted"  # submitted|routing|implementing|reviewing|testing|complete|failed
    
    # Agent History
    agent_attempts: List[AgentAttempt] = field(default_factory=list)
    current_agent: str = None
    agent_selection_reasoning: str = None
    
    # Modifications
    files_modified: Dict[str, List[FileModification]] = field(default_factory=dict)
    total_changes: int = 0
    
    # Review State
    review_results: List[ReviewResult] = field(default_factory=list)
    review_passed: bool = None
    review_findings: List[Dict] = field(default_factory=list)
    
    # Test State
    test_results: List[TestResult] = field(default_factory=list)
    test_passed: bool = None
    test_output: str = None
    failed_tests: List[str] = field(default_factory=list)
    
    # Retry State
    retry_count: int = 0
    max_retries: int = 3
    strategies_tried: List[str] = field(default_factory=list)
    failure_patterns: List[str] = field(default_factory=list)
    
    # Learning
    successful_patterns: List[Dict] = field(default_factory=list)
    avoided_pitfalls: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = None
    duration_seconds: float = 0.0
    
    def add_attempt(self, agent: str, result: Dict):
        """Record an agent attempt"""
        self.agent_attempts.append(AgentAttempt(
            agent=agent,
            timestamp=datetime.now(),
            result=result,
            success=result.get("success", False)
        ))
        
    def add_review_finding(self, finding: Dict):
        """Add a code review finding"""
        self.review_findings.append(finding)
        
    def add_test_failure(self, test_name: str, output: str):
        """Record a test failure"""
        self.failed_tests.append(test_name)
        if self.test_output:
            self.test_output += f"\n{output}"
        else:
            self.test_output = output
            
    def should_retry(self) -> bool:
        """Determine if we should retry"""
        return self.retry_count < self.max_retries
        
    def get_next_strategy(self) -> str:
        """Determine next retry strategy based on history"""
        if "syntax_fix" not in self.strategies_tried:
            return "syntax_fix"
        elif "refactor" not in self.strategies_tried:
            return "refactor"
        elif "simplify" not in self.strategies_tried:
            return "simplify"
        return "escalate"
        
    def to_context_dict(self) -> Dict:
        """Convert state to context for agent consumption"""
        return {
            "previous_attempts": len(self.agent_attempts),
            "files_already_modified": list(self.files_modified.keys()),
            "test_failures": self.failed_tests,
            "review_findings": self.review_findings,
            "strategies_tried": self.strategies_tried,
            "retry_count": self.retry_count
        }
```

## Integration Points

### 1. IssueOrchestratorAgent
```python
def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
    # Create pipeline state
    state = PipelineState(
        issue_id=self._extract_issue_id(task),
        execution_context=context,
        original_task=task
    )
    
    # Route through pipeline with state
    return self._execute_pipeline(state)
    
def _execute_pipeline(self, state: PipelineState):
    # Each stage updates state
    state.current_stage = "routing"
    agent = self._select_agent(state)
    
    state.current_stage = "implementing"
    result = self._run_agent(agent, state)
    
    if result.get("files_modified"):
        state.current_stage = "reviewing"
        review_result = self._run_review(state)
        
        if review_result["passed"]:
            state.current_stage = "testing"
            test_result = self._run_tests(state)
            
            if not test_result["passed"] and state.should_retry():
                state.retry_count += 1
                state.current_stage = "retrying"
                return self._retry_with_feedback(state)
```

### 2. IntelligentIssueAgent
```python
def execute_task(self, task: str, context: ExecutionContext = None, 
                 pipeline_state: PipelineState = None):
    # Use pipeline state for context
    if pipeline_state:
        # Learn from previous attempts
        self._analyze_previous_attempts(pipeline_state)
        
        # Adjust strategy based on feedback
        strategy = self._select_strategy_from_state(pipeline_state)
        
        # Apply fixes with awareness of history
        result = self._apply_contextual_fixes(task, pipeline_state)
        
        # Update state with our attempt
        pipeline_state.add_attempt(self.__class__.__name__, result)
```

## Benefits
1. **Complete context preservation** across all stages
2. **Learning from failures** - agents know what's been tried
3. **Intelligent retry strategies** - based on failure patterns
4. **Audit trail** - full history of attempts
5. **Metrics and insights** - success rates, patterns, bottlenecks
6. **Resumable pipelines** - can restart from any stage
7. **Debugging support** - full state visibility

## Success Criteria
- [ ] PipelineState class implemented
- [ ] All agents accept and update pipeline state
- [ ] State persisted across retries
- [ ] State accessible for debugging
- [ ] Metrics derived from state
- [ ] Learning patterns extracted from state

## Priority
Critical - This is foundational for reliable multi-stage agent operations

## Agent Assignment
IssueOrchestratorAgent (primary), All agents (integration)