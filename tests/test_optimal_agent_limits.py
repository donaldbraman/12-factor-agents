#!/usr/bin/env uv run python
"""
Test script to determine optimal concurrent agent limits without throttling the machine.

This script systematically tests different agent limits to find the sweet spot where
performance is maximized without overwhelming system resources.
"""
import asyncio
import psutil
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.background_executor import BackgroundAgentExecutor, ResourceLimits

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SystemSnapshot:
    """System resource snapshot"""

    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_io_read: int
    disk_io_write: int
    network_sent: int
    network_recv: int
    load_average: Tuple[float, float, float]
    active_processes: int


@dataclass
class TestResult:
    """Results from testing a specific agent limit"""

    max_agents: int
    total_agents_spawned: int
    successful_spawns: int
    failed_spawns: int
    spawn_time_seconds: float
    peak_cpu_percent: float
    peak_memory_percent: float
    system_became_unresponsive: bool
    average_response_time: float
    recommendation: str


class OptimalLimitTester:
    """Test optimal concurrent agent limits"""

    def __init__(self):
        self.baseline_snapshot = None
        self.test_results: List[TestResult] = []

    def capture_system_snapshot(self) -> SystemSnapshot:
        """Capture current system state"""
        # CPU and memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        # Disk I/O
        disk_io = psutil.disk_io_counters()

        # Network I/O
        network_io = psutil.net_io_counters()

        # Load average (Unix-like systems)
        try:
            load_avg = psutil.getloadavg()
        except (AttributeError, OSError):
            load_avg = (0.0, 0.0, 0.0)  # Windows fallback

        return SystemSnapshot(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_available_gb=memory.available / (1024**3),
            disk_io_read=disk_io.read_bytes if disk_io else 0,
            disk_io_write=disk_io.write_bytes if disk_io else 0,
            network_sent=network_io.bytes_sent if network_io else 0,
            network_recv=network_io.bytes_recv if network_io else 0,
            load_average=load_avg,
            active_processes=len(psutil.pids()),
        )

    def analyze_system_health(self, snapshot: SystemSnapshot) -> Dict[str, Any]:
        """Analyze if system is healthy or under stress"""
        health_score = 100.0
        warnings = []

        # CPU stress indicators
        if snapshot.cpu_percent > 90:
            health_score -= 30
            warnings.append(f"High CPU usage: {snapshot.cpu_percent:.1f}%")
        elif snapshot.cpu_percent > 70:
            health_score -= 15
            warnings.append(f"Elevated CPU usage: {snapshot.cpu_percent:.1f}%")

        # Memory stress indicators
        if snapshot.memory_percent > 90:
            health_score -= 30
            warnings.append(f"High memory usage: {snapshot.memory_percent:.1f}%")
        elif snapshot.memory_percent > 80:
            health_score -= 15
            warnings.append(f"Elevated memory usage: {snapshot.memory_percent:.1f}%")

        # Available memory warning
        if snapshot.memory_available_gb < 1.0:
            health_score -= 25
            warnings.append(
                f"Low available memory: {snapshot.memory_available_gb:.2f}GB"
            )

        # Load average warnings (if available)
        if snapshot.load_average[0] > psutil.cpu_count():
            health_score -= 20
            warnings.append(f"High system load: {snapshot.load_average[0]:.2f}")

        return {
            "health_score": max(0, health_score),
            "status": (
                "healthy"
                if health_score > 70
                else "stressed"
                if health_score > 40
                else "critical"
            ),
            "warnings": warnings,
        }

    async def test_agent_limit(
        self, max_agents: int, test_duration: int = 30
    ) -> TestResult:
        """Test a specific agent limit"""
        logger.info(f"Testing {max_agents} concurrent agents...")

        # Create executor with specified limit
        executor = BackgroundAgentExecutor(max_parallel_agents=max_agents)

        # Track metrics
        start_time = time.time()
        successful_spawns = 0
        failed_spawns = 0
        peak_cpu = 0.0
        peak_memory = 0.0
        response_times = []
        system_unresponsive = False

        try:
            # Phase 1: Spawn agents up to the limit
            spawn_start = time.time()

            for i in range(max_agents):
                try:
                    # Measure spawn response time
                    spawn_time_start = time.time()

                    agent_id = await executor.spawn_background_agent(
                        agent_class="TestLoadAgent",
                        task=f"load_test_{i}",
                        workflow_data={
                            "duration": 10,  # 10 second simulated work
                            "cpu_intensity": "low",
                            "memory_usage": "modest",
                        },
                        resource_limits=ResourceLimits(
                            max_memory_mb=256,
                            max_cpu_percent=10.0,  # Low per-agent CPU limit
                            max_execution_time_minutes=2,
                        ),
                    )

                    spawn_time = time.time() - spawn_time_start
                    response_times.append(spawn_time)

                    successful_spawns += 1

                    # Quick responsiveness test
                    if (
                        spawn_time > 5.0
                    ):  # If spawning takes >5 seconds, system may be stressed
                        logger.warning(
                            f"Slow spawn time: {spawn_time:.2f}s for agent {i}"
                        )

                except Exception as e:
                    failed_spawns += 1
                    logger.warning(f"Failed to spawn agent {i}: {e}")

                # Monitor system health during spawning
                if i % 5 == 0:  # Check every 5 agents
                    snapshot = self.capture_system_snapshot()
                    health = self.analyze_system_health(snapshot)

                    peak_cpu = max(peak_cpu, snapshot.cpu_percent)
                    peak_memory = max(peak_memory, snapshot.memory_percent)

                    if health["status"] == "critical":
                        logger.error(
                            f"System critical during spawn {i}: {health['warnings']}"
                        )
                        system_unresponsive = True
                        break

                    # Brief pause to prevent overwhelming system
                    await asyncio.sleep(0.1)

            spawn_time = time.time() - spawn_start

            # Phase 2: Monitor system during agent execution
            if not system_unresponsive and successful_spawns > 0:
                logger.info(
                    f"Monitoring system with {successful_spawns} active agents..."
                )

                monitor_start = time.time()
                while time.time() - monitor_start < test_duration:
                    snapshot = self.capture_system_snapshot()
                    health = self.analyze_system_health(snapshot)

                    peak_cpu = max(peak_cpu, snapshot.cpu_percent)
                    peak_memory = max(peak_memory, snapshot.memory_percent)

                    # Check if system becomes unresponsive
                    response_test_start = time.time()
                    # Simple responsiveness test
                    await asyncio.sleep(0.01)
                    response_time = time.time() - response_test_start

                    if (
                        response_time > 1.0
                    ):  # If basic operations take >1s, system is struggling
                        logger.warning(
                            f"System unresponsive: basic operation took {response_time:.3f}s"
                        )
                        system_unresponsive = True
                        break

                    if health["status"] == "critical":
                        logger.error(
                            f"System critical during execution: {health['warnings']}"
                        )
                        system_unresponsive = True
                        break

                    await asyncio.sleep(2)  # Monitor every 2 seconds

        finally:
            # Cleanup
            await executor.cleanup_all()

        # Calculate metrics
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0.0
        )

        # Generate recommendation
        recommendation = self._generate_recommendation(
            max_agents,
            successful_spawns,
            failed_spawns,
            peak_cpu,
            peak_memory,
            system_unresponsive,
            avg_response_time,
        )

        result = TestResult(
            max_agents=max_agents,
            total_agents_spawned=successful_spawns + failed_spawns,
            successful_spawns=successful_spawns,
            failed_spawns=failed_spawns,
            spawn_time_seconds=spawn_time,
            peak_cpu_percent=peak_cpu,
            peak_memory_percent=peak_memory,
            system_became_unresponsive=system_unresponsive,
            average_response_time=avg_response_time,
            recommendation=recommendation,
        )

        self.test_results.append(result)
        return result

    def _generate_recommendation(
        self,
        max_agents: int,
        successful: int,
        failed: int,
        peak_cpu: float,
        peak_memory: float,
        unresponsive: bool,
        avg_response: float,
    ) -> str:
        """Generate recommendation based on test results"""

        if unresponsive:
            return f"❌ AVOID: {max_agents} agents made system unresponsive"

        if failed > successful * 0.2:  # >20% failure rate
            return f"❌ AVOID: {max_agents} agents had {failed}/{max_agents} failures ({failed/max_agents:.1%})"

        if peak_cpu > 95 or peak_memory > 95:
            return f"⚠️ RISKY: {max_agents} agents pushed resources to critical levels (CPU: {peak_cpu:.1f}%, Mem: {peak_memory:.1f}%)"

        if avg_response > 2.0:
            return f"⚠️ SLOW: {max_agents} agents caused slow response times ({avg_response:.2f}s avg)"

        if peak_cpu > 80 or peak_memory > 80:
            return f"🟡 CAUTION: {max_agents} agents used significant resources (CPU: {peak_cpu:.1f}%, Mem: {peak_memory:.1f}%)"

        if successful == max_agents and peak_cpu < 70 and peak_memory < 70:
            return f"✅ OPTIMAL: {max_agents} agents ran smoothly with good resource utilization"

        return f"✅ GOOD: {max_agents} agents completed successfully"

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test across multiple agent limits"""

        print("🔍 OPTIMAL AGENT LIMIT TESTING")
        print("=" * 50)

        # Capture baseline
        print("📊 Capturing baseline system state...")
        self.baseline_snapshot = self.capture_system_snapshot()
        baseline_health = self.analyze_system_health(self.baseline_snapshot)

        print(
            f"Baseline System Health: {baseline_health['status']} ({baseline_health['health_score']:.1f}/100)"
        )
        if baseline_health["warnings"]:
            print(f"Baseline Warnings: {', '.join(baseline_health['warnings'])}")

        # Test different limits
        test_limits = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100]

        print(f"\n🧪 Testing limits: {test_limits}")
        print("=" * 50)

        for limit in test_limits:
            try:
                result = await self.test_agent_limit(limit, test_duration=20)

                print(f"\n📈 Results for {limit} agents:")
                print(
                    f"  Successful spawns: {result.successful_spawns}/{result.max_agents}"
                )
                print(f"  Peak CPU: {result.peak_cpu_percent:.1f}%")
                print(f"  Peak Memory: {result.peak_memory_percent:.1f}%")
                print(f"  Avg response time: {result.average_response_time:.3f}s")
                print(f"  System unresponsive: {result.system_became_unresponsive}")
                print(f"  {result.recommendation}")

                # If system becomes unresponsive, stop testing higher limits
                if (
                    result.system_became_unresponsive
                    or result.failed_spawns > result.successful_spawns
                ):
                    print(f"\n⚠️ Stopping tests at {limit} agents due to system stress")
                    break

                # Brief recovery time between tests
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Test failed for {limit} agents: {e}")
                break

        # Generate final recommendations
        return self._generate_final_recommendations()

    def _generate_final_recommendations(self) -> Dict[str, Any]:
        """Generate final recommendations based on all test results"""

        if not self.test_results:
            return {"error": "No test results available"}

        # Find optimal ranges
        optimal_results = [
            r for r in self.test_results if "OPTIMAL" in r.recommendation
        ]
        good_results = [
            r
            for r in self.test_results
            if "GOOD" in r.recommendation or "OPTIMAL" in r.recommendation
        ]
        safe_results = [
            r
            for r in self.test_results
            if not r.system_became_unresponsive and r.failed_spawns == 0
        ]

        # System specifications
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)

        recommendations = {
            "system_info": {
                "cpu_cores": cpu_count,
                "total_memory_gb": memory_gb,
                "baseline_cpu": self.baseline_snapshot.cpu_percent,
                "baseline_memory": self.baseline_snapshot.memory_percent,
            },
            "test_results": [
                {
                    "max_agents": r.max_agents,
                    "successful_spawns": r.successful_spawns,
                    "peak_cpu": r.peak_cpu_percent,
                    "peak_memory": r.peak_memory_percent,
                    "recommendation": r.recommendation,
                }
                for r in self.test_results
            ],
        }

        # Conservative recommendation (safe for production)
        if safe_results:
            max_safe = max(r.max_agents for r in safe_results)
            recommendations["conservative_limit"] = min(max_safe, cpu_count * 2)
            recommendations[
                "conservative_reasoning"
            ] = "Safe limit with no failures or system stress"
        else:
            recommendations["conservative_limit"] = 5
            recommendations[
                "conservative_reasoning"
            ] = "Very conservative due to system constraints"

        # Optimal recommendation (best performance without major issues)
        if good_results:
            max_good = max(r.max_agents for r in good_results)
            recommendations["optimal_limit"] = max_good
            recommendations[
                "optimal_reasoning"
            ] = "Best performance without major resource stress"
        else:
            recommendations["optimal_limit"] = recommendations["conservative_limit"]
            recommendations[
                "optimal_reasoning"
            ] = "Same as conservative due to system constraints"

        # Maximum recommendation (absolute limit before system becomes unresponsive)
        working_results = [
            r for r in self.test_results if not r.system_became_unresponsive
        ]
        if working_results:
            max_working = max(r.max_agents for r in working_results)
            recommendations["maximum_limit"] = max_working
            recommendations[
                "maximum_reasoning"
            ] = "Highest tested limit before system stress"
        else:
            recommendations["maximum_limit"] = recommendations["optimal_limit"]
            recommendations[
                "maximum_reasoning"
            ] = "Same as optimal due to early system stress"

        return recommendations


async def main():
    """Run optimal limit testing"""

    tester = OptimalLimitTester()

    print("⚡ BACKGROUND AGENT EXECUTOR - OPTIMAL LIMIT TESTING")
    print("=" * 60)
    print("This test will systematically find the optimal concurrent agent limit")
    print("for your system without throttling performance.")
    print()

    # Run comprehensive test
    results = await tester.run_comprehensive_test()

    # Display final recommendations
    print("\n🎯 FINAL RECOMMENDATIONS")
    print("=" * 50)

    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return 1

    system = results["system_info"]
    print(f"System: {system['cpu_cores']} cores, {system['total_memory_gb']:.1f}GB RAM")
    print()

    print(f"📊 CONSERVATIVE LIMIT: {results['conservative_limit']} agents")
    print(f"   {results['conservative_reasoning']}")
    print()

    print(f"🚀 OPTIMAL LIMIT: {results['optimal_limit']} agents")
    print(f"   {results['optimal_reasoning']}")
    print()

    print(f"⚠️ MAXIMUM LIMIT: {results['maximum_limit']} agents")
    print(f"   {results['maximum_reasoning']}")
    print()

    # Usage recommendations
    print("💡 USAGE RECOMMENDATIONS:")
    print(f"   • Development/Testing: Use {results['conservative_limit']} agents")
    print(f"   • Production Workloads: Use {results['optimal_limit']} agents")
    print(f"   • Never exceed: {results['maximum_limit']} agents")
    print()

    # Save results
    results_file = Path("optimal_agent_limits_test_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"📁 Detailed results saved to: {results_file}")

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
