"""
Comprehensive unit tests for R&D Framework Context Optimizer
Testing 40-60% context reduction and delegation logic
"""

import pytest
from unittest.mock import patch, AsyncMock

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.context_optimizer import (
    ContextOptimizer,
    ContextOptimizedAgent,
    ReducedContext,
    ContextReductionStrategy,
)


class TestContextOptimizer:
    """Test suite for ContextOptimizer R&D Framework implementation"""

    @pytest.fixture
    def optimizer(self):
        """Create context optimizer instance"""
        return ContextOptimizer(max_tokens=8000, delegation_threshold=0.3)

    @pytest.fixture
    def sample_context(self):
        """Create sample context for testing"""
        return {
            "conversation_history": ["msg1", "msg2"] * 50,  # Long history
            "requirements": "Build a user authentication system",
            "duplicate_data": "This is duplicate",
            "duplicate_data_copy": "This is duplicate",
            "verbose_section": "x" * 2000,  # Very long string
            "relevant_data": "authentication related info",
            "irrelevant_data": "unrelated information",
            "subtasks": [
                "Implement login",
                "Add password reset",
                "Create user registration",
            ],
        }

    def test_remove_redundant_context(self, optimizer, sample_context):
        """Test removal of duplicate information"""
        task = "implement authentication"

        # Apply redundancy removal
        reduced, strategy = optimizer.remove_redundant_context(sample_context, task)

        # Verify duplicates removed
        assert "duplicate_data" in reduced
        assert "duplicate_data_copy" not in reduced  # Duplicate removed
        assert strategy == ContextReductionStrategy.REMOVE_REDUNDANT.value

        # Verify unique content preserved
        assert "requirements" in reduced
        assert "relevant_data" in reduced

    def test_summarize_verbose_sections(self, optimizer, sample_context):
        """Test summarization of verbose content"""
        task = "implement authentication"

        # Apply summarization
        reduced, strategy = optimizer.summarize_verbose_sections(sample_context, task)

        # Verify long string summarized
        assert len(reduced["verbose_section"]) < len(sample_context["verbose_section"])
        assert reduced["verbose_section"].endswith("...")
        assert strategy == ContextReductionStrategy.SUMMARIZE_VERBOSE.value

        # Verify conversation history summarized
        assert isinstance(reduced["conversation_history"], dict)
        assert "sample" in reduced["conversation_history"]
        assert len(reduced["conversation_history"]["sample"]) == 3

    def test_extract_relevant_only(self, optimizer, sample_context):
        """Test extraction of task-relevant content"""
        task = "implement authentication system"

        # Apply relevance filtering
        reduced, strategy = optimizer.extract_relevant_only(sample_context, task)

        # Verify relevant content kept
        assert "requirements" in reduced  # Core item always relevant
        assert "relevant_data" in reduced  # Contains "authentication"

        # Verify irrelevant content removed
        assert "irrelevant_data" not in reduced
        assert strategy == ContextReductionStrategy.EXTRACT_RELEVANT.value

    def test_compress_conversation_history(self, optimizer):
        """Test conversation history compression"""
        context = {"conversation_history": [f"message_{i}" for i in range(100)]}
        task = "any task"

        # Apply compression
        reduced, strategy = optimizer.compress_conversation_history(context, task)

        # Verify compression structure
        history = reduced["conversation_history"]
        assert isinstance(history, dict)
        assert len(history["initial"]) == 5
        assert len(history["recent"]) == 10
        assert "summary" in history
        assert strategy == ContextReductionStrategy.COMPRESS_HISTORY.value

    def test_optimize_context_achieves_reduction(self, optimizer, sample_context):
        """Test that optimization achieves 40-60% reduction"""
        task = "implement authentication"

        # Optimize context
        result = optimizer.optimize_context(sample_context, task)

        # Verify reduction achieved
        assert isinstance(result, ReducedContext)
        assert result.metrics.reduction_percentage >= 40
        assert result.metrics.reduction_percentage <= 60

        # Verify metrics
        assert result.metrics.original_tokens > result.metrics.reduced_tokens
        assert len(result.metrics.strategies_applied) > 0

    def test_delegation_triggered_at_threshold(self, optimizer):
        """Test delegation triggers when context exceeds threshold"""
        # Create large context that exceeds threshold
        large_context = {
            "massive_data": "x" * 10000,
            "subtasks": [
                "Complex task requiring specialized knowledge",
                "Another complex specialized task",
            ],
        }
        task = "process everything"

        # Set low threshold to trigger delegation
        optimizer.delegation_threshold = 0.1

        # Optimize context
        result = optimizer.optimize_context(large_context, task)

        # Verify delegation occurred
        assert result.metrics.delegation_recommended
        assert len(result.delegated_tasks) > 0
        assert result.delegated_tasks[0]["recommended_agent"] in [
            "ImplementationAgent",
            "GeneralPurposeAgent",
        ]

    def test_identify_delegatable_tasks(self, optimizer, sample_context):
        """Test identification of tasks for delegation"""
        sample_context["subtasks"].append("x" * 300)  # Add complex task
        task = "implement system"

        # Identify delegatable tasks
        delegatable = optimizer.identify_delegatable_tasks(sample_context, task)

        # Verify complex task identified
        assert len(delegatable) > 0
        assert "recommended_agent" in delegatable[0]
        assert "context_subset" in delegatable[0]

    def test_token_estimation(self, optimizer):
        """Test token counting estimation"""
        context = {"text": "Hello world"}

        # Estimate tokens (approximately 4 chars per token)
        tokens = optimizer.estimate_tokens(context)

        # JSON string is about 20 chars, so ~5 tokens
        assert 3 <= tokens <= 7  # Allow some variance

    def test_cost_savings_calculation(self, optimizer):
        """Test cost savings calculation"""
        original = 10000
        reduced = 4000

        # Calculate savings
        savings = optimizer.calculate_cost_savings(original, reduced)

        # Verify savings (assuming $0.01 per 1K tokens)
        expected = (10000 - 4000) / 1000 * 0.01
        assert savings == expected

    def test_keyword_extraction(self, optimizer):
        """Test keyword extraction from task"""
        task = "implement the user authentication and authorization system"

        # Extract keywords
        keywords = optimizer.extract_keywords(task)

        # Verify extraction
        assert "implement" in keywords
        assert "user" in keywords
        assert "authentication" in keywords
        assert "authorization" in keywords
        assert "the" not in keywords  # Stopword filtered
        assert "and" not in keywords  # Stopword filtered

    def test_relevance_checking(self, optimizer):
        """Test relevance checking logic"""
        keywords = ["authentication", "user", "login"]

        # Test relevant items
        assert optimizer.is_relevant_to_task("user_auth", "data", keywords)
        assert optimizer.is_relevant_to_task("data", "login process", keywords)
        assert optimizer.is_relevant_to_task(
            "requirements", "any", keywords
        )  # Core item

        # Test irrelevant items
        assert not optimizer.is_relevant_to_task("weather", "sunny day", keywords)

    def test_session_id_generation(self, optimizer):
        """Test unique session ID generation"""
        id1 = optimizer.generate_session_id()
        id2 = optimizer.generate_session_id()

        # Verify uniqueness and format
        assert id1 != id2
        assert len(id1) == 12
        assert all(c in "0123456789abcdef" for c in id1)

    def test_optimization_report(self, optimizer, sample_context):
        """Test optimization metrics reporting"""
        task = "test task"

        # Run multiple optimizations
        for _ in range(3):
            optimizer.optimize_context(sample_context, task)

        # Get report
        report = optimizer.get_optimization_report()

        # Verify report contents
        assert report["total_optimizations"] == 3
        assert "total_tokens_saved" in report
        assert "average_reduction_percentage" in report
        assert "total_cost_savings" in report
        assert "most_used_strategies" in report
        assert "delegation_rate" in report

    def test_agent_recommendation(self, optimizer):
        """Test appropriate agent type recommendation"""
        # Test implementation tasks
        assert (
            optimizer.recommend_agent_type("implement feature") == "ImplementationAgent"
        )
        assert optimizer.recommend_agent_type("create service") == "ImplementationAgent"

        # Test testing tasks
        assert optimizer.recommend_agent_type("test functionality") == "TestingAgent"
        assert optimizer.recommend_agent_type("validate results") == "TestingAgent"

        # Test research tasks
        assert optimizer.recommend_agent_type("analyze data") == "ResearchAgent"
        assert optimizer.recommend_agent_type("research options") == "ResearchAgent"

        # Test documentation tasks
        assert optimizer.recommend_agent_type("document API") == "DocumentationAgent"

        # Test general tasks
        assert optimizer.recommend_agent_type("random task") == "GeneralPurposeAgent"

    def test_specialized_knowledge_detection(self, optimizer):
        """Test detection of specialized domain requirements"""
        assert optimizer.requires_specialized_knowledge("legal document review")
        assert optimizer.requires_specialized_knowledge("medical diagnosis system")
        assert optimizer.requires_specialized_knowledge("financial risk assessment")
        assert not optimizer.requires_specialized_knowledge("build web interface")

    def test_important_message_extraction(self, optimizer):
        """Test extraction of important messages from history"""
        messages = [
            "regular message",
            "ERROR: Critical failure",
            "important decision made",
            "normal chat",
            "requirement: must have auth",
            "casual conversation",
        ]

        # Extract important messages
        important = optimizer.extract_important_messages(messages)

        # Verify important ones identified
        assert any("ERROR" in str(msg) for msg in important)
        assert any("important" in str(msg) for msg in important)
        assert any("requirement" in str(msg) for msg in important)
        assert len(important) <= 5


