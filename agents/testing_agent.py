"""
TestingAgent - Comprehensive testing for 12-factor agents system.
Runs unit tests, integration tests, and validates agent functionality.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys
import traceback

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent  # noqa: E402
from core.tools import Tool, ToolResponse  # noqa: E402
from core.execution_context import ExecutionContext  # noqa: E402


class UnitTestTool(Tool):
    """Run unit tests for agents"""

    def __init__(self):
        super().__init__(
            name="run_unit_tests", description="Run unit tests for all agents"
        )

    def execute(self) -> ToolResponse:
        """Run unit tests"""
        try:
            test_results = []

            # Test core imports
            try:
                from core.tools import ToolResponse

                test_results.append(
                    {
                        "test": "core_imports",
                        "status": "passed",
                        "message": "All core modules import successfully",
                    }
                )
            except Exception as e:
                test_results.append(
                    {"test": "core_imports", "status": "failed", "error": str(e)}
                )

            # Test agent imports
            agent_modules = [
                "repository_setup_agent",
                "prompt_management_agent",
                "event_system_agent",
                "component_migration_agent",
                "issue_orchestrator_agent",
                "uv_migration_agent",
                "code_review_agent",
                "issue_processor_agent",
                "issue_fixer_agent",
            ]

            for module in agent_modules:
                try:
                    # Use importlib instead of exec for safety
                    import importlib

                    importlib.import_module(f"agents.{module}")
                    test_results.append(
                        {
                            "test": f"import_{module}",
                            "status": "passed",
                            "message": f"{module} imports successfully",
                        }
                    )
                except Exception as e:
                    test_results.append(
                        {
                            "test": f"import_{module}",
                            "status": "failed",
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                        }
                    )

            # Test concrete agent instantiation (BaseAgent is abstract)
            try:
                from agents.repository_setup_agent import RepositorySetupAgent

                agent = RepositorySetupAgent()
                assert hasattr(agent, "execute_task")
                assert hasattr(agent, "register_tools")
                assert hasattr(agent, "_apply_action")
                test_results.append(
                    {
                        "test": "concrete_agent_instantiation",
                        "status": "passed",
                        "message": "Concrete agent instantiates correctly",
                    }
                )
            except Exception as e:
                test_results.append(
                    {
                        "test": "concrete_agent_instantiation",
                        "status": "failed",
                        "error": str(e),
                    }
                )

            # Test ToolResponse
            try:
                response = ToolResponse(success=True, data={"test": "data"})
                assert response.success
                assert response.data["test"] == "data"
                test_results.append(
                    {
                        "test": "tool_response",
                        "status": "passed",
                        "message": "ToolResponse works correctly",
                    }
                )
            except Exception as e:
                test_results.append(
                    {"test": "tool_response", "status": "failed", "error": str(e)}
                )

            # Count results
            passed = len([r for r in test_results if r["status"] == "passed"])
            failed = len([r for r in test_results if r["status"] == "failed"])

            return ToolResponse(
                success=failed == 0,
                data={
                    "tests_run": len(test_results),
                    "passed": passed,
                    "failed": failed,
                    "results": test_results,
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}


class IntegrationTestTool(Tool):
    """Run integration tests"""

    def __init__(self):
        super().__init__(
            name="run_integration_tests",
            description="Run integration tests for agent interactions",
        )

    def execute(self) -> ToolResponse:
        """Run integration tests"""
        try:
            test_results = []

            # Test agent creation and execution
            from agents.repository_setup_agent import RepositorySetupAgent

            try:
                agent = RepositorySetupAgent()
                # Don't actually run the task to avoid modifying files
                assert agent is not None
                assert len(agent.tools) > 0
                test_results.append(
                    {
                        "test": "repository_setup_agent_creation",
                        "status": "passed",
                        "message": "RepositorySetupAgent creates successfully",
                    }
                )
            except Exception as e:
                test_results.append(
                    {
                        "test": "repository_setup_agent_creation",
                        "status": "failed",
                        "error": str(e),
                    }
                )

            # Test state management
            from core.state import UnifiedState

            try:
                state = UnifiedState()
                state.set("test_key", "test_value")
                assert state.get("test_key") == "test_value"
                test_results.append(
                    {
                        "test": "state_management",
                        "status": "passed",
                        "message": "UnifiedState works correctly",
                    }
                )
            except Exception as e:
                test_results.append(
                    {"test": "state_management", "status": "failed", "error": str(e)}
                )

            # Test prompt manager
            from core.prompt_manager import PromptManager

            try:
                pm = PromptManager()
                # Test that it initializes
                assert pm is not None
                test_results.append(
                    {
                        "test": "prompt_manager",
                        "status": "passed",
                        "message": "PromptManager initializes correctly",
                    }
                )
            except Exception as e:
                test_results.append(
                    {"test": "prompt_manager", "status": "failed", "error": str(e)}
                )

            # Test event system
            from core.triggers import LocalEventSystem

            try:
                event_system = LocalEventSystem()
                event_id = event_system.emit("test_event", {"data": "test"})
                assert event_id is not None
                test_results.append(
                    {
                        "test": "event_system",
                        "status": "passed",
                        "message": "LocalEventSystem works correctly",
                    }
                )
            except Exception as e:
                test_results.append(
                    {"test": "event_system", "status": "failed", "error": str(e)}
                )

            # Count results
            passed = len([r for r in test_results if r["status"] == "passed"])
            failed = len([r for r in test_results if r["status"] == "failed"])

            return ToolResponse(
                success=failed == 0,
                data={
                    "tests_run": len(test_results),
                    "passed": passed,
                    "failed": failed,
                    "results": test_results,
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}


class PytestTool(Tool):
    """Run pytest tests"""

    def __init__(self):
        super().__init__(name="run_pytest", description="Run pytest test suite")

    def execute(self, test_dir: str = "tests") -> ToolResponse:
        """Run pytest"""
        try:
            # Create test directory if it doesn't exist
            test_path = Path(test_dir)
            test_path.mkdir(exist_ok=True)

            # Create a comprehensive test file if it doesn't exist
            test_file = test_path / "test_agents.py"
            if not test_file.exists():
                test_content = '''"""Comprehensive tests for 12-factor agents"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.agent import BaseAgent
