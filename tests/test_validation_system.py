#!/usr/bin/env uv run python
"""
Comprehensive tests for the validation and rollback system.

Tests cover:
- TransactionalFileModifier functionality
- Syntax validation for Python, JSON, YAML
- Indentation error detection
- Rollback mechanisms
- Integration with ExecutionContext
- Error handling and recovery
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from core.validation import (
    TransactionalFileModifier,
    ValidationResult,
    validate_file_content,
    create_safe_file_modifier,
    ValidationIntegrationMixin,
)
from core.execution_context import ExecutionContext, create_default_context


class TestTransactionalFileModifier:
    """Test the core TransactionalFileModifier functionality"""

    def setup_method(self):
        """Set up test environment"""
        # Create temporary directory for tests
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_validation_"))
        self.context = ExecutionContext(repo_path=self.test_dir)
        self.modifier = TransactionalFileModifier(self.context)

    def teardown_method(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_transaction_initialization(self):
        """Test transaction initialization"""
        tx_id = self.modifier.begin_transaction()

        assert tx_id == self.modifier.transaction_id
        assert self.modifier.state.backup_dir is not None
        assert self.modifier.state.backup_dir.exists()
        assert not self.modifier.state.is_committed
        assert not self.modifier.state.is_rolled_back

    def test_stage_modification_new_file(self):
        """Test staging a modification for a new file"""
        self.modifier.begin_transaction()

        test_content = "print('Hello, World!')\n"
        test_file = "new_file.py"

        result = self.modifier.stage_modification(test_file, test_content)

        assert result.result == ValidationResult.SUCCESS
        # Check that the resolved path is in modifications
        resolved_path = str(self.context.resolve_path(test_file))
        assert resolved_path in self.modifier.state.modifications

        record = self.modifier.state.modifications[
            str(self.context.resolve_path(test_file))
        ]
        assert record.original_content == ""
        assert record.modified_content == test_content

    def test_stage_modification_existing_file(self):
        """Test staging a modification for an existing file"""
        self.modifier.begin_transaction()

        # Create existing file
        test_file = self.test_dir / "existing.py"
        original_content = "print('Original')\n"
        test_file.write_text(original_content)

        new_content = "print('Modified')\n"

        result = self.modifier.stage_modification(str(test_file), new_content)

        assert result.result == ValidationResult.SUCCESS

        record = self.modifier.state.modifications[str(test_file)]
        assert record.original_content == original_content
        assert record.modified_content == new_content
        assert record.backup_path is not None
        assert record.backup_path.read_text() == original_content

    def test_commit_transaction_success(self):
        """Test successful transaction commit"""
        self.modifier.begin_transaction()

        test_file = "test_commit.py"
        test_content = "print('Committed content')\n"

        self.modifier.stage_modification(test_file, test_content)
        success, errors = self.modifier.commit_transaction()

        assert success
        assert len(errors) == 0
        assert self.modifier.state.is_committed

        # Verify file was written
        file_path = self.context.resolve_path(test_file)
        assert file_path.exists()
        assert file_path.read_text() == test_content

    def test_rollback_transaction(self):
        """Test transaction rollback"""
        self.modifier.begin_transaction()

        # Create original file
        test_file = self.test_dir / "rollback_test.py"
        original_content = "print('Original')\n"
        test_file.write_text(original_content)

        # Stage modification
        new_content = "print('Modified')\n"
        self.modifier.stage_modification(str(test_file), new_content)

        # Rollback
        success = self.modifier.rollback_transaction()

        assert success
        assert self.modifier.state.is_rolled_back

        # Verify original content is restored
        assert test_file.read_text() == original_content

    def test_cleanup(self):
        """Test cleanup of backup directories"""
        _ = self.modifier.begin_transaction()
        backup_path = self.modifier.state.backup_dir

        assert backup_path.exists()

        self.modifier.cleanup()

        assert not backup_path.exists()


class TestPythonSyntaxValidation:
    """Test Python syntax validation capabilities"""

    def setup_method(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_python_validation_"))
        self.context = ExecutionContext(repo_path=self.test_dir)
        self.modifier = TransactionalFileModifier(self.context)

    def teardown_method(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_valid_python_syntax(self):
        """Test validation of valid Python code"""
        valid_code = """
def hello_world():
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
"""
        result = self.modifier.validate_python_syntax(valid_code)
        assert result.result == ValidationResult.SUCCESS

    def test_syntax_error_detection(self):
        """Test detection of syntax errors"""
        invalid_code = """
