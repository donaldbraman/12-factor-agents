"""Quick validation tests for pre-commit hooks"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestQuickValidation:
    """Fast tests to catch major regressions"""

    def test_imports_work(self):
        """Test core imports don't crash"""
        try:
            from core.hierarchical_orchestrator import HierarchicalOrchestrator
            from core.context_manager import ContextManager
            from core.agent_executor import AgentExecutor

            assert True
        except ImportError as e:
            pytest.fail(f"Core import failed: {e}")

    def test_orchestrator_basic_function(self):
        """Test orchestrator can be created"""
        from core.hierarchical_orchestrator import HierarchicalOrchestrator

        orchestrator = HierarchicalOrchestrator()
        assert orchestrator is not None
        assert hasattr(orchestrator, "execute_task")

    def test_context_manager_efficiency(self):
        """Quick context efficiency check"""
        from core.context_manager import ContextManager

        manager = ContextManager(max_tokens=1000)
        manager.add_context("test", priority=1)

        efficiency = manager.get_efficiency()
        assert 0 <= efficiency <= 1.0, f"Invalid efficiency: {efficiency}"

    def test_agent_executor_basic(self):
        """Test agent executor works"""
        from core.agent_executor import AgentExecutor

        executor = AgentExecutor()
        result = executor.execute("test", {"test": True})
        assert result is not None
        assert "result" in result

    def test_marketplace_imports(self):
        """Test marketplace components import"""
        try:
            from core.marketplace.registry import AgentRegistry
            from core.marketplace.plugin_system import PluginManager
            from core.marketplace.security import SecurityValidator

            assert True
        except ImportError as e:
            pytest.fail(f"Marketplace import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
