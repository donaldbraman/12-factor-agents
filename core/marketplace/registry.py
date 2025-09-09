"""
Agent Registry System - 12-Factor Agents Framework
Implements agent discovery, registration, and lifecycle management
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Set, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import importlib
import importlib.util
import semver

from ..base import BaseAgent, ToolResponse


class AgentCapability(Enum):
    """Standard agent capabilities"""

    FILE_OPERATIONS = "file_operations"
    NETWORK_ACCESS = "network_access"
    DATABASE_ACCESS = "database_access"
    CODE_EXECUTION = "code_execution"
    WEB_SCRAPING = "web_scraping"
    API_INTEGRATION = "api_integration"
    DATA_ANALYSIS = "data_analysis"
    NATURAL_LANGUAGE = "natural_language"
    IMAGE_PROCESSING = "image_processing"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"


@dataclass
class AgentMetadata:
    """Agent metadata for registry"""

    name: str
    version: str
    description: str
    author: str
    capabilities: List[AgentCapability]
    dependencies: List[str] = None
    min_python_version: str = "3.8"
    license: str = "MIT"
    homepage: str = ""
    keywords: List[str] = None
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.keywords is None:
            self.keywords = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class AgentRegistration:
    """Agent registration in marketplace"""

    agent_id: str
    metadata: AgentMetadata
    module_path: str
    class_name: str
    checksum: str
    status: str = "active"
    registration_time: str = None
    last_verified: str = None
    usage_count: int = 0
    rating: float = 0.0
    reviews: List[Dict] = None

    def __post_init__(self):
        if self.registration_time is None:
            self.registration_time = datetime.now().isoformat()
        if self.last_verified is None:
            self.last_verified = self.registration_time
        if self.reviews is None:
            self.reviews = []


class AgentRegistry:
    """
    Production-ready agent registry following 12-factor principles

    Features:
    - Agent discovery and registration
    - Version management with semantic versioning
    - Dependency resolution
    - Security validation
    - Performance monitoring
    """

    def __init__(self, registry_path: Union[str, Path] = None):
        """Initialize agent registry"""
        self.registry_path = Path(registry_path or "agents/registry.json")
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        self._agents: Dict[str, AgentRegistration] = {}
        self._name_index: Dict[str, Set[str]] = {}  # name -> set of agent_ids
        self._capability_index: Dict[AgentCapability, Set[str]] = {}
        self._version_index: Dict[
            str, Dict[str, str]
        ] = {}  # name -> version -> agent_id

        self._load_registry()

    def _load_registry(self):
        """Load registry from disk"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r") as f:
                    data = json.load(f)

                for agent_data in data.get("agents", []):
                    # Reconstruct AgentRegistration from dict
                    metadata_dict = agent_data["metadata"]
                    metadata_dict["capabilities"] = [
                        AgentCapability(cap) for cap in metadata_dict["capabilities"]
                    ]
                    metadata = AgentMetadata(**metadata_dict)

                    registration = AgentRegistration(
                        agent_id=agent_data["agent_id"],
                        metadata=metadata,
                        module_path=agent_data["module_path"],
                        class_name=agent_data["class_name"],
                        checksum=agent_data["checksum"],
                        status=agent_data.get("status", "active"),
                        registration_time=agent_data.get("registration_time"),
                        last_verified=agent_data.get("last_verified"),
                        usage_count=agent_data.get("usage_count", 0),
                        rating=agent_data.get("rating", 0.0),
                        reviews=agent_data.get("reviews", []),
                    )

                    self._agents[registration.agent_id] = registration
                    self._update_indexes(registration)

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Warning: Failed to load registry: {e}")
                self._agents = {}

    def _save_registry(self):
        """Save registry to disk"""
        registry_data = {
            "version": "1.0",
            "updated": datetime.now().isoformat(),
            "agents": [],
        }

        for registration in self._agents.values():
            agent_dict = asdict(registration)
            # Convert enum capabilities to strings
            agent_dict["metadata"]["capabilities"] = [
                cap.value for cap in registration.metadata.capabilities
            ]
            registry_data["agents"].append(agent_dict)

        with open(self.registry_path, "w") as f:
            json.dump(registry_data, f, indent=2)

    def _update_indexes(self, registration: AgentRegistration):
        """Update search indexes"""
        agent_id = registration.agent_id
        metadata = registration.metadata

        # Update name index
        if metadata.name not in self._name_index:
            self._name_index[metadata.name] = set()
        self._name_index[metadata.name].add(agent_id)

        # Update capability index
        for capability in metadata.capabilities:
            if capability not in self._capability_index:
                self._capability_index[capability] = set()
            self._capability_index[capability].add(agent_id)

        # Update version index
        if metadata.name not in self._version_index:
            self._version_index[metadata.name] = {}
        self._version_index[metadata.name][metadata.version] = agent_id

    def _remove_from_indexes(self, registration: AgentRegistration):
        """Remove agent from search indexes"""
        agent_id = registration.agent_id
        metadata = registration.metadata

        # Remove from name index
        if metadata.name in self._name_index:
            self._name_index[metadata.name].discard(agent_id)
            if not self._name_index[metadata.name]:
                del self._name_index[metadata.name]

        # Remove from capability index
        for capability in metadata.capabilities:
            if capability in self._capability_index:
                self._capability_index[capability].discard(agent_id)
                if not self._capability_index[capability]:
                    del self._capability_index[capability]

        # Remove from version index
        if metadata.name in self._version_index:
            if metadata.version in self._version_index[metadata.name]:
                del self._version_index[metadata.name][metadata.version]
            if not self._version_index[metadata.name]:
                del self._version_index[metadata.name]

    def _calculate_checksum(self, module_path: str) -> str:
        """Calculate checksum for agent module"""
        try:
            with open(module_path, "rb") as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except FileNotFoundError:
            return ""

    def _validate_agent_class(self, module_path: str, class_name: str) -> bool:
        """Validate that the agent class exists and inherits from BaseAgent"""
        try:
            spec = importlib.util.spec_from_file_location("agent_module", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, class_name):
                return False

            agent_class = getattr(module, class_name)
            return issubclass(agent_class, BaseAgent)
        except Exception:
            return False

    async def register_agent(
        self,
        metadata: AgentMetadata,
        module_path: str,
        class_name: str,
        force: bool = False,
    ) -> ToolResponse:
        """
        Register a new agent in the marketplace

        Args:
            metadata: Agent metadata
            module_path: Path to agent module file
            class_name: Name of agent class
            force: Force registration even if agent exists

        Returns:
            ToolResponse with registration result
        """
        try:
            # Validate semantic version
            try:
                semver.VersionInfo.parse(metadata.version)
            except ValueError:
                return ToolResponse(
                    success=False,
                    data={},
                    error=f"Invalid semantic version: {metadata.version}",
                )

            # Validate agent class
            if not self._validate_agent_class(module_path, class_name):
                return ToolResponse(
                    success=False,
                    data={},
                    error=f"Invalid agent class {class_name} in {module_path}",
                )

            # Calculate checksum
            checksum = self._calculate_checksum(module_path)
            if not checksum:
                return ToolResponse(
                    success=False,
                    data={},
                    error=f"Cannot read module file: {module_path}",
                )

            # Generate agent ID
            agent_id = f"{metadata.name}_{metadata.version}_{checksum[:8]}"

            # Check if agent already exists
            if agent_id in self._agents and not force:
                return ToolResponse(
                    success=False,
                    data={"agent_id": agent_id},
                    error="Agent already registered. Use force=True to override.",
                )

            # Check for version conflicts
            if (
                metadata.name in self._version_index
                and metadata.version in self._version_index[metadata.name]
                and not force
            ):
                existing_id = self._version_index[metadata.name][metadata.version]
                return ToolResponse(
                    success=False,
                    data={"existing_agent_id": existing_id},
                    error=f"Version {metadata.version} already exists for {metadata.name}",
                )

            # Create registration
            registration = AgentRegistration(
                agent_id=agent_id,
                metadata=metadata,
                module_path=module_path,
                class_name=class_name,
                checksum=checksum,
            )

            # Update registry
            self._agents[agent_id] = registration
            self._update_indexes(registration)
            self._save_registry()

            return ToolResponse(
                success=True,
                data={"agent_id": agent_id, "registration": asdict(registration)},
                metadata={"operation": "register_agent"},
            )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Registration failed: {str(e)}"
            )

    async def unregister_agent(self, agent_id: str) -> ToolResponse:
        """Remove agent from registry"""
        try:
            if agent_id not in self._agents:
                return ToolResponse(
                    success=False, data={}, error=f"Agent {agent_id} not found"
                )

            registration = self._agents[agent_id]
            self._remove_from_indexes(registration)
            del self._agents[agent_id]
            self._save_registry()

            return ToolResponse(
                success=True,
                data={"agent_id": agent_id},
                metadata={"operation": "unregister_agent"},
            )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Unregistration failed: {str(e)}"
            )

    async def discover_agents(
        self,
        name: str = None,
        capabilities: List[AgentCapability] = None,
        keywords: List[str] = None,
        version_range: str = None,
    ) -> ToolResponse:
        """
        Discover agents matching criteria

        Args:
            name: Agent name (exact or partial match)
            capabilities: Required capabilities
            keywords: Keywords to match
            version_range: Semantic version range (e.g., ">=1.0.0,<2.0.0")

        Returns:
            ToolResponse with matching agents
        """
        try:
            matching_ids = set(self._agents.keys())

            # Filter by name
            if name:
                name_matches = set()
                for agent_name, agent_ids in self._name_index.items():
                    if name.lower() in agent_name.lower():
                        name_matches.update(agent_ids)
                matching_ids &= name_matches

            # Filter by capabilities
            if capabilities:
                for capability in capabilities:
                    if capability in self._capability_index:
                        matching_ids &= self._capability_index[capability]
                    else:
                        matching_ids = set()  # No agents have this capability
                        break

            # Filter by keywords
            if keywords:
                keyword_matches = set()
                for agent_id in matching_ids:
                    agent_keywords = self._agents[agent_id].metadata.keywords
                    if any(
                        kw.lower() in [ak.lower() for ak in agent_keywords]
                        for kw in keywords
                    ):
                        keyword_matches.add(agent_id)
                matching_ids &= keyword_matches

            # Filter by version range
            if version_range and name:
                version_matches = set()
                if name in self._version_index:
                    for version, agent_id in self._version_index[name].items():
                        if self._version_satisfies_range(version, version_range):
                            version_matches.add(agent_id)
                matching_ids &= version_matches

            # Get matching registrations
            results = []
            for agent_id in matching_ids:
                if self._agents[agent_id].status == "active":
                    results.append(asdict(self._agents[agent_id]))

            # Sort by rating and usage
            results.sort(key=lambda x: (x["rating"], x["usage_count"]), reverse=True)

            return ToolResponse(
                success=True,
                data={"agents": results, "total_count": len(results)},
                metadata={"operation": "discover_agents"},
            )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Discovery failed: {str(e)}"
            )

    def _version_satisfies_range(self, version: str, version_range: str) -> bool:
        """Check if version satisfies range specification"""
        try:
            # Simple implementation - can be enhanced with full semver range parsing
            if version_range.startswith(">="):
                min_version = version_range[2:]
                return semver.compare(version, min_version) >= 0
            elif version_range.startswith(">"):
                min_version = version_range[1:]
                return semver.compare(version, min_version) > 0
            elif version_range.startswith("<="):
                max_version = version_range[2:]
                return semver.compare(version, max_version) <= 0
            elif version_range.startswith("<"):
                max_version = version_range[1:]
                return semver.compare(version, max_version) < 0
            elif version_range.startswith("=="):
                exact_version = version_range[2:]
                return version == exact_version
            else:
                return version == version_range
        except Exception:
            return False

    async def get_agent(self, agent_id: str) -> ToolResponse:
        """Get agent registration by ID"""
        if agent_id not in self._agents:
            return ToolResponse(
                success=False, data={}, error=f"Agent {agent_id} not found"
            )

        registration = self._agents[agent_id]
        return ToolResponse(
            success=True,
            data={"agent": asdict(registration)},
            metadata={"operation": "get_agent"},
        )

    async def load_agent(self, agent_id: str) -> ToolResponse:
        """Load and instantiate agent class"""
        try:
            if agent_id not in self._agents:
                return ToolResponse(
                    success=False, data={}, error=f"Agent {agent_id} not found"
                )

            registration = self._agents[agent_id]

            # Verify checksum
            current_checksum = self._calculate_checksum(registration.module_path)
            if current_checksum != registration.checksum:
                return ToolResponse(
                    success=False,
                    data={},
                    error="Agent module has been modified (checksum mismatch)",
                )

            # Load module and class
            spec = importlib.util.spec_from_file_location(
                "agent_module", registration.module_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            agent_class = getattr(module, registration.class_name)
            agent_instance = agent_class()

            # Update usage stats
            registration.usage_count += 1
            registration.last_verified = datetime.now().isoformat()
            self._save_registry()

            return ToolResponse(
                success=True,
                data={
                    "agent_instance": agent_instance,
                    "metadata": asdict(registration.metadata),
                },
                metadata={"operation": "load_agent"},
            )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Failed to load agent: {str(e)}"
            )

    async def update_agent_rating(
        self, agent_id: str, rating: float, review: str = None
    ) -> ToolResponse:
        """Update agent rating and add review"""
        try:
            if agent_id not in self._agents:
                return ToolResponse(
                    success=False, data={}, error=f"Agent {agent_id} not found"
                )

            if not (0 <= rating <= 5):
                return ToolResponse(
                    success=False, data={}, error="Rating must be between 0 and 5"
                )

            registration = self._agents[agent_id]

            # Add review
            if review:
                registration.reviews.append(
                    {
                        "rating": rating,
                        "review": review,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # Update average rating
            all_ratings = [r["rating"] for r in registration.reviews if "rating" in r]
            if all_ratings:
                registration.rating = sum(all_ratings) / len(all_ratings)

            self._save_registry()

            return ToolResponse(
                success=True,
                data={
                    "agent_id": agent_id,
                    "new_rating": registration.rating,
                    "total_reviews": len(registration.reviews),
                },
                metadata={"operation": "update_rating"},
            )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Failed to update rating: {str(e)}"
            )

    async def get_registry_stats(self) -> ToolResponse:
        """Get registry statistics"""
        try:
            stats = {
                "total_agents": len(self._agents),
                "active_agents": len(
                    [a for a in self._agents.values() if a.status == "active"]
                ),
                "total_capabilities": len(self._capability_index),
                "total_usage": sum(a.usage_count for a in self._agents.values()),
                "average_rating": sum(a.rating for a in self._agents.values())
                / len(self._agents)
                if self._agents
                else 0,
                "top_capabilities": [],
                "top_agents": [],
            }

            # Top capabilities by agent count
            capability_counts = [
                (cap.value, len(agent_ids))
                for cap, agent_ids in self._capability_index.items()
            ]
            capability_counts.sort(key=lambda x: x[1], reverse=True)
            stats["top_capabilities"] = capability_counts[:10]

            # Top agents by usage
            agent_usage = [
                (agent_id, reg.usage_count, reg.rating)
                for agent_id, reg in self._agents.items()
                if reg.status == "active"
            ]
            agent_usage.sort(key=lambda x: (x[1], x[2]), reverse=True)
            stats["top_agents"] = agent_usage[:10]

            return ToolResponse(
                success=True, data=stats, metadata={"operation": "get_stats"}
            )

        except Exception as e:
            return ToolResponse(
                success=False, data={}, error=f"Failed to get stats: {str(e)}"
            )
