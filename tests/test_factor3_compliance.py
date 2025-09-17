"""
Tests for Factor 3: Own Your Context Window compliance validation.
"""

from core.compliance import Factor3Validator, ComplianceLevel
from core.agent import BaseAgent
from core.tools import ToolResponse
from core.context import ContextManager
from core.execution_context import ExecutionContext


class CompliantContextAgent(BaseAgent):
    """Example of agent with proper context window management."""

    def __init__(self):
        super().__init__()
        # Override with proper context manager
        self.context_manager = ContextManager(max_tokens=100000)

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        """Execute task with proper context management."""
        # Add task to context with appropriate priority
        self.context_manager.add_context(f"Task: {task}", priority=8, source="task")

        # Use context in execution
        if context:
            self.context_manager.add_context(
                f"Execution context: {context.repo_name}",
                priority=6,
                source="execution",
            )

        # Build prompt respecting token limits
        self.context_manager.build_prompt()

        # Clean up old context periodically
        self.context_manager.remove_old_context()

        return ToolResponse(
            success=True,
            data={
                "task": task,
                "context_tokens": self.context_manager.get_token_usage()["total"],
            },
        )


class NoContextAgent(BaseAgent):
    """Example of agent without proper context management."""

    def __init__(self):
        # Call parent but override context_manager to None
        super().__init__()
        self.context_manager = None

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        """Execute task without context management."""
        # No context management at all
        return ToolResponse(success=True, data={"task": task})


class PartialContextAgent(BaseAgent):
    """Example of agent with partial context management."""

    def __init__(self):
        super().__init__()
        # Has context_manager but it's not fully featured
        self.context_manager = MockContextManager()

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        """Execute task with limited context management."""
        self.context_manager.add_content(task)  # Wrong method name
        return ToolResponse(success=True, data={"task": task})


class MockContextManager:
    """Mock context manager with limited functionality."""

    def __init__(self):
        self.content = []

    def add_content(self, content):
        """Wrong method name - should be add_context."""
        self.content.append(content)

    def build_prompt(self):
        """Has build_prompt but missing other features."""
        return "\n".join(self.content)


class BadLimitContextAgent(BaseAgent):
    """Agent with unreasonable context limits."""

    def __init__(self):
        super().__init__()
        # Unreasonable token limit
        self.context_manager = ContextManager(max_tokens=1000000)  # Too high

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})


