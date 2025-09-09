# Issue #226: Phase 3 - Restore Async Orchestration to SmartIssueAgent

## Description
**Performance Critical**: Integrate the proven HierarchicalOrchestrator into SmartIssueAgent to restore parallel processing, load balancing, and sophisticated coordination patterns.

## Current Problem
SmartIssueAgent processes sub-issues **sequentially** (one by one), making complex issues with multiple sub-tasks extremely slow:

```python
# CURRENT: Slow sequential processing
for sub_issue in sub_issues:
    result = agent.execute_task(issue_num)  # Waits for each to complete
```

## Target Solution
Restore the **parallel orchestration** that made the old system "work very quickly":

```python
# TARGET: Fast parallel orchestration
async def process_complex_issue(self, issue):
    orchestrator = HierarchicalOrchestrator()
    result = await orchestrator.orchestrate_complex_task(issue)
    # All independent sub-issues run in parallel!
```

## Implementation Plan

### **Step 1: Connect SmartIssueAgent to HierarchicalOrchestrator**
```python
class SmartIssueAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.orchestrator = HierarchicalOrchestrator()
        
    async def execute_complex_task(self, issue_data):
        # Route complex issues to orchestrator
        if complexity == "complex" or complexity == "enterprise":
            return await self.orchestrator.orchestrate_complex_task(...)
```

### **Step 2: Enable Orchestration Patterns**
- [ ] **MapReduce**: For issues with multiple similar subtasks
- [ ] **Pipeline**: For sequential dependencies  
- [ ] **Fork-Join**: For independent parallel tasks
- [ ] **Scatter-Gather**: For broadcast to multiple agents
- [ ] **Saga**: For transactional coordination

### **Step 3: Pattern Selection Intelligence**
```python
def select_orchestration_pattern(self, task_analysis):
    if "parallel" in keywords or independent_tasks:
        return OrchestrationPattern.FORK_JOIN
    elif "sequential" in keywords or has_dependencies:
        return OrchestrationPattern.PIPELINE
    elif "aggregate" in keywords or needs_collection:
        return OrchestrationPattern.MAPREDUCE
    # etc...
```

### **Step 4: Load Balancing**
```python
# Distribute work based on agent capacity
agents = self.get_available_agents()
distribution = self.workload_distributor.distribute(
    tasks=sub_issues,
    agents=agents, 
    strategy="least_loaded"  # or "round_robin", "capability_based"
)
```

## Performance Improvements Expected

| Metric | Current (Sequential) | Target (Orchestrated) | Improvement |
|--------|---------------------|----------------------|-------------|
| 3 Independent Tasks | 30 seconds | 10 seconds | **3x faster** |
| 5 Independent Tasks | 50 seconds | 10 seconds | **5x faster** |
| 10 Mixed Tasks | 100 seconds | 25 seconds | **4x faster** |

## Success Criteria
- [ ] Complex issues use HierarchicalOrchestrator
- [ ] Independent sub-issues run in parallel
- [ ] Load balancing distributes work across agents
- [ ] Orchestration patterns selected intelligently
- [ ] Performance improvement of 3-5x for complex issues

## Test Scenarios
1. **Parallel Test**: Issue with 5 independent sub-tasks → All run simultaneously
2. **Pipeline Test**: Issue with sequential dependencies → Proper ordering maintained
3. **Load Balance Test**: 10 tasks, 3 agents → Work distributed evenly
4. **Pattern Selection**: Different issue types → Correct pattern selected

## Integration Requirements
- [ ] Maintain backward compatibility with current SmartIssueAgent interface
- [ ] Preserve intelligent complexity analysis
- [ ] Keep circuit breaker and failure analysis
- [ ] Add performance metrics tracking

## Dependencies
- **Prerequisites**: Issue #224 & #225 (Agents must work first)
- **Uses**: Existing `core/hierarchical_orchestrator.py`
- **Parent Epic**: Issue #223 (Hybrid Architecture Master Plan)

## Priority
**High** - Major performance improvement

## Type
performance

## Status
open

## Assignee
orchestration_team

## Labels
phase-3, performance, orchestration, parallel-processing