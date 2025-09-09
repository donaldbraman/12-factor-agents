# Issue #205: Implement Error Telemetry System

## Summary
Build a lightweight, privacy-focused error telemetry system to automatically collect and analyze errors from all sister repositories using the 12-factor-agents framework.

## Problem
Currently, we don't know what errors users encounter in pin-citer, cite-assist, and other sister repos. We're flying blind when it comes to:
- Common failure patterns
- Which agents fail most often
- What file operations are problematic
- When git operations conflict

## Solution
Implement an automatic error telemetry system that:
1. Collects sanitized error data from all repos
2. Identifies patterns across repositories
3. Suggests fixes for common issues
4. Preserves user privacy

## Requirements

### Core Functionality
1. **Create TelemetryCollector class** in `core/telemetry.py`
   - Record errors with automatic sanitization
   - Store in JSONL format at `/tmp/12-factor-telemetry/`
   - Auto-detect repository name
   - Provide pattern analysis

2. **Integrate with BaseAgent** in `core/agent.py`
   - Add telemetry hooks to catch all errors
   - Make it zero-configuration (works via symlinks)
   - Include opt-out mechanism via environment variable

3. **Privacy Protection**
   - Sanitize user paths (/Users/name → /Users/***)
   - Remove API tokens, emails, IPs
   - Never log file contents
   - Truncate long strings

4. **Pattern Detection**
   - Identify errors occurring across multiple repos
   - Detect common failure types (file not found, permission denied, git locks)
   - Generate actionable fix suggestions

### Files to Create/Modify

**New Files:**
- `core/telemetry.py` - Main telemetry collector class
- `bin/telemetry_dashboard.py` - CLI dashboard for viewing analytics
- `tests/test_telemetry.py` - Comprehensive test suite

**Modified Files:**
- `core/agent.py` - Add telemetry hooks to BaseAgent
- `bin/agent.py` - Add telemetry CLI commands

### Implementation Details

```python
# core/telemetry.py structure
class TelemetryCollector:
    def __init__(self, telemetry_dir: Path = None):
        self.telemetry_dir = telemetry_dir or Path("/tmp/12-factor-telemetry")
        
    def record_error(self, repo_name: str, agent_name: str, 
                    error_type: str, error_message: str, 
                    context: Dict = None) -> str:
        # Sanitize and record
        
    def get_error_summary(self) -> Dict:
        # Analyze patterns
        
    def suggest_fixes(self) -> List[Dict]:
        # Return actionable suggestions

# Integration in core/agent.py
class BaseAgent(ABC):
    def __init__(self):
        self.telemetry = TelemetryCollector() if os.getenv("TELEMETRY_ENABLED", "true") == "true" else None
        
    def execute_task(self, task: str) -> ToolResponse:
        try:
            return self._execute_task_impl(task)
        except Exception as e:
            if self.telemetry:
                self.telemetry.record_error(
                    repo_name=self._detect_repo(),
                    agent_name=self.__class__.__name__,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
            raise
```

## Testing Requirements

1. **Privacy Tests** in `tests/test_telemetry_privacy.py`
   - Verify all sensitive data is sanitized
   - Check no passwords/tokens leak through
   - Validate truncation works

2. **Pattern Detection Tests** in `tests/test_telemetry_patterns.py`
   - Test identification of common errors
   - Verify cross-repo pattern detection
   - Check fix suggestions are generated

3. **Integration Tests** in `tests/test_telemetry_integration.py`
   - Test BaseAgent integration
   - Verify opt-out mechanism
   - Check performance impact < 10ms

## Success Criteria

1. **Working System**
   - Telemetry automatically collects errors from all agents
   - Zero configuration needed for sister repos
   - Privacy is fully preserved

2. **Useful Analytics**
   - Dashboard shows top errors and patterns
   - Fix suggestions are actionable
   - Trends are visible over time

3. **Performance**
   - < 10ms overhead per error
   - < 100MB storage for 30 days of data
   - No impact on normal operations

## Rollout Plan

1. **Phase 1**: Implement core telemetry (this issue)
2. **Phase 2**: Deploy to test branch and validate
3. **Phase 3**: Enable for pin-citer as pilot
4. **Phase 4**: Roll out to all sister repos
5. **Phase 5**: Build automated fix suggestions

## Example Dashboard Output

```
$ ./bin/agent telemetry summary

📊 Error Telemetry Report
━━━━━━━━━━━━━━━━━━━━━━━━
Last 7 days: 47 errors across 3 repositories

Top Issues:
1. FileNotFoundError (38%) - Missing citation files
   → Add existence checks before file operations
   
2. PermissionError (26%) - Locked files during writes  
   → Implement retry with exponential backoff
   
3. GitError (17%) - index.lock conflicts
   → Add mutex for git operations

Affected Repos:
- pin-citer: 22 errors (mostly FileNotFoundError)
- cite-assist: 18 errors (mostly PermissionError)  
- article-analytics: 7 errors (mixed)

📈 Trend: ↓ 23% decrease from last week
```

## Notes
- This system will help us proactively fix issues before users report them
- Privacy is paramount - we must never collect sensitive data
- The telemetry should "just work" via symlinks with zero setup

---

**Type**: feature
**Priority**: high
**Assignee**: IntelligentIssueAgent
**Labels**: telemetry, monitoring, privacy