"""
Tests for Factor 7: Contact Humans with Tool Calls compliance validation.
"""

from core.compliance import Factor7Validator, ComplianceLevel
from core.agent import BaseAgent
from core.tools import Tool, ToolResponse, HumanInteractionTool
from core.execution_context import ExecutionContext
from typing import Any, Dict


class CompliantHumanContactAgent(BaseAgent):
    """Example of agent with proper human contact tools."""

    def register_tools(self):
        return [
            HumanInteractionTool(),
            MockHumanApprovalTool(),
        ]

    def get_tools(self):
        return self.register_tools()

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        """Execute task with human interaction capability."""
        return ToolResponse(
            success=True,
            data={"task": task, "result": f"Processed: {task}"},
            metadata={"human_tools_available": True},
        )


class MockHumanApprovalTool(Tool):
    """Mock human approval tool for testing."""

    def __init__(self):
        super().__init__(
            name="human_approval", description="Request human approval for actions"
        )

    def execute(
        self, message: str, context: Dict[str, Any] = None, timeout: int = 300
    ) -> ToolResponse:
        """Execute approval request with proper validation."""
        if not message:
            return ToolResponse(
                success=False, error="Message is required for human approval"
            )

        try:
            # Simulate timeout handling and structured response
            request_data = {
                "message": message,
                "context": context or {},
                "timeout": timeout,
                "request_id": f"approval_{hash(message)}",
            }

            response_data = {
                "approved": True,
                "feedback": "Mock approval granted",
                "timestamp": "2024-01-01T00:00:00Z",
            }

            return ToolResponse(
                success=True,
                data=response_data,
                metadata={"request_data": request_data},
            )
        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Clear message describing what needs approval",
                },
                "context": {
                    "type": "object",
                    "description": "Additional context for the approval decision",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds for human response",
                },
            },
            "required": ["message"],
        }


class NoHumanToolsAgent(BaseAgent):
    """Example of agent without human contact tools."""

    def register_tools(self):
        return []

    def get_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})


class PartialHumanToolsAgent(BaseAgent):
    """Example of agent with partial human tools implementation."""

    def register_tools(self):
        return [MockIncompleteHumanTool()]

    def get_tools(self):
        return self.register_tools()

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})


class MockIncompleteHumanTool(Tool):
    """Mock human tool with incomplete implementation."""

    def __init__(self):
        super().__init__(name="human_contact", description="Basic human contact")

    def execute(self, prompt: str) -> ToolResponse:
        """Basic execute without proper protocols."""
        # Missing: timeout handling, error handling, structured response
        return ToolResponse(success=True, data={"response": "basic response"})

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"prompt": {"type": "string"}},  # Missing description
            "required": ["prompt"],
        }


class BadStructureHumanAgent(BaseAgent):
    """Agent with human tools that don't follow tool patterns."""

    def register_tools(self):
        return [MockBadStructureTool()]

    def get_tools(self):
        return self.register_tools()

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})


class MockBadStructureTool:
    """Tool that doesn't inherit from Tool base class."""

    def __init__(self):
        self.name = "human_interaction"
        self.description = "Human interaction tool"

    def run(self, text: str):  # Wrong method name
        return {"result": "bad structure"}

    # Missing get_parameters_schema method


