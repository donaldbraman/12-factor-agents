# 12-Factor Agents - User Guide (Stable Rollback Version)

## Quick Start

The stable rollback branch is immediately available and fully functional. This guide shows how to use the working system while we develop improvements.

### Switch to Stable Branch

```bash
# Get the stable working version
git fetch origin
git checkout rollback-to-stable

# Install dependencies
uv pip install -r requirements.txt
```

## Basic Usage

### List Available Agents

```bash
uv run python bin/agent.py list
```

Available agents:
- `CodeReviewAgent` - Review code for quality and standards
- `TestingAgent` - Generate and run tests
- `RefactoringAgent` - Refactor and improve code
- `IssueFixerAgent` - Fix GitHub issues
- `IssueDecomposerAgent` - Break down complex issues
- `QAAgent` - Quality assurance and validation
- `ComponentMigrationAgent` - Migrate components between systems
- `EnhancedWorkflowAgent` - Orchestrate complex workflows

### Run a Single Agent

```bash
# Basic usage
uv run python bin/agent.py run <AgentName> "<task description>"

# Examples
uv run python bin/agent.py run CodeReviewAgent "Review the authentication module"
uv run python bin/agent.py run TestingAgent "Create tests for user.py"
uv run python bin/agent.py run RefactoringAgent "Refactor database.py for better performance"
```

### Orchestrate Complex Tasks

For complex tasks that need multiple agents:

```bash
# Use the orchestration system
uv run python bin/agent.py orchestrate complex-task

# Or use HierarchicalOrchestrator directly
uv run python -c "
from core.hierarchical_orchestrator import HierarchicalOrchestrator
orch = HierarchicalOrchestrator()
result = orch.orchestrate_task('Implement user authentication with tests and documentation')
print(result)
"
```

## Working with GitHub Issues

### Fix a Single Issue

```bash
# Fix issue #123
uv run python bin/agent.py run IssueFixerAgent "Fix issue #123"
```

### Handle Complex Issues

```bash
# Decompose and fix a complex issue
uv run python bin/agent.py run IssueDecomposerAgent "Decompose issue #456"
# Then run each sub-issue
uv run python bin/agent.py run IssueFixerAgent "Fix sub-issue #456-1"
```

## Advanced Features

### Parallel Processing

The system automatically runs independent tasks in parallel:

```python
from core.hierarchical_orchestrator import HierarchicalOrchestrator

orch = HierarchicalOrchestrator()

# This will run all independent subtasks in parallel
result = orch.orchestrate_task("""
    1. Review all Python files in src/
    2. Generate tests for user module
    3. Update documentation
    4. Check for security issues
""")
```

### Orchestration Patterns

The system supports multiple orchestration patterns:

- **MapReduce**: For processing multiple similar items
- **Pipeline**: For sequential task dependencies
- **Fork-Join**: For parallel independent tasks
- **Scatter-Gather**: For broadcasting to multiple agents
- **Saga**: For transactional workflows

### Load Balancing

The orchestrator automatically balances work across available agents:

```python
# The system will distribute tasks efficiently
orch = HierarchicalOrchestrator(
    max_parallel_agents=10,  # Run up to 10 agents in parallel
    load_balance_strategy="least_loaded"  # Or "round_robin", "capability_based"
)
```

## Integration with External Projects

### Setup Symlinks

If you're using this from another project:

```bash
# In your project root
mkdir -p .agents
cd .agents
ln -s ../../12-factor-agents framework

# Now you can import
from .framework.core.hierarchical_orchestrator import HierarchicalOrchestrator
from .framework.agents.issue_fixer_agent import IssueFixerAgent
```

### Create Custom Agents

Extend the base agent for your needs:

```python
from agents.base import BaseAgent

class YourCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
    def execute_task(self, task):
        # Your custom logic here
        return self.process(task)
```

## Monitoring and Checkpoints

Agents automatically save checkpoints:

```bash
# Check agent status
ls .claude/agents/checkpoints/

# View checkpoint
cat .claude/agents/checkpoints/IssueFixerAgent_*.json
```

## Performance Tips

1. **Use Orchestration for Complex Tasks**: Let the system parallelize automatically
2. **Batch Similar Operations**: Use MapReduce pattern for multiple similar tasks
3. **Monitor Resource Usage**: Watch CPU/memory when running many parallel agents
4. **Use Checkpoints**: Agents can resume from checkpoints if interrupted

## Troubleshooting

### Common Issues

1. **Agent Not Found**
   ```bash
   # Make sure you're in the project root
   pwd  # Should show /path/to/12-factor-agents
   ```

2. **Import Errors**
   ```bash
   # Reinstall dependencies
   uv pip install -r requirements.txt
   ```

3. **Task Fails**
   ```bash
   # Check agent logs
   cat .claude/agents/checkpoints/*.json | grep error
   ```

## What's Working

✅ **All Core Features**:
- File creation and modification
- GitHub issue processing
- Code review and refactoring
- Test generation
- Parallel task execution
- Load balancing
- Checkpoint/resume
- All orchestration patterns

## What's Being Improved

The `hybrid-development` branch is adding:
- Intelligent task decomposition (better understanding of complex requests)
- Smart pattern selection (choosing best orchestration automatically)
- Enhanced error handling
- Performance optimizations

## Support

- **Issues**: https://github.com/donaldbraman/12-factor-agents/issues
- **Branch**: `rollback-to-stable`
- **Status**: Fully functional and stable

## Migration Notes

When the new hybrid system is ready:
1. We'll announce beta testing
2. You can test on `hybrid-development` branch
3. Full migration guide will be provided
4. Rollback branch remains available as fallback

---

**Note**: This is the stable, working version. Use this while we develop the enhanced hybrid system with improved intelligence and testing.