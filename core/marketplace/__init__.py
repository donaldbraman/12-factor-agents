"""
Agent Marketplace - 12-Factor Agents Framework
Production-ready marketplace for agent discovery, registration, and management
"""

from .registry import AgentRegistry, AgentRegistration, AgentMetadata, AgentCapability
from .plugin_system import (
    PluginManager,
    AgentPlugin,
    PluginManifest,
    PluginType,
    PluginState,
)

# Alias for backward compatibility
PluginSystem = PluginManager
from .security import (  # noqa: E402
    SecurityManager,
    SecurityValidator,
    SecurityPolicy,
    SecurityLevel,
    SecurityRisk,
)

__all__ = [
    "AgentRegistry",
    "AgentRegistration",
    "AgentMetadata",
    "AgentCapability",
    "PluginManager",
    "PluginSystem",  # Alias for backward compatibility
    "AgentPlugin",
    "PluginManifest",
    "PluginType",
    "PluginState",
    "SecurityManager",
    "SecurityValidator",
    "SecurityPolicy",
    "SecurityLevel",
    "SecurityRisk",
]

__version__ = "1.0.0"
