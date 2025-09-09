# 12-Factor Agents Usage Guide

## Setup (2 minutes)

```bash
cd /path/to/your-project

# Create symlinks
ln -s ../12-factor-agents .agents
echo ".agents/" >> .gitignore

# Initialize project with dependencies
uv init
uv add pydantic jinja2 psutil pyyaml semver pytest-asyncio

# Test it works
uv run python .agents/bin/agent.py list
```

## Creating Your First Agent

### Basic Agent Structure
```python
# your_project/my_agent.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / ".agents"))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.set_workflow_stages(["init", "process", "complete"])
    
    def register_tools(self):
        # Return empty list if no tools needed
        return []
    
    def execute_task(self, task: str) -> ToolResponse:
        self.set_progress(0.1, "init")
        
        # Your logic here
        result = {"processed": task, "status": "completed"}
        
        self.set_progress(1.0, "complete")
        return ToolResponse(success=True, data=result)
    
    def _apply_action(self, action: dict) -> ToolResponse:
        # Required abstract method
        return ToolResponse(success=True, data={"action": action})
```

### Run Your Agent
```python
# test_agent.py
from my_agent import MyCustomAgent

agent = MyCustomAgent()
result = agent.execute_task("analyze this text")
print(result.data)
```

## Key Patterns

### 1. Pipeline Architecture
```python
from core.pipeline import MultiStagePipeline, PipelineStage

class ProcessingStage(PipelineStage):
    async def process_async(self, data, context=None):
        # Process data
        return processed_data, metadata

# Use in agent
self.pipeline = MultiStagePipeline()
self.pipeline.add_stage(ProcessingStage())
result = await self.pipeline.process_item_async(data)
```

### 2. Checkpoint System
```python
# Save progress
self.save_checkpoint()

# Resume from checkpoint
if self.load_checkpoint():
    self.set_progress(self.progress, "resumed")
```

### 3. Error Handling
```python
try:
    result = self._risky_operation()
except Exception as e:
    self.handle_error(e, "operation_failed")
    return ToolResponse(success=False, error=str(e))
```

### 4. Progress Tracking
```python
self.set_progress(0.0, "starting")
for i, item in enumerate(items):
    self._process_item(item)
    self.set_progress((i+1)/len(items), f"processed_{i+1}")
self.set_progress(1.0, "completed")
```

## CLI Commands

```bash
# Agent operations
uv run python .agents/bin/agent.py list               # List all agents
uv run python .agents/bin/agent.py list --verbose     # Detailed info
uv run python .agents/bin/agent.py info AgentName     # Agent details
uv run python .agents/bin/agent.py run AgentName "task" # Execute agent

# Testing (from 12-factor-agents directory)
cd .agents && make test                     # Run full test suite
cd .agents && make quick-test               # Quick validation
cd .agents && make format                   # Format code
cd .agents && make lint                     # Lint code
```

## Configuration

### Environment Variables
```bash
# .env file
CHECKPOINT_DIR=.claude/agents/checkpoints
MAX_CONCURRENT_AGENTS=10
ENABLE_METRICS=true
```

### Project Structure
```
your-project/
├── .agents/              # Symlink to 12-factor-agents
├── agents/               # Your custom agents
│   ├── __init__.py
│   └── custom_agent.py
├── prompts/              # Externalized prompts
│   └── templates/
└── tests/
    └── test_agents.py
```

## Testing Your Agents

```python
# tests/test_custom_agent.py
import pytest
from agents.custom_agent import CustomAgent

def test_agent_execution():
    agent = CustomAgent()
    result = agent.execute_task("test task")
    assert result.success
    assert "expected_key" in result.data

def test_12factor_compliance():
    from core.compliance import ComplianceAuditor
    agent = CustomAgent()
    auditor = ComplianceAuditor()
    report = auditor.audit_agent(agent)
    assert report["overall_compliance"] in ["fully_compliant", "mostly_compliant"]
```

## Advanced Features

### Parallel Execution
```python
from core.agent_executor import AgentExecutor

executor = AgentExecutor()
tasks = [{"task": "analyze file1"}, {"task": "analyze file2"}]
results = executor.execute_parallel(tasks)
```

### Orchestration
```python
from core.orchestrator import ProgressAwareOrchestrator

class WorkflowOrchestrator(ProgressAwareOrchestrator):
    def __init__(self):
        super().__init__("workflow")
        self.register_phase_processor("analysis", self._analyze)
        self.register_phase_processor("processing", self._process)
    
    async def _analyze(self, data):
        # Analysis logic
        pass
    
    async def _process(self, data):
        # Processing logic
        pass
```

### Event System
```python
from core.triggers import LocalEventSystem

event_system = LocalEventSystem()

# Emit event
event_system.emit("task_completed", {"task_id": "123"})

# Listen for events
@event_system.on("task_completed")
def handle_completion(event_data):
    print(f"Task {event_data['task_id']} completed")
```


## Performance Tips

- Use `async` methods for I/O operations
- Implement caching in frequently called methods
- Set resource limits for background agents
- Use pipeline stages for complex workflows
- Keep agents focused (single responsibility)

## Common Issues

| Issue | Solution |
|-------|----------|
| Import errors | Ensure symlinks are created correctly |
| Agent not found | Check agent class name matches file name |
| Checkpoint failures | Verify CHECKPOINT_DIR exists and is writable |
| Performance issues | Use pipeline stages to parallelize work |
| Test failures | Run `make format` to fix formatting issues |

## Example: Code Review Agent

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / ".agents"))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse
import subprocess

class SimpleReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.set_workflow_stages(["analyze", "review", "report"])
    
    def register_tools(self):
        return []  # No external tools needed
    
    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data={"action": action})
    
    def execute_task(self, task: str) -> ToolResponse:
        self.set_progress(0.1, "analyze")
        
        # Run linting
        lint_result = subprocess.run(
            ["ruff", "check", "."], 
            capture_output=True, 
            text=True
        )
        
        self.set_progress(0.5, "review")
        
        # Parse results
        issues = lint_result.stdout.split('\n')
        
        self.set_progress(1.0, "report")
        
        return ToolResponse(
            success=True,
            data={
                "issues_found": len(issues),
                "details": issues[:10]  # First 10 issues
            }
        )
```

## Production Deployment

```dockerfile
# Dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD ["uv", "run", "agent", "run", "YourAgent"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  agent:
    build: .
    environment:
      - CHECKPOINT_DIR=/data/checkpoints
    volumes:
      - ./data:/data
```

## Next Steps

1. Create your first agent following the pattern above
2. Run tests to validate 12-factor compliance
3. Use the CLI to execute your agents
4. Add checkpoint support for long-running tasks
5. Implement pipelines for complex workflows