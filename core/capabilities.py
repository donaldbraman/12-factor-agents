"""
Agent Capabilities Framework - Defines what each agent can and cannot do.
Used by IssueOrchestratorAgent to provide helpful routing feedback.
"""

from dataclasses import dataclass
from typing import List, Set, Optional, Dict, Any
from enum import Enum


class CapabilityType(Enum):
    """Types of capabilities agents can have"""

    READ_ONLY = "read_only"
    WRITE_FILES = "write_files"
    CREATE_FILES = "create_files"
    RUN_TESTS = "run_tests"
    FIX_BUGS = "fix_bugs"
    ANALYZE_CODE = "analyze_code"
    SETUP_INFRASTRUCTURE = "setup_infrastructure"
    REVIEW_CODE = "review_code"
    PROCESS_ISSUES = "process_issues"
    ORCHESTRATE = "orchestrate"
    MIGRATE_CODE = "migrate_code"
    GENERATE_DOCS = "generate_docs"


class IntentType(Enum):
    """Types of user intents that can be detected from issues"""

    FIX_TEST_FAILURE = "fix_test_failure"
    RUN_TESTS = "run_tests"
    CREATE_FEATURE = "create_feature"
    FIX_BUG = "fix_bug"
    CODE_REVIEW = "code_review"
    SETUP_PROJECT = "setup_project"
    MIGRATE_CODE = "migrate_code"
    IMPROVE_DOCS = "improve_docs"
    ANALYZE_PERFORMANCE = "analyze_performance"
    UNKNOWN = "unknown"


