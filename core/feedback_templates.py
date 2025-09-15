"""
Feedback Templates for Agent Routing Mismatches.
Provides helpful, specific feedback when issues are routed to incorrect agents.
"""

from typing import Dict, Any, List
from .capabilities import IntentType, AGENT_CAPABILITIES


class FeedbackTemplate:
    """Template for generating helpful routing feedback"""

    def __init__(
        self, template: str, suggestions: List[str] = None, actions: List[str] = None
    ):
        self.template = template
        self.suggestions = suggestions or []
        self.actions = actions or []

    def format(self, **kwargs) -> Dict[str, Any]:
        """Format the template with provided context"""
        return {
            "message": self.template.format(**kwargs),
            "suggestions": [s.format(**kwargs) for s in self.suggestions],
            "recommended_actions": [a.format(**kwargs) for a in self.actions],
        }


# Common mismatch scenarios and their feedback templates
MISMATCH_TEMPLATES = {
    # TestingAgent receiving fix requests
    ("TestingAgent", "FIX_TEST_FAILURE"): FeedbackTemplate(
        template="🚫 **Routing Mismatch Detected**\n\n"
        "The issue '{issue_title}' appears to be about **fixing failing tests**, but it's been assigned to **TestingAgent**.\n\n"
        "**The Problem**: TestingAgent can only *run* tests and *validate* code quality - it cannot fix failing tests or modify code.\n\n"
        "**What TestingAgent Does**: \n"
        "✅ Runs comprehensive test suites\n"
        "✅ Validates code quality\n"
        "✅ Generates test reports\n\n"
        "**What TestingAgent Cannot Do**:\n"
        "❌ Fix failing tests\n"
        "❌ Modify existing code\n"
        "❌ Resolve test errors\n",
        suggestions=[
            "Assign this issue to **IssueFixerAgent** instead - it's specifically designed to fix failing tests and resolve code issues",
            "If you want to *run tests first* to understand the failures, you could create a separate issue for TestingAgent, then assign the fixing to IssueFixerAgent",
        ],
        actions=[
            "Update the issue's **Agent Assignment** section to: `IssueFixerAgent`",
            "Consider adding labels like `bug` or `test-failure` to make the intent clearer",
        ],
    ),
    ("TestingAgent", "FIX_BUG"): FeedbackTemplate(
        template="🚫 **Routing Mismatch Detected**\n\n"
        "The issue '{issue_title}' appears to be about **fixing a bug**, but it's been assigned to **TestingAgent**.\n\n"
        "**The Problem**: TestingAgent is read-only and cannot fix bugs or modify code - it can only run tests and analyze quality.\n",
        suggestions=[
            "Assign this issue to **IssueFixerAgent** - it's designed specifically for bug fixes and code modifications",
            "Use **CodeReviewAgent** first if you need to analyze the bug, then **IssueFixerAgent** to implement the fix",
        ],
        actions=[
            "Change the agent assignment to: `IssueFixerAgent`",
            "Add a `bug` label to make the intent clear",
        ],
    ),
    # IssueFixerAgent receiving test-only requests
    ("IssueFixerAgent", "RUN_TESTS"): FeedbackTemplate(
        template="🚫 **Routing Mismatch Detected**\n\n"
        "The issue '{issue_title}' appears to be about **running tests**, but it's been assigned to **IssueFixerAgent**.\n\n"
        "**The Problem**: IssueFixerAgent is designed to *fix* issues, not just run test suites for validation.\n\n"
        "**What IssueFixerAgent Does**: \n"
        "✅ Fixes failing tests\n"
        "✅ Resolves bugs in code\n"
        "✅ Modifies and creates files\n\n"
        "**For Just Running Tests**:\n"
        "Use **TestingAgent** instead - it's specialized for comprehensive test execution and validation.\n",
        suggestions=[
            "Assign this issue to **TestingAgent** instead - it's specifically designed to run comprehensive test suites",
            "If tests are *failing* and need to be *fixed*, then IssueFixerAgent is correct, but consider clarifying the issue title",
        ],
        actions=[
            "Change the agent assignment to: `TestingAgent`",
            "If the tests are failing, update the title to make it clear: 'Fix failing tests' instead of 'Run tests'",
        ],
    ),
    # CodeReviewAgent receiving modification requests
    ("CodeReviewAgent", "FIX_BUG"): FeedbackTemplate(
        template="🚫 **Routing Mismatch Detected**\n\n"
        "The issue '{issue_title}' appears to be about **fixing a bug**, but it's been assigned to **CodeReviewAgent**.\n\n"
        "**The Problem**: CodeReviewAgent is read-only and cannot fix bugs - it can only analyze code and provide recommendations.\n\n"
        "**What CodeReviewAgent Does**: \n"
        "✅ Analyzes code quality\n"
        "✅ Identifies security vulnerabilities\n"
        "✅ Suggests improvements\n\n"
        "**What CodeReviewAgent Cannot Do**:\n"
        "❌ Fix bugs\n"
        "❌ Modify existing code\n"
        "❌ Implement changes\n",
        suggestions=[
            "Use **IssueFixerAgent** to actually fix the bug",
            "If you want a code review *before* fixing, create two issues: one for CodeReviewAgent (analysis) and one for IssueFixerAgent (implementation)",
        ],
        actions=[
            "Change the agent assignment to: `IssueFixerAgent`",
            "Or split into two issues: 'Review code for bug analysis' (CodeReviewAgent) and 'Fix identified bug' (IssueFixerAgent)",
        ],
    ),
    ("CodeReviewAgent", "CREATE_FEATURE"): FeedbackTemplate(
        template="🚫 **Routing Mismatch Detected**\n\n"
        "The issue '{issue_title}' appears to be about **creating a new feature**, but it's been assigned to **CodeReviewAgent**.\n\n"
        "**The Problem**: CodeReviewAgent cannot create or implement features - it only reviews existing code.\n",
        suggestions=[
            "Use **IssueFixerAgent** to implement the new feature - it can create and modify files",
            "Consider using **RepositorySetupAgent** if this involves setting up new project structure",
        ],
        actions=[
            "Change the agent assignment to: `IssueFixerAgent`",
            "Add an `enhancement` or `feature` label to clarify the intent",
        ],
    ),
    # IssueOrchestratorAgent receiving direct work requests
    ("IssueOrchestratorAgent", "FIX_BUG"): FeedbackTemplate(
        template="🚫 **Routing Mismatch Detected**\n\n"
        "The issue '{issue_title}' appears to be about **fixing a bug**, but it's been assigned to **IssueOrchestratorAgent**.\n\n"
        "**The Problem**: IssueOrchestratorAgent (Sparky) is a meta-agent that coordinates other agents - it cannot directly fix bugs.\n\n"
        "**What IssueOrchestratorAgent Does**: \n"
        "✅ Coordinates multiple agents\n"
        "✅ Manages issue dependencies\n"
        "✅ Orchestrates complex workflows\n\n"
        "**For Direct Bug Fixes**:\n"
        "Assign to the appropriate specialist agent instead.\n",
        suggestions=[
            "Use **IssueFixerAgent** for direct bug fixes",
            "Only use IssueOrchestratorAgent for complex issues requiring multiple agents or dependency management",
        ],
        actions=[
            "Change the agent assignment to: `IssueFixerAgent`",
            "Reserve IssueOrchestratorAgent for multi-step workflows or issues with dependencies",
        ],
    ),
    # RepositorySetupAgent receiving maintenance requests
    ("RepositorySetupAgent", "FIX_BUG"): FeedbackTemplate(
        template="🚫 **Routing Mismatch Detected**\n\n"
        "The issue '{issue_title}' appears to be about **fixing a bug**, but it's been assigned to **RepositorySetupAgent**.\n\n"
        "**The Problem**: RepositorySetupAgent is designed for *new project setup*, not fixing existing code issues.\n\n"
        "**What RepositorySetupAgent Does**: \n"
        "✅ Initializes new projects\n"
        "✅ Creates directory structure\n"
        "✅ Sets up configuration files\n"
        "✅ Scaffolds new repositories\n\n"
        "**For Bug Fixes**:\n"
        "Use **IssueFixerAgent** instead.\n",
        suggestions=[
            "Assign to **IssueFixerAgent** for bug fixes in existing code",
            "Use RepositorySetupAgent only for initializing new projects or major structural changes",
        ],
        actions=[
            "Change the agent assignment to: `IssueFixerAgent`",
            "Use RepositorySetupAgent only for issues involving new project setup",
        ],
    ),
}


