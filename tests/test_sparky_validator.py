"""
Comprehensive tests for SparkySelfValidator.

Tests all validation capabilities to ensure we catch Sparky's common mistakes:
- Bad naming conventions (sentenceboundarychunker -> SentenceBoundaryChunker)
- Placeholder implementations (TODO, NotImplementedError, etc.)
- Critical file modifications
- Minimal method signatures
- Missing basic functionality
"""

from unittest.mock import patch
from core.sparky_validator import SparkySelfValidator, ValidationResult


class TestSparkySelfValidator:
    """Test suite for SparkySelfValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SparkySelfValidator()
        self.test_issue = {
            "number": 999,
            "title": "Test Issue",
            "body": "Implement a test feature",
        }

    def test_initialization(self):
        """Test validator initialization with correct defaults."""
        assert self.validator.max_iterations == 3
        assert self.validator.quality_threshold == 0.95
        assert len(self.validator.critical_files) > 0
        assert "config.py" in self.validator.critical_files

    def test_file_protection_critical_file_modified(self):
        """Test detection of critical file modifications."""
        implementation = {
            "files_modified": ["core/config.py", "src/feature.py"],
            "files_created": ["tests/test_feature.py"],
        }

        result = self.validator._check_file_protection(implementation)
        assert not result.passed
        assert "Critical file modified" in result.message
        assert "config.py" in result.fix_instructions

    def test_file_protection_safe_modifications(self):
        """Test that safe file modifications pass."""
        implementation = {
            "files_modified": ["src/feature.py", "tests/test_feature.py"],
            "files_created": ["src/new_feature.py"],
        }

        result = self.validator._check_file_protection(implementation)
        assert result.passed
        assert result.message == "File protection check passed"

    def test_naming_conventions_bad_camelcase(self):
        """Test detection of Sparky's signature bad naming."""
        implementation = {
            "class_names": [
                "backgroundexecutor",  # Should be BackgroundExecutor
                "sentenceboundarychunker",  # Should be SentenceBoundaryChunker
                "ValidClassName",
            ]
        }

        result = self.validator._check_naming_conventions(implementation)
        assert not result.passed
        assert "backgroundexecutor" in result.message
        assert "BackgroundExecutor" in result.fix_instructions
        assert "sentenceboundarychunker" in result.message

    def test_naming_conventions_good_names(self):
        """Test that proper naming conventions pass."""
        implementation = {
            "class_names": ["DataProcessor", "ConfigManager", "TestRunner"]
        }

        result = self.validator._check_naming_conventions(implementation)
        assert result.passed
        assert result.quality_score == 1.0

    def test_no_placeholders_found(self):
        """Test detection of placeholder code."""
        implementation = {
            "code_content": """
            def process_data():
                # TODO: Implement this
                pass
            
            def analyze():
                raise NotImplementedError("Need to implement")
            
            def compute():
                return "Unknown Feature"
            """
        }

        result = self.validator._check_no_placeholders(implementation)
        assert not result.passed
        assert "TODO" in result.message
        assert "NotImplementedError" in result.message
        assert "Unknown Feature" in result.message

    def test_no_placeholders_clean_code(self):
        """Test that code without placeholders passes."""
        implementation = {
            "code_content": '''
            def process_data(data):
                """Process the input data."""
                result = data.strip().lower()
                return result.split()
            
            def analyze(items):
                """Analyze the items."""
                return sum(len(item) for item in items)
            '''
        }

        result = self.validator._check_no_placeholders(implementation)
        assert result.passed
        assert result.quality_score == 1.0

    def test_method_signatures_minimal(self):
        """Test detection of minimal method signatures."""
        implementation = {
            "methods": [
                {"name": "process", "params": [], "has_docstring": False},
                {"name": "compute", "params": ["x"], "has_docstring": False},
                {
                    "name": "analyze",
                    "params": ["data", "options"],
                    "has_docstring": True,
                },
            ]
        }

        result = self.validator._check_method_signatures(implementation)
        assert not result.passed
        assert "process" in result.message
        assert "docstring" in result.fix_instructions.lower()

    def test_method_signatures_complete(self):
        """Test that complete method signatures pass."""
        implementation = {
            "methods": [
                {
                    "name": "process_data",
                    "params": ["data", "config"],
                    "has_docstring": True,
                },
                {
                    "name": "validate_input",
                    "params": ["input_str"],
                    "has_docstring": True,
                },
            ]
        }

        result = self.validator._check_method_signatures(implementation)
        assert result.passed
        assert result.quality_score == 1.0

    def test_basic_functionality_incomplete(self):
        """Test detection of incomplete functionality."""
        implementation = {
            "has_tests": False,
            "has_error_handling": False,
            "has_logging": False,
            "has_type_hints": True,
        }

        result = self.validator._check_basic_functionality(implementation)
        assert not result.passed
        assert "tests" in result.message
        assert "error handling" in result.message

    def test_basic_functionality_complete(self):
        """Test that complete functionality passes."""
        implementation = {
            "has_tests": True,
            "has_error_handling": True,
            "has_logging": True,
            "has_type_hints": True,
        }

        result = self.validator._check_basic_functionality(implementation)
        assert result.passed
        assert result.quality_score == 1.0

    def test_fix_camel_case(self):
        """Test CamelCase fixing logic."""
        test_cases = [
            ("backgroundexecutor", "BackgroundExecutor"),
            ("sentenceboundarychunker", "SentenceBoundaryChunker"),
            ("testrunner", "TestRunner"),
            ("apiclient", "APIClient"),
            ("xmlparser", "XMLParser"),
        ]

        for input_name, expected in test_cases:
            result = self.validator._fix_camel_case(input_name)
            assert (
                result == expected
            ), f"Failed for {input_name}: got {result}, expected {expected}"

    def test_validate_implementation_success(self):
        """Test successful validation with high quality."""
        # Mock implementation that passes all checks
        implementation = {
            "files_modified": ["src/feature.py"],
            "files_created": ["tests/test_feature.py"],
            "class_names": ["FeatureProcessor"],
            "method_names": ["process_data"],
            "code_content": "def process_data(data):\n    return data.strip()",
            "methods": [
                {"name": "process_data", "params": ["data"], "has_docstring": True}
            ],
            "has_tests": True,
            "has_error_handling": True,
            "has_logging": True,
            "has_type_hints": True,
        }

        result = self.validator.validate_implementation(implementation, self.test_issue)
        assert result["success"]
        assert result["quality_score"] >= 0.95
        assert result["iterations"] == 1

    def test_validate_implementation_with_retry(self):
        """Test validation with retry mechanism."""
        # First attempt - bad naming
        bad_implementation = {
            "files_modified": ["src/feature.py"],
            "class_names": ["backgroundexecutor"],  # Bad name
            "method_names": ["process"],
            "code_content": "def process(data):\n    return data",
            "methods": [{"name": "process", "params": ["data"], "has_docstring": True}],
            "has_tests": True,
            "has_error_handling": True,
            "has_logging": True,
            "has_type_hints": True,
        }

        # Fixed implementation
        fixed_implementation = {
            "files_modified": ["src/feature.py"],
            "class_names": ["BackgroundExecutor"],  # Fixed name
            "method_names": ["process_data"],
            "code_content": "def process_data(data):\n    return data",
            "methods": [
                {"name": "process_data", "params": ["data"], "has_docstring": True}
            ],
            "has_tests": True,
            "has_error_handling": True,
            "has_logging": True,
            "has_type_hints": True,
        }

        # Mock the fix_implementation method to return fixed version
        with patch.object(self.validator, "fix_implementation") as mock_fix:
            mock_fix.return_value = fixed_implementation

            result = self.validator.validate_implementation(
                bad_implementation, self.test_issue
            )
            assert result["success"]
            assert result["iterations"] == 2
            assert mock_fix.called

    def test_validate_implementation_max_iterations(self):
        """Test that validation stops after max iterations."""
        # Implementation that will never pass
        bad_implementation = {
            "files_modified": ["core/config.py"],  # Critical file
            "class_names": [],
            "code_content": "# TODO: Implement everything",
            "methods": [],
            "has_tests": False,
            "has_error_handling": False,
            "has_logging": False,
            "has_type_hints": False,
        }

        with patch.object(self.validator, "fix_implementation") as mock_fix:
            mock_fix.return_value = bad_implementation  # Never improves

            result = self.validator.validate_implementation(
                bad_implementation, self.test_issue
            )
            assert not result["success"]
            assert result["iterations"] == 3
            assert len(result["validation_errors"]) > 0

    def test_integration_full_validation_flow(self):
        """Test the complete validation flow end-to-end."""
        # Create implementation with mixed quality (typical Sparky output)
        implementation = {
            "files_modified": ["src/processor.py"],
            "files_created": ["tests/test_processor.py"],
            "class_names": ["DataProcessor", "resulthandler"],  # One bad name
            "method_names": ["process_data", "handle_result"],
            "code_content": '''
            class DataProcessor:
                def process_data(self, data):
                    """Process the input data."""
                    if not data:
                        raise ValueError("Empty data")
                    return data.strip()
            
            class resulthandler:  # Bad name
                def handle_result(self, result):
                    # TODO: Add validation
                    return result
            ''',
            "methods": [
                {
                    "name": "process_data",
                    "params": ["self", "data"],
                    "has_docstring": True,
                },
                {
                    "name": "handle_result",
                    "params": ["self", "result"],
                    "has_docstring": False,
                },
            ],
            "has_tests": True,
            "has_error_handling": True,
            "has_logging": False,
            "has_type_hints": False,
        }

        result = self.validator.validate_implementation(implementation, self.test_issue)

        # Should fail initially due to bad naming and TODO
        assert "quality_score" in result
        assert result["quality_score"] < 0.95

        # Should have specific error messages
        if not result["success"]:
            errors = result["validation_errors"]
            error_messages = " ".join(errors)
            assert "resulthandler" in error_messages or "TODO" in error_messages


