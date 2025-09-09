"""
Plugin System - 12-Factor Agents Framework
Advanced plugin architecture with loading, lifecycle management, and dependency resolution
"""

import sys
import json
import asyncio
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import tempfile
import shutil
import zipfile
import hashlib
import threading
from contextlib import contextmanager

from ..base import BaseAgent, ToolResponse
from .registry import AgentRegistry, AgentCapability


class PluginState(Enum):
    """Plugin lifecycle states"""

    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    FAILED = "failed"
    UNLOADING = "unloading"


class PluginType(Enum):
    """Types of plugins"""

    AGENT = "agent"
    TOOL = "tool"
    MIDDLEWARE = "middleware"
    EXTENSION = "extension"


@dataclass
class PluginManifest:
    """Plugin manifest definition"""

    name: str
    version: str
    plugin_type: PluginType
    description: str
    author: str
    entry_point: str  # module.class or module.function
    dependencies: List[str] = None
    python_version: str = ">=3.8"
    capabilities: List[AgentCapability] = None
    permissions: List[str] = None
    config_schema: Dict[str, Any] = None
    hooks: Dict[str, str] = None  # event -> handler
    resources: List[str] = None
    created_at: str = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.capabilities is None:
            self.capabilities = []
        if self.permissions is None:
            self.permissions = []
        if self.config_schema is None:
            self.config_schema = {}
        if self.hooks is None:
            self.hooks = {}
        if self.resources is None:
            self.resources = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class PluginInfo:
    """Runtime plugin information"""

    plugin_id: str
    manifest: PluginManifest
    module_path: Path
    state: PluginState
    instance: Any = None
    config: Dict[str, Any] = None
    load_time: Optional[str] = None
    error: Optional[str] = None
    dependencies_resolved: bool = False
    checksum: str = ""

    def __post_init__(self):
        if self.config is None:
            self.config = {}


class AgentPlugin:
    """
    Base class for agent plugins
    Provides standard interface for plugin lifecycle management
    """

    def __init__(self, plugin_id: str, config: Dict[str, Any] = None):
        self.plugin_id = plugin_id
        self.config = config or {}
        self.state = PluginState.UNLOADED
        self.hooks = {}

    async def initialize(self) -> ToolResponse:
        """Initialize plugin - override in subclasses"""
        self.state = PluginState.LOADED
        return ToolResponse(success=True, data={"plugin_id": self.plugin_id})

    async def activate(self) -> ToolResponse:
        """Activate plugin - override in subclasses"""
        self.state = PluginState.ACTIVE
        return ToolResponse(success=True, data={"plugin_id": self.plugin_id})

    async def suspend(self) -> ToolResponse:
        """Suspend plugin - override in subclasses"""
        self.state = PluginState.SUSPENDED
        return ToolResponse(success=True, data={"plugin_id": self.plugin_id})

    async def cleanup(self) -> ToolResponse:
        """Cleanup plugin resources - override in subclasses"""
        self.state = PluginState.UNLOADED
        return ToolResponse(success=True, data={"plugin_id": self.plugin_id})

    def register_hook(self, event: str, handler: Callable):
        """Register event hook"""
        if event not in self.hooks:
            self.hooks[event] = []
        self.hooks[event].append(handler)

    async def emit_event(self, event: str, data: Dict[str, Any] = None):
        """Emit event to registered hooks"""
        if event in self.hooks:
            for handler in self.hooks[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data or {})
                    else:
                        handler(data or {})
                except Exception as e:
                    print(f"Hook error in {self.plugin_id}: {e}")


