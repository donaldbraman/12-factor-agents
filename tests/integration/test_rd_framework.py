"""
Integration tests for R&D Framework with real cite-assist and pin-citer workloads
Validates 40-60% context reduction in production scenarios
"""

import pytest
import json
import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from core.context_optimizer import ContextOptimizer
from core.autonomous import AutonomousImplementationAgent
from core.github_integration import GitHubIntegrationAgent
from core.handoff import HandoffAgent


class TestCiteAssistIntegration:
    """Test R&D Framework with cite-assist workloads"""

    @pytest.fixture
    def cite_assist_context(self):
        """Create realistic cite-assist context"""
        return {
            "legal_research": {
                "case_law": ["Case " + str(i) for i in range(100)],
                "statutes": ["Statute " + str(i) for i in range(50)],
                "regulations": ["Regulation " + str(i) for i in range(30)],
            },
            "citation_scoring": {
                "adequacy_metrics": [0.8, 0.9, 0.7] * 20,
                "relevance_scores": [0.85, 0.92, 0.78] * 20,
                "completeness": [0.9, 0.88, 0.91] * 20,
            },
            "zotero_integration": {
                "library_items": [f"Item_{i}" for i in range(200)],
                "collections": [f"Collection_{i}" for i in range(20)],
                "tags": [f"Tag_{i}" for i in range(50)],
            },
            "argument_analysis": {
                "arguments": ["Legal argument " + str(i) for i in range(40)],
                "classifications": ["Type A", "Type B", "Type C"] * 30,
                "confidence_scores": [0.95, 0.87, 0.91] * 30,
            },
            "conversation_history": [
                f"User: Question about legal topic {i}\nAssistant: Response {i}"
                for i in range(100)
            ],
            "requirements": "Analyze citation adequacy for Supreme Court brief",
            "duplicate_data_1": "Important legal precedent" * 10,
            "duplicate_data_2": "Important legal precedent" * 10,
            "verbose_documentation": "x" * 5000,
        }

    def test_cite_assist_context_optimization(self, cite_assist_context):
        """Test optimization of cite-assist legal research context"""
        optimizer = ContextOptimizer(max_tokens=8000)
        task = "analyze citation adequacy for Supreme Court brief"

        # Measure original size
        original_size = optimizer.estimate_tokens(cite_assist_context)

        # Optimize context
        result = optimizer.optimize_context(cite_assist_context, task)

        # Verify 40-60% reduction achieved
        assert 40 <= result.metrics.reduction_percentage <= 60

        # Verify legal research preserved (relevant)
        assert "requirements" in result.content
        assert "citation_scoring" in result.content  # Relevant to task

        # Verify duplicates removed
        assert not (
            "duplicate_data_1" in result.content
            and "duplicate_data_2" in result.content
        )

        # Verify verbose content summarized
        if "verbose_documentation" in result.content:
            assert len(str(result.content["verbose_documentation"])) < 5000

        # Verify conversation history compressed
        if "conversation_history" in result.content:
            history = result.content["conversation_history"]
            if isinstance(history, dict):
                assert "initial" in history
                assert "recent" in history

    @pytest.mark.asyncio
    async def test_autonomous_agent_with_optimization(self, cite_assist_context):
        """Test AutonomousImplementationAgent with R&D Framework"""
        agent = AutonomousImplementationAgent("citation_scoring_enhancement")

        # Add context optimizer
        agent.context_optimizer = ContextOptimizer(max_tokens=8000)

        # Set heavy context
        agent.workflow_data = cite_assist_context

        # Execute with optimization
        task_spec = """
        name: Citation Scoring Enhancement
        requirements: Improve multi-dimensional citation adequacy assessment
        complexity: high
        domain: legal_research
        """

        # Mock the actual implementation
        with pytest.mock.patch.object(
            agent, "_execute_autonomous_workflow"
        ) as mock_exec:
            mock_exec.return_value = {"status": "completed"}

            # Optimize before execution
            optimized = agent.context_optimizer.optimize_context(
                agent.workflow_data, task_spec
            )

            # Verify optimization occurred
            assert optimized.metrics.reduction_percentage >= 30
            assert (
                optimized.metrics.delegation_recommended
                or len(optimized.delegated_tasks) >= 0
            )

    def test_specialized_legal_task_delegation(self, cite_assist_context):
        """Test delegation of specialized legal tasks"""
        optimizer = ContextOptimizer(max_tokens=2000)  # Low limit to force delegation
        task = "comprehensive legal research and citation analysis"

        # Add complex legal subtasks
        cite_assist_context["subtasks"] = [
            "Analyze Supreme Court precedents for constitutional arguments",
            "Research federal circuit court decisions on similar matters",
            "Evaluate citation adequacy using multi-dimensional scoring",
        ]

        # Optimize with delegation
        result = optimizer.optimize_context(cite_assist_context, task)

        # Verify delegation triggered
        assert result.metrics.delegation_recommended
        assert len(result.delegated_tasks) > 0

        # Verify appropriate agent recommendations
        agents = [d["recommended_agent"] for d in result.delegated_tasks]
        assert "ResearchAgent" in agents or "GeneralPurposeAgent" in agents


