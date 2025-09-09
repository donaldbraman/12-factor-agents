#!/usr/bin/env uv run python
"""
Performance benchmark for R&D Framework Context Optimizer
Validates 40-60% context reduction across various workloads
"""

import sys
import os
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from statistics import mean

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.context_optimizer import ContextOptimizer


@dataclass
class BenchmarkResult:
    """Results from a benchmark run"""

    workload_name: str
    original_tokens: int
    reduced_tokens: int
    reduction_percentage: float
    optimization_time: float
    strategies_applied: List[str]
    delegation_triggered: bool
    cost_savings: float


class ContextOptimizationBenchmark:
    """Benchmark suite for R&D Framework validation"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []

    def create_cite_assist_workload(self) -> Dict[str, Any]:
        """Create realistic cite-assist legal research workload"""
        return {
            "legal_research": {
                "case_law": [
                    f"Case {i}: " + "Legal precedent analysis " * 10 for i in range(100)
                ],
                "statutes": [
                    f"Statute {i}: " + "Legislative text " * 8 for i in range(50)
                ],
                "regulations": [
                    f"Reg {i}: " + "Regulatory framework " * 6 for i in range(30)
                ],
            },
            "citation_scoring": {
                "adequacy_metrics": [0.8, 0.9, 0.7, 0.85, 0.92] * 40,
                "relevance_scores": [0.85, 0.92, 0.78, 0.88, 0.91] * 40,
                "completeness": [0.9, 0.88, 0.91, 0.87, 0.93] * 40,
            },
            "zotero_integration": {
                "library_items": [
                    f"Item_{i}: Research paper abstract" for i in range(200)
                ],
                "collections": [
                    f"Collection_{i}: Category description" for i in range(20)
                ],
                "tags": [f"Tag_{i}" for i in range(50)],
            },
            "conversation_history": [
                f"User: Legal question {i}\nAssistant: Detailed legal response with citations"
                for i in range(150)
            ],
            "duplicate_analysis_1": "Important legal precedent analysis " * 50,
            "duplicate_analysis_2": "Important legal precedent analysis " * 50,
            "verbose_documentation": "Detailed legal documentation and notes " * 200,
            "requirements": "Analyze citation adequacy for Supreme Court brief on constitutional law",
        }

    def create_pin_citer_workload(self) -> Dict[str, Any]:
        """Create realistic pin-citer PDF processing workload"""
        return {
            "pdf_metadata": {
                "documents": [f"Document_{i}.pdf: 500 pages" for i in range(50)],
                "pages": list(range(1, 500)),
                "extracted_text": [
                    "Page text content with citations " * 50 for _ in range(100)
                ],
            },
            "processing_pipeline": {
                "stages": [
                    "download",
                    "extract",
                    "chunk",
                    "embed",
                    "index",
                    "validate",
                ],
                "status": ["completed"] * 3 + ["in_progress"] + ["pending"] * 2,
                "metrics": {
                    "pages_processed": 250,
                    "chunks_created": 1000,
                    "embeddings_generated": 750,
                    "citations_extracted": 500,
                },
            },
            "citation_extraction": {
                "citations": [f"Citation_{i}: Author et al., 2024" for i in range(200)],
                "references": [
                    f"Reference_{i}: Full bibliographic entry" for i in range(150)
                ],
                "footnotes": [f"Footnote_{i}: Explanatory note" for i in range(100)],
            },
            "conversation_history": [
                f"Processing status update {i}" for i in range(200)
            ],
            "duplicate_metadata": [{"doc": "metadata"} for _ in range(100)],
            "verbose_logs": "Detailed processing log entry with timestamps\n" * 500,
            "requirements": "Extract and validate all citations from large PDF corpus",
        }

    def create_complex_workload(self) -> Dict[str, Any]:
        """Create complex multi-domain workload"""
        return {
            "project_overview": "Build comprehensive AI agent system " * 20,
            "technical_requirements": [
                f"Requirement {i}: " + "Detailed technical specification " * 5
                for i in range(30)
            ],
            "architecture": {
                "components": [f"Component_{i}" for i in range(50)],
                "services": [f"Service_{i}" for i in range(30)],
                "databases": ["PostgreSQL", "Redis", "MongoDB", "Elasticsearch"],
                "queues": ["RabbitMQ", "Kafka", "SQS"],
            },
            "implementation_details": {
                "code_files": [f"file_{i}.py" for i in range(100)],
                "test_files": [f"test_{i}.py" for i in range(50)],
                "documentation": [f"doc_{i}.md" for i in range(20)],
            },
            "conversation_history": [
                f"Discussion {i}: Technical design conversation" for i in range(300)
            ],
            "duplicate_specs_1": "System specification document " * 100,
            "duplicate_specs_2": "System specification document " * 100,
            "duplicate_specs_3": "System specification document " * 100,
            "verbose_notes": "Detailed implementation notes and comments " * 300,
            "subtasks": [
                "Implement authentication system with OAuth2 and JWT tokens",
                "Build real-time notification system using WebSockets",
                "Create data processing pipeline with Apache Spark",
                "Develop machine learning model for recommendation engine",
                "Implement distributed caching with Redis cluster",
            ],
            "requirements": "Design and implement distributed AI agent system",
        }

    def run_benchmark(
        self,
        workload_name: str,
        context: Dict[str, Any],
        task: str,
        max_tokens: int = 8000,
    ) -> BenchmarkResult:
        """Run optimization benchmark on a workload"""
        optimizer = ContextOptimizer(max_tokens=max_tokens, delegation_threshold=0.3)

        # Measure optimization time
        start_time = time.time()
        result = optimizer.optimize_context(context, task)
        optimization_time = time.time() - start_time

        # Create benchmark result
        return BenchmarkResult(
            workload_name=workload_name,
            original_tokens=result.metrics.original_tokens,
            reduced_tokens=result.metrics.reduced_tokens,
            reduction_percentage=result.metrics.reduction_percentage,
            optimization_time=optimization_time,
            strategies_applied=result.metrics.strategies_applied,
            delegation_triggered=result.metrics.delegation_recommended,
            cost_savings=result.metrics.estimated_cost_savings,
        )

    def run_all_benchmarks(self):
        """Run benchmarks on all workloads"""
        print("=" * 80)
        print("R&D FRAMEWORK CONTEXT OPTIMIZATION BENCHMARKS")
        print("=" * 80)
        print()

        # Define workloads
        workloads = [
            (
                "cite-assist Legal Research",
                self.create_cite_assist_workload(),
                "analyze citation adequacy for Supreme Court brief",
            ),
            (
                "pin-citer PDF Processing",
                self.create_pin_citer_workload(),
                "extract and validate citations from PDFs",
            ),
            (
                "Complex Multi-Domain",
                self.create_complex_workload(),
                "implement distributed AI agent system",
            ),
        ]

        # Run benchmarks
        for name, context, task in workloads:
            print(f"Running benchmark: {name}")
            result = self.run_benchmark(name, context, task)
            self.results.append(result)
            self.print_result(result)
            print()

        # Print summary
        self.print_summary()

    def print_result(self, result: BenchmarkResult):
        """Print individual benchmark result"""
        print(f"  Original tokens: {result.original_tokens:,}")
        print(f"  Reduced tokens:  {result.reduced_tokens:,}")
        print(f"  Reduction:       {result.reduction_percentage:.1f}%")
        print(f"  Time taken:      {result.optimization_time:.3f} seconds")
        print(f"  Strategies:      {', '.join(result.strategies_applied)}")
        print(f"  Delegation:      {'Yes' if result.delegation_triggered else 'No'}")
        print(f"  Cost savings:    ${result.cost_savings:.4f}")

        # Validation
        if 40 <= result.reduction_percentage <= 60:
            print(f"  ✅ TARGET MET: {result.reduction_percentage:.1f}% reduction")
        else:
            print(
                f"  ⚠️  Outside target range (40-60%): {result.reduction_percentage:.1f}%"
            )

    def print_summary(self):
        """Print benchmark summary"""
        print("=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        print()

        # Calculate statistics
        reductions = [r.reduction_percentage for r in self.results]
        times = [r.optimization_time for r in self.results]
        savings = [r.cost_savings for r in self.results]

        avg_reduction = mean(reductions)
        avg_time = mean(times)
        total_savings = sum(savings)

        print(f"Average reduction:     {avg_reduction:.1f}%")
        print(f"Reduction range:       {min(reductions):.1f}% - {max(reductions):.1f}%")
        print(f"Average time:          {avg_time:.3f} seconds")
        print(f"Total cost savings:    ${total_savings:.4f}")
        print()

        # Target validation
        in_target = sum(1 for r in reductions if 40 <= r <= 60)
        total = len(reductions)

        print("Target Achievement (40-60% reduction):")
        print(f"  {in_target}/{total} workloads in target range")
        print(f"  Success rate: {(in_target/total)*100:.0f}%")
        print()

        if avg_reduction >= 40 and avg_reduction <= 60:
            print(
                "✅ OVERALL TARGET MET: Average reduction of {:.1f}% is within 40-60% target range".format(
                    avg_reduction
                )
            )
        else:
            print(
                "⚠️  Average reduction of {:.1f}% is outside 40-60% target range".format(
                    avg_reduction
                )
            )

        # Performance analysis
        print()
        print("Performance Analysis:")
        print(
            f"  Tokens saved:  {sum(r.original_tokens - r.reduced_tokens for r in self.results):,}"
        )
        print(
            f"  Throughput:    {sum(r.original_tokens for r in self.results) / sum(times):.0f} tokens/second"
        )

        # Strategy usage
        print()
        print("Strategy Usage:")
        all_strategies = []
        for r in self.results:
            all_strategies.extend(r.strategies_applied)

        strategy_counts = {}
        for s in all_strategies:
            strategy_counts[s] = strategy_counts.get(s, 0) + 1

        for strategy, count in sorted(
            strategy_counts.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {strategy}: {count} times")

        # Delegation analysis
        print()
        delegations = sum(1 for r in self.results if r.delegation_triggered)
        print(
            f"Delegation triggered: {delegations}/{total} workloads ({(delegations/total)*100:.0f}%)"
        )


def main():
    """Run the benchmark suite"""
    benchmark = ContextOptimizationBenchmark()
    benchmark.run_all_benchmarks()

    # Return exit code based on success
    avg_reduction = mean([r.reduction_percentage for r in benchmark.results])
    if 40 <= avg_reduction <= 60:
        print("\n🎉 SUCCESS: R&D Framework achieves target reduction!")
        return 0
    else:
        print("\n⚠️  WARNING: R&D Framework outside target range")
        return 1


if __name__ == "__main__":
    exit(main())
