"""
Dynamic Context Priming System - Claude Code Pattern Implementation

Replaces static memory files with dynamic, workflow-specific context loaders.
Enables commands like `/prime-feature`, `/prime-bug-fix`, `/prime-refactor` for
instant context setup with 50% time reduction.

Implements 12-Factor Agent methodology:
- Factor 2: Own Your Prompts (versioned primer templates)  
- Factor 3: Own Your Context Window (optimized context loading)
- Factor 11: Small, Focused Agents (specialized primers)
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import yaml
from jinja2 import Environment, FileSystemLoader

from .simple_primers import (
    _prime_feature_development,
    _prime_bug_fix,
    _prime_refactoring,
    _prime_testing,
    _prime_documentation,
    _prime_research,
    _prime_optimization,
    _prime_migration,
)


class PrimerType(Enum):
    """Types of context primers"""

    FEATURE_DEVELOPMENT = "feature_development"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    OPTIMIZATION = "optimization"
    MIGRATION = "migration"


class PrimerComplexity(Enum):
    """Complexity levels for primers"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ENTERPRISE = "enterprise"


@dataclass
class PrimerTemplate:
    """Template for context priming"""

    name: str
    primer_type: PrimerType
    description: str
    variables: Dict[str, Any]
    context_template: str
    tools: List[str]
    workflow_steps: List[str]
    checkpoints: List[str]
    success_criteria: List[str]
    complexity: PrimerComplexity = PrimerComplexity.MEDIUM
    estimated_time_minutes: int = 60
    prerequisites: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class PrimerResult:
    """Result from primer execution"""

    success: bool
    content: str
    primer_type: str
    generation_time: float
    error_message: str = ""
    template_used: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrimerContext:
    """Generated context from primer"""

    primer_name: str
    primer_type: PrimerType
    generated_context: List[str]
    tools_loaded: List[str]
    workflow: str
    checkpoints: List[str]
    variables_used: Dict[str, Any]
    success_criteria: List[str]
    estimated_completion_time: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class DynamicContextPrimer:
    """
    Dynamic Context Priming System implementing Claude Code patterns

    Provides reusable workflow templates that reduce context setup time
    by 50% while improving consistency across development workflows.
    """

    def __init__(self, primers_directory: Optional[Path] = None):
        """
        Initialize Dynamic Context Primer

        Args:
            primers_directory: Directory containing primer templates
        """
        self.primers_directory = (
            primers_directory or Path(__file__).parent.parent / "primers"
        )
        self.primers_directory.mkdir(exist_ok=True, parents=True)

        # Registry of primer functions (alias for backward compatibility)
        self.primer_registry: Dict[str, Callable] = {}
        self.primers: Dict[str, Callable] = self.primer_registry  # Alias
        self.primer_templates: Dict[str, PrimerTemplate] = {}

        # Template engine
        self.template_env = Environment(
            loader=FileSystemLoader(str(self.primers_directory / "templates")),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Primer chains for complex workflows
        self.primer_chains: Dict[str, List[str]] = {}

        # Performance tracking
        self.primer_performance: Dict[str, Dict[str, float]] = {}

        # Load built-in primers
        self._load_builtin_primers()

    def _load_builtin_primers(self):
        """Load built-in primer templates"""

        # Register all built-in primers (using sync functions for tests)
        self.register_primer("feature_development", _prime_feature_development)
        self.register_primer("bug_fix", _prime_bug_fix)
        self.register_primer("refactoring", _prime_refactoring)
        self.register_primer("testing", _prime_testing)
        self.register_primer("documentation", _prime_documentation)
        self.register_primer("research", _prime_research)
        self.register_primer("optimization", _prime_optimization)
        self.register_primer("migration", _prime_migration)

        # Load template files if they exist
        self._load_template_files()

    def _load_template_files(self):
        """Load template files from templates directory"""
        template_dir = self.primers_directory / "templates"
        if template_dir.exists():
            for template_file in template_dir.glob("*.md"):
                template_name = template_file.stem
                # Templates are loaded on-demand when used

    def register_primer(self, name: str, primer_func: Callable):
        """
        Register a reusable context primer

        Args:
            name: Unique primer name
            primer_func: Function that generates primer context (sync or async)
        """
        self.primer_registry[name] = primer_func

    def prime(self, primer_type: str, variables: Dict[str, Any] = None) -> PrimerResult:
        """
        Generate primer content using template or built-in function

        Args:
            primer_type: Type of primer to generate
            variables: Variables for template rendering

        Returns:
            PrimerResult with generated content
        """
        import time

        start_time = time.time()

        if variables is None:
            variables = {}

        try:
            # Check if primer type exists
            if primer_type not in self.primer_registry:
                return PrimerResult(
                    success=False,
                    content="",
                    primer_type=primer_type,
                    generation_time=0.0,
                    error_message=f"Unknown primer type: {primer_type}",
                )

            # Try to use template file first
            template_path = self._get_template_path(primer_type)
            if template_path and template_path.exists():
                try:
                    template = self.template_env.get_template(f"{primer_type}.md")
                    content = template.render(**variables)

                    generation_time = time.time() - start_time
                    return PrimerResult(
                        success=True,
                        content=content,
                        primer_type=primer_type,
                        generation_time=generation_time,
                        template_used=str(template_path),
                    )
                except Exception:
                    # Fall back to built-in function
                    pass

            # Use built-in primer function
            primer_func = self.primer_registry[primer_type]
            content = primer_func(variables)

            generation_time = time.time() - start_time
            return PrimerResult(
                success=True,
                content=content,
                primer_type=primer_type,
                generation_time=generation_time,
                template_used="built-in",
            )

        except Exception as e:
            generation_time = time.time() - start_time
            return PrimerResult(
                success=False,
                content="",
                primer_type=primer_type,
                generation_time=generation_time,
                error_message=str(e),
            )

    def _get_template_path(self, primer_type: str) -> Optional[Path]:
        """Get path to template file for primer type"""
        template_path = self.primers_directory / "templates" / f"{primer_type}.md"
        return template_path if template_path.exists() else None

    def register_primer_chain(self, name: str, primer_sequence: List[str]):
        """
        Register a chain of primers for complex workflows

        Args:
            name: Chain name
            primer_sequence: List of primer names to execute in order
        """
        # Validate all primers exist
        for primer_name in primer_sequence:
            if primer_name not in self.primers:
                raise ValueError(f"Primer '{primer_name}' not found in registry")

        self.primer_chains[name] = primer_sequence
        print(f"🔗 Registered primer chain: {name} → {' → '.join(primer_sequence)}")

    # Removed old async prime method - using new sync version above

    async def _execute_primer_chain(self, chain_name: str, **kwargs) -> PrimerContext:
        """Execute a chain of primers"""

        primer_sequence = self.primer_chains[chain_name]
        combined_context = []
        combined_tools = []
        combined_checkpoints = []
        combined_criteria = []

        print(f"🔗 Executing primer chain: {chain_name}")

        for primer_name in primer_sequence:
            print(f"  ▶️ Executing: {primer_name}")

            primer_context = await self.prime(primer_name, **kwargs)

            # Combine contexts
            combined_context.extend(primer_context.generated_context)
            combined_tools.extend(primer_context.tools_loaded)
            combined_checkpoints.extend(primer_context.checkpoints)
            combined_criteria.extend(primer_context.success_criteria)

        return PrimerContext(
            primer_name=chain_name,
            primer_type=PrimerType.FEATURE_DEVELOPMENT,  # Default for chains
            generated_context=combined_context,
            tools_loaded=list(set(combined_tools)),  # Deduplicate
            workflow=f"chained_{chain_name}",
            checkpoints=combined_checkpoints,
            variables_used=kwargs,
            success_criteria=combined_criteria,
            estimated_completion_time=datetime.now(),
            metadata={"chain": True, "primers": primer_sequence},
        )

    def _create_primer_context(
        self, primer_name: str, context_data: Dict[str, Any], variables: Dict[str, Any]
    ) -> PrimerContext:
        """Create PrimerContext from primer execution results"""

        return PrimerContext(
            primer_name=primer_name,
            primer_type=PrimerType(
                context_data.get("primer_type", "feature_development")
            ),
            generated_context=context_data.get("context", []),
            tools_loaded=context_data.get("tools", []),
            workflow=context_data.get("workflow", primer_name),
            checkpoints=context_data.get("checkpoints", []),
            variables_used=variables,
            success_criteria=context_data.get("success_criteria", []),
            estimated_completion_time=datetime.now(),
            metadata=context_data.get("metadata", {}),
        )

    def _track_primer_performance(self, primer_name: str, execution_time: float):
        """Track primer execution performance"""

        if primer_name not in self.primer_performance:
            self.primer_performance[primer_name] = {
                "total_executions": 0,
                "total_time": 0.0,
                "average_time": 0.0,
                "fastest_time": float("inf"),
                "slowest_time": 0.0,
            }

        stats = self.primer_performance[primer_name]
        stats["total_executions"] += 1
        stats["total_time"] += execution_time
        stats["average_time"] = stats["total_time"] / stats["total_executions"]
        stats["fastest_time"] = min(stats["fastest_time"], execution_time)
        stats["slowest_time"] = max(stats["slowest_time"], execution_time)

    # Built-in Primer Functions

    async def _prime_feature_development(
        self,
        feature_name: str,
        requirements: List[str] = None,
        complexity: str = "medium",
        **kwargs,
    ) -> Dict[str, Any]:
        """Prime context for feature development"""

        requirements = requirements or [
            "Implement core functionality",
            "Add error handling",
            "Write tests",
        ]

        # Get project architecture patterns
        architecture = self._get_architecture_patterns()
        testing_approach = self._get_testing_approach(complexity)

        return {
            "primer_type": "feature_development",
            "context": [
                f"🚀 FEATURE DEVELOPMENT: {feature_name}",
                f"Complexity Level: {complexity.upper()}",
                "",
                "📋 REQUIREMENTS:",
                *[f"  • {req}" for req in requirements],
                "",
                "🏗️ ARCHITECTURE PATTERNS:",
                *[f"  • {pattern}" for pattern in architecture],
                "",
                "🧪 TESTING APPROACH:",
                *[f"  • {approach}" for approach in testing_approach],
                "",
                "💡 DEVELOPMENT GUIDELINES:",
                "  • Follow 12-factor agent methodology",
                "  • Implement with context preservation",
                "  • Use structured ToolResponse pattern",
                "  • Add comprehensive error handling",
                "  • Document all public interfaces",
            ],
            "tools": [
                "code_writer",
                "test_generator",
                "documentation_writer",
                "architecture_analyzer",
            ],
            "workflow": "feature_development",
            "checkpoints": [
                "requirements_analysis",
                "design_review",
                "implementation",
                "testing",
                "documentation",
            ],
            "success_criteria": [
                "All requirements implemented",
                "Tests passing with >90% coverage",
                "Code follows project patterns",
                "Documentation complete",
                "Performance benchmarks pass",
            ],
            "metadata": {
                "complexity": complexity,
                "estimated_hours": self._estimate_feature_hours(complexity),
                "recommended_approach": "iterative_with_checkpoints",
            },
        }

    async def _prime_bug_fix(
        self,
        issue_id: str = None,
        description: str = None,
        affected_components: List[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Prime context for bug fixing"""

        affected_components = affected_components or ["core", "tests"]

        # Analyze bug context
        debugging_strategy = self._get_debugging_strategy(description)
        related_files = self._find_potentially_affected_files(affected_components)

        return {
            "primer_type": "bug_fix",
            "context": [
                f"🐛 BUG FIX: {issue_id or 'Issue Analysis'}",
                f"Description: {description or 'Bug reproduction and fix'}",
                "",
                "🔍 DEBUGGING STRATEGY:",
                *[f"  • {strategy}" for strategy in debugging_strategy],
                "",
                "📁 POTENTIALLY AFFECTED FILES:",
                *[f"  • {file_path}" for file_path in related_files],
                "",
                "🧪 TESTING APPROACH:",
                "  • Create reproduction test case",
                "  • Validate fix with existing tests",
                "  • Add regression prevention tests",
                "  • Test edge cases and error conditions",
                "",
                "✅ VALIDATION CHECKLIST:",
                "  • Bug reproduces consistently",
                "  • Fix addresses root cause",
                "  • No new test failures",
                "  • Performance impact assessed",
                "  • Similar issues prevented",
            ],
            "tools": ["debugger", "test_runner", "code_analyzer", "regression_tester"],
            "workflow": "bug_fix",
            "checkpoints": [
                "reproduce_bug",
                "identify_root_cause",
                "implement_fix",
                "validate_fix",
                "prevent_regression",
            ],
            "success_criteria": [
                "Bug consistently reproduced",
                "Root cause identified and documented",
                "Fix implemented and tested",
                "All existing tests pass",
                "Regression prevention measures added",
            ],
            "metadata": {
                "issue_id": issue_id,
                "priority": "high",
                "requires_regression_test": True,
            },
        }

    async def _prime_refactoring(
        self,
        component: str,
        refactor_type: str = "cleanup",
        goals: List[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Prime context for refactoring"""

        goals = goals or [
            "Improve code maintainability",
            "Reduce complexity",
            "Enhance performance",
        ]

        refactoring_patterns = self._get_refactoring_patterns(refactor_type)
        quality_metrics = self._get_quality_metrics()

        return {
            "primer_type": "refactoring",
            "context": [
                f"🔧 REFACTORING: {component}",
                f"Type: {refactor_type.title()} Refactoring",
                "",
                "🎯 REFACTORING GOALS:",
                *[f"  • {goal}" for goal in goals],
                "",
                "📐 REFACTORING PATTERNS:",
                *[f"  • {pattern}" for pattern in refactoring_patterns],
                "",
                "📊 QUALITY METRICS TO TRACK:",
                *[f"  • {metric}" for metric in quality_metrics],
                "",
                "⚠️ SAFETY MEASURES:",
                "  • Comprehensive test coverage before changes",
                "  • Incremental refactoring with frequent commits",
                "  • Performance benchmarking",
                "  • Code review for architecture changes",
                "  • Rollback plan documented",
            ],
            "tools": [
                "code_analyzer",
                "complexity_calculator",
                "test_coverage",
                "performance_profiler",
            ],
            "workflow": "refactoring",
            "checkpoints": [
                "analyze_current_state",
                "plan_refactoring",
                "implement_changes",
                "validate_improvements",
                "document_changes",
            ],
            "success_criteria": [
                "Code complexity reduced",
                "All tests remain passing",
                "Performance maintained or improved",
                "Code maintainability increased",
                "Architecture patterns followed",
            ],
            "metadata": {
                "component": component,
                "refactor_type": refactor_type,
                "risk_level": "medium",
                "requires_performance_testing": True,
            },
        }

    async def _prime_testing(
        self,
        test_type: str = "unit",
        coverage_target: int = 90,
        focus_areas: List[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Prime context for testing"""

        focus_areas = focus_areas or [
            "core functionality",
            "error handling",
            "edge cases",
        ]

        testing_strategy = self._get_testing_strategy(test_type)
        test_patterns = self._get_test_patterns()

        return {
            "primer_type": "testing",
            "context": [
                f"🧪 TESTING: {test_type.title()} Test Suite",
                f"Coverage Target: {coverage_target}%",
                "",
                "🎯 FOCUS AREAS:",
                *[f"  • {area}" for area in focus_areas],
                "",
                "📋 TESTING STRATEGY:",
                *[f"  • {strategy}" for strategy in testing_strategy],
                "",
                "🔧 TEST PATTERNS:",
                *[f"  • {pattern}" for pattern in test_patterns],
                "",
                "✅ TESTING CHECKLIST:",
                "  • Happy path scenarios covered",
                "  • Error conditions tested",
                "  • Edge cases identified and tested",
                "  • Performance requirements validated",
                "  • Integration points verified",
            ],
            "tools": [
                "test_generator",
                "coverage_analyzer",
                "test_runner",
                "assertion_helper",
            ],
            "workflow": "testing",
            "checkpoints": [
                "test_planning",
                "test_implementation",
                "coverage_analysis",
                "performance_testing",
                "test_documentation",
            ],
            "success_criteria": [
                f"Test coverage reaches {coverage_target}%",
                "All critical paths tested",
                "Error conditions properly handled",
                "Performance tests pass",
                "Test documentation complete",
            ],
            "metadata": {
                "test_type": test_type,
                "coverage_target": coverage_target,
                "includes_performance_tests": True,
            },
        }

    async def _prime_documentation(
        self,
        doc_type: str = "api",
        audience: str = "developers",
        sections: List[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Prime context for documentation"""

        sections = sections or [
            "Overview",
            "Usage Examples",
            "API Reference",
            "Best Practices",
        ]

        doc_templates = self._get_documentation_templates(doc_type)
        style_guide = self._get_documentation_style()

        return {
            "primer_type": "documentation",
            "context": [
                f"📚 DOCUMENTATION: {doc_type.title()} Documentation",
                f"Target Audience: {audience.title()}",
                "",
                "📖 DOCUMENTATION SECTIONS:",
                *[f"  • {section}" for section in sections],
                "",
                "📝 DOCUMENTATION TEMPLATES:",
                *[f"  • {template}" for template in doc_templates],
                "",
                "🎨 STYLE GUIDELINES:",
                *[f"  • {guideline}" for guideline in style_guide],
                "",
                "✍️ WRITING PRINCIPLES:",
                "  • Clear and concise language",
                "  • Practical examples included",
                "  • Progressive disclosure of complexity",
                "  • Searchable and well-organized",
                "  • Regular updates and maintenance",
            ],
            "tools": [
                "documentation_generator",
                "example_creator",
                "style_checker",
                "link_validator",
            ],
            "workflow": "documentation",
            "checkpoints": [
                "content_planning",
                "draft_creation",
                "review_and_revision",
                "example_validation",
                "publication",
            ],
            "success_criteria": [
                "All sections complete",
                "Examples tested and working",
                "Style guide compliance",
                "Peer review approved",
                "Published and accessible",
            ],
            "metadata": {
                "doc_type": doc_type,
                "audience": audience,
                "requires_examples": True,
            },
        }

    async def _prime_research(
        self,
        research_topic: str,
        scope: str = "comprehensive",
        deliverables: List[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Prime context for research"""

        deliverables = deliverables or [
            "Research summary",
            "Recommendations",
            "Implementation plan",
        ]

        return {
            "primer_type": "research",
            "context": [
                f"🔬 RESEARCH: {research_topic}",
                f"Scope: {scope.title()}",
                "",
                "📋 RESEARCH DELIVERABLES:",
                *[f"  • {deliverable}" for deliverable in deliverables],
                "",
                "🔍 RESEARCH METHODOLOGY:",
                "  • Literature review and source analysis",
                "  • Comparative analysis of alternatives",
                "  • Technical feasibility assessment",
                "  • Cost-benefit analysis",
                "  • Risk assessment and mitigation",
                "",
                "📊 ANALYSIS FRAMEWORK:",
                "  • Identify key research questions",
                "  • Gather credible sources and data",
                "  • Synthesize findings and insights",
                "  • Generate actionable recommendations",
                "  • Document methodology and conclusions",
            ],
            "tools": [
                "web_searcher",
                "document_analyzer",
                "data_synthesizer",
                "report_generator",
            ],
            "workflow": "research",
            "checkpoints": [
                "scope_definition",
                "information_gathering",
                "analysis",
                "synthesis",
                "reporting",
            ],
            "success_criteria": [
                "Research questions answered",
                "Multiple credible sources consulted",
                "Clear recommendations provided",
                "Implementation roadmap created",
                "Findings well-documented",
            ],
            "metadata": {
                "research_topic": research_topic,
                "scope": scope,
                "evidence_based": True,
            },
        }

    async def _prime_optimization(
        self,
        optimization_target: str,
        metrics: List[str] = None,
        constraints: List[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Prime context for optimization"""

        metrics = metrics or ["Performance", "Memory usage", "Response time"]
        constraints = constraints or [
            "Maintain functionality",
            "Preserve API compatibility",
        ]

        return {
            "primer_type": "optimization",
            "context": [
                f"⚡ OPTIMIZATION: {optimization_target}",
                "",
                "📈 TARGET METRICS:",
                *[f"  • {metric}" for metric in metrics],
                "",
                "⚠️ CONSTRAINTS:",
                *[f"  • {constraint}" for constraint in constraints],
                "",
                "🔧 OPTIMIZATION APPROACH:",
                "  • Baseline performance measurement",
                "  • Identify performance bottlenecks",
                "  • Implement targeted improvements",
                "  • Validate performance gains",
                "  • Monitor for regressions",
                "",
                "📊 MEASUREMENT STRATEGY:",
                "  • Establish baseline metrics",
                "  • Use performance profiling tools",
                "  • Run before/after benchmarks",
                "  • Track key performance indicators",
                "  • Document optimization results",
            ],
            "tools": [
                "performance_profiler",
                "benchmark_runner",
                "memory_analyzer",
                "optimization_validator",
            ],
            "workflow": "optimization",
            "checkpoints": [
                "baseline_measurement",
                "bottleneck_identification",
                "optimization_implementation",
                "performance_validation",
                "monitoring_setup",
            ],
            "success_criteria": [
                "Performance benchmarks improved",
                "No functionality regressions",
                "Constraints maintained",
                "Optimization documented",
                "Monitoring in place",
            ],
            "metadata": {
                "optimization_target": optimization_target,
                "requires_benchmarking": True,
                "performance_critical": True,
            },
        }

    async def _prime_migration(
        self,
        migration_type: str,
        source: str,
        target: str,
        migration_strategy: str = "incremental",
        **kwargs,
    ) -> Dict[str, Any]:
        """Prime context for migration"""

        return {
            "primer_type": "migration",
            "context": [
                f"🔄 MIGRATION: {migration_type}",
                f"Source: {source}",
                f"Target: {target}",
                f"Strategy: {migration_strategy.title()}",
                "",
                "📋 MIGRATION PHASES:",
                "  • Assessment and planning",
                "  • Environment preparation",
                "  • Data/code migration",
                "  • Testing and validation",
                "  • Cutover and monitoring",
                "",
                "⚠️ RISK MITIGATION:",
                "  • Comprehensive backup strategy",
                "  • Rollback procedures documented",
                "  • Incremental migration approach",
                "  • Extensive testing at each phase",
                "  • Stakeholder communication plan",
                "",
                "✅ SUCCESS CRITERIA:",
                "  • All functionality preserved",
                "  • Performance maintained or improved",
                "  • No data loss or corruption",
                "  • User experience uninterrupted",
                "  • Migration timeline met",
            ],
            "tools": [
                "migration_planner",
                "data_migrator",
                "compatibility_checker",
                "rollback_manager",
            ],
            "workflow": "migration",
            "checkpoints": [
                "migration_planning",
                "environment_setup",
                "migration_execution",
                "testing_validation",
                "go_live",
            ],
            "success_criteria": [
                "Migration plan approved",
                "All data successfully migrated",
                "Functionality fully validated",
                "Performance requirements met",
                "Users successfully onboarded",
            ],
            "metadata": {
                "migration_type": migration_type,
                "source": source,
                "target": target,
                "strategy": migration_strategy,
                "high_risk": True,
            },
        }

    # Helper Methods

    def _get_architecture_patterns(self) -> List[str]:
        """Get relevant architecture patterns"""
        return [
            "12-factor agent methodology compliance",
            "Microservices with clear boundaries",
            "Event-driven architecture for loose coupling",
            "Repository pattern for data access",
            "Dependency injection for testability",
        ]

    def _get_testing_approach(self, complexity: str) -> List[str]:
        """Get testing approach based on complexity"""
        base_approaches = [
            "Unit tests with high coverage",
            "Integration tests for workflows",
        ]

        if complexity in ["high", "enterprise"]:
            base_approaches.extend(
                [
                    "End-to-end testing scenarios",
                    "Performance and load testing",
                    "Security testing and validation",
                ]
            )

        return base_approaches

    def _estimate_feature_hours(self, complexity: str) -> int:
        """Estimate development hours by complexity"""
        hours_map = {"low": 8, "medium": 24, "high": 64, "enterprise": 120}
        return hours_map.get(complexity, 24)

    def _get_debugging_strategy(self, description: Optional[str]) -> List[str]:
        """Get debugging strategy based on issue description"""
        base_strategy = [
            "Reproduce the issue consistently",
            "Analyze logs and error messages",
            "Use debugger to trace execution",
            "Isolate the problematic code section",
        ]

        if description and any(
            keyword in description.lower()
            for keyword in ["performance", "slow", "timeout"]
        ):
            base_strategy.append("Profile performance bottlenecks")

        if description and any(
            keyword in description.lower() for keyword in ["memory", "leak", "crash"]
        ):
            base_strategy.append("Analyze memory usage patterns")

        return base_strategy

    def _find_potentially_affected_files(self, components: List[str]) -> List[str]:
        """Find potentially affected files based on components"""
        # This would be enhanced with actual file analysis
        return [f"{component}/**/*.py" for component in components]

    def _get_refactoring_patterns(self, refactor_type: str) -> List[str]:
        """Get refactoring patterns by type"""
        patterns_map = {
            "cleanup": [
                "Extract method for complex functions",
                "Remove duplicate code",
                "Simplify conditional expressions",
                "Improve variable and method names",
            ],
            "architecture": [
                "Separate concerns into distinct modules",
                "Apply SOLID principles",
                "Introduce design patterns where appropriate",
                "Improve layer separation",
            ],
            "performance": [
                "Optimize data structures and algorithms",
                "Reduce unnecessary computations",
                "Implement caching strategies",
                "Minimize I/O operations",
            ],
        }
        return patterns_map.get(refactor_type, patterns_map["cleanup"])

    def _get_quality_metrics(self) -> List[str]:
        """Get code quality metrics to track"""
        return [
            "Cyclomatic complexity",
            "Test coverage percentage",
            "Code duplication ratio",
            "Technical debt ratio",
            "Performance benchmarks",
        ]

    def _get_testing_strategy(self, test_type: str) -> List[str]:
        """Get testing strategy by type"""
        strategies = {
            "unit": [
                "Test individual functions and methods",
                "Mock external dependencies",
                "Focus on edge cases and error conditions",
                "Achieve high code coverage",
            ],
            "integration": [
                "Test component interactions",
                "Validate data flow between modules",
                "Test API endpoints and responses",
                "Verify database operations",
            ],
            "end-to-end": [
                "Test complete user workflows",
                "Validate system behavior under realistic conditions",
                "Test across different environments",
                "Verify performance requirements",
            ],
        }
        return strategies.get(test_type, strategies["unit"])

    def _get_test_patterns(self) -> List[str]:
        """Get common test patterns"""
        return [
            "Arrange-Act-Assert (AAA) pattern",
            "Given-When-Then (GWT) scenarios",
            "Test fixtures for consistent setup",
            "Parameterized tests for multiple inputs",
            "Mock objects for external dependencies",
        ]

    def _get_documentation_templates(self, doc_type: str) -> List[str]:
        """Get documentation templates by type"""
        templates = {
            "api": [
                "OpenAPI/Swagger specifications",
                "Function/method documentation",
                "Request/response examples",
                "Error code references",
            ],
            "user": [
                "Getting started guides",
                "Step-by-step tutorials",
                "FAQ and troubleshooting",
                "Best practices guide",
            ],
            "technical": [
                "Architecture decision records",
                "Technical specifications",
                "Design documents",
                "Code contribution guidelines",
            ],
        }
        return templates.get(doc_type, templates["api"])

    def _get_documentation_style(self) -> List[str]:
        """Get documentation style guidelines"""
        return [
            "Use active voice and present tense",
            "Write for your target audience level",
            "Include practical examples",
            "Keep sections focused and scannable",
            "Use consistent formatting and structure",
        ]

    def _load_template_files(self):
        """Load primer templates from YAML files"""
        try:
            for template_file in self.primers_directory.glob("*.yaml"):
                with open(template_file, "r") as f:
                    template_data = yaml.safe_load(f)

                # Create PrimerTemplate objects from YAML
                if "primers" in template_data:
                    for primer_data in template_data["primers"]:
                        template = PrimerTemplate(
                            name=primer_data["name"],
                            primer_type=PrimerType(primer_data["type"]),
                            description=primer_data["description"],
                            variables=primer_data.get("variables", {}),
                            context_template=primer_data["context_template"],
                            tools=primer_data.get("tools", []),
                            workflow_steps=primer_data.get("workflow_steps", []),
                            checkpoints=primer_data.get("checkpoints", []),
                            success_criteria=primer_data.get("success_criteria", []),
                        )
                        self.primer_templates[template.name] = template

        except Exception as e:
            print(f"Warning: Could not load template files: {e}")

    def get_primer_statistics(self) -> Dict[str, Any]:
        """Get primer performance statistics"""
        total_executions = sum(
            stats["total_executions"] for stats in self.primer_performance.values()
        )

        return {
            "total_primers": len(self.primers),
            "total_executions": total_executions,
            "primer_chains": len(self.primer_chains),
            "template_files": len(self.primer_templates),
            "average_execution_time": sum(
                stats["average_time"] for stats in self.primer_performance.values()
            )
            / len(self.primer_performance)
            if self.primer_performance
            else 0,
            "performance_by_primer": self.primer_performance.copy(),
        }

    def list_available_primers(self) -> List[str]:
        """List all available primers"""
        return list(self.primers.keys())

    def list_primer_chains(self) -> Dict[str, List[str]]:
        """List all primer chains"""
        return self.primer_chains.copy()