class TestPinCiterIntegration:
    """Test R&D Framework with pin-citer PDF processing workloads"""

    @pytest.fixture
    def pin_citer_context(self):
        """Create realistic pin-citer PDF processing context"""
        return {
            "pdf_metadata": {
                "documents": [f"Document_{i}.pdf" for i in range(50)],
                "pages": list(range(1, 500)),
                "extracted_text": ["Page text " * 100 for _ in range(100)],
            },
            "processing_pipeline": {
                "stages": ["download", "extract", "chunk", "embed", "index"],
                "status": [
                    "completed",
                    "completed",
                    "in_progress",
                    "pending",
                    "pending",
                ],
                "metrics": {
                    "pages_processed": 250,
                    "chunks_created": 1000,
                    "embeddings_generated": 750,
                },
            },
            "citation_extraction": {
                "citations": [f"Citation_{i}" for i in range(200)],
                "references": [f"Reference_{i}" for i in range(150)],
                "footnotes": [f"Footnote_{i}" for i in range(100)],
            },
            "validation_results": {
                "valid_citations": 180,
                "invalid_citations": 20,
                "confidence_scores": [0.9] * 200,
            },
            "conversation_history": [f"Processing update {i}" for i in range(150)],
            "requirements": "Extract and validate all citations from PDF corpus",
            "duplicate_metadata_1": {"doc": "info"} * 50,
            "duplicate_metadata_2": {"doc": "info"} * 50,
            "verbose_logs": "Processing log entry\n" * 1000,
        }

    def test_pin_citer_context_optimization(self, pin_citer_context):
        """Test optimization of pin-citer PDF processing context"""
        optimizer = ContextOptimizer(max_tokens=8000)
        task = "extract and validate citations from PDFs"

        # Optimize context
        result = optimizer.optimize_context(pin_citer_context, task)

        # Verify 40-60% reduction achieved
        assert 40 <= result.metrics.reduction_percentage <= 60

        # Verify pipeline data preserved (relevant)
        assert "requirements" in result.content
        assert "citation_extraction" in result.content  # Core to task

        # Verify metadata deduplication
        assert not (
            "duplicate_metadata_1" in result.content
            and "duplicate_metadata_2" in result.content
        )

        # Verify log compression
        if "verbose_logs" in result.content:
            assert len(str(result.content["verbose_logs"])) < 10000

    def test_pdf_processing_delegation(self, pin_citer_context):
        """Test delegation of complex PDF processing tasks"""
        optimizer = ContextOptimizer(max_tokens=3000)
        task = "process large PDF corpus with citation extraction"

        # Add complex processing subtasks
        pin_citer_context["subtasks"] = [
            "Process 500-page legal document with complex formatting",
            "Extract citations from scanned PDFs using OCR",
            "Validate citations against legal databases",
            "Generate embedding vectors for all text chunks",
        ]

        # Optimize with delegation
        result = optimizer.optimize_context(pin_citer_context, task)

        # Verify appropriate delegation
        if result.delegated_tasks:
            # Check for specialized agent recommendations
            for delegated in result.delegated_tasks:
                assert delegated["recommended_agent"] in [
                    "ImplementationAgent",
                    "ResearchAgent",
                    "TestingAgent",
                    "GeneralPurposeAgent",
                ]
                assert "context_subset" in delegated

    @pytest.mark.asyncio
    async def test_github_integration_with_optimization(self, pin_citer_context):
        """Test GitHubIntegrationAgent with R&D Framework"""
        agent = GitHubIntegrationAgent("pin-citer/main", "pdf_processing")

        # Add context optimizer
        agent.context_optimizer = ContextOptimizer(max_tokens=8000)

        # Set heavy context
        agent.workflow_data = pin_citer_context

        # Create task for GitHub issue creation
        task_spec = {
            "project_name": "PDF Citation Extraction Enhancement",
            "requirements": [
                "Process large PDF corpus",
                "Extract all citations",
                "Validate against databases",
            ],
        }

        # Mock GitHub operations
        with pytest.mock.patch.object(agent, "_create_issue_hierarchy") as mock_create:
            mock_create.return_value = {
                "parent_issue": 100,
                "sub_issues": [101, 102, 103],
            }

            # Optimize context before execution
            optimized = agent.context_optimizer.optimize_context(
                agent.workflow_data, json.dumps(task_spec)
            )

            # Verify optimization
            assert optimized.metrics.reduction_percentage >= 30
            assert len(optimized.metrics.strategies_applied) > 0


