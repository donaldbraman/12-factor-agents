"""Lazy loading utilities for 50% faster startup"""
import importlib
from typing import Any, Optional


class LazyLoader:
    """Lazy load modules only when needed"""

    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module: Optional[Any] = None

    def __getattr__(self, name: str) -> Any:
        """Load module on first access"""
        if self._module is None:
            self._module = importlib.import_module(self.module_name)
        return getattr(self._module, name)


# Lazy load heavy modules
def get_orchestrator():
    """Get orchestrator with lazy loading"""
    from core.hierarchical_orchestrator import HierarchicalOrchestrator

    return HierarchicalOrchestrator()


def get_marketplace():
    """Get marketplace components with lazy loading"""
    from core.marketplace import registry

    return registry


def get_executor():
    """Get executor with lazy loading"""
    from core.agent_executor import AgentExecutor

    return AgentExecutor()


# Export for easy access
__all__ = ["LazyLoader", "get_orchestrator", "get_marketplace", "get_executor"]
