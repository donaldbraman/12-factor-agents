"""Comprehensive tests for 12-factor agents"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.agent import BaseAgent
from core.tools import ToolResponse
from core.state import UnifiedState
from core.context import AgentContext


class TestCore:
    """Test core functionality"""

    def test_base_agent(self):
        """Test BaseAgent creation"""

        # BaseAgent is abstract, need to create a concrete implementation
        class TestAgentImpl(BaseAgent):
            def register_tools(self):
                return []

            def execute_task(self, task):
                return ToolResponse(success=True, data={"test": "pass"})

            def _apply_action(self, action):
                return ToolResponse(success=True, data={"test": "pass"})

        agent = TestAgentImpl()
        assert agent is not None
        assert hasattr(agent, "execute_task")
        assert hasattr(agent, "register_tools")

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
        assert (
            len(agent.tools) == 3
        )  # GitInitTool, DirectoryCreatorTool, FileCreatorTool

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
