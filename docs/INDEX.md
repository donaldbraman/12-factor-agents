# 12-Factor Agents Documentation

Welcome to the comprehensive documentation for the 12-Factor Agents framework - a local-first, multi-repository AI agent system following the 12-factor methodology.

## Quick Navigation

### 🚀 **Getting Started**
- [README](../README.md) - Quick start and overview
- [User Guide](user/USER_GUIDE.md) - Complete user manual
- [Installation & Setup](user/USER_GUIDE.md#installation) - Get up and running

### 👩‍💻 **For Developers**
- [Developer Guide](developer/DEVELOPER_GUIDE.md) - Build agents and extend the framework
- [Architecture Overview](architecture/ARCHITECTURE_OVERVIEW.md) - System architecture and design principles
- [Integration Guide](developer/DEVELOPER_GUIDE.md#sister-repository-integration) - Sister repository integration

### 🏗️ **Architecture & Design**
- [Architecture Overview](architecture/ARCHITECTURE_OVERVIEW.md) - High-level system design
- [Hierarchical Orchestration](HIERARCHICAL-ORCHESTRATION.md) - Multi-level agent coordination
- [Hybrid System Specification](HYBRID_SYSTEM_SPECIFICATION.md) - System specifications
- [12-Factor Compliance](architecture/ARCHITECTURE_OVERVIEW.md#12-factor-compliance) - Compliance details

### 📋 **Templates & Guides**
- [Agent Issue Template](AGENT-ISSUE-TEMPLATE.md) - Template for creating agent issues
- [Development Templates](templates/) - Templates for various development tasks
  - [Bug Fix Template](templates/bug_fix.md)
  - [Feature Development Template](templates/feature_development.md)
  - [Documentation Template](templates/documentation.md)
  - [Testing Template](templates/testing.md)
  - [Migration Template](templates/migration.md)
  - [Refactoring Template](templates/refactoring.md)
  - [Optimization Template](templates/optimization.md)
  - [Research Template](templates/research.md)

### 🔧 **Technical Documentation**
- [Dynamic Context Priming](DYNAMIC-CONTEXT-PRIMING.md) - Context management system
- [Telemetry Specification](TELEMETRY_SPEC.md) - Monitoring and metrics
- [PR Review Setup](PR_REVIEW_SETUP.md) - Pull request review configuration
- [Phase 1 Implementation](PHASE_1_IMPLEMENTATION.md) - Implementation roadmap

### 🎯 **Use Cases & Examples**
- [Citation Management](user/USER_GUIDE.md#real-world-example-for-pin-citer) - pin-citer integration
- [Legal Documents](user/USER_GUIDE.md#real-world-example-for-cite-assist) - cite-assist integration
- [Background Research](user/USER_GUIDE.md#background-research-agents) - Parallel research agents
- [Issue Processing](user/USER_GUIDE.md#real-examples-by-complexity) - Automated issue resolution

## Documentation Structure

This documentation is organized into logical sections:

```
docs/
├── INDEX.md                    # This navigation guide
├── user/                       # User-facing documentation
│   └── USER_GUIDE.md          # Complete user guide
├── developer/                  # Developer documentation
│   └── DEVELOPER_GUIDE.md     # Developer guide and integration
├── architecture/               # Architecture documentation
│   └── ARCHITECTURE_OVERVIEW.md  # System architecture
├── templates/                  # Document templates
│   ├── bug_fix.md             # Bug fix template
│   ├── feature_development.md  # Feature development template
│   ├── documentation.md        # Documentation template
│   ├── testing.md             # Testing template
│   ├── migration.md           # Migration template
│   ├── refactoring.md         # Refactoring template
│   ├── optimization.md        # Optimization template
│   └── research.md            # Research template
└── [technical specs...]        # Additional technical documentation
```

## Key Features Highlight

### ✅ **Local-First Operation**
- 100% local execution, no external dependencies
- Git-friendly configuration and state management
- Cross-repository agent sharing through sister repository model

### ✅ **Intelligent Issue Resolution**
- Automatic complexity analysis (atomic → enterprise)
- Smart task decomposition and routing
- 12-Factor compliant sub-issue creation
- Orchestrated execution across multiple agents

### ✅ **Sister Repository Integration**
- Zero-configuration integration with existing projects
- Relative path-based access for instant updates
- Cross-repository context management
- Standard import patterns for seamless operation

### ✅ **Production-Ready Architecture**
- Full 12-factor methodology compliance
- Comprehensive telemetry and monitoring
- Graceful error handling and recovery
- Horizontal scaling through orchestration

## Getting Help

### For Users
- Start with the [User Guide](user/USER_GUIDE.md)
- Check the [Troubleshooting section](user/USER_GUIDE.md#troubleshooting)
- Review [examples by project type](user/USER_GUIDE.md#examples-by-project-type)

### For Developers
- Begin with the [Developer Guide](developer/DEVELOPER_GUIDE.md)
- Study the [Architecture Overview](architecture/ARCHITECTURE_OVERVIEW.md)
- Explore [core development patterns](developer/DEVELOPER_GUIDE.md#core-development-patterns)

### For System Architects
- Read the [Architecture Overview](architecture/ARCHITECTURE_OVERVIEW.md)
- Understand [Hierarchical Orchestration](HIERARCHICAL-ORCHESTRATION.md)
- Review [system specifications](HYBRID_SYSTEM_SPECIFICATION.md)

## Quick Commands Reference

### Installation
```bash
# Setup framework
./setup.sh

# Link to your project (from project directory)
ln -s ../12-factor-agents .agents
```

### Basic Usage
```bash
# Process an issue with automatic complexity detection
uv run python bin/agent.py run SmartIssueAgent "issue-number"

# List available agents
uv run python bin/agent.py list

# Get agent information
uv run python bin/agent.py info SmartIssueAgent
```

### Testing
```bash
# Run test suite
make test

# Quick validation
make quick-test

# Format and lint
make format && make lint
```

## Why uv?

The framework uses **uv** for Python management, providing:
- 🚀 **10-100x faster** than pip/python
- 🔧 **Zero configuration** - Just works
- 📦 **Automatic dependencies** - No virtual envs needed
- ✅ **Consistent execution** - Same environment everywhere

## Framework Philosophy

The 12-Factor Agents framework embodies:

- **Modularity**: Agents are independently deployable and composable
- **Observability**: Full telemetry and monitoring throughout the system
- **Resilience**: Graceful degradation and error recovery
- **Scalability**: Horizontal scaling through intelligent orchestration
- **Maintainability**: Clear separation of concerns and well-defined interfaces

## Contributing

Contributions are welcome! Please:

1. Start with the appropriate template from [templates/](templates/)
2. Follow the [12-factor principles](architecture/ARCHITECTURE_OVERVIEW.md#12-factor-compliance)
3. Ensure comprehensive testing and documentation
4. Submit clear, focused pull requests

---

**Need something specific?** Use the navigation above to jump directly to the section you need, or start with the [User Guide](user/USER_GUIDE.md) for a comprehensive introduction to the framework.