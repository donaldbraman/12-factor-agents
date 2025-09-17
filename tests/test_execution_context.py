#!/usr/bin/env uv run python
"""
Test ExecutionContext system for cross-repository operations.

This test suite verifies that the ExecutionContext system properly enables
agents to work across different repositories by providing correct file path resolution.

Critical for issue #83: https://github.com/donaldbraman/12-factor-agents/issues/83
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.execution_context import (
    ExecutionContext,
    create_external_context,
    create_default_context,
)
from core.github_integration import ExternalIssueProcessor
from agents.issue_orchestrator_agent import IssueOrchestratorAgent
from agents.intelligent_issue_agent import IntelligentIssueAgent


class TestExecutionContext:
    """Test ExecutionContext dataclass functionality"""

    def test_execution_context_creation(self):
        """Test basic ExecutionContext creation"""
        context = ExecutionContext(
            repo_name="test-repo", repo_path=Path("/test/path"), is_external=True
        )

        assert context.repo_name == "test-repo"
        assert context.repo_path == Path("/test/path")
        assert context.is_external
        assert context.workflow_id is not None
        assert context.trace_id is not None

    def test_path_resolution(self):
        """Test path resolution using context"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            context = ExecutionContext(repo_path=temp_path)

            # Test resolving a relative path
            resolved = context.resolve_path("tests/test_file.py")
            expected = temp_path / "tests" / "test_file.py"

            assert resolved == expected

    def test_child_context_creation(self):
        """Test creating child contexts"""
        parent = ExecutionContext(
            repo_name="parent-repo",
            repo_path=Path("/parent"),
            workflow_id="parent-workflow",
        )

        child = parent.create_child_context(
            repo_name="child-repo", repo_path=Path("/child")
        )

        assert child.repo_name == "child-repo"
        assert child.repo_path == Path("/child")
        assert child.parent_context == parent
        assert child.workflow_id != parent.workflow_id  # New workflow ID

    def test_is_path_within_repo(self):
        """Test checking if paths are within repository boundaries"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            context = ExecutionContext(repo_path=temp_path)

            # Path within repo
            inner_path = temp_path / "src" / "file.py"
            assert context.is_path_within_repo(inner_path)

            # Path outside repo
            outer_path = Path("/outside/file.py")
            assert not context.is_path_within_repo(outer_path)

    def test_to_dict_serialization(self):
        """Test context serialization to dict"""
        context = ExecutionContext(
            repo_name="test-repo",
            repo_path=Path("/test"),
            issue_number=123,
            is_external=True,
        )

        context_dict = context.to_dict()

        assert context_dict["repo_name"] == "test-repo"
        assert context_dict["repo_path"] == "/test"
        assert context_dict["issue_number"] == 123
        assert context_dict["is_external"]
        assert "workflow_id" in context_dict
        assert "trace_id" in context_dict


class TestExternalContextCreation:
    """Test convenience functions for creating external contexts"""

    def test_create_external_context(self):
        """Test creating external repository context"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = create_external_context(
                repo="owner/repo-name", repo_path=temp_path, issue_number=144
            )

            assert context.repo_name == "repo-name"
            assert context.repo_path == temp_path
            assert context.source_repo == "owner/repo-name"
            assert context.issue_number == 144
            assert context.is_external
            assert "github.com/owner/repo-name" in context.repo_url

    def test_create_default_context(self):
        """Test creating default context for current repo"""
        context = create_default_context()

        assert context.repo_name == "12-factor-agents"
        assert not context.is_external
        assert context.repo_path == Path.cwd()


class TestExternalIssueProcessorContext:
    """Test that ExternalIssueProcessor creates and uses context correctly"""

    def test_external_issue_processor_creates_context(self):
        """Test that processor creates ExecutionContext for external repos"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a mock issues directory
            issues_dir = temp_path / "issues"
            issues_dir.mkdir()

            # Create a test issue file
            test_issue = issues_dir / "144-test-issue.md"
            test_issue.write_text(
                """# Issue #144: Test Issue

