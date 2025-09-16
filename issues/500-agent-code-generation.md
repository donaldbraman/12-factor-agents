# Issue #500: Enable Agents to Write Code, Test, and Create PRs

## Problem
Our IntelligentIssueAgent successfully analyzes issues but fails to:
1. Write actual code fixes
2. Test the changes
3. Create pull requests
4. Apply fixes to sister repositories

When processing pin-citer issue #145, the agent created an empty planning document instead of fixing the document creation pipeline bug.

## Current Behavior
```python
# What happens now:
1. Agent receives issue #145 from pin-citer
2. Creates empty file: issues/145-cite-assist-inspect-document.md
3. Updates state: "pipeline completed"
4. No code written, no PR created, issue remains unfixed
```

## Expected Behavior
```python
# What should happen:
1. Agent receives issue #145 from pin-citer
2. Analyzes the document creation pipeline bug
3. Writes fix code for google_docs_writer.py
4. Runs validation tests
5. Creates feature branch
6. Commits changes
7. Creates PR with detailed description
8. Updates issue with PR link
```

## Root Cause Analysis

### Missing Capabilities in IntelligentIssueAgent:
1. **No Code Generation**: Only creates empty templates
2. **No File Modification**: Can't edit sister repo files
3. **No Git Operations**: Can't create branches or commits
4. **No PR Creation**: Missing GitHub PR API integration
5. **No Test Execution**: Can't validate fixes

## Implementation Plan

### Phase 1: Code Generation
```python
class IntelligentIssueAgent:
    def generate_fix_code(self, issue_analysis):
        """Generate actual code to fix the issue"""
        # Analyze issue type (bug fix, feature, refactor)
        # Identify affected files
        # Generate code changes
        # Return dict of file_path -> new_content
```

### Phase 2: File Modification
```python
    def apply_code_changes(self, repo_path, changes):
        """Apply generated code to actual files"""
        # Navigate to sister repo
        # Read existing files
        # Apply changes intelligently
        # Preserve code style and structure
```

### Phase 3: Test Execution
```python
    def run_validation_tests(self, repo_path, test_commands):
        """Execute tests to validate fix"""
        # Run provided test commands
        # Capture output
        # Determine success/failure
        # Rollback on failure
```

### Phase 4: PR Creation
```python
    def create_pull_request(self, repo_path, branch_name, issue_number):
        """Create PR with fix"""
        # Create feature branch
        # Commit changes with descriptive message
        # Push to remote
        # Create PR via GitHub API
        # Link PR to issue
```

## Test Case: Pin-Citer Issue #145

The document creation pipeline bug is perfect for testing because:
1. Clear problem: Empty documents with no content
2. Known location: google_docs_writer.py
3. Validation available: validate_document_comprehensive.py
4. Success criteria: 5/5 tests passing

### Expected Fix Code:
```python
# In google_docs_writer.py
def insert_template_content(self, document_id, template_content):
    """Insert template content into document"""
    requests = []
    
    # Parse template for content and citations
    lines = template_content.split('\n')
    current_index = 1
    
    for line in lines:
        # Insert text
        requests.append({
            'insertText': {
                'location': {'index': current_index},
                'text': line + '\n'
            }
        })
        current_index += len(line) + 1
        
        # Process citations
        if '[CITE:' in line:
            citation_match = re.search(r'\[CITE: ([^\]]+)\]', line)
            if citation_match:
                self.create_footnote_for_citation(
                    document_id, 
                    citation_match.group(1),
                    current_index
                )
    
    # Execute batch update
    self.docs_service.documents().batchUpdate(
        documentId=document_id,
        body={'requests': requests}
    ).execute()
```

## Success Criteria
1. ✅ Agent generates working code fix
2. ✅ Code is applied to correct files
3. ✅ Tests pass (5/5 validation tests)
4. ✅ PR is created with:
   - Descriptive title
   - Problem/solution description
   - Test results
   - Link to issue
5. ✅ Issue is updated with PR link
6. ✅ Sister repo can merge and close issue

## Configuration Requirements

```json
{
  "agent_capabilities": {
    "code_generation": true,
    "file_modification": true,
    "git_operations": true,
    "pr_creation": true,
    "test_execution": true,
    "cross_repo_access": true
  },
  "quality_thresholds": {
    "min_test_coverage": 0.8,
    "max_pr_size_lines": 500,
    "require_test_pass": true,
    "require_lint_pass": true
  }
}
```

## Implementation Priority
**CRITICAL** - Without this capability, agents can only analyze but not fix issues, making the entire system ineffective for actual development work.

## Related Issues
- Pin-citer #145: Document creation pipeline (waiting for fix)
- Pin-citer #144: MapReduce pattern bug (manually fixed after agent syntax errors)

## Technical Requirements
1. Git operations via subprocess or GitPython
2. GitHub API via PyGithub or gh CLI
3. Code generation via templates + AST manipulation
4. Test execution via subprocess
5. Rollback capability for failed attempts

## Risk Mitigation
1. **Sandbox Testing**: Test in feature branches first
2. **Validation Gates**: Require tests to pass before PR
3. **Human Review**: Keep PRs as draft initially
4. **Rollback**: Automatic revert on test failure
5. **Incremental Changes**: Small, focused PRs

## Example Usage
```bash
# Process issue with full capabilities
python bin/agent.py process-issue pin-citer 145 --write-code --test --create-pr

# Expected output:
🔍 Analyzing issue #145...
✍️ Generating fix code...
📝 Applying changes to 3 files...
🧪 Running validation tests...
✅ Tests passed: 5/5
🌿 Creating branch: fix/issue-145-document-creation
💾 Committing changes...
🚀 Creating PR #146...
🔗 Updated issue #145 with PR link
✨ Fix complete!
```

## Dog Food Testing
Once implemented, we'll test by:
1. Creating this capability in IntelligentIssueAgent
2. Using it to fix pin-citer issue #145
3. Validating the document creation works
4. Confirming PR is properly created
5. Having the fix actually merged

This will prove our agents can do real development work, not just planning!