class TestContextOptimizedAgent:
    """Test suite for ContextOptimizedAgent with R&D Framework"""

    @pytest.fixture
    def agent(self):
        """Create context-optimized agent instance"""
        return ContextOptimizedAgent(agent_id="test_agent", max_context_tokens=8000)

    @pytest.mark.asyncio
    async def test_execute_task_with_optimization(self, agent):
        """Test task execution with context optimization"""
        task = "implement user authentication"

        # Mock the context and processing
        with patch.object(agent, "get_current_context") as mock_context:
            mock_context.return_value = {
                "requirements": "auth system",
                "duplicate": "data",
                "duplicate_copy": "data",
            }

            with patch.object(agent, "process_with_optimized_context") as mock_process:
                mock_process.return_value = "Task completed"

                # Execute task
                result = await agent.execute_task(task)

                # Verify optimization occurred
                assert result.success
                assert "optimization_metrics" in result.data
                assert "result" in result.data
                assert result.data["optimization_metrics"]["original_tokens"] > 0
                assert result.data["optimization_metrics"]["reduced_tokens"] > 0

    @pytest.mark.asyncio
    async def test_delegation_handling(self, agent):
        """Test handling of delegated tasks"""
        # Create delegated tasks
        delegated_tasks = [
            {
                "task": "complex subtask",
                "recommended_agent": "SpecializedAgent",
                "context_subset": {"data": "subset"},
            }
        ]

        with patch.object(agent, "spawn_specialized_agent") as mock_spawn:
            mock_agent = AsyncMock()
            mock_agent.execute_task.return_value = {"status": "completed"}
            mock_spawn.return_value = mock_agent

            # Handle delegations
            results = await agent.handle_delegations(delegated_tasks)

            # Verify delegation handling
            assert len(results) == 1
            assert results[0]["task"] == "complex subtask"
            assert results[0]["agent"] == "SpecializedAgent"
            assert "result" in results[0]

    @pytest.mark.asyncio
    async def test_specialized_agent_spawning(self, agent):
        """Test spawning of specialized agents"""
        agent_type = "ResearchAgent"
        context = {"research_data": "test"}

        # Spawn specialized agent
        specialized = await agent.spawn_specialized_agent(agent_type, context)

        # Verify agent created
        assert specialized.agent_id == "test_agent_delegate_0"
        assert specialized.workflow_data == context


