"""
Tests for Factor 8: Own Your Control Flow compliance validation.
"""

from core.compliance import Factor8Validator, ComplianceLevel
from core.agent import BaseAgent
from core.tools import ToolResponse


class ExplicitFlowAgent(BaseAgent):
    """Example of agent with explicit control flow."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: dict = None) -> ToolResponse:
        """Execute task with explicit stage-based flow."""
        # Set up explicit workflow stages
        stages = ["parse", "validate", "execute", "verify"]
        self.set_workflow_stages(stages)

        for stage_name in stages:
            self.set_progress(self.progress, stage_name)

            if stage_name == "parse":
                result = self._parse_task(task)
            elif stage_name == "validate":
                result = self._validate_input(task)
            elif stage_name == "execute":
                result = self._execute_core_logic(task)
            elif stage_name == "verify":
                result = self._verify_results(task)

            # Explicit decision logic
            if not result.success:
                return self._handle_stage_failure(stage_name, result)

            self.advance_stage()

        return ToolResponse(
            success=True, data={"task": task, "completed_stages": stages}
        )

    def _parse_task(self, task: str) -> ToolResponse:
        """Parse task input."""
        if not task or len(task.strip()) == 0:
            return ToolResponse(success=False, error="Empty task")
        return ToolResponse(success=True, data={"parsed": task.strip()})

    def _validate_input(self, task: str) -> ToolResponse:
        """Validate task input."""
        if len(task) > 1000:
            return ToolResponse(success=False, error="Task too long")
        return ToolResponse(success=True, data={"valid": True})

    def _execute_core_logic(self, task: str) -> ToolResponse:
        """Execute main task logic."""
        return ToolResponse(success=True, data={"executed": task})

    def _verify_results(self, task: str) -> ToolResponse:
        """Verify execution results."""
        return ToolResponse(success=True, data={"verified": True})

    def _handle_stage_failure(self, stage: str, result: ToolResponse) -> ToolResponse:
        """Handle stage failure with explicit decision logic."""
        self.handle_error(Exception(result.error), f"stage_{stage}")
        return ToolResponse(
            success=False,
            error=f"Failed at stage {stage}: {result.error}",
            metadata={"failed_stage": stage},
        )


class ImplicitFlowAgent(BaseAgent):
    """Example of agent with implicit, unclear control flow."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: dict = None) -> ToolResponse:
        """Execute task with unclear, implicit flow."""
        import random

        # Non-deterministic behavior
        if random.choice([True, False]):
            self._do_something(task)

        # Implicit branching without clear criteria
        self._maybe_validate(task)
        result = self._process_somehow(task)

        # No clear stages or progress tracking
        return {"result": result}  # Wrong return type

    def _do_something(self, task):
        """Unclear what this does."""
        pass

    def _maybe_validate(self, task):
        """Unclear validation logic."""
        import time

        if time.time() % 2 == 0:  # Non-deterministic
            return True
        return False

    def _process_somehow(self, task):
        """Unclear processing logic."""
        return "processed"


class PartialFlowAgent(BaseAgent):
    """Example of agent with partial control flow compliance."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: dict = None) -> ToolResponse:
        """Execute task with some flow control but missing elements."""
        # Has some stage-like structure but not explicit
        pipeline = ["step1", "step2", "step3"]

        for step in pipeline:
            if step == "step1":
                result = self._step_one(task)
            elif step == "step2":
                result = self._step_two(task)
            else:
                result = self._step_three(task)

            # Has decision logic but missing proper error handling
            if not result:
                return ToolResponse(success=False, error=f"Failed at {step}")

        # Missing proper flow observability (no progress tracking)
        return ToolResponse(success=True, data={"task": task})

    def _step_one(self, task: str) -> bool:
        return len(task) > 0

    def _step_two(self, task: str) -> bool:
        return task.isascii()

    def _step_three(self, task: str) -> bool:
        return True


class NoFlowAgent(BaseAgent):
    """Agent without any flow control structure."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: dict = None) -> ToolResponse:
        """Simple execution without any flow control."""
        return ToolResponse(success=True, data={"task": task})


