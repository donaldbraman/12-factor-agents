#!/usr/bin/env python3
"""
Quality validation tests for the intelligent trigger system.
Tests the quality-focused routing decisions on real-world scenarios.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.intelligent_triggers import create_trigger_engine  # noqa: E402


class TestQualityTriggerSystem(unittest.TestCase):
    """Test the quality-focused trigger system with real scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = create_trigger_engine()

    def test_cite_assist_issue_123_routing(self):
        """Test routing of the actual cite-assist issue #123"""

        cite_assist_issue = """
        # Issue #123: Implement Document-Level Summary Embeddings for Whole-Document Relevance

        ## Goal
        Add whole-document relevance scoring by creating AI-generated summaries (1500-1800 chars) 
        that get embedded as single vectors for enhanced search functionality.

        ## Key Components
        1. **DocumentSummarizer** - Uses Gemini to create optimized summaries
        2. **Document Summary Store** - New Qdrant collection for document-level vectors  
        3. **Enhanced Search** - Weighted combination of chunk + document relevance
        4. **Caching System** - Avoids re-summarization of documents

        ## Technical Implementation
        This requires creating new Python modules in the cite-assist codebase:
        - `src/cite_assist/document_summarizer.py`
        - `src/cite_assist/document_summary_store.py`  
        - `src/cite_assist/enhanced_search.py`
        - `tests/test_document_summaries.py`

        ## Success Criteria
        - 8 comprehensive test suites covering quality, performance, and integration
        - Summaries must be 1500-1800 chars (optimal for embeddings)
        - Cache hit rate > 90%
        - < 5 seconds per summary generation
        - Configurable weighting between chunk and document relevance
        """

        decision = self.engine.route_task(cite_assist_issue)

        # Quality assertions
        self.assertEqual(
            decision.handler,
            "IntelligentIssueAgent",
            "Should route to IntelligentIssueAgent for feature creation",
        )
        self.assertGreaterEqual(
            decision.confidence, 0.85, "Should meet quality confidence threshold"
        )
        self.assertIn(
            "IntelligentIssueAgent",
            decision.factors_considered,
            "Should have considered IntelligentIssueAgent",
        )
        self.assertTrue(
            len(decision.reasoning) >= 3, "Should provide detailed reasoning"
        )

        print(f"✅ cite-assist #123 routed to: {decision.handler}")
        print(f"✅ Confidence: {decision.confidence:.3f}")
        print(f"✅ Reasoning provided: {len(decision.reasoning)} points")

    def test_bug_fix_routing(self):
        """Test routing of a bug fix issue"""

        bug_fix_issue = """
        # Bug Report: Authentication failing on login

        ## Problem
        Users are experiencing authentication failures when trying to log in.
        The error appears to be in the session handling logic.

        ## Steps to Reproduce
        1. Navigate to login page
        2. Enter valid credentials
        3. Click login button
        4. Error: "Session expired" appears

        ## Technical Details
        Error occurs in `src/auth/session_manager.py` around line 145.
        The session validation logic seems to have a timing issue.

        ## Expected Fix
        Fix the session validation logic and add proper error handling.
        """

        decision = self.engine.route_task(bug_fix_issue)

        # Should route to issue processor or be conservative
        self.assertIn(
            decision.handler,
            ["IssueProcessorAgent", "IntelligentIssueAgent"],
            "Should route to appropriate bug fix handler",
        )

        if decision.confidence >= 0.85:
            self.assertEqual(
                decision.handler,
                "IssueProcessorAgent",
                "High confidence should route to IssueProcessorAgent",
            )

        print(f"✅ Bug fix routed to: {decision.handler}")
        print(f"✅ Confidence: {decision.confidence:.3f}")

    def test_testing_focused_routing(self):
        """Test routing of testing-focused issues"""

        testing_issue = """
        # Testing Requirements: Comprehensive Test Suite

        ## Goal
        Create comprehensive test coverage for the new payment processing system.
        Need to validate all edge cases and error conditions.

        ## Testing Requirements
        - Unit tests for all payment methods
        - Integration tests with payment providers
        - End-to-end testing of payment flows
        - Performance testing under load
        - Security testing for payment data

        ## Success Criteria
        - 95% code coverage
        - All tests pass consistently
        - Performance benchmarks met
        - Security audit passes
        """

        decision = self.engine.route_task(testing_issue)

        # Could route to TestingAgent or IntelligentIssueAgent
        self.assertIn(
            decision.handler,
            ["TestingAgent", "IntelligentIssueAgent"],
            "Should route to testing-capable handler",
        )

        print(f"✅ Testing issue routed to: {decision.handler}")
        print(f"✅ Confidence: {decision.confidence:.3f}")

    def test_complex_orchestration_routing(self):
        """Test routing of complex orchestration tasks"""

        orchestration_issue = """
        # System Integration: Multi-Service Orchestration

        ## Goal
        Coordinate deployment across multiple microservices with proper rollback capabilities.
        Need to orchestrate database migrations, API updates, and frontend deployments.

        ## Technical Implementation
        - Coordinate between 5 different services
        - Manage dependencies between deployments
        - Implement automated rollback mechanisms
        - Monitor deployment health across systems
        - Integrate with existing CI/CD pipeline

        ## Success Criteria
        - Zero-downtime deployments
        - Automatic rollback on failure
        - Complete deployment visibility
        - Service dependency management
        """

        decision = self.engine.route_task(orchestration_issue)

        # Should route to orchestrator for complex coordination
        if decision.confidence >= 0.85:
            self.assertEqual(
                decision.handler,
                "HierarchicalOrchestrator",
                "High confidence complex task should route to orchestrator",
            )

        print(f"✅ Orchestration routed to: {decision.handler}")
        print(f"✅ Confidence: {decision.confidence:.3f}")

    def test_quality_threshold_enforcement(self):
        """Test that quality thresholds are properly enforced"""

        ambiguous_issue = """
        # Unclear Request
        
        Fix the thing that's broken in the system.
        """

        decision = self.engine.route_task(ambiguous_issue)

        # Should have low confidence due to ambiguity
        self.assertLess(
            decision.confidence, 0.85, "Ambiguous requests should have low confidence"
        )
        self.assertEqual(
            decision.handler,
            "IntelligentIssueAgent",
            "Should fallback to IntelligentIssueAgent for unclear requests",
        )

        print("✅ Ambiguous issue handled conservatively")
        print(f"✅ Low confidence: {decision.confidence:.3f}")

    def test_quality_reasoning_depth(self):
        """Test that quality reasoning is sufficiently detailed"""

        test_issue = """
        # Test Issue: Create new user management system
        
        ## Goal
        Implement a comprehensive user management system with authentication.
        
        ## Technical Implementation
        - Create `src/user_manager.py`
        - Create `src/auth_service.py`
        - Create `tests/test_user_management.py`
        """

        decision = self.engine.route_task(test_issue)

        # Quality assertions for reasoning
        self.assertGreaterEqual(
            len(decision.reasoning), 3, "Should provide at least 3 reasoning points"
        )
        self.assertTrue(
            any("confidence" in reason.lower() for reason in decision.reasoning),
            "Should explain confidence level",
        )
        self.assertTrue(
            any("analyzer" in reason.lower() for reason in decision.reasoning),
            "Should mention analyzer contributions",
        )

        print(f"✅ Detailed reasoning provided: {len(decision.reasoning)} points")


