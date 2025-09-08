# Issue #007: Create CLI Tool

## Description
Build a command-line interface for agent management and execution across all repositories.

## Acceptance Criteria
- [ ] Create bin/agent executable script
- [ ] Implement agent discovery across repos
- [ ] Add agent execution commands
- [ ] Create pipeline execution support
- [ ] Add agent listing and info commands
- [ ] Implement configuration management
- [ ] Add debug and verbose modes

## CLI Commands
```bash
agent list                          # List all available agents
agent info <agent>                  # Show agent details
agent run <agent> "<task>"          # Run an agent
agent pipeline <name>               # Run a pipeline
agent config get/set <key> <value>  # Manage configuration
agent status                        # Show running agents
agent kill <pid>                    # Stop a background agent
agent test <agent>                  # Test an agent
agent install <repo>/<agent>        # Install an agent
```

## Implementation Structure
```python
#!/usr/bin/env python3
import click

@click.group()
def cli():
    """12-Factor Agent CLI"""
    pass

@cli.command()
def list():
    """List available agents"""
    
@cli.command()
@click.argument('agent')
@click.argument('task')
def run(agent, task):
    """Run an agent with a task"""
```

## Agent Assignment
`CLIBuilderAgent`

## Priority
P2 - Medium

## Dependencies
- Depends on: #002, #005, #006

## Labels
cli, tooling, user-interface