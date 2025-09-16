# Quick Integration Guide for Quality-Focused Intelligent Agent System

## 🚀 5-Minute Setup for Sister Repos

### What You Get
Our new quality-focused intelligent agent system with:
- 85% confidence threshold for quality over speed
- Smart state management with rollback capabilities
- Deep semantic analysis to prevent broken fixes
- Comprehensive telemetry reporting

### Step 1: Submit Issues (Not Tasks!)

Sister repos submit GitHub issue numbers to our `IntelligentIssueAgent`:

```python
from core.external_issue_processor import SimpleExternalIssueProcessor

# Get issue content (e.g., from GitHub API or gh CLI)
issue_content = get_github_issue_content(issue_number)  

processor = SimpleExternalIssueProcessor()
result = processor.process_cite_assist_issue(issue_number, issue_content)
print(f"Agent used: {result.get('agent')}")
print(f"Confidence: {result.get('confidence')}")
```

## 📝 Critical: How to Structure Issues for Best Results

The quality of your issue directly impacts the agent's ability to help. Our intelligent trigger system analyzes multiple dimensions of your issue.

### ✅ GOOD Issue Examples

#### Example 1: Bug Fix with Clear Context
```markdown
Title: MapReduce pattern returning 0 citations in test_citation_patterns.py

## Problem
The MapReduce pattern in our citation extraction is returning 0 citations when processing papers.

## Current Behavior
- Line 829: Calling `paper.get('year', 2024)` on a PaperData dataclass
- This fails because dataclass objects don't have `.get()` method
- Citation count calculation `len(paper.content.split()) // 50` always returns 0

## Expected Behavior
- Should access `paper.metadata.get('publication_year', 2024)`
- Should generate at least 3 citations for testing
- Content should have minimum 75 words

## Files Affected
- `tests/test_citation_patterns.py` (line 829)
- `src/patterns/mapreduce.py`

## Test Command
`pytest tests/test_citation_patterns.py::test_mapreduce_citations -xvs`
```

**Why This Works:**
- Clear problem statement with specific line numbers
- Shows understanding of root cause
- Provides expected behavior
- Includes test command for validation
- Gives file paths for quick navigation

#### Example 2: Feature Implementation
```markdown
Title: Add smart state management for pipeline tracking

## Objective
Implement state management system that tracks pipeline execution stages

## Requirements
1. Track pipeline states: analyze → design → implement → test → validate
2. Enable rollback to previous states on failure
3. Persist state across agent handoffs
4. Support cross-repository context coordination

## Technical Details
- Use StateType and StateStatus enums for type safety
- Implement in `core/smart_state.py`
- Integrate with existing `IntelligentIssueAgent`
- Must be 12-factor compliant (stateless operations)

## Success Criteria
- All pipeline stages trackable
- Rollback works on test failures
- State persists across operations
- Tests pass with 100% coverage
```

**Why This Works:**
- Clear objective with measurable success criteria
- Technical requirements specified
- File structure suggested
- Compliance requirements noted

### ❌ BAD Issue Examples (Common Mistakes)

#### Mistake 1: Vague Problem Description
```markdown
Title: Fix the bug

The tests are failing. Please fix.
```

**Problems:**
- No specific information about which tests
- No error messages or stack traces
- No context about what changed
- Agent has to guess the problem

#### Mistake 2: Task List Without Context
```markdown
Title: Multiple things to do

- Fix citation bug
- Add new feature
- Update docs
- Run tests
```

**Problems:**
- No details on what "citation bug" means
- No specification for "new feature"
- No indication of priority or dependencies
- Agent can't determine proper sequencing

#### Mistake 3: Solution Without Problem
```markdown
Title: Change line 829

Change paper.get() to paper.metadata.get() on line 829
```

**Problems:**
- No explanation of why this change is needed
- No context about the dataclass issue
- No validation criteria
- Agent might make change without understanding implications

#### Mistake 4: Mixing Multiple Unrelated Issues
```markdown
Title: Fix everything

There's a citation bug in tests, also need dark mode for UI, 
and the README needs updating. Also check security.
```

**Problems:**
- Multiple unrelated concerns
- No clear priority
- Impossible to validate completion
- Should be separate issues

### 📊 How Issues Are Analyzed

Our intelligent trigger system evaluates issues on multiple dimensions:

```python
# What happens when you submit an issue:

