# Bug-to-PR Pipeline Documentation

## Overview
Complete automated pipeline for bug detection, investigation, and resolution.

## Pipeline Flow
```
Bug Report → Investigation → GitHub Issue → SPARKY Fix → Pull Request
```

## Components

### 1. Bug Investigation Agent
- **Location**: `agents/bug_investigation_agent_simple.py`
- **Patterns Detected**: 8 patterns including validation failures, ExecutionContext errors
- **Confidence**: 90% for known patterns

### 2. Bug-to-Issue-to-PR Pipeline
- **Location**: `core/bug_to_issue_to_pr.py`
- **Features**:
  - Rate limiting and duplicate detection
  - Smart repository routing
  - Automatic GitHub issue creation
  - SPARKY integration for fixes

### 3. Bug Reporter
- **Location**: `core/agent_bug_reporter.py`
- **Webhook**: `scripts/bug_report_webhook.py`
- **Features**:
  - Centralized bug collection
  - GitHub issue creation with labels
  - Fallback local logging

### 4. SPARKY Integration
- **Location**: `core/sparky_integration.py`
- **Capabilities**:
  - Clone repositories
  - Create branches
  - Apply fixes
  - Create pull requests

## Usage

### Submit Bug Report
```python
from core.bug_to_issue_to_pr import BugToIssueToPR, AgentBugReport

bug = AgentBugReport(
    agent_name='your-agent',
    agent_version='1.0.0',
    repo_name='owner/repository',
    error_type='ValidationError',
    error_message='Validation failed: 0% coverage',
    task_description='Description of what failed',
    severity='high'
)

pipeline = BugToIssueToPR()
result = pipeline.process_bug_report(bug)
```

### Start Webhook Server
```bash
uv run python scripts/bug_report_webhook.py --port 8080
```

## Supported Bug Patterns

1. **json_serialization** - JSON serialization errors
2. **routing_error** - Incorrect agent routing
3. **state_mutation** - State being mutated
4. **unbound_variable** - Variables accessed before assignment
5. **github_api** - GitHub API failures
6. **agent_assignment** - Unassigned issues
7. **execution_context_attribute** - Missing ExecutionContext attributes
8. **validation_failure** - Disconnected validation methods

## Configuration

### Environment Variables
- `GH_TOKEN` - GitHub authentication token
- `NODE_OPTIONS="--max-old-space-size=4096"` - Memory for Claude Code

### Labels Required in Target Repos
- `bug` - Universal bug label (required)
- Priority labels (optional): `critical`, `high`, `medium`, `low`

## Testing

Test the pipeline:
```bash
uv run python core/bug_to_issue_to_pr.py --test
```

Test SPARKY integration:
```bash
uv run python core/sparky_integration.py --test
```

## Results
- Successfully created issues in multiple repos
- SPARKY creates branches and PRs automatically
- 90% confidence on known patterns
- Fallback logging when GitHub unavailable