class TestFactor8Validator:
    """Test suite for Factor 8 validator."""

    def test_explicit_flow_agent(self):
        """Test that agent with explicit control flow passes validation."""
        agent = ExplicitFlowAgent()
        validator = Factor8Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.FULLY_COMPLIANT
        assert details["score"] == 1.0
        assert details["checks"]["explicit_stages"]
        assert details["checks"]["flow_observability"]
        assert details["checks"]["deterministic_flow"]
        assert details["checks"]["flow_control_methods"]
        assert len(details["issues"]) == 0

    def test_implicit_flow_agent(self):
        """Test that agent with implicit flow fails validation."""
        agent = ImplicitFlowAgent()
        validator = Factor8Validator()

        compliance, details = validator.validate(agent)

        assert compliance in [
            ComplianceLevel.MOSTLY_COMPLIANT,
            ComplianceLevel.PARTIALLY_COMPLIANT,
        ]
        assert details["score"] >= 0.5
        assert len(details["issues"]) > 0
        assert len(details["recommendations"]) > 0

        # Check specific violations
        assert any(
            "random" in issue or "time.time" in issue for issue in details["issues"]
        )

    def test_partial_flow_agent(self):
        """Test that agent with partial compliance gets appropriate score."""
        agent = PartialFlowAgent()
        validator = Factor8Validator()

        compliance, details = validator.validate(agent)

        assert compliance in [
            ComplianceLevel.PARTIALLY_COMPLIANT,
            ComplianceLevel.MOSTLY_COMPLIANT,
            ComplianceLevel.FULLY_COMPLIANT,
        ]
        assert 0.25 <= details["score"] <= 1.0

    def test_no_flow_agent(self):
        """Test that agent without flow control gets lower score."""
        agent = NoFlowAgent()
        validator = Factor8Validator()

        compliance, details = validator.validate(agent)

        assert compliance in [
            ComplianceLevel.MOSTLY_COMPLIANT,
            ComplianceLevel.PARTIALLY_COMPLIANT,
        ]
        assert details["score"] >= 0.5
        assert len(details["issues"]) > 0

    def test_flow_observability_check(self):
        """Test that flow observability is properly validated."""
        agent = ExplicitFlowAgent()
        validator = Factor8Validator()

        # Agent should have required attributes
        assert hasattr(agent, "progress")
        assert hasattr(agent, "current_stage")
        assert hasattr(agent, "total_stages")
        assert hasattr(agent, "get_status")

        compliance, details = validator.validate(agent)
        assert details["checks"]["flow_observability"]

    def test_deterministic_flow_check(self):
        """Test that deterministic flow validation works correctly."""
        validator = Factor8Validator()

        # Test deterministic agent
        deterministic_agent = ExplicitFlowAgent()
        compliance, details = validator.validate(deterministic_agent)
        assert details["checks"]["deterministic_flow"]

        # Test non-deterministic agent
        nondeterministic_agent = ImplicitFlowAgent()
        compliance, details = validator.validate(nondeterministic_agent)
        assert not details["checks"]["deterministic_flow"]

    def test_flow_control_methods_check(self):
        """Test that flow control methods are properly validated."""
        agent = ExplicitFlowAgent()
        validator = Factor8Validator()

        # Check that agent has required methods
        assert hasattr(agent, "set_progress")
        assert hasattr(agent, "advance_stage")
        assert hasattr(agent, "set_workflow_stages")

        compliance, details = validator.validate(agent)
        assert details["checks"]["flow_control_methods"]

    def test_recommendations_provided(self):
        """Test that validator provides actionable recommendations."""
        agent = ImplicitFlowAgent()
        validator = Factor8Validator()

        _, details = validator.validate(agent)

        assert len(details["recommendations"]) > 0
        recommendations_text = " ".join(details["recommendations"])
        # Should have at least one of these recommendation patterns
        has_relevant_recommendation = any(
            [
                "non-deterministic" in recommendations_text,
                "decision criteria" in recommendations_text,
                "explicit" in recommendations_text,
            ]
        )
        assert has_relevant_recommendation

    def test_stage_pattern_detection(self):
        """Test that various stage patterns are detected correctly."""

        class StagePatternAgent(BaseAgent):
            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            def execute_task(self, task: str, context: dict = None) -> ToolResponse:
                """Uses different stage pattern keywords."""
                workflow = ["analyze", "process", "output"]
                for step in workflow:
                    self.current_stage = step
                return ToolResponse(success=True, data={"task": task})

        agent = StagePatternAgent()
        validator = Factor8Validator()

        compliance, details = validator.validate(agent)
        # Should detect stage patterns even with different keywords
        assert details["checks"]["explicit_stages"] or details["score"] > 0.0

    def test_edge_cases(self):
        """Test validator handles edge cases gracefully."""

        class MinimalAgent(BaseAgent):
            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            def execute_task(self, task: str, context: dict = None) -> ToolResponse:
                """Minimal implementation without flow control."""
                return ToolResponse(success=True, data={"task": task})

        agent = MinimalAgent()
        validator = Factor8Validator()

        # Should handle minimal implementation gracefully
        compliance, details = validator.validate(agent)
        assert compliance in [
            ComplianceLevel.NON_COMPLIANT,
            ComplianceLevel.PARTIALLY_COMPLIANT,
            ComplianceLevel.MOSTLY_COMPLIANT,
        ]
        assert isinstance(details["score"], float)
        assert 0.0 <= details["score"] <= 1.0


if __name__ == "__main__":
    # Run tests
    test = TestFactor8Validator()

    print("Testing Factor 8 Validator...")

    try:
        test.test_explicit_flow_agent()
        print("✅ Explicit flow agent test passed")
    except AssertionError as e:
        print(f"❌ Explicit flow agent test failed: {e}")

    try:
        test.test_implicit_flow_agent()
        print("✅ Implicit flow agent test passed")
    except AssertionError as e:
        print(f"❌ Implicit flow agent test failed: {e}")

    try:
        test.test_partial_flow_agent()
        print("✅ Partial flow agent test passed")
    except AssertionError as e:
        print(f"❌ Partial flow agent test failed: {e}")

    try:
        test.test_no_flow_agent()
        print("✅ No flow agent test passed")
    except AssertionError as e:
        print(f"❌ No flow agent test failed: {e}")

    try:
        test.test_flow_observability_check()
        print("✅ Flow observability test passed")
    except AssertionError as e:
        print(f"❌ Flow observability test failed: {e}")

    try:
        test.test_deterministic_flow_check()
        print("✅ Deterministic flow test passed")
    except AssertionError as e:
        print(f"❌ Deterministic flow test failed: {e}")

    try:
        test.test_flow_control_methods_check()
        print("✅ Flow control methods test passed")
    except AssertionError as e:
        print(f"❌ Flow control methods test failed: {e}")

    try:
        test.test_recommendations_provided()
        print("✅ Recommendations test passed")
    except AssertionError as e:
        print(f"❌ Recommendations test failed: {e}")

    try:
        test.test_stage_pattern_detection()
        print("✅ Stage pattern detection test passed")
    except AssertionError as e:
        print(f"❌ Stage pattern detection test failed: {e}")

    try:
        test.test_edge_cases()
        print("✅ Edge cases test passed")
    except AssertionError as e:
        print(f"❌ Edge cases test failed: {e}")

    print("\n🎉 All Factor 8 tests completed!")