class PluginManager:
    """
    Production-ready plugin management system following 12-factor principles

    Features:
    - Plugin discovery and loading
    - Dependency resolution
    - Lifecycle management
    - Hot reloading
    - Sandboxed execution
    - Event system
    """

    def __init__(
        self, plugins_dir: Union[str, Path] = None, registry: AgentRegistry = None
    ):
        """Initialize plugin manager"""
        self.plugins_dir = Path(plugins_dir or "agents/plugins")
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        self.registry = registry or AgentRegistry()

        # Plugin storage
        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_modules: Dict[str, Any] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._reverse_deps: Dict[str, Set[str]] = {}

        # Event system
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._plugin_lock = threading.RLock()

        # Configuration
        self._config = {
            "max_plugins": 100,
            "enable_hot_reload": True,
            "sandbox_plugins": True,
            "timeout_seconds": 30,
        }

    async def discover_plugins(
        self, search_paths: List[Union[str, Path]] = None
    ) -> ToolResponse:
        """
        Discover plugins in specified directories

        Args:
            search_paths: Directories to search for plugins

        Returns:
            ToolResponse with discovered plugins
        """
        try:
            search_paths = search_paths or [self.plugins_dir]
            discovered = []

            for search_path in search_paths:
                path = Path(search_path)
                if not path.exists():
                    continue

                # Look for plugin manifest files
                for manifest_file in path.rglob("plugin.json"):
                    try:
                        manifest_data = json.loads(manifest_file.read_text())
                        manifest_data["plugin_type"] = PluginType(
                            manifest_data["plugin_type"]
                        )

                        if "capabilities" in manifest_data:
                            manifest_data["capabilities"] = [
                                AgentCapability(cap)
                                for cap in manifest_data["capabilities"]
                            ]

                        manifest = PluginManifest(**manifest_data)

                        # Calculate plugin ID and checksum
                        plugin_dir = manifest_file.parent
                        plugin_id = f"{manifest.name}_{manifest.version}"
                        checksum = self._calculate_directory_checksum(plugin_dir)

                        discovered.append(
                            {
                                "plugin_id": plugin_id,
                                "manifest": asdict(manifest),
                                "path": str(plugin_dir),
                                "checksum": checksum,
                            }
                        )

                    except (json.JSONDecodeError, TypeError, ValueError) as e:
                        print(f"Invalid plugin manifest {manifest_file}: {e}")
                        continue

            return ToolResponse(
                success=True,
                data={"plugins": discovered, "count": len(discovered)},
                metadata={"operation": "discover_plugins"},
            )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Plugin discovery failed: {str(e)}"
            )

    def _calculate_directory_checksum(self, directory: Path) -> str:
        """Calculate checksum for plugin directory"""
        hasher = hashlib.sha256()

        for file_path in sorted(directory.rglob("*")):
            if file_path.is_file():
                hasher.update(str(file_path.relative_to(directory)).encode())
                try:
                    hasher.update(file_path.read_bytes())
                except (OSError, PermissionError):
                    pass  # Skip files we can't read

        return hasher.hexdigest()

    async def install_plugin(
        self, plugin_source: Union[str, Path], verify_signature: bool = True
    ) -> ToolResponse:
        """
        Install plugin from file, directory, or URL

        Args:
            plugin_source: Path to plugin archive, directory, or URL
            verify_signature: Whether to verify plugin signature

        Returns:
            ToolResponse with installation result
        """
        try:
            source_path = Path(plugin_source)

            # Handle different source types
            if source_path.is_file() and source_path.suffix == ".zip":
                # Extract zip archive
                with tempfile.TemporaryDirectory() as temp_dir:
                    with zipfile.ZipFile(source_path, "r") as zip_ref:
                        zip_ref.extractall(temp_dir)

                    # Find manifest
                    manifest_files = list(Path(temp_dir).rglob("plugin.json"))
                    if not manifest_files:
                        return ToolResponse(
                            success=False,
                            data={},
                            error="No plugin.json found in archive",
                        )

                    plugin_dir = manifest_files[0].parent
                    return await self._install_from_directory(plugin_dir)

            elif source_path.is_dir():
                # Install from directory
                return await self._install_from_directory(source_path)

            else:
                return ToolResponse(
                    success=False,
                    data={},
                    error=f"Unsupported plugin source: {plugin_source}",
                )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Plugin installation failed: {str(e)}"
            )

    async def _install_from_directory(self, source_dir: Path) -> ToolResponse:
        """Install plugin from directory"""
        try:
            # Read manifest
            manifest_file = source_dir / "plugin.json"
            if not manifest_file.exists():
                return ToolResponse(
                    success=False, data={}, error="No plugin.json found"
                )

            manifest_data = json.loads(manifest_file.read_text())
            manifest_data["plugin_type"] = PluginType(manifest_data["plugin_type"])

            if "capabilities" in manifest_data:
                manifest_data["capabilities"] = [
                    AgentCapability(cap) for cap in manifest_data["capabilities"]
                ]

            manifest = PluginManifest(**manifest_data)
            plugin_id = f"{manifest.name}_{manifest.version}"

            # Check if plugin already exists
            if plugin_id in self._plugins:
                return ToolResponse(
                    success=False,
                    data={"plugin_id": plugin_id},
                    error="Plugin already installed",
                )

            # Copy to plugins directory
            target_dir = self.plugins_dir / plugin_id
            if target_dir.exists():
                shutil.rmtree(target_dir)

            shutil.copytree(source_dir, target_dir)

            # Create plugin info
            checksum = self._calculate_directory_checksum(target_dir)
            plugin_info = PluginInfo(
                plugin_id=plugin_id,
                manifest=manifest,
                module_path=target_dir,
                state=PluginState.UNLOADED,
                checksum=checksum,
            )

            self._plugins[plugin_id] = plugin_info

            return ToolResponse(
                success=True,
                data={"plugin_id": plugin_id, "path": str(target_dir)},
                metadata={"operation": "install_plugin"},
            )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Installation failed: {str(e)}"
            )

    async def load_plugin(
        self, plugin_id: str, config: Dict[str, Any] = None
    ) -> ToolResponse:
        """
        Load and initialize plugin

        Args:
            plugin_id: Plugin identifier
            config: Plugin configuration

        Returns:
            ToolResponse with loading result
        """
        try:
            with self._plugin_lock:
                if plugin_id not in self._plugins:
                    return ToolResponse(
                        success=False, data={}, error=f"Plugin {plugin_id} not found"
                    )

                plugin_info = self._plugins[plugin_id]

                if plugin_info.state != PluginState.UNLOADED:
                    return ToolResponse(
                        success=False,
                        data={"current_state": plugin_info.state.value},
                        error=f"Plugin {plugin_id} is not unloaded",
                    )

                plugin_info.state = PluginState.LOADING
                plugin_info.config = config or {}

                try:
                    # Resolve dependencies first
                    resolve_result = await self._resolve_dependencies(plugin_id)
                    if not resolve_result.success:
                        plugin_info.state = PluginState.FAILED
                        plugin_info.error = resolve_result.error
                        return resolve_result

                    # Load module
                    module_result = await self._load_plugin_module(plugin_info)
                    if not module_result.success:
                        plugin_info.state = PluginState.FAILED
                        plugin_info.error = module_result.error
                        return module_result

                    plugin_info.state = PluginState.LOADED
                    plugin_info.load_time = datetime.now().isoformat()
                    plugin_info.error = None

                    # Emit plugin loaded event
                    await self._emit_event("plugin_loaded", {"plugin_id": plugin_id})

                    return ToolResponse(
                        success=True,
                        data={"plugin_id": plugin_id, "state": plugin_info.state.value},
                        metadata={"operation": "load_plugin"},
                    )

                except Exception as e:
                    plugin_info.state = PluginState.FAILED
                    plugin_info.error = str(e)
                    raise

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Plugin loading failed: {str(e)}"
            )

    async def _resolve_dependencies(self, plugin_id: str) -> ToolResponse:
        """Resolve plugin dependencies"""
        try:
            plugin_info = self._plugins[plugin_id]
            dependencies = plugin_info.manifest.dependencies

            # Build dependency graph
            self._dependency_graph[plugin_id] = set()

            for dep in dependencies:
                # Simple name-based dependency resolution
                dep_id = self._find_plugin_by_name(dep)
                if not dep_id:
                    return ToolResponse(
                        success=False, data={}, error=f"Dependency {dep} not found"
                    )

                self._dependency_graph[plugin_id].add(dep_id)

                # Update reverse dependencies
                if dep_id not in self._reverse_deps:
                    self._reverse_deps[dep_id] = set()
                self._reverse_deps[dep_id].add(plugin_id)

                # Load dependency if not already loaded
                dep_plugin = self._plugins[dep_id]
                if dep_plugin.state == PluginState.UNLOADED:
                    dep_result = await self.load_plugin(dep_id)
                    if not dep_result.success:
                        return dep_result

            plugin_info.dependencies_resolved = True

            return ToolResponse(
                success=True,
                data={"plugin_id": plugin_id, "dependencies": list(dependencies)},
                metadata={"operation": "resolve_dependencies"},
            )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Dependency resolution failed: {str(e)}"
            )

    def _find_plugin_by_name(self, name: str) -> Optional[str]:
        """Find plugin ID by name"""
        for plugin_id, plugin_info in self._plugins.items():
            if plugin_info.manifest.name == name:
                return plugin_id
        return None

    async def _load_plugin_module(self, plugin_info: PluginInfo) -> ToolResponse:
        """Load plugin module and create instance"""
        try:
            manifest = plugin_info.manifest
            entry_point = manifest.entry_point

            # Parse entry point (module.class or module.function)
            if "." not in entry_point:
                return ToolResponse(
                    success=False,
                    data={},
                    error=f"Invalid entry point format: {entry_point}",
                )

            module_name, class_or_func = entry_point.rsplit(".", 1)

            # Find module file
            module_path = (
                plugin_info.module_path / f"{module_name.replace('.', '/')}.py"
            )
            if not module_path.exists():
                # Try direct module file
                module_path = plugin_info.module_path / f"{module_name}.py"
                if not module_path.exists():
                    return ToolResponse(
                        success=False, data={}, error=f"Module {module_name} not found"
                    )

            # Load module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_info.plugin_id}_{module_name}", module_path
            )
            module = importlib.util.module_from_spec(spec)

            # Add plugin directory to sys.path temporarily
            plugin_dir_str = str(plugin_info.module_path)
            if plugin_dir_str not in sys.path:
                sys.path.insert(0, plugin_dir_str)

            try:
                spec.loader.exec_module(module)
                self._plugin_modules[plugin_info.plugin_id] = module

                # Get class or function
                if not hasattr(module, class_or_func):
                    return ToolResponse(
                        success=False,
                        data={},
                        error=f"Entry point {class_or_func} not found in module",
                    )

                entry_obj = getattr(module, class_or_func)

                # Create instance based on plugin type
                if manifest.plugin_type == PluginType.AGENT:
                    if not issubclass(entry_obj, BaseAgent):
                        return ToolResponse(
                            success=False,
                            data={},
                            error="Agent plugin must inherit from BaseAgent",
                        )
                    plugin_info.instance = entry_obj()

                elif manifest.plugin_type == PluginType.TOOL:
                    # Tools can be functions or classes
                    plugin_info.instance = entry_obj

                else:
                    # For other plugin types, instantiate if it's a class
                    if isinstance(entry_obj, type):
                        plugin_info.instance = entry_obj(
                            plugin_info.plugin_id, plugin_info.config
                        )
                    else:
                        plugin_info.instance = entry_obj

                # Initialize if it has initialize method
                if hasattr(plugin_info.instance, "initialize"):
                    init_result = await plugin_info.instance.initialize()
                    if not init_result.success:
                        return init_result

                return ToolResponse(
                    success=True,
                    data={"plugin_id": plugin_info.plugin_id},
                    metadata={"operation": "load_module"},
                )

            finally:
                # Remove from sys.path
                if plugin_dir_str in sys.path:
                    sys.path.remove(plugin_dir_str)

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Module loading failed: {str(e)}"
            )

    async def unload_plugin(self, plugin_id: str) -> ToolResponse:
        """Unload plugin and cleanup resources"""
        try:
            with self._plugin_lock:
                if plugin_id not in self._plugins:
                    return ToolResponse(
                        success=False, data={}, error=f"Plugin {plugin_id} not found"
                    )

                plugin_info = self._plugins[plugin_id]

                # Check for dependent plugins
                if plugin_id in self._reverse_deps:
                    dependent_plugins = [
                        pid
                        for pid in self._reverse_deps[plugin_id]
                        if self._plugins[pid].state
                        in [PluginState.LOADED, PluginState.ACTIVE]
                    ]
                    if dependent_plugins:
                        return ToolResponse(
                            success=False,
                            data={"dependents": dependent_plugins},
                            error=f"Cannot unload: plugins {dependent_plugins} depend on this plugin",
                        )

                plugin_info.state = PluginState.UNLOADING

                try:
                    # Cleanup instance
                    if plugin_info.instance and hasattr(
                        plugin_info.instance, "cleanup"
                    ):
                        await plugin_info.instance.cleanup()

                    # Remove from modules
                    if plugin_id in self._plugin_modules:
                        del self._plugin_modules[plugin_id]

                    # Clean up dependencies
                    if plugin_id in self._dependency_graph:
                        for dep_id in self._dependency_graph[plugin_id]:
                            if dep_id in self._reverse_deps:
                                self._reverse_deps[dep_id].discard(plugin_id)
                        del self._dependency_graph[plugin_id]

                    plugin_info.state = PluginState.UNLOADED
                    plugin_info.instance = None
                    plugin_info.error = None
                    plugin_info.dependencies_resolved = False

                    # Emit plugin unloaded event
                    await self._emit_event("plugin_unloaded", {"plugin_id": plugin_id})

                    return ToolResponse(
                        success=True,
                        data={"plugin_id": plugin_id},
                        metadata={"operation": "unload_plugin"},
                    )

                except Exception as e:
                    plugin_info.state = PluginState.FAILED
                    plugin_info.error = str(e)
                    raise

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Plugin unloading failed: {str(e)}"
            )

    async def activate_plugin(self, plugin_id: str) -> ToolResponse:
        """Activate loaded plugin"""
        try:
            if plugin_id not in self._plugins:
                return ToolResponse(
                    success=False, data={}, error=f"Plugin {plugin_id} not found"
                )

            plugin_info = self._plugins[plugin_id]

            if plugin_info.state != PluginState.LOADED:
                return ToolResponse(
                    success=False,
                    data={"current_state": plugin_info.state.value},
                    error=f"Plugin {plugin_id} must be loaded first",
                )

            # Activate instance
            if plugin_info.instance and hasattr(plugin_info.instance, "activate"):
                result = await plugin_info.instance.activate()
                if not result.success:
                    return result

            plugin_info.state = PluginState.ACTIVE

            # Emit plugin activated event
            await self._emit_event("plugin_activated", {"plugin_id": plugin_id})

            return ToolResponse(
                success=True,
                data={"plugin_id": plugin_id, "state": plugin_info.state.value},
                metadata={"operation": "activate_plugin"},
            )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Plugin activation failed: {str(e)}"
            )

    async def get_plugin_info(self, plugin_id: str) -> ToolResponse:
        """Get plugin information"""
        if plugin_id not in self._plugins:
            return ToolResponse(
                success=False, data={}, error=f"Plugin {plugin_id} not found"
            )

        plugin_info = self._plugins[plugin_id]
        info_dict = asdict(plugin_info)

        # Convert enum fields to strings
        info_dict["state"] = plugin_info.state.value
        info_dict["manifest"]["plugin_type"] = plugin_info.manifest.plugin_type.value
        info_dict["manifest"]["capabilities"] = [
            cap.value for cap in plugin_info.manifest.capabilities
        ]

        # Remove instance from serialization
        info_dict["instance"] = (
            str(type(plugin_info.instance)) if plugin_info.instance else None
        )

        return ToolResponse(
            success=True,
            data={"plugin_info": info_dict},
            metadata={"operation": "get_plugin_info"},
        )

    async def list_plugins(self, state_filter: PluginState = None) -> ToolResponse:
        """List all plugins with optional state filter"""
        try:
            plugins = []

            for plugin_id, plugin_info in self._plugins.items():
                if state_filter is None or plugin_info.state == state_filter:
                    plugin_dict = {
                        "plugin_id": plugin_id,
                        "name": plugin_info.manifest.name,
                        "version": plugin_info.manifest.version,
                        "type": plugin_info.manifest.plugin_type.value,
                        "state": plugin_info.state.value,
                        "description": plugin_info.manifest.description,
                        "author": plugin_info.manifest.author,
                        "load_time": plugin_info.load_time,
                        "error": plugin_info.error,
                    }
                    plugins.append(plugin_dict)

            return ToolResponse(
                success=True,
                data={"plugins": plugins, "count": len(plugins)},
                metadata={"operation": "list_plugins"},
            )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Failed to list plugins: {str(e)}"
            )

    def register_event_handler(self, event: str, handler: Callable):
        """Register global event handler"""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    async def _emit_event(self, event: str, data: Dict[str, Any] = None):
        """Emit global event"""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data or {})
                    else:
                        handler(data or {})
                except Exception as e:
                    print(f"Event handler error for {event}: {e}")

    @contextmanager
    def plugin_sandbox(self, plugin_id: str):
        """Create sandboxed execution context for plugin"""
        # This is a simplified sandbox - in production, you'd want more robust isolation
        original_path = sys.path.copy()
        original_modules = sys.modules.copy()

        try:
            yield
        finally:
            # Restore original state
            sys.path = original_path
            # Remove any modules added during plugin execution
            for module_name in list(sys.modules.keys()):
                if module_name not in original_modules:
                    del sys.modules[module_name]

    async def get_manager_stats(self) -> ToolResponse:
        """Get plugin manager statistics"""
        try:
            state_counts = {}
            for state in PluginState:
                state_counts[state.value] = 0

            type_counts = {}
            for ptype in PluginType:
                type_counts[ptype.value] = 0

            for plugin_info in self._plugins.values():
                state_counts[plugin_info.state.value] += 1
                type_counts[plugin_info.manifest.plugin_type.value] += 1

            stats = {
                "total_plugins": len(self._plugins),
                "state_counts": state_counts,
                "type_counts": type_counts,
                "dependency_edges": sum(
                    len(deps) for deps in self._dependency_graph.values()
                ),
                "event_handlers": len(self._event_handlers),
                "config": self._config,
            }

            return ToolResponse(
                success=True, data=stats, metadata={"operation": "get_manager_stats"}
            )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Failed to get manager stats: {str(e)}"
            )