class TestFactor3Validator:
    """Test suite for Factor 3 validator."""

    def test_compliant_context_agent(self):
        """Test that agent with proper context management passes validation."""
        agent = CompliantContextAgent()
        validator = Factor3Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.FULLY_COMPLIANT
        assert details["score"] == 1.0
        assert details["checks"]["has_context_manager"]
        assert details["checks"]["context_size_management"]
        assert details["checks"]["context_structure"]
        assert details["checks"]["context_optimization"]
        assert len(details["issues"]) == 0

    def test_no_context_agent(self):
        """Test that agent without context management fails validation."""
        agent = NoContextAgent()
        validator = Factor3Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert details["score"] == 0.0
        assert not details["checks"]["has_context_manager"]
        assert len(details["issues"]) > 0
        assert len(details["recommendations"]) > 0

    def test_partial_context_agent(self):
        """Test that agent with partial context management gets partial score."""
        agent = PartialContextAgent()
        validator = Factor3Validator()

        compliance, details = validator.validate(agent)

        assert compliance in [
            ComplianceLevel.NON_COMPLIANT,
            ComplianceLevel.PARTIALLY_COMPLIANT,
        ]
        assert 0.0 <= details["score"] < 1.0
        assert len(details["issues"]) > 0

    def test_bad_limit_context_agent(self):
        """Test that agent with bad limits gets penalized."""
        agent = BadLimitContextAgent()
        validator = Factor3Validator()

        compliance, details = validator.validate(agent)

        assert compliance in [
            ComplianceLevel.PARTIALLY_COMPLIANT,
            ComplianceLevel.MOSTLY_COMPLIANT,
        ]
        assert details["checks"]["has_context_manager"]
        assert not details["checks"][
            "context_size_management"
        ]  # Should fail due to bad limit

    def test_context_manager_presence(self):
        """Test context manager presence validation."""
        validator = Factor3Validator()

        # Test agent with proper context manager
        good_agent = CompliantContextAgent()
        compliance, details = validator.validate(good_agent)
        assert details["checks"]["has_context_manager"]

        # Test agent without context manager
        bad_agent = NoContextAgent()
        compliance, details = validator.validate(bad_agent)
        assert not details["checks"]["has_context_manager"]

    def test_context_size_management(self):
        """Test context size management validation."""
        agent = CompliantContextAgent()
        validator = Factor3Validator()

        # Should have proper token limits and usage tracking
        assert hasattr(agent.context_manager, "max_tokens")
        assert hasattr(agent.context_manager, "get_token_usage")

        # Test token usage method
        usage = agent.context_manager.get_token_usage()
        assert isinstance(usage, dict)
        assert "total" in usage
        assert "max" in usage
        assert "available" in usage

        compliance, details = validator.validate(agent)
        assert details["checks"]["context_size_management"]

    def test_context_structure(self):
        """Test context structure validation."""
        agent = CompliantContextAgent()
        validator = Factor3Validator()

        # Should have priority-based context management
        import inspect

        sig = inspect.signature(agent.context_manager.add_context)
        assert "priority" in sig.parameters

        # Should support ExecutionContext
        assert hasattr(agent, "context")

        compliance, details = validator.validate(agent)
        assert details["checks"]["context_structure"]

    def test_context_optimization(self):
        """Test context optimization validation."""
        agent = CompliantContextAgent()
        validator = Factor3Validator()

        # Should have optimization methods
        optimization_methods = ["clear", "remove_old_context", "compact_errors"]
        found_methods = []
        for method in optimization_methods:
            if hasattr(agent.context_manager, method):
                found_methods.append(method)

        assert len(found_methods) >= 2  # Should have at least 2 optimization methods

        compliance, details = validator.validate(agent)
        assert details["checks"]["context_optimization"]

    def test_context_functionality(self):
        """Test actual context functionality works correctly."""
        agent = CompliantContextAgent()

        # Test adding context with priority
        agent.context_manager.add_context("High priority", priority=9)
        agent.context_manager.add_context("Low priority", priority=2)

        # Test building prompt
        prompt = agent.context_manager.build_prompt()
        assert "High priority" in prompt
        assert "Low priority" in prompt

        # Test token usage
        usage = agent.context_manager.get_token_usage()
        assert usage["total"] > 0

        # Test context cleanup
        agent.context_manager.remove_old_context(keep_recent=1)
        # Should clean up some items (exact behavior depends on priorities)

    def test_recommendations_provided(self):
        """Test that validator provides actionable recommendations."""
        agent = NoContextAgent()
        validator = Factor3Validator()

        _, details = validator.validate(agent)

        assert len(details["recommendations"]) > 0
        recommendations_text = " ".join(details["recommendations"])
        assert "ContextManager" in recommendations_text
        assert "context_manager" in recommendations_text

    def test_execution_context_integration(self):
        """Test integration with ExecutionContext."""
        agent = CompliantContextAgent()

        # Create execution context
        exec_context = ExecutionContext(repo_name="test-repo", issue_number=123)

        # Execute task with context
        result = agent.execute_task("Test task", context=exec_context)

        assert result.success
        assert "context_tokens" in result.data
        assert result.data["context_tokens"] > 0

    def test_edge_cases(self):
        """Test validator handles edge cases gracefully."""
        validator = Factor3Validator()

        # Test agent with context_manager but it's None
        class NullContextAgent(BaseAgent):
            def __init__(self):
                super().__init__()
                self.context_manager = None

            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            def execute_task(
                self, task: str, context: ExecutionContext = None
            ) -> ToolResponse:
                return ToolResponse(success=True, data={"task": task})

        agent = NullContextAgent()
        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert not details["checks"]["has_context_manager"]
        assert isinstance(details["score"], float)
        assert 0.0 <= details["score"] <= 1.0

    def test_token_limits_validation(self):
        """Test various token limit scenarios."""
        validator = Factor3Validator()

        # Test reasonable limit
        class ReasonableLimitAgent(BaseAgent):
            def __init__(self):
                super().__init__()
                self.context_manager = ContextManager(max_tokens=50000)  # Reasonable

            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            def execute_task(
                self, task: str, context: ExecutionContext = None
            ) -> ToolResponse:
                return ToolResponse(success=True, data={"task": task})

        agent = ReasonableLimitAgent()
        compliance, details = validator.validate(agent)
        assert details["checks"]["context_size_management"]

        # Test zero limit
        class ZeroLimitAgent(BaseAgent):
            def __init__(self):
                super().__init__()
                self.context_manager = ContextManager(max_tokens=0)  # Bad

            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            def execute_task(
                self, task: str, context: ExecutionContext = None
            ) -> ToolResponse:
                return ToolResponse(success=True, data={"task": task})

        agent = ZeroLimitAgent()
        compliance, details = validator.validate(agent)
        assert not details["checks"]["context_size_management"]


