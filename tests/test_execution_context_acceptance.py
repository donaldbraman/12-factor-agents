"""
Test to verify that all agents accept ExecutionContext parameter.
Related to Issue #85: Fix TestingAgent and other agents to accept ExecutionContext.
"""

import sys
from pathlib import Path
import inspect

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.execution_context import create_default_context
from core.agent import BaseAgent
import pytest


def test_agent_execute_task_signatures():
    """Test that all agents have execute_task methods with proper ExecutionContext parameter"""

    # Import all agent classes
    from agents.testing_agent import TestingAgent
    from agents.repository_setup_agent import RepositorySetupAgent
    from agents.event_system_agent import EventSystemAgent
    from agents.prompt_management_agent import PromptManagementAgent
    from agents.pr_review_agent import PRReviewAgent
    from agents.enhanced_workflow_agent import EnhancedWorkflowAgent
    from agents.failure_analysis_agent import FailureAnalysisAgent
    from agents.code_review_agent import CodeReviewAgent
    from agents.component_migration_agent import ComponentMigrationAgent
    from agents.issue_processor_agent import IssueProcessorAgent
    from agents.issue_decomposer_agent import IssueDecomposerAgent
    from agents.issue_fixer_agent import IssueFixerAgent
    from agents.smart_issue_agent import SmartIssueAgent
    from agents.uv_migration_agent import UvMigrationAgent
    from agents.pr_review_agent_simple import SimplePRReviewAgent
    from agents.issue_orchestrator_agent import IssueOrchestratorAgent
    from agents.intelligent_issue_agent import IntelligentIssueAgent

    # List of all agent classes to test
    agent_classes = [
        TestingAgent,
        RepositorySetupAgent,
        EventSystemAgent,
        PromptManagementAgent,
        PRReviewAgent,
        EnhancedWorkflowAgent,
        FailureAnalysisAgent,
        CodeReviewAgent,
        ComponentMigrationAgent,
        IssueProcessorAgent,
        IssueDecomposerAgent,
        IssueFixerAgent,
        SmartIssueAgent,
        UvMigrationAgent,
        SimplePRReviewAgent,
        IssueOrchestratorAgent,
        IntelligentIssueAgent,
    ]

    failed_agents = []

    for agent_class in agent_classes:
        # Check if execute_task method exists
        if not hasattr(agent_class, "execute_task"):
            failed_agents.append(f"{agent_class.__name__}: No execute_task method")
            continue

        # Get the method signature
        method = getattr(agent_class, "execute_task")
        sig = inspect.signature(method)

        # Check if it has the context parameter
        params = list(sig.parameters.keys())

        # Should have at least 'self', 'task', and 'context'
        if len(params) < 3:
            failed_agents.append(f"{agent_class.__name__}: Missing context parameter")
            continue

        # Check that second parameter is 'task' and third is 'context'
        if params[1] != "task":
            failed_agents.append(
                f"{agent_class.__name__}: Second parameter should be 'task', got '{params[1]}'"
            )
            continue

        if params[2] != "context":
            failed_agents.append(
                f"{agent_class.__name__}: Third parameter should be 'context', got '{params[2]}'"
            )
            continue

        # Check that context parameter has default value (should be None for Optional)
        context_param = sig.parameters["context"]
        if context_param.default is inspect.Parameter.empty:
            failed_agents.append(
                f"{agent_class.__name__}: context parameter should have default value (None)"
            )
        elif context_param.default is not None:
            failed_agents.append(
                f"{agent_class.__name__}: context parameter default should be None, got '{context_param.default}'"
            )

    if failed_agents:
        pytest.fail(
            "Agents with incorrect execute_task signatures:\n"
            + "\n".join(failed_agents)
        )


def test_agent_instantiation_and_context_usage():
    """Test that agents can be instantiated and accept ExecutionContext"""

    # Test a few representative agents
    from agents.testing_agent import TestingAgent
    from agents.repository_setup_agent import RepositorySetupAgent

    # Create execution context
    context = create_default_context()

    # Test TestingAgent
    testing_agent = TestingAgent()
    assert testing_agent is not None

    # Verify execute_task accepts context (we won't actually run the task)
    method = getattr(testing_agent, "execute_task")
    sig = inspect.signature(method)
    assert "context" in sig.parameters

    # Test RepositorySetupAgent
    repo_agent = RepositorySetupAgent()
    assert repo_agent is not None

    # Verify execute_task accepts context
    method = getattr(repo_agent, "execute_task")
    sig = inspect.signature(method)
    assert "context" in sig.parameters


def test_base_agent_signature_compliance():
    """Test that BaseAgent abstract method has correct signature"""

    # Get BaseAgent's execute_task signature
    method = getattr(BaseAgent, "execute_task")
    sig = inspect.signature(method)

    params = list(sig.parameters.keys())

    # Should have 'self', 'task', and 'context'
    assert (
        len(params) == 3
    ), f"BaseAgent.execute_task should have 3 parameters, got {len(params)}"
    assert params[0] == "self"
    assert params[1] == "task"
    assert params[2] == "context"

    # Check context parameter type annotation
    context_param = sig.parameters["context"]
    assert context_param.default is None  # Optional parameter


if __name__ == "__main__":
    test_agent_execute_task_signatures()
    test_agent_instantiation_and_context_usage()
    test_base_agent_signature_compliance()
    print("✅ All tests passed! All agents properly accept ExecutionContext.")