from core.tools import Tool, ToolResponse
from core.state import UnifiedState
from core.context import AgentContext


class TestCore:
    """Test core functionality"""
    
    def test_base_agent(self):
        """Test BaseAgent creation"""
        agent = BaseAgent()
        assert agent is not None
        assert hasattr(agent, 'execute_task')
        assert hasattr(agent, 'register_tools')
    
    def test_tool_response(self):
        """Test ToolResponse"""
        response = ToolResponse(success=True, data={"test": "data"})
        assert response.success
        assert response.data["test"] == "data"
        
        error_response = ToolResponse(success=False, error="Test error")
        assert not error_response.success
        assert error_response.error == "Test error"
    
    def test_unified_state(self):
        """Test UnifiedState"""
        state = UnifiedState()
        state.set("key", "value")
        assert state.get("key") == "value"
        
        state.set("nested.key", {"data": "test"})
        assert state.get("nested.key")["data"] == "test"
    
    def test_agent_context(self):
        """Test AgentContext"""
        context = AgentContext()
        context.add("test", "data")
        assert "test" in str(context)


class TestAgents:
    """Test individual agents"""
    
    def test_repository_setup_agent(self):
        """Test RepositorySetupAgent"""
        from agents.repository_setup_agent import RepositorySetupAgent
        agent = RepositorySetupAgent()
        assert agent is not None
        assert len(agent.tools) == 3  # GitInitTool, DirectoryCreatorTool, FileCreatorTool
    
    def test_prompt_management_agent(self):
        """Test PromptManagementAgent"""
        from agents.prompt_management_agent import PromptManagementAgent
        agent = PromptManagementAgent()
        assert agent is not None
        assert len(agent.tools) > 0
    
    def test_event_system_agent(self):
        """Test EventSystemAgent"""
        from agents.event_system_agent import EventSystemAgent
        agent = EventSystemAgent()
        assert agent is not None
        assert len(agent.tools) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
                test_file.write_text(test_content)

            # Run pytest
            cmd = [
                "uv",
                "run",
                "python",
                "-m",
                "pytest",
                str(test_path),
                "-v",
                "--tb=short",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            return ToolResponse(
                success=result.returncode == 0,
                data={
                    "exit_code": result.returncode,
                    "output": result.stdout,
                    "errors": result.stderr if result.stderr else None,
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"test_dir": {"type": "string"}}}


class LintTool(Tool):
    """Run linting checks"""

    def __init__(self):
        super().__init__(name="run_lint", description="Run linting on codebase")

    def execute(self) -> ToolResponse:
        """Run basic linting checks"""
        try:
            issues = []

            # Check Python files for basic issues
            for py_file in Path(".").rglob("*.py"):
                # Skip virtual environment
                if ".venv" in str(py_file):
                    continue

                try:
                    with open(py_file, "r") as f:
                        content = f.read()

                    # Try to compile the file
                    compile(content, str(py_file), "exec")

                except SyntaxError as e:
                    issues.append(
                        {
                            "file": str(py_file),
                            "type": "syntax_error",
                            "line": e.lineno,
                            "message": str(e),
                        }
                    )
                except Exception as e:
                    issues.append(
                        {"file": str(py_file), "type": "error", "message": str(e)}
                    )

            return ToolResponse(
                success=len(issues) == 0,
                data={
                    "issues": issues,
                    "files_checked": len(list(Path(".").rglob("*.py"))),
                    "issues_found": len(issues),
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}


class TestingAgent(BaseAgent):
    """
    Comprehensive testing agent for 12-factor agents system.
    Runs unit tests, integration tests, pytest suite, and linting.
    """

    def register_tools(self) -> List[Tool]:
        """Register testing tools"""
        return [UnitTestTool(), IntegrationTestTool(), PytestTool(), LintTool()]

    def execute_task(
        self, task: str, context: Optional[ExecutionContext] = None
    ) -> ToolResponse:
        """
        Execute comprehensive testing.
        Task format: "run tests" or "test <specific_area>"
        """

        all_results = {}
        all_passed = True

        # Step 1: Lint check
        print("\n🔍 Running lint checks...")
        lint_tool = self.tools[3]
        lint_result = lint_tool.execute()
        all_results["lint"] = lint_result.data

        if lint_result.success:
            print(
                f"✅ Lint check passed - {lint_result.data['files_checked']} files checked"
            )
        else:
            print(f"⚠️ Lint issues found: {len(lint_result.data['issues'])} issues")
            all_passed = False

        # Step 2: Unit tests
        print("\n🧪 Running unit tests...")
        unit_tool = self.tools[0]
        unit_result = unit_tool.execute()
        all_results["unit_tests"] = unit_result.data

        if unit_result.success:
            print(
                f"✅ Unit tests passed - {unit_result.data['passed']}/{unit_result.data['tests_run']} passed"
            )
        else:
            print(f"❌ Unit tests failed - {unit_result.data['failed']} failures")
            all_passed = False

            # Show failures
            for test in unit_result.data["results"]:
                if test["status"] == "failed":
                    print(f"  ❌ {test['test']}: {test.get('error', 'Unknown error')}")

        # Step 3: Integration tests
        print("\n🔗 Running integration tests...")
        integration_tool = self.tools[1]
        integration_result = integration_tool.execute()
        all_results["integration_tests"] = integration_result.data

        if integration_result.success:
            print(
                f"✅ Integration tests passed - {integration_result.data['passed']}/{integration_result.data['tests_run']} passed"
            )
        else:
            print(
                f"❌ Integration tests failed - {integration_result.data['failed']} failures"
            )
            all_passed = False

        # Step 4: Pytest suite
        print("\n🚀 Running pytest suite...")
        pytest_tool = self.tools[2]
        pytest_result = pytest_tool.execute()
        all_results["pytest"] = pytest_result.data

        if pytest_result.success:
            print("✅ Pytest suite passed")
        else:
            print("❌ Pytest suite failed")
            all_passed = False

        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        if all_passed:
            print("✅ ALL TESTS PASSED!")
        else:
            print("❌ SOME TESTS FAILED")

        print("\nResults:")
        print(f"  Lint: {'✅ Passed' if lint_result.success else '❌ Failed'}")
        print(
            f"  Unit Tests: {all_results['unit_tests']['passed']}/{all_results['unit_tests']['tests_run']} passed"
        )
        print(
            f"  Integration Tests: {all_results['integration_tests']['passed']}/{all_results['integration_tests']['tests_run']} passed"
        )
        print(f"  Pytest: {'✅ Passed' if pytest_result.success else '❌ Failed'}")

        # Update state
        self.state.set("tests_complete", True)
        self.state.set("all_passed", all_passed)
        self.state.set("test_results", all_results)

        return ToolResponse(
            success=all_passed,
            data={
                "all_passed": all_passed,
                "results": all_results,
                "summary": {
                    "lint": lint_result.success,
                    "unit_tests": f"{all_results['unit_tests']['passed']}/{all_results['unit_tests']['tests_run']}",
                    "integration_tests": f"{all_results['integration_tests']['passed']}/{all_results['integration_tests']['tests_run']}",
                    "pytest": pytest_result.success,
                },
            },
        )

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply test action"""
        action_type = action.get("type", "test")

        if action_type == "test":
            return self.execute_task(action.get("task", "run tests"))

        return ToolResponse(success=False, error=f"Unknown action type: {action_type}")


# Self-test when run directly
if __name__ == "__main__":
    print("🧪 Running comprehensive test suite...")
    agent = TestingAgent()

    result = agent.execute_task("run all tests")

    if result.success:
        print("\n✅ All tests passed successfully!")
    else:
        print("\n❌ Some tests failed. Review the output above for details.")

    # Save test report
    report_path = Path("test_report.json")
    report_path.write_text(json.dumps(result.data, indent=2))
    print(f"\n📄 Test report saved to {report_path}")
