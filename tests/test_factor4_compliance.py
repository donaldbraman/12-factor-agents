"""
Tests for Factor 4: Tools are Structured Outputs compliance validation.
"""

from core.compliance import Factor4Validator, ComplianceLevel
from core.agent import BaseAgent
from core.tools import Tool, ToolResponse
from typing import Dict, Any


class CompliantTool(Tool):
    """Example of a fully compliant tool with structured outputs."""

    def __init__(self):
        super().__init__(
            name="compliant_tool",
            description="A tool that demonstrates proper structured output compliance",
        )

    def execute(self, operation: str, data: str = None) -> ToolResponse:
        """Execute tool operation with proper error handling and ToolResponse."""
        try:
            if operation == "process":
                result = f"Processed: {data}"
                return ToolResponse(
                    success=True, data={"operation": operation, "result": result}
                )
            elif operation == "validate":
                is_valid = data is not None and len(data) > 0
                return ToolResponse(
                    success=True, data={"operation": operation, "valid": is_valid}
                )
            else:
                return ToolResponse(
                    success=False, error=f"Unknown operation: {operation}"
                )
        except Exception as e:
            return ToolResponse(success=False, error=f"Tool execution error: {str(e)}")

    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return proper JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["process", "validate"],
                    "description": "Operation to perform",
                },
                "data": {
                    "type": "string",
                    "description": "Data to process or validate",
                },
            },
            "required": ["operation"],
        }


class ViolatingTool:
    """Example of a tool that violates structured output principles."""

    def __init__(self):
        self.name = "violating_tool"
        # Missing description

    def execute(self, data):
        """Method without proper error handling or ToolResponse."""
        # No try/catch block
        # Returns inconsistent types
        if data:
            return {"result": data}
        else:
            return None  # Inconsistent return type

    # Missing get_parameters_schema method


class PartiallyCompliantTool(Tool):
    """Example of a tool that is partially compliant."""

    def __init__(self):
        super().__init__(
            name="partial_tool", description="Tool with some compliance issues"
        )

    def execute(self, operation: str) -> ToolResponse:
        # Has error handling but not comprehensive
        if operation == "test":
            return ToolResponse(success=True, data={"result": "ok"})
        # Missing comprehensive error handling for invalid operations
        return {"error": "unknown"}  # Wrong return type for errors

    def get_parameters_schema(self) -> Dict[str, Any]:
        """Schema is present but minimal."""
        return {"type": "object", "properties": {"operation": {"type": "string"}}}


class CompliantToolAgent(BaseAgent):
    """Agent with fully compliant tools."""

    def register_tools(self):
        return [CompliantTool()]

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: dict = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})


class ViolatingToolAgent(BaseAgent):
    """Agent with non-compliant tools."""

    def register_tools(self):
        return [ViolatingTool()]

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: dict = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})


class PartiallyCompliantAgent(BaseAgent):
    """Agent with mixed compliance tools."""

    def register_tools(self):
        return [CompliantTool(), PartiallyCompliantTool()]

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: dict = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})


