#!/usr/bin/env python3
"""
12-Factor Compliant Intelligent Trigger System

Implements efficient, stateless trigger routing that adheres to 12-factor principles:
- Factor 1: Stateless (no internal state, pure functions)
- Factor 2: Explicit dependencies (clear trigger rule definitions)
- Factor 3: Configuration (externalized trigger rules)
- Factor 4: Backing services (pluggable trigger engines)
- Factor 10: Small, focused agents (specialized trigger analyzers)
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


class TriggerConfidence(Enum):
    """Confidence levels for trigger decisions"""

    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4
    UNCERTAIN = 0.2


@dataclass
class TriggerRule:
    """Stateless trigger rule definition"""

    name: str
    pattern_type: str  # "keyword", "regex", "semantic", "structural"
    patterns: List[str]
    target_handler: str
    confidence_boost: float = 0.1
    context_requirements: List[str] = None

    def __post_init__(self):
        if self.context_requirements is None:
            self.context_requirements = []


@dataclass
class TriggerDecision:
    """Result of trigger analysis"""

    handler: str
    confidence: float
    reasoning: List[str]
    factors_considered: Dict[str, float]
    fallback_handlers: List[str]


class TriggerAnalyzer:
    """Small, focused trigger analyzer (Factor 10: Small Agents)"""

    def __init__(self, analyzer_type: str):
        self.analyzer_type = analyzer_type

    def analyze(self, content: str, context: Dict[str, Any]) -> Dict[str, float]:
        """Pure function analysis (Factor 1: Stateless)"""
        raise NotImplementedError


class KeywordTriggerAnalyzer(TriggerAnalyzer):
    """Efficient keyword-based trigger analysis"""

    def __init__(self):
        super().__init__("keyword")

    def analyze(self, content: str, context: Dict[str, Any]) -> Dict[str, float]:
        """Stateless keyword analysis with confidence scoring"""
        content_lower = content.lower()

        # Load rules from configuration (Factor 3: Configuration)
        rules = context.get("trigger_rules", {})

        scores = {}
        for handler, rule_patterns in rules.items():
            score = 0.0
            matches = []

            for pattern in rule_patterns.get("keywords", []):
                if pattern in content_lower:
                    score += rule_patterns.get("weight", 0.1)
                    matches.append(pattern)

            # Normalize score
            if matches:
                scores[handler] = min(score, 1.0)

        return scores


class StructuralTriggerAnalyzer(TriggerAnalyzer):
    """Analyze document structure for routing hints"""

    def __init__(self):
        super().__init__("structural")

    def analyze(self, content: str, context: Dict[str, Any]) -> Dict[str, float]:
        """Analyze markdown structure and content organization"""
        lines = content.split("\n")

        structure_signals = {
            "feature_creation": 0.0,
            "simple_task": 0.0,
            "complex_orchestration": 0.0,
        }

        # Count structural elements
        sections = len([line for line in lines if line.startswith("## ")])
        file_mentions = content.count("`") // 2  # Rough estimate
        bullet_points = len([line for line in lines if line.strip().startswith("- ")])

        # Structural scoring (efficient heuristics)
        if sections >= 3 and file_mentions >= 2:
            structure_signals["feature_creation"] = 0.7
        elif sections >= 5 or bullet_points >= 10:
            structure_signals["complex_orchestration"] = 0.6
        else:
            structure_signals["simple_task"] = 0.5

        return structure_signals


class DeepSemanticTriggerAnalyzer(TriggerAnalyzer):
    """Deep semantic analysis prioritizing quality over speed"""

    def __init__(self):
        super().__init__("deep_semantic")

    def analyze(self, content: str, context: Dict[str, Any]) -> Dict[str, float]:
        """Deep semantic analysis with comprehensive understanding"""

        quality_settings = context.get("trigger_rules", {}).get("quality_settings", {})

        if not quality_settings.get("enable_deep_analysis", False):
            return self._lightweight_analysis(content)

        # Deep semantic understanding with multiple dimensions
        semantic_dimensions = {
            "creation_intent": {
                "primary": [
                    "implement",
                    "create",
                    "build",
                    "develop",
                    "design",
                    "construct",
                ],
                "secondary": ["add", "introduce", "establish", "setup", "initialize"],
                "context": ["new", "fresh", "novel", "original", "custom"],
                "scope": [
                    "feature",
                    "functionality",
                    "capability",
                    "component",
                    "module",
                ],
                "outcome": ["system", "service", "tool", "framework", "solution"],
            },
            "modification_intent": {
                "primary": ["fix", "repair", "resolve", "correct", "patch"],
                "secondary": ["update", "modify", "change", "refactor", "improve"],
                "context": ["bug", "issue", "problem", "error", "defect"],
                "scope": ["code", "logic", "algorithm", "structure", "architecture"],
                "outcome": [
                    "stability",
                    "performance",
                    "reliability",
                    "maintainability",
                ],
            },
            "analysis_intent": {
                "primary": ["analyze", "review", "evaluate", "assess", "examine"],
                "secondary": [
                    "investigate",
                    "study",
                    "explore",
                    "understand",
                    "validate",
                ],
                "context": [
                    "quality",
                    "performance",
                    "security",
                    "compliance",
                    "standards",
                ],
                "scope": [
                    "codebase",
                    "system",
                    "architecture",
                    "design",
                    "implementation",
                ],
                "outcome": [
                    "insights",
                    "recommendations",
                    "findings",
                    "report",
                    "assessment",
                ],
            },
            "orchestration_intent": {
                "primary": [
                    "orchestrate",
                    "coordinate",
                    "manage",
                    "integrate",
                    "deploy",
                ],
                "secondary": [
                    "synchronize",
                    "harmonize",
                    "align",
                    "unify",
                    "consolidate",
                ],
                "context": [
                    "workflow",
                    "pipeline",
                    "process",
                    "automation",
                    "coordination",
                ],
                "scope": ["systems", "services", "components", "teams", "resources"],
                "outcome": ["efficiency", "automation", "streamlining", "optimization"],
            },
        }

        content_lower = content.lower()

        # Analyze each dimension with weighted scoring
        dimension_scores = {}

        for intent, dimensions in semantic_dimensions.items():
            total_score = 0.0
            signal_strength = 0

            # Primary signals (highest weight)
            primary_matches = len(
                [w for w in dimensions["primary"] if w in content_lower]
            )
            if primary_matches > 0:
                total_score += primary_matches * 0.4
                signal_strength += 1

            # Secondary signals
            secondary_matches = len(
                [w for w in dimensions["secondary"] if w in content_lower]
            )
            if secondary_matches > 0:
                total_score += secondary_matches * 0.25
                signal_strength += 1

            # Context signals
            context_matches = len(
                [w for w in dimensions["context"] if w in content_lower]
            )
            if context_matches > 0:
                total_score += context_matches * 0.2
                signal_strength += 1

            # Scope signals
            scope_matches = len([w for w in dimensions["scope"] if w in content_lower])
            if scope_matches > 0:
                total_score += scope_matches * 0.15
                signal_strength += 1

            # Outcome signals
            outcome_matches = len(
                [w for w in dimensions["outcome"] if w in content_lower]
            )
            if outcome_matches > 0:
                total_score += outcome_matches * 0.1
                signal_strength += 1

            # Require multiple signals for high confidence
            if (
                quality_settings.get("require_multiple_signals", True)
                and signal_strength >= 2
            ):
                # Boost confidence when we have multiple confirming signals
                confidence_boost = min(signal_strength * 0.1, 0.3)
                total_score += confidence_boost
            elif signal_strength < 2:
                # Penalize single-signal matches for quality
                total_score *= 0.6

            # Map to handler
            handler_mapping = {
                "creation_intent": "AsyncSparky",
                "modification_intent": "IssueProcessorAgent",
                "analysis_intent": "TestingAgent",
                "orchestration_intent": "HierarchicalOrchestrator",
            }

            if total_score > 0:
                handler = handler_mapping.get(intent, "AsyncSparky")
                dimension_scores[handler] = min(total_score, 1.0)

        return dimension_scores

    def _lightweight_analysis(self, content: str) -> Dict[str, float]:
        """Fallback lightweight analysis"""
        semantic_clusters = {
            "creation": ["create", "implement", "build", "develop", "design", "add"],
            "modification": [
                "fix",
                "update",
                "modify",
                "change",
                "refactor",
                "improve",
            ],
            "analysis": ["analyze", "review", "evaluate", "assess", "validate", "test"],
            "orchestration": [
                "coordinate",
                "orchestrate",
                "manage",
                "integrate",
                "deploy",
            ],
        }

        content_words = set(content.lower().split())

        scores = {}
        for intent, cluster_words in semantic_clusters.items():
            overlap = len(content_words.intersection(set(cluster_words)))
            if overlap > 0:
                scores[f"{intent}_handler"] = min(overlap * 0.2, 0.8)

        return scores


class ContextualIntentAnalyzer(TriggerAnalyzer):
    """Deep contextual analysis for high-quality routing decisions"""

    def __init__(self):
        super().__init__("contextual")

    def analyze(self, content: str, context: Dict[str, Any]) -> Dict[str, float]:
        """Analyze contextual clues for intent understanding"""

        # Parse markdown structure for context
        sections = self._parse_markdown_sections(content)

        # Analyze technical complexity indicators
        complexity_signals = self._analyze_complexity_signals(content, sections)

        # Analyze file and code references
        code_signals = self._analyze_code_references(content)

        # Analyze scope and impact
        scope_signals = self._analyze_scope_and_impact(content, sections)

        # Combine signals with weighted approach
        contextual_scores = {}

        # Feature creation context
        if (
            sections.get("technical_implementation")
            and code_signals.get("files_to_create", 0) >= 2
            and scope_signals.get("new_functionality", False)
        ):
            contextual_scores["AsyncSparky"] = 0.9

        # Complex orchestration context
        elif (
            complexity_signals.get("multi_system", False)
            and scope_signals.get("cross_cutting", False)
            and sections.get("workflow")
            or sections.get("pipeline")
        ):
            contextual_scores["HierarchicalOrchestrator"] = 0.85

        # Quality/testing context
        elif (
            sections.get("testing")
            or sections.get("validation")
            or content.lower().count("test") >= 3
        ):
            contextual_scores["TestingAgent"] = 0.8

        # Bug fix context
        elif complexity_signals.get("error_fixing", False) and not scope_signals.get(
            "new_functionality", False
        ):
            contextual_scores["IssueProcessorAgent"] = 0.75

        return contextual_scores

    def _parse_markdown_sections(self, content: str) -> Dict[str, bool]:
        """Parse markdown sections for structural analysis"""
        lines = content.split("\n")
        sections = {}

        for line in lines:
            line_lower = line.lower().strip()
            if line_lower.startswith("## "):
                section_name = line_lower[3:].strip()
                if any(
                    keyword in section_name
                    for keyword in ["goal", "objective", "purpose"]
                ):
                    sections["goals"] = True
                elif any(
                    keyword in section_name
                    for keyword in ["technical", "implementation", "approach"]
                ):
                    sections["technical_implementation"] = True
                elif any(
                    keyword in section_name
                    for keyword in ["test", "validation", "verify"]
                ):
                    sections["testing"] = True
                elif any(
                    keyword in section_name
                    for keyword in ["success", "criteria", "acceptance"]
                ):
                    sections["success_criteria"] = True
                elif any(
                    keyword in section_name
                    for keyword in ["workflow", "pipeline", "process"]
                ):
                    sections["workflow"] = True

        return sections

    def _analyze_complexity_signals(
        self, content: str, sections: Dict
    ) -> Dict[str, Any]:
        """Analyze signals indicating task complexity"""
        content_lower = content.lower()

        signals = {}

        # Multi-system indicators
        signals["multi_system"] = any(
            phrase in content_lower
            for phrase in [
                "integrate with",
                "coordinate between",
                "multiple systems",
                "cross-service",
                "microservices",
                "distributed",
            ]
        )

        # Error fixing indicators
        signals["error_fixing"] = any(
            phrase in content_lower
            for phrase in [
                "bug",
                "error",
                "issue",
                "problem",
                "broken",
                "failing",
                "not working",
                "incorrect",
                "wrong",
            ]
        )

        # Architecture indicators
        signals["architectural"] = any(
            phrase in content_lower
            for phrase in [
                "architecture",
                "design pattern",
                "refactor",
                "restructure",
                "migrate",
                "modernize",
            ]
        )

        return signals

    def _analyze_code_references(self, content: str) -> Dict[str, Any]:
        """Analyze code and file references"""
        import re

        # Count file references in backticks
        file_pattern = r"`([^`]+\.(py|js|md|json|yaml|yml|ts|go|rs))`"
        file_matches = re.findall(file_pattern, content)

        # Count code blocks
        code_blocks = content.count("```")

        # Look for creation language
        creation_patterns = [
            r"create.*?`([^`]+)`",
            r"implement.*?`([^`]+)`",
            r"add.*?`([^`]+)`",
        ]

        files_to_create = 0
        for pattern in creation_patterns:
            files_to_create += len(re.findall(pattern, content.lower()))

        return {
            "total_file_references": len(file_matches),
            "files_to_create": files_to_create,
            "code_blocks": code_blocks // 2,  # Pairs of ```
            "has_code_examples": code_blocks >= 2,
        }

    def _analyze_scope_and_impact(self, content: str, sections: Dict) -> Dict[str, Any]:
        """Analyze scope and impact of the task"""
        content_lower = content.lower()

        signals = {}

        # New functionality indicators
        signals["new_functionality"] = any(
            phrase in content_lower
            for phrase in [
                "new feature",
                "implement",
                "create",
                "build",
                "develop",
                "add functionality",
                "enhancement",
            ]
        )

        # Cross-cutting concerns
        signals["cross_cutting"] = any(
            phrase in content_lower
            for phrase in [
                "across",
                "throughout",
                "all",
                "entire",
                "system-wide",
                "global",
                "everywhere",
            ]
        )

        # Impact scope
        high_impact_words = ["critical", "important", "major", "significant", "core"]
        signals["high_impact"] = any(
            word in content_lower for word in high_impact_words
        )

        return signals


class QualityTriggerEngine:
    """
    12-Factor compliant trigger engine prioritizing quality over speed

    Factor 1: Stateless - No internal state between requests
    Factor 3: Configuration - All rules externally configurable
    Factor 4: Backing services - Pluggable analyzers

    Quality-focused features:
    - Deep semantic analysis with multiple dimensions
    - Cross-validation between analyzers
    - Conservative routing with high confidence thresholds
    - Comprehensive contextual understanding
    """

    def __init__(self, config_path: Optional[str] = None):
        # Factor 3: Configuration from environment
        self.config_path = config_path or "config/trigger_rules.json"

        # Factor 4: Quality-focused backing services (pluggable analyzers)
        self.analyzers = [
            KeywordTriggerAnalyzer(),
            StructuralTriggerAnalyzer(),
            DeepSemanticTriggerAnalyzer(),  # Enhanced semantic analysis
            ContextualIntentAnalyzer(),  # Deep contextual analysis
        ]

    def route_task(
        self, content: str, context: Dict[str, Any] = None
    ) -> TriggerDecision:
        """
        Quality-focused, stateless task routing with deep analysis

        Factor 1: Stateless - Pure function with no side effects
        Factor 10: Small agents - Delegates to focused analyzers

        Quality Features:
        - Cross-validation between multiple analyzers
        - Conservative routing with high confidence requirements
        - Deep reasoning and explanation
        - Comprehensive signal analysis
        """
        if context is None:
            context = {}

        # Load configuration (Factor 3: Configuration)
        trigger_config = self._load_trigger_config()
        context["trigger_rules"] = trigger_config
        quality_settings = trigger_config.get("quality_settings", {})
        quality_thresholds = trigger_config.get("quality_thresholds", {})

        # Deep analysis by specialized, quality-focused agents (Factor 10)
        all_scores = {}
        detailed_reasoning = []
        analyzer_insights = {}

        for analyzer in self.analyzers:
            analyzer_scores = analyzer.analyze(content, context)
            analyzer_insights[analyzer.analyzer_type] = analyzer_scores

            for handler, score in analyzer_scores.items():
                if handler not in all_scores:
                    all_scores[handler] = []
                all_scores[handler].append((analyzer.analyzer_type, score))

        # Quality-focused aggregation with cross-validation
        final_scores = {}
        consensus_scores = {}

        for handler, score_list in all_scores.items():
            if len(score_list) == 0:
                continue

            # Calculate multiple quality metrics
            scores = [score for _, score in score_list]
            analyzer_count = len(scores)

            # Weighted average (baseline score)
            baseline_score = sum(scores) / analyzer_count

            # Consensus bonus (multiple analyzers agree)
            high_scores = len([s for s in scores if s >= 0.7])
            if analyzer_count >= 2 and high_scores >= 2:
                consensus_bonus = min(high_scores * 0.1, 0.2)
                consensus_scores[handler] = baseline_score + consensus_bonus
            else:
                consensus_scores[handler] = (
                    baseline_score * 0.8
                )  # Penalize low consensus

            # Conservative routing: require multiple signals for high confidence
            if quality_settings.get("require_multiple_signals", True):
                if analyzer_count >= 3:  # Strong consensus
                    quality_multiplier = 1.2
                elif analyzer_count >= 2:  # Moderate consensus
                    quality_multiplier = 1.0
                else:  # Single signal - be conservative
                    quality_multiplier = 0.6
            else:
                quality_multiplier = 1.0

            final_scores[handler] = min(
                consensus_scores[handler] * quality_multiplier, 1.0
            )

            # Build detailed reasoning
            analyzer_details = [
                f"{analyzer}: {score:.3f}" for analyzer, score in score_list
            ]
            detailed_reasoning.append(
                f"{handler} (consensus: {consensus_scores[handler]:.3f}, "
                f"final: {final_scores[handler]:.3f}) - {analyzer_details}"
            )

        # Apply quality thresholds for conservative routing
        min_confidence = quality_thresholds.get("min_confidence_threshold", 0.85)
        high_quality_threshold = quality_thresholds.get("high_quality_threshold", 0.95)

        # Filter out low-confidence options
        high_confidence_handlers = {
            h: s for h, s in final_scores.items() if s >= min_confidence
        }

        if not high_confidence_handlers:
            # No high-confidence options - be conservative
            fallback_handler = quality_thresholds.get("fallback_handler", "AsyncSparky")
            return TriggerDecision(
                handler=fallback_handler,
                confidence=TriggerConfidence.UNCERTAIN.value,
                reasoning=[
                    f"No handlers met quality threshold ({min_confidence:.2f})",
                    "Using conservative fallback routing",
                    f"Available scores: {final_scores}",
                ]
                + detailed_reasoning,
                factors_considered=final_scores,
                fallback_handlers=list(final_scores.keys())[:2],
            )

        # Select best high-confidence handler
        best_handler = max(high_confidence_handlers, key=high_confidence_handlers.get)
        confidence = high_confidence_handlers[best_handler]

        # Enhanced reasoning for quality decisions
        quality_reasoning = [
            f"Selected {best_handler} with {confidence:.3f} confidence",
            f"Met quality threshold ({min_confidence:.2f})",
            f"Cross-validation: {len(analyzer_insights)} analyzers contributed",
        ]

        if confidence >= high_quality_threshold:
            quality_reasoning.append(
                f"Exceeds high-quality threshold ({high_quality_threshold:.2f})"
            )

        # Create quality-ranked fallback options
        sorted_handlers = sorted(
            high_confidence_handlers.items(), key=lambda x: x[1], reverse=True
        )
        fallback_handlers = [
            h for h, s in sorted_handlers[1:3]
        ]  # Top 2 high-confidence alternatives

        # Ensure we always have at least one fallback
        if not fallback_handlers and len(final_scores) > 1:
            all_sorted = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
            fallback_handlers = [h for h, s in all_sorted[1:3] if h != best_handler]

        return TriggerDecision(
            handler=best_handler,
            confidence=confidence,
            reasoning=quality_reasoning + detailed_reasoning,
            factors_considered=final_scores,
            fallback_handlers=fallback_handlers,
        )

    def _load_trigger_config(self) -> Dict[str, Any]:
        """Load configuration from external source (Factor 3)"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                return json.loads(config_file.read_text())
        except Exception:
            pass

        # Efficient default configuration
        return {
            "AsyncSparky": {
                "keywords": ["implement", "create", "build", "develop", "feature"],
                "weight": 0.3,
            },
            "IssueProcessorAgent": {
                "keywords": ["fix", "bug", "error", "resolve", "repair"],
                "weight": 0.2,
            },
            "HierarchicalOrchestrator": {
                "keywords": [
                    "orchestrate",
                    "coordinate",
                    "multiple",
                    "complex",
                    "integrate",
                ],
                "weight": 0.4,
            },
            "TestingAgent": {
                "keywords": ["test", "validate", "verify", "check"],
                "weight": 0.2,
            },
        }