@dataclass
class AgentCapabilities:
    """
    Defines what an agent can and cannot do.
    Used for intelligent routing and mismatch detection.
    """

    agent_name: str
    primary_purpose: str
    can_read: bool = True
    can_write: bool = False
    can_create_files: bool = False
    can_run_tests: bool = False
    can_fix_bugs: bool = False
    can_analyze_code: bool = False
    can_setup_infrastructure: bool = False
    can_review_code: bool = False
    can_process_issues: bool = False
    can_orchestrate: bool = False
    can_migrate_code: bool = False
    can_generate_docs: bool = False

    # Specific strengths and limitations
    strengths: List[str] = None
    limitations: List[str] = None
    ideal_for: List[IntentType] = None
    not_suitable_for: List[IntentType] = None

    # Keywords that suggest this agent should be used
    trigger_keywords: Set[str] = None
    anti_keywords: Set[
        str
    ] = None  # Keywords that suggest this agent should NOT be used

    def __post_init__(self):
        """Initialize default values"""
        if self.strengths is None:
            self.strengths = []
        if self.limitations is None:
            self.limitations = []
        if self.ideal_for is None:
            self.ideal_for = []
        if self.not_suitable_for is None:
            self.not_suitable_for = []
        if self.trigger_keywords is None:
            self.trigger_keywords = set()
        if self.anti_keywords is None:
            self.anti_keywords = set()

    def get_capabilities(self) -> Set[CapabilityType]:
        """Get all capabilities this agent has"""
        capabilities = set()

        if self.can_read:
            capabilities.add(CapabilityType.READ_ONLY)
        if self.can_write:
            capabilities.add(CapabilityType.WRITE_FILES)
        if self.can_create_files:
            capabilities.add(CapabilityType.CREATE_FILES)
        if self.can_run_tests:
            capabilities.add(CapabilityType.RUN_TESTS)
        if self.can_fix_bugs:
            capabilities.add(CapabilityType.FIX_BUGS)
        if self.can_analyze_code:
            capabilities.add(CapabilityType.ANALYZE_CODE)
        if self.can_setup_infrastructure:
            capabilities.add(CapabilityType.SETUP_INFRASTRUCTURE)
        if self.can_review_code:
            capabilities.add(CapabilityType.REVIEW_CODE)
        if self.can_process_issues:
            capabilities.add(CapabilityType.PROCESS_ISSUES)
        if self.can_orchestrate:
            capabilities.add(CapabilityType.ORCHESTRATE)
        if self.can_migrate_code:
            capabilities.add(CapabilityType.MIGRATE_CODE)
        if self.can_generate_docs:
            capabilities.add(CapabilityType.GENERATE_DOCS)

        return capabilities

    def is_suitable_for_intent(self, intent: IntentType) -> bool:
        """Check if this agent is suitable for a given intent"""
        if intent in self.not_suitable_for:
            return False
        if intent in self.ideal_for:
            return True

        # Basic capability mapping
        intent_capability_map = {
            IntentType.FIX_TEST_FAILURE: {
                CapabilityType.FIX_BUGS,
                CapabilityType.WRITE_FILES,
            },
            IntentType.RUN_TESTS: {CapabilityType.RUN_TESTS},
            IntentType.CREATE_FEATURE: {
                CapabilityType.CREATE_FILES,
                CapabilityType.WRITE_FILES,
            },
            IntentType.FIX_BUG: {CapabilityType.FIX_BUGS, CapabilityType.WRITE_FILES},
            IntentType.CODE_REVIEW: {
                CapabilityType.REVIEW_CODE,
                CapabilityType.ANALYZE_CODE,
            },
            IntentType.SETUP_PROJECT: {
                CapabilityType.SETUP_INFRASTRUCTURE,
                CapabilityType.CREATE_FILES,
            },
            IntentType.MIGRATE_CODE: {
                CapabilityType.MIGRATE_CODE,
                CapabilityType.WRITE_FILES,
            },
            IntentType.IMPROVE_DOCS: {
                CapabilityType.GENERATE_DOCS,
                CapabilityType.WRITE_FILES,
            },
            IntentType.ANALYZE_PERFORMANCE: {CapabilityType.ANALYZE_CODE},
        }

        required_capabilities = intent_capability_map.get(intent, set())
        agent_capabilities = self.get_capabilities()

        # Check if agent has any of the required capabilities
        return len(required_capabilities.intersection(agent_capabilities)) > 0

    def matches_keywords(self, text: str) -> bool:
        """Check if the text contains keywords that suggest this agent"""
        text_lower = text.lower()

        # Check anti-keywords first (these override trigger keywords)
        if any(anti_keyword in text_lower for anti_keyword in self.anti_keywords):
            return False

        # Check trigger keywords
        return any(keyword in text_lower for keyword in self.trigger_keywords)

    def get_mismatch_reason(
        self, intent: IntentType, issue_text: str = ""
    ) -> Optional[str]:
        """Get reason why this agent is not suitable for the given intent"""
        if self.is_suitable_for_intent(intent):
            return None

        if intent in self.not_suitable_for:
            return (
                f"{self.agent_name} is explicitly not designed for {intent.value} tasks"
            )

        # Check for anti-keywords
        if issue_text:
            text_lower = issue_text.lower()
            for anti_keyword in self.anti_keywords:
                if anti_keyword in text_lower:
                    return f"{self.agent_name} is not suitable for issues involving '{anti_keyword}'"

        # Generic capability mismatch
        intent_capability_map = {
            IntentType.FIX_TEST_FAILURE: "fix failing tests and modify code",
            IntentType.RUN_TESTS: "run test suites",
            IntentType.CREATE_FEATURE: "create new files and features",
            IntentType.FIX_BUG: "fix bugs and modify existing code",
            IntentType.CODE_REVIEW: "review and analyze code quality",
            IntentType.SETUP_PROJECT: "setup infrastructure and create project structure",
            IntentType.MIGRATE_CODE: "migrate and refactor existing code",
            IntentType.IMPROVE_DOCS: "generate and improve documentation",
            IntentType.ANALYZE_PERFORMANCE: "analyze code performance",
        }

        required_action = intent_capability_map.get(intent, "handle this type of task")
        return f"{self.agent_name} cannot {required_action}"