# Intent-specific guidance
INTENT_GUIDANCE = {
    IntentType.FIX_TEST_FAILURE: {
        "recommended_agent": "IssueFixerAgent",
        "description": "For fixing failing tests and resolving test errors",
        "wrong_agents": ["TestingAgent", "CodeReviewAgent"],
        "explanation": "TestingAgent can only *run* tests, not fix them. CodeReviewAgent can only analyze, not implement fixes.",
    },
    IntentType.RUN_TESTS: {
        "recommended_agent": "TestingAgent",
        "description": "For running comprehensive test suites and validation",
        "wrong_agents": ["IssueFixerAgent", "CodeReviewAgent"],
        "explanation": "IssueFixerAgent is for fixing, not just running tests. CodeReviewAgent doesn't run tests.",
    },
    IntentType.FIX_BUG: {
        "recommended_agent": "IssueFixerAgent",
        "description": "For fixing bugs and resolving code issues",
        "wrong_agents": ["TestingAgent", "CodeReviewAgent", "IssueOrchestratorAgent"],
        "explanation": "Only IssueFixerAgent can actually modify code to fix bugs. Other agents are read-only or coordinative.",
    },
    IntentType.CODE_REVIEW: {
        "recommended_agent": "CodeReviewAgent",
        "description": "For analyzing code quality and providing review feedback",
        "wrong_agents": ["IssueFixerAgent", "TestingAgent"],
        "explanation": "IssueFixerAgent focuses on implementation, TestingAgent on validation. CodeReviewAgent specializes in quality analysis.",
    },
    IntentType.CREATE_FEATURE: {
        "recommended_agent": "IssueFixerAgent",
        "description": "For implementing new features and creating functionality",
        "wrong_agents": ["TestingAgent", "CodeReviewAgent"],
        "explanation": "TestingAgent and CodeReviewAgent cannot create or modify code - only IssueFixerAgent can implement new features.",
    },
    IntentType.SETUP_PROJECT: {
        "recommended_agent": "RepositorySetupAgent",
        "description": "For initializing new projects and setting up infrastructure",
        "wrong_agents": ["IssueFixerAgent", "TestingAgent", "CodeReviewAgent"],
        "explanation": "RepositorySetupAgent specializes in project initialization and structural setup.",
    },
}


