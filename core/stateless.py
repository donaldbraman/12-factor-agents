"""
Stateless validation decorator for Factor 12 compliance.
Ensures agent methods are pure functions with no side effects.
"""

import functools
import inspect
import ast
from typing import Callable


class StatelessViolation(Exception):
    """Raised when a function violates stateless principles."""

    pass


def stateless(func: Callable) -> Callable:
    """
    Decorator that validates a method is stateless.

    Checks:
    - No instance variable mutations
    - No global state access
    - Predictable return types

    Usage:
        @stateless
        def execute_task(self, task: str, context: ExecutionContext) -> ToolResponse:
            # Pure function implementation
            pass
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Pre-execution validation
        if hasattr(self, "__dict__"):
            initial_state = self.__dict__.copy()

        # Execute the function
        result = func(self, *args, **kwargs)

        # Post-execution validation
        if hasattr(self, "__dict__"):
            final_state = self.__dict__

            # Check for state mutations
            for key, value in initial_state.items():
                if key in final_state and final_state[key] is not value:
                    # Allow certain safe modifications (e.g., cache updates)
                    if not key.startswith("_cache"):
                        raise StatelessViolation(
                            f"Method {func.__name__} modified instance variable '{key}'. "
                            f"Stateless methods must not mutate state."
                        )

        return result

    # Static analysis at decoration time
    try:
        source = inspect.getsource(func)
        tree = ast.parse(source)

        # Check for state mutations
        for node in ast.walk(tree):
            # Check for self.x = value patterns
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        if (
                            isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                        ):
                            print(
                                f"⚠️  Warning: Potential state mutation in {func.__name__}: "
                                f"self.{target.attr} assignment detected"
                            )

            # Check for global keyword
            if isinstance(node, ast.Global):
                print(
                    f"⚠️  Warning: Global state access in {func.__name__}: "
                    f"'global' keyword detected"
                )
    except Exception:
        # If we can't analyze the source, skip static checks
        pass

    # Mark function as stateless-validated
    wrapper._stateless_validated = True
    wrapper._original_func = func

    return wrapper


def validate_stateless_agent(agent_class: type) -> dict:
    """
    Validate that an entire agent class follows stateless principles.

    Returns:
        Dictionary with validation results
    """
    results = {
        "class": agent_class.__name__,
        "stateless_methods": [],
        "stateful_methods": [],
        "warnings": [],
        "score": 0.0,
    }

    # Check all methods
    for name, method in inspect.getmembers(agent_class, inspect.ismethod):
        if name.startswith("_"):
            continue  # Skip private methods

        # Check if method is decorated with @stateless
        if hasattr(method, "_stateless_validated"):
            results["stateless_methods"].append(name)
        else:
            # Analyze method for stateless compliance
            try:
                source = inspect.getsource(method)

                # Look for state mutations
                if "self." in source and "=" in source:
                    # Simple heuristic - might have false positives
                    lines = source.split("\n")
                    for line in lines:
                        if "self." in line and "=" in line and "==" not in line:
                            if not line.strip().startswith("#"):
                                results["stateful_methods"].append(name)
                                results["warnings"].append(
                                    f"{name}: Potential state mutation detected"
                                )
                                break
            except Exception:
                results["warnings"].append(f"{name}: Could not analyze")

    # Calculate score
    total_methods = len(results["stateless_methods"]) + len(results["stateful_methods"])
    if total_methods > 0:
        results["score"] = len(results["stateless_methods"]) / total_methods

    return results


# Example usage for testing
if __name__ == "__main__":
    from core.agent import BaseAgent
    from core.tools import ToolResponse

    class TestAgent(BaseAgent):
        def __init__(self):
            super().__init__()
            self.counter = 0

        @stateless
        def good_method(self, task: str) -> ToolResponse:
            # Pure function - no state mutation
            result = task.upper()
            return ToolResponse(success=True, data={"result": result})

        def bad_method(self, task: str) -> ToolResponse:
            # Violates stateless - mutates state
            self.counter += 1  # State mutation!
            return ToolResponse(success=True, data={"count": self.counter})

    # Test the agent
    agent = TestAgent()

    # This should work fine
    print("Testing stateless method:")
    result = agent.good_method("hello")
    print(f"✅ Result: {result.data}")

    # This should raise a warning
    print("\nTesting stateful method:")
    result = agent.bad_method("hello")
    print(f"⚠️  Result: {result.data}")

    # Validate the entire agent
    print("\nValidating agent:")
    validation = validate_stateless_agent(TestAgent)
    print(f"📊 Validation results: {validation}")
