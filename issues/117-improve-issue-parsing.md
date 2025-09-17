# Issue #117: Improve Issue Parsing Logic

## Problem
Issue parsing is rudimentary and fails to understand the semantic structure of issues, leading to incorrect interpretations and implementations.

## Current Behavior
- Basic regex pattern matching
- No understanding of markdown structure
- Cannot differentiate sections properly
- Misses context and relationships
- No semantic understanding

## Expected Behavior
- Understand markdown hierarchy
- Parse semantic sections (Problem, Solution, etc.)
- Recognize common patterns:
  - Current/Desired state
  - Given/When/Then
  - Problem/Solution
  - Before/After
- Extract metadata correctly
- Understand code blocks in context

## Parsing Improvements Needed
1. **Structural Parsing**
   - Markdown AST parsing
   - Section hierarchy understanding
   - Code block language detection
   - List and table parsing

2. **Semantic Understanding**
   - Intent recognition
   - Requirement extraction
   - Example identification
   - Success criteria parsing

3. **Pattern Recognition**
   - Common issue templates
   - Bug report patterns
   - Feature request patterns
   - Documentation patterns

## Implementation Ideas
- Use markdown parser (e.g., mistune)
- Build semantic analyzer on top of AST
- Pattern library for common formats
- Machine learning for intent classification
- Context-aware parsing

## Files Affected
- `tools/issue_parser.py` - Core parsing logic
- `agents/issue_decomposer_agent.py` - Use improved parser
- `agents/issue_fixer_agent.py` - Better issue understanding
- `core/patterns.py` - Pattern library (new)

## Priority
MEDIUM - Improves accuracy significantly

## Success Criteria
- [ ] Markdown AST parsing implemented
- [ ] Semantic section recognition
- [ ] Common patterns recognized
- [ ] Intent correctly identified
- [ ] Examples vs requirements differentiated
- [ ] Tests for various issue formats
- [ ] Documentation of supported patterns