class TestRDFrameworkIntegration:
    """Integration tests for R&D Framework"""

    def test_end_to_end_optimization(self):
        """Test complete optimization workflow"""
        optimizer = ContextOptimizer(max_tokens=1000, delegation_threshold=0.2)

        # Create realistic context
        context = {
            "project_description": "Build a comprehensive e-commerce platform with user authentication, "
            * 10,
            "requirements": [
                "User registration and login",
                "Product catalog",
                "Shopping cart",
                "Payment processing",
                "Order management",
            ],
            "technical_specs": {
                "framework": "Django",
                "database": "PostgreSQL",
                "cache": "Redis",
                "queue": "Celery",
            },
            "conversation_history": [
                f"Message {i}: Discussion about feature {i}" for i in range(50)
            ],
            "code_samples": "def example():\n    pass\n" * 20,
            "duplicate_info": "This is important",
            "duplicate_info_2": "This is important",
            "irrelevant_notes": "Team lunch is at noon tomorrow",
        }

        task = "implement user authentication module"

        # Optimize context
        result = optimizer.optimize_context(context, task)

        # Verify significant reduction
        assert result.metrics.reduction_percentage >= 30

        # Verify relevant content preserved
        assert "requirements" in result.content
        assert "technical_specs" in result.content

        # Verify optimization strategies applied
        assert len(result.metrics.strategies_applied) >= 2

        # Verify cost savings
        assert result.metrics.estimated_cost_savings > 0

    def test_performance_benchmark(self):
        """Benchmark optimization performance"""
        import time

        optimizer = ContextOptimizer()

        # Create large context
        large_context = {f"section_{i}": f"Content {i} " * 100 for i in range(20)}

        # Measure optimization time
        start = time.time()
        result = optimizer.optimize_context(large_context, "optimize this")
        duration = time.time() - start

        # Should optimize quickly (under 1 second)
        assert duration < 1.0

        # Should achieve good reduction
        assert result.metrics.reduction_percentage >= 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