def generate_mismatch_feedback(
    assigned_agent: str, detected_intent: IntentType, issue_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate comprehensive feedback for agent routing mismatches"""

    # Get specific template if available
    template_key = (assigned_agent, detected_intent.name)
    if template_key in MISMATCH_TEMPLATES:
        template = MISMATCH_TEMPLATES[template_key]
        feedback = template.format(
            issue_title=issue_context.get("title", "Unknown Issue"),
            assigned_agent=assigned_agent,
            detected_intent=detected_intent.value,
        )
        return {"type": "specific_mismatch", "severity": "high", **feedback}

    # Generate generic feedback using intent guidance
    if detected_intent in INTENT_GUIDANCE:
        guidance = INTENT_GUIDANCE[detected_intent]

        message = "🚫 **Routing Mismatch Detected**\n\n"
        message += f"The issue '{issue_context.get('title', 'Unknown Issue')}' appears to be about **{detected_intent.value}**, "
        message += f"but it's been assigned to **{assigned_agent}**.\n\n"

        if assigned_agent in guidance["wrong_agents"]:
            message += f"**The Problem**: {guidance['explanation']}\n\n"

        message += f"**Recommended Agent**: {guidance['recommended_agent']}\n"
        message += f"**Why**: {guidance['description']}\n"

        return {
            "type": "generic_mismatch",
            "severity": "medium",
            "message": message,
            "suggestions": [
                f"Change the agent assignment to: `{guidance['recommended_agent']}`",
                f"Ensure the issue title and description clearly indicate the intent: {detected_intent.value}",
            ],
            "recommended_actions": [
                f"Update the **Agent Assignment** section to: `{guidance['recommended_agent']}`",
                "Consider adding appropriate labels to make the intent clearer",
            ],
        }

    # Fallback for unknown intents
    return {
        "type": "unknown_intent",
        "severity": "low",
        "message": f"⚠️ **Unclear Intent**\n\nCould not determine the specific intent of the issue '{issue_context.get('title', 'Unknown Issue')}'. "
        f"The assigned agent **{assigned_agent}** may or may not be appropriate.\n\n"
        f"**Suggestion**: Please clarify the issue title and description to make the intended action clear.",
        "suggestions": [
            "Make the issue title more specific about what needs to be done",
            "Add labels like 'bug', 'enhancement', 'test', etc. to clarify intent",
            "Include clear action words like 'fix', 'create', 'run', 'review' in the description",
        ],
        "recommended_actions": [
            "Review the issue title and description for clarity",
            "Add appropriate labels to indicate the type of work needed",
        ],
    }


def get_success_confirmation(assigned_agent: str, detected_intent: IntentType) -> str:
    """Generate confirmation message when routing is correct"""
    agent_capabilities = AGENT_CAPABILITIES.get(assigned_agent)
    if not agent_capabilities:
        return f"✅ Agent assignment confirmed: {assigned_agent}"

    return (
        f"✅ **Perfect Match!**\n\n"
        f"The issue has been correctly assigned to **{assigned_agent}**.\n\n"
        f"**Agent Purpose**: {agent_capabilities.primary_purpose}\n"
        f"**Detected Intent**: {detected_intent.value}\n\n"
        f"This agent is well-suited for this type of task."
    )
