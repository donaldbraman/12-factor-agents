# Issue #005: Create Background Launcher Module

## Description
Implement a background agent launcher to enable async execution without blocking.

## Acceptance Criteria
- [ ] Create core/launcher.py with BackgroundLauncher class
- [ ] Implement process spawning with proper isolation
- [ ] Add PID tracking and management
- [ ] Create status monitoring capability
- [ ] Implement graceful shutdown
- [ ] Add resource limiting options
- [ ] Create process cleanup on exit

## Implementation Details
```python
class BackgroundLauncher:
    def launch(self, agent_class: str, task: str) -> str  # Returns PID
    def monitor(self, pid: str) -> Dict[str, Any]
    def kill(self, pid: str) -> bool
    def cleanup_orphans(self)
    def get_running_agents(self) -> List[Dict]
```

## Process Management
- Use subprocess.Popen with start_new_session=True
- Write PIDs to ~/.claude-shared-state/pids/
- Implement heartbeat mechanism
- Auto-cleanup stale processes

## Agent Assignment
`InfrastructureAgent`

## Priority
P1 - High

## Dependencies
- Depends on: #002

## Labels
infrastructure, background-execution, process-management