## Description
This is a test issue for context validation.

## Agent Assignment
IntelligentIssueAgent

## Status
OPEN
"""
            )

            processor = ExternalIssueProcessor()

            # Mock the GitHub API calls
            with patch.object(processor, "add_github_comment"):
                with patch("core.github_integration.GitHubIssueLoader") as mock_loader:
                    # Mock the loader
                    mock_loader_instance = MagicMock()
                    mock_loader.return_value = mock_loader_instance

                    # Mock fetch_issue to return test data
                    mock_loader_instance.fetch_issue.return_value = {
                        "number": 144,
                        "title": "Test Issue",
                        "body": "Test issue body",
                        "labels": [],
                        "state": "open",
                        "repository": "test-owner/test-repo",
                    }

                    # Mock convert_to_sparky_format
                    mock_loader_instance.convert_to_sparky_format.return_value = {
                        "number": 144,
                        "title": "Test Issue",
                        "content": "Test issue body",
                        "agent": "IntelligentIssueAgent",
                        "labels": [],
                        "state": "open",
                        "repository": "test-owner/test-repo",
                    }

                    # Mock save_as_issue_file to return our test file
                    mock_loader_instance.save_as_issue_file.return_value = test_issue

                    # Mock IssueOrchestratorAgent
                    with patch(
                        "agents.issue_orchestrator_agent.IssueOrchestratorAgent"
                    ) as mock_sparky_class:
                        mock_sparky = MagicMock()
                        mock_sparky_class.return_value = mock_sparky

                        # Mock execute_task to capture the context
                        mock_sparky.execute_task.return_value = MagicMock(
                            success=True, data={"test": "result"}
                        )

                        # Test the processor
                        processor.process_external_issue(
                            repo="test-owner/test-repo",
                            issue_number=144,
                            repo_path=str(temp_path),
                        )

                        # Verify the call was made with context
                        mock_sparky.execute_task.assert_called_once()
                        call_args = mock_sparky.execute_task.call_args

                        # Verify context was passed
                        assert "context" in call_args[1]
                        context = call_args[1]["context"]

                        assert isinstance(context, ExecutionContext)
                        assert context.repo_name == "test-repo"
                        assert context.repo_path == temp_path
                        assert context.source_repo == "test-owner/test-repo"
                        assert context.issue_number == 144
                        assert context.is_external


class TestIssueOrchestratorAgentContext:
    """Test that IssueOrchestratorAgent accepts and passes context"""

    def test_orchestrator_accepts_context(self):
        """Test that IssueOrchestratorAgent accepts ExecutionContext"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create issues directory and test issue
            issues_dir = temp_path / "issues"
            issues_dir.mkdir()

            test_issue = issues_dir / "1-test-issue.md"
            test_issue.write_text(
                """# Issue #1: Test Issue

## Description
Test issue for context flow.

## Agent Assignment
IntelligentIssueAgent

## Status
OPEN
"""
            )

            context = ExecutionContext(
                repo_name="test-repo", repo_path=temp_path, is_external=True
            )

            orchestrator = IssueOrchestratorAgent()

            # Mock the agent dispatcher to capture context
            with patch.object(orchestrator, "tools") as mock_tools:
                mock_reader = MagicMock()
                mock_dispatcher = MagicMock()
                mock_updater = MagicMock()

                mock_tools.__getitem__.side_effect = [
                    mock_reader,
                    mock_dispatcher,
                    mock_updater,
                ]

                # Mock reader to return test issue
                mock_reader.execute.return_value = MagicMock(
                    success=True,
                    data={
                        "issue": {
                            "number": "1",
                            "title": "Test Issue",
                            "description": "Test issue for context flow",
                            "agent": "IntelligentIssueAgent",
                            "status": "open",
                            "dependencies": [],
                            "path": str(test_issue),
                        }
                    },
                )

                # Mock dispatcher to succeed
                mock_dispatcher.execute.return_value = MagicMock(
                    success=True, data={"test": "success"}
                )

                # Mock updater to succeed
                mock_updater.execute.return_value = MagicMock(success=True)

                # Execute with context
                orchestrator.execute_task("resolve all issues", context=context)

                # Verify context was stored
                assert orchestrator.context == context

                # Verify dispatcher was called with context
                mock_dispatcher.execute.assert_called()
                call_args = mock_dispatcher.execute.call_args
                assert "context" in call_args[1]
                assert call_args[1]["context"] == context


