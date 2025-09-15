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
from typing import Dict, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
import logging
import time

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
class RetryAttempt:
    """Record of a retry attempt"""

    attempt_number: int
    strategy: str
    original_content: str
    modified_content: str
    validation_error: ValidationError
    success: bool
    timestamp: float = field(default_factory=time.time)


@dataclass
class RetryResult:
    """Result of the intelligent retry process"""

    success: bool
    final_content: Optional[str] = None
    attempts: List[RetryAttempt] = field(default_factory=list)
    total_attempts: int = 0
    final_error: Optional[ValidationError] = None
    resolution_strategy: Optional[str] = None


class RetryStrategy(Enum):
    """Different retry strategies for fixing validation errors"""

    MECHANICAL_FIX = "mechanical_fix"  # Direct application of suggested fixes
    REGENERATION = "regeneration"  # Regenerate problematic sections
    SIMPLIFIED = "simplified"  # Simplify the approach
    ESCALATION = "escalation"  # Escalate to user


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


class IntelligentValidationRetry:
    """
    Intelligent validation retry mechanism that automatically fixes common validation errors.

    This system implements progressive retry strategies:
    1. Mechanical Fix: Apply suggested fixes directly (e.g., fix indentation)
    2. Regeneration: Regenerate problematic code sections
    3. Simplified: Simplify the approach to avoid complexity

    Designed to achieve 95% autonomous resolution for common syntax errors.
    """

    def __init__(self, max_attempts: int = 3, logger: Optional[logging.Logger] = None):
        """
        Initialize the intelligent retry system.

        Args:
            max_attempts: Maximum number of retry attempts before escalation
            logger: Optional logger for debugging
        """
        self.max_attempts = max_attempts
        self.logger = logger or logging.getLogger(__name__)

        # Strategy progression: more aggressive fixes as attempts increase
        self.strategy_progression = [
            RetryStrategy.MECHANICAL_FIX,
            RetryStrategy.REGENERATION,
            RetryStrategy.SIMPLIFIED,
        ]

    def retry_with_validation(
        self,
        file_path: Path,
        content: str,
        validator: Callable[[Path, str], ValidationError],
    ) -> RetryResult:
        """
        Attempt to fix validation errors through intelligent retry.

        Args:
            file_path: Path to the file being validated
            content: Content to validate and potentially fix
            validator: Function that validates content and returns ValidationError

        Returns:
            RetryResult: Complete result of the retry process
        """
        attempts = []
        current_content = content

        for attempt_num in range(self.max_attempts):
            # Validate current content
            try:
                validation_error = validator(file_path, current_content)
            except Exception as e:
                self.logger.error(
                    f"Validator exception on attempt {attempt_num + 1}: {e}"
                )
                return RetryResult(
                    success=False,
                    final_content=current_content,
                    attempts=attempts,
                    total_attempts=len(attempts),
                    final_error=ValidationError(
                        result=ValidationResult.UNKNOWN_ERROR,
                        message=f"Validator exception: {e}",
                        error_type=type(e).__name__,
                    ),
                    resolution_strategy="validator_exception",
                )

            if validation_error.result == ValidationResult.SUCCESS:
                # Success! Return the result
                return RetryResult(
                    success=True,
                    final_content=current_content,
                    attempts=attempts,
                    total_attempts=len(attempts),
                    resolution_strategy=attempts[-1].strategy
                    if attempts
                    else "no_retry_needed",
                )

            # Determine strategy for this attempt
            strategy = self.strategy_progression[
                min(attempt_num, len(self.strategy_progression) - 1)
            ]

            self.logger.info(
                f"Retry attempt {attempt_num + 1}/{self.max_attempts} using {strategy.value}"
            )
            self.logger.info(f"Validation error: {validation_error.message}")

            # Apply the strategy to fix the content
            fixed_content = self._apply_strategy(
                strategy, current_content, validation_error, file_path
            )

            # Record this attempt
            attempt = RetryAttempt(
                attempt_number=attempt_num + 1,
                strategy=strategy.value,
                original_content=current_content,
                modified_content=fixed_content,
                validation_error=validation_error,
                success=False,  # Will be updated if this fixes the issue
            )
            attempts.append(attempt)

            # Update current content for next iteration
            current_content = fixed_content

        # All attempts failed
        final_validation = validator(file_path, current_content)
        return RetryResult(
            success=False,
            final_content=current_content,
            attempts=attempts,
            total_attempts=len(attempts),
            final_error=final_validation,
            resolution_strategy="escalation_required",
        )

    def _apply_strategy(
        self,
        strategy: RetryStrategy,
        content: str,
        error: ValidationError,
        file_path: Path,
    ) -> str:
        """Apply a specific retry strategy to fix the content."""

        if strategy == RetryStrategy.MECHANICAL_FIX:
            return self._apply_mechanical_fix(content, error)
        elif strategy == RetryStrategy.REGENERATION:
            return self._apply_regeneration_fix(content, error, file_path)
        elif strategy == RetryStrategy.SIMPLIFIED:
            return self._apply_simplified_fix(content, error)
        else:
            return content  # No change

    def _apply_mechanical_fix(self, content: str, error: ValidationError) -> str:
        """
        Apply direct mechanical fixes based on validation error messages.

        This handles cases like:
        - "Expected 4 spaces, got 0" -> Add 4 spaces
        - Specific indentation errors
        - Simple syntax fixes
        """
        lines = content.split("\n")

        if error.line_number and error.line_number <= len(lines):
            line_idx = error.line_number - 1  # Convert to 0-based index
            current_line = lines[line_idx]

            # Handle indentation errors specifically
            if error.result == ValidationResult.INDENTATION_ERROR:
                fixed_line = self._fix_indentation_error(current_line, error)
                if fixed_line != current_line:
                    lines[line_idx] = fixed_line
                    self.logger.info(
                        f"Applied indentation fix to line {error.line_number}"
                    )
                    return "\n".join(lines)

            # Handle other syntax errors
            elif error.result == ValidationResult.SYNTAX_ERROR:
                fixed_line = self._fix_syntax_error(current_line, error)
                if fixed_line != current_line:
                    lines[line_idx] = fixed_line
                    self.logger.info(f"Applied syntax fix to line {error.line_number}")
                    return "\n".join(lines)

        return content  # No changes applied

    def _fix_indentation_error(self, line: str, error: ValidationError) -> str:
        """Fix specific indentation errors."""

        # Parse error message for expected vs actual indentation
        message = error.message.lower()

        # Match patterns like "expected 4 spaces, got 0"
        expected_match = re.search(r"expected (\d+) spaces?, got (\d+)", message)
        if expected_match:
            expected_spaces = int(expected_match.group(1))
            actual_spaces = int(expected_match.group(2))

            # Calculate the difference
            spaces_diff = expected_spaces - actual_spaces

            if spaces_diff > 0:
                # Add spaces
                stripped_line = line.lstrip()
                return " " * expected_spaces + stripped_line
            elif spaces_diff < 0:
                # Remove spaces (more complex, be careful)
                stripped_line = line.lstrip()
                return " " * expected_spaces + stripped_line

        # Handle "unindent does not match any outer indentation level"
        if "unindent does not match" in message:
            # Try to fix by aligning with common indentation levels (0, 4, 8, 12)
            stripped_line = line.lstrip()
            # Default to 4 spaces for most cases
            return " " * 4 + stripped_line

        # Handle "unexpected indent"
        if "unexpected indent" in message:
            # Remove the unexpected indentation
            return line.lstrip()

        # General fallback for indentation errors - try common indentations
        if error.result == ValidationResult.INDENTATION_ERROR:
            stripped_line = line.lstrip()
            # If we have a line number and can infer expected indentation
            if error.column_number is not None:
                # Try to use the column number as a hint
                expected_indent = max(0, error.column_number)
                return " " * expected_indent + stripped_line
            else:
                # Default to 4 spaces for basic indentation
                return "    " + stripped_line

        return line  # No fix applied

    def _fix_syntax_error(self, line: str, error: ValidationError) -> str:
        """Fix common syntax errors."""

        message = error.message.lower()

        # Fix missing colons
        if (
            "invalid syntax" in message
            and ":" not in line
            and any(
                keyword in line.lower()
                for keyword in [
                    "if ",
                    "def ",
                    "class ",
                    "for ",
                    "while ",
                    "try",
                    "except",
                    "with ",
                ]
            )
        ):
            # Add colon at the end
            return line.rstrip() + ":"

        # Fix missing parentheses in print statements
        if "invalid syntax" in message and line.strip().startswith("print "):
            # Convert print statement to print function
            content = line.strip()[6:]  # Remove 'print '
            indentation = line[: len(line) - len(line.lstrip())]
            return f"{indentation}print({content})"

        return line  # No fix applied

    def _apply_regeneration_fix(
        self, content: str, error: ValidationError, file_path: Path
    ) -> str:
        """
        Regenerate problematic code sections.

        This strategy identifies the problematic area and generates a simpler,
        more reliable version of the same functionality.
        """
        lines = content.split("\n")

        if not error.line_number:
            return content

        line_idx = error.line_number - 1

        # Find the scope of the problematic section (function, class, etc.)
        start_idx, end_idx = self._find_code_block_boundaries(lines, line_idx)

        # Extract the problematic block
        problematic_block = lines[start_idx : end_idx + 1]

        # Generate a simplified version
        regenerated_block = self._regenerate_code_block(problematic_block, error)

        # Replace the block
        new_lines = lines[:start_idx] + regenerated_block + lines[end_idx + 1 :]

        self.logger.info(
            f"Regenerated code block from lines {start_idx + 1} to {end_idx + 1}"
        )
        return "\n".join(new_lines)

    def _find_code_block_boundaries(
        self, lines: List[str], error_line_idx: int
    ) -> Tuple[int, int]:
        """Find the start and end of the code block containing the error."""

        # Look backwards for function/class definition
        start_idx = error_line_idx
        for i in range(error_line_idx, -1, -1):
            line = lines[i].strip()
            if line.startswith(("def ", "class ", "if ", "for ", "while ", "try:")):
                start_idx = i
                break

        # Look forwards for the end of the block
        end_idx = error_line_idx
        base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())

        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            if line.strip():  # Non-empty line
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= base_indent and not line.strip().startswith("#"):
                    end_idx = i - 1
                    break
            end_idx = i

        return start_idx, end_idx

    def _regenerate_code_block(
        self, block: List[str], error: ValidationError
    ) -> List[str]:
        """Generate a simpler version of the code block."""

        if not block:
            return block

        first_line = block[0].strip()
        base_indent = len(block[0]) - len(block[0].lstrip())

        # Handle function definitions
        if first_line.startswith("def "):
            func_name = first_line.split("(")[0].replace("def ", "")
            return [
                block[0],  # Keep original function signature
                " " * (base_indent + 4)
                + '"""Simplified implementation after validation error"""',
                " " * (base_indent + 4) + "pass  # TODO: Implement " + func_name,
            ]

        # Handle if statements with indentation issues
        if first_line.startswith("if "):
            return [
                block[0],  # Keep original if statement
                " " * (base_indent + 4) + "pass  # Simplified due to validation error",
            ]

        # Default: just simplify with pass
        return [
            block[0],
            " " * (base_indent + 4) + "pass  # Simplified after validation error",
        ]

    def _apply_simplified_fix(self, content: str, error: ValidationError) -> str:
        """
        Apply a simplified approach that removes complexity.

        This is the most aggressive strategy that prioritizes working code
        over feature completeness.
        """
        lines = content.split("\n")

        if not error.line_number:
            return content

        line_idx = error.line_number - 1
        current_line = lines[line_idx]
        base_indent = len(current_line) - len(current_line.lstrip())

        # For indentation errors, use the most conservative approach
        if error.result == ValidationResult.INDENTATION_ERROR:
            stripped_line = current_line.lstrip()

            # If it's a complex statement, simplify it
            if any(
                keyword in stripped_line.lower()
                for keyword in ["if ", "for ", "while ", "try:"]
            ):
                # Replace with a simple pass statement
                lines[line_idx] = (
                    " " * base_indent + "pass  # Simplified due to validation error"
                )
            else:
                # Just fix the indentation to 0 or 4 spaces
                target_indent = 4 if any(c.isalpha() for c in stripped_line) else 0
                lines[line_idx] = " " * target_indent + stripped_line

        # For syntax errors, comment out the problematic line
        elif error.result == ValidationResult.SYNTAX_ERROR:
            lines[line_idx] = (
                " " * base_indent
                + "# "
                + current_line.lstrip()
                + "  # Commented due to syntax error"
            )

        self.logger.info(f"Applied simplified fix to line {error.line_number}")
        return "\n".join(lines)


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
        self.retry_system = IntelligentValidationRetry(logger=self.logger)

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

    def stage_modification_with_retry(
        self, file_path: Union[str, Path], new_content: str, validate: bool = True
    ) -> Tuple[ValidationError, Optional[RetryResult]]:
        """
        Stage a file modification with intelligent retry on validation failures.

        This method uses the IntelligentValidationRetry system to automatically
        fix validation errors through progressive strategies.

        Args:
            file_path: Path to file (relative to context or absolute)
            new_content: New file content
            validate: Whether to perform syntax validation with retry

        Returns:
            Tuple[ValidationError, Optional[RetryResult]]:
                - ValidationError: Final validation result
                - RetryResult: Details of retry process (None if no retry needed)
        """
        # Resolve file path using context
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.is_absolute():
            file_path = self.context.resolve_path(str(file_path))

        if not validate:
            # No retry if validation is disabled
            return self.stage_modification(file_path, new_content, validate=False), None

        # Create a validator function for the retry system
        def validator(path: Path, content: str) -> ValidationError:
            return self.validate_content(path, content)

        # Try with intelligent retry
        retry_result = self.retry_system.retry_with_validation(
            file_path, new_content, validator
        )

        if retry_result.success:
            # Retry succeeded, stage the final content
            final_validation = self.stage_modification(
                file_path, retry_result.final_content, validate=False
            )
            self.logger.info(
                f"Successfully staged {file_path} after {retry_result.total_attempts} retry attempts "
                f"using {retry_result.resolution_strategy} strategy"
            )
            return final_validation, retry_result
        else:
            # Retry failed, log the failure details
            self.logger.warning(
                f"Failed to fix validation errors for {file_path} after {retry_result.total_attempts} attempts"
            )
            if retry_result.final_error:
                self.logger.warning(f"Final error: {retry_result.final_error.message}")

            return (
                retry_result.final_error
                or ValidationError(
                    result=ValidationResult.UNKNOWN_ERROR,
                    message="Retry system failed without specific error",
                ),
                retry_result,
            )

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

    def stage_file_change_with_retry(
        self, file_path: Union[str, Path], content: str, validate: bool = True
    ) -> Tuple[ValidationError, Optional["RetryResult"]]:
        """Stage a file change with intelligent validation retry"""
        modifier = self._get_file_modifier()
        return modifier.stage_modification_with_retry(file_path, content, validate)

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
