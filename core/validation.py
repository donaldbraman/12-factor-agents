#!/usr/bin/env uv run python
"""
Validation and Rollback System for Cross-Repository File Modifications

This module provides robust validation and rollback mechanisms for file modifications,
specifically designed to prevent syntax errors and provide transaction-like capabilities
for cross-repository operations.

Key Features:
- Pre-application syntax validation using ast.parse for Python files
- Transactional file modification with automatic rollback on failure
- Integration with ExecutionContext for cross-repo operations  
- Structured error handling and feedback
- Detection and prevention of common indentation errors
- Post-modification testing capabilities

The system addresses the critical issue where agents add malformed code
(like incorrectly indented `if result is not None:` checks) that cause
IndentationErrors and break the codebase.
"""

import ast
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

from core.execution_context import ExecutionContext


class ValidationResult(Enum):
    """Result status for validation operations"""

    SUCCESS = "success"
    SYNTAX_ERROR = "syntax_error"
    INDENTATION_ERROR = "indentation_error"
    ENCODING_ERROR = "encoding_error"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_ERROR = "permission_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ValidationError:
    """Detailed error information from validation"""

    result: ValidationResult
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    error_type: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class FileModificationRecord:
    """Record of a file modification for rollback purposes"""

    file_path: Path
    original_content: str
    modified_content: str
    backup_path: Optional[Path] = None
    modification_time: float = field(default_factory=lambda: __import__("time").time())


@dataclass
class TransactionState:
    """State tracking for transactional operations"""

    transaction_id: str
    modifications: Dict[str, FileModificationRecord] = field(default_factory=dict)
    backup_dir: Optional[Path] = None
    is_committed: bool = False
    is_rolled_back: bool = False


