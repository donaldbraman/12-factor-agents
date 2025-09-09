# Error Telemetry System Specification

## Overview
Lightweight, privacy-focused error telemetry system for 12-factor-agents framework to identify and fix common issues across all sister repositories.

## Goals
1. **Identify common failures** across pin-citer, cite-assist, article-analytics, etc.
2. **Preserve privacy** - no sensitive data, user paths, or secrets
3. **Zero configuration** - works automatically via symlinks
4. **Actionable insights** - detect patterns and suggest fixes

## Architecture

### 1. Telemetry Collector (Core Component)
Location: `core/telemetry.py`

**Responsibilities:**
- Record sanitized error events
- Auto-detect repository name
- Write to shared telemetry directory
- Provide pattern analysis

**Key Methods:**
```python
class TelemetryCollector:
    def record_error(repo_name, agent_name, error_type, error_message, context)
    def get_error_summary() -> Dict[patterns, suggestions]
    def _sanitize_message(message) -> str  # Remove sensitive data
```

### 2. BaseAgent Integration
Location: `core/agent.py` (modification)

**Auto-telemetry on errors:**
```python
class BaseAgent:
    def __init__(self):
        self.telemetry = TelemetryCollector() if TELEMETRY_ENABLED else None
        
    def execute_task(self, task):
        try:
            return self._execute_task_impl(task)
        except Exception as e:
            if self.telemetry:
                self.telemetry.record_error(...)
            raise
```

### 3. Storage Format
Location: `/tmp/12-factor-telemetry/` (or `~/.12-factor-telemetry/`)

**File Structure:**
```
/tmp/12-factor-telemetry/
├── all_errors.jsonl          # Central log
├── pin-citer_errors.jsonl    # Repo-specific
├── cite-assist_errors.jsonl
└── telemetry.lock            # Prevent conflicts
```

**Event Format (JSONL):**
```json
{
  "timestamp": "2024-01-09T10:30:00",
  "repo": "pin-citer",
  "agent": "IssueProcessorAgent",
  "error_type": "FileNotFoundError",
  "error_message": "File not found: /Users/***/Documents/file.txt",
  "context": {
    "operation": "read",
    "file_type": "txt",
    "retry_count": 0
  },
  "telemetry_id": "a3f4b2c1"
}
```

## Privacy Protection

### Data Sanitization Rules
1. **User paths**: `/Users/john/` → `/Users/***/`
2. **API tokens**: `sk-abc123...` → `***TOKEN***`
3. **Emails**: `user@example.com` → `***EMAIL***`
4. **IP addresses**: `192.168.1.1` → `***IP***`
5. **File contents**: Never logged
6. **Issue descriptions**: Truncated to 100 chars

### Opt-out Mechanism
```python
# In .env or environment
TELEMETRY_ENABLED=false

# Or in code
BaseAgent(telemetry_enabled=False)
```

## Error Patterns to Detect

### 1. File Operation Failures
- **Pattern**: Multiple "File not found" errors
- **Detection**: > 3 FileNotFoundError in 24 hours
- **Suggestion**: "Add file existence checks before operations"

### 2. Permission Issues
- **Pattern**: Permission denied on file writes
- **Detection**: PermissionError with "locked" or "denied"
- **Suggestion**: "Implement retry logic with exponential backoff"

### 3. Git Operation Conflicts
- **Pattern**: Git index.lock errors
- **Detection**: "index.lock" in error message
- **Suggestion**: "Add git lock detection and retry"

### 4. Missing Methods
- **Pattern**: AttributeError on agent methods
- **Detection**: Same AttributeError across multiple repos
- **Suggestion**: "Framework bug - method missing from BaseAgent"

### 5. Import Failures
- **Pattern**: ModuleNotFoundError for agents
- **Detection**: "No module named 'agents'"
- **Suggestion**: "Check symlink configuration"

## Analytics Dashboard

### CLI Command
```bash
# Show error summary
./bin/agent telemetry summary

# Show patterns
./bin/agent telemetry patterns

# Clear old data (> 30 days)
./bin/agent telemetry clean
```

### Output Example
```
📊 Telemetry Summary (Last 7 days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Errors: 47
Affected Repos: 3 (pin-citer, cite-assist, article-analytics)

Top Error Types:
1. FileNotFoundError (18 occurrences) - 38%
2. PermissionError (12 occurrences) - 26%
3. GitError (8 occurrences) - 17%

🎯 Detected Patterns:
1. File operations failing in cite-assist
   → Suggestion: Check file paths are absolute
   
2. Git locks in all repos during parallel execution
   → Suggestion: Add mutex for git operations

3. IssueFixerAgent missing _intelligent_processing
   → Suggestion: Update framework - known bug

📈 Trend: Errors decreasing (↓ 23% from last week)
```

## Implementation Phases

### Phase 1: Core Telemetry (Week 1)
- [ ] Create TelemetryCollector class
- [ ] Add sanitization methods
- [ ] Implement JSONL storage
- [ ] Add pattern detection

### Phase 2: Integration (Week 2)
- [ ] Integrate with BaseAgent
- [ ] Add opt-out mechanism
- [ ] Test with sister repos
- [ ] Verify privacy protection

### Phase 3: Analytics (Week 3)
- [ ] Build CLI dashboard
- [ ] Add trend analysis
- [ ] Create automated reports
- [ ] Add fix suggestions

## Success Metrics
1. **Discovery Rate**: Find 80% of common errors within first week
2. **Privacy**: Zero sensitive data leaks
3. **Performance**: < 10ms overhead per error
4. **Actionability**: 90% of patterns have fix suggestions

## Testing Requirements
1. Unit tests for sanitization
2. Integration tests with agents
3. Privacy audit of collected data
4. Performance benchmarks
5. Cross-repo validation

## Security Considerations
1. Telemetry files use 600 permissions (user-only)
2. No network transmission (local only)
3. Automatic cleanup after 30 days
4. No execution of telemetry data
5. Read-only analysis

## Future Enhancements
1. Success telemetry (not just errors)
2. Performance metrics
3. Feature usage tracking (opt-in)
4. Automatic fix suggestions via AI
5. Integration with GitHub Issues