# Pre-defined agent capabilities
AGENT_CAPABILITIES = {
    "TestingAgent": AgentCapabilities(
        agent_name="TestingAgent",
        primary_purpose="Run comprehensive test suites and validate code quality",
        can_read=True,
        can_write=False,  # Only runs tests, doesn't fix them
        can_create_files=True,  # Can create test files
        can_run_tests=True,
        can_fix_bugs=False,  # Critical: Cannot fix bugs
        can_analyze_code=True,
        strengths=[
            "Comprehensive test suite execution",
            "Unit and integration testing",
            "Code quality validation",
            "Test report generation",
        ],
        limitations=[
            "Cannot fix failing tests",
            "Cannot modify existing code",
            "Read-only analysis of test failures",
        ],
        ideal_for=[IntentType.RUN_TESTS],
        not_suitable_for=[IntentType.FIX_TEST_FAILURE, IntentType.FIX_BUG],
        trigger_keywords={"run tests", "test suite", "validate", "check quality"},
        anti_keywords={"fix", "failing", "broken", "error", "bug"},
    ),
    "IssueFixerAgent": AgentCapabilities(
        agent_name="IssueFixerAgent",
        primary_purpose="Fix bugs, resolve test failures, and modify existing code",
        can_read=True,
        can_write=True,
        can_create_files=True,
        can_run_tests=False,  # Doesn't run tests, but fixes them
        can_fix_bugs=True,
        can_analyze_code=True,
        strengths=[
            "Intelligent bug fixing",
            "Test failure resolution",
            "Code modification and refactoring",
            "Context-aware problem solving",
        ],
        limitations=[
            "Cannot run test suites",
            "Focuses on fixing rather than validation",
        ],
        ideal_for=[IntentType.FIX_TEST_FAILURE, IntentType.FIX_BUG],
        not_suitable_for=[IntentType.RUN_TESTS],
        trigger_keywords={"fix", "failing", "broken", "error", "bug", "resolve"},
        anti_keywords={"run tests", "validate", "check"},
    ),
    "CodeReviewAgent": AgentCapabilities(
        agent_name="CodeReviewAgent",
        primary_purpose="Review code quality, suggest improvements, and analyze code",
        can_read=True,
        can_write=False,  # Reviews but doesn't modify
        can_create_files=False,
        can_run_tests=False,
        can_fix_bugs=False,
        can_analyze_code=True,
        can_review_code=True,
        strengths=[
            "Code quality analysis",
            "Security vulnerability detection",
            "Best practice recommendations",
            "Architecture review",
        ],
        limitations=[
            "Cannot fix issues it identifies",
            "Read-only analysis",
            "Cannot run tests or modify code",
        ],
        ideal_for=[IntentType.CODE_REVIEW, IntentType.ANALYZE_PERFORMANCE],
        not_suitable_for=[
            IntentType.FIX_BUG,
            IntentType.FIX_TEST_FAILURE,
            IntentType.CREATE_FEATURE,
        ],
        trigger_keywords={"review", "analyze", "quality", "security", "performance"},
        anti_keywords={"fix", "create", "implement"},
    ),
    "IssueOrchestratorAgent": AgentCapabilities(
        agent_name="IssueOrchestratorAgent",
        primary_purpose="Orchestrate and coordinate other agents to resolve issues",
        can_read=True,
        can_write=False,  # Delegates to other agents
        can_create_files=False,
        can_run_tests=False,
        can_fix_bugs=False,
        can_analyze_code=False,
        can_orchestrate=True,
        can_process_issues=True,
        strengths=[
            "Multi-agent coordination",
            "Issue prioritization",
            "Dependency management",
            "Workflow orchestration",
        ],
        limitations=[
            "Cannot directly fix issues",
            "Relies on other agents for implementation",
            "Meta-level coordination only",
        ],
        ideal_for=[],  # Should not be directly assigned to issues
        not_suitable_for=[
            IntentType.FIX_TEST_FAILURE,
            IntentType.FIX_BUG,
            IntentType.RUN_TESTS,
        ],
        trigger_keywords={"orchestrate", "coordinate", "manage"},
        anti_keywords={"fix", "run", "create", "implement"},
    ),
    "RepositorySetupAgent": AgentCapabilities(
        agent_name="RepositorySetupAgent",
        primary_purpose="Setup project structure and initialize repositories",
        can_read=True,
        can_write=True,
        can_create_files=True,
        can_run_tests=False,
        can_fix_bugs=False,
        can_analyze_code=False,
        can_setup_infrastructure=True,
        strengths=[
            "Project initialization",
            "Directory structure creation",
            "Configuration file setup",
            "Repository scaffolding",
        ],
        limitations=[
            "Cannot fix existing code issues",
            "Focused on new project setup",
            "Cannot run tests",
        ],
        ideal_for=[IntentType.SETUP_PROJECT],
        not_suitable_for=[
            IntentType.FIX_TEST_FAILURE,
            IntentType.FIX_BUG,
            IntentType.RUN_TESTS,
        ],
        trigger_keywords={"setup", "initialize", "create project", "scaffold"},
        anti_keywords={"fix", "bug", "failing"},
    ),
}


def get_agent_capabilities(agent_name: str) -> Optional[AgentCapabilities]:
    """Get capabilities for a specific agent"""
    return AGENT_CAPABILITIES.get(agent_name)


