# Running Agents with UV

All Python operations should use `uv` as per CLAUDE.md requirements.

## Running Agents

```bash
# Instead of: python3 agents/agent_name.py
uv run agents/repository_setup_agent.py

# Run the orchestrator
uv run agents/issue_orchestrator_agent.py

# Run with specific Python version if needed
uv run --python 3.11 agents/event_system_agent.py
```

## Installing Dependencies

```bash
# If requirements.txt exists
uv pip install -r requirements.txt

# Install specific packages
uv pip install pydantic
```

## Virtual Environment Management

```bash
# Create venv
uv venv

# Activate (automatic with uv run)
uv run <command>
```

## Agent Launcher Script

```bash
#!/bin/bash
# bin/run-agent
uv run python -c "
from agents.issue_orchestrator_agent import IssueOrchestratorAgent
agent = IssueOrchestratorAgent()
result = agent.execute_task('resolve all issues')
print(f'Success: {result.success}')
"
```

## Testing

```bash
# Run all agent tests
uv run pytest tests/

# Run specific agent
uv run agents/prompt_management_agent.py
```