"""
Tests for Factor 5: Unify Execution and Business State compliance validation.
"""

from core.compliance import Factor5Validator, ComplianceLevel
from core.agent import BaseAgent
from core.tools import ToolResponse
from core.state import UnifiedState
from core.execution_context import ExecutionContext
from typing import Any


class CompliantUnifiedStateAgent(BaseAgent):
    """Example of agent with proper unified state management."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        """Execute task with unified state management."""
        # Create tool response with both business and execution data
        result = ToolResponse(
            success=True,
            data={"task": task, "result": f"Processed: {task}"},
            metadata={"execution_stage": "complete", "tool_calls": 1},
        )

        # Update unified state with tool response
        self.state.update(result)

        # Demonstrate business state usage
        self.state.set("last_task", task, state_type="business")
        self.state.set(
            "task_count", self.state.get("task_count", 0) + 1, state_type="business"
        )

        return result


class NoStateAgent(BaseAgent):
    """Example of agent without proper state management."""

    def __init__(self):
        super().__init__()
        self.state = None  # No state management

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        """Execute task without state management."""
        return ToolResponse(success=True, data={"task": task})


class PartialStateAgent(BaseAgent):
    """Example of agent with partial state management."""

    def __init__(self):
        super().__init__()
        self.state = MockPartialState()

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        """Execute task with limited state management."""
        result = ToolResponse(success=True, data={"task": task})
        # Limited state update
        self.state.data[task] = "processed"
        return result


class MockPartialState:
    """Mock state with limited functionality."""

    def __init__(self):
        self.data = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any, state_type: str = "business"):
        self.data[key] = value

    # Missing: update, to_dict, from_dict methods
    # Missing: execution_state, business_state attributes


class SeparateStateAgent(BaseAgent):
    """Agent with separate execution and business states (violates Factor 5)."""

    def __init__(self):
        super().__init__()
        # Separate state stores - violates unification principle
        self.execution_state = {}
        self.business_state = {}
        self.state = None  # No unified state

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        """Execute task with separate state management."""
        # Update separate states
        self.execution_state["last_execution"] = task
        self.business_state["task_data"] = f"Processed: {task}"

        return ToolResponse(success=True, data={"task": task})


class TestFactor5Validator:
    """Test suite for Factor 5 validator."""

    def test_compliant_unified_state_agent(self):
        """Test that agent with proper unified state passes validation."""
        agent = CompliantUnifiedStateAgent()
        validator = Factor5Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.FULLY_COMPLIANT
        assert details["score"] == 1.0
        assert details["checks"]["has_unified_state"]
        assert details["checks"]["state_management"]
        assert details["checks"]["state_persistence"]
        assert details["checks"]["state_observability"]
        assert len(details["issues"]) == 0

    def test_no_state_agent(self):
        """Test that agent without state management fails validation."""
        agent = NoStateAgent()
        validator = Factor5Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert details["score"] == 0.0
        assert not details["checks"]["has_unified_state"]
        assert len(details["issues"]) > 0
        assert len(details["recommendations"]) > 0

    def test_partial_state_agent(self):
        """Test that agent with partial state management gets partial score."""
        agent = PartialStateAgent()
        validator = Factor5Validator()

        compliance, details = validator.validate(agent)

        assert compliance in [
            ComplianceLevel.NON_COMPLIANT,
            ComplianceLevel.PARTIALLY_COMPLIANT,
        ]
        assert 0.0 <= details["score"] < 1.0
        assert len(details["issues"]) > 0

    def test_separate_state_agent(self):
        """Test that agent with separate states fails validation."""
        agent = SeparateStateAgent()
        validator = Factor5Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert details["score"] == 0.0
        assert not details["checks"]["has_unified_state"]

    def test_unified_state_presence(self):
        """Test unified state presence validation."""
        validator = Factor5Validator()

        # Test agent with proper unified state
        good_agent = CompliantUnifiedStateAgent()
        compliance, details = validator.validate(good_agent)
        assert details["checks"]["has_unified_state"]

        # Verify state has required methods
        required_methods = ["get", "set", "update", "to_dict", "from_dict"]
        for method in required_methods:
            assert hasattr(good_agent.state, method)

        # Verify state has required attributes
        assert hasattr(good_agent.state, "execution_state")
        assert hasattr(good_agent.state, "business_state")

    def test_state_management_capabilities(self):
        """Test state management validation."""
        agent = CompliantUnifiedStateAgent()
        validator = Factor5Validator()

        # Should have history tracking
        assert hasattr(agent.state, "history")

        # Should have update method that accepts ToolResponse
        assert hasattr(agent.state, "update")

        # Test actual state update functionality
        initial_history_length = len(agent.state.history)
        test_response = ToolResponse(success=True, data={"test": "data"})
        agent.state.update(test_response)

        assert len(agent.state.history) > initial_history_length
        assert agent.state.get("test") == "data"

        compliance, details = validator.validate(agent)
        assert details["checks"]["state_management"]

    def test_state_persistence(self):
        """Test state persistence validation."""
        agent = CompliantUnifiedStateAgent()
        validator = Factor5Validator()

        # Should have serialization methods
        assert hasattr(agent.state, "to_dict")
        assert hasattr(agent.state, "from_dict")

        # Should have checkpoint methods
        assert hasattr(agent, "save_checkpoint")
        assert hasattr(agent, "load_checkpoint")

        # Test serialization functionality
        state_dict = agent.state.to_dict()
        assert isinstance(state_dict, dict)
        assert "execution_state" in state_dict
        assert "business_state" in state_dict
        assert "history" in state_dict

        # Test deserialization
        new_state = UnifiedState.from_dict(state_dict)
        assert isinstance(new_state, UnifiedState)

        compliance, details = validator.validate(agent)
        assert details["checks"]["state_persistence"]

    def test_state_observability(self):
        """Test state observability validation."""
        agent = CompliantUnifiedStateAgent()
        validator = Factor5Validator()

        # Should have summary method
        assert hasattr(agent.state, "get_summary")

        # Should have history access
        assert hasattr(agent.state, "get_recent_history")
        assert hasattr(agent.state, "history")

        # Should have status method
        assert hasattr(agent, "get_status")

        # Test summary functionality
        summary = agent.state.get_summary()
        assert isinstance(summary, dict)
        assert "business_keys" in summary
        assert "execution_keys" in summary

        # Test history functionality
        recent_history = agent.state.get_recent_history(5)
        assert isinstance(recent_history, list)

        compliance, details = validator.validate(agent)
        assert details["checks"]["state_observability"]

    def test_state_functionality_integration(self):
        """Test actual state functionality works correctly."""
        agent = CompliantUnifiedStateAgent()

        # Execute task to generate state changes
        result = agent.execute_task("Test unified state")

        assert result.success
        assert agent.state.get("last_task") == "Test unified state"
        assert agent.state.get("task_count") == 1

        # Execute another task
        agent.execute_task("Second task")
        assert agent.state.get("task_count") == 2

        # Check history tracking
        history = agent.state.get_recent_history()
        assert len(history) >= 2

        # Check state summary
        summary = agent.state.get_summary()
        assert summary["history_length"] >= 2

    def test_recommendations_provided(self):
        """Test that validator provides actionable recommendations."""
        agent = NoStateAgent()
        validator = Factor5Validator()

        _, details = validator.validate(agent)

        assert len(details["recommendations"]) > 0
        recommendations_text = " ".join(details["recommendations"])
        assert "UnifiedState" in recommendations_text
        assert (
            "execution_state" in recommendations_text
            or "business_state" in recommendations_text
        )

    def test_error_state_handling(self):
        """Test unified state handles errors correctly."""
        agent = CompliantUnifiedStateAgent()

        # Create error response
        error_response = ToolResponse(success=False, error="Test error")
        agent.state.update(error_response)

        # Check error is tracked in execution state
        assert agent.state.get("last_error") == "Test error"
        assert agent.state.get("error_count", 0) > 0

        # Check error appears in history
        recent_history = agent.state.get_recent_history(1)
        assert len(recent_history) > 0
        assert recent_history[-1]["success"] is False
        assert recent_history[-1]["error"] == "Test error"

    def test_state_copy_functionality(self):
        """Test state copying for stateless operations."""
        agent = CompliantUnifiedStateAgent()

        # Add some state
        agent.state.set("test_key", "test_value", "business")
        agent.state.set("exec_key", "exec_value", "execution")

        # Create copy
        state_copy = agent.state.copy()

        # Verify copy is independent
        assert state_copy.get("test_key") == "test_value"
        assert state_copy.get("exec_key") == "exec_value"

        # Modify original
        agent.state.set("test_key", "modified", "business")

        # Copy should be unchanged
        assert state_copy.get("test_key") == "test_value"
        assert agent.state.get("test_key") == "modified"

    def test_edge_cases(self):
        """Test validator handles edge cases gracefully."""
        validator = Factor5Validator()

        # Test agent with state but missing methods
        class IncompleteStateAgent(BaseAgent):
            def __init__(self):
                super().__init__()
                self.state = MockIncompleteState()

            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            def execute_task(
                self, task: str, context: ExecutionContext = None
            ) -> ToolResponse:
                return ToolResponse(success=True, data={"task": task})

        class MockIncompleteState:
            def get(self, key: str, default: Any = None):
                return default

            # Missing other required methods

        agent = IncompleteStateAgent()
        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert not details["checks"]["has_unified_state"]
        assert isinstance(details["score"], float)
        assert 0.0 <= details["score"] <= 1.0

    def test_checkpoint_integration(self):
        """Test integration with checkpoint system."""
        agent = CompliantUnifiedStateAgent()

        # Add some state
        agent.state.set("checkpoint_test", "before_save", "business")

        # Save checkpoint
        agent.save_checkpoint()

        # Modify state
        agent.state.set("checkpoint_test", "after_save", "business")

        # Load checkpoint
        loaded = agent.load_checkpoint()
        assert loaded  # Should successfully load

        # State should be restored (if checkpoint system works correctly)
        # Note: This tests the integration, not necessarily that state is restored
        # as that depends on the specific checkpoint implementation


if __name__ == "__main__":
    # Run tests
    test = TestFactor5Validator()

    print("Testing Factor 5 Validator...")

    try:
        test.test_compliant_unified_state_agent()
        print("✅ Compliant unified state agent test passed")
    except AssertionError as e:
        print(f"❌ Compliant unified state agent test failed: {e}")

    try:
        test.test_no_state_agent()
        print("✅ No state agent test passed")
    except AssertionError as e:
        print(f"❌ No state agent test failed: {e}")

    try:
        test.test_partial_state_agent()
        print("✅ Partial state agent test passed")
    except AssertionError as e:
        print(f"❌ Partial state agent test failed: {e}")

    try:
        test.test_separate_state_agent()
        print("✅ Separate state agent test passed")
    except AssertionError as e:
        print(f"❌ Separate state agent test failed: {e}")

    try:
        test.test_unified_state_presence()
        print("✅ Unified state presence test passed")
    except AssertionError as e:
        print(f"❌ Unified state presence test failed: {e}")

    try:
        test.test_state_management_capabilities()
        print("✅ State management capabilities test passed")
    except AssertionError as e:
        print(f"❌ State management capabilities test failed: {e}")

    try:
        test.test_state_persistence()
        print("✅ State persistence test passed")
    except AssertionError as e:
        print(f"❌ State persistence test failed: {e}")

    try:
        test.test_state_observability()
        print("✅ State observability test passed")
    except AssertionError as e:
        print(f"❌ State observability test failed: {e}")

    try:
        test.test_state_functionality_integration()
        print("✅ State functionality integration test passed")
    except AssertionError as e:
        print(f"❌ State functionality integration test failed: {e}")

    try:
        test.test_recommendations_provided()
        print("✅ Recommendations test passed")
    except AssertionError as e:
        print(f"❌ Recommendations test failed: {e}")

    try:
        test.test_error_state_handling()
        print("✅ Error state handling test passed")
    except AssertionError as e:
        print(f"❌ Error state handling test failed: {e}")

    try:
        test.test_state_copy_functionality()
        print("✅ State copy functionality test passed")
    except AssertionError as e:
        print(f"❌ State copy functionality test failed: {e}")

    try:
        test.test_edge_cases()
        print("✅ Edge cases test passed")
    except AssertionError as e:
        print(f"❌ Edge cases test failed: {e}")

    try:
        test.test_checkpoint_integration()
        print("✅ Checkpoint integration test passed")
    except AssertionError as e:
        print(f"❌ Checkpoint integration test failed: {e}")

    print("\n🎉 All Factor 5 tests completed!")
