# 12-Factor Agents Framework

A local-first, multi-repository AI agent system following the 12-factor methodology for intelligent issue resolution and automated development workflows.

## Features
- ✅ **100% local operation** - No external dependencies
- ✅ **Cross-repository agent sharing** - Sister repository integration  
- ✅ **Intelligent issue resolution** - Automatic complexity analysis and decomposition
- ✅ **Git-friendly configuration** - Version-controlled settings
- ✅ **Full 12-factor compliance** - Production-ready architecture
- ✅ **Hierarchical orchestration** - Multi-level agent coordination

## Quick Start

### Prerequisites
Install **uv** for optimal performance (10-100x faster than pip):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation
```bash
# 1. Setup framework
./setup.sh

# 2. Verify framework accessibility (from your project directory)
ls ../12-factor-agents

# 3. Test the integration
uv run python ../12-factor-agents/bin/agent.py list
```

### Basic Usage
```bash
# Process any issue - complexity detection is automatic
uv run python bin/agent.py run SmartIssueAgent "issue-number"

# List all available agents
uv run python bin/agent.py list

# Get information about a specific agent
uv run python bin/agent.py info SmartIssueAgent
```

## System Architecture

```
12-factor-agents/
├── core/           # Framework foundation (BaseAgent, tools, pipelines)
├── agents/         # Specialized agent implementations
├── bin/            # CLI tools and executables
├── orchestration/  # Multi-agent coordination and patterns
├── shared-state/   # Cross-repository state management
├── prompts/        # Externalized prompts and templates
├── docs/           # Comprehensive documentation
└── tests/          # Test suite with 12-factor compliance
```

## Sister Repository Integration

The framework works alongside your existing projects as a sister repository:

```
parent-directory/
├── 12-factor-agents/     # This framework
├── your-project-1/       # Your project (e.g., pin-citer)
├── your-project-2/       # Another project (e.g., cite-assist)
└── other-projects/       # Additional projects
```

### Zero-Configuration Setup
Your projects automatically get access to the intelligent agent system through relative paths:

```bash
# From any project directory
cd /path/to/your-project

# Now you have access to everything via relative paths
uv run python ../12-factor-agents/bin/agent.py run IntelligentIssueAgent "Create a citation template"
```

## What Makes This Different

### Intelligent Issue Resolution
The system automatically:
1. **Analyzes complexity** (atomic → enterprise scale)
2. **Routes intelligently** (direct handling vs decomposition)  
3. **Creates 12-Factor compliant sub-issues** when needed
4. **Assigns specialized agents** automatically
5. **Orchestrates execution** across all sub-tasks

### Real Example - Automatic Decomposition
```bash
# Input: Complex documentation overhaul
uv run python bin/agent.py run SmartIssueAgent "064"

# Output: Automatic decomposition
🔍 Analyzing complexity...
📊 Complexity: complex (confidence: 80.0%)
🧩 Issue decomposed into 4 sub-issues:
   📋 Fix CLI Commands in README
   📋 Fix Pipeline Example in INTEGRATION-GUIDE.md
   📋 Add Complete Imports Section  
   📋 Add IssueFixerAgent Documentation
🚀 Processing sub-issues...
   ✅ Sub-issue 1/4 completed
   ✅ Sub-issue 2/4 completed
   ✅ Sub-issue 3/4 completed
   ✅ Sub-issue 4/4 completed
📊 Overall result: 4/4 sub-issues completed successfully
```

### Background Research Agents
Launch truly parallel research that doesn't block your workflow:

```bash
# Fire-and-forget research
/path/to/12-factor-agents/bin/launch_background.sh "research quantum computing applications"

# Returns immediately with:
# TASK_ID:research_20250910_070253_4841
# CHECK:cat /tmp/12-factor-agents-background/research_..._status.json
# Continue other work while research runs...
```

## Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[📖 Documentation Index](docs/INDEX.md)** | **Main navigation hub** | **Everyone** |
| [🚀 User Guide](docs/user/USER_GUIDE.md) | Complete user manual with examples | End users, project teams |
| [👩‍💻 Developer Guide](docs/developer/DEVELOPER_GUIDE.md) | Build agents, extend framework | Developers, integrators |
| [🏗️ Architecture Overview](docs/architecture/ARCHITECTURE_OVERVIEW.md) | System design and principles | Architects, advanced users |
| [🔗 Hierarchical Orchestration](docs/HIERARCHICAL-ORCHESTRATION.md) | Multi-level agent coordination | System designers |

### Quick Links
- **Just getting started?** → [User Guide](docs/user/USER_GUIDE.md)
- **Building agents?** → [Developer Guide](docs/developer/DEVELOPER_GUIDE.md)
- **Understanding the system?** → [Architecture Overview](docs/architecture/ARCHITECTURE_OVERVIEW.md)
- **Need templates?** → [Templates](docs/templates/)

## Key Commands

### From Your Project (Recommended)
```bash
# Process issues in your project
uv run python ../12-factor-agents/bin/agent.py run SmartIssueAgent "123"

# Access intelligent agents
uv run python ../12-factor-agents/bin/agent.py run IntelligentIssueAgent "Create API documentation"
```

### From Framework Directory
```bash
# Core framework operations
uv run python bin/agent.py list               # List agents
uv run python bin/agent.py info AgentName     # Agent details
uv run python bin/agent.py run AgentName "task" # Execute agent
uv run python bin/agent.py orchestrate issue-pipeline # Full pipeline

# Testing and validation
make test          # Full test suite
make quick-test    # Quick validation
make format        # Code formatting
make lint          # Code linting
```

## Use Cases

### Citation Management (pin-citer)
```python
# Natural language citation processing
agent = IntelligentIssueAgent()
result = agent.execute_task("Fix formatting issues in references.bib and add missing DOIs")
# Automatically handles file analysis, formatting fixes, and DOI lookup
```

### Legal Documents (cite-assist)  
```python
# Legal document processing
result = agent.execute_task("Review all case references in chapter-2 and update citation format")
# Understands legal citation requirements and formatting standards
```

### Development Workflows
```bash
# Complex development tasks
uv run python bin/agent.py run SmartIssueAgent "080"  # Enterprise-scale changes
# Automatically decomposes into manageable sub-tasks and orchestrates execution
```

## 12-Factor Principles Applied

The framework follows [12-Factor Agent methodology](https://github.com/humanlayer/12-factor-agents):

- **Factor 1**: Natural Language → Tool Calls
- **Factor 4**: Structured Outputs  
- **Factor 8**: Own Your Control Flow
- **Factor 10**: Small, Focused Agents
- **Factor 12**: Stateless Reducer

This ensures reliable, predictable, production-ready agent behavior.

## Performance

- **Coordination Overhead**: <5% (typically 2-4%)
- **Agent Capacity**: 150+ concurrent agents
- **Task Decomposition**: 50-80ms
- **Pattern Execution**: 200-400ms
- **Memory Usage**: 200-350MB

## Requirements

- **Python 3.11+** (managed automatically by uv)
- **uv package manager** (recommended, 10-100x faster than pip)
- **Git** (for version control and sister repository integration)

## Contributing

1. Read the [Developer Guide](docs/developer/DEVELOPER_GUIDE.md)
2. Use appropriate [templates](docs/templates/)
3. Follow 12-factor principles
4. Ensure comprehensive testing
5. Update documentation

## License

MIT - See [LICENSE](LICENSE) for details

---

**🚀 Ready to get started?** Begin with the [User Guide](docs/user/USER_GUIDE.md) or jump straight to [setup instructions](docs/user/USER_GUIDE.md#installation).

**💡 Need help?** Check the [Documentation Index](docs/INDEX.md) for comprehensive guides and examples.