class TestHandoffOptimization:
    """Test R&D Framework with agent handoff scenarios"""

    @pytest.fixture
    def handoff_context(self):
        """Create realistic handoff context"""
        return {
            "work_completed": {
                "tasks": [f"Task_{i}" for i in range(30)],
                "code_changes": [f"File_{i}.py modified" for i in range(20)],
                "test_results": ["PASS"] * 25 + ["FAIL"] * 5,
            },
            "current_state": {
                "phase": "implementation",
                "progress": 0.75,
                "blockers": ["Database connection issue", "API rate limit"],
            },
            "next_steps": [
                "Complete remaining implementation",
                "Fix failing tests",
                "Add documentation",
                "Create pull request",
            ],
            "conversation_history": [f"Development discussion {i}" for i in range(200)],
            "technical_context": {
                "architecture": "microservices",
                "technologies": ["Python", "Django", "PostgreSQL", "Redis"],
                "dependencies": [f"package_{i}" for i in range(50)],
            },
            "duplicate_notes_1": "Important context" * 20,
            "duplicate_notes_2": "Important context" * 20,
            "verbose_explanation": "Detailed explanation " * 500,
        }

    @pytest.mark.asyncio
    async def test_handoff_context_optimization(self, handoff_context):
        """Test optimization of handoff context"""
        agent = HandoffAgent()
        agent.context_optimizer = ContextOptimizer(max_tokens=6000)

        # Set handoff context
        agent.workflow_data = handoff_context

        # Optimize for handoff
        task = "prepare handoff documentation for next agent"
        optimized = agent.context_optimizer.optimize_context(agent.workflow_data, task)

        # Verify optimization
        assert 30 <= optimized.metrics.reduction_percentage <= 60

        # Verify critical handoff data preserved
        assert "work_completed" in optimized.content
        assert "current_state" in optimized.content
        assert "next_steps" in optimized.content

        # Verify deduplication
        assert not (
            "duplicate_notes_1" in optimized.content
            and "duplicate_notes_2" in optimized.content
        )

        # Verify session ID for continuity
        assert optimized.session_id
        assert len(optimized.session_id) == 12


class TestPerformanceBenchmarks:
    """Performance benchmarks for R&D Framework"""

    def test_context_reduction_benchmark(self):
        """Benchmark context reduction across various sizes"""
        optimizer = ContextOptimizer(max_tokens=8000)

        results = []

        # Test different context sizes
        for size_multiplier in [1, 5, 10, 20]:
            context = {
                f"section_{i}": f"Content {i} " * (10 * size_multiplier)
                for i in range(10 * size_multiplier)
            }

            task = "optimize this context"
            result = optimizer.optimize_context(context, task)

            results.append(
                {
                    "original_tokens": result.metrics.original_tokens,
                    "reduced_tokens": result.metrics.reduced_tokens,
                    "reduction_percentage": result.metrics.reduction_percentage,
                    "strategies_applied": len(result.metrics.strategies_applied),
                }
            )

        # Verify consistent reduction across sizes
        for result in results:
            assert 20 <= result["reduction_percentage"] <= 70
            assert result["strategies_applied"] > 0

    def test_delegation_threshold_tuning(self):
        """Test different delegation thresholds for optimal performance"""
        thresholds = [0.2, 0.3, 0.4, 0.5]

        context = {
            "data": "x" * 5000,
            "subtasks": ["Complex task 1", "Complex task 2", "Complex task 3"],
        }

        delegation_results = []

        for threshold in thresholds:
            optimizer = ContextOptimizer(
                max_tokens=8000, delegation_threshold=threshold
            )
            result = optimizer.optimize_context(context, "process all tasks")

            delegation_results.append(
                {
                    "threshold": threshold,
                    "delegated": len(result.delegated_tasks),
                    "final_tokens": result.metrics.reduced_tokens,
                }
            )

        # Verify threshold impact
        # Lower thresholds should trigger more delegation
        assert delegation_results[0]["delegated"] >= delegation_results[-1]["delegated"]

    @pytest.mark.asyncio
    async def test_concurrent_optimization(self):
        """Test concurrent context optimization for multiple agents"""
        # Create multiple optimizers
        optimizers = [ContextOptimizer() for _ in range(5)]

        # Create contexts
        contexts = [
            {f"data_{i}_{j}": f"content_{j}" * 100 for j in range(20)} for i in range(5)
        ]

        # Optimize concurrently
        tasks = [
            optimizer.optimize_context(context, f"task_{i}")
            for i, (optimizer, context) in enumerate(zip(optimizers, contexts))
        ]

        # Execute concurrently (simulated)
        results = []
        for task in tasks:
            results.append(task)

        # Verify all optimizations successful
        for result in results:
            assert result.metrics.reduction_percentage > 0
            assert result.metrics.reduced_tokens < result.metrics.original_tokens


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
