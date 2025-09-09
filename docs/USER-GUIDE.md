# SmartIssueAgent User Guide
**Zero-to-productive in 2 minutes. No fluff, only actionable intelligence.**

## Quick Start (30 seconds)

```bash
# Submit ANY issue - complexity detection is automatic
cd /path/to/12-factor-agents
uv run python bin/agent.py run SmartIssueAgent "issue-number"
```

**That's it.** The system handles everything else automatically.

## What Happens Automatically

When you submit an issue, SmartIssueAgent:

1. **Analyzes complexity** (atomic → enterprise)  
2. **Routes intelligently** (direct handling vs decomposition)
3. **Creates 12-Factor compliant sub-issues** if needed
4. **Assigns appropriate agents** automatically
5. **Orchestrates execution** across all sub-tasks

You never think about which agent to use or how complex your issue is.

## Real Examples by Complexity

### Atomic (Handled Directly)
```bash
# Simple typo fix
uv run python bin/agent.py run SmartIssueAgent "088"
```
**Output:** Direct fix applied immediately.

### Simple (Handled Directly)  
```bash
# Single file update
uv run python bin/agent.py run SmartIssueAgent "086"
```
**Output:** File updated, task completed.

### Moderate (Auto-Decomposed)
```bash
# Multi-file changes
uv run python bin/agent.py run SmartIssueAgent "083" 
```
**Output:** 
```
🧩 Issue decomposed into 3 sub-issues
🚀 Processing sub-issues...
   ✅ Update testing_agent.py
   ✅ Update benchmarks.py  
   ✅ Update test.yml
📊 Overall result: 3/3 sub-issues completed
```

### Complex (Auto-Decomposed)
```bash
# Documentation overhaul with numbered sections
uv run python bin/agent.py run SmartIssueAgent "064"
```
**Output:**
```
🔍 Analyzing complexity...
📊 Complexity: complex (confidence: 80.0%)
🧩 Issue decomposed into 4 sub-issues
   📋 Fix CLI Commands in README
   📋 Fix Pipeline Example in INTEGRATION-GUIDE.md  
   📋 Add Complete Imports Section
   📋 Add IssueFixerAgent Documentation
```

### Enterprise (Auto-Decomposed)
```bash  
# System-wide changes
uv run python bin/agent.py run SmartIssueAgent "080"
```
**Output:** 
```
📊 Complexity: enterprise (confidence: 90.0%)
🧩 Issue decomposed into 6 sub-issues
   📋 Create Core framework foundation
   📋 Implement Database schema changes
   📋 Design and implement API redesign
   [... 3 more focused tasks]
```

## Understanding Results

### Success (Direct Handling)
```
✅ Issue is simple - handling directly
✅ Task completed successfully
```
→ **Done.** Your issue was fixed immediately.

### Success (Decomposed)
```
🧩 Issue decomposed into N sub-issues
📊 Overall result: N/N sub-issues completed  
✅ Complex issue orchestrated successfully
```
→ **Done.** All sub-tasks completed successfully.

### Partial Success
```
📊 Overall result: 2/4 sub-issues completed
❌ Some sub-issues failed
```
→ **Check the details.** Some tasks succeeded, others need attention.

## Writing Issues That Decompose Well

### ✅ Good Issue Structure
```markdown
# Issue: Update Documentation with Correct Usage

## Description  
Multiple files need updates to fix CLI commands.

### 1. Fix CLI Commands in README
Current:
```bash
uv run agent list
```

Should be:
```bash  
uv run python bin/agent.py list
```

### 2. Update Integration Guide
Add missing imports to all examples.

## Files to Update
- README.md
- docs/INTEGRATION-GUIDE.md
```

**Why this works:**
- Numbered sections → automatic sub-issue creation
- Current/Should patterns → actionable changes  
- Explicit file lists → clear targets
- Specific requirements → executable tasks

### ❌ Poor Issue Structure  
```markdown
# Issue: Make everything better

Please improve the system somehow.
```

**Why this fails:**
- Vague requirements → no actionable tasks
- No specific files → unclear targets
- No current/should patterns → no clear changes

## Advanced Usage

### View Available Agents
```bash
uv run python bin/agent.py list
```

### Get Agent Information
```bash
uv run python bin/agent.py info SmartIssueAgent
```

### Run Other Agents Directly
```bash  
# For specific use cases
uv run python bin/agent.py run TestingAgent "run all tests"
uv run python bin/agent.py run IssueFixerAgent "061"
```

### Orchestrate Pipelines
```bash
uv run python bin/agent.py orchestrate issue-pipeline
```

## 12-Factor Principles Applied

SmartIssueAgent follows [12-Factor Agent](https://github.com/humanlayer/12-factor-agents) principles:

- **Factor 1**: Natural Language → Tool Calls (issue → actions)
- **Factor 4**: Structured Outputs (clear sub-issues)  
- **Factor 8**: Own Your Control Flow (explicit steps)
- **Factor 10**: Small, Focused Agents (atomic sub-tasks)
- **Factor 12**: Stateless Reducer (clear input/output)

This ensures reliable, predictable, production-ready agent behavior.

## Troubleshooting

### Issue Not Found
```
❌ No issue file found for #123
```
→ **Check:** Issue file exists in `issues/` directory

### Agent Failed
```
❌ Task failed: Could not determine what changes to make
```  
→ **Fix:** Add more specific Current/Should code blocks to your issue

### Complexity Misdetection
```
📊 Complexity: enterprise (expected: simple)
```
→ **Normal:** System errs on the side of caution. Still handles correctly.

## That's It

**You now know everything needed to be productive with SmartIssueAgent.**

Submit issues, get results. The system handles all complexity automatically.

---
*Built with 12-Factor Agent principles for production reliability.*