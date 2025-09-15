# 12-Factor Agents Integration Guide

**Sparky** - Your intelligent issue resolution system for automated GitHub issue processing and implementation.

## What is Sparky?

Sparky is the 12-Factor Agents framework configured as an intelligent issue resolution system. It automatically:
- Analyzes GitHub issues for complexity and requirements
- Decomposes complex issues into manageable sub-tasks
- Routes tasks to specialized agents (testing, code review, implementation)
- Implements actual code changes based on issue descriptions
- Tracks progress with granular telemetry

## Setup for Sister Repositories (2 minutes)

Sparky (12-factor-agents) works as a sister repository alongside your project repos, accessing them via relative paths from your mutual parent directory.

### Directory Structure
```
parent-directory/
├── 12-factor-agents/     # Sparky issue resolution system
├── your-project-1/       # Sister repo 1
├── your-project-2/       # Sister repo 2
└── other-projects/       # Other sister repos
```

### Integration Methods

#### Method 1: Direct Relative Path Access
```bash
# From your project directory
cd /path/to/parent-directory/your-project

# Run Sparky on your issues
uv run python ../12-factor-agents/bin/agent.py run IntelligentIssueAgent "Process issue #123"

# Process issues with repo path
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "12-factor-agents"))

from core.github_integration import ExternalIssueProcessor
processor = ExternalIssueProcessor()
result = processor.process_external_issue(
    repo="your-org/your-project",
    issue_number=123,
    repo_path="../your-project"  # Relative to 12-factor-agents
)
```

#### Method 2: Symlink Setup (Optional)
```bash
cd /path/to/your-project

# Create symlink to sister repo
ln -s ../12-factor-agents .agents
echo ".agents/" >> .gitignore

# Test it works
uv run python .agents/bin/agent.py list
```

## Using Sparky for Issue Resolution

### Process Issues Across Sister Repositories
```bash
# From 12-factor-agents directory - process own issues
uv run python bin/agent.py run IntelligentIssueAgent "Process issue #123"

# From sister repo - process that repo's issues
cd ../your-project
uv run python ../12-factor-agents/bin/agent.py run SmartIssueAgent "123"

# Process sister repository issues programmatically
from core.github_integration import ExternalIssueProcessor, CrossRepoContextManager

# Process issue in sister repo
processor = ExternalIssueProcessor()
result = processor.process_external_issue(
    repo="your-org/sister-repo",
    issue_number=123,
    repo_path="../sister-repo"  # Relative path from parent directory
)

# Context switching between sister repos
context_manager = CrossRepoContextManager()
if context_manager.switch_to_repo("../another-sister-repo"):
    # Now operating in context of another sister repo
    # Sparky can make changes, run tests, etc.
    pass
context_manager.restore_context()
```

### Issue File Format
Sparky expects issues in the `issues/` directory:
```markdown
# Issue #123: Fix authentication bug

## Description
The login system fails when...

## Current Code
```python
def authenticate(user):
    return False  # Bug here
```

## Should Be
```python
def authenticate(user):
    return user.is_valid()
```

## Metadata
- **Repository**: your-repo
- **Labels**: bug, high-priority

## Agent Assignment
IntelligentIssueAgent
```

## Creating Your First Agent

### Basic Agent Structure
```python
# your_project/custom_agent.py
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
async def setup_pipeline(self):
    self.pipeline = MultiStagePipeline(stages=[
        CodeReviewAgent(),
        TestingAgent(),
        DeploymentAgent()
    ])
    result = await self.pipeline.process_item_async(data)
    return result
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

## CLI Commands for Sister Repos

```bash
# From sister repo - use Sparky to process your issues
cd /path/to/parent-directory/your-project
uv run python ../12-factor-agents/bin/agent.py run IntelligentIssueAgent "Process issue #123"
uv run python ../12-factor-agents/bin/agent.py run SmartIssueAgent "123"  # Auto-decomposition
uv run python ../12-factor-agents/bin/agent.py orchestrate issue-pipeline  # Full pipeline

# From 12-factor-agents directory itself
cd /path/to/parent-directory/12-factor-agents
uv run python bin/agent.py list               # List all agents
uv run python bin/agent.py list --verbose     # Detailed info
uv run python bin/agent.py info AgentName     # Agent details
uv run python bin/agent.py run AgentName "task" # Execute agent

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

### Orchestration (Sparky's Core Pattern)
```python
from core.orchestrator import ProgressAwareOrchestrator

class IssueOrchestrator(ProgressAwareOrchestrator):
    """Sparky's issue processing orchestrator"""
    def __init__(self):
        super().__init__("issue_resolution")
        # Sparky's workflow phases
        self.register_phase_processor(WorkflowPhase.INITIALIZATION, self._load_issue)
        self.register_phase_processor(WorkflowPhase.ANALYSIS, self._analyze_complexity)
        self.register_phase_processor(WorkflowPhase.PROCESSING, self._implement_changes)
        self.register_phase_processor(WorkflowPhase.FINALIZATION, self._validate_changes)
    
    async def _load_issue(self, data):
        # Load and parse GitHub issue
        pass
    
    async def _analyze_complexity(self, data):
        # Determine if decomposition needed
        pass
    
    async def _implement_changes(self, data):
        # Make actual code changes
        pass
    
    async def _validate_changes(self, data):
        # Run tests and validation
        pass
```

### Event System
```python
from core.triggers import LocalEventSystem

event_system = LocalEventSystem()

# Emit event
event_system.emit("task_completed", {"task_id": "123"})

# Listen for events
def handle_completion(event_data):
    print(f"Task {event_data.data['task_id']} completed")

event_system.watch("task_completed", handle_completion)
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