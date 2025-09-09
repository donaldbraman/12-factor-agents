# Issue #064: Update Documentation with Correct Usage Patterns

## Description
Documentation needs updates to reflect the actual working usage patterns discovered through testing.

## Problems Found
1. CLI commands use `uv run python bin/agent.py` not `uv run agent`
2. Pipeline initialization requires stages parameter
3. Missing documentation for IssueFixerAgent
4. Examples missing required imports

## Solution

### 1. Fix CLI Commands in README
Current broken:
```bash
uv run agent list
uv run agent run <name> "<task>"
```

Should be:
```bash
uv run python bin/agent.py list
uv run python bin/agent.py run <name> "<task>"
uv run python bin/agent.py info <name>
uv run python bin/agent.py orchestrate <pipeline>
```

### 2. Fix Pipeline Example in INTEGRATION-GUIDE.md
Current broken:
```python
self.pipeline = MultiStagePipeline()
self.pipeline.add_stage(ProcessingStage())
```

Should be:
```python
self.pipeline = MultiStagePipeline(stages=[ProcessingStage()])
# Or initialize empty and add stages
self.pipeline = MultiStagePipeline(stages=[])
self.pipeline.add_stage(ProcessingStage())
```

### 3. Add Complete Imports Section
Add at the top of code examples:
```python
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / ".agents"))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse
from core.state import UnifiedState
from core.triggers import LocalEventSystem
from orchestration.pipeline import MultiStagePipeline
```

### 4. Add IssueFixerAgent Documentation
Add to Available Agents section:
```markdown
## Available Agents

- **RepositorySetupAgent**: Initialize project structure
- **IssueOrchestratorAgent**: Process and delegate GitHub issues  
- **IssueFixerAgent**: Apply fixes from issue descriptions
- **TestingAgent**: Run comprehensive test suites
- **CodeReviewAgent**: Analyze code quality
- **UvMigrationAgent**: Migrate to uv package manager
- **PromptManagementAgent**: Manage prompt templates
- **EventSystemAgent**: Handle event-driven workflows
```

## Implementation
Update `/Users/dbraman/Documents/GitHub/12-factor-agents/README.md` and `/Users/dbraman/Documents/GitHub/12-factor-agents/docs/INTEGRATION-GUIDE.md` with all corrections.

## Type
documentation

## Priority
high

## Status
open

## Assignee
issue_fixer_agent