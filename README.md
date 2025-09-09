# 12-Factor Agents Framework

A local-first, multi-repository AI agent system following the 12-factor methodology.

## Features
- ✅ 100% local operation (no cloud dependencies required)
- ✅ Cross-repository agent sharing via symlinks
- ✅ No external service dependencies
- ✅ Git-friendly configuration
- ✅ Full 12-factor compliance
- ✅ Powered by uv for fast, reliable Python management

## Quick Start

1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Run setup: `./setup.sh`
3. Use agents:
   - List: `uv run python uv run bin/agent.py list`
   - Run: `uv run python uv run bin/agent.py run <name> "<task>"`
   - Info: `uv run python uv run bin/agent.py info <name>`
   - Orchestrate: `uv run python uv run bin/agent.py orchestrate <pipeline>`

## Available Agents

- **RepositorySetupAgent**: Initialize project structure
- **IssueOrchestratorAgent**: Process and delegate GitHub issues
- **IssueFixerAgent**: Apply fixes from issue descriptions
- **TestingAgent**: Run comprehensive test suites
- **CodeReviewAgent**: Analyze code quality and suggest improvements
- **UvMigrationAgent**: Migrate Python operations to uv
- **PromptManagementAgent**: Manage external prompt templates
- **EventSystemAgent**: Handle event-driven workflows

## Structure

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

## Documentation

See [docs/](docs/) for detailed documentation.

## License

MIT


## 🔧 Local Development Quality Gates

For hobbyist development with automatic quality checks:

```bash
# Install pre-commit hooks (run once)
make install-hooks

# Run all quality gates
make test

# Quick checks before committing  
make quick-test

# Format and lint code
make format lint

# Performance regression check
make perf-test
```

### Pre-commit Hooks
- **Black**: Code formatting
- **Ruff**: Linting and fixes
- **Quick Tests**: Import validation and basic functionality
- **Performance Check**: Regression detection

Quality gates ensure code stays consistent and performant without manual checking.
