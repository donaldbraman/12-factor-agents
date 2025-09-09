"""Context efficiency benchmarks for 12-factor agents"""
import pytest
import time
import signal
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))


def timeout_handler(signum, frame):
    raise TimeoutError("Benchmark exceeded time limit")


class TestContextEfficiency:
    """Validate 95% context efficiency target"""

    @pytest.fixture(autouse=True)
    def setup_timeout(self):
        """Apply timeout protection to all tests"""
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30 second maximum
        yield
        signal.alarm(0)  # Cancel timeout

    def test_context_window_usage(self):
        """Test context window efficiency stays above 95%"""
        from core.context_manager import ContextManager

        manager = ContextManager(max_tokens=100000)

        # Simulate agent operations
        for i in range(100):
            manager.add_context(f"Operation {i}", priority=i % 3)

        efficiency = manager.get_efficiency()
        assert (
            efficiency >= 0.95
        ), f"Context efficiency {efficiency:.2%} below 95% target"

    def test_context_pruning_performance(self):
        """Benchmark context pruning speed"""
        from core.context_manager import ContextManager

        manager = ContextManager(max_tokens=50000)

        # Fill context
        start = time.perf_counter()
        for i in range(1000):
            manager.add_context(f"Data chunk {i}" * 100)
        add_time = time.perf_counter() - start

        # Prune context
        start = time.perf_counter()
        manager.prune_to_fit()
        prune_time = time.perf_counter() - start

        assert prune_time < 0.1, f"Pruning took {prune_time:.3f}s, target < 0.1s"
        print(f"✅ Context operations: add={add_time:.3f}s, prune={prune_time:.3f}s")

    def test_context_recovery(self):
        """Test context recovery after handoff"""
        from core.context_manager import ContextManager

        manager = ContextManager()
        manager.add_context("Critical info", priority=3)

        # Simulate handoff
        snapshot = manager.create_snapshot()
        new_manager = ContextManager()

        start = time.perf_counter()
        new_manager.restore_snapshot(snapshot)
        recovery_time = time.perf_counter() - start

        assert (
            recovery_time < 0.004
        ), f"Recovery took {recovery_time:.3f}s, target < 0.004s"
        assert new_manager.get_context("Critical info") is not None
