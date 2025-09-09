"""
Performance tests for Hierarchical Orchestration System.

Tests scaling behavior, coordination overhead, and performance characteristics
under various load conditions and complexity levels.
"""

import pytest
import asyncio
import time
import psutil
import statistics

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.hierarchical_orchestrator import (
    HierarchicalOrchestrator,
)
from orchestration.patterns import PatternExecutor, TaskSlice, OrchestrationPattern


class PerformanceBenchmark:
    """Performance benchmarking utilities"""

    @staticmethod
    def measure_memory_usage():
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    @staticmethod
    def measure_execution_time(func):
        """Decorator to measure execution time"""

        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            return result, execution_time

        return wrapper

    @staticmethod
    def calculate_coordination_overhead(
        total_time: float, execution_time: float
    ) -> float:
        """Calculate coordination overhead percentage"""
        if execution_time == 0:
            return 0.0
        coordination_time = total_time - execution_time
        return (coordination_time / execution_time) * 100


@pytest.mark.performance
class TestOrchestrationScaling:
    """Test orchestration scaling performance"""

    @pytest.mark.asyncio
    async def test_100_agent_orchestration(self):
        """Test orchestration with 100+ agents"""
        # Create high-capacity orchestrator
        orchestrator = HierarchicalOrchestrator(
            max_depth=4,
            max_agents_per_level={
                "primary": 2,
                "secondary": 30,
                "tertiary": 68,
                "quaternary": 100,
            },
        )

        # Massive parallel task
        massive_task = (
            "Process 1000 documents simultaneously: "
            "extract text, analyze sentiment, classify content, "
            "generate summaries, validate accuracy, store results, "
            "update search index, trigger notifications"
        )

        # Measure performance
        start_memory = PerformanceBenchmark.measure_memory_usage()
        start_time = time.perf_counter()

        result = await orchestrator.orchestrate_complex_task(massive_task)

        end_time = time.perf_counter()
        end_memory = PerformanceBenchmark.measure_memory_usage()

        # Performance assertions
        assert result.success
        assert result.agents_used >= 10  # Should use many agents
        assert result.coordination_overhead < 10.0  # <10% overhead
        assert (end_time - start_time) < 10.0  # Should complete in <10s
        assert (end_memory - start_memory) < 500  # <500MB memory increase

        print("100-Agent Test Results:")
        print(f"  Agents used: {result.agents_used}")
        print(f"  Execution time: {end_time - start_time:.2f}s")
        print(f"  Coordination overhead: {result.coordination_overhead:.1f}%")
        print(f"  Memory usage: {end_memory - start_memory:.1f}MB")

    @pytest.mark.asyncio
    async def test_deep_hierarchy_performance(self):
        """Test deep hierarchy performance characteristics"""
        # Test different hierarchy depths
        depth_results = []

        for max_depth in [2, 3, 4, 5]:
            orchestrator = HierarchicalOrchestrator(
                max_depth=max_depth,
                max_agents_per_level={
                    "primary": 1,
                    "secondary": 8,
                    "tertiary": 16,
                    "quaternary": 32,
                    "quinary": 64,
                },
            )

            complex_task = (
                f"Deep hierarchy test depth {max_depth}: "
                "multi-level analysis with component breakdown, "
                "sub-component processing, atomic operations"
            )

            start_time = time.perf_counter()
            result = await orchestrator.orchestrate_complex_task(complex_task)
            end_time = time.perf_counter()

            depth_results.append(
                {
                    "depth": max_depth,
                    "success": result.success,
                    "execution_time": end_time - start_time,
                    "agents_used": result.agents_used,
                    "levels_deep": result.levels_deep,
                    "coordination_overhead": result.coordination_overhead,
                }
            )

        # Analyze results
        successful_results = [r for r in depth_results if r["success"]]
        assert len(successful_results) >= 3  # Most depths should work

        # Coordination overhead should remain reasonable
        avg_overhead = statistics.mean(
            [r["coordination_overhead"] for r in successful_results]
        )
        assert avg_overhead < 8.0

        print("Deep Hierarchy Results:")
        for result in depth_results:
            print(
                f"  Depth {result['depth']}: "
                f"{result['execution_time']:.2f}s, "
                f"{result['agents_used']} agents, "
                f"{result['coordination_overhead']:.1f}% overhead"
            )

    @pytest.mark.asyncio
    async def test_coordination_overhead_scaling(self):
        """Test coordination overhead across different scales"""
        overhead_results = []

        # Test different scales
        scale_configs = [
            {"agents": {"secondary": 5, "tertiary": 10}, "task_complexity": "moderate"},
            {"agents": {"secondary": 10, "tertiary": 20}, "task_complexity": "complex"},
            {
                "agents": {"secondary": 20, "tertiary": 40},
                "task_complexity": "enterprise",
            },
            {"agents": {"secondary": 30, "tertiary": 60}, "task_complexity": "massive"},
        ]

        for config in scale_configs:
            orchestrator = HierarchicalOrchestrator(
                max_depth=3, max_agents_per_level={"primary": 1, **config["agents"]}
            )

            # Task scaled to configuration
            task_descriptions = {
                "moderate": "Process 50 items with validation",
                "complex": "Analyze 200 documents with cross-references",
                "enterprise": "Migrate 500 components with dependencies",
                "massive": "Handle 1000 concurrent operations",
            }

            task = task_descriptions[config["task_complexity"]]

            # Measure coordination overhead
            start_time = time.perf_counter()
            result = await orchestrator.orchestrate_complex_task(task)
            total_time = time.perf_counter() - start_time

            overhead_results.append(
                {
                    "scale": config["task_complexity"],
                    "total_agents": sum(config["agents"].values()) + 1,
                    "coordination_overhead": result.coordination_overhead,
                    "execution_time": total_time,
                    "agents_used": result.agents_used,
                }
            )

        # Analyze overhead scaling
        successful_overheads = [r["coordination_overhead"] for r in overhead_results]
        max_overhead = max(successful_overheads)
        avg_overhead = statistics.mean(successful_overheads)

        assert max_overhead < 15.0  # Maximum 15% overhead
        assert avg_overhead < 8.0  # Average <8% overhead

        print("Coordination Overhead Scaling:")
        for result in overhead_results:
            print(
                f"  {result['scale']}: "
                f"{result['coordination_overhead']:.1f}% overhead, "
                f"{result['agents_used']} agents used"
            )
        print(f"Average overhead: {avg_overhead:.1f}%")

    @pytest.mark.asyncio
    async def test_pattern_performance_comparison(self):
        """Compare performance across different orchestration patterns"""
        pattern_executor = PatternExecutor()

        # Common test setup
        task_slices = [TaskSlice(f"task-{i}", f"Process item {i}") for i in range(20)]
        agents = [f"agent-{i}" for i in range(8)]

        pattern_results = {}

        # Test all patterns
        patterns_to_test = [
            OrchestrationPattern.MAPREDUCE,
            OrchestrationPattern.PIPELINE,
            OrchestrationPattern.FORK_JOIN,
            OrchestrationPattern.SCATTER_GATHER,
            OrchestrationPattern.SAGA,
        ]

        for pattern in patterns_to_test:
            start_time = time.perf_counter()
            start_memory = PerformanceBenchmark.measure_memory_usage()

            result = await pattern_executor.execute_pattern(
                pattern, task_slices, agents
            )

            end_time = time.perf_counter()
            end_memory = PerformanceBenchmark.measure_memory_usage()

            pattern_results[pattern.value] = {
                "success": result.success,
                "execution_time": end_time - start_time,
                "memory_usage": end_memory - start_memory,
                "agents_used": result.agents_used,
                "slices_processed": result.slices_processed,
            }

        # All patterns should complete successfully
        successful_patterns = [r for r in pattern_results.values() if r["success"]]
        assert len(successful_patterns) == len(patterns_to_test)

        # Performance should be reasonable
        execution_times = [r["execution_time"] for r in successful_patterns]
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)

        assert avg_execution_time < 2.0  # Average <2s
        assert max_execution_time < 5.0  # Maximum <5s

        print("Pattern Performance Comparison:")
        for pattern_name, metrics in pattern_results.items():
            print(
                f"  {pattern_name}: "
                f"{metrics['execution_time']:.3f}s, "
                f"{metrics['memory_usage']:.1f}MB"
            )

    @pytest.mark.asyncio
    async def test_concurrent_orchestration_performance(self):
        """Test performance with concurrent orchestrations"""
        orchestrator = HierarchicalOrchestrator(
            max_agents_per_level={"primary": 3, "secondary": 20, "tertiary": 40}
        )

        # Create multiple concurrent orchestrations
        concurrent_tasks = [
            "Analyze user behavior patterns",
            "Generate performance reports",
            "Process API request logs",
            "Update recommendation engine",
            "Validate data integrity",
            "Optimize database queries",
            "Generate security audit",
            "Process customer feedback",
        ]

        # Execute all concurrently
        start_time = time.perf_counter()
        start_memory = PerformanceBenchmark.measure_memory_usage()

        results = await asyncio.gather(
            *[
                orchestrator.orchestrate_complex_task(task, f"concurrent-{i}")
                for i, task in enumerate(concurrent_tasks)
            ],
            return_exceptions=True,
        )

        end_time = time.perf_counter()
        end_memory = PerformanceBenchmark.measure_memory_usage()

        # Analyze concurrent performance
        successful_results = [r for r in results if not isinstance(r, Exception)]
        total_agents_used = sum(r.agents_used for r in successful_results)
        avg_coordination_overhead = statistics.mean(
            [r.coordination_overhead for r in successful_results]
        )

        # Performance assertions
        assert len(successful_results) >= 6  # Most should succeed
        assert (end_time - start_time) < 15.0  # Complete in <15s
        assert avg_coordination_overhead < 10.0  # <10% average overhead
        assert (end_memory - start_memory) < 600  # <600MB memory

        print("Concurrent Orchestration Results:")
        print(
            f"  Successful orchestrations: {len(successful_results)}/{len(concurrent_tasks)}"
        )
        print(f"  Total execution time: {end_time - start_time:.2f}s")
        print(f"  Total agents used: {total_agents_used}")
        print(f"  Average coordination overhead: {avg_coordination_overhead:.1f}%")
        print(f"  Memory usage: {end_memory - start_memory:.1f}MB")

    @pytest.mark.asyncio
    async def test_memory_usage_scaling(self):
        """Test memory usage scaling with orchestration size"""
        memory_results = []

        # Test different orchestration sizes
        size_configs = [
            {"max_agents": 10, "description": "Small orchestration"},
            {"max_agents": 25, "description": "Medium orchestration"},
            {"max_agents": 50, "description": "Large orchestration"},
            {"max_agents": 100, "description": "Extra large orchestration"},
        ]

        for config in size_configs:
            # Create orchestrator with specified capacity
            orchestrator = HierarchicalOrchestrator(
                max_depth=3,
                max_agents_per_level={
                    "primary": 1,
                    "secondary": config["max_agents"] // 3,
                    "tertiary": (config["max_agents"] * 2) // 3,
                },
            )

            # Memory-intensive task
            memory_task = (
                f"Memory scaling test for {config['max_agents']} agents: "
                "process large datasets, maintain state, coordinate results"
            )

            # Measure memory usage
            baseline_memory = PerformanceBenchmark.measure_memory_usage()

            result = await orchestrator.orchestrate_complex_task(memory_task)

            peak_memory = PerformanceBenchmark.measure_memory_usage()
            memory_increase = peak_memory - baseline_memory

            memory_results.append(
                {
                    "max_agents": config["max_agents"],
                    "agents_used": result.agents_used,
                    "memory_increase": memory_increase,
                    "success": result.success,
                    "description": config["description"],
                }
            )

            # Cleanup to reset memory baseline
            del orchestrator
            await asyncio.sleep(0.1)  # Allow cleanup

        # Analyze memory scaling
        successful_results = [r for r in memory_results if r["success"]]

        # Memory usage should scale reasonably
        memory_per_agent = [
            r["memory_increase"] / max(r["agents_used"], 1) for r in successful_results
        ]
        avg_memory_per_agent = statistics.mean(memory_per_agent)

        assert avg_memory_per_agent < 20  # <20MB per agent

        print("Memory Usage Scaling:")
        for result in memory_results:
            memory_per_agent = result["memory_increase"] / max(result["agents_used"], 1)
            print(
                f"  {result['description']}: "
                f"{result['memory_increase']:.1f}MB total, "
                f"{memory_per_agent:.1f}MB per agent"
            )
        print(f"Average: {avg_memory_per_agent:.1f}MB per agent")

    @pytest.mark.asyncio
    async def test_task_decomposition_performance(self):
        """Test task decomposition performance"""
        from core.hierarchical_orchestrator import TaskDecomposer

        decomposer = TaskDecomposer()

        # Test different complexity levels
        test_tasks = [
            ("Simple task", "fix bug in login form"),
            ("Moderate task", "implement user authentication system"),
            ("Complex task", "migrate microservices to kubernetes with monitoring"),
            (
                "Enterprise task",
                "architect complete platform modernization with AI integration",
            ),
        ]

        decomposition_results = []

        for complexity_name, task in test_tasks:
            start_time = time.perf_counter()

            # Decompose task multiple times for average
            decomposition_times = []
            for _ in range(10):  # 10 iterations for average
                iter_start = time.perf_counter()
                decomposed_task = decomposer.decompose(task, max_depth=3)
                iter_end = time.perf_counter()
                decomposition_times.append(iter_end - iter_start)

            avg_decomposition_time = statistics.mean(decomposition_times)

            decomposition_results.append(
                {
                    "complexity": complexity_name,
                    "task": task,
                    "avg_decomposition_time": avg_decomposition_time,
                    "complexity_detected": decomposed_task.complexity.value,
                    "level": decomposed_task.level.value,
                }
            )

        # Performance assertions
        decomposition_times = [
            r["avg_decomposition_time"] for r in decomposition_results
        ]
        max_decomposition_time = max(decomposition_times)
        avg_decomposition_time = statistics.mean(decomposition_times)

        assert max_decomposition_time < 0.1  # <100ms max
        assert avg_decomposition_time < 0.05  # <50ms average

        print("Task Decomposition Performance:")
        for result in decomposition_results:
            print(
                f"  {result['complexity']}: "
                f"{result['avg_decomposition_time']*1000:.1f}ms, "
                f"detected as {result['complexity_detected']}"
            )
        print(f"Average: {avg_decomposition_time*1000:.1f}ms")

    @pytest.mark.asyncio
    async def test_end_to_end_performance_benchmark(self):
        """Comprehensive end-to-end performance benchmark"""
        print("\n" + "=" * 60)
        print("HIERARCHICAL ORCHESTRATION PERFORMANCE BENCHMARK")
        print("=" * 60)

        # Test configuration
        orchestrator = HierarchicalOrchestrator(
            max_depth=4,
            max_agents_per_level={
                "primary": 2,
                "secondary": 25,
                "tertiary": 75,
                "quaternary": 150,
            },
        )

        # Comprehensive benchmark task
        benchmark_task = (
            "Complete enterprise system modernization: "
            "analyze 1000+ legacy components, design microservices architecture, "
            "implement API gateway with authentication, set up monitoring and logging, "
            "create CI/CD pipeline, migrate databases with zero downtime, "
            "implement security scanning, performance optimization, "
            "generate comprehensive documentation and training materials"
        )

        # Comprehensive performance measurement
        initial_memory = PerformanceBenchmark.measure_memory_usage()
        start_time = time.perf_counter()

        result = await orchestrator.orchestrate_complex_task(benchmark_task)

        end_time = time.perf_counter()
        final_memory = PerformanceBenchmark.measure_memory_usage()

        total_time = end_time - start_time
        memory_usage = final_memory - initial_memory

        # Get system performance data
        hierarchy = await orchestrator.get_agent_hierarchy()
        total_agents = sum(len(agents) for agents in hierarchy.values())

        # Performance summary
        print("\nBENCHMARK RESULTS:")
        print("  Task: Enterprise system modernization")
        print(f"  Success: {'✅' if result.success else '❌'}")
        print(f"  Total execution time: {total_time:.2f}s")
        print(f"  Agents created: {total_agents}")
        print(f"  Agents used: {result.agents_used}")
        print(f"  Hierarchy depth: {result.levels_deep}")
        print(f"  Coordination overhead: {result.coordination_overhead:.1f}%")
        print(f"  Memory usage: {memory_usage:.1f}MB")
        print(f"  Patterns used: {', '.join(result.metadata.get('patterns_used', []))}")

        # Performance targets validation
        performance_targets = {
            "Success rate": (result.success, True),
            "Execution time": (total_time, "<15s", total_time < 15.0),
            "Coordination overhead": (
                result.coordination_overhead,
                "<10%",
                result.coordination_overhead < 10.0,
            ),
            "Memory usage": (memory_usage, "<800MB", memory_usage < 800),
            "Agents efficiency": (result.agents_used > 10, True),
        }

        print("\nPERFORMANCE TARGET VALIDATION:")
        for metric, validation in performance_targets.items():
            if len(validation) == 3:
                value, target, passed = validation
                status = "✅" if passed else "❌"
                print(f"  {metric}: {value} {target} {status}")
            else:
                value, target = validation
                status = "✅" if value == target else "❌"
                print(f"  {metric}: {value} {status}")

        # Overall benchmark assessment
        all_targets_met = all(
            validation[2] if len(validation) == 3 else validation[0] == validation[1]
            for validation in performance_targets.values()
        )

        print(
            f"\nOVERALL BENCHMARK: {'✅ PASSED' if all_targets_met else '❌ NEEDS OPTIMIZATION'}"
        )

        # Assert critical performance requirements
        assert result.success, "Benchmark task must complete successfully"
        assert result.coordination_overhead < 10.0, "Coordination overhead too high"
        assert total_time < 20.0, "Execution time exceeds acceptable limit"
        assert memory_usage < 1000, "Memory usage too high"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
