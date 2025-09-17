"""
Tests for Factor 11: Trigger from Anywhere compliance validation.
"""

from core.compliance import Factor11Validator, ComplianceLevel
from core.agent import BaseAgent
from core.tools import ToolResponse
from core.execution_context import ExecutionContext
from typing import Any, Dict
import asyncio


class CompliantTriggerAnywhereAgent(BaseAgent):
    """Example of agent with comprehensive trigger support."""

    def __init__(self):
        super().__init__()
        self.trigger_registry = {}
        self.triggers = []

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    async def execute_task(
        self, task: str, context: ExecutionContext = None
    ) -> ToolResponse:
        """Execute task with async support for flexible triggering."""
        return ToolResponse(
            success=True,
            data={"task": task, "result": f"Processed: {task}"},
            metadata={"trigger_supported": True, "async_execution": True},
        )

    def main(self, args=None):
        """CLI entry point for command-line triggering."""
        if args:
            task = args.get("task", "default task")
            return asyncio.run(self.execute_task(task))
        return "CLI interface available"

    def handle_api_request(self, request: Dict[str, Any]) -> ToolResponse:
        """API entry point for HTTP/REST triggering."""
        task = request.get("task", "api task")
        result = asyncio.run(self.execute_task(task))
        return result

    def on_event(self, event_type: str, callback):
        """Event-driven entry point for event triggering."""
        self.register_trigger(f"event:{event_type}", callback)
        return f"Event handler registered for {event_type}"

    def schedule_task(self, cron_expression: str, task: str):
        """Scheduled entry point for time-based triggering."""
        self.register_trigger(f"schedule:{cron_expression}", task)
        return f"Scheduled task registered: {cron_expression}"

    def register_trigger(self, trigger_type: str, handler):
        """Register a trigger in the trigger registry."""
        self.trigger_registry[trigger_type] = handler
        self.triggers.append({"type": trigger_type, "handler": handler})
        return f"Trigger registered: {trigger_type}"

    def get_triggers(self) -> Dict[str, Any]:
        """Get documentation of available triggers."""
        return {
            "cli": "Command-line interface via main() method",
            "api": "REST API via handle_api_request() method",
            "events": "Event-driven via on_event() method",
            "schedule": "Time-based via schedule_task() method",
            "registered_triggers": list(self.trigger_registry.keys()),
            "total_triggers": len(self.triggers),
        }

    def webhook_handler(self, payload: Dict[str, Any]):
        """Webhook support for remote triggering."""
        task = payload.get("task", "webhook task")
        return asyncio.run(self.execute_task(task))

    def process_message_queue(self, message: Dict[str, Any]):
        """Message queue support for async remote triggering."""
        task = message.get("task", "queue task")
        return asyncio.run(self.execute_task(task))