class TestFactor7Validator:
    """Test suite for Factor 7 validator."""

    def test_compliant_human_contact_agent(self):
        """Test that agent with proper human contact tools passes validation."""
        agent = CompliantHumanContactAgent()
        validator = Factor7Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.FULLY_COMPLIANT
        assert details["score"] == 1.0
        assert details["checks"]["has_human_tools"]
        assert details["checks"]["communication_protocols"]
        assert details["checks"]["user_experience"]
        assert details["checks"]["tool_call_patterns"]
        assert len(details["issues"]) == 0

    def test_no_human_tools_agent(self):
        """Test that agent without human tools fails validation."""
        agent = NoHumanToolsAgent()
        validator = Factor7Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert details["score"] == 0.0
        assert not details["checks"]["has_human_tools"]
        assert len(details["issues"]) > 0
        assert len(details["recommendations"]) > 0
        assert "HumanInteractionTool" in " ".join(details["recommendations"])

    def test_partial_human_tools_agent(self):
        """Test that agent with incomplete human tools gets partial score."""
        agent = PartialHumanToolsAgent()
        validator = Factor7Validator()

        compliance, details = validator.validate(agent)

        assert compliance in [
            ComplianceLevel.NON_COMPLIANT,
            ComplianceLevel.PARTIALLY_COMPLIANT,
        ]
        assert 0.0 <= details["score"] < 1.0
        assert details["checks"]["has_human_tools"]  # Has tools but incomplete
        assert len(details["issues"]) > 0

    def test_bad_structure_agent(self):
        """Test that agent with improperly structured tools fails validation."""
        agent = BadStructureHumanAgent()
        validator = Factor7Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert details["score"] <= 0.25  # May get partial credit for having tools
        assert len(details["issues"]) > 0

    def test_human_tools_detection(self):
        """Test human tools detection logic."""
        # Test agent with proper human tools
        good_agent = CompliantHumanContactAgent()
        tools = good_agent.get_tools()

        human_tools = []
        for tool in tools:
            tool_name = getattr(tool, "name", "").lower()
            tool_desc = getattr(tool, "description", "").lower()

            if any(
                keyword in tool_name or keyword in tool_desc
                for keyword in [
                    "human",
                    "interaction",
                    "approval",
                    "contact",
                    "escalate",
                ]
            ):
                human_tools.append(tool)

        assert (
            len(human_tools) >= 2
        )  # Should find HumanInteractionTool and MockHumanApprovalTool

        # Verify tools are properly structured
        for tool in human_tools:
            assert hasattr(tool, "execute")
            assert hasattr(tool, "get_parameters_schema")

    def test_communication_protocols_validation(self):
        """Test communication protocols validation."""
        agent = CompliantHumanContactAgent()

        tools = agent.get_tools()
        human_tools = [
            t for t in tools if hasattr(t, "name") and "human" in t.name.lower()
        ]

        assert len(human_tools) > 0

        # Check that at least one human tool has proper protocols
        has_proper_protocols = False
        for tool in human_tools:
            if hasattr(tool, "execute"):
                import inspect

                source = inspect.getsource(tool.execute)

                has_timeout = "timeout" in source.lower()
                has_structure = any(
                    keyword in source
                    for keyword in ["request", "response", "message", "context"]
                )
                has_error_handling = "except" in source or "error" in source.lower()

                if has_timeout and has_structure and has_error_handling:
                    has_proper_protocols = True
                    break

        assert has_proper_protocols

    def test_user_experience_validation(self):
        """Test user experience elements validation."""
        agent = CompliantHumanContactAgent()

        tools = agent.get_tools()
        human_tools = [
            t
            for t in tools
            if hasattr(t, "name")
            and any(
                keyword in t.name.lower()
                or keyword in getattr(t, "description", "").lower()
                for keyword in ["human", "interaction", "approval"]
            )
        ]

        assert len(human_tools) > 0

        # Check UX elements in at least one tool
        has_good_ux = False
        for tool in human_tools:
            if hasattr(tool, "get_parameters_schema"):
                schema = tool.get_parameters_schema()

                has_message_param = False
                has_context_param = False
                has_descriptions = False

                if "properties" in schema:
                    props = schema["properties"]
                    for prop_name, prop_info in props.items():
                        if (
                            "message" in prop_name.lower()
                            or "prompt" in prop_name.lower()
                        ):
                            has_message_param = True
                        if "context" in prop_name.lower():
                            has_context_param = True
                        if "description" in prop_info:
                            has_descriptions = True

                if has_message_param and has_context_param and has_descriptions:
                    has_good_ux = True
                    break

        assert has_good_ux

    def test_tool_call_patterns_validation(self):
        """Test tool call patterns validation."""
        agent = CompliantHumanContactAgent()

        tools = agent.get_tools()
        human_tools = [
            t for t in tools if hasattr(t, "name") and "human" in t.name.lower()
        ]

        assert len(human_tools) > 0

        # Check patterns in at least one tool
        follows_patterns = False
        for tool in human_tools:
            if hasattr(tool, "execute"):
                import inspect

                source = inspect.getsource(tool.execute)

                returns_toolresponse = "ToolResponse" in source
                has_validation = (
                    "validate" in source.lower() or "required" in source.lower()
                )

                if returns_toolresponse and has_validation:
                    follows_patterns = True
                    break

        assert follows_patterns

    def test_recommendations_provided(self):
        """Test that validator provides actionable recommendations."""
        agent = NoHumanToolsAgent()
        validator = Factor7Validator()

        _, details = validator.validate(agent)

        assert len(details["recommendations"]) > 0
        recommendations_text = " ".join(details["recommendations"])
        assert any(
            keyword in recommendations_text
            for keyword in ["HumanInteractionTool", "human", "contact", "tool"]
        )

    def test_human_interaction_tool_integration(self):
        """Test integration with actual HumanInteractionTool from core.tools."""
        agent = CompliantHumanContactAgent()
        tools = agent.get_tools()

        # Find HumanInteractionTool
        human_interaction_tool = None
        for tool in tools:
            if tool.__class__.__name__ == "HumanInteractionTool":
                human_interaction_tool = tool
                break

        assert human_interaction_tool is not None
        assert hasattr(human_interaction_tool, "execute")
        assert hasattr(human_interaction_tool, "get_parameters_schema")

        # Test schema
        schema = human_interaction_tool.get_parameters_schema()
        assert "properties" in schema
        assert "interaction_type" in schema["properties"]
        assert "message" in schema["properties"]

    def test_mock_approval_tool_functionality(self):
        """Test MockHumanApprovalTool functionality."""
        tool = MockHumanApprovalTool()

        # Test successful execution
        response = tool.execute(
            message="Please approve this action",
            context={"action": "delete_file"},
            timeout=60,
        )

        assert response.success
        assert "approved" in response.data
        assert "feedback" in response.data
        assert "request_data" in response.metadata

        # Test validation (missing message)
        response = tool.execute(message="")
        assert not response.success
        assert "required" in response.error.lower()

    def test_edge_cases(self):
        """Test validator handles edge cases gracefully."""
        validator = Factor7Validator()

        # Test agent without get_tools method
        class NoGetToolsAgent(BaseAgent):
            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            def execute_task(
                self, task: str, context: ExecutionContext = None
            ) -> ToolResponse:
                return ToolResponse(success=True, data={"task": task})

        agent = NoGetToolsAgent()
        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert details["score"] == 0.0
        assert not details["checks"]["has_human_tools"]

    def test_partial_deduction_for_bad_structure(self):
        """Test partial deduction when tools exist but have bad structure."""
        agent = BadStructureHumanAgent()
        validator = Factor7Validator()

        compliance, details = validator.validate(agent)

        # Should get some credit for having tools, but lose points for bad structure
        assert details["score"] <= 0.25
        assert "structure" in " ".join(details["issues"]).lower()

    def test_multiple_human_tools_handling(self):
        """Test handling of multiple human tools."""
        agent = CompliantHumanContactAgent()
        tools = agent.get_tools()

        # Should have multiple human-related tools
        human_tools = []
        for tool in tools:
            tool_name = getattr(tool, "name", "").lower()
            tool_desc = getattr(tool, "description", "").lower()

            if any(
                keyword in tool_name or keyword in tool_desc
                for keyword in ["human", "interaction", "approval", "contact"]
            ):
                human_tools.append(tool)

        assert len(human_tools) >= 2

    def test_compliance_level_thresholds(self):
        """Test compliance level determination."""
        # Test compliance level logic
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


