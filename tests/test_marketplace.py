"""
Comprehensive tests for Agent Marketplace - 12-Factor Agents Framework
Tests registry, plugin system, and security framework
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import marketplace components
from core.marketplace import (
    AgentRegistry, AgentRegistration, AgentMetadata, AgentCapability,
    PluginManager, AgentPlugin, PluginManifest, PluginType, PluginState,
    SecurityManager, SecurityValidator, SecurityPolicy, SecurityLevel, SecurityRisk
)
from core.base import BaseAgent, ToolResponse, AgentState


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_agent_metadata():
    """Sample agent metadata for testing"""
    return AgentMetadata(
        name="test_agent",
        version="1.0.0",
        description="Test agent for unit tests",
        author="test_author",
        capabilities=[AgentCapability.NATURAL_LANGUAGE, AgentCapability.FILE_OPERATIONS],
        dependencies=["numpy>=1.0.0"],
        keywords=["test", "example"]
    )


@pytest.fixture
def sample_agent_code():
    """Sample agent code for testing"""
    return '''
from core.base import BaseAgent, ToolResponse
import json
import asyncio

class TestAgent(BaseAgent):
    def __init__(self, agent_id=None):
        super().__init__(agent_id)
        
    async def execute_task(self, task: str) -> ToolResponse:
        return ToolResponse(
            success=True,
            data={"task": task, "result": "completed"},
            metadata={"agent": "TestAgent"}
        )
'''


@pytest.fixture
def sample_plugin_manifest():
    """Sample plugin manifest for testing"""
    return PluginManifest(
        name="test_plugin",
        version="1.0.0",
        plugin_type=PluginType.AGENT,
        description="Test plugin for unit tests",
        author="test_author",
        entry_point="test_plugin.TestPlugin",
        capabilities=[AgentCapability.NATURAL_LANGUAGE]
    )


@pytest.fixture
def registry(temp_dir):
    """Create test registry"""
    return AgentRegistry(registry_path=temp_dir / "test_registry.json")


@pytest.fixture
def plugin_manager(temp_dir):
    """Create test plugin manager"""
    return PluginManager(plugins_dir=temp_dir / "plugins")


@pytest.fixture
def security_manager():
    """Create test security manager"""
    return SecurityManager()


class TestAgentRegistry:
    """Test Agent Registry functionality"""
    
    @pytest.mark.asyncio
    async def test_register_agent_success(self, registry, sample_agent_metadata, temp_dir, sample_agent_code):
        """Test successful agent registration"""
        # Create test agent file
        agent_file = temp_dir / "test_agent.py"
        agent_file.write_text(sample_agent_code)
        
        # Register agent
        result = await registry.register_agent(
            metadata=sample_agent_metadata,
            module_path=str(agent_file),
            class_name="TestAgent"
        )
        
        assert result.success
        assert "agent_id" in result.data
        assert result.data["agent_id"].startswith("test_agent_1.0.0_")
    
    @pytest.mark.asyncio
    async def test_register_agent_invalid_version(self, registry, sample_agent_metadata, temp_dir, sample_agent_code):
        """Test registration with invalid version"""
        sample_agent_metadata.version = "invalid-version"
        agent_file = temp_dir / "test_agent.py"
        agent_file.write_text(sample_agent_code)
        
        result = await registry.register_agent(
            metadata=sample_agent_metadata,
            module_path=str(agent_file),
            class_name="TestAgent"
        )
        
        assert not result.success
        assert "Invalid semantic version" in result.error
    
    @pytest.mark.asyncio
    async def test_register_agent_nonexistent_file(self, registry, sample_agent_metadata):
        """Test registration with nonexistent file"""
        result = await registry.register_agent(
            metadata=sample_agent_metadata,
            module_path="nonexistent_file.py",
            class_name="TestAgent"
        )
        
        assert not result.success
        assert "Cannot read module file" in result.error
    
    @pytest.mark.asyncio
    async def test_register_agent_invalid_class(self, registry, sample_agent_metadata, temp_dir):
        """Test registration with invalid class"""
        agent_file = temp_dir / "invalid_agent.py"
        agent_file.write_text("class NotAnAgent: pass")
        
        result = await registry.register_agent(
            metadata=sample_agent_metadata,
            module_path=str(agent_file),
            class_name="NotAnAgent"
        )
        
        assert not result.success
        assert "Invalid agent class" in result.error
    
    @pytest.mark.asyncio
    async def test_discover_agents_by_name(self, registry, sample_agent_metadata, temp_dir, sample_agent_code):
        """Test agent discovery by name"""
        # Register test agent
        agent_file = temp_dir / "test_agent.py"
        agent_file.write_text(sample_agent_code)
        await registry.register_agent(sample_agent_metadata, str(agent_file), "TestAgent")
        
        # Discover agents
        result = await registry.discover_agents(name="test_agent")
        
        assert result.success
        assert result.data["total_count"] == 1
        assert result.data["agents"][0]["metadata"]["name"] == "test_agent"
    
    @pytest.mark.asyncio
    async def test_discover_agents_by_capability(self, registry, sample_agent_metadata, temp_dir, sample_agent_code):
        """Test agent discovery by capability"""
        agent_file = temp_dir / "test_agent.py"
        agent_file.write_text(sample_agent_code)
        await registry.register_agent(sample_agent_metadata, str(agent_file), "TestAgent")
        
        result = await registry.discover_agents(capabilities=[AgentCapability.NATURAL_LANGUAGE])
        
        assert result.success
        assert result.data["total_count"] == 1
    
    @pytest.mark.asyncio
    async def test_load_agent(self, registry, sample_agent_metadata, temp_dir, sample_agent_code):
        """Test agent loading"""
        agent_file = temp_dir / "test_agent.py"
        agent_file.write_text(sample_agent_code)
        
        # Register agent
        reg_result = await registry.register_agent(sample_agent_metadata, str(agent_file), "TestAgent")
        agent_id = reg_result.data["agent_id"]
        
        # Load agent
        load_result = await registry.load_agent(agent_id)
        
        assert load_result.success
        assert isinstance(load_result.data["agent_instance"], BaseAgent)
    
    @pytest.mark.asyncio
    async def test_unregister_agent(self, registry, sample_agent_metadata, temp_dir, sample_agent_code):
        """Test agent unregistration"""
        agent_file = temp_dir / "test_agent.py"
        agent_file.write_text(sample_agent_code)
        
        # Register and unregister agent
        reg_result = await registry.register_agent(sample_agent_metadata, str(agent_file), "TestAgent")
        agent_id = reg_result.data["agent_id"]
        
        unreg_result = await registry.unregister_agent(agent_id)
        assert unreg_result.success
        
        # Verify agent is no longer discoverable
        discover_result = await registry.discover_agents(name="test_agent")
        assert discover_result.data["total_count"] == 0
    
    @pytest.mark.asyncio
    async def test_update_agent_rating(self, registry, sample_agent_metadata, temp_dir, sample_agent_code):
        """Test agent rating updates"""
        agent_file = temp_dir / "test_agent.py"
        agent_file.write_text(sample_agent_code)
        
        # Register agent
        reg_result = await registry.register_agent(sample_agent_metadata, str(agent_file), "TestAgent")
        agent_id = reg_result.data["agent_id"]
        
        # Update rating
        rating_result = await registry.update_agent_rating(agent_id, 4.5, "Great agent!")
        
        assert rating_result.success
        assert rating_result.data["new_rating"] == 4.5
        assert rating_result.data["total_reviews"] == 1
    
    @pytest.mark.asyncio
    async def test_get_registry_stats(self, registry, sample_agent_metadata, temp_dir, sample_agent_code):
        """Test registry statistics"""
        agent_file = temp_dir / "test_agent.py"
        agent_file.write_text(sample_agent_code)
        await registry.register_agent(sample_agent_metadata, str(agent_file), "TestAgent")
        
        stats_result = await registry.get_registry_stats()
        
        assert stats_result.success
        assert stats_result.data["total_agents"] == 1
        assert stats_result.data["active_agents"] == 1


class TestPluginManager:
    """Test Plugin Manager functionality"""
    
    @pytest.mark.asyncio
    async def test_discover_plugins(self, plugin_manager, temp_dir, sample_plugin_manifest):
        """Test plugin discovery"""
        # Create plugin directory with manifest
        plugin_dir = temp_dir / "plugins" / "test_plugin"
        plugin_dir.mkdir(parents=True)
        
        manifest_file = plugin_dir / "plugin.json"
        manifest_dict = {
            "name": sample_plugin_manifest.name,
            "version": sample_plugin_manifest.version,
            "plugin_type": sample_plugin_manifest.plugin_type.value,
            "description": sample_plugin_manifest.description,
            "author": sample_plugin_manifest.author,
            "entry_point": sample_plugin_manifest.entry_point,
            "capabilities": [cap.value for cap in sample_plugin_manifest.capabilities]
        }
        manifest_file.write_text(json.dumps(manifest_dict))
        
        # Discover plugins
        result = await plugin_manager.discover_plugins([temp_dir / "plugins"])
        
        assert result.success
        assert result.data["count"] == 1
        assert result.data["plugins"][0]["manifest"]["name"] == "test_plugin"
    
    @pytest.mark.asyncio
    async def test_install_plugin_from_directory(self, plugin_manager, temp_dir, sample_plugin_manifest, sample_agent_code):
        """Test plugin installation from directory"""
        # Create source plugin directory
        source_dir = temp_dir / "source_plugin"
        source_dir.mkdir()
        
        # Create manifest
        manifest_dict = {
            "name": sample_plugin_manifest.name,
            "version": sample_plugin_manifest.version,
            "plugin_type": sample_plugin_manifest.plugin_type.value,
            "description": sample_plugin_manifest.description,
            "author": sample_plugin_manifest.author,
            "entry_point": sample_plugin_manifest.entry_point,
            "capabilities": [cap.value for cap in sample_plugin_manifest.capabilities]
        }
        (source_dir / "plugin.json").write_text(json.dumps(manifest_dict))
        
        # Create plugin code
        (source_dir / "test_plugin.py").write_text(sample_agent_code.replace("TestAgent", "TestPlugin"))
        
        # Install plugin
        result = await plugin_manager.install_plugin(source_dir)
        
        assert result.success
        assert "plugin_id" in result.data
    
    @pytest.mark.asyncio
    async def test_load_plugin_success(self, plugin_manager, temp_dir, sample_plugin_manifest, sample_agent_code):
        """Test successful plugin loading"""
        # Install plugin first
        await self._install_test_plugin(plugin_manager, temp_dir, sample_plugin_manifest, sample_agent_code)
        
        plugin_id = f"{sample_plugin_manifest.name}_{sample_plugin_manifest.version}"
        
        # Load plugin
        result = await plugin_manager.load_plugin(plugin_id)
        
        assert result.success
        assert result.data["plugin_id"] == plugin_id
        assert result.data["state"] == PluginState.LOADED.value
    
    @pytest.mark.asyncio
    async def test_load_plugin_nonexistent(self, plugin_manager):
        """Test loading nonexistent plugin"""
        result = await plugin_manager.load_plugin("nonexistent_plugin")
        
        assert not result.success
        assert "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_unload_plugin(self, plugin_manager, temp_dir, sample_plugin_manifest, sample_agent_code):
        """Test plugin unloading"""
        # Install and load plugin
        await self._install_test_plugin(plugin_manager, temp_dir, sample_plugin_manifest, sample_agent_code)
        plugin_id = f"{sample_plugin_manifest.name}_{sample_plugin_manifest.version}"
        await plugin_manager.load_plugin(plugin_id)
        
        # Unload plugin
        result = await plugin_manager.unload_plugin(plugin_id)
        
        assert result.success
        assert result.data["plugin_id"] == plugin_id
    
    @pytest.mark.asyncio
    async def test_activate_plugin(self, plugin_manager, temp_dir, sample_plugin_manifest, sample_agent_code):
        """Test plugin activation"""
        # Install and load plugin
        await self._install_test_plugin(plugin_manager, temp_dir, sample_plugin_manifest, sample_agent_code)
        plugin_id = f"{sample_plugin_manifest.name}_{sample_plugin_manifest.version}"
        await plugin_manager.load_plugin(plugin_id)
        
        # Activate plugin
        result = await plugin_manager.activate_plugin(plugin_id)
        
        assert result.success
        assert result.data["state"] == PluginState.ACTIVE.value
    
    @pytest.mark.asyncio
    async def test_list_plugins(self, plugin_manager, temp_dir, sample_plugin_manifest, sample_agent_code):
        """Test plugin listing"""
        # Install plugin
        await self._install_test_plugin(plugin_manager, temp_dir, sample_plugin_manifest, sample_agent_code)
        
        # List plugins
        result = await plugin_manager.list_plugins()
        
        assert result.success
        assert result.data["count"] == 1
        assert result.data["plugins"][0]["name"] == "test_plugin"
    
    @pytest.mark.asyncio
    async def test_get_plugin_info(self, plugin_manager, temp_dir, sample_plugin_manifest, sample_agent_code):
        """Test getting plugin information"""
        # Install plugin
        await self._install_test_plugin(plugin_manager, temp_dir, sample_plugin_manifest, sample_agent_code)
        plugin_id = f"{sample_plugin_manifest.name}_{sample_plugin_manifest.version}"
        
        # Get plugin info
        result = await plugin_manager.get_plugin_info(plugin_id)
        
        assert result.success
        assert result.data["plugin_info"]["plugin_id"] == plugin_id
    
    @pytest.mark.asyncio
    async def test_get_manager_stats(self, plugin_manager):
        """Test plugin manager statistics"""
        result = await plugin_manager.get_manager_stats()
        
        assert result.success
        assert "total_plugins" in result.data
        assert "state_counts" in result.data
        assert "type_counts" in result.data
    
    async def _install_test_plugin(self, plugin_manager, temp_dir, manifest, code):
        """Helper to install test plugin"""
        source_dir = temp_dir / "test_plugin_source"
        source_dir.mkdir()
        
        manifest_dict = {
            "name": manifest.name,
            "version": manifest.version,
            "plugin_type": manifest.plugin_type.value,
            "description": manifest.description,
            "author": manifest.author,
            "entry_point": manifest.entry_point,
            "capabilities": [cap.value for cap in manifest.capabilities]
        }
        (source_dir / "plugin.json").write_text(json.dumps(manifest_dict))
        (source_dir / "test_plugin.py").write_text(code.replace("TestAgent", "TestPlugin"))
        
        return await plugin_manager.install_plugin(source_dir)


class TestSecurityFramework:
    """Test Security Framework functionality"""
    
    def test_security_validator_safe_code(self, security_manager):
        """Test validation of safe code"""
        safe_code = '''
import json
import datetime

class SafeAgent:
    def __init__(self):
        self.data = {}
    
    def process_data(self, input_data):
        return json.dumps(input_data)
'''
        
        validator = SecurityValidator()
        result = validator.validate_code(safe_code)
        
        assert result.passed
        assert result.risk_level == SecurityRisk.LOW
        assert len(result.violations) == 0
    
    def test_security_validator_dangerous_code(self, security_manager):
        """Test validation of dangerous code"""
        dangerous_code = '''
import subprocess
import os

class DangerousAgent:
    def execute_command(self, cmd):
        return subprocess.call(cmd, shell=True)
    
    def read_sensitive_file(self):
        return eval("open('/etc/passwd').read()")
'''
        
        validator = SecurityValidator()
        result = validator.validate_code(dangerous_code)
        
        assert not result.passed
        assert result.risk_level in [SecurityRisk.HIGH, SecurityRisk.CRITICAL]
        assert len(result.violations) > 0
        
        # Check for specific violations
        violation_types = [v.violation_type for v in result.violations]
        assert any("banned_import" in vt or "dangerous_import" in vt for vt in violation_types)
        assert any("eval_exec" in vt or "code_injection" in vt for vt in violation_types)
    
    @pytest.mark.asyncio
    async def test_audit_agent_file(self, security_manager, temp_dir):
        """Test auditing agent file"""
        # Create test agent file
        agent_code = '''
from core.base import BaseAgent, ToolResponse

class TestAgent(BaseAgent):
    async def execute_task(self, task):
        return ToolResponse(success=True, data={"result": task})
'''
        agent_file = temp_dir / "test_agent.py"
        agent_file.write_text(agent_code)
        
        # Audit agent
        result = await security_manager.audit_agent(agent_file, security_level=SecurityLevel.STANDARD)
        
        assert result.success
        assert result.data["audit_result"]["passed"]
    
    @pytest.mark.asyncio
    async def test_audit_agent_directory(self, security_manager, temp_dir):
        """Test auditing agent directory"""
        # Create agent directory with multiple files
        agent_dir = temp_dir / "agent"
        agent_dir.mkdir()
        
        (agent_dir / "__init__.py").write_text("# Agent package")
        (agent_dir / "main.py").write_text('''
from core.base import BaseAgent, ToolResponse

class MainAgent(BaseAgent):
    async def execute_task(self, task):
        return ToolResponse(success=True, data={})
''')
        (agent_dir / "utils.py").write_text('''
def helper_function(data):
    return data.upper()
''')
        
        # Audit directory
        result = await security_manager.audit_agent(agent_dir)
        
        assert result.success
        assert result.data["audit_result"]["passed"]
    
    def test_sign_and_verify_agent(self, security_manager, temp_dir):
        """Test agent signing and verification"""
        # Create test file
        test_file = temp_dir / "test_agent.py"
        test_file.write_text("# Test agent code")
        
        # Sign agent
        sign_result = security_manager.sign_agent(test_file)
        assert sign_result.success
        
        signature = sign_result.data["signature"]
        
        # Verify signature
        verify_result = security_manager.verify_signature(test_file, signature)
        assert verify_result.success
        assert verify_result.data["signature_valid"]
    
    def test_verify_invalid_signature(self, security_manager, temp_dir):
        """Test verification with invalid signature"""
        test_file = temp_dir / "test_agent.py"
        test_file.write_text("# Test agent code")
        
        # Try to verify with wrong signature
        verify_result = security_manager.verify_signature(test_file, "invalid_signature")
        assert verify_result.success
        assert not verify_result.data["signature_valid"]
    
    @pytest.mark.asyncio
    async def test_security_report(self, security_manager, temp_dir):
        """Test security report generation"""
        # Create and audit a test file to generate history
        test_file = temp_dir / "test_agent.py"
        test_file.write_text("# Safe test code")
        await security_manager.audit_agent(test_file)
        
        # Generate security report
        result = await security_manager.get_security_report()
        
        assert result.success
        assert "total_audits" in result.data
        assert "pass_rate" in result.data
        assert "risk_distribution" in result.data
    
    def test_sandbox_context(self, security_manager):
        """Test sandbox context manager"""
        policy = SecurityPolicy(max_memory_mb=100, max_cpu_seconds=10)
        
        with security_manager.create_sandbox(SecurityLevel.STANDARD) as sandbox:
            # Test workspace creation
            workspace = sandbox.create_temp_workspace()
            assert workspace.exists()
            assert workspace.is_dir()
        
        # Workspace should be cleaned up after context exit
        # Note: This may not work in all test environments due to permissions


class TestIntegration:
    """Integration tests for marketplace components"""
    
    @pytest.mark.asyncio
    async def test_full_agent_lifecycle(self, temp_dir, sample_agent_metadata, sample_agent_code):
        """Test complete agent lifecycle: register -> discover -> load -> execute"""
        # Setup
        registry = AgentRegistry(registry_path=temp_dir / "registry.json")
        security_manager = SecurityManager()
        
        # Create agent file
        agent_file = temp_dir / "test_agent.py"
        agent_file.write_text(sample_agent_code)
        
        # 1. Security audit
        audit_result = await security_manager.audit_agent(agent_file)
        assert audit_result.success
        
        # 2. Register agent
        reg_result = await registry.register_agent(
            metadata=sample_agent_metadata,
            module_path=str(agent_file),
            class_name="TestAgent"
        )
        assert reg_result.success
        agent_id = reg_result.data["agent_id"]
        
        # 3. Discover agent
        discover_result = await registry.discover_agents(name="test_agent")
        assert discover_result.success
        assert discover_result.data["total_count"] == 1
        
        # 4. Load agent
        load_result = await registry.load_agent(agent_id)
        assert load_result.success
        agent_instance = load_result.data["agent_instance"]
        
        # 5. Execute task
        task_result = await agent_instance.execute_task("test task")
        assert task_result.success
        assert task_result.data["task"] == "test task"
    
    @pytest.mark.asyncio
    async def test_plugin_with_security_validation(self, temp_dir, sample_plugin_manifest, sample_agent_code):
        """Test plugin installation with security validation"""
        plugin_manager = PluginManager(plugins_dir=temp_dir / "plugins")
        security_manager = SecurityManager()
        
        # Create plugin directory
        plugin_dir = temp_dir / "test_plugin"
        plugin_dir.mkdir()
        
        # Create manifest
        manifest_dict = {
            "name": sample_plugin_manifest.name,
            "version": sample_plugin_manifest.version,
            "plugin_type": sample_plugin_manifest.plugin_type.value,
            "description": sample_plugin_manifest.description,
            "author": sample_plugin_manifest.author,
            "entry_point": "test_plugin.TestPlugin",
            "capabilities": [cap.value for cap in sample_plugin_manifest.capabilities]
        }
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest_dict))
        
        # Create plugin code
        plugin_code = sample_agent_code.replace("TestAgent", "TestPlugin")
        (plugin_dir / "test_plugin.py").write_text(plugin_code)
        
        # Security audit
        audit_result = await security_manager.audit_agent(plugin_dir)
        assert audit_result.success
        
        # Install plugin
        install_result = await plugin_manager.install_plugin(plugin_dir)
        assert install_result.success
        
        # Load and activate
        plugin_id = f"{sample_plugin_manifest.name}_{sample_plugin_manifest.version}"
        load_result = await plugin_manager.load_plugin(plugin_id)
        assert load_result.success
        
        activate_result = await plugin_manager.activate_plugin(plugin_id)
        assert activate_result.success
    
    @pytest.mark.asyncio
    async def test_marketplace_stats_and_reporting(self, temp_dir, sample_agent_metadata, sample_agent_code):
        """Test marketplace statistics and reporting"""
        registry = AgentRegistry(registry_path=temp_dir / "registry.json")
        plugin_manager = PluginManager(plugins_dir=temp_dir / "plugins")
        security_manager = SecurityManager()
        
        # Register multiple agents
        for i in range(3):
            agent_file = temp_dir / f"agent_{i}.py"
            agent_file.write_text(sample_agent_code.replace("TestAgent", f"TestAgent{i}"))
            
            metadata = AgentMetadata(
                name=f"test_agent_{i}",
                version="1.0.0",
                description=f"Test agent {i}",
                author="test_author",
                capabilities=[AgentCapability.NATURAL_LANGUAGE]
            )
            
            # Audit and register
            await security_manager.audit_agent(agent_file)
            await registry.register_agent(metadata, str(agent_file), f"TestAgent{i}")
        
        # Get statistics
        registry_stats = await registry.get_registry_stats()
        assert registry_stats.success
        assert registry_stats.data["total_agents"] == 3
        
        plugin_stats = await plugin_manager.get_manager_stats()
        assert plugin_stats.success
        
        security_report = await security_manager.get_security_report()
        assert security_report.success
        assert security_report.data["total_audits"] == 3


# Test fixtures for mocking
@pytest.fixture
def mock_agent_class():
    """Mock agent class for testing"""
    class MockAgent(BaseAgent):
        async def execute_task(self, task: str) -> ToolResponse:
            return ToolResponse(success=True, data={"mock": "result"})
    return MockAgent


@pytest.fixture  
def mock_plugin_class():
    """Mock plugin class for testing"""
    class MockPlugin(AgentPlugin):
        async def initialize(self) -> ToolResponse:
            return ToolResponse(success=True, data={"initialized": True})
    return MockPlugin


# Performance tests
class TestPerformance:
    """Performance tests for marketplace components"""
    
    @pytest.mark.asyncio
    async def test_registry_performance_bulk_operations(self, temp_dir):
        """Test registry performance with bulk operations"""
        registry = AgentRegistry(registry_path=temp_dir / "perf_registry.json")
        
        # Create multiple agents
        agents_count = 50
        tasks = []
        
        for i in range(agents_count):
            agent_file = temp_dir / f"perf_agent_{i}.py"
            agent_file.write_text(f'''
from core.base import BaseAgent, ToolResponse
class PerfAgent{i}(BaseAgent):
    async def execute_task(self, task):
        return ToolResponse(success=True, data={{"agent": {i}}})
''')
            
            metadata = AgentMetadata(
                name=f"perf_agent_{i}",
                version="1.0.0", 
                description=f"Performance test agent {i}",
                author="test",
                capabilities=[AgentCapability.NATURAL_LANGUAGE]
            )
            
            tasks.append(registry.register_agent(metadata, str(agent_file), f"PerfAgent{i}"))
        
        # Execute all registrations
        results = await asyncio.gather(*tasks)
        
        # Verify all succeeded
        assert all(r.success for r in results)
        
        # Test bulk discovery
        discovery_result = await registry.discover_agents()
        assert discovery_result.success
        assert discovery_result.data["total_count"] == agents_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])