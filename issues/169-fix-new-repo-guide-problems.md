# Issue #169: Fix New Repo Guide Critical Problems

## Description
Following the NEW-REPO-GUIDE.md step-by-step reveals multiple critical issues that prevent new repositories from using the system.

## Problems Found

### 1. SmartIssueAgent Not Available
**Location:** Guide promises SmartIssueAgent will be available after setup
**Current:** `./bin/agent list` shows 12 agents but no SmartIssueAgent
**Impact:** Guide's main example `./bin/agent run SmartIssueAgent "001"` fails completely

### 2. Setup Script Creates Broken Instructions  
**Location:** setup-new-repo.sh creates test issue that references missing agent
**Current:** Test issue says to run SmartIssueAgent but it doesn't exist
**Impact:** New users immediately hit failure on their first test

### 3. Remote Submodule Missing New Agents
**Location:** GitHub remote repository doesn't include new agent files
**Current:** Submodule pulls from remote that lacks SmartIssueAgent, IssueDecomposerAgent, etc.
**Impact:** Both manual and automated setup methods fail

### 4. Guide Documentation Mismatch
**Location:** Guide examples throughout assume agents exist
**Current:** All SmartIssueAgent examples will fail
**Impact:** Complete guide is unusable for actual new repositories

## Root Cause
The new agent system (SmartIssueAgent, IssueDecomposerAgent, FailureAnalysisAgent, etc.) exists locally but was never committed/pushed to the remote repository that submodules reference.

## Required Fix
```bash
# Current (broken)
./bin/agent run SmartIssueAgent "001"
# Result: Agent 'SmartIssueAgent' not found

# Should work after fix  
./bin/agent run SmartIssueAgent "001"
# Result: Processing issue with complexity detection...
```

## Files That Need Updates
- Push new agents to remote repository first
- Update setup-new-repo.sh to create working test issues
- Update NEW-REPO-GUIDE.md examples to match available agents
- Verify all guide steps work end-to-end

## Success Criteria
- [ ] Guide can be followed step-by-step without errors
- [ ] SmartIssueAgent appears in agent list after setup
- [ ] All guide examples work as documented
- [ ] New repositories can successfully process first issue
- [ ] Both automated and manual setup methods work

## Test Plan
1. Follow guide exactly as written with fresh repository
2. Verify each step produces expected output
3. Test all example commands work as shown
4. Confirm new repo can process real issues

## Type
bug

## Priority
critical

## Status
open

## Assignee
smart_issue_agent