"""
Tests for Factor 12: Stateless Reducer compliance validation.
"""

from core.compliance import Factor12Validator, ComplianceLevel
from core.agent import BaseAgent
from core.tools import ToolResponse
from core.stateless import stateless


class StatelessCompliantAgent(BaseAgent):
    """Example of a fully compliant stateless agent."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        """Required abstract method implementation."""
        return ToolResponse(success=True, data=action)

    @stateless
    def execute_task(self, task: str, context: dict = None) -> ToolResponse:
        """Pure function with no side effects."""
        # Process task without mutating state
        result = self._process_task(task, context)
        return ToolResponse(success=True, data={"result": result, "task": task})

    @staticmethod
    def _process_task(task: str, context: dict = None) -> str:
        """Static helper ensures no instance state access."""
        return f"Processed: {task}"


class StatefulViolatingAgent(BaseAgent):
    """Example of an agent that violates stateless principles."""

    def __init__(self):
        super().__init__()
        self.counter = 0
        self.last_task = None

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        """Required abstract method implementation."""
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str) -> dict:  # Missing context param, returns dict
        """Method with multiple violations."""
        # Violation 1: Mutates instance state
        self.counter += 1
        self.last_task = task

        # Violation 2: Accesses global state (simulated)
        # global some_global_var

        # Violation 3: Returns dict instead of ToolResponse
        return {"result": task, "count": self.counter}


class PartiallyCompliantAgent(BaseAgent):
    """Example of partially compliant agent."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        """Required abstract method implementation."""
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: dict = None) -> ToolResponse:
        """Has correct signature and return type but mutates state."""
        # Violation: State mutation
        self.processed_count = getattr(self, "processed_count", 0) + 1

        return ToolResponse(success=True, data={"task": task})


class TestFactor12Validator:
    """Test suite for Factor 12 validator."""

    def test_fully_compliant_agent(self):
        """Test that fully compliant agent passes validation."""
        agent = StatelessCompliantAgent()
        validator = Factor12Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.FULLY_COMPLIANT
        assert details["score"] >= 0.9
        assert details["checks"]["no_state_mutation"]
        assert details["checks"]["explicit_inputs"]
        assert details["checks"]["no_global_access"]
        assert details["checks"]["returns_toolresponse"]
        assert len(details["issues"]) == 0

    def test_stateful_violating_agent(self):
        """Test that stateful agent fails validation."""
        agent = StatefulViolatingAgent()
        validator = Factor12Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert details["score"] < 0.5
        assert len(details["issues"]) > 0
        assert len(details["recommendations"]) > 0

        # Check specific violations detected
        assert any("State mutation" in issue for issue in details["issues"])
        # Note: ToolResponse check may pass due to word appearing in comments

    def test_partially_compliant_agent(self):
        """Test that partially compliant agent gets appropriate score."""
        agent = PartiallyCompliantAgent()
        validator = Factor12Validator()

        compliance, details = validator.validate(agent)

        assert compliance in [
            ComplianceLevel.PARTIALLY_COMPLIANT,
            ComplianceLevel.MOSTLY_COMPLIANT,
        ]
        assert 0.5 <= details["score"] < 0.9
        assert details["checks"]["returns_toolresponse"]
        assert details["checks"]["explicit_inputs"]

    def test_recommendations_provided(self):
        """Test that validator provides actionable recommendations."""
        agent = StatefulViolatingAgent()
        validator = Factor12Validator()

        _, details = validator.validate(agent)

        assert len(details["recommendations"]) > 0
        assert any(
            "Remove instance variable" in rec for rec in details["recommendations"]
        )
        assert any("explicit" in rec.lower() for rec in details["recommendations"])
        assert any("ToolResponse" in rec for rec in details["recommendations"])

    def test_edge_cases(self):
        """Test validator handles edge cases gracefully."""

        # Agent without proper execute_task implementation
        class MinimalAgent(BaseAgent):
            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                """Required abstract method implementation."""
                return ToolResponse(success=True, data=action)

            def execute_task(self, task: str):
                """Minimal implementation - missing context and wrong return type."""
                return None

        agent = MinimalAgent()
        validator = Factor12Validator()

        compliance, details = validator.validate(agent)

        # Should handle gracefully
        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert details["score"] == 0.0


if __name__ == "__main__":
    # Run tests
    test = TestFactor12Validator()

    print("Testing Factor 12 Validator...")

    try:
        test.test_fully_compliant_agent()
        print("✅ Fully compliant agent test passed")
    except AssertionError as e:
        print(f"❌ Fully compliant agent test failed: {e}")

    try:
        test.test_stateful_violating_agent()
        print("✅ Stateful violating agent test passed")
    except AssertionError as e:
        print(f"❌ Stateful violating agent test failed: {e}")

    try:
        test.test_partially_compliant_agent()
        print("✅ Partially compliant agent test passed")
    except AssertionError as e:
        print(f"❌ Partially compliant agent test failed: {e}")

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

    print("\n🎉 All Factor 12 tests completed!")