def detect_intent_from_issue(
    title: str, description: str = "", labels: List[str] = None
) -> IntentType:
    """
    Detect user intent from issue title, description, and labels.
    This is used by IssueOrchestratorAgent to provide better routing feedback.
    """
    if labels is None:
        labels = []

    # Combine all text for analysis
    all_text = f"{title} {description} {' '.join(labels)}".lower()

    # Intent detection patterns (ordered by specificity - most specific first)
    intent_patterns = {
        IntentType.FIX_TEST_FAILURE: [
            "fix failing test",
            "fix test fail",
            "test fail",
            "failing test",
            "test error",
            "test break",
            "test not pass",
            "assertion error",
            "test suite fail",
            "unit test fail",
            "integration test fail",
            "fix test",
            "repair test",
        ],
        IntentType.CODE_REVIEW: [
            "review",
            "code review",
            "pr review",
            "pull request review",
            "analyze code",
            "code quality",
            "security review",
            "review security",
            "review vulnerabilities",
            "code analysis",
            "security analysis",
            "audit",
        ],
        IntentType.RUN_TESTS: [
            "run test",
            "execute test",
            "test suite",
            "run all tests",
            "validate tests",
            "check tests",
            "test execution",
            "run unit test",
            "run integration test",
        ],
        IntentType.ANALYZE_PERFORMANCE: [
            "performance",
            "optimize",
            "slow",
            "speed",
            "benchmark",
            "profile",
            "memory leak",
            "cpu usage",
            "memory usage",
            "performance analysis",
        ],
        IntentType.CREATE_FEATURE: [
            "create",
            "add new",
            "new feature",
            "implement",
            "build",
            "develop",
            "feature request",
            "enhancement",
            "add feature",
        ],
        IntentType.SETUP_PROJECT: [
            "setup",
            "initialize",
            "scaffold",
            "create project",
            "new project",
            "bootstrap",
            "init",
            "project setup",
        ],
        IntentType.MIGRATE_CODE: [
            "migrate",
            "migration",
            "upgrade",
            "refactor",
            "modernize",
            "convert",
            "port",
            "transition",
        ],
        IntentType.IMPROVE_DOCS: [
            "documentation",
            "docs",
            "readme",
            "guide",
            "manual",
            "wiki",
            "document",
            "explain",
            "write docs",
        ],
        IntentType.FIX_BUG: [
            "fix bug",
            "bug fix",
            "fix error",
            "fix problem",
            "fix broken",
            "resolve bug",
            "bug",
            "error",
            "fix",
            "broken",
            "not work",
            "issue",
            "problem",
            "exception",
            "crash",
            "fail",
            "debug",
        ],
    }

    # Check patterns in order of specificity
    for intent, patterns in intent_patterns.items():
        for pattern in patterns:
            if pattern in all_text:
                return intent

    return IntentType.UNKNOWN


def find_suitable_agents(intent: IntentType, issue_text: str = "") -> List[str]:
    """Find agents suitable for a given intent"""
    suitable_agents = []

    for agent_name, capabilities in AGENT_CAPABILITIES.items():
        if capabilities.is_suitable_for_intent(intent):
            # Check keyword matching for additional confidence
            if not issue_text or capabilities.matches_keywords(issue_text):
                suitable_agents.append(agent_name)

    return suitable_agents


def get_routing_mismatch_feedback(
    assigned_agent: str, intent: IntentType, issue_text: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Get feedback when there's a mismatch between assigned agent and detected intent.
    Returns None if no mismatch is detected.
    """
    capabilities = get_agent_capabilities(assigned_agent)
    if not capabilities:
        return {
            "mismatch_detected": True,
            "reason": f"Unknown agent: {assigned_agent}",
            "suggestions": [],
        }

    if capabilities.is_suitable_for_intent(intent):
        return None  # No mismatch

    mismatch_reason = capabilities.get_mismatch_reason(intent, issue_text)
    suitable_agents = find_suitable_agents(intent, issue_text)

    return {
        "mismatch_detected": True,
        "assigned_agent": assigned_agent,
        "detected_intent": intent.value,
        "reason": mismatch_reason,
        "suggested_agents": suitable_agents,
        "issue_context": {
            "intent_type": intent.value,
            "agent_purpose": capabilities.primary_purpose,
            "agent_limitations": capabilities.limitations,
        },
    }
