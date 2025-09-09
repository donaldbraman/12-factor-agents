#!/usr/bin/env python3
"""
Background Executor Performance Benchmarks

Test concurrent agent execution, resource monitoring, and throughput.
Validates the 20-30+ concurrent agent target.
"""
import asyncio
import time
import json
import statistics
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.background_executor import (
    BackgroundAgentExecutor,
    ResourceLimits,
)


class BackgroundExecutorBenchmark:
    """Comprehensive benchmarks for Background Agent Executor"""

    def __init__(self):
        self.executor = None
        self.results = {}

    async def setup(self):
        """Initialize executor for benchmarks"""
        self.executor = BackgroundAgentExecutor(max_parallel_agents=35)

    async def cleanup(self):
        """Cleanup after benchmarks"""
        if self.executor:
            await self.executor.cleanup_all()

    def print_header(self, title: str):
        """Print formatted header"""
        print("=" * 80)
        print(f"{title:^80}")
        print("=" * 80)
        print()

    def print_result(
        self, test_name: str, metric: str, value: float, target: float, unit: str
    ):
        """Print benchmark result with target comparison"""
        status = "✅ TARGET MET" if value <= target else "❌ TARGET MISSED"
        print(f"  {test_name}:")
        print(f"    {metric}: {value:.3f}{unit} (target: ≤{target}{unit})")
        print(f"    {status}")
        print()

    async def benchmark_concurrent_spawning(self):
        """Test concurrent agent spawning performance"""
        print("Benchmarking: Concurrent Agent Spawning")

        # Test different concurrency levels
        concurrency_levels = [5, 10, 20, 30]
        spawn_times = []

        for level in concurrency_levels:
            print(f"  Testing {level} concurrent agents...")

            # Measure spawn time
            start_time = time.time()
            agent_ids = []

            # Spawn agents concurrently
            spawn_tasks = []
            for i in range(level):
                task = asyncio.create_task(
                    self.executor.spawn_background_agent(
                        agent_class="BaseAgent",
                        task=f"concurrent_test_{i}",
                        workflow_data={"agent_number": i, "level": level},
                    )
                )
                spawn_tasks.append(task)

            # Wait for all spawns to complete
            agent_ids = await asyncio.gather(*spawn_tasks)
            spawn_time = time.time() - start_time
            spawn_times.append(spawn_time)

            print(f"    Spawned {level} agents in {spawn_time:.3f}s")
            print(f"    Active agents: {len(self.executor.active_agents)}")

            # Wait a bit for agents to start
            await asyncio.sleep(0.5)

            # Cleanup for next test
            await self.executor.cleanup_all()
            await asyncio.sleep(0.2)

        # Calculate metrics
        avg_spawn_time = statistics.mean(spawn_times)
        max_spawn_time = max(spawn_times)

        self.results["concurrent_spawning"] = {
            "levels_tested": concurrency_levels,
            "spawn_times": spawn_times,
            "avg_spawn_time": avg_spawn_time,
            "max_spawn_time": max_spawn_time,
        }

        print(f"  Average spawn time: {avg_spawn_time:.3f}s")
        print(f"  Maximum spawn time: {max_spawn_time:.3f}s")

        # Target: Should spawn 30 agents within 5 seconds
        target_spawn_time = 5.0
        status = (
            "✅ TARGET MET" if max_spawn_time <= target_spawn_time else "❌ TARGET MISSED"
        )
        print(
            f"  {status}: Maximum spawn time {max_spawn_time:.3f}s ≤ {target_spawn_time}s"
        )
        print()

    async def benchmark_throughput(self):
        """Test agent execution throughput"""
        print("Benchmarking: Execution Throughput")

        # Spawn 25 agents for throughput test
        agent_count = 25
        print(f"  Spawning {agent_count} agents for throughput test...")

        start_time = time.time()
        agent_ids = []

        # Spawn all agents
        for i in range(agent_count):
            agent_id = await self.executor.spawn_background_agent(
                agent_class="BaseAgent",
                task=f"throughput_test_{i}",
                workflow_data={"execution_time": 1.0},  # 1 second execution
            )
            agent_ids.append(agent_id)

        spawn_complete_time = time.time()

        # Monitor completion
        completed_count = 0
        check_interval = 0.5
        max_wait_time = 30.0
        elapsed_time = 0

        while completed_count < agent_count and elapsed_time < max_wait_time:
            await asyncio.sleep(check_interval)
            elapsed_time += check_interval

            # Count completed agents
            completed_count = 0
            for agent_id in agent_ids:
                info = self.executor.get_agent_info(agent_id)
                if info and info.status.name in ["COMPLETED", "FAILED"]:
                    completed_count += 1

            print(
                f"    Progress: {completed_count}/{agent_count} completed ({elapsed_time:.1f}s)"
            )

        total_time = time.time() - start_time
        throughput = agent_count / total_time if total_time > 0 else 0

        self.results["throughput"] = {
            "agent_count": agent_count,
            "total_time": total_time,
            "spawn_time": spawn_complete_time - start_time,
            "throughput": throughput,
            "completed_count": completed_count,
        }

        print(f"  Total execution time: {total_time:.3f}s")
        print(f"  Throughput: {throughput:.2f} agents/second")
        print(
            f"  Completion rate: {completed_count}/{agent_count} ({completed_count/agent_count*100:.1f}%)"
        )

        # Target: Should handle 25 agents with >80% completion
        completion_rate = completed_count / agent_count
        target_completion = 0.8
        status = (
            "✅ TARGET MET"
            if completion_rate >= target_completion
            else "❌ TARGET MISSED"
        )
        print(
            f"  {status}: Completion rate {completion_rate:.1f} ≥ {target_completion:.1f}"
        )
        print()

    async def benchmark_resource_monitoring(self):
        """Test resource monitoring performance"""
        print("Benchmarking: Resource Monitoring")

        # Spawn agents with resource limits
        agent_count = 15
        limits = ResourceLimits(
            max_memory_mb=128, max_cpu_percent=25.0, max_execution_time=10.0
        )

        print(f"  Spawning {agent_count} agents with resource limits...")

        start_time = time.time()
        agent_ids = []

        for i in range(agent_count):
            agent_id = await self.executor.spawn_background_agent(
                agent_class="BaseAgent",
                task=f"resource_test_{i}",
                resource_limits=limits,
                workflow_data={"resource_intensive": True},
            )
            agent_ids.append(agent_id)

        # Monitor resource usage
        monitoring_samples = []
        for _ in range(10):  # Take 10 samples over 5 seconds
            sample_start = time.time()

            # Get status for all agents
            status_count = 0
            for agent_id in agent_ids:
                status = await self.executor.get_agent_status(agent_id)
                if status:
                    status_count += 1

            sample_time = time.time() - sample_start
            monitoring_samples.append(sample_time)

            print(
                f"    Monitored {status_count}/{agent_count} agents in {sample_time:.4f}s"
            )
            await asyncio.sleep(0.5)

        total_time = time.time() - start_time
        avg_monitoring_time = statistics.mean(monitoring_samples)
        max_monitoring_time = max(monitoring_samples)

        self.results["resource_monitoring"] = {
            "agent_count": agent_count,
            "total_time": total_time,
            "monitoring_samples": monitoring_samples,
            "avg_monitoring_time": avg_monitoring_time,
            "max_monitoring_time": max_monitoring_time,
        }

        print(f"  Average monitoring time: {avg_monitoring_time:.4f}s per sample")
        print(f"  Maximum monitoring time: {max_monitoring_time:.4f}s per sample")

        # Target: Monitoring should be <100ms per sample
        target_monitoring_time = 0.1
        status = (
            "✅ TARGET MET"
            if max_monitoring_time <= target_monitoring_time
            else "❌ TARGET MISSED"
        )
        print(
            f"  {status}: Max monitoring {max_monitoring_time:.4f}s ≤ {target_monitoring_time:.4f}s"
        )
        print()

    async def benchmark_capacity_stress_test(self):
        """Test executor under capacity stress"""
        print("Benchmarking: Capacity Stress Test")

        # Set high capacity and test limits
        self.executor.max_parallel_agents = 50
        target_agents = 40

        print(f"  Attempting to spawn {target_agents} agents (max capacity: 50)...")

        start_time = time.time()
        successful_spawns = 0
        failed_spawns = 0
        agent_ids = []

        # Spawn agents rapidly
        for i in range(target_agents):
            try:
                agent_id = await self.executor.spawn_background_agent(
                    agent_class="BaseAgent",
                    task=f"stress_test_{i}",
                    workflow_data={"stress_test": True},
                )
                agent_ids.append(agent_id)
                successful_spawns += 1
            except Exception:
                failed_spawns += 1

            # Brief pause every 10 agents
            if i % 10 == 9:
                await asyncio.sleep(0.1)
                print(
                    f"    Progress: {successful_spawns} successful, {failed_spawns} failed"
                )

        spawn_time = time.time() - start_time
        active_count = len(self.executor.active_agents)

        print("  Spawn results:")
        print(f"    Successful spawns: {successful_spawns}")
        print(f"    Failed spawns: {failed_spawns}")
        print(f"    Active agents: {active_count}")
        print(f"    Total spawn time: {spawn_time:.3f}s")

        # Monitor system stability
        print("  Monitoring system stability...")
        stable_samples = 0
        for i in range(5):
            current_active = len(self.executor.active_agents)
            if current_active > 0:
                stable_samples += 1
            print(f"    Sample {i+1}: {current_active} active agents")
            await asyncio.sleep(1.0)

        self.results["capacity_stress"] = {
            "target_agents": target_agents,
            "successful_spawns": successful_spawns,
            "failed_spawns": failed_spawns,
            "active_count": active_count,
            "spawn_time": spawn_time,
            "stable_samples": stable_samples,
        }

        # Target: Should handle 30+ agents with >90% success
        success_rate = successful_spawns / target_agents
        target_success_rate = 0.9
        target_min_agents = 30

        success_status = (
            "✅ TARGET MET" if success_rate >= target_success_rate else "❌ TARGET MISSED"
        )
        capacity_status = (
            "✅ TARGET MET"
            if successful_spawns >= target_min_agents
            else "❌ TARGET MISSED"
        )

        print(
            f"  {success_status}: Success rate {success_rate:.1%} ≥ {target_success_rate:.1%}"
        )
        print(
            f"  {capacity_status}: Successful spawns {successful_spawns} ≥ {target_min_agents}"
        )
        print()

    async def benchmark_event_bus_performance(self):
        """Test event bus performance under load"""
        print("Benchmarking: Event Bus Performance")

        events_received = []

        async def event_handler(event_type: str, data: dict):
            events_received.append((time.time(), event_type, data))

        # Register handler
        self.executor.event_bus.register_handler("benchmark_event", event_handler)

        # Send many events rapidly
        event_count = 1000
        print(f"  Sending {event_count} events...")

        start_time = time.time()

        for i in range(event_count):
            await self.executor.event_bus.emit(
                "benchmark_event",
                {
                    "event_number": i,
                    "timestamp": time.time(),
                    "data": f"benchmark_data_{i}",
                },
            )

        send_time = time.time() - start_time

        # Wait for event processing
        await asyncio.sleep(1.0)

        total_time = time.time() - start_time
        events_processed = len(events_received)
        throughput = events_processed / total_time if total_time > 0 else 0

        self.results["event_bus"] = {
            "event_count": event_count,
            "events_processed": events_processed,
            "send_time": send_time,
            "total_time": total_time,
            "throughput": throughput,
        }

        print(f"  Events sent: {event_count}")
        print(f"  Events processed: {events_processed}")
        print(f"  Send time: {send_time:.3f}s")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Throughput: {throughput:.0f} events/second")

        # Target: Should process >500 events/second
        target_throughput = 500
        processing_rate = events_processed / event_count

        throughput_status = (
            "✅ TARGET MET" if throughput >= target_throughput else "❌ TARGET MISSED"
        )
        processing_status = (
            "✅ TARGET MET" if processing_rate >= 0.95 else "❌ TARGET MISSED"
        )

        print(
            f"  {throughput_status}: Throughput {throughput:.0f} ≥ {target_throughput} events/s"
        )
        print(f"  {processing_status}: Processing rate {processing_rate:.1%} ≥ 95%")
        print()

    def generate_summary(self):
        """Generate benchmark summary"""
        self.print_header("BENCHMARK SUMMARY")

        # Extract key metrics
        metrics = {}

        if "concurrent_spawning" in self.results:
            metrics["max_concurrent_agents"] = max(
                self.results["concurrent_spawning"]["levels_tested"]
            )
            metrics["max_spawn_time"] = self.results["concurrent_spawning"][
                "max_spawn_time"
            ]

        if "throughput" in self.results:
            metrics["throughput_agents"] = self.results["throughput"]["agent_count"]
            metrics["completion_rate"] = (
                self.results["throughput"]["completed_count"]
                / self.results["throughput"]["agent_count"]
            )

        if "capacity_stress" in self.results:
            metrics["max_successful_spawns"] = self.results["capacity_stress"][
                "successful_spawns"
            ]
            metrics["success_rate"] = (
                self.results["capacity_stress"]["successful_spawns"]
                / self.results["capacity_stress"]["target_agents"]
            )

        if "event_bus" in self.results:
            metrics["event_throughput"] = self.results["event_bus"]["throughput"]

        # Print summary
        print("Performance Metrics:")
        for key, value in metrics.items():
            if isinstance(value, float):
                if "rate" in key or "success" in key:
                    print(f"  {key.replace('_', ' ').title()}: {value:.1%}")
                elif "time" in key:
                    print(f"  {key.replace('_', ' ').title()}: {value:.3f}s")
                else:
                    print(f"  {key.replace('_', ' ').title()}: {value:.0f}")
            else:
                print(f"  {key.replace('_', ' ').title()}: {value}")

        print()

        # Target achievement summary
        print("Target Achievement:")

        targets_met = 0
        total_targets = 0

        # Concurrent spawning target
        if "concurrent_spawning" in self.results:
            total_targets += 1
            if self.results["concurrent_spawning"]["max_spawn_time"] <= 5.0:
                targets_met += 1
                print("  ✅ Concurrent spawning ≤5s")
            else:
                print("  ❌ Concurrent spawning >5s")

        # Capacity target
        if "capacity_stress" in self.results:
            total_targets += 1
            if self.results["capacity_stress"]["successful_spawns"] >= 30:
                targets_met += 1
                print("  ✅ Capacity ≥30 agents")
            else:
                print("  ❌ Capacity <30 agents")

        # Throughput target
        if "throughput" in self.results:
            total_targets += 1
            completion_rate = (
                self.results["throughput"]["completed_count"]
                / self.results["throughput"]["agent_count"]
            )
            if completion_rate >= 0.8:
                targets_met += 1
                print("  ✅ Completion rate ≥80%")
            else:
                print("  ❌ Completion rate <80%")

        # Event bus target
        if "event_bus" in self.results:
            total_targets += 1
            if self.results["event_bus"]["throughput"] >= 500:
                targets_met += 1
                print("  ✅ Event throughput ≥500/s")
            else:
                print("  ❌ Event throughput <500/s")

        print()
        print(
            f"Overall Success Rate: {targets_met}/{total_targets} ({targets_met/total_targets:.1%})"
        )

        if targets_met == total_targets:
            print("🎉 SUCCESS: Background Executor meets all performance targets!")
        else:
            print("⚠️  WARNING: Some performance targets not met")

        return targets_met == total_targets

    async def run_all_benchmarks(self):
        """Run all benchmarks"""
        self.print_header("BACKGROUND AGENT EXECUTOR PERFORMANCE BENCHMARKS")

        await self.setup()

        try:
            # Run each benchmark
            await self.benchmark_concurrent_spawning()
            await self.benchmark_throughput()
            await self.benchmark_resource_monitoring()
            await self.benchmark_capacity_stress_test()
            await self.benchmark_event_bus_performance()

            # Generate summary
            success = self.generate_summary()

            # Save results
            results_file = Path("benchmark_results_background_executor.json")
            with open(results_file, "w") as f:
                json.dump(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "results": self.results,
                        "success": success,
                    },
                    f,
                    indent=2,
                )

            print(f"\nResults saved to: {results_file}")

            return success

        finally:
            await self.cleanup()


async def main():
    """Main benchmark execution"""
    benchmark = BackgroundExecutorBenchmark()
    success = await benchmark.run_all_benchmarks()
    return 0 if success else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
