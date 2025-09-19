# SPARKY Technical Reference

## Versions

| Version | Lines | Key Feature | Factor |
|---------|-------|-------------|---------|
| 1.0 | 94 | Lean core | - |
| 2.0 | 220 | Context awareness | 3 |
| 3.0 | 285 | Git pipeline | - |
| 4.0 | 200 | Structured outputs | 4 |
| 5.0 | 400 | Prompt-driven | 2 |
| 6.0 | 600 | Async/pause/resume | 6 |

## SPARKY 6.0 Architecture

### Core Components

```python
@dataclass
class ExecutionContext:
    agent_id: str
    issue_file: Path
    current_state: AgentState
    pause_reason: Optional[PauseReason]
    actions_completed: List[Dict]
    actions_pending: List[Dict]
    learning_insights: List[str]
    resume_token: str

class AgentState(Enum):
    INITIALIZED
    RUNNING
    PAUSED
    WAITING_FOR_TESTS
    WAITING_FOR_APPROVAL
    COMPLETED
    FAILED
```

### API

```python
# Launch
context = await sparky.launch(issue_file)

# Resume with data
context = await sparky.resume(agent_id, event_data)

# Status check
sparky.status(agent_id)
```

### State Persistence

```
~/.sparky/
├── state/
│   ├── {agent_id}.pkl  # Serialized context
│   └── {agent_id}.json # Human-readable status
└── learning/
    └── insights.json    # Pattern tracking
```

### Pause Triggers

1. `TEST_SUITE_RUNNING` - Waiting for external tests
2. `HUMAN_APPROVAL_NEEDED` - Destructive action pending
3. `RATE_LIMITED` - API limit reached
4. `LEARNING_CHECKPOINT` - Analysis point
5. `ERROR_RECOVERY` - Failed action

### Learning Engine

```python
insights.json:
{
  "patterns": {
    "action_type_target": {
      "count": N,
      "success": N
    }
  },
  "last_run": {
    "agent_id": "xxx",
    "test_results": {...},
    "insights": [...]
  }
}
```

## Test Suite

### Structure
```
tests/sparky_test_suite/
├── issues/
│   ├── level_1_basic/
│   ├── level_2_intermediate/
│   ├── level_3_advanced/
│   └── level_4_integration/
├── fixtures/
│   ├── simple_function.py
│   ├── data_processor.py
│   └── main_app.py
├── run_suite.py
├── run_suite_async.py
└── reset_suite.py
```

### Results
- 4/4 tests passing
- 0.71s average execution
- 100% async flow coverage

## Usage Patterns

### CI/CD Integration
```bash
# GitHub Actions
sparky launch issue.md
# ... build runs ...
sparky resume $AGENT_ID '{"test_results": {...}}'
```

### Batch Processing
```python
for issue in issues:
    context = await sparky.launch(issue)
    pending.append(context.agent_id)

# Later
for agent_id in pending:
    await sparky.resume(agent_id)
```

### Error Recovery
```python
if context.pause_reason == PauseReason.ERROR_RECOVERY:
    # Automatic retry with backoff
    await asyncio.sleep(2 ** attempt)
    context = await sparky.resume(agent_id)
```

## Performance

- State save/load: <10ms
- Pause overhead: ~50ms  
- Resume latency: <100ms
- Learning lookup: O(1)

## Files

```
agents/sparky_6_async.py         # Main implementation
tests/sparky_test_suite/         # Test framework
prompts/sparky/                  # Prompt templates
~/.sparky/                       # Runtime state
```

## Next: SPARKY 7.0

- Factor 7: Human interaction tools
- Factor 8: Control flow ownership
- Factor 11: Sandboxed execution
- Factor 12: Stateless reducer