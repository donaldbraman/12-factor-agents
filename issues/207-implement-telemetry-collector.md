# Issue #207: Implement TelemetryCollector from Comprehensive Spec

## Problem
We have an excellent telemetry specification (docs/TELEMETRY_SPEC.md) and comprehensive tests (tests/test_telemetry_system.py), but `core/telemetry.py` only contains a placeholder. We need to implement the actual TelemetryCollector class to match our spec and pass our tests.

## Background
- ✅ Specification complete: docs/TELEMETRY_SPEC.md  
- ✅ Tests written: tests/test_telemetry_system.py (includes TelemetryCollector class)
- ❌ Implementation missing: core/telemetry.py is just placeholder

The tests already contain a working TelemetryCollector implementation that we can extract and use as the foundation.

## Requirements

### 1. Implement TelemetryCollector Class
Replace the placeholder in `core/telemetry.py` with a fully functional class that includes:

**Core Methods:**
```python
class TelemetryCollector:
    def __init__(self, telemetry_dir: Path = None):
        # Store in /tmp/12-factor-telemetry by default
    
    def record_error(self, repo_name: str, agent_name: str, 
                    error_type: str, error_message: str, 
                    context: Dict = None) -> str:
        # Record error with privacy protection
        
    def get_error_summary(self) -> Dict:
        # Analyze patterns and provide insights
        
    def _sanitize_message(self, message: str) -> str:
        # Remove sensitive data (paths, tokens, emails)
        
    def _sanitize_context(self, context: Dict) -> Dict:
        # Keep only safe context keys
        
    def _hash_if_needed(self, repo_name: str) -> str:
        # Hash private repo names
```

### 2. Privacy Protection Requirements
Must sanitize all sensitive data:
- User paths: `/Users/name/` → `/Users/***/`
- API tokens: `sk-abc123...` → `***TOKEN***`
- Emails: `user@example.com` → `***EMAIL***`
- Long tokens: `[a-zA-Z0-9]{32,}` → `***TOKEN***`

### 3. Storage Format
Store as JSONL files:
- Central log: `/tmp/12-factor-telemetry/all_errors.jsonl`
- Repo-specific: `/tmp/12-factor-telemetry/{repo}_errors.jsonl`

Event format:
```json
{
  "timestamp": "2024-01-09T10:30:00",
  "repo": "pin-citer",
  "agent": "IssueProcessorAgent", 
  "error_type": "FileNotFoundError",
  "error_message": "File not found: /Users/***/Documents/file.txt",
  "context": {"operation": "read", "file_type": "txt"},
  "telemetry_id": "a3f4b2c1"
}
```

### 4. Pattern Detection
Implement intelligence to detect:
- **File not found patterns** (>3 occurrences)
- **Permission denied patterns** 
- **Git lock conflicts**
- **Cross-repo framework bugs** (same error in 3+ repos)

With actionable suggestions:
- "Add file existence checks before operations"
- "Implement retry logic with exponential backoff"  
- "Add git index.lock handling"
- "Framework bug - method missing from BaseAgent"

## Implementation Approach

### Option 1: Extract from Tests (Recommended)
The TelemetryCollector class in `tests/test_telemetry_system.py` is already fully implemented and tested. Extract it to `core/telemetry.py`.

### Option 2: Build from Spec
Implement from scratch following docs/TELEMETRY_SPEC.md exactly.

## Success Criteria

### 1. All Tests Pass
```bash
# These should all pass
uv run python -m pytest tests/test_telemetry_system.py -v
uv run python tests/test_telemetry_system.py  # Standalone
```

### 2. Privacy Protection Works
```python
from core.telemetry import TelemetryCollector
collector = TelemetryCollector()

# Test privacy
collector.record_error(
    repo_name="test-repo",
    agent_name="TestAgent", 
    error_type="TestError",
    error_message="Token sk-1234567890abcdef user@example.com at /Users/john/secret",
    context={"secret": "hide_me", "operation": "test"}
)

# Verify sanitization worked
summary = collector.get_error_summary()
# Should contain: "***TOKEN***", "***EMAIL***", "/Users/***/secret"
# Should NOT contain: "sk-1234567890abcdef", "user@example.com", "hide_me"
```

### 3. Pattern Detection Works
```python
# Simulate repeated errors
for i in range(5):
    collector.record_error("repo", "agent", "FileNotFoundError", "File not found")

patterns = collector.get_error_summary()["patterns"] 
assert len(patterns) > 0
assert "File not found errors" in str(patterns)
```

### 4. Real Usage Test
```python
# Test actual integration
import sys
sys.path.insert(0, 'core')

from telemetry import TelemetryCollector

collector = TelemetryCollector()
telemetry_id = collector.record_error(
    repo_name="12-factor-agents",
    agent_name="IntelligentIssueAgent",
    error_type="RuntimeError", 
    error_message="Test error for validation",
    context={"test": True}
)

print(f"✅ Recorded with ID: {telemetry_id}")
summary = collector.get_error_summary()
print(f"📊 Total errors: {summary['total_errors']}")
```

## Files to Modify

**Primary:**
- `core/telemetry.py` - Replace placeholder with full implementation

**Optional:**
- `core/agent.py` - Add telemetry integration hooks (future)
- `bin/agent.py` - Add telemetry CLI commands (future)

## Testing Strategy

1. **Unit Tests**: All methods work in isolation
2. **Integration Tests**: Works with file system and multiple repos
3. **Privacy Tests**: No sensitive data leaks
4. **Performance Tests**: < 10ms per error record
5. **Regression Tests**: Existing functionality unaffected

## Dependencies
- `pathlib` (built-in)
- `json` (built-in) 
- `datetime` (built-in)
- `hashlib` (built-in)
- `re` (built-in)

No external dependencies needed!

## Expected Outcome
After implementation:
- ✅ Comprehensive error telemetry system
- ✅ Privacy-protected data collection
- ✅ Pattern detection with actionable insights
- ✅ Foundation for retry logic improvements
- ✅ Ready for BaseAgent integration

---

**Type**: implementation
**Priority**: high
**Assignee**: IntelligentIssueAgent
**Labels**: telemetry, implementation, privacy
**Dependencies**: Issue #205 (spec), tests already written
**Estimated**: 1-2 hours (mostly extraction and cleanup)