# Issue #008: Externalize Hardcoded Prompts (Factor 2)

## Description
Multiple agents have hardcoded prompts that violate Factor 2: Own Your Prompts. These should be moved to external prompt templates.

## Files with Hardcoded Prompts
- agents/code_review_agent.py (lines ~170-200)
- agents/intelligent_issue_agent.py (multiple locations)
- agents/issue_processor_agent.py 
- agents/failure_analysis_agent.py
- agents/component_migration_agent.py
- agents/issue_orchestrator_agent.py
- agents/pr_creation_agent.py

## Solution
1. Move prompts to `prompts/agents/` directory
2. Use `core/simple_prompts.py` format_prompt() function
3. Version control prompt templates separately
4. Allow runtime prompt customization

## Priority
Medium - Improves maintainability and flexibility

## Type
refactoring

## Status
open