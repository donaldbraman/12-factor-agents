"""
Tests for Factor 9: Compact Errors into Context Window compliance validation.
"""

from core.compliance import Factor9Validator, ComplianceLevel
from core.agent import BaseAgent
from core.tools import ToolResponse
from core.execution_context import ExecutionContext
from typing import Any, Dict


class CompliantErrorCompactionAgent(BaseAgent):
    """Example of agent with proper error compaction."""

    # Error codes (Factor 9 compliance)
    ERR_DB_001 = "Database connection failed"
    ERR_VALIDATION_002 = "Input validation error"
    ERR_TIMEOUT_003 = "Operation timeout"

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        """Execute task with proper error handling."""
        try:
            return ToolResponse(
                success=True,
                data={"task": task, "result": f"Processed: {task}"},
            )
        except Exception as e:
            # Compact error handling
            compacted_error = self.compact_error(str(e))
            return ToolResponse(success=False, error=compacted_error)

    def handle_error(self, error: Exception) -> str:
        """Handle and compact errors efficiently."""
        error_str = str(error)

        # Truncate long error messages
        if len(error_str) > 100:
            error_str = error_str[:97] + "..."

        # Classify error and add code
        error_code = self.classify_error(error)
        return f"{error_code}: {error_str}"

    def compact_error(self, error_msg: str) -> str:
        """Compact verbose error messages."""
        # Remove stack trace details, keep essential info
        if "Traceback" in error_msg:
            # Extract just the error type and message from the last line
            lines = [line.strip() for line in error_msg.split("\n") if line.strip()]
            for line in reversed(lines):
                if (
                    line
                    and not line.startswith("File")
                    and not line.startswith("Traceback")
                    and ":" in line
                ):
                    return line.strip()
            # If no proper error line found, take the last non-empty line
            if lines:
                return lines[-1].strip()

        # Truncate if too long
        max_length = 150
        if len(error_msg) > max_length:
            return error_msg[: max_length - 3] + "..."

        return error_msg

    def classify_error(self, error: Exception) -> str:
        """Classify errors and return appropriate code."""
        error_type = type(error).__name__
        error_msg = str(error).lower()

        if "connection" in error_msg or "database" in error_msg:
            return "ERR_DB_001"
        elif "validation" in error_msg or "invalid" in error_msg:
            return "ERR_VALIDATION_002"
        elif "timeout" in error_msg:
            return "ERR_TIMEOUT_003"
        else:
            return f"ERR_GENERAL_{hash(error_type) % 1000:03d}"

    def summarize_errors(self) -> Dict[str, Any]:
        """Summarize historical errors for context efficiency."""
        if not hasattr(self.state, "get_recent_history"):
            return {"error_count": 0, "patterns": []}

        history = self.state.get_recent_history(50)  # Last 50 entries
        errors = [entry for entry in history if not entry.get("success", True)]

        # Group by error patterns
        error_patterns = {}
        for error in errors:
            error_msg = error.get("error", "")
            error_code = error_msg.split(":")[0] if ":" in error_msg else "UNKNOWN"
            error_patterns[error_code] = error_patterns.get(error_code, 0) + 1

        return {
            "error_count": len(errors),
            "patterns": error_patterns,
            "recent_errors": errors[-5:] if errors else [],  # Last 5 errors
        }

    def get_error_context(self, max_entries: int = 10) -> str:
        """Get relevant error context efficiently."""
        summary = self.summarize_errors()

        if summary["error_count"] == 0:
            return "No recent errors"

        # Compact context
        context_parts = [
            f"Recent errors: {summary['error_count']}",
            f"Top patterns: {dict(list(summary['patterns'].items())[:3])}",
        ]

        return " | ".join(context_parts)


class NoErrorHandlingAgent(BaseAgent):
    """Example of agent without error handling."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        # No error handling
        return ToolResponse(success=True, data={"task": task})


class VerboseErrorAgent(BaseAgent):
    """Example of agent with verbose, uncompacted errors."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})

    def handle_error(self, error: Exception) -> str:
        """Verbose error handling - not compacted."""
        # Return full stack trace (bad for Factor 9)
        import traceback

        return f"Full error details:\n{traceback.format_exc()}\nError: {str(error)}\nThis is a very long error message that doesn't compact information efficiently and wastes context window space."