class TransactionalFileModifier:
    """
    Transactional file modifier with validation and rollback capabilities.

    Provides transaction-like semantics for file modifications:
    1. Begin transaction
    2. Stage modifications (with validation)
    3. Commit all changes or rollback on any failure

    Features:
    - Pre-modification syntax validation
    - Automatic backup creation
    - Atomic commit/rollback operations
    - Integration with ExecutionContext
    - Detailed error reporting
    """

    def __init__(self, context: ExecutionContext, transaction_id: Optional[str] = None):
        """
        Initialize the transactional modifier.

        Args:
            context: ExecutionContext for path resolution
            transaction_id: Optional transaction ID (generated if not provided)
        """
        self.context = context
        self.transaction_id = transaction_id or self._generate_transaction_id()
        self.state = TransactionState(transaction_id=self.transaction_id)
        self.logger = logging.getLogger(__name__)

    def _generate_transaction_id(self) -> str:
        """Generate a unique transaction ID"""
        import uuid

        return f"tx_{uuid.uuid4().hex[:8]}"

    def begin_transaction(self, backup_dir: Optional[Path] = None) -> str:
        """
        Begin a new transaction.

        Args:
            backup_dir: Optional directory for backups (temp dir if not provided)

        Returns:
            str: Transaction ID
        """
        if backup_dir is None:
            backup_dir = Path(tempfile.mkdtemp(prefix=f"backup_{self.transaction_id}_"))

        self.state.backup_dir = backup_dir
        self.state.backup_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(
            f"Transaction {self.transaction_id} started with backup dir: {backup_dir}"
        )
        return self.transaction_id

    def stage_modification(
        self, file_path: Union[str, Path], new_content: str, validate: bool = True
    ) -> ValidationError:
        """
        Stage a file modification with optional validation.

        Args:
            file_path: Path to file (relative to context or absolute)
            new_content: New file content
            validate: Whether to perform syntax validation

        Returns:
            ValidationError: Validation result (success or error details)
        """
        # Resolve file path using context
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.is_absolute():
            file_path = self.context.resolve_path(str(file_path))

        # Check if file exists and read original content
        if file_path.exists():
            try:
                original_content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError as e:
                return ValidationError(
                    result=ValidationResult.ENCODING_ERROR,
                    message=f"Could not read file due to encoding error: {e}",
                    error_type="UnicodeDecodeError",
                )
            except PermissionError as e:
                return ValidationError(
                    result=ValidationResult.PERMISSION_ERROR,
                    message=f"Permission denied reading file: {e}",
                    error_type="PermissionError",
                )
        else:
            # New file
            original_content = ""

        # Perform validation if requested
        if validate:
            validation_error = self.validate_content(file_path, new_content)
            if validation_error.result != ValidationResult.SUCCESS:
                return validation_error

        # Create backup if original content exists
        backup_path = None
        if original_content and self.state.backup_dir:
            backup_filename = f"{file_path.name}_{self.transaction_id}.backup"
            backup_path = self.state.backup_dir / backup_filename
            backup_path.write_text(original_content, encoding="utf-8")

        # Store modification record
        self.state.modifications[str(file_path)] = FileModificationRecord(
            file_path=file_path,
            original_content=original_content,
            modified_content=new_content,
            backup_path=backup_path,
        )

        self.logger.info(f"Staged modification for {file_path}")
        return ValidationError(
            result=ValidationResult.SUCCESS,
            message="File modification staged successfully",
        )

    def commit_transaction(self) -> Tuple[bool, List[ValidationError]]:
        """
        Commit all staged modifications.

        Returns:
            Tuple[bool, List[ValidationError]]: Success status and any errors
        """
        if self.state.is_committed:
            return False, [
                ValidationError(
                    result=ValidationResult.UNKNOWN_ERROR,
                    message="Transaction already committed",
                )
            ]

        errors = []

        # Apply all modifications
        for file_path_str, record in self.state.modifications.items():
            try:
                record.file_path.parent.mkdir(parents=True, exist_ok=True)
                record.file_path.write_text(record.modified_content, encoding="utf-8")
                self.logger.info(f"Applied modification to {record.file_path}")
            except Exception as e:
                errors.append(
                    ValidationError(
                        result=ValidationResult.UNKNOWN_ERROR,
                        message=f"Failed to write {record.file_path}: {e}",
                        error_type=type(e).__name__,
                    )
                )

        if errors:
            # Rollback on any error
            self.rollback_transaction()
            return False, errors

        self.state.is_committed = True
        self.logger.info(f"Transaction {self.transaction_id} committed successfully")
        return True, []

    def rollback_transaction(self) -> bool:
        """
        Rollback all modifications in the transaction.

        Returns:
            bool: Success status
        """
        if self.state.is_rolled_back:
            return True

        success = True

        # Restore original content for each file
        for file_path_str, record in self.state.modifications.items():
            try:
                if record.original_content:
                    # Restore original content
                    record.file_path.write_text(
                        record.original_content, encoding="utf-8"
                    )
                    self.logger.info(f"Restored {record.file_path}")
                elif record.file_path.exists():
                    # Remove newly created file
                    record.file_path.unlink()
                    self.logger.info(f"Removed newly created file {record.file_path}")
            except Exception as e:
                self.logger.error(f"Failed to rollback {record.file_path}: {e}")
                success = False

        self.state.is_rolled_back = True
        self.logger.info(f"Transaction {self.transaction_id} rolled back")
        return success

    def cleanup(self):
        """Clean up backup files and temporary directories"""
        if self.state.backup_dir and self.state.backup_dir.exists():
            try:
                shutil.rmtree(self.state.backup_dir)
                self.logger.info(f"Cleaned up backup directory {self.state.backup_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup backup directory: {e}")

    def validate_content(self, file_path: Path, content: str) -> ValidationError:
        """
        Validate file content based on file type.

        Args:
            file_path: Path to the file
            content: File content to validate

        Returns:
            ValidationError: Validation result
        """
        if file_path.suffix == ".py":
            return self.validate_python_syntax(content)
        elif file_path.suffix in [".json"]:
            return self.validate_json_syntax(content)
        elif file_path.suffix in [".yaml", ".yml"]:
            return self.validate_yaml_syntax(content)
        else:
            # For other file types, just check for basic issues
            return self.validate_generic_content(content)

    def validate_python_syntax(self, content: str) -> ValidationError:
        """
        Validate Python syntax using ast.parse and detect common indentation errors.

        Args:
            content: Python code content

        Returns:
            ValidationError: Validation result with detailed error info
        """
        try:
            # First check for common indentation patterns that cause issues
            indentation_error = self._check_indentation_patterns(content)
            if indentation_error:
                return indentation_error

            # Parse the content using AST
            ast.parse(content)
            return ValidationError(
                result=ValidationResult.SUCCESS, message="Python syntax is valid"
            )

        except IndentationError as e:
            return ValidationError(
                result=ValidationResult.INDENTATION_ERROR,
                message=f"Indentation error: {e.msg}",
                line_number=e.lineno,
                column_number=e.offset,
                error_type="IndentationError",
                suggested_fix=self._suggest_indentation_fix(
                    content, e.lineno, e.offset
                ),
            )

        except SyntaxError as e:
            return ValidationError(
                result=ValidationResult.SYNTAX_ERROR,
                message=f"Syntax error: {e.msg}",
                line_number=e.lineno,
                column_number=e.offset,
                error_type="SyntaxError",
                suggested_fix=self._suggest_syntax_fix(content, e),
            )

        except Exception as e:
            return ValidationError(
                result=ValidationResult.UNKNOWN_ERROR,
                message=f"Unexpected error during validation: {e}",
                error_type=type(e).__name__,
            )

    def _check_indentation_patterns(self, content: str) -> Optional[ValidationError]:
        """
        Check for common indentation patterns that cause errors.

        This specifically targets the bug mentioned in the requirements where agents
        add `if result is not None:` checks with incorrect indentation.

        Args:
            content: Python code content

        Returns:
            Optional[ValidationError]: Error if problematic pattern found
        """
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for common problematic patterns
            problematic_patterns = [
                (r"^\s*if\s+\w+\s+is\s+not\s+None\s*:", "if result is not None"),
                (r"^\s*if\s+result\s*:", "if result"),
                (r"^\s*if\s+\w+\s*!=\s*None\s*:", "if variable != None"),
            ]

            for pattern, description in problematic_patterns:
                if re.match(pattern, line):
                    # Check if this line has incorrect indentation
                    # Look at surrounding context
                    context_lines = lines[max(0, i - 3) : min(len(lines), i + 2)]

                    # Calculate expected indentation based on context
                    expected_indent = self._calculate_expected_indentation(
                        context_lines, len(context_lines) - 3
                    )
                    actual_indent = len(line) - len(line.lstrip())

                    if actual_indent != expected_indent:
                        return ValidationError(
                            result=ValidationResult.INDENTATION_ERROR,
                            message=f"Incorrect indentation for {description} statement. Expected {expected_indent} spaces, got {actual_indent}",
                            line_number=i,
                            column_number=actual_indent,
                            error_type="IndentationError",
                            suggested_fix=f"Change indentation from {actual_indent} to {expected_indent} spaces",
                        )

        return None

    def _calculate_expected_indentation(
        self, context_lines: List[str], target_line_index: int
    ) -> int:
        """
        Calculate the expected indentation level for a line based on context.

        Args:
            context_lines: Lines around the target line
            target_line_index: Index of the target line in context_lines

        Returns:
            int: Expected indentation level in spaces
        """
        if target_line_index <= 0:
            return 0

        # Look at the previous non-empty line
        for i in range(target_line_index - 1, -1, -1):
            prev_line = context_lines[i].rstrip()
            if prev_line:
                prev_indent = len(context_lines[i]) - len(context_lines[i].lstrip())

                # If previous line ends with ':', increase indentation
                if prev_line.endswith(":"):
                    return prev_indent + 4
                else:
                    return prev_indent

        return 0

    def _suggest_indentation_fix(
        self, content: str, line_number: Optional[int], column: Optional[int]
    ) -> str:
        """Suggest a fix for indentation errors"""
        if line_number is None:
            return (
                "Check indentation levels and ensure consistent use of spaces or tabs"
            )

        lines = content.split("\n")
        if line_number <= len(lines):
            _ = lines[line_number - 1]

            # Calculate what the indentation should be
            expected_indent = self._calculate_expected_indentation(
                lines[:line_number], line_number - 1
            )

            return f"Line {line_number}: Change indentation to {expected_indent} spaces"

        return "Fix indentation on the indicated line"

    def _suggest_syntax_fix(self, content: str, syntax_error: SyntaxError) -> str:
        """Suggest a fix for syntax errors"""
        if "invalid syntax" in syntax_error.msg.lower():
            return "Check for missing colons, parentheses, or incorrect operators"
        elif "unexpected indent" in syntax_error.msg.lower():
            return "Remove unexpected indentation"
        elif "unindent does not match" in syntax_error.msg.lower():
            return "Fix indentation to match outer indentation level"
        else:
            return f"Fix syntax error: {syntax_error.msg}"

    def validate_json_syntax(self, content: str) -> ValidationError:
        """Validate JSON syntax"""
        try:
            import json

            json.loads(content)
            return ValidationError(
                result=ValidationResult.SUCCESS, message="JSON syntax is valid"
            )
        except json.JSONDecodeError as e:
            return ValidationError(
                result=ValidationResult.SYNTAX_ERROR,
                message=f"JSON syntax error: {e.msg}",
                line_number=e.lineno,
                column_number=e.colno,
                error_type="JSONDecodeError",
            )

    def validate_yaml_syntax(self, content: str) -> ValidationError:
        """Validate YAML syntax"""
        try:
            import yaml

            yaml.safe_load(content)
            return ValidationError(
                result=ValidationResult.SUCCESS, message="YAML syntax is valid"
            )
        except yaml.YAMLError as e:
            line_number = None
            column_number = None
            if hasattr(e, "problem_mark"):
                line_number = e.problem_mark.line + 1
                column_number = e.problem_mark.column + 1

            return ValidationError(
                result=ValidationResult.SYNTAX_ERROR,
                message=f"YAML syntax error: {e}",
                line_number=line_number,
                column_number=column_number,
                error_type="YAMLError",
            )

    def validate_generic_content(self, content: str) -> ValidationError:
        """Validate generic file content for basic issues"""
        # Check for null bytes or other problematic characters
        if "\0" in content:
            return ValidationError(
                result=ValidationResult.SYNTAX_ERROR,
                message="File contains null bytes",
                error_type="InvalidContent",
            )

        return ValidationError(
            result=ValidationResult.SUCCESS, message="Content appears valid"
        )


