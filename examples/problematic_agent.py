"""
Deliberately problematic agent to test our 12-factor compliance validation system.

This agent violates multiple 12-factor principles to demonstrate how our 
validator system identifies issues and provides actionable recommendations.
"""

import json
from typing import Dict, Any
from core.agent import BaseAgent
from core.tools import ToolResponse
from core.execution_context import ExecutionContext

# Global state (violates multiple factors!)
GLOBAL_COUNTER = 0
GLOBAL_CACHE = {}


class ProblematicAgent(BaseAgent):
    """
    An agent that deliberately violates many 12-factor principles.
    Perfect for testing our compliance validation system!
    """

    def __init__(self):
        super().__init__()
        # No proper state management (violates Factor 5)
        self.random_data = {}
        self.execution_count = 0
        self.errors = []  # Separate error storage (violates Factor 5)
        self.business_data = {}  # Separate business storage (violates Factor 5)

        # No context management (violates Factor 3)
        # No tool registration (violates Factor 1, 4)
        # No human interaction tools (violates Factor 7)

    def register_tools(self):
        """No tools registered - violates Factor 1 and 4"""
        return []

    def _apply_action(self, action: dict) -> ToolResponse:
        """Basic action application without proper structure"""
        return ToolResponse(success=True, data=action)

    def execute_task(self, task: str, context: ExecutionContext = None) -> ToolResponse:
        """
        Execute task with many 12-factor violations:
        - Uses global state (violates Factor 8, 12)
        - No proper error handling (violates Factor 9)
        - Not stateless (violates Factor 12)
        - Mutates instance state (violates Factor 12)
        - No context window management (violates Factor 3)
        - Returns inconsistent output format (violates Factor 4)
        """
        global GLOBAL_COUNTER, GLOBAL_CACHE

        # Mutate global state (bad!)
        GLOBAL_COUNTER += 1

        # Mutate instance state (violates stateless principle)
        self.execution_count += 1
        self.random_data[task] = f"execution_{self.execution_count}"

        # No error compaction or handling (violates Factor 9)
        try:
            result = self._do_complex_work(task)

            # Store in global cache (bad!)
            GLOBAL_CACHE[task] = result

            # Inconsistent return format (violates Factor 4)
            if self.execution_count % 2 == 0:
                return {"success": True, "data": result}  # Wrong format!
            else:
                return ToolResponse(success=True, data=result)

        except Exception as e:
            # Verbose error without compaction (violates Factor 9)
            import traceback

            full_error = (
                f"MASSIVE ERROR DUMP:\n{traceback.format_exc()}\n"
                + f"Error details: {str(e)}\n"
                + "Stack trace follows with tons of unnecessary details that "
                + "waste context window space and don't help with debugging "
                + "because they're too verbose and unstructured..."
            )

            self.errors.append(full_error)  # Separate error storage (bad!)
            return ToolResponse(success=False, error=full_error)

    def _do_complex_work(self, task: str) -> Dict[str, Any]:
        """Simulate complex work that might fail"""
        if "fail" in task.lower():
            raise ValueError("Task failed as requested")

        # Access file system directly (not configurable)
        try:
            with open("/tmp/agent_data.txt", "w") as f:
                f.write(json.dumps({"task": task, "count": self.execution_count}))
        except Exception:
            pass  # Silent failure (bad!)

        return {
            "task": task,
            "global_counter": GLOBAL_COUNTER,
            "instance_counter": self.execution_count,
            "timestamp": "hardcoded_timestamp",  # Not dynamic (bad!)
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Status method that violates multiple principles:
        - No unified state (violates Factor 5)
        - No context management info (violates Factor 3)
        - No proper observability (violates Factor 5)
        """
        return {
            "execution_count": self.execution_count,
            "errors": len(self.errors),  # Separate error tracking (bad!)
            "global_counter": GLOBAL_COUNTER,  # Exposes global state (bad!)
            "cached_items": len(GLOBAL_CACHE),  # Exposes global state (bad!)
            "random_data_keys": list(self.random_data.keys()),
        }

    # Missing many factor implementations:
    # - No trigger mechanisms (violates Factor 11)
    # - No human interaction tools (violates Factor 7)
    # - No pause/resume capability (violates Factor 6)
    # - No prompt management (violates Factor 2)
    # - No context window management (violates Factor 3)
    # - No error compaction (violates Factor 9)
    # - Not small/focused (violates Factor 10) - does too many things


# Additional global functions that make the agent non-compliant
def reset_global_state():
    """Global function that agents might depend on (bad!)"""
    global GLOBAL_COUNTER, GLOBAL_CACHE
    GLOBAL_COUNTER = 0
    GLOBAL_CACHE = {}


def get_global_stats():
    """Another global dependency (bad!)"""
    return {"counter": GLOBAL_COUNTER, "cache_size": len(GLOBAL_CACHE)}


if __name__ == "__main__":
    # Test the problematic agent
    agent = ProblematicAgent()

    print("Testing ProblematicAgent...")

    # Execute some tasks
    result1 = agent.execute_task("normal task")
    print(f"Task 1 result: {result1}")

    result2 = agent.execute_task("another task")
    print(f"Task 2 result: {result2}")

    # Try a failing task
    result3 = agent.execute_task("fail this task")
    print(f"Task 3 result: {result3}")

    # Check status
    status = agent.get_status()
    print(f"Agent status: {status}")

    print(f"Global stats: {get_global_stats()}")
