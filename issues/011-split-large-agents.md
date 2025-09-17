# Issue #011: Split Large Agents (Factor 10)

## Description
Several agents violate Factor 10: Small, Focused Agents by having too many responsibilities.

## Oversized Agents
1. **intelligent_issue_agent.py** (1155 lines)
   - File analysis
   - Issue parsing
   - Solution generation
   - Implementation
   - Testing

2. **issue_fixer_agent.py** (500+ lines)
   - Multiple tool implementations
   - Complex orchestration

3. **issue_orchestrator_agent.py**
   - Dispatcher, updater, planner in one

## Solution
Split into focused agents:
- IssueAnalyzerAgent - Just analyze issues
- SolutionGeneratorAgent - Generate solutions
- ImplementationAgent - Implement changes
- ValidationAgent - Validate changes
- Each <200 lines, single responsibility

## Benefits
- Easier to test
- Better reusability
- Clearer interfaces
- Simpler maintenance

## Priority
Medium - Improves architecture

## Type
refactoring

## Status
open