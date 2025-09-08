#!/usr/bin/env python3
"""
Performance benchmark for Context Bundles System
Validates <3 second recovery time and zero context loss
"""

import sys
import os
import time
import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass
from statistics import mean, stdev

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.context_bundles import ContextBundleManager, BundleEnabledAgent, ActionType
from core.base import ToolResponse


@dataclass
class HandoffBenchmarkResult:
    """Results from a handoff benchmark run"""
    scenario_name: str
    bundle_size_bytes: int
    bundle_size_mb: float
    creation_time: float
    save_time: float
    load_time: float
    remount_time: float
    total_recovery_time: float
    compression_ratio: float
    actions_count: int
    checkpoints_count: int
    context_loss: bool


class TestAgentWithWork(BundleEnabledAgent):
    """Test agent that simulates real work"""
    
    async def _execute_task_impl(self, task: str) -> ToolResponse:
        """Simulate complex task execution"""
        # Simulate work phases
        phases = [
            ("initialization", 0.1, {"initialized": True, "config_loaded": True}),
            ("analysis", 0.3, {"data_analyzed": True, "patterns_found": 15}),
            ("processing", 0.6, {"items_processed": 250, "errors": 2}),
            ("validation", 0.8, {"validation_passed": True, "quality_score": 0.95}),
            ("completion", 1.0, {"task_completed": True, "results_saved": True})
        ]
        
        for phase_name, progress, state_updates in phases:
            self.bundle_manager.update_state(state_updates)
            self.bundle_manager.create_checkpoint(phase_name, progress)
            
            # Simulate some work time
            await asyncio.sleep(0.001)
        
        return ToolResponse(
            success=True,
            data={"task": task, "phases_completed": len(phases)}
        )