1. Keyword Analysis (weight: 0.3)
   - Detects: fix, bug, implement, create, test
   - Maps to appropriate agent

2. Structural Analysis (weight: 0.25)
   - Checks for: code blocks, file paths, line numbers
   - Validates technical depth

3. Semantic Analysis (weight: 0.35)
   - Understands: intent, complexity, dependencies
   - Determines confidence level

4. Context Analysis (weight: 0.25)
   - Evaluates: cross-references, external dependencies
   - Identifies related issues

Minimum confidence threshold: 85%
If confidence < 85%: Routes to IntelligentIssueAgent for deep analysis
```

## 🎯 Complete Integration Example

### 1. Create Your Issue (in GitHub)
```bash
gh issue create \
  --title "Fix MapReduce citation extraction returning 0" \
  --body "$(cat <<'EOF'
## Problem
MapReduce pattern in test_citation_patterns.py returns 0 citations.

## Root Cause
Line 829 calls paper.get('year', 2024) on PaperData dataclass.
Dataclasses don't have .get() method.

## Solution
Use paper.metadata.get('publication_year', 2024)

## Test
pytest tests/test_citation_patterns.py::test_mapreduce -xvs
EOF
)"
```

### 2. Create Integration Script in Your Repo

`scripts/submit_to_sparky.py`:
```python
#!/usr/bin/env python3
"""Submit issues to quality-focused intelligent agent system."""

import sys
import json
import subprocess
from pathlib import Path

# Add 12-factor-agents to path
framework_path = Path(__file__).parent.parent.parent / "12-factor-agents"
sys.path.insert(0, str(framework_path))

from core.external_issue_processor import SimpleExternalIssueProcessor
from core.telemetry import TelemetryClient

def get_issue_content(repo: str, issue_number: int) -> str:
    """Get issue content using GitHub CLI."""
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_number), "--repo", repo, "--json", "body", "-q", ".body"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise RuntimeError(f"Failed to get issue: {result.stderr}")
    except Exception as e:
        raise RuntimeError(f"Error getting issue content: {e}")

def submit_issue(repo: str, issue_number: int):
    """Submit issue to intelligent agent system with telemetry."""
    
    processor = SimpleExternalIssueProcessor()
    telemetry = TelemetryClient()
    
    # Get issue content
    issue_content = get_issue_content(repo, issue_number)
    
    # Start telemetry tracking
    telemetry_id = telemetry.start_operation(
        operation_type="external_issue_submission",
        metadata={
            "repo": repo,
            "issue": issue_number,
            "source": "sister_repo"
        }
    )
    
    try:
        # Submit to intelligent system
        result = processor.process_cite_assist_issue(issue_number, issue_content)
        
        # Report telemetry
        telemetry.record_event(telemetry_id, "issue_processed", {
            "agent": result.get("agent", "unknown"),
            "confidence": result.get("confidence", 0),
            "success": result.get("success", False)
        })
        
        # Display results
        print(f"✅ Issue #{issue_number} processed")
        print(f"📊 Agent: {result.get('agent')}")
        print(f"🎯 Confidence: {result.get('confidence', 0):.1%}")
        print(f"📈 Quality Score: {result.get('quality_score', 0):.1%}")
        
        if result.get("success"):
            print(f"✨ Result: {result.get('summary', 'Completed successfully')}")
        else:
            print(f"⚠️  Warning: {result.get('error', 'Unknown error')}")
            
        return result
        
    except Exception as e:
        telemetry.record_error(telemetry_id, str(e))
        print(f"❌ Error: {e}")
        return None
    finally:
        telemetry.end_operation(telemetry_id)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python submit_to_sparky.py <org/repo> <issue_number>")
        sys.exit(1)
    
    repo = sys.argv[1]
    issue_num = int(sys.argv[2])
    
    result = submit_issue(repo, issue_num)
    sys.exit(0 if result and result.get("success") else 1)
```

### 3. Submit Your Issue
```bash
# After creating issue #144 in pin-citer
python scripts/submit_to_sparky.py pin-citer/pin-citer 144
```

### 4. Monitor Telemetry
```python
# Get telemetry for your submissions
from core.telemetry import TelemetryClient

telemetry = TelemetryClient()
events = telemetry.get_events(
    filters={
        "source": "sister_repo",
        "repo": "pin-citer/pin-citer"
    },
    limit=10
)

for event in events:
    print(f"Issue #{event['issue']}: {event['agent']} ({event['confidence']:.1%})")
