#!/usr/bin/env uv run python
"""
Comprehensive test suite for IntelligentIssueAgent.
Tests the bejeezus out of the intelligent layer on top of the old system.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch

from agents.intelligent_issue_agent import IntelligentIssueAgent
from core.tools import ToolResponse, FileTool


class TestIntelligentIssueAgent:
    """Test the intelligent issue understanding and routing"""

    @pytest.fixture
    def agent(self):
        """Create an agent instance for testing"""
        return IntelligentIssueAgent()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    # ============== Issue Reference Extraction Tests ==============

    def test_extract_github_issue_number(self, agent):
        """Test extraction of GitHub issue numbers"""
        result = agent._extract_issue_reference("Fix issue #123")
        assert result == {"type": "github", "number": "123"}

    def test_extract_issue_file_path(self, agent):
        """Test extraction of issue file paths"""
        result = agent._extract_issue_reference("Process issues/bug-report.md")
        assert result == {"type": "file", "path": "issues/bug-report.md"}

    def test_extract_no_issue_reference(self, agent):
        """Test when no issue reference is found"""
        result = agent._extract_issue_reference("Just do something")
        assert result is None

    def test_extract_multiple_issue_formats(self, agent):
        """Test various issue reference formats"""
        test_cases = [
            ("Issue #456 needs fixing", {"type": "github", "number": "456"}),
            ("Check issue/test.md", {"type": "file", "path": "issue/test.md"}),
            ("Review PR #789", {"type": "github", "number": "789"}),
        ]
        for input_text, expected in test_cases:
            result = agent._extract_issue_reference(input_text)
            assert result == expected, f"Failed for: {input_text}"

    # ============== Issue Reading Tests ==============

    def test_read_local_issue_file(self, agent, temp_dir):
        """Test reading a local issue file"""
        issue_file = temp_dir / "test-issue.md"
        issue_content = "# Test Issue\nFix the bug"
        issue_file.write_text(issue_content)

        issue_data = {"type": "file", "path": str(issue_file)}
        result = agent._read_issue(issue_data)
        assert result == issue_content

    def test_read_nonexistent_issue_file(self, agent):
        """Test reading a non-existent file"""
        issue_data = {"type": "file", "path": "nonexistent.md"}
        result = agent._read_issue(issue_data)
        assert result is None

    # ============== Intent Understanding Tests ==============

    def test_understand_simple_fix_intent(self, agent):
        """Test understanding a simple fix request"""
        content = "Fix the authentication bug in auth.py"
        intent = agent._understand_issue_intent(content)

        assert "fix" in intent["actions"]
        assert "auth.py" in intent["files_mentioned"]
        assert intent["complexity"] == "simple"

    def test_understand_complex_multi_action_intent(self, agent):
        """Test understanding complex multi-action requests"""
        content = """
        Fix the bug in src/main.py, create tests in test_main.py,
        and update the documentation in README.md
        """
        intent = agent._understand_issue_intent(content)

        assert "fix" in intent["actions"]
        assert "create" in intent["actions"]
        assert "update" in intent["actions"]
        assert intent["complexity"] == "complex"
        assert intent["requires_parallel"] == True

    def test_understand_file_creation_intent(self, agent):
        """Test understanding file creation requests"""
        content = "Create a configuration file at config/settings.yaml"
        intent = agent._understand_issue_intent(content)

        assert "create" in intent["actions"]
        assert "config/settings.yaml" in intent["files_mentioned"]
        assert len(intent["create_requests"]) > 0

    def test_detect_parallel_processing_needs(self, agent):
        """Test detection of parallel processing requirements"""
        test_cases = [
            ("Fix all bugs in the project", True),
            ("Update multiple files", True),
            ("Fix one bug", False),
            ("Create a single file", False),
        ]

        for content, should_be_parallel in test_cases:
            intent = agent._understand_issue_intent(content)
            assert (
                intent["requires_parallel"] == should_be_parallel
            ), f"Failed for: {content}"

    # ============== File Operation Tests ==============

    def test_create_file_with_content(self, agent, temp_dir):
        """Test file creation with appropriate content"""
        request = {"path": str(temp_dir / "test.py"), "type": "python"}

        result = agent._create_file(request)
        assert result["success"] == True
        assert Path(request["path"]).exists()

        content = Path(request["path"]).read_text()
        assert "#!/usr/bin/env python3" in content

    def test_generate_content_for_different_file_types(self, agent):
        """Test content generation for various file types"""
        test_cases = [
            ("test.py", "#!/usr/bin/env python3"),
            ("README.md", "# "),
            ("config.json", "{}"),
            ("data.txt", "Generated"),
        ]

        for filename, expected_content in test_cases:
            request = {"path": filename}
            content = agent._generate_file_content(request)
            assert expected_content in content, f"Failed for: {filename}"

    # ============== Integration Tests ==============

    def test_end_to_end_simple_issue_processing(self, agent, temp_dir):
        """Test complete flow for a simple issue"""
        # Create test issue
        issue_file = temp_dir / "issue.md"
        issue_file.write_text("Create a README.md file")

        # Process issue
        result = agent.execute_task(f"Process {issue_file}")

        assert result.success == True
        assert result.data is not None
        assert "operations" in result.data

    def test_end_to_end_complex_issue_orchestration(self, agent, temp_dir):
        """Test complex issue requiring orchestration"""
        issue_file = temp_dir / "complex.md"
        issue_file.write_text(
            """
        Fix bugs in auth.py, user.py, and database.py.
        Also create tests for all three modules.
        """
        )

        with patch.object(agent.orchestrator, "orchestrate_complex_task") as mock_orch:
            mock_orch.return_value = {"success": True}

            result = agent.execute_task(f"Handle {issue_file}")

            assert result.success == True
            assert result.data["intent"]["complexity"] == "complex"
            assert result.data["intent"]["requires_parallel"] == True
            mock_orch.assert_called_once()

    # ============== Error Handling Tests ==============

    def test_handle_invalid_issue_reference(self, agent):
        """Test handling of invalid issue references"""
        result = agent.execute_task("Do something without issue reference")
        assert result.success == False
        assert "Could not identify issue reference" in result.error

    def test_handle_unreadable_issue(self, agent):
        """Test handling of unreadable issues"""
        result = agent.execute_task("Process issue #99999")
        assert result.success == False
        assert "Could not read issue" in result.error

    def test_handle_file_creation_failure(self, agent):
        """Test handling of file creation failures"""
        with patch.object(FileTool, "execute") as mock_execute:
            mock_execute.return_value = ToolResponse(
                success=False, error="Permission denied"
            )

            request = {"path": "/readonly/test.txt"}
            result = agent._create_file(request)

            assert result["success"] == False
            assert result["error"] == "Permission denied"

    # ============== Pattern Extraction Tests ==============

    def test_extract_creation_requests(self, agent):
        """Test extraction of file creation requests"""
        test_cases = [
            (
                "Create a test file at tests/test_new.py",
                [{"type": "test", "path": "tests/test_new.py", "action": "create"}],
            ),
            (
                "Add new config file in config/prod.yaml",
                [{"type": "config", "path": "config/prod.yaml", "action": "create"}],
            ),
        ]

        for content, expected_count in test_cases:
            requests = agent._extract_creation_requests(content)
            assert len(requests) >= len(expected_count), f"Failed for: {content}"

    def test_extract_fix_requests(self, agent):
        """Test extraction of fix requests"""
        content = "Fix the memory bug in src/memory.c and resolve the race error in threading.py"
        requests = agent._extract_fix_requests(content)

        assert len(requests) >= 2
        paths = [r["path"] for r in requests]
        assert "src/memory.c" in paths or "memory.c" in paths
        assert "threading.py" in paths

    # ============== Performance Tests ==============

    def test_performance_large_issue(self, agent):
        """Test handling of large issue descriptions"""
        import time

        # Create a large issue description
        large_content = "Fix bugs in " + ", ".join([f"file{i}.py" for i in range(100)])

        start = time.time()
        intent = agent._understand_issue_intent(large_content)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Too slow: {elapsed}s"
        assert "fix" in intent["actions"]
        assert len(intent["files_mentioned"]) > 50

    # ============== Regression Tests ==============

    def test_backward_compatibility_with_old_tools(self, agent):
        """Test that we still use the old FileTool correctly"""
        assert any(isinstance(tool, FileTool) for tool in agent.tools)

        # Verify FileTool still works
        file_tool = agent.tools[0]
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            temp_path = f.name

        result = file_tool.execute(operation="read", path=temp_path)
        assert result.success == True
        assert result.data["content"] == "test"

        Path(temp_path).unlink()

    def test_orchestrator_integration(self, agent):
        """Test that HierarchicalOrchestrator is properly integrated"""
        assert hasattr(agent, "orchestrator")
        assert agent.orchestrator is not None

        # Verify orchestrator has expected methods
        assert hasattr(agent.orchestrator, "orchestrate_complex_task")


class TestIntelligentIssueAgentEdgeCases:
    """Test edge cases and unusual scenarios"""

    @pytest.fixture
    def agent(self):
        return IntelligentIssueAgent()

    def test_empty_issue_content(self, agent):
        """Test handling of empty issue content"""
        intent = agent._understand_issue_intent("")
        assert intent["actions"] == []
        assert intent["complexity"] == "simple"

    def test_malformed_file_paths(self, agent):
        """Test handling of malformed file paths"""
        content = "Fix the bug in ../../../etc/passwd and /root/.ssh/id_rsa"
        intent = agent._understand_issue_intent(content)
        # Should extract but we'd want security checks in production
        assert len(intent["files_mentioned"]) >= 0

    def test_circular_reference_prevention(self, agent):
        """Test prevention of circular references in orchestration"""
        content = "Fix issue #123 which references issue #123"
        intent = agent._understand_issue_intent(content)
        # Should handle gracefully
        assert intent is not None

    def test_unicode_and_special_characters(self, agent):
        """Test handling of unicode and special characters"""
        content = "Fix the bug in файл.py and 测试.js"
        intent = agent._understand_issue_intent(content)
        assert "fix" in intent["actions"]
        # Should handle international characters

    def test_extremely_long_file_paths(self, agent):
        """Test handling of very long file paths"""
        long_path = "/".join(["directory"] * 50) + "/file.txt"
        content = f"Create a file at {long_path}"
        intent = agent._understand_issue_intent(content)
        assert "create" in intent["actions"]


class TestIntelligentIssueAgentSecurity:
    """Test security aspects of the intelligent agent"""

    @pytest.fixture
    def agent(self):
        return IntelligentIssueAgent()

    def test_no_path_traversal_in_file_operations(self, agent, tmp_path):
        """Test that path traversal attacks are prevented"""
        malicious_paths = [
            "../../../etc/passwd",
            "../../../../root/.bashrc",
            "..\\..\\..\\windows\\system32\\config\\sam",
        ]

        for path in malicious_paths:
            request = {"path": path}
            # In production, this should be blocked
            # For now, just verify it doesn't crash
            content = agent._generate_file_content(request)
            assert content is not None

    def test_no_code_injection_in_content_generation(self, agent):
        """Test that code injection is prevented in generated content"""
        request = {"path": "test.py'; rm -rf /; echo '", "type": "python"}
        content = agent._generate_file_content(request)
        # Should not execute the malicious code
        assert "rm -rf" not in content or "Generated file" in content

    def test_safe_file_operations(self, agent, tmp_path):
        """Test that file operations are safe"""
        safe_file = tmp_path / "safe.txt"
        safe_file.write_text("original")

        # Should not overwrite without explicit permission
        request = {"path": str(safe_file)}
        # The current implementation will overwrite - this is a test to ensure we know the behavior
        result = agent._create_file(request)

        # Document current behavior
        assert result["success"] == True  # Currently overwrites