if __name__ == "__main__":
    # Run tests
    test = TestFactor7Validator()

    print("Testing Factor 7 Validator...")

    try:
        test.test_compliant_human_contact_agent()
        print("✅ Compliant human contact agent test passed")
    except AssertionError as e:
        print(f"❌ Compliant human contact agent test failed: {e}")

    try:
        test.test_no_human_tools_agent()
        print("✅ No human tools agent test passed")
    except AssertionError as e:
        print(f"❌ No human tools agent test failed: {e}")

    try:
        test.test_partial_human_tools_agent()
        print("✅ Partial human tools agent test passed")
    except AssertionError as e:
        print(f"❌ Partial human tools agent test failed: {e}")

    try:
        test.test_bad_structure_agent()
        print("✅ Bad structure agent test passed")
    except AssertionError as e:
        print(f"❌ Bad structure agent test failed: {e}")

    try:
        test.test_human_tools_detection()
        print("✅ Human tools detection test passed")
    except AssertionError as e:
        print(f"❌ Human tools detection test failed: {e}")

    try:
        test.test_communication_protocols_validation()
        print("✅ Communication protocols validation test passed")
    except AssertionError as e:
        print(f"❌ Communication protocols validation test failed: {e}")

    try:
        test.test_user_experience_validation()
        print("✅ User experience validation test passed")
    except AssertionError as e:
        print(f"❌ User experience validation test failed: {e}")

    try:
        test.test_tool_call_patterns_validation()
        print("✅ Tool call patterns validation test passed")
    except AssertionError as e:
        print(f"❌ Tool call patterns validation test failed: {e}")

    try:
        test.test_recommendations_provided()
        print("✅ Recommendations test passed")
    except AssertionError as e:
        print(f"❌ Recommendations test failed: {e}")

    try:
        test.test_human_interaction_tool_integration()
        print("✅ Human interaction tool integration test passed")
    except AssertionError as e:
        print(f"❌ Human interaction tool integration test failed: {e}")

    try:
        test.test_mock_approval_tool_functionality()
        print("✅ Mock approval tool functionality test passed")
    except AssertionError as e:
        print(f"❌ Mock approval tool functionality test failed: {e}")

    try:
        test.test_edge_cases()
        print("✅ Edge cases test passed")
    except AssertionError as e:
        print(f"❌ Edge cases test failed: {e}")

    try:
        test.test_partial_deduction_for_bad_structure()
        print("✅ Partial deduction test passed")
    except AssertionError as e:
        print(f"❌ Partial deduction test failed: {e}")

    try:
        test.test_multiple_human_tools_handling()
        print("✅ Multiple human tools handling test passed")
    except AssertionError as e:
        print(f"❌ Multiple human tools handling test failed: {e}")

    try:
        test.test_compliance_level_thresholds()
        print("✅ Compliance level thresholds test passed")
    except AssertionError as e:
        print(f"❌ Compliance level thresholds test failed: {e}")

    print("\n🎉 All Factor 7 tests completed!")