if __name__ == "__main__":
    # Run tests
    test = TestFactor3Validator()

    print("Testing Factor 3 Validator...")

    try:
        test.test_compliant_context_agent()
        print("✅ Compliant context agent test passed")
    except AssertionError as e:
        print(f"❌ Compliant context agent test failed: {e}")

    try:
        test.test_no_context_agent()
        print("✅ No context agent test passed")
    except AssertionError as e:
        print(f"❌ No context agent test failed: {e}")

    try:
        test.test_partial_context_agent()
        print("✅ Partial context agent test passed")
    except AssertionError as e:
        print(f"❌ Partial context agent test failed: {e}")

    try:
        test.test_bad_limit_context_agent()
        print("✅ Bad limit context agent test passed")
    except AssertionError as e:
        print(f"❌ Bad limit context agent test failed: {e}")

    try:
        test.test_context_manager_presence()
        print("✅ Context manager presence test passed")
    except AssertionError as e:
        print(f"❌ Context manager presence test failed: {e}")

    try:
        test.test_context_size_management()
        print("✅ Context size management test passed")
    except AssertionError as e:
        print(f"❌ Context size management test failed: {e}")

    try:
        test.test_context_structure()
        print("✅ Context structure test passed")
    except AssertionError as e:
        print(f"❌ Context structure test failed: {e}")

    try:
        test.test_context_optimization()
        print("✅ Context optimization test passed")
    except AssertionError as e:
        print(f"❌ Context optimization test failed: {e}")

    try:
        test.test_context_functionality()
        print("✅ Context functionality test passed")
    except AssertionError as e:
        print(f"❌ Context functionality test failed: {e}")

    try:
        test.test_recommendations_provided()
        print("✅ Recommendations test passed")
    except AssertionError as e:
        print(f"❌ Recommendations test failed: {e}")

    try:
        test.test_execution_context_integration()
        print("✅ ExecutionContext integration test passed")
    except AssertionError as e:
        print(f"❌ ExecutionContext integration test failed: {e}")

    try:
        test.test_edge_cases()
        print("✅ Edge cases test passed")
    except AssertionError as e:
        print(f"❌ Edge cases test failed: {e}")

    try:
        test.test_token_limits_validation()
        print("✅ Token limits validation test passed")
    except AssertionError as e:
        print(f"❌ Token limits validation test failed: {e}")

    print("\n🎉 All Factor 3 tests completed!")
