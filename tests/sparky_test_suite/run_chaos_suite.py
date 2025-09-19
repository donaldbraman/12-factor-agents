#!/usr/bin/env python3
"""
SPARKY Chaos Engineering Test Suite Runner

Executes Level 5 chaos tests that simulate real-world production failures
and stress conditions. Tests SPARKY 6.0's resilience, recovery capabilities,
and graceful degradation under extreme conditions.
"""

import asyncio
import json
import sys
import time
import random
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.sparky_6_async import ExecutionContext, launch_sparky, resume_sparky


class ChaosType(Enum):
    TEST_FAILURE_CASCADE = "test_failure_cascade"
    RESOURCE_CONFLICTS = "resource_conflicts"
    STATE_CORRUPTION = "state_corruption"
    API_RATE_LIMITS = "api_rate_limits"
    MEMORY_PRESSURE = "memory_pressure"


@dataclass
class ChaosResult:
    test_name: str
    chaos_type: ChaosType
    success: bool
    execution_time: float
    recovery_time: Optional[float]
    error_details: Optional[str]
    resilience_score: float  # 0-100


class ChaosOrchestrator:
    """Orchestrates chaos engineering tests with realistic failure simulation"""

    def __init__(self):
        self.results: List[ChaosResult] = []
        self.chaos_suite_dir = Path(__file__).parent / "issues" / "level_5_chaos"

    async def run_chaos_suite(self) -> Dict:
        """Run all chaos engineering tests"""
        print("🔥 SPARKY Chaos Engineering Suite")
        print("=" * 50)

        chaos_tests = [
            ("001-test-failure-cascade.md", ChaosType.TEST_FAILURE_CASCADE),
            ("002-concurrent-resource-conflicts.md", ChaosType.RESOURCE_CONFLICTS),
            ("003-state-corruption-recovery.md", ChaosType.STATE_CORRUPTION),
            ("004-api-rate-limit-cascade.md", ChaosType.API_RATE_LIMITS),
            ("005-memory-pressure-fragmentation.md", ChaosType.MEMORY_PRESSURE),
        ]

        total_tests = len(chaos_tests)
        passed_tests = 0

        for i, (test_file, chaos_type) in enumerate(chaos_tests, 1):
            print(f"\n🎯 Test {i}/{total_tests}: {chaos_type.value}")
            print("-" * 40)

            result = await self._run_chaos_test(test_file, chaos_type)
            self.results.append(result)

            if result.success:
                passed_tests += 1
                print(f"✅ PASSED - Resilience: {result.resilience_score:.1f}%")
            else:
                print(f"❌ FAILED - {result.error_details}")

            if result.recovery_time:
                print(f"🔄 Recovery Time: {result.recovery_time:.2f}s")

        # Generate summary report
        success_rate = (passed_tests / total_tests) * 100
        avg_resilience = sum(r.resilience_score for r in self.results) / total_tests

        print("\n🏆 CHAOS SUITE SUMMARY")
        print("=" * 50)
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"Average Resilience Score: {avg_resilience:.1f}%")
        print(
            f"Total Execution Time: {sum(r.execution_time for r in self.results):.2f}s"
        )

        return {
            "success_rate": success_rate,
            "average_resilience": avg_resilience,
            "results": [self._result_to_dict(r) for r in self.results],
        }

    async def _run_chaos_test(
        self, test_file: str, chaos_type: ChaosType
    ) -> ChaosResult:
        """Run individual chaos test with failure simulation"""
        start_time = time.time()

        try:
            # Launch SPARKY with chaos test issue
            issue_path = self.chaos_suite_dir / test_file
            context = await launch_sparky(issue_path)

            # Simulate chaos conditions based on test type
            chaos_events = await self._simulate_chaos(context, chaos_type)

            # Monitor execution and recovery
            recovery_start = None
            while context.current_state.name in [
                "RUNNING",
                "PAUSED",
                "WAITING_FOR_TESTS",
            ]:
                if context.pause_reason and not recovery_start:
                    recovery_start = time.time()

                # Simulate external events and resume
                event_data = await self._generate_chaos_event(chaos_type)
                context = await resume_sparky(context.agent_id, event_data)

                await asyncio.sleep(0.1)  # Prevent tight loop

                # Timeout protection
                if time.time() - start_time > 300:  # 5 minute timeout
                    raise Exception("Chaos test timeout - agent failed to complete")

            execution_time = time.time() - start_time
            recovery_time = (time.time() - recovery_start) if recovery_start else None

            # Calculate resilience score based on performance under chaos
            resilience_score = self._calculate_resilience(
                context, chaos_events, execution_time, recovery_time
            )

            success = context.current_state.name == "COMPLETED"

            return ChaosResult(
                test_name=test_file,
                chaos_type=chaos_type,
                success=success,
                execution_time=execution_time,
                recovery_time=recovery_time,
                error_details=None if success else "Agent failed to complete",
                resilience_score=resilience_score,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ChaosResult(
                test_name=test_file,
                chaos_type=chaos_type,
                success=False,
                execution_time=execution_time,
                recovery_time=None,
                error_details=str(e),
                resilience_score=0.0,
            )

    async def _simulate_chaos(
        self, context: ExecutionContext, chaos_type: ChaosType
    ) -> List[Dict]:
        """Simulate chaos conditions specific to test type"""
        events = []

        if chaos_type == ChaosType.TEST_FAILURE_CASCADE:
            # Simulate cascading test failures
            events.append(
                {
                    "type": "test_failure_cascade",
                    "initial_failures": 47,
                    "cascade_pattern": [47, 23, 8, 0],
                }
            )

        elif chaos_type == ChaosType.RESOURCE_CONFLICTS:
            # Simulate resource contention
            events.append(
                {
                    "type": "resource_conflicts",
                    "concurrent_agents": 5,
                    "git_lock_timeout": 15,
                    "db_pool_exhausted": True,
                }
            )

        elif chaos_type == ChaosType.STATE_CORRUPTION:
            # Simulate state corruption
            events.append(
                {
                    "type": "state_corruption",
                    "corruption_points": [0.3, 0.6, 0.9],  # At 30%, 60%, 90% completion
                    "corruption_types": ["pickle", "json", "filesystem"],
                }
            )

        elif chaos_type == ChaosType.API_RATE_LIMITS:
            # Simulate API rate limiting
            events.append(
                {
                    "type": "api_rate_limits",
                    "rate_limit": 5,  # 5 req/min
                    "downtime_windows": [(60, 180), (240, 360)],  # Downtime periods
                    "concurrent_agents": 8,
                }
            )

        elif chaos_type == ChaosType.MEMORY_PRESSURE:
            # Simulate memory pressure
            events.append(
                {
                    "type": "memory_pressure",
                    "memory_limit": "2GB",
                    "fragmentation_level": 0.7,
                    "gc_delays": True,
                }
            )

        return events

    async def _generate_chaos_event(self, chaos_type: ChaosType) -> Dict:
        """Generate realistic chaos events during execution"""
        base_event = {"timestamp": time.time()}

        if chaos_type == ChaosType.TEST_FAILURE_CASCADE:
            # Simulate test results with failures
            return {
                **base_event,
                "test_results": {
                    "passed": random.randint(0, 20),
                    "failed": random.randint(5, 47),
                    "skipped": random.randint(0, 5),
                    "duration_seconds": random.uniform(15, 120),
                    "failure_details": [
                        "Authentication token validation failed",
                        "Database connection timeout",
                        "Race condition in session cleanup",
                    ],
                },
            }

        elif chaos_type == ChaosType.RESOURCE_CONFLICTS:
            # Simulate resource availability
            return {
                **base_event,
                "resource_status": {
                    "git_lock_available": random.choice([True, False]),
                    "db_connections_available": random.randint(0, 3),
                    "memory_pressure": random.uniform(0.6, 0.95),
                },
            }

        # Add more chaos event patterns for other types
        return base_event

    def _calculate_resilience(
        self,
        context: ExecutionContext,
        chaos_events: List[Dict],
        execution_time: float,
        recovery_time: Optional[float],
    ) -> float:
        """Calculate resilience score based on chaos test performance"""
        base_score = 100.0

        # Deduct points for execution time (longer = less resilient)
        if execution_time > 60:
            base_score -= min(30, (execution_time - 60) / 10)

        # Deduct points for recovery time
        if recovery_time:
            base_score -= min(20, recovery_time / 5)

        # Bonus points for successful completion under chaos
        if context.current_state.name == "COMPLETED":
            base_score += 10

        # Analyze learning insights for adaptation
        if len(context.learning_insights) > 0:
            base_score += 5

        return max(0.0, min(100.0, base_score))

    def _result_to_dict(self, result: ChaosResult) -> Dict:
        """Convert result to dictionary for JSON serialization"""
        return {
            "test_name": result.test_name,
            "chaos_type": result.chaos_type.value,
            "success": result.success,
            "execution_time": result.execution_time,
            "recovery_time": result.recovery_time,
            "error_details": result.error_details,
            "resilience_score": result.resilience_score,
        }


async def main():
    """Main entry point for chaos engineering suite"""
    print("🚀 Initializing SPARKY Chaos Engineering Suite...")

    orchestrator = ChaosOrchestrator()
    results = await orchestrator.run_chaos_suite()

    # Save results
    results_file = Path(__file__).parent / "chaos_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📊 Results saved to: {results_file}")

    # Exit with error code if tests failed
    if results["success_rate"] < 100:
        print(
            "\n⚠️  Some chaos tests failed - review results for resilience improvements"
        )
        sys.exit(1)
    else:
        print("\n🎉 All chaos tests passed - SPARKY shows excellent resilience!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