def validate_file_content(file_path: Union[str, Path], content: str) -> ValidationError:
    """
    Standalone function to validate file content.

    Args:
        file_path: Path to the file (for determining validation type)
        content: Content to validate

    Returns:
        ValidationError: Validation result
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Create a temporary context for validation
    from core.execution_context import create_default_context

    context = create_default_context()

    modifier = TransactionalFileModifier(context)
    return modifier.validate_content(file_path, content)


def create_safe_file_modifier(context: ExecutionContext) -> TransactionalFileModifier:
    """
    Factory function to create a file modifier with safety defaults.

    Args:
        context: ExecutionContext for operations

    Returns:
        TransactionalFileModifier: Configured modifier instance
    """
    return TransactionalFileModifier(context)


class ValidationIntegrationMixin:
    """
    Mixin class that can be added to agents to provide validation capabilities.

    This mixin provides methods that agents can use to safely modify files
    with validation and rollback support.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_modifier: Optional[TransactionalFileModifier] = None

    def _get_file_modifier(self) -> TransactionalFileModifier:
        """Get or create the file modifier instance"""
        if self._file_modifier is None:
            context = getattr(self, "context", None)
            if context is None:
                from core.execution_context import create_default_context

                context = create_default_context()
            self._file_modifier = TransactionalFileModifier(context)
        return self._file_modifier

    def begin_safe_modifications(self) -> str:
        """Begin a transaction for safe file modifications"""
        modifier = self._get_file_modifier()
        return modifier.begin_transaction()

    def stage_file_change(
        self, file_path: Union[str, Path], content: str, validate: bool = True
    ) -> ValidationError:
        """Stage a file change with validation"""
        modifier = self._get_file_modifier()
        return modifier.stage_modification(file_path, content, validate)

    def commit_changes(self) -> Tuple[bool, List[ValidationError]]:
        """Commit all staged changes"""
        modifier = self._get_file_modifier()
        return modifier.commit_transaction()

    def rollback_changes(self) -> bool:
        """Rollback all changes"""
        modifier = self._get_file_modifier()
        return modifier.rollback_transaction()

    def cleanup_modifications(self):
        """Clean up modification resources"""
        if self._file_modifier:
            self._file_modifier.cleanup()
            self._file_modifier = None


# Example usage and testing utilities
if __name__ == "__main__":
    # Example usage
    from core.execution_context import create_default_context

    context = create_default_context()
    modifier = TransactionalFileModifier(context)

    # Begin transaction
    tx_id = modifier.begin_transaction()
    print(f"Started transaction: {tx_id}")

    # Test validation
    test_code = """
def test_function():
    if result is not None:
        return result
    return None
"""

    validation_result = modifier.validate_python_syntax(test_code)
    print(f"Validation result: {validation_result}")

    # Clean up
    modifier.cleanup()
