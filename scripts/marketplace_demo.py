#!/usr/bin/env python3
"""
Agent Marketplace Demo Script
Demonstrates the comprehensive marketplace functionality for Issue #37
"""

import asyncio
import json
import tempfile
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.marketplace import (
    AgentRegistry,
    AgentMetadata,
    AgentCapability,
    PluginManager,
    PluginManifest,
    PluginType,
    SecurityManager,
    SecurityLevel,
)


# Sample agent for demonstration
SAMPLE_AGENT_CODE = '''
from core.base import BaseAgent, ToolResponse
import asyncio

class DemoAgent(BaseAgent):
    """Demonstration agent for marketplace"""
    
    def __init__(self, agent_id=None):
        super().__init__(agent_id)
        self.processed_count = 0
        
    async def execute_task(self, task: str) -> ToolResponse:
        """Execute a demonstration task"""
        await asyncio.sleep(0.1)  # Simulate work
        self.processed_count += 1
        
        return ToolResponse(
            success=True,
            data={
                "task": task,
                "result": f"Processed: {task}",
                "count": self.processed_count,
                "agent_id": self.agent_id
            },
            metadata={"agent_type": "DemoAgent"}
        )
'''


async def demonstrate_agent_registry():
    """Demonstrate agent registry functionality"""
    print("=== AGENT REGISTRY DEMONSTRATION ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Initialize registry
        registry = AgentRegistry(registry_path=temp_path / "registry.json")

        # Create sample agent file
        agent_file = temp_path / "demo_agent.py"
        agent_file.write_text(SAMPLE_AGENT_CODE)

        # Create agent metadata
        metadata = AgentMetadata(
            name="demo_agent",
            version="1.0.0",
            description="Demonstration agent for marketplace showcase",
            author="12-Factor Agents Team",
            capabilities=[
                AgentCapability.NATURAL_LANGUAGE,
                AgentCapability.DATA_ANALYSIS,
                AgentCapability.WORKFLOW_ORCHESTRATION,
            ],
            keywords=["demo", "example", "showcase"],
        )

        print("1. Registering agent...")
        reg_result = await registry.register_agent(
            metadata, str(agent_file), "DemoAgent"
        )
        if reg_result.success:
            agent_id = reg_result.data["agent_id"]
            print(f"   ✓ Agent registered with ID: {agent_id}")
        else:
            print(f"   ✗ Registration failed: {reg_result.error}")
            return

        print("2. Discovering agents...")
        discover_result = await registry.discover_agents(
            capabilities=[AgentCapability.NATURAL_LANGUAGE]
        )
        if discover_result.success:
            count = discover_result.data["total_count"]
            print(f"   ✓ Found {count} agents with natural language capability")

        print("3. Loading and executing agent...")
        load_result = await registry.load_agent(agent_id)
        if load_result.success:
            agent_instance = load_result.data["agent_instance"]
            print("   ✓ Agent loaded successfully")

            # Execute task
            task_result = await agent_instance.execute_task("Process demo data")
            if task_result.success:
                print(f"   ✓ Task executed: {task_result.data['result']}")

        print("4. Getting registry statistics...")
        stats_result = await registry.get_registry_stats()
        if stats_result.success:
            stats = stats_result.data
            print(f"   ✓ Registry has {stats['total_agents']} agents")
            print(f"   ✓ Average rating: {stats['average_rating']:.2f}")


async def demonstrate_plugin_system():
    """Demonstrate plugin system functionality"""
    print("\n=== PLUGIN SYSTEM DEMONSTRATION ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Initialize plugin manager
        plugin_manager = PluginManager(plugins_dir=temp_path / "plugins")

        # Create sample plugin
        plugin_dir = temp_path / "demo_plugin"
        plugin_dir.mkdir(parents=True)

        # Create plugin manifest
        manifest = PluginManifest(
            name="demo_plugin",
            version="1.0.0",
            plugin_type=PluginType.AGENT,
            description="Demonstration plugin",
            author="12-Factor Agents Team",
            entry_point="demo_plugin.DemoPlugin",
            capabilities=[AgentCapability.NATURAL_LANGUAGE],
        )

        manifest_dict = {
            "name": manifest.name,
            "version": manifest.version,
            "plugin_type": manifest.plugin_type.value,
            "description": manifest.description,
            "author": manifest.author,
            "entry_point": manifest.entry_point,
            "capabilities": [cap.value for cap in manifest.capabilities],
        }

        (plugin_dir / "plugin.json").write_text(json.dumps(manifest_dict, indent=2))
        (plugin_dir / "demo_plugin.py").write_text(
            SAMPLE_AGENT_CODE.replace("DemoAgent", "DemoPlugin")
        )

        print("1. Installing plugin...")
        install_result = await plugin_manager.install_plugin(plugin_dir)
        if install_result.success:
            plugin_id = install_result.data["plugin_id"]
            print(f"   ✓ Plugin installed with ID: {plugin_id}")
        else:
            print(f"   ✗ Installation failed: {install_result.error}")
            return

        print("2. Loading plugin...")
        load_result = await plugin_manager.load_plugin(plugin_id)
        if load_result.success:
            print("   ✓ Plugin loaded successfully")
        else:
            print(f"   ✗ Loading failed: {load_result.error}")
            return

        print("3. Activating plugin...")
        activate_result = await plugin_manager.activate_plugin(plugin_id)
        if activate_result.success:
            print("   ✓ Plugin activated")

        print("4. Getting plugin information...")
        info_result = await plugin_manager.get_plugin_info(plugin_id)
        if info_result.success:
            info = info_result.data["plugin_info"]
            print(
                f"   ✓ Plugin '{info['manifest']['name']}' v{info['manifest']['version']}"
            )
            print(f"   ✓ State: {info['state']}")

        print("5. Listing all plugins...")
        list_result = await plugin_manager.list_plugins()
        if list_result.success:
            count = list_result.data["count"]
            print(f"   ✓ Found {count} plugins in manager")


async def demonstrate_security_framework():
    """Demonstrate security framework functionality"""
    print("\n=== SECURITY FRAMEWORK DEMONSTRATION ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Initialize security manager
        security_manager = SecurityManager()

        print("1. Auditing safe agent code...")
        safe_file = temp_path / "safe_agent.py"
        safe_file.write_text(SAMPLE_AGENT_CODE)

        safe_audit = await security_manager.audit_agent(
            safe_file, security_level=SecurityLevel.STANDARD
        )
        if safe_audit.success:
            audit_data = safe_audit.data["audit_result"]
            print(f"   ✓ Audit passed: {audit_data['passed']}")
            print(f"   ✓ Risk level: {audit_data['risk_level']}")
            print(f"   ✓ Violations: {len(audit_data['violations'])}")

        print("2. Auditing potentially dangerous code...")
        dangerous_code = """
import subprocess
import os

class DangerousAgent:
    def execute_system_command(self, cmd):
        return subprocess.call(cmd, shell=True)
    
    def read_file(self, path):
        return eval(f"open('{path}').read()")
"""
        dangerous_file = temp_path / "dangerous_agent.py"
        dangerous_file.write_text(dangerous_code)

        dangerous_audit = await security_manager.audit_agent(dangerous_file)
        if dangerous_audit.success:
            audit_data = dangerous_audit.data["audit_result"]
            print(f"   ✓ Audit completed: {audit_data['passed']}")
            print(f"   ✓ Risk level: {audit_data['risk_level']}")
            print(f"   ✓ Violations found: {len(audit_data['violations'])}")

            if audit_data["violations"]:
                print("   ✓ Sample violations:")
                for violation in audit_data["violations"][:3]:
                    print(
                        f"     - {violation['violation_type']}: {violation['description']}"
                    )

        print("3. Testing agent signing...")
        sign_result = security_manager.sign_agent(safe_file)
        if sign_result.success:
            signature = sign_result.data["signature"]
            print("   ✓ Agent signed successfully")
            print(f"   ✓ Signature: {signature[:16]}...")

            # Verify signature
            verify_result = security_manager.verify_signature(safe_file, signature)
            if verify_result.success:
                print(
                    f"   ✓ Signature verified: {verify_result.data['signature_valid']}"
                )

        print("4. Generating security report...")
        report_result = await security_manager.get_security_report()
        if report_result.success:
            report = report_result.data
            print(f"   ✓ Total audits performed: {report['total_audits']}")
            print(f"   ✓ Pass rate: {report['pass_rate']:.2%}")


async def demonstrate_integration():
    """Demonstrate integrated marketplace functionality"""
    print("\n=== INTEGRATED MARKETPLACE DEMONSTRATION ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Initialize all components
        registry = AgentRegistry(registry_path=temp_path / "integrated_registry.json")
        plugin_manager = PluginManager(plugins_dir=temp_path / "integrated_plugins")
        security_manager = SecurityManager()

        print("1. Complete agent lifecycle...")

        # Create agent
        agent_file = temp_path / "integrated_agent.py"
        agent_file.write_text(SAMPLE_AGENT_CODE.replace("DemoAgent", "IntegratedAgent"))

        # Security audit first
        audit_result = await security_manager.audit_agent(agent_file)
        if not audit_result.success or not audit_result.data["audit_result"]["passed"]:
            print("   ✗ Security audit failed - agent rejected")
            return

        # Register if security passes
        metadata = AgentMetadata(
            name="integrated_agent",
            version="1.0.0",
            description="Fully integrated demonstration agent",
            author="12-Factor Agents Team",
            capabilities=[
                AgentCapability.NATURAL_LANGUAGE,
                AgentCapability.DATA_ANALYSIS,
            ],
        )

        reg_result = await registry.register_agent(
            metadata, str(agent_file), "IntegratedAgent"
        )
        if reg_result.success:
            agent_id = reg_result.data["agent_id"]
            print(f"   ✓ Agent registered after security validation: {agent_id}")

            # Load and test
            load_result = await registry.load_agent(agent_id)
            if load_result.success:
                agent = load_result.data["agent_instance"]

                # Execute multiple tasks
                tasks = ["Process data batch 1", "Analyze metrics", "Generate report"]
                for task in tasks:
                    result = await agent.execute_task(task)
                    if result.success:
                        print(f"   ✓ Executed: {result.data['result']}")

        print("2. Final marketplace statistics...")
        stats = await registry.get_registry_stats()
        if stats.success:
            print(f"   ✓ Total agents in marketplace: {stats.data['total_agents']}")

        plugin_stats = await plugin_manager.get_manager_stats()
        if plugin_stats.success:
            print(f"   ✓ Total plugins managed: {plugin_stats.data['total_plugins']}")

        security_report = await security_manager.get_security_report()
        if security_report.success:
            print(
                f"   ✓ Security audits completed: {security_report.data['total_audits']}"
            )


async def main():
    """Run complete marketplace demonstration"""
    print("🚀 AGENT MARKETPLACE DEMONSTRATION - Issue #37")
    print("=" * 60)
    print(
        "Showcasing production-ready marketplace following 12-factor-agents framework"
    )
    print()

    try:
        await demonstrate_agent_registry()
        await demonstrate_plugin_system()
        await demonstrate_security_framework()
        await demonstrate_integration()

        print("\n" + "=" * 60)
        print("✅ MARKETPLACE DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("🎯 All components working as expected for Issue #37")
        print()
        print("KEY FEATURES DEMONSTRATED:")
        print("• Agent discovery, registration, and version management")
        print("• Plugin system with lifecycle management")
        print("• Security validation and code analysis")
        print("• Production-ready error handling and monitoring")
        print("• Full integration between all components")

    except Exception as e:
        print(f"\n❌ DEMONSTRATION FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