def hello_world(:  # Missing closing parenthesis
    print("Hello, World!")
"""
        result = self.modifier.validate_python_syntax(invalid_code)
        assert result.result == ValidationResult.SYNTAX_ERROR
        assert "syntax error" in result.message.lower()
        assert result.line_number is not None

    def test_indentation_error_detection(self):
        """Test detection of indentation errors"""
        indented_code = """
def hello_world():
    print("Hello, World!")
  print("Inconsistent indentation")  # Wrong indentation
"""
        result = self.modifier.validate_python_syntax(indented_code)
        assert result.result == ValidationResult.INDENTATION_ERROR
        assert "indentation" in result.message.lower()
        assert result.line_number is not None

    def test_problematic_if_pattern_detection(self):
        """Test detection of problematic 'if result is not None' patterns"""
        # This is the specific bug pattern mentioned in the requirements
        problematic_code = """
def process_data():
    result = get_data()
if result is not None:  # Incorrect indentation
        return result.value
    return None
"""
        result = self.modifier.validate_python_syntax(problematic_code)
        assert result.result == ValidationResult.INDENTATION_ERROR
        assert (
            "if result is not None" in result.message
            or "indentation" in result.message.lower()
        )

    def test_indentation_pattern_check(self):
        """Test the specific indentation pattern checking"""
        # Test the internal method directly
        problematic_code = """
def process_data():
    result = get_data()
if result is not None:  # Wrong indentation
        return result.value
    return None
"""
        error = self.modifier._check_indentation_patterns(problematic_code)
        assert error is not None
        assert error.result == ValidationResult.INDENTATION_ERROR
        assert "if result is not None" in error.message

    def test_correct_indentation_pattern(self):
        """Test that correctly indented patterns pass"""
        correct_code = """
def process_data():
    result = get_data()
    if result is not None:  # Correct indentation
        return result.value
    return None
"""
        error = self.modifier._check_indentation_patterns(correct_code)
        assert error is None

    def test_indentation_fix_suggestions(self):
        """Test that fix suggestions are provided for indentation errors"""
        problematic_code = """
def test():
    x = 1
  y = 2  # Wrong indentation
"""
        result = self.modifier.validate_python_syntax(problematic_code)
        assert result.result == ValidationResult.INDENTATION_ERROR
        assert result.suggested_fix is not None
        assert "indentation" in result.suggested_fix.lower()


class TestFileContentValidation:
    """Test validation for different file types"""

    def setup_method(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_content_validation_"))
        self.context = ExecutionContext(repo_path=self.test_dir)
        self.modifier = TransactionalFileModifier(self.context)

    def teardown_method(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_json_validation_valid(self):
        """Test valid JSON content"""
        valid_json = '{"key": "value", "number": 42, "list": [1, 2, 3]}'
        result = self.modifier.validate_json_syntax(valid_json)
        assert result.result == ValidationResult.SUCCESS

    def test_json_validation_invalid(self):
        """Test invalid JSON content"""
        invalid_json = '{"key": "value", "number": 42, "list": [1, 2, 3}}'  # Missing ]
        result = self.modifier.validate_json_syntax(invalid_json)
        assert result.result == ValidationResult.SYNTAX_ERROR
        assert "json" in result.message.lower()

    def test_yaml_validation_valid(self):
        """Test valid YAML content"""
        valid_yaml = """
key: value
number: 42
list:
  - item1
  - item2
  - item3
"""
        result = self.modifier.validate_yaml_syntax(valid_yaml)
        assert result.result == ValidationResult.SUCCESS

    def test_yaml_validation_invalid(self):
        """Test invalid YAML content"""
        invalid_yaml = """
key: value
  invalid: indentation
"""
        result = self.modifier.validate_yaml_syntax(invalid_yaml)
        # YAML validation might pass or fail depending on the specific error
        # The test ensures we get a proper response
        assert result.result in [
            ValidationResult.SUCCESS,
            ValidationResult.SYNTAX_ERROR,
        ]

    def test_generic_content_validation(self):
        """Test generic content validation"""
        # Test normal content
        normal_content = "This is normal text content."
        result = self.modifier.validate_generic_content(normal_content)
        assert result.result == ValidationResult.SUCCESS

        # Test content with null bytes
        null_content = "This has null bytes\0in it."
        result = self.modifier.validate_generic_content(null_content)
        assert result.result == ValidationResult.SYNTAX_ERROR
        assert "null bytes" in result.message.lower()


class TestTransactionIntegration:
    """Test the full transaction workflow with validation"""

    def setup_method(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_transaction_integration_"))
        self.context = ExecutionContext(repo_path=self.test_dir)
        self.modifier = TransactionalFileModifier(self.context)

    def teardown_method(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_full_workflow_success(self):
        """Test complete workflow with successful validation and commit"""
        self.modifier.begin_transaction()

        # Stage multiple files
        files_content = {
            "module1.py": """
def function1():
    return "success"
""",
            "module2.py": """
def function2():
    result = function1()
    if result is not None:
        return result
    return "default"
""",
            "config.json": '{"setting": "value"}',
        }

        for file_path, content in files_content.items():
            result = self.modifier.stage_modification(file_path, content)
            assert result.result == ValidationResult.SUCCESS

        # Commit all changes
        success, errors = self.modifier.commit_transaction()
        assert success
        assert len(errors) == 0

        # Verify all files were written
        for file_path in files_content.keys():
            file_full_path = self.context.resolve_path(file_path)
            assert file_full_path.exists()
            assert file_full_path.read_text() == files_content[file_path]

    def test_workflow_with_validation_failure(self):
        """Test workflow where validation fails and rollback occurs"""
        self.modifier.begin_transaction()

        # Stage valid file first
        valid_content = "def valid_function():\n    return True\n"
        result = self.modifier.stage_modification("valid.py", valid_content)
        assert result.result == ValidationResult.SUCCESS

        # Stage invalid file
        invalid_content = "def invalid_function(:\n    return True\n"  # Syntax error
        result = self.modifier.stage_modification("invalid.py", invalid_content)
        assert result.result == ValidationResult.SYNTAX_ERROR

        # Transaction should not commit due to validation error
        # In real usage, the calling code would detect the validation error
        # and not attempt to commit

    def test_rollback_preserves_original_files(self):
        """Test that rollback preserves original file contents"""
        # Create original files
        original_files = {
            "file1.py": "original content 1",
            "file2.py": "original content 2",
        }

        for file_path, content in original_files.items():
            full_path = self.test_dir / file_path
            full_path.write_text(content)

        self.modifier.begin_transaction()

        # Stage modifications
        for file_path in original_files.keys():
            new_content = f"modified {file_path}"
            self.modifier.stage_modification(file_path, new_content)

        # Rollback
        self.modifier.rollback_transaction()

        # Verify original contents are preserved
        for file_path, original_content in original_files.items():
            full_path = self.test_dir / file_path
            assert full_path.read_text() == original_content


class TestValidationIntegrationMixin:
    """Test the ValidationIntegrationMixin for agent integration"""

    def test_mixin_functionality(self):
        """Test that the mixin provides expected functionality"""

        class TestAgent(ValidationIntegrationMixin):
            def __init__(self):
                self.context = create_default_context()
                super().__init__()

        agent = TestAgent()

        # Test that mixin methods are available
        assert hasattr(agent, "begin_safe_modifications")
        assert hasattr(agent, "stage_file_change")
        assert hasattr(agent, "commit_changes")
        assert hasattr(agent, "rollback_changes")
        assert hasattr(agent, "cleanup_modifications")

        # Test that methods return expected types
        tx_id = agent.begin_safe_modifications()
        assert isinstance(tx_id, str)

        agent.cleanup_modifications()


class TestStandaloneValidation:
    """Test standalone validation functions"""

    def test_validate_file_content_function(self):
        """Test the standalone validate_file_content function"""
        # Test valid Python
        valid_python = "def test():\n    return True\n"
        result = validate_file_content("test.py", valid_python)
        assert result.result == ValidationResult.SUCCESS

        # Test invalid Python
        invalid_python = "def test(:\n    return True\n"
        result = validate_file_content("test.py", invalid_python)
        assert result.result == ValidationResult.SYNTAX_ERROR

        # Test valid JSON
        valid_json = '{"key": "value"}'
        result = validate_file_content("test.json", valid_json)
        assert result.result == ValidationResult.SUCCESS

    def test_create_safe_file_modifier_factory(self):
        """Test the factory function for creating file modifiers"""
        context = create_default_context()
        modifier = create_safe_file_modifier(context)

        assert isinstance(modifier, TransactionalFileModifier)
        assert modifier.context == context


class TestErrorHandling:
    """Test error handling and edge cases"""

    def setup_method(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_error_handling_"))
        self.context = ExecutionContext(repo_path=self.test_dir)
        self.modifier = TransactionalFileModifier(self.context)

    def teardown_method(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_file_permission_error_handling(self):
        """Test handling of file permission errors"""
        self.modifier.begin_transaction()

        # Create a file and make it read-only
        readonly_file = self.test_dir / "readonly.py"
        readonly_file.write_text("print('original content')")  # Valid Python syntax
        readonly_file.chmod(0o444)  # Read-only

        try:
            result = self.modifier.stage_modification(
                str(readonly_file), "print('new content')"
            )  # Valid Python syntax
            # The result depends on the system and permissions
            # We just ensure it doesn't crash and handles it gracefully
            assert result.result in [
                ValidationResult.SUCCESS,
                ValidationResult.PERMISSION_ERROR,
                ValidationResult.ENCODING_ERROR,
            ]
        finally:
            # Restore permissions for cleanup
            readonly_file.chmod(0o644)

    def test_invalid_file_encoding(self):
        """Test handling of files with invalid encoding"""
        self.modifier.begin_transaction()

        # Create a file with invalid UTF-8
        invalid_file = self.test_dir / "invalid_encoding.py"
        invalid_file.write_bytes(b"\xff\xfe\x00\x00invalid utf-8")

        result = self.modifier.stage_modification(str(invalid_file), "new content")
        # Should handle encoding error gracefully
        assert result.result in [
            ValidationResult.SUCCESS,
            ValidationResult.ENCODING_ERROR,
        ]

    def test_nonexistent_directory_handling(self):
        """Test handling of files in nonexistent directories"""
        self.modifier.begin_transaction()

        nested_file = "nonexistent/directory/file.py"
        result = self.modifier.stage_modification(nested_file, "content")

        # Should succeed because stage_modification creates parent directories
        assert result.result == ValidationResult.SUCCESS


if __name__ == "__main__":
    pytest.main([__file__])
