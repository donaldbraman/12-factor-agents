# 12-Factor Agents Framework

A local-first, multi-repository AI agent system following the 12-factor methodology.

## Features
- ✅ 100% local operation
- ✅ Cross-repository agent sharing
- ✅ No external dependencies
- ✅ Git-friendly configuration
- ✅ Full 12-factor compliance

## Quick Start

1. Run setup: `./setup.sh`
2. Link in your project: `ln -s ../12-factor-agents/core .claude/agents`
3. Run agents: `uv run bin/agent <name> "<task>"`

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