class TestValidationResult:
    """Test the ValidationResult dataclass."""

    def test_creation_with_defaults(self):
        """Test ValidationResult creation with default values."""
        result = ValidationResult(passed=True, message="Test passed", quality_score=1.0)
        assert result.passed
        assert result.message == "Test passed"
        assert result.quality_score == 1.0
        assert result.fix_instructions == ""

    def test_creation_with_all_fields(self):
        """Test ValidationResult creation with all fields."""
        result = ValidationResult(
            passed=False,
            message="Test failed",
            quality_score=0.3,
            fix_instructions="Fix the issue by doing X",
        )
        assert not result.passed
        assert result.message == "Test failed"
        assert result.quality_score == 0.3
        assert result.fix_instructions == "Fix the issue by doing X"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_implementation(self):
        """Test validation with empty implementation."""
        validator = SparkySelfValidator()
        empty_impl = {}

        result = validator.validate_implementation(
            empty_impl, {"number": 1, "title": "Test"}
        )
        assert not result["success"]
        assert result["quality_score"] < 0.95  # Should fail validation

    def test_none_values_in_implementation(self):
        """Test handling of None values in implementation."""
        validator = SparkySelfValidator()
        impl_with_none = {
            "files_modified": None,
            "class_names": None,
            "code_content": None,
        }

        # Should handle gracefully without crashing
        result = validator.validate_implementation(
            impl_with_none, {"number": 1, "title": "Test"}
        )
        assert "quality_score" in result

    def test_malformed_class_names(self):
        """Test handling of malformed class names."""
        validator = SparkySelfValidator()

        weird_names = [
            "123Class",  # Starts with number
            "class-name",  # Contains hyphen
            "_PrivateClass",  # Starts with underscore
            "",  # Empty string
            "a" * 100,  # Very long name
        ]

        for name in weird_names:
            result = validator._fix_camel_case(name)
            assert isinstance(result, str)  # Should return something without crashing
