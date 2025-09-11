# 12-Factor Agents

Local-first AI agent framework. Zero cloud dependencies.

## Quick Start
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
./setup.sh
uv run bin/agent.py list
uv run bin/agent.py run IssueFixerAgent "fix bug in file.py"
```

## Core Agents
- **IssueOrchestratorAgent**: GitHub issue processing
- **IntelligentIssueAgent**: Smart issue analysis & fixes  
- **TestingAgent**: Test execution & validation
- **CodeReviewAgent**: Code quality analysis

## Performance
- **22 GitHub issues processed** in single session
- **95% context efficiency** achieved
- **Fork-Join orchestration** for parallel task execution
- **uv-powered** for maximum speed

## Documentation
- `docs/AGENT-ISSUE-TEMPLATE.md` - Issue agent patterns
- `docs/HIERARCHICAL-ORCHESTRATION.md` - Performance data
- `docs/INTEGRATION-GUIDE.md` - Setup & usage

## Architecture
```
bin/agent.py → core/agent_executor.py → agents/*.py
              ↓
core/orchestration → Fork-Join Pattern → Results
```

Built with 12-factor principles. Battle-tested on real GitHub issues.