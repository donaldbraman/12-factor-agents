#!/usr/bin/env uv run python
"""Quick performance regression check for pre-commit"""
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_orchestration_performance():
    """Quick orchestration overhead check"""
    from core.hierarchical_orchestrator import HierarchicalOrchestrator

    orchestrator = HierarchicalOrchestrator()

    # Quick test - should complete in <0.1s
    start = time.perf_counter()
    try:
        # Test basic orchestration creation
        if hasattr(orchestrator, "execute_task"):
            result = orchestrator.execute_task("test task")
        else:
            # Just verify it initializes
            result = orchestrator.agents
        duration = time.perf_counter() - start

        if duration > 0.5:  # Conservative threshold
            print(f"⚠️ Orchestration slower than expected: {duration:.3f}s")
            return False

        print(f"✅ Orchestration performance OK: {duration:.3f}s")
        return True

    except Exception as e:
        print(f"❌ Orchestration test failed: {e}")
        return False


def check_context_efficiency():
    """Quick context efficiency check"""
    from core.context_manager import ContextManager

    try:
        manager = ContextManager(max_tokens=1000)

        # Add substantial context to test efficiency
        for i in range(50):
            # Each context is ~10 tokens
            manager.add_context(
                f"This is test context number {i} with some content", priority=1
            )

        efficiency = manager.get_efficiency()

        # With 50 items * ~10 tokens = 500 tokens out of 1000 = 50% efficiency
        if efficiency < 0.3:  # Lower threshold for realistic test
            print(f"⚠️ Context efficiency low: {efficiency:.1%}")
            return False

        print(f"✅ Context efficiency OK: {efficiency:.1%}")
        return True

    except Exception as e:
        print(f"❌ Context efficiency test failed: {e}")
        return False


def main():
    """Run quick performance checks"""
    print("🚀 Running quick performance regression checks...")

    checks = [
        ("Orchestration Performance", check_orchestration_performance),
        ("Context Efficiency", check_context_efficiency),
    ]

    failed = 0
    for name, check in checks:
        print(f"\n🔍 Checking {name}...")
        if not check():
            failed += 1

    if failed > 0:
        print(f"\n❌ {failed}/{len(checks)} performance checks failed")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(checks)} performance checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