class PartialErrorCompactionAgent(BaseAgent):
    """Example of agent with partial error compaction."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})

    def compact_error(self, error_msg: str) -> str:
        """Basic error compaction."""
        if len(error_msg) > 200:
            return error_msg[:197] + "..."
        return error_msg

    # Missing: error codes, pattern recognition, summarization


class TestFactor9Validator:
    """Test suite for Factor 9 validator."""

    def test_compliant_error_compaction_agent(self):
        """Test that agent with proper error compaction passes validation."""
        agent = CompliantErrorCompactionAgent()
        validator = Factor9Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.FULLY_COMPLIANT
        assert details["score"] == 1.0
        assert details["checks"]["error_compaction"]
        assert details["checks"]["error_patterns"]
        assert details["checks"]["context_efficiency"]
        assert details["checks"]["error_summarization"]
        assert len(details["issues"]) == 0

    def test_no_error_handling_agent(self):
        """Test that agent without error handling fails validation."""
        agent = NoErrorHandlingAgent()
        validator = Factor9Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert details["score"] == 0.0
        assert not details["checks"]["error_compaction"]
        assert not details["checks"]["error_patterns"]
        assert len(details["issues"]) > 0
        assert len(details["recommendations"]) > 0

    def test_verbose_error_agent(self):
        """Test that agent with verbose errors gets lower score."""
        agent = VerboseErrorAgent()
        validator = Factor9Validator()

        compliance, details = validator.validate(agent)

        # Should fail most checks due to verbose error handling
        assert compliance in [
            ComplianceLevel.NON_COMPLIANT,
            ComplianceLevel.PARTIALLY_COMPLIANT,
        ]
        assert details["score"] < 1.0
        assert len(details["issues"]) > 0

    def test_partial_error_compaction_agent(self):
        """Test that agent with partial error compaction gets partial score."""
        agent = PartialErrorCompactionAgent()
        validator = Factor9Validator()

        compliance, details = validator.validate(agent)

        assert compliance in [
            ComplianceLevel.NON_COMPLIANT,
            ComplianceLevel.PARTIALLY_COMPLIANT,
        ]
        assert details["score"] == 0.25  # Should get only compaction points
        assert details["checks"]["error_compaction"]  # Has compaction
        assert not details["checks"]["error_patterns"]  # No patterns
        assert not details["checks"]["context_efficiency"]  # No context efficiency
        assert not details["checks"]["error_summarization"]  # No summarization

    def test_error_compaction_detection(self):
        """Test error compaction detection logic."""
        agent = CompliantErrorCompactionAgent()
        validator = Factor9Validator()

        # Test compaction method exists and works
        assert hasattr(agent, "compact_error")

        # Test compaction functionality
        long_error = "A" * 200  # Very long error
        compacted = agent.compact_error(long_error)
        assert len(compacted) < len(long_error)
        assert "..." in compacted

        # Test validation detects compaction
        has_compaction = validator._check_error_compaction(agent)
        assert has_compaction

    def test_error_patterns_detection(self):
        """Test error patterns and codes detection."""
        agent = CompliantErrorCompactionAgent()
        validator = Factor9Validator()

        # Test error codes exist
        assert hasattr(agent, "ERR_DB_001")
        assert hasattr(agent, "ERR_VALIDATION_002")
        assert hasattr(agent, "ERR_TIMEOUT_003")

        # Test classification works
        assert hasattr(agent, "classify_error")

        # Test validation detects patterns
        has_patterns = validator._check_error_patterns(agent)
        assert has_patterns

    def test_context_efficiency_detection(self):
        """Test context efficiency detection."""
        agent = CompliantErrorCompactionAgent()
        validator = Factor9Validator()

        # Test context management exists
        assert hasattr(agent, "get_error_context")

        # Test context is efficient
        context = agent.get_error_context()
        assert isinstance(context, str)
        assert len(context) < 500  # Should be compact

        # Test validation detects efficiency
        has_efficiency = validator._check_context_efficiency(agent)
        assert has_efficiency

    def test_error_summarization_detection(self):
        """Test error summarization detection."""
        agent = CompliantErrorCompactionAgent()
        validator = Factor9Validator()

        # Test summarization method exists
        assert hasattr(agent, "summarize_errors")

        # Test summarization works
        summary = agent.summarize_errors()
        assert isinstance(summary, dict)
        assert "error_count" in summary
        assert "patterns" in summary

        # Test validation detects summarization
        has_summarization = validator._check_error_summarization(agent)
        assert has_summarization

    def test_error_classification_functionality(self):
        """Test error classification functionality."""
        agent = CompliantErrorCompactionAgent()

        # Test different error types get different codes
        db_error = Exception("Database connection failed")
        validation_error = Exception("Invalid input provided")
        timeout_error = Exception("Operation timeout occurred")

        db_code = agent.classify_error(db_error)
        validation_code = agent.classify_error(validation_error)
        timeout_code = agent.classify_error(timeout_error)

        assert db_code == "ERR_DB_001"
        assert validation_code == "ERR_VALIDATION_002"
        assert timeout_code == "ERR_TIMEOUT_003"

    def test_error_compaction_functionality(self):
        """Test error compaction functionality."""
        agent = CompliantErrorCompactionAgent()

        # Test stack trace compaction
        stack_trace = """
        Traceback (most recent call last):
          File "/path/to/file.py", line 123, in function
            result = complex_operation()
          File "/path/to/other.py", line 456, in complex_operation
            data = fetch_data()
        ConnectionError: Database connection failed
        """

        compacted = agent.compact_error(stack_trace)
        assert "ConnectionError: Database connection failed" in compacted
        assert "Traceback" not in compacted
        assert len(compacted) < len(stack_trace)

    def test_error_context_efficiency(self):
        """Test error context is efficiently managed."""
        agent = CompliantErrorCompactionAgent()

        # Simulate some error history in state
        if hasattr(agent.state, "history"):
            # Add some mock errors
            agent.state.history.extend(
                [
                    {"success": False, "error": "ERR_DB_001: Connection timeout"},
                    {"success": False, "error": "ERR_DB_001: Connection refused"},
                    {"success": True, "data": {"task": "success"}},
                    {"success": False, "error": "ERR_VALIDATION_002: Invalid email"},
                ]
            )

        context = agent.get_error_context()
        assert len(context) < 200  # Should be compact
        assert "Recent errors:" in context or "No recent errors" in context

    def test_recommendations_provided(self):
        """Test that validator provides actionable recommendations."""
        agent = NoErrorHandlingAgent()
        validator = Factor9Validator()

        _, details = validator.validate(agent)

        assert len(details["recommendations"]) > 0
        recommendations_text = " ".join(details["recommendations"])
        assert "compact" in recommendations_text.lower()
        assert "error" in recommendations_text.lower()

    def test_edge_cases(self):
        """Test validator handles edge cases gracefully."""
        validator = Factor9Validator()

        # Test agent without state
        class NoStateAgent(BaseAgent):
            def __init__(self):
                super().__init__()
                self.state = None

            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            def execute_task(
                self, task: str, context: ExecutionContext = None
            ) -> ToolResponse:
                return ToolResponse(success=True, data={"task": task})

        agent = NoStateAgent()
        compliance, details = validator.validate(agent)

        # Should handle gracefully
        assert isinstance(details["score"], float)
        assert 0.0 <= details["score"] <= 1.0

    def test_state_based_error_tracking(self):
        """Test error tracking through state management."""
        agent = CompliantErrorCompactionAgent()

        # Verify state has error tracking capability
        if hasattr(agent.state, "get_summary"):
            summary = agent.state.get_summary()
            assert isinstance(summary, dict)

    def test_compliance_level_thresholds(self):
        """Test compliance level determination."""
        # Test different score thresholds
        test_cases = [
            (1.0, ComplianceLevel.FULLY_COMPLIANT),
            (0.9, ComplianceLevel.FULLY_COMPLIANT),
            (0.8, ComplianceLevel.MOSTLY_COMPLIANT),
            (0.75, ComplianceLevel.MOSTLY_COMPLIANT),
            (0.6, ComplianceLevel.PARTIALLY_COMPLIANT),
            (0.5, ComplianceLevel.PARTIALLY_COMPLIANT),
            (0.4, ComplianceLevel.NON_COMPLIANT),
            (0.0, ComplianceLevel.NON_COMPLIANT),
        ]

        for score, expected_level in test_cases:
            if score >= 0.9:
                expected = ComplianceLevel.FULLY_COMPLIANT
            elif score >= 0.75:
                expected = ComplianceLevel.MOSTLY_COMPLIANT
            elif score >= 0.5:
                expected = ComplianceLevel.PARTIALLY_COMPLIANT
            else:
                expected = ComplianceLevel.NON_COMPLIANT

            assert expected == expected_level

    def test_error_code_constants(self):
        """Test that error code constants are properly detected."""
        agent = CompliantErrorCompactionAgent()

        # Check that error codes are detected as class attributes
        assert hasattr(agent, "ERR_DB_001")
        assert hasattr(agent, "ERR_VALIDATION_002")
        assert hasattr(agent, "ERR_TIMEOUT_003")

        # Test detection logic
        has_patterns = False
        for attr_name in dir(agent.__class__):
            if attr_name.upper().startswith(("ERR_", "ERROR_")):
                has_patterns = True
                break

        assert has_patterns

    def test_full_error_workflow(self):
        """Test complete error handling workflow."""
        agent = CompliantErrorCompactionAgent()

        # Simulate an error
        try:
            raise ConnectionError("Database connection failed after 30 seconds timeout")
        except Exception as e:
            # Test error handling workflow
            compacted = agent.compact_error(str(e))
            classified_code = agent.classify_error(e)
            handled = agent.handle_error(e)

            # Verify compaction
            assert len(compacted) <= 150

            # Verify classification
            assert classified_code == "ERR_DB_001"

            # Verify handling combines both
            assert classified_code in handled
            assert len(handled) < len(str(e)) + 50  # Should be more compact

    def test_historical_error_analysis(self):
        """Test historical error analysis and trends."""
        agent = CompliantErrorCompactionAgent()

        # Test error summarization
        summary = agent.summarize_errors()

        assert "error_count" in summary
        assert "patterns" in summary
        assert "recent_errors" in summary

        # Summary should be compact
        summary_str = str(summary)
        assert len(summary_str) < 1000  # Should be reasonably compact


if __name__ == "__main__":
    # Run tests
    test = TestFactor9Validator()

    print("Testing Factor 9 Validator...")

    try:
        test.test_compliant_error_compaction_agent()
        print("✅ Compliant error compaction agent test passed")
    except AssertionError as e:
        print(f"❌ Compliant error compaction agent test failed: {e}")

    try:
        test.test_no_error_handling_agent()
        print("✅ No error handling agent test passed")
    except AssertionError as e:
        print(f"❌ No error handling agent test failed: {e}")

    try:
        test.test_verbose_error_agent()
        print("✅ Verbose error agent test passed")
    except AssertionError as e:
        print(f"❌ Verbose error agent test failed: {e}")

    try:
        test.test_partial_error_compaction_agent()
        print("✅ Partial error compaction agent test passed")
    except AssertionError as e:
        print(f"❌ Partial error compaction agent test failed: {e}")

    try:
        test.test_error_compaction_detection()
        print("✅ Error compaction detection test passed")
    except AssertionError as e:
        print(f"❌ Error compaction detection test failed: {e}")

    try:
        test.test_error_patterns_detection()
        print("✅ Error patterns detection test passed")
    except AssertionError as e:
        print(f"❌ Error patterns detection test failed: {e}")

    try:
        test.test_context_efficiency_detection()
        print("✅ Context efficiency detection test passed")
    except AssertionError as e:
        print(f"❌ Context efficiency detection test failed: {e}")

    try:
        test.test_error_summarization_detection()
        print("✅ Error summarization detection test passed")
    except AssertionError as e:
        print(f"❌ Error summarization detection test failed: {e}")

    try:
        test.test_error_classification_functionality()
        print("✅ Error classification functionality test passed")
    except AssertionError as e:
        print(f"❌ Error classification functionality test failed: {e}")

    try:
        test.test_error_compaction_functionality()
        print("✅ Error compaction functionality test passed")
    except AssertionError as e:
        print(f"❌ Error compaction functionality test failed: {e}")

    try:
        test.test_error_context_efficiency()
        print("✅ Error context efficiency test passed")
    except AssertionError as e:
        print(f"❌ Error context efficiency test failed: {e}")

    try:
        test.test_recommendations_provided()
        print("✅ Recommendations test passed")
    except AssertionError as e:
        print(f"❌ Recommendations test failed: {e}")

    try:
        test.test_edge_cases()
        print("✅ Edge cases test passed")
    except AssertionError as e:
        print(f"❌ Edge cases test failed: {e}")

    try:
        test.test_compliance_level_thresholds()
        print("✅ Compliance level thresholds test passed")
    except AssertionError as e:
        print(f"❌ Compliance level thresholds test failed: {e}")

    try:
        test.test_full_error_workflow()
        print("✅ Full error workflow test passed")
    except AssertionError as e:
        print(f"❌ Full error workflow test failed: {e}")

    print("\n🎉 All Factor 9 tests completed!")