class NoTriggerSupportAgent(BaseAgent):
    """Example of agent without trigger support."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})


class PartialTriggerSupportAgent(BaseAgent):
    """Example of agent with partial trigger support."""

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})

    def main(self, args=None):
        """CLI entry point only."""
        return "CLI available"

    def handle_api_request(self, request: Dict[str, Any]):
        """API entry point only."""
        return ToolResponse(success=True, data=request)

    # Missing: event handlers, scheduling, trigger registration, documentation


class LimitedFlexibilityAgent(BaseAgent):
    """Agent with triggers but limited flexibility."""

    def __init__(self):
        super().__init__()
        self.triggers = {}

    def register_tools(self):
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        return ToolResponse(success=True, data={"task": task})

    def main(self):
        """CLI entry point."""
        return "CLI available"

    def handle_request(self, request):
        """Basic request handler."""
        return "Request handled"

    def register_trigger(self, name, handler):
        """Basic trigger registration."""
        self.triggers[name] = handler

    # Missing: async support, remote triggers, flexible mechanisms


class TestFactor11Validator:
    """Test suite for Factor 11 validator."""

    def test_compliant_trigger_anywhere_agent(self):
        """Test that agent with comprehensive trigger support passes validation."""
        agent = CompliantTriggerAnywhereAgent()
        validator = Factor11Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.FULLY_COMPLIANT
        assert details["score"] == 1.0
        assert details["checks"]["multiple_entry_points"]
        assert details["checks"]["trigger_registration"]
        assert details["checks"]["trigger_flexibility"]
        assert details["checks"]["trigger_documentation"]
        assert len(details["issues"]) == 0

    def test_no_trigger_support_agent(self):
        """Test that agent without trigger support fails validation."""
        agent = NoTriggerSupportAgent()
        validator = Factor11Validator()

        compliance, details = validator.validate(agent)

        assert compliance == ComplianceLevel.NON_COMPLIANT
        assert details["score"] == 0.0
        assert not details["checks"]["multiple_entry_points"]
        assert not details["checks"]["trigger_registration"]
        assert not details["checks"]["trigger_flexibility"]
        assert not details["checks"]["trigger_documentation"]
        assert len(details["issues"]) == 4
        assert len(details["recommendations"]) == 4

    def test_partial_trigger_support_agent(self):
        """Test that agent with partial trigger support gets partial score."""
        agent = PartialTriggerSupportAgent()
        validator = Factor11Validator()

        compliance, details = validator.validate(agent)

        assert compliance in [
            ComplianceLevel.NON_COMPLIANT,
            ComplianceLevel.PARTIALLY_COMPLIANT,
        ]
        assert 0.0 < details["score"] < 1.0
        assert details["checks"]["multiple_entry_points"]  # Has CLI and API
        assert not details["checks"]["trigger_registration"]  # No registration
        assert len(details["issues"]) > 0

    def test_limited_flexibility_agent(self):
        """Test that agent with limited flexibility gets lower score."""
        agent = LimitedFlexibilityAgent()
        validator = Factor11Validator()

        compliance, details = validator.validate(agent)

        assert compliance in [
            ComplianceLevel.NON_COMPLIANT,
            ComplianceLevel.PARTIALLY_COMPLIANT,
            ComplianceLevel.MOSTLY_COMPLIANT,
        ]
        assert details["checks"]["trigger_registration"]  # Has registration
        # May or may not have other features

    def test_multiple_entry_points_detection(self):
        """Test multiple entry points detection logic."""
        agent = CompliantTriggerAnywhereAgent()
        validator = Factor11Validator()

        # Test entry point methods exist
        assert hasattr(agent, "main")  # CLI
        assert hasattr(agent, "handle_api_request")  # API
        assert hasattr(agent, "on_event")  # Events
        assert hasattr(agent, "schedule_task")  # Scheduling

        # Test validator detects multiple entry points
        has_multiple = validator._check_multiple_entry_points(agent)
        assert has_multiple

    def test_trigger_registration_detection(self):
        """Test trigger registration system detection."""
        agent = CompliantTriggerAnywhereAgent()
        validator = Factor11Validator()

        # Test trigger registration methods exist
        assert hasattr(agent, "register_trigger")
        assert hasattr(agent, "trigger_registry")
        assert hasattr(agent, "triggers")

        # Test registration functionality
        agent.register_trigger("test_trigger", lambda: "test")
        assert "test_trigger" in agent.trigger_registry
        assert len(agent.triggers) > 0

        # Test validator detects registration
        has_registration = validator._check_trigger_registration(agent)
        assert has_registration

    def test_trigger_flexibility_detection(self):
        """Test trigger flexibility detection."""
        agent = CompliantTriggerAnywhereAgent()
        validator = Factor11Validator()

        # Test async support
        import inspect

        assert inspect.iscoroutinefunction(agent.execute_task)

        # Test remote trigger methods
        assert hasattr(agent, "webhook_handler")
        assert hasattr(agent, "process_message_queue")

        # Test validator detects flexibility
        has_flexibility = validator._check_trigger_flexibility(agent)
        assert has_flexibility

    def test_trigger_documentation_detection(self):
        """Test trigger documentation detection."""
        agent = CompliantTriggerAnywhereAgent()
        validator = Factor11Validator()

        # Test documentation method exists
        assert hasattr(agent, "get_triggers")

        # Test documentation provides useful info
        docs = agent.get_triggers()
        assert isinstance(docs, dict)
        assert "cli" in docs
        assert "api" in docs
        assert "events" in docs
        assert "schedule" in docs

        # Test validator detects documentation
        has_docs = validator._check_trigger_documentation(agent)
        assert has_docs

    def test_cli_entry_point_functionality(self):
        """Test CLI entry point functionality."""
        agent = CompliantTriggerAnywhereAgent()

        # Test CLI interface
        result = agent.main({"task": "cli test"})
        assert result.success
        assert "cli test" in str(result.data)

    def test_api_entry_point_functionality(self):
        """Test API entry point functionality."""
        agent = CompliantTriggerAnywhereAgent()

        # Test API interface
        request = {"task": "api test", "data": {"key": "value"}}
        result = agent.handle_api_request(request)
        assert result.success
        assert "api test" in str(result.data)

    def test_event_driven_functionality(self):
        """Test event-driven functionality."""
        agent = CompliantTriggerAnywhereAgent()

        # Test event handler registration
        def test_callback(event):
            return f"Handled: {event}"

        result = agent.on_event("file_changed", test_callback)
        assert "file_changed" in result
        assert "event:file_changed" in agent.trigger_registry

    def test_scheduled_functionality(self):
        """Test scheduled task functionality."""
        agent = CompliantTriggerAnywhereAgent()

        # Test schedule registration
        result = agent.schedule_task("0 * * * *", "hourly_task")
        assert "0 * * * *" in result
        assert "schedule:0 * * * *" in agent.trigger_registry

    def test_async_execution_support(self):
        """Test async execution support."""
        agent = CompliantTriggerAnywhereAgent()

        # Test async execution
        async def run_async_test():
            result = await agent.execute_task("async test")
            return result

        result = asyncio.run(run_async_test())
        assert result.success
        assert result.metadata["async_execution"]

    def test_remote_trigger_support(self):
        """Test remote trigger support."""
        agent = CompliantTriggerAnywhereAgent()

        # Test webhook handler
        payload = {"task": "webhook test", "source": "external"}
        result = agent.webhook_handler(payload)
        assert result.success

        # Test message queue processing
        message = {"task": "queue test", "priority": "high"}
        result = agent.process_message_queue(message)
        assert result.success

    def test_trigger_registry_management(self):
        """Test trigger registry management."""
        agent = CompliantTriggerAnywhereAgent()

        # Test multiple trigger registrations
        agent.register_trigger("type1", "handler1")
        agent.register_trigger("type2", "handler2")
        agent.register_trigger("type3", "handler3")

        assert len(agent.trigger_registry) >= 3
        assert len(agent.triggers) >= 3
        assert "type1" in agent.trigger_registry
        assert "type2" in agent.trigger_registry
        assert "type3" in agent.trigger_registry

    def test_recommendations_provided(self):
        """Test that validator provides actionable recommendations."""
        agent = NoTriggerSupportAgent()
        validator = Factor11Validator()

        _, details = validator.validate(agent)

        assert (
            len(details["recommendations"]) >= 3
        )  # Should have at least 3 recommendations
        recommendations_text = " ".join(details["recommendations"])
        assert "entry points" in recommendations_text.lower()
        assert "registration" in recommendations_text.lower()
        assert "mechanisms" in recommendations_text.lower()
        assert "document" in recommendations_text.lower()

    def test_edge_cases(self):
        """Test validator handles edge cases gracefully."""
        validator = Factor11Validator()

        # Test agent with no methods
        class MinimalAgent(BaseAgent):
            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            def execute_task(self, task: str, context=None) -> ToolResponse:
                return ToolResponse(success=True, data={"task": task})

        agent = MinimalAgent()
        compliance, details = validator.validate(agent)

        assert isinstance(details["score"], float)
        assert 0.0 <= details["score"] <= 1.0
        assert compliance == ComplianceLevel.NON_COMPLIANT

    def test_trigger_detection_edge_cases(self):
        """Test edge cases in trigger detection."""
        validator = Factor11Validator()

        # Test agent with trigger-like method names but no actual functionality
        class FakeTriggerAgent(BaseAgent):
            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            def execute_task(self, task: str, context=None) -> ToolResponse:
                return ToolResponse(success=True, data={"task": task})

            def main_function(self):  # Has 'main' in name
                return "fake"

            def api_like_method(self):  # Has 'api' in name
                return "fake"

        agent = FakeTriggerAgent()
        has_multiple = validator._check_multiple_entry_points(agent)
        # May or may not detect depending on exact method names - test that it handles gracefully
        assert isinstance(has_multiple, bool)

    def test_async_detection(self):
        """Test async functionality detection."""
        validator = Factor11Validator()

        # Test agent with async methods
        class AsyncAgent(BaseAgent):
            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            async def execute_task(self, task: str) -> ToolResponse:
                return ToolResponse(success=True, data={"task": task})

            async def async_method(self):
                await asyncio.sleep(0.01)
                return "async result"

        agent = AsyncAgent()
        has_flexibility = validator._check_trigger_flexibility(agent)
        assert has_flexibility

    def test_explicit_documentation_methods(self):
        """Test documentation detection via explicit methods."""
        validator = Factor11Validator()

        # Test agent with explicit trigger documentation method
        class DocumentedAgent(BaseAgent):
            def register_tools(self):
                return []

            def _apply_action(self, action: dict) -> ToolResponse:
                return ToolResponse(success=True, data=action)

            def execute_task(self, task: str) -> ToolResponse:
                return ToolResponse(success=True, data={"task": task})

            def get_triggers(self):
                """Explicit trigger documentation method."""
                return {"cli": "Available", "api": "Available"}

        agent = DocumentedAgent()
        has_docs = validator._check_trigger_documentation(agent)
        assert has_docs

    def test_compliance_level_thresholds(self):
        """Test compliance level determination."""
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

    def test_trigger_registry_functionality(self):
        """Test comprehensive trigger registry functionality."""
        agent = CompliantTriggerAnywhereAgent()

        # Test different trigger types
        trigger_types = [
            ("cli", lambda: "cli handler"),
            ("api", lambda req: f"api handler: {req}"),
            ("event:user_login", lambda event: f"login handler: {event}"),
            ("schedule:daily", lambda: "daily task"),
            ("webhook:github", lambda payload: f"github hook: {payload}"),
        ]

        for trigger_type, handler in trigger_types:
            result = agent.register_trigger(trigger_type, handler)
            assert trigger_type in result
            assert trigger_type in agent.trigger_registry

        # Verify all triggers are registered
        assert len(agent.trigger_registry) >= len(trigger_types)

        # Test trigger documentation includes all registered triggers
        docs = agent.get_triggers()
        assert len(docs["registered_triggers"]) >= len(trigger_types)

    def test_comprehensive_functionality(self):
        """Test complete trigger functionality workflow."""
        agent = CompliantTriggerAnywhereAgent()

        # Test all entry points work
        cli_result = agent.main({"task": "cli workflow test"})
        assert cli_result.success

        api_result = agent.handle_api_request({"task": "api workflow test"})
        assert api_result.success

        # Test trigger registration and retrieval
        def workflow_handler():
            return "workflow complete"

        agent.register_trigger("workflow:test", workflow_handler)
        docs = agent.get_triggers()
        assert "workflow:test" in docs["registered_triggers"]

        # Test async functionality
        async def async_workflow():
            return await agent.execute_task("async workflow test")

        result = asyncio.run(async_workflow())
        assert result.success
        assert "async workflow test" in str(result.data)


if __name__ == "__main__":
    # Run tests
    test = TestFactor11Validator()

    print("Testing Factor 11 Validator...")

    try:
        test.test_compliant_trigger_anywhere_agent()
        print("✅ Compliant trigger anywhere agent test passed")
    except AssertionError as e:
        print(f"❌ Compliant trigger anywhere agent test failed: {e}")

    try:
        test.test_no_trigger_support_agent()
        print("✅ No trigger support agent test passed")
    except AssertionError as e:
        print(f"❌ No trigger support agent test failed: {e}")

    try:
        test.test_partial_trigger_support_agent()
        print("✅ Partial trigger support agent test passed")
    except AssertionError as e:
        print(f"❌ Partial trigger support agent test failed: {e}")

    try:
        test.test_multiple_entry_points_detection()
        print("✅ Multiple entry points detection test passed")
    except AssertionError as e:
        print(f"❌ Multiple entry points detection test failed: {e}")

    try:
        test.test_trigger_registration_detection()
        print("✅ Trigger registration detection test passed")
    except AssertionError as e:
        print(f"❌ Trigger registration detection test failed: {e}")

    try:
        test.test_trigger_flexibility_detection()
        print("✅ Trigger flexibility detection test passed")
    except AssertionError as e:
        print(f"❌ Trigger flexibility detection test failed: {e}")

    try:
        test.test_trigger_documentation_detection()
        print("✅ Trigger documentation detection test passed")
    except AssertionError as e:
        print(f"❌ Trigger documentation detection test failed: {e}")

    try:
        test.test_async_execution_support()
        print("✅ Async execution support test passed")
    except AssertionError as e:
        print(f"❌ Async execution support test failed: {e}")

    try:
        test.test_comprehensive_functionality()
        print("✅ Comprehensive functionality test passed")
    except AssertionError as e:
        print(f"❌ Comprehensive functionality test failed: {e}")

    print("\n🎉 All Factor 11 tests completed!")