class NoToolsAgent(BaseAgent):
    """Agent with no tools - edge case."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: dict = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})


class TestFactor4Validator:
    """Test suite for Factor 4 validator."""

    def test_fully_compliant_agent(self):
        """Test that agent with fully compliant tools passes validation."""
        agent = CompliantToolAgent()
        validator = Factor4Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.FULLY_COMPLIANT
        assert details["score"] == 1.0
        assert details["checks"]["tools_return_toolresponse"]
        assert details["checks"]["schema_compliance"]
        assert details["checks"]["error_handling"]
        assert details["checks"]["output_documentation"]
        assert len(details["issues"]) == 0

    def test_violating_agent(self):
        """Test that agent with non-compliant tools fails validation."""
        agent = ViolatingToolAgent()
        validator = Factor4Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert details["score"] < 0.5
        assert len(details["issues"]) > 0
        assert len(details["recommendations"]) > 0

        # Should detect multiple violations
        issues_text = " ".join(details["issues"])
        assert "does not inherit from Tool base class" in issues_text

    def test_partially_compliant_agent(self):
        """Test that agent with mixed compliance gets appropriate score."""
        agent = PartiallyCompliantAgent()
        validator = Factor4Validator()

        compliance, details = validator.validate(agent)

        assert compliance in [
            ComplianceLevel.PARTIALLY_COMPLIANT,
            ComplianceLevel.MOSTLY_COMPLIANT,
        ]
        assert 0.5 <= details["score"] < 1.0

    def test_no_tools_agent(self):
        """Test that agent with no tools is handled gracefully."""
        agent = NoToolsAgent()
        validator = Factor4Validator()

        compliance, details = validator.validate(agent)

        # No tools means all checks pass (no violations found)
        assert compliance == ComplianceLevel.FULLY_COMPLIANT
        assert details["score"] == 1.0
        assert details["checks"]["tools_return_toolresponse"]
        assert details["checks"]["schema_compliance"]
        assert details["checks"]["error_handling"]
        assert details["checks"]["output_documentation"]

    def test_recommendations_provided(self):
        """Test that validator provides actionable recommendations."""
        agent = ViolatingToolAgent()
        validator = Factor4Validator()

        _, details = validator.validate(agent)

        assert len(details["recommendations"]) > 0
        recommendations_text = " ".join(details["recommendations"])
        assert "Tool base class" in recommendations_text
        assert "get_parameters_schema" in recommendations_text
        assert "try/catch" in recommendations_text
        assert "docstring" in recommendations_text

    def test_individual_checks(self):
        """Test individual validation checks work correctly."""
        validator = Factor4Validator()

        # Test tool response check
        agent = CompliantToolAgent()
        _, details = validator.validate(agent)
        assert details["checks"]["tools_return_toolresponse"]

        # Test schema compliance check
        tool = CompliantTool()
        schema = tool.get_parameters_schema()
        assert isinstance(schema, dict)
        assert "type" in schema
        assert "properties" in schema

        # Test error handling patterns
        tool_response = tool.execute("invalid_operation")
        assert isinstance(tool_response, ToolResponse)
        assert not tool_response.success
        assert tool_response.error is not None

    def test_edge_cases(self):
        """Test validator handles edge cases gracefully."""
        validator = Factor4Validator()

        # Test with agent that has tools but can't analyze source
        class EdgeCaseAgent(BaseAgent):
            def register_tools(self):
                # Return a tool with no source code available
                tool = CompliantTool()
                # Simulate inability to get source
                return [tool]

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            def execute_task(self, task: str, context: dict = None) -> ToolResponse:
                return ToolResponse(success=True, data={"task": task})

        agent = EdgeCaseAgent()
        compliance, details = validator.validate(agent)

        # Should handle gracefully and still provide useful results
        assert compliance is not None
        assert isinstance(details["score"], float)
        assert 0.0 <= details["score"] <= 1.0


if __name__ == "__main__":
    # Run tests
    test = TestFactor4Validator()

    print("Testing Factor 4 Validator...")

    try:
        test.test_fully_compliant_agent()
        print("✅ Fully compliant agent test passed")
    except AssertionError as e:
        print(f"❌ Fully compliant agent test failed: {e}")

    try:
        test.test_violating_agent()
        print("✅ Violating agent test passed")
    except AssertionError as e:
        print(f"❌ Violating agent test failed: {e}")

    try:
        test.test_partially_compliant_agent()
        print("✅ Partially compliant agent test passed")
    except AssertionError as e:
        print(f"❌ Partially compliant agent test failed: {e}")

    try:
        test.test_no_tools_agent()
        print("✅ No tools agent test passed")
    except AssertionError as e:
        print(f"❌ No tools agent test failed: {e}")

    try:
        test.test_recommendations_provided()
        print("✅ Recommendations test passed")
    except AssertionError as e:
        print(f"❌ Recommendations test failed: {e}")

    try:
        test.test_individual_checks()
        print("✅ Individual checks test passed")
    except AssertionError as e:
        print(f"❌ Individual checks test failed: {e}")

    try:
        test.test_edge_cases()
        print("✅ Edge cases test passed")
    except AssertionError as e:
        print(f"❌ Edge cases test failed: {e}")

    print("\n🎉 All Factor 4 tests completed!")