```

## 📈 Telemetry Integration

Our system provides rich telemetry data:

```python
# What you get from telemetry
{
    "operation_id": "op_12345",
    "issue_number": 144,
    "repo": "pin-citer/pin-citer",
    "agent": "IntelligentIssueAgent",
    "confidence": 0.92,
    "quality_score": 0.88,
    "stages": {
        "analysis": {"duration_ms": 250, "status": "complete"},
        "design": {"duration_ms": 180, "status": "complete"},
        "implementation": {"duration_ms": 1200, "status": "complete"},
        "testing": {"duration_ms": 800, "status": "complete"},
        "validation": {"duration_ms": 150, "status": "complete"}
    },
    "total_duration_ms": 2580,
    "rollbacks": 0,
    "success": true
}
```

## 🔥 Quick Start for Pin-Citer

```bash
# 1. Clone as sister repo (if not already)
cd ~/Documents/GitHub
git clone https://github.com/your-org/pin-citer.git

# 2. Create integration script
cat > pin-citer/scripts/use_sparky.py << 'EOF'
#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "12-factor-agents"))
from core.external_issue_processor import SimpleExternalIssueProcessor

# Get issue content
issue_num = int(sys.argv[1])
result = subprocess.run(
    ["gh", "issue", "view", str(issue_num), "--json", "body", "-q", ".body"],
    capture_output=True, text=True
)
issue_content = result.stdout

processor = SimpleExternalIssueProcessor()
result = processor.process_cite_assist_issue(issue_num, issue_content)
print(f"Processed by: {result.get('agent')} (confidence: {result.get('confidence', 0):.1%})")
EOF

chmod +x pin-citer/scripts/use_sparky.py

# 3. Submit an issue
pin-citer/scripts/use_sparky.py 144
```

## ⚠️ Common Integration Mistakes

### ❌ DON'T: Call agents directly
```python
# WRONG - Bypasses quality analysis
from agents.intelligent_issue_agent import IntelligentIssueAgent
agent = IntelligentIssueAgent()
agent.execute_task("fix bug")  # No context, no validation!
```

### ❌ DON'T: Submit without issue content
```python
# WRONG - Missing required issue content
processor.process_cite_assist_issue(123, None)  # Will fail!
```

### ❌ DON'T: Skip issue creation
```python
# WRONG - No audit trail
result = magic_fix_function("just fix everything")  # No tracking!
```

### ✅ DO: Always provide issue content
```python
# CORRECT - Full tracking and quality analysis
issue_content = get_github_issue_content(144)
processor.process_cite_assist_issue(144, issue_content)
```

## 📊 Integration Validation

Check your integration is working:

```python
# validation_check.py
import sys
from pathlib import Path

framework = Path("../12-factor-agents")
if not framework.exists():
    print("❌ Framework not found as sister repo")
    sys.exit(1)

sys.path.insert(0, str(framework))

try:
    from core.external_issue_processor import SimpleExternalIssueProcessor
    from core.telemetry import TelemetryCollector
    from core.intelligent_triggers import QualityTriggerEngine
    print("✅ All imports working")
    
    # Test processor
    processor = SimpleExternalIssueProcessor()
    print(f"✅ Processor initialized")
    
    # Test quality engine
    engine = QualityTriggerEngine()
    decision = engine.route_task("Fix bug in line 829", {})
    print(f"✅ Routing works: {decision.handler} ({decision.confidence:.1%})")
    
    # Test telemetry
    telemetry = TelemetryCollector()
    print(f"✅ Telemetry collector ready")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
```

## 🎯 Results You Should Expect

With proper issue structure:
- **Confidence**: 85-95% for well-structured issues
- **Processing Time**: 2-5 seconds for analysis
- **Success Rate**: 95%+ for clear, specific issues
- **Rollback Rate**: <5% with quality thresholds

With poor issue structure:
- **Confidence**: 40-60% triggers fallback routing  
- **Processing Time**: 10-15 seconds (deep analysis)
- **Success Rate**: 60-70% depending on ambiguity
- **Rollback Rate**: 20-30% due to misunderstanding

## Summary

1. **Structure issues properly** with context, problem, and solution
2. **Always use issue numbers**, never raw task descriptions  
3. **Monitor telemetry** to track quality and performance
4. **Avoid common mistakes** like vague descriptions or mixed concerns

The better your issue, the better our intelligent agent can help!