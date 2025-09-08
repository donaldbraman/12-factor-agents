# Issue #006: Implement Shared State Management

## Description
Create a file-based shared state system that works across all repositories without external dependencies.

## Acceptance Criteria
- [ ] Create LocalSharedState class in shared-state/manager.py
- [ ] Implement file locking for concurrent access
- [ ] Add JSON serialization for complex objects
- [ ] Create state expiration/TTL support
- [ ] Implement state namespacing per repository
- [ ] Add state history tracking
- [ ] Create cleanup for old state files

## Implementation Requirements
```python
class LocalSharedState:
    def set(self, key: str, value: Any, repo: str = None, ttl: int = None)
    def get(self, key: str, repo: str = None) -> Any
    def delete(self, key: str, repo: str = None)
    def exists(self, key: str, repo: str = None) -> bool
    def list_keys(self, pattern: str = "*", repo: str = None) -> List[str]
    def cleanup_expired(self)
```

## State Directory Structure
```
~/.claude-shared-state/
├── global/           # Cross-repo shared state
├── by-repo/         # Repository-specific state
│   ├── project1/
│   └── project2/
├── locks/           # File locks
└── history/         # State change history
```

## Agent Assignment
`InfrastructureAgent`

## Priority
P1 - High

## Dependencies
- Depends on: #001

## Labels
state-management, infrastructure, cross-repo