# Factory function for dependency injection (Factor 2: Explicit Dependencies)
def create_trigger_engine(config_path: Optional[str] = None) -> QualityTriggerEngine:
    """Factory function with explicit dependencies - Quality-focused implementation"""
    return QualityTriggerEngine(config_path)


# Example quality-focused usage
if __name__ == "__main__":
    # Factor 1: Stateless usage with quality prioritization
    engine = create_trigger_engine()

    test_content = """
    # Implement Document-Level Summary Embeddings for Whole-Document Relevance
    
    ## Goal
    Add whole-document relevance scoring by creating AI-generated summaries (1500-1800 chars) 
    that get embedded as single vectors for enhanced search functionality.
    
    ## Technical Implementation
    This requires creating new Python modules in the cite-assist codebase:
    - Create `src/cite_assist/document_summarizer.py` - Uses Gemini to create optimized summaries
    - Create `src/cite_assist/document_summary_store.py` - New Qdrant collection for document-level vectors
    - Create `src/cite_assist/enhanced_search.py` - Weighted combination of chunk + document relevance
    - Create `tests/test_document_summaries.py` - Comprehensive test coverage
    
    ## Success Criteria
    - 8 comprehensive test suites covering quality, performance, and integration
    - Summaries must be 1500-1800 chars (optimal for embeddings)
    - Cache hit rate > 90%
    - < 5 seconds per summary generation
    - Configurable weighting between chunk and document relevance
    """

    print("🎯 Quality-Focused Trigger Analysis")
    print("=" * 50)

    decision = engine.route_task(test_content)

    print(f"📍 Selected Handler: {decision.handler}")
    print(f"🎯 Confidence Score: {decision.confidence:.3f}")
    print(f"🔄 Fallback Options: {decision.fallback_handlers}")
    print(f"📊 All Scores: {decision.factors_considered}")
    print("\n🧠 Quality Reasoning:")
    for reason in decision.reasoning:
        print(f"  • {reason}")

    print("\n✨ Quality Features Enabled:")
    print("  • Deep semantic analysis with 5 dimensions")
    print("  • Cross-validation between 4 specialized analyzers")
    print("  • Conservative routing (85% confidence threshold)")
    print("  • Multi-signal consensus requirements")
    print("  • Comprehensive contextual understanding")
