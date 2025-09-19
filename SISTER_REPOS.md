# Sister Repository Integration Guide

## Quick Start

Sister repositories should access 12-factor-agents via relative paths from a shared parent directory. No embedded agent code should exist in sister repos.

## Standard Directory Structure

```
parent-directory/
├── 12-factor-agents/       # This framework
├── cite-assist/           # Sister repo example
├── pin-citer/            # Another sister repo
└── other-projects/       # More sister repos
```

## Integration Method

### 1. Copy the Agent Bridge

Copy `utils/agent_bridge.py` to your project's utils directory:

```bash
cp ../12-factor-agents/utils/agent_bridge.py your-project/utils/
```

### 2. Use in Your Code

```python
# In your agent files
from utils.agent_bridge import setup_agent_framework

# Framework is now available
from agents.sparky_6_async import AsyncSparky

# Create and use agent
agent = AsyncSparky()
result = await agent.launch("issues/123.md")
```

### 3. Direct CLI Usage

Run agents directly from sister repos:

```bash
# From your sister repo directory
uv run python ../12-factor-agents/bin/agent.py run AsyncSparky "Fix issue #123"
```

## Available Agents

### SPARKY 6.0 (AsyncSparky) - Primary Agent
- **Purpose**: Intelligent issue processing with Git workflow
- **Usage**: `AsyncSparky().launch(issue_path)`
- **Features**: Feature branches, pause/resume, checkpoint recovery

### Legacy Support
- `IntelligentIssueAgent` - Deprecated, redirects to AsyncSparky
- Old code will continue working but should be updated

## Migration from Old Integration

### Remove Old Artifacts
1. Delete any embedded agent code in your repo
2. Remove old import paths like `from agents.intelligent_issue_agent`
3. Archive experimental integration scripts

### Update Imports
```python
# Old (deprecated)
from agents.intelligent_issue_agent import IntelligentIssueAgent
agent = IntelligentIssueAgent()

# New (recommended)
from agents.sparky_6_async import AsyncSparky
agent = AsyncSparky()
```

## Telemetry Integration

Sister repos automatically send telemetry to 12-factor-agents:

```python
from core.telemetry import TelemetryCollector

telemetry = TelemetryCollector()
telemetry.record_event(
    repo_name="cite-assist",
    event_type="issue_processed",
    data={"issue_number": 123}
)
```

## Troubleshooting

### Framework Not Found
Ensure 12-factor-agents is cloned as a sibling:
```bash
cd ..
git clone https://github.com/yourusername/12-factor-agents.git
```

### Import Errors
Verify agent_bridge.py is in your utils directory and properly configured.

### Old Agent References
Search and replace all `IntelligentIssueAgent` references with `AsyncSparky`.

## Best Practices

1. **Never embed agent code** - Always use relative imports
2. **Keep agent_bridge.py updated** - Copy latest version periodically
3. **Use AsyncSparky** - It's the primary maintained agent
4. **Feature branches** - SPARKY automatically creates feature branches
5. **Monitor telemetry** - Check `telemetry.db` for cross-repo events

## Example Integration

See `cite-assist/utils/agent_bridge.py` for a working example of proper integration.