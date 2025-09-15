# Issue #424: Create Comprehensive Tests for PRReviewAgent

## Description

Implement comprehensive test coverage for the PRReviewAgent, including unit tests for each tool, integration tests for the full workflow, and end-to-end tests with real GitHub API interactions.

## Objectives

1. Unit test each tool independently
2. Integration test the agent workflow
3. Mock GitHub API interactions
4. Test error handling and edge cases
5. Validate output formats

## Technical Requirements

### 1. Unit Tests (`tests/test_pr_review_agent.py`)

```python
import unittest
from unittest.mock import Mock, patch, MagicMock
from agents.pr_review_agent import (
    PRReviewAgent,
    FetchPRTool,
    AnalyzeCodeTool,
    PostCommentTool,
    UpdatePRDescriptionTool
)

class TestFetchPRTool(unittest.TestCase):
    @patch('agents.pr_review_agent.Github')
    def test_fetch_pr_success(self, mock_github):
        # Mock PR data
        mock_pr = Mock()
        mock_pr.number = 123
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.get_files.return_value = []
        
        mock_repo = Mock()
        mock_repo.get_pull.return_value = mock_pr
        
        mock_github.return_value.get_repo.return_value = mock_repo
        
        tool = FetchPRTool()
        result = tool.execute(pr_number=123, repo="test/repo")
        
        assert result.success
        assert result.data["number"] == 123
        assert result.data["title"] == "Test PR"

class TestAnalyzeCodeTool(unittest.TestCase):
    def test_analyze_with_guidelines(self):
        tool = AnalyzeCodeTool()
        pr_data = {
            "number": 123,
            "title": "Add feature",
            "files": [{"filename": "test.py", "patch": "+def hello(): pass"}]
        }
        
        result = tool.execute(pr_data, guidelines="Check PEP8")
        
        assert result.success
        assert "quality_score" in result.data
        assert "issues" in result.data

class TestPostCommentTool(unittest.TestCase):
    @patch('agents.pr_review_agent.Github')
    def test_post_comment(self, mock_github):
        mock_pr = Mock()
        mock_comment = Mock(id=456)
        mock_pr.create_issue_comment.return_value = mock_comment
        
        mock_repo = Mock()
        mock_repo.get_pull.return_value = mock_pr
        
        mock_github.return_value.get_repo.return_value = mock_repo
        
        tool = PostCommentTool()
        result = tool.execute(
            pr_number=123,
            comment="Test comment",
            repo="test/repo"
        )
        
        assert result.success
        mock_pr.create_issue_comment.assert_called_once()
```

### 2. Integration Tests (`tests/test_pr_review_integration.py`)

```python
import pytest
from unittest.mock import patch, Mock
from agents.pr_review_agent import PRReviewAgent

class TestPRReviewWorkflow:
    @patch('agents.pr_review_agent.Github')
    def test_full_review_workflow(self, mock_github):
        # Setup comprehensive mocks
        agent = PRReviewAgent()
        
        # Test full workflow
        result = agent.execute_task("review PR #123")
        
        assert "review" in result
        assert "posted" in result or "analyzed" in result.lower()
    
    def test_review_with_custom_guidelines(self):
        agent = PRReviewAgent()
        agent.guidelines = "Check for security issues"
        
        result = agent.execute_task("review PR #456 with security focus")
        
        # Verify guidelines were applied
        assert result is not None
```

### 3. Mock Fixtures (`tests/fixtures/pr_data.py`)

```python
def get_mock_pr():
    """Create realistic PR mock data"""
    return {
        "number": 123,
        "title": "Add new feature",
        "body": "This PR adds feature X",
        "user": {"login": "testuser"},
        "head": {"ref": "feature-branch"},
        "base": {"ref": "main"},
        "files": [
            {
                "filename": "app.py",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
                "patch": "@@ -1,5 +1,10 @@\n+def new_func():\n+    pass"
            }
        ]
    }

def get_mock_diff():
    """Create realistic diff data"""
    return """
diff --git a/app.py b/app.py
index abc123..def456 100644
--- a/app.py
+++ b/app.py
@@ -1,5 +1,10 @@
+def new_func():
+    '''New functionality'''
+    return True
+
 def existing_func():
     pass
"""
```

### 4. Error Handling Tests

```python
class TestErrorHandling:
    def test_invalid_pr_number(self):
        agent = PRReviewAgent()
        result = agent.execute_task("review PR #invalid")
        
        # Should handle gracefully
        assert "error" in str(result).lower() or result == {}
    
    @patch('agents.pr_review_agent.Github')
    def test_github_api_failure(self, mock_github):
        mock_github.side_effect = Exception("API Error")
        
        agent = PRReviewAgent()
        result = agent.execute_task("review PR #123")
        
        # Should not crash
        assert result is not None
    
    def test_missing_token(self):
        with patch.dict('os.environ', {}, clear=True):
            agent = PRReviewAgent()
            result = agent.execute_task("review PR #123")
            
            # Should provide helpful error
            assert result is not None
```

### 5. End-to-End Test Script (`scripts/test_pr_review_e2e.py`)

```python
#!/usr/bin/env python
"""
End-to-end test for PR Review Agent
Requires GITHUB_TOKEN and a test repository
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.pr_review_agent import PRReviewAgent

def test_real_pr():
    """Test with a real PR (read-only)"""
    
    # Use a known public PR for testing
    test_repo = "microsoft/vscode"
    test_pr = 1  # First PR, always exists
    
    agent = PRReviewAgent()
    result = agent.execute_task(f"analyze PR #{test_pr} in {test_repo}")
    
    print(f"Result: {result}")
    assert result is not None
    
if __name__ == "__main__":
    if not os.getenv("GITHUB_TOKEN"):
        print("Skipping E2E test - no GITHUB_TOKEN")
        sys.exit(0)
    
    test_real_pr()
    print("✅ E2E test passed!")
```

### 6. Test Configuration

Update `pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
```

### 7. Run Tests

```bash
# Unit tests only
pytest tests/test_pr_review_agent.py -v

# Integration tests
pytest tests/test_pr_review_integration.py -v -m integration

# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=agents.pr_review_agent --cov-report=html
```

## Success Criteria

- [ ] Unit tests for all 4 tools
- [ ] Integration test for full workflow
- [ ] Mock fixtures for GitHub data
- [ ] Error handling tests pass
- [ ] Test coverage > 80%
- [ ] E2E test script working

## Agent Assignment

CodeTestingAgent

## Priority

High

## Dependencies

- Issue #420 (PRReviewAgent implementation) must be complete
- pytest and pytest-cov installed
- Mock/patch utilities

## Estimated Effort

2-3 hours

## Notes

Start with unit tests for individual tools, then build up to integration tests. E2E tests can be optional if GitHub token is not available. Focus on testing the business logic rather than GitHub API internals.