class TestQualitySystemIntegration(unittest.TestCase):
    """Integration tests for the complete quality system"""

    def test_end_to_end_quality_flow(self):
        """Test complete flow from trigger to routing decision"""

        # This would be a real issue from cite-assist
        real_world_issue = """
        # Feature Request: Advanced Search with AI Ranking
        
        ## Goal
        Implement AI-powered search ranking that combines multiple signals
        for more relevant research paper recommendations.
        
        ## Key Components
        1. **SearchRanker** - ML model for relevance scoring
        2. **Signal Aggregator** - Combines multiple ranking signals
        3. **Personalization Engine** - User preference integration
        4. **A/B Testing Framework** - Compare ranking algorithms
        
        ## Technical Implementation
        Create new modules:
        - `src/search/ai_ranker.py` - Core ML ranking logic
        - `src/search/signal_aggregator.py` - Signal combination
        - `src/search/personalization.py` - User preference handling
        - `src/search/ab_testing.py` - Experiment framework
        - `tests/test_ai_search.py` - Comprehensive test suite
        - `config/search_config.yaml` - Configuration management
        
        ## Success Criteria
        - 15% improvement in search relevance metrics
        - Sub-100ms response time for search queries
        - A/B testing framework with statistical significance
        - 90%+ test coverage for all new modules
        - Integration with existing search infrastructure
        """

        engine = create_trigger_engine()
        decision = engine.route_task(real_world_issue)

        # This should be high-quality routing
        self.assertGreaterEqual(
            decision.confidence,
            0.85,
            "Real-world feature should meet quality threshold",
        )
        self.assertEqual(
            decision.handler,
            "IntelligentIssueAgent",
            "Should route to IntelligentIssueAgent for feature creation",
        )
        self.assertTrue(
            len(decision.fallback_handlers) >= 1, "Should provide fallback options"
        )

        # Validate quality of decision
        self.assertIn(
            "consensus",
            " ".join(decision.reasoning).lower(),
            "Should mention consensus in reasoning",
        )
        self.assertIn(
            "threshold",
            " ".join(decision.reasoning).lower(),
            "Should mention quality threshold",
        )

        print("🎯 End-to-end quality validation passed")
        print(f"🎯 Handler: {decision.handler}")
        print(f"🎯 Confidence: {decision.confidence:.3f}")
        print(f"🎯 Fallbacks: {decision.fallback_handlers}")


if __name__ == "__main__":
    print("🧪 Running Quality Trigger System Tests")
    print("=" * 50)

    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)

    print("\n✨ Quality System Validation Complete")
    print("✨ System ready for precious code protection!")
