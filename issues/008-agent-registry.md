# Issue #008: Create Agent Registry and Discovery

## Description
Build a local agent registry system for discovering and managing agents across all repositories.

## Acceptance Criteria
- [ ] Create LocalAgentRegistry class in core/discovery.py
- [ ] Implement automatic agent discovery
- [ ] Add agent capability tracking
- [ ] Create agent versioning support
- [ ] Implement dependency resolution
- [ ] Add agent metadata management
- [ ] Create REGISTRY.md documentation

## Implementation Requirements
```python
class LocalAgentRegistry:
    def scan_for_agents(self) -> List[AgentInfo]
    def register_agent(self, agent_class: type, metadata: Dict)
    def get_agent(self, name: str) -> type
    def list_agents(self, capability: str = None) -> List[str]
    def get_agent_info(self, name: str) -> AgentInfo
    def resolve_dependencies(self, agent: str) -> List[str]
```

## Registry Storage Format
```json
{
  "agents": {
    "core/FileSearchAgent": {
      "path": "~/Documents/GitHub/12-factor-agents/agents/file_search.py",
      "version": "1.0.0",
      "capabilities": ["search", "file-operations"],
      "dependencies": [],
      "tools": ["GrepTool", "GlobTool"],
      "description": "Search files and content"
    }
  }
}
```

## Discovery Locations
1. `~/Documents/GitHub/12-factor-agents/agents/` - Core agents
2. `~/Documents/GitHub/*/`.claude/custom/` - Project-specific agents
3. `~/.claude-agents/installed/` - Installed third-party agents

## Agent Assignment
`RegistryBuilderAgent`

## Priority
P2 - Medium

## Dependencies
- Depends on: #002

## Labels
registry, discovery, agent-management