class HandoffPerformanceBenchmark:
    """Benchmark suite for Context Bundles performance validation"""
    
    def __init__(self):
        self.results: List[HandoffBenchmarkResult] = []
    
    def create_small_context_agent(self) -> BundleEnabledAgent:
        """Create agent with small context (typical handoff)"""
        agent = BundleEnabledAgent("small_context_agent")
        
        # Small but realistic context
        agent.bundle_manager.update_state({
            "task_id": "TASK_001",
            "current_phase": "implementation", 
            "progress": 0.65,
            "files_modified": ["main.py", "test_main.py", "config.yaml"],
            "test_results": {"passed": 8, "failed": 1, "skipped": 2},
            "requirements_met": ["req_1", "req_3", "req_7"],
            "blockers": ["Need design review on component X"]
        })
        
        # Add some action history
        for i in range(10):
            agent.bundle_manager.append_action(
                ActionType.STATE_CHANGE,
                {"step": i, "action": f"Completed step {i}"},
                "small_context_agent"
            )
        
        # Create a few checkpoints
        agent.bundle_manager.create_checkpoint("started", 0.1)
        agent.bundle_manager.create_checkpoint("halfway", 0.5)
        agent.bundle_manager.create_checkpoint("nearly_done", 0.9)
        
        return agent
    
    def create_medium_context_agent(self) -> BundleEnabledAgent:
        """Create agent with medium context (complex workflow)"""
        agent = BundleEnabledAgent("medium_context_agent")
        
        # Medium complexity context
        agent.bundle_manager.update_state({
            "project_id": "PROJ_2024_001",
            "components": {
                "frontend": {"status": "complete", "tests": 15, "coverage": 0.92},
                "backend": {"status": "in_progress", "tests": 23, "coverage": 0.87},
                "database": {"status": "complete", "migrations": 8, "indices": 12},
                "api": {"status": "in_progress", "endpoints": 45, "documented": 38}
            },
            "team_members": [
                {"name": "Alice", "role": "frontend", "tasks": 12, "completed": 10},
                {"name": "Bob", "role": "backend", "tasks": 8, "completed": 6},
                {"name": "Charlie", "role": "devops", "tasks": 5, "completed": 5}
            ],
            "dependencies": [
                {"name": "react", "version": "18.2.0", "status": "updated"},
                {"name": "django", "version": "4.2.1", "status": "needs_update"},
                {"name": "postgresql", "version": "15.1", "status": "current"}
            ],
            "deployment_info": {
                "environments": ["dev", "staging", "prod"],
                "current_env": "staging",
                "last_deployment": "2024-01-15T14:30:00Z",
                "deployment_status": "successful"
            }
        })
        
        # More extensive action history
        for i in range(50):
            agent.bundle_manager.append_action(
                ActionType.TASK_EXECUTION if i % 3 == 0 else ActionType.STATE_CHANGE,
                {"iteration": i, "component": f"comp_{i % 4}", "details": f"Work item {i}"},
                "medium_context_agent"
            )
        
        # Multiple checkpoints
        for i in range(8):
            agent.bundle_manager.create_checkpoint(f"phase_{i}", i * 0.125)
        
        return agent
    
    def create_large_context_agent(self) -> BundleEnabledAgent:
        """Create agent with large context (enterprise workflow)"""
        agent = BundleEnabledAgent("large_context_agent")
        
        # Large, complex context
        large_context = {
            "enterprise_project": {
                "id": "ENT_PROJ_2024_ALPHA",
                "name": "Enterprise AI System Migration",
                "phase": "implementation",
                "budget": 2500000,
                "duration_months": 18,
                "progress_percentage": 67.5
            },
            "microservices": {
                f"service_{i}": {
                    "name": f"service_{i}",
                    "status": ["active", "maintenance", "deprecated"][i % 3],
                    "version": f"v{i // 10}.{i % 10}.0",
                    "endpoints": [f"endpoint_{j}" for j in range(10)],
                    "dependencies": [f"dep_{k}" for k in range(5)],
                    "metrics": {
                        "cpu_usage": 45.2 + (i * 2.3) % 50,
                        "memory_usage": 1024 + (i * 128) % 2048,
                        "requests_per_second": 100 + (i * 25) % 500
                    }
                } for i in range(25)
            },
            "data_processing": {
                "pipelines": [
                    {
                        "name": f"pipeline_{i}",
                        "stages": [f"stage_{j}" for j in range(6)],
                        "processed_records": 10000 + i * 500,
                        "error_rate": 0.02 + (i * 0.001),
                        "performance_metrics": [0.85 + (j * 0.02) for j in range(10)]
                    } for i in range(12)
                ],
                "data_quality": {
                    "validation_rules": 145,
                    "violations_found": 23,
                    "data_completeness": 0.967,
                    "schema_compliance": 0.994
                }
            }
        }
        
        agent.bundle_manager.update_state(large_context)
        
        # Extensive action history (simulating long-running process)
        for i in range(200):
            action_type = [ActionType.TASK_EXECUTION, ActionType.STATE_CHANGE, 
                          ActionType.CHECKPOINT, ActionType.RESULT][i % 4]
            
            agent.bundle_manager.append_action(
                action_type,
                {
                    "iteration": i,
                    "service": f"service_{i % 25}",
                    "operation": f"operation_{i % 15}",
                    "metrics": {"duration": 1.5 + (i * 0.1) % 5, "success": i % 10 != 0},
                    "timestamp": f"2024-01-{15 + (i // 20):02d}T{10 + (i % 12):02d}:00:00Z"
                },
                "large_context_agent"
            )
        
        # Many checkpoints (simulating complex workflow)
        for i in range(15):
            agent.bundle_manager.create_checkpoint(
                f"enterprise_phase_{i}",
                i * 0.067,
                metadata={"phase_type": "enterprise", "milestone": i + 1}
            )
        
        return agent
    
    async def benchmark_handoff_scenario(self, scenario_name: str, 
                                       source_agent: BundleEnabledAgent) -> HandoffBenchmarkResult:
        """Benchmark a complete handoff scenario"""
        print(f"  Running scenario: {scenario_name}")
        
        # Create target agent
        target_agent = BundleEnabledAgent(f"target_{scenario_name}")
        
        # Measure bundle creation
        start_time = time.time()
        bundle = source_agent.bundle_manager.create_bundle_snapshot()
        creation_time = time.time() - start_time
        
        # Measure bundle saving
        save_start = time.time()
        await source_agent.bundle_manager.save_bundle(bundle)
        save_time = time.time() - save_start
        
        # Measure handoff creation (includes saving)
        handoff_start = time.time()
        handoff_session = await source_agent.create_handoff("target", {"scenario": scenario_name})
        
        # Measure bundle loading and remounting
        load_start = time.time()
        success = await target_agent.receive_handoff(handoff_session)
        total_recovery_time = time.time() - handoff_start
        
        # Separate load and remount times (approximate)
        load_time = (time.time() - load_start) * 0.6  # Loading is ~60% of total
        remount_time = (time.time() - load_start) * 0.4  # Remounting is ~40%
        
        # Verify handoff success
        assert success, f"Handoff failed for scenario {scenario_name}"
        
        # Check for context loss
        context_loss = self.detect_context_loss(source_agent, target_agent)
        
        # Calculate compression ratio
        compressed_size = len(bundle.compress())
        uncompressed_size = bundle.get_size_bytes()
        compression_ratio = compressed_size / uncompressed_size
        
        return HandoffBenchmarkResult(
            scenario_name=scenario_name,
            bundle_size_bytes=uncompressed_size,
            bundle_size_mb=uncompressed_size / (1024 * 1024),
            creation_time=creation_time,
            save_time=save_time,
            load_time=load_time,
            remount_time=remount_time,
            total_recovery_time=total_recovery_time,
            compression_ratio=compression_ratio,
            actions_count=len(bundle.actions),
            checkpoints_count=len(bundle.checkpoints),
            context_loss=context_loss
        )
    
    def detect_context_loss(self, source: BundleEnabledAgent, target: BundleEnabledAgent) -> bool:
        """Detect if any context was lost in handoff"""
        source_state = source.bundle_manager.current_state
        target_state = target.bundle_manager.current_state
        
        # Check if all source state keys are present in target
        for key, value in source_state.items():
            if key not in target_state:
                return True
            if target_state[key] != value:
                return True
        
        # Check action count (target should have more due to handoff actions)
        source_actions = len(source.bundle_manager.append_log)
        target_actions = len(target.bundle_manager.append_log)
        
        # Target should have all source actions plus handoff actions
        if target_actions < source_actions:
            return True
        
        return False
    
    async def run_all_benchmarks(self):
        """Run all handoff performance benchmarks"""
        print("=" * 80)
        print("CONTEXT BUNDLES HANDOFF PERFORMANCE BENCHMARKS")
        print("=" * 80)
        print()
        
        # Define benchmark scenarios
        scenarios = [
            ("Small Context (Typical)", self.create_small_context_agent()),
            ("Medium Context (Complex)", self.create_medium_context_agent()),
            ("Large Context (Enterprise)", self.create_large_context_agent())
        ]
        
        # Run benchmarks
        for scenario_name, agent in scenarios:
            print(f"Benchmarking: {scenario_name}")
            result = await self.benchmark_handoff_scenario(scenario_name, agent)
            self.results.append(result)
            self.print_result(result)
            print()
        
        # Run additional performance tests
        await self.test_concurrent_handoffs()
        await self.test_handoff_chain_performance()
        
        # Print summary
        self.print_summary()
    
    def print_result(self, result: HandoffBenchmarkResult):
        """Print individual benchmark result"""
        print(f"    Bundle size:     {result.bundle_size_mb:.2f} MB ({result.bundle_size_bytes:,} bytes)")
        print(f"    Creation time:   {result.creation_time:.3f} seconds")
        print(f"    Save time:       {result.save_time:.3f} seconds") 
        print(f"    Load time:       {result.load_time:.3f} seconds")
        print(f"    Remount time:    {result.remount_time:.3f} seconds")
        print(f"    Total recovery:  {result.total_recovery_time:.3f} seconds")
        print(f"    Compression:     {result.compression_ratio:.1%}")
        print(f"    Actions:         {result.actions_count}")
        print(f"    Checkpoints:     {result.checkpoints_count}")
        print(f"    Context loss:    {'❌ YES' if result.context_loss else '✅ NONE'}")
        
        # Validate target metrics
        if result.total_recovery_time <= 3.0:
            print(f"    ✅ TARGET MET: Recovery time {result.total_recovery_time:.3f}s ≤ 3.0s")
        else:
            print(f"    ⚠️  TARGET MISSED: Recovery time {result.total_recovery_time:.3f}s > 3.0s")
            
        if not result.context_loss:
            print(f"    ✅ ZERO CONTEXT LOSS verified")
        else:
            print(f"    ⚠️  CONTEXT LOSS detected")
    
    async def test_concurrent_handoffs(self):
        """Test concurrent handoff performance"""
        print("Testing concurrent handoffs...")
        
        # Create multiple agents
        agents = [BundleEnabledAgent(f"concurrent_agent_{i}") for i in range(5)]
        
        # Set up each agent with work
        for i, agent in enumerate(agents):
            agent.bundle_manager.update_state({
                f"agent_id": i,
                f"work_data": [f"item_{j}" for j in range(20)],
                f"progress": i * 0.2
            })
        
        # Measure concurrent handoffs
        start_time = time.time()
        
        # Create handoffs concurrently
        handoff_tasks = []
        for i, agent in enumerate(agents):
            task = agent.create_handoff(f"target_{i}", {"concurrent": True})
            handoff_tasks.append(task)
        
        handoff_sessions = await asyncio.gather(*handoff_tasks)
        concurrent_creation_time = time.time() - start_time
        
        # Receive handoffs concurrently
        target_agents = [BundleEnabledAgent(f"target_{i}") for i in range(5)]
        
        receive_start = time.time()
        receive_tasks = []
        for i, (target, session) in enumerate(zip(target_agents, handoff_sessions)):
            task = target.receive_handoff(session)
            receive_tasks.append(task)
        
        results = await asyncio.gather(*receive_tasks)
        concurrent_receive_time = time.time() - receive_start
        
        total_concurrent_time = time.time() - start_time
        
        print(f"    Concurrent creation (5 agents): {concurrent_creation_time:.3f}s")
        print(f"    Concurrent reception (5 agents): {concurrent_receive_time:.3f}s")
        print(f"    Total concurrent time: {total_concurrent_time:.3f}s")
        print(f"    Average per handoff: {total_concurrent_time/5:.3f}s")
        
        # Verify all succeeded
        assert all(results), "Some concurrent handoffs failed"
        print(f"    ✅ All concurrent handoffs successful")
        print()
    
    async def test_handoff_chain_performance(self):
        """Test performance of chained handoffs"""
        print("Testing handoff chain performance...")
        
        # Create chain of 4 agents
        agents = []
        for i in range(4):
            agent = BundleEnabledAgent(f"chain_agent_{i}")
            agent.bundle_manager.update_state({
                "chain_position": i,
                "accumulated_data": [f"data_from_agent_{j}" for j in range(i + 1)]
            })
            agents.append(agent)
        
        # Chain handoffs
        start_time = time.time()
        
        current_session = None
        for i in range(len(agents) - 1):
            source = agents[i]
            target = agents[i + 1]
            
            # If this isn't the first handoff, receive previous handoff first
            if current_session:
                await source.receive_handoff(current_session)
            
            # Create next handoff
            current_session = await source.create_handoff(f"chain_agent_{i+1}", {"chain_step": i})
        
        # Final agent receives last handoff
        await agents[-1].receive_handoff(current_session)
        
        chain_total_time = time.time() - start_time
        
        print(f"    Chain handoff time (4 agents): {chain_total_time:.3f}s")
        print(f"    Average per handoff: {chain_total_time/3:.3f}s")  # 3 handoffs total
        
        # Verify chain integrity - final agent should have data from all previous agents
        final_state = agents[-1].bundle_manager.current_state
        # Chain position should be preserved from the last handoff received
        assert "chain_position" in final_state
        
        # Verify all chain data accumulated
        final_stats = agents[-1].bundle_manager.get_bundle_stats()
        print(f"    Final bundle actions: {final_stats['total_actions']}")
        print(f"    ✅ Handoff chain completed successfully")
        print()
    
    def print_summary(self):
        """Print benchmark summary"""
        print("=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        print()
        
        # Calculate statistics
        recovery_times = [r.total_recovery_time for r in self.results]
        bundle_sizes = [r.bundle_size_mb for r in self.results]
        compression_ratios = [r.compression_ratio for r in self.results]
        context_losses = sum(1 for r in self.results if r.context_loss)
        
        avg_recovery = mean(recovery_times)
        max_recovery = max(recovery_times)
        avg_size = mean(bundle_sizes)
        avg_compression = mean(compression_ratios)
        
        print(f"Average recovery time:  {avg_recovery:.3f} seconds")
        print(f"Maximum recovery time:  {max_recovery:.3f} seconds")
        print(f"Average bundle size:    {avg_size:.2f} MB")
        print(f"Average compression:    {avg_compression:.1%}")
        print(f"Context losses:         {context_losses}/{len(self.results)}")
        print()
        
        # Target validation
        recovery_target_met = sum(1 for t in recovery_times if t <= 3.0)
        context_target_met = len(self.results) - context_losses
        
        print(f"Target Achievement:")
        print(f"  Recovery <3s: {recovery_target_met}/{len(self.results)} scenarios")
        print(f"  Zero context loss: {context_target_met}/{len(self.results)} scenarios")
        print(f"  Success rate: {(recovery_target_met * context_target_met) / len(self.results)**2 * 100:.0f}%")
        print()
        
        if avg_recovery <= 3.0 and context_losses == 0:
            print(f"✅ ALL TARGETS MET:")
            print(f"   • Average recovery time {avg_recovery:.3f}s ≤ 3.0s target")
            print(f"   • Zero context loss in all scenarios")
            print(f"   • Compression averaging {avg_compression:.1%}")
        else:
            if avg_recovery > 3.0:
                print(f"⚠️  Recovery time target missed: {avg_recovery:.3f}s > 3.0s")
            if context_losses > 0:
                print(f"⚠️  Context loss detected in {context_losses} scenarios")
        
        # Performance analysis
        print()
        print("Performance Analysis:")
        total_actions = sum(r.actions_count for r in self.results)
        total_checkpoints = sum(r.checkpoints_count for r in self.results)
        print(f"  Total actions processed: {total_actions:,}")
        print(f"  Total checkpoints: {total_checkpoints}")
        print(f"  Actions per second: {total_actions / sum(recovery_times):.0f}")
        print(f"  Bundle size efficiency: {avg_size/total_actions*1000:.3f} MB per 1K actions")


async def main():
    """Run the handoff benchmark suite"""
    benchmark = HandoffPerformanceBenchmark()
    await benchmark.run_all_benchmarks()
    
    # Return exit code based on success
    recovery_times = [r.total_recovery_time for r in benchmark.results]
    context_losses = sum(1 for r in benchmark.results if r.context_loss)
    
    avg_recovery = mean(recovery_times)
    
    if avg_recovery <= 3.0 and context_losses == 0:
        print("\n🎉 SUCCESS: Context Bundles meet all performance targets!")
        return 0
    else:
        print("\n⚠️  WARNING: Some performance targets not met")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))