# 12-Factor Agents Developer Guide

A comprehensive guide for developers building agents and extending the 12-Factor Agents framework.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Creating Your First Agent](#creating-your-first-agent)
- [Core Development Patterns](#core-development-patterns)
- [Advanced Features](#advanced-features)
- [Testing Your Agents](#testing-your-agents)
- [Production Deployment](#production-deployment)
- [Performance Optimization](#performance-optimization)

## Architecture Overview

### Framework Structure
```
12-factor-agents/
├── core/           # Base classes and interfaces
├── agents/         # Reusable agent implementations
├── bin/           # CLI tools
├── shared-state/  # Cross-repo state management
├── orchestration/ # Multi-agent pipelines
├── prompts/       # Externalized prompts
├── docs/          # Documentation
└── tests/         # Test suite
```

### Sister Repository Integration

The framework works as a sister repository alongside your project repos, accessing them via relative paths:

```
parent-directory/
├── 12-factor-agents/     # Framework repository
├── your-project-1/       # Sister repo 1
├── your-project-2/       # Sister repo 2
└── other-projects/       # Other sister repos
```

### Integration Method: Relative Path Access

**The 12-Factor Agents framework uses a zero-setup relative path approach for sister repository integration.**

```python
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

**Key Benefits:**
- Zero configuration required
- No symlinks to manage or ignore
- Works consistently across all environments
- Standard pattern for all sister repositories

## Cross-Repository Setup

### Directory Layout
Organize your repositories as siblings in a parent directory:

```
parent-directory/
├── 12-factor-agents/     # The framework (this repository)
├── project-alpha/        # Your first project
├── project-beta/         # Your second project  
├── legacy-system/        # Existing system to integrate
└── experimental/         # Research projects
```

### Helper Pattern for Sister Repos
Create a standard helper in each project for consistent imports:

```python
# your_project/utils/agent_bridge.py
"""
Standard bridge to 12-factor-agents framework.
Use this in all sister repositories for consistent access.
"""
import sys
from pathlib import Path

def setup_agent_framework():
    """Setup path to 12-factor-agents framework."""
    framework_path = Path(__file__).parent.parent.parent / "12-factor-agents"
    if framework_path.exists():
        sys.path.insert(0, str(framework_path))
        return True
    else:
        raise ImportError(f"12-factor-agents not found at {framework_path}")

def get_framework_path():
    """Get absolute path to the framework."""
    return Path(__file__).parent.parent.parent / "12-factor-agents"

# Auto-setup when imported
setup_agent_framework()
```

### Usage in Your Projects
```python
# your_project/agents/my_agent.py
from utils.agent_bridge import setup_agent_framework

# Framework is now available
from core.agent import BaseAgent
from core.tools import ToolResponse

class MyProjectAgent(BaseAgent):
    def execute_task(self, task: str) -> ToolResponse:
        # Your agent implementation
        return ToolResponse(success=True, data={"result": "completed"})
```

### Running Agents from Sister Repos
```bash
# From your project directory
cd /path/to/your-project

# Run framework agents directly
uv run python ../12-factor-agents/bin/agent.py run SmartIssueAgent "123"

# Run your custom agents
uv run python agents/my_agent.py
```

## Creating Your First Agent

### Basic Agent Structure
```python
# your_project/custom_agent.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "12-factor-agents"))

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

### Issue File Format
Agents expect issues in the `issues/` directory:
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

## Core Development Patterns

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

### 5. Cross-Repository Operations
```python
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
    # Agent can make changes, run tests, etc.
    pass
context_manager.restore_context()
```

## Advanced Features

### Parallel Execution
```python
from core.agent_executor import AgentExecutor

executor = AgentExecutor()
tasks = [{"task": "analyze file1"}, {"task": "analyze file2"}]
results = executor.execute_parallel(tasks)
```

### Orchestration Pattern
```python
from core.orchestrator import ProgressAwareOrchestrator

class IssueOrchestrator(ProgressAwareOrchestrator):
    """Framework's issue processing orchestrator"""
    def __init__(self):
        super().__init__("issue_resolution")
        # Framework's workflow phases
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

### Tools Development
```python
from core.tools import Tool, ToolResponse

class CustomTool(Tool):
    def __init__(self):
        super().__init__(name="custom_tool", description="Performs custom operations")
    
    def execute(self, parameters: dict) -> ToolResponse:
        # Tool implementation
        result = self._perform_custom_operation(parameters)
        return ToolResponse(success=True, data=result)
    
    def _perform_custom_operation(self, parameters: dict):
        # Your custom logic here
        return {"processed": parameters}
```

## Testing Your Agents

### Basic Agent Tests
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

### Integration Tests
```python
def test_sister_repo_integration():
    """Test that agent can operate on sister repositories"""
    from core.github_integration import CrossRepoContextManager
    
    context_manager = CrossRepoContextManager()
    assert context_manager.switch_to_repo("../test-sister-repo")
    
    # Test operations in sister repo context
    agent = CustomAgent()
    result = agent.execute_task("test cross-repo task")
    assert result.success
    
    context_manager.restore_context()
```

### Pipeline Tests
```python
def test_pipeline_execution():
    """Test multi-stage pipeline processing"""
    from core.pipeline import MultiStagePipeline
    
    pipeline = MultiStagePipeline(stages=[
        TestStage1(),
        TestStage2(),
        TestStage3()
    ])
    
    result = await pipeline.process_item_async(test_data)
    assert result.success
    assert len(result.stage_results) == 3
```

## Production Deployment

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD ["uv", "run", "agent", "run", "YourAgent"]
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  agent:
    build: .
    environment:
      - CHECKPOINT_DIR=/data/checkpoints
      - MAX_CONCURRENT_AGENTS=10
      - ENABLE_METRICS=true
    volumes:
      - ./data:/data
      - ./sister-repos:/sister-repos  # Mount sister repositories
```

### Environment Configuration
```bash
# .env file
CHECKPOINT_DIR=.claude/agents/checkpoints
MAX_CONCURRENT_AGENTS=10
ENABLE_METRICS=true
SISTER_REPO_BASE_PATH=/path/to/parent-directory
```

### Project Structure
```
parent-directory/
├── 12-factor-agents/     # Framework repository
├── your-project/         # Your project
│   ├── agents/           # Your custom agents
│   │   ├── __init__.py
│   │   └── custom_agent.py
│   ├── prompts/          # Externalized prompts
│   │   └── templates/
│   ├── tests/
│   │   └── test_agents.py
│   └── .env              # Environment configuration
└── other-projects/       # Other sister repositories
```

## Performance Optimization

### Best Practices
- Use `async` methods for I/O operations
- Implement caching in frequently called methods
- Set resource limits for background agents
- Use pipeline stages for complex workflows
- Keep agents focused (single responsibility)

### Caching Strategies
```python
from functools import lru_cache
from core.cache import AgentCache

class OptimizedAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.cache = AgentCache()
    
    @lru_cache(maxsize=128)
    def expensive_computation(self, input_data):
        # Expensive operation
        return result
    
    def cached_external_call(self, key, fetch_func):
        """Cache external API calls"""
        if cached_result := self.cache.get(key):
            return cached_result
        
        result = fetch_func()
        self.cache.set(key, result, ttl=300)  # Cache for 5 minutes
        return result
```

### Resource Management
```python
from core.resources import ResourceManager

class ResourceAwareAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.resource_manager = ResourceManager()
    
    async def execute_task(self, task: str):
        with self.resource_manager.allocate(cpu=2, memory="1GB"):
            # Execute resource-intensive task
            result = await self._process_task(task)
            return result
```

### Monitoring and Metrics
```python
from core.telemetry import AgentTelemetry

class MonitoredAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.telemetry = AgentTelemetry()
    
    def execute_task(self, task: str):
        with self.telemetry.timer("task_execution"):
            self.telemetry.increment_counter("tasks_started")
            try:
                result = self._execute_task_impl(task)
                self.telemetry.increment_counter("tasks_completed")
                return result
            except Exception as e:
                self.telemetry.increment_counter("tasks_failed")
                raise
```

## Example: Code Review Agent

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "12-factor-agents"))

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

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Import errors | Ensure relative path to 12-factor-agents is correct |
| Agent not found | Check agent class name matches file name |
| Checkpoint failures | Verify CHECKPOINT_DIR exists and is writable |
| Performance issues | Use pipeline stages to parallelize work |
| Test failures | Run `make format` to fix formatting issues |
| Cross-repo access fails | Verify sister repository paths are correct |
| Resource exhaustion | Implement resource management and limits |

## Next Steps

1. Create your first agent following the pattern above
2. Run tests to validate 12-factor compliance
3. Use the CLI to execute your agents
4. Add checkpoint support for long-running tasks
5. Implement pipelines for complex workflows
6. Set up monitoring and telemetry
7. Deploy to production with proper resource management

For more specific examples and advanced patterns, see the architecture documentation and existing agent implementations in the `agents/` directory.