class TestIntelligentIssueAgentContext:
    """Test that IntelligentIssueAgent uses context for file operations"""

    def test_agent_uses_context_for_file_resolution(self):
        """Test that IntelligentIssueAgent resolves files using context"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test repo structure
            issues_dir = temp_path / "issues"
            issues_dir.mkdir()

            src_dir = temp_path / "src"
            src_dir.mkdir()

            # Create test issue
            test_issue = issues_dir / "42-test-bug.md"
            test_issue.write_text(
                """# Issue #42: Test Bug Fix

## Description
Fix the bug in `src/test_file.py` that causes parsing errors.

## Agent Assignment
IntelligentIssueAgent

## Status
OPEN
"""
            )

            # Create test source file
            test_file = src_dir / "test_file.py"
            test_file.write_text(
                """def test_function():
    # Function implementation pending
    pass

def another_function():
    # Known issue: returns None
    return None
"""
            )

            context = ExecutionContext(
                repo_name="test-repo", repo_path=temp_path, is_external=True
            )

            agent = IntelligentIssueAgent()

            # Execute task with context
            result = agent.execute_task("Process issue #42", context=context)

            # Verify the agent found and processed the issue
            assert result.success
            assert result.data["issue_number"] == "42"

            # Verify context was used
            assert agent.context == context

            # Check that files were analyzed from the correct repository
            implementation_result = result.data.get("implementation_result", {})
            if "files_read" in implementation_result:
                # Verify paths are resolved within the context repo
                for file_path in implementation_result["files_read"]:
                    assert temp_path.name in file_path or str(temp_path) in file_path

    def test_external_repo_file_operations(self):
        """Test file operations work correctly in external repository context"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Simulate external repo directory structure
            external_repo = Path(temp_dir) / "external-repo"
            external_repo.mkdir()

            # Create issues directory
            issues_dir = external_repo / "issues"
            issues_dir.mkdir()

            # Create test files directory
            tests_dir = external_repo / "tests"
            tests_dir.mkdir()

            # Create test issue referencing external repo files
            test_issue = issues_dir / "144-failing-tests.md"
            test_issue.write_text(
                """# Issue #144: Failing Tests

## Description
The tests in `tests/test_patterns.py` are failing due to parsing issues.

## Agent Assignment
IntelligentIssueAgent

## Status
OPEN
"""
            )

            # Create the referenced test file
            test_file = tests_dir / "test_patterns.py"
            test_file.write_text(
                """import pytest

def test_pattern_matching():
    # Test implementation pending
    pass

def test_regex_validation():
    # Known issue: test disabled
    assert False
"""
            )

            # Create external context
            context = create_external_context(
                repo="external-owner/external-repo",
                repo_path=external_repo,
                issue_number=144,
            )

            agent = IntelligentIssueAgent()

            # Process the external issue
            result = agent.execute_task("Process issue #144", context=context)

            # Verify success
            assert result.success

            # Verify the agent operated in the external repo context
            assert agent.context.repo_name == "external-repo"
            assert agent.context.repo_path == external_repo
            assert agent.context.is_external

            # Verify files were found and processed in external repo
            implementation_result = result.data.get("implementation_result", {})
            if "files_read" in implementation_result:
                # Should have found and read the test file
                files_read = implementation_result["files_read"]
                assert any("test_patterns.py" in f for f in files_read)


class TestContextFlowIntegration:
    """Integration tests for context flow through the entire pipeline"""

    def test_complete_context_flow(self):
        """Test context flows from ExternalIssueProcessor -> Sparky -> IntelligentIssueAgent"""
        with tempfile.TemporaryDirectory() as temp_dir:
            external_repo = Path(temp_dir) / "pin-citer"
            external_repo.mkdir()

            # Create realistic directory structure
            issues_dir = external_repo / "issues"
            tests_dir = external_repo / "tests"
            issues_dir.mkdir()
            tests_dir.mkdir()

            # Create issue file
            issue_file = issues_dir / "144-test-failure.md"
            issue_file.write_text(
                """# Issue #144: Test Patterns Failing

## Description
Tests in tests/test_patterns.py are failing because of regex parsing issues.

## Agent Assignment
IntelligentIssueAgent

## Status
OPEN
"""
            )

            # Create test file that will be modified
            test_file = tests_dir / "test_patterns.py"
            test_file.write_text(
                """# Test patterns for citation parsing
import re

def test_citation_pattern():
    # Test implementation pending
    pass

def test_url_validation():
    # Known issue: regex pattern needs improvement
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.compile(pattern)
"""
            )

            processor = ExternalIssueProcessor()

            # Mock GitHub API components
            with patch(
                "core.github_integration.GitHubIssueLoader"
            ) as mock_loader_class:
                mock_loader = MagicMock()
                mock_loader_class.return_value = mock_loader = mock_loader

                # Mock GitHub issue data
                mock_loader.fetch_issue.return_value = {
                    "number": 144,
                    "title": "Test Patterns Failing",
                    "body": "Tests in tests/test_patterns.py are failing because of regex parsing issues.",
                    "labels": [{"name": "bug"}],
                    "state": "open",
                    "repository": "pin-citer/pin-citer",
                }

                mock_loader.convert_to_sparky_format.return_value = {
                    "number": 144,
                    "title": "Test Patterns Failing",
                    "content": "Tests in tests/test_patterns.py are failing because of regex parsing issues.",
                    "agent": "IntelligentIssueAgent",
                    "labels": ["bug"],
                    "state": "open",
                    "repository": "pin-citer/pin-citer",
                }

                mock_loader.save_as_issue_file.return_value = issue_file

                # Don't mock the agents - let them run with real context
                with patch.object(processor, "add_github_comment"):
                    # Process the external issue
                    result = processor.process_external_issue(
                        repo="pin-citer/pin-citer",
                        issue_number=144,
                        repo_path=str(external_repo),
                    )

                    # Verify the processing succeeded
                    assert result["success"]

                    # Verify context was created correctly
                    context_dict = result.get("context", {})
                    assert context_dict["repo_name"] == "pin-citer"
                    assert context_dict["is_external"]
                    assert context_dict["issue_number"] == 144

                    # The test file should still exist (files were read from correct repo)
                    assert test_file.exists()


if __name__ == "__main__":
    # Run a quick validation test
    print("🧪 Running ExecutionContext validation tests...")

    # Test 1: Basic context creation
    context = ExecutionContext(repo_name="test", repo_path=Path("/tmp"))
    assert context.repo_name == "test"
    print("✅ Basic context creation works")

    # Test 2: Path resolution
    resolved = context.resolve_path("src/file.py")
    expected = Path("/tmp/src/file.py")
    assert resolved == expected
    print("✅ Path resolution works")

    # Test 3: External context creation
    external = create_external_context("owner/repo", Path("/external"), 123)
    assert external.repo_name == "repo"
    assert external.is_external
    assert external.issue_number == 123
    print("✅ External context creation works")

    print("\n🎉 All ExecutionContext validation tests passed!")
    print("📝 Context system is ready for cross-repository operations!")
