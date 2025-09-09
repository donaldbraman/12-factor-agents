"""Orchestration overhead benchmarks"""

import pytest
import time
import signal
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))


def timeout_handler(signum, frame):
    raise TimeoutError("Benchmark exceeded time limit")


class TestOrchestrationOverhead:
    """Validate <5% coordination overhead target"""

    @pytest.fixture(autouse=True)
    def setup_timeout(self):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        yield
        signal.alarm(0)

    def test_hierarchical_overhead(self):
        """Measure hierarchical orchestration overhead"""
        from core.hierarchical_orchestrator import HierarchicalOrchestrator

        orchestrator = HierarchicalOrchestrator()

        # Measure task execution without orchestration
        start = time.perf_counter()
        for i in range(100):
            result = i * 2  # Simple task
        direct_time = time.perf_counter() - start

        # Measure with orchestration
        start = time.perf_counter()
        orchestrator.execute_task("multiply", [(i, 2) for i in range(100)])
        orchestrated_time = time.perf_counter() - start

        overhead = (orchestrated_time - direct_time) / direct_time
        assert overhead < 0.05, f"Overhead {overhead:.1%} exceeds 5% target"
        print(f"✅ Orchestration overhead: {overhead:.2%}")

    def test_agent_coordination_scaling(self):
        """Test coordination with increasing agent count"""
        from core.hierarchical_orchestrator import HierarchicalOrchestrator

        results = {}
        for agent_count in [10, 50, 100]:
            orchestrator = HierarchicalOrchestrator(max_agents=agent_count)

            start = time.perf_counter()
            orchestrator.coordinate_agents(agent_count)
            coord_time = time.perf_counter() - start

            overhead_per_agent = coord_time / agent_count * 1000  # ms per agent
            results[agent_count] = overhead_per_agent

            assert (
                overhead_per_agent < 5
            ), f"Per-agent overhead {overhead_per_agent:.1f}ms exceeds 5ms"

        print(f"✅ Coordination scaling: {results}")

    def test_pattern_performance(self):
        """Benchmark all 5 coordination patterns"""
        from orchestration.patterns import OrchestrationPattern, PatternExecutor

        patterns = [
            OrchestrationPattern.MAPREDUCE,
            OrchestrationPattern.PIPELINE,
            OrchestrationPattern.FORK_JOIN,
            OrchestrationPattern.SCATTER_GATHER,
            OrchestrationPattern.SAGA,
        ]

        for pattern in patterns:
            executor = PatternExecutor(pattern)

            start = time.perf_counter()
            result = executor.execute(range(100))
            exec_time = time.perf_counter() - start

            assert (
                exec_time < 1.0
            ), f"{pattern.value} took {exec_time:.2f}s, target < 1s"
            print(f"✅ {pattern.value}: {exec_time:.3f}s")
