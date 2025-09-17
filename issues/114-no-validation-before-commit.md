# Issue #114: No Validation Before Committing Changes

## Problem
Changes are committed without any validation, leading to broken code, syntax errors, and failed tests being pushed to repositories.

## Current Behavior
- No syntax checking before commit
- No test execution to verify changes
- Generated code not validated
- No linting or formatting checks
- Changes committed even if they break the build

## Expected Behavior
- Syntax validation for all file types
- Run relevant tests before committing
- Validate generated code compiles/runs
- Apply linting and formatting
- Block commits if validation fails
- Provide clear error messages

## Types of Validation Needed
1. **Syntax Validation**
   - Python: `ast.parse()` or `compile()`
   - JavaScript/TypeScript: Parser validation
   - YAML/JSON: Schema validation
   - Markdown: Structure validation

2. **Semantic Validation**
   - Import verification
   - Variable/function usage
   - Type checking where applicable

3. **Test Validation**
   - Run unit tests for modified files
   - Execute integration tests if needed
   - Check test coverage

## Files Affected
- `agents/pr_creation_agent.py` - Add validation step
- `agents/code_generation_agent.py` - Validate generated code
- `tools/validator.py` - New validation tool needed
- `agents/issue_fixer_agent.py` - Pre-commit validation

## Priority
HIGH - Prevents broken code from being committed

## Success Criteria
- [ ] Syntax validation for all languages
- [ ] Test execution before commit
- [ ] Linting and formatting checks
- [ ] Clear validation error messages
- [ ] Validation can be configured/disabled
- [ ] Performance impact is acceptable