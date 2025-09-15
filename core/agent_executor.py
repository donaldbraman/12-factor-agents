"""
Agent Execution Orchestrator
Manages agent discovery, execution, and orchestration for the CLI
"""

import json
import time
import importlib
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from concurrent.futures import ThreadPoolExecutor

from .agent import BaseAgent


class AgentExecutor:
    """Executes agents via CLI with uv integration"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.agents_dir = self.project_root / "agents"
        self.orchestration_dir = self.project_root / "orchestration"
        self._agent_cache = {}

    def discover_agents(self) -> Dict[str, Type[BaseAgent]]:
        """Discover all available agents in the agents directory"""
        agents = {}

        for file in self.agents_dir.glob("*_agent.py"):
            if file.name.startswith("__"):
                continue

            module_name = file.stem
            try:
                module = importlib.import_module(f"agents.{module_name}")

                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseAgent)
                        and obj != BaseAgent
                        and not name.startswith("_")
                    ):
                        agents[name] = obj

            except ImportError as e:
                print(f"⚠️  Could not import {module_name}: {e}")

        return agents

    def list_agents(self, verbose: bool = False) -> List[str]:
        """List all available agents"""
        agents = self.discover_agents()

        if not agents:
            return []

        print(f"\n📦 Available Agents ({len(agents)} found):")
        print("=" * 50)

        agent_list = []
        for name, agent_class in sorted(agents.items()):
            agent_list.append(name)

            if verbose:
                # Get docstring if available
                doc = inspect.getdoc(agent_class) or "No description available"
                first_line = doc.split("\n")[0]
                print(f"\n  🤖 {name}")
                print(f"     {first_line}")

                # Show available methods
                methods = [
                    m
                    for m in dir(agent_class)
                    if not m.startswith("_") and callable(getattr(agent_class, m))
                ]
                if methods:
                    print(f"     Methods: {', '.join(methods[:5])}")
            else:
                print(f"  🤖 {name}")

        print("\n💡 Use 'uv run agent info <name>' for detailed information")
        print("💡 Use 'uv run agent run <name> \"<task>\"' to execute an agent")

        return agent_list

    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific agent"""
        # Add alias support for Sparky
        if agent_name.lower() in ["sparky", "sparkyrocketsuit"]:
            agent_name = "IssueOrchestratorAgent"

        agents = self.discover_agents()

        if agent_name not in agents:
            return None

        agent_class = agents[agent_name]

        print(f"\n🤖 Agent: {agent_name}")
        print("=" * 50)

        # Get docstring
        doc = inspect.getdoc(agent_class) or "No description available"
        print(f"\n📝 Description:\n{doc}")

        # Get methods
        methods = []
        for method_name in dir(agent_class):
            if not method_name.startswith("_"):
                method = getattr(agent_class, method_name)
                if callable(method) and method_name != "execute_task":
                    methods.append(method_name)

        if methods:
            print("\n🔧 Available Methods:")
            for method in methods:
                print(f"  • {method}")

        # Get init parameters
        init_signature = inspect.signature(agent_class.__init__)
        params = [p for p in init_signature.parameters.keys() if p != "self"]
        if params:
            print("\n⚙️  Initialization Parameters:")
            for param in params:
                print(f"  • {param}")

        print(f'\n💡 Run with: uv run agent run {agent_name} "<your task>"')

        return {
            "name": agent_name,
            "class": agent_class,
            "docstring": doc,
            "methods": methods,
            "parameters": params,
        }

    def run_agent(self, agent_name: str, task: str, context: str = "{}") -> bool:
        """Run a specific agent with the given task"""
        # Add alias support for Sparky
        if agent_name.lower() in ["sparky", "sparkyrocketsuit"]:
            agent_name = "IssueOrchestratorAgent"

        agents = self.discover_agents()

        if agent_name not in agents:
            print(f"❌ Agent '{agent_name}' not found")
            print("💡 Run 'uv run agent list' to see available agents")
            return False

        try:
            # Parse context if provided
            context_dict = json.loads(context) if context != "{}" else {}

            # Instantiate and run agent
            agent_class = agents[agent_name]
            agent = agent_class()

            print(f"📋 Task: {task}")
            if context_dict:
                print(f"📎 Context: {context_dict}")
            print("-" * 50)

            # Execute the task
            result = agent.execute_task(task)

            # Display results
            if result:
                if isinstance(result, dict):
                    print("\n📊 Results:")
                    for key, value in result.items():
                        print(f"  • {key}: {value}")
                else:
                    print(f"\n📊 Result: {result}")

            return True

        except Exception as e:
            print(f"❌ Error executing agent: {e}")
            import traceback

            traceback.print_exc()
            return False

    def orchestrate(
        self, pipeline_name: str, config_path: Optional[Path] = None
    ) -> bool:
        """Run an orchestration pipeline"""
        try:
            # Try to import the orchestration module
            module = importlib.import_module(f"orchestration.{pipeline_name}")

            if hasattr(module, "run_pipeline"):
                print(f"🎭 Starting pipeline: {pipeline_name}")

                # Load config if provided
                config = {}
                if config_path and config_path.exists():
                    with open(config_path) as f:
                        config = json.load(f)
                    print(f"📋 Loaded configuration from {config_path}")

                # Run the pipeline
                result = module.run_pipeline(config)

                if result:
                    print(f"✅ Pipeline '{pipeline_name}' completed successfully")
                else:
                    print(f"⚠️  Pipeline '{pipeline_name}' completed with warnings")

                return True
            else:
                print(
                    f"❌ Pipeline '{pipeline_name}' does not have a run_pipeline function"
                )
                return False

        except ImportError:
            print(f"❌ Pipeline '{pipeline_name}' not found")
            print("💡 Available pipelines:")

            # List available pipelines
            if self.orchestration_dir.exists():
                for file in self.orchestration_dir.glob("*.py"):
                    if not file.name.startswith("__"):
                        print(f"  • {file.stem}")

            return False
        except Exception as e:
            print(f"❌ Error running pipeline: {e}")
            return False

    def execute(self, task_type: str, params: Dict[str, Any]) -> Any:
        """Execute single task (legacy compatibility)"""
        time.sleep(0.01)  # Simulate work
        return {"task": task_type, "result": "completed", "params": params}

    def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """Execute tasks in parallel (legacy compatibility)"""
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for task in tasks:
                future = executor.submit(self.execute, "process_task", task)
                futures.append(future)
            return [f.result() for f in futures]
