"""End-to-end performance validation"""
import pytest
import time
import signal
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

def timeout_handler(signum, frame):
    raise TimeoutError("Benchmark exceeded time limit")

class TestE2EPerformance:
    """Validate complete workflow performance"""
    
    @pytest.fixture(autouse=True)
    def setup_timeout(self):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        yield
        signal.alarm(0)
        
    def test_simple_task_latency(self):
        """Test simple task execution latency"""
        from core.agent_executor import AgentExecutor
        
        executor = AgentExecutor()
        
        start = time.perf_counter()
        result = executor.execute("simple_task", {"value": 42})
        latency = time.perf_counter() - start
        
        assert latency < 0.1, f"Simple task latency {latency:.3f}s exceeds 0.1s"
        print(f"✅ Simple task latency: {latency:.3f}s")
        
    def test_complex_workflow_performance(self):
        """Test complex multi-agent workflow"""
        from core.hierarchical_orchestrator import HierarchicalOrchestrator
        
        orchestrator = HierarchicalOrchestrator()
        
        # Complex workflow with multiple stages
        workflow = {
            "stages": [
                {"type": "data_collection", "agents": 5},
                {"type": "processing", "agents": 10},
                {"type": "aggregation", "agents": 3},
                {"type": "reporting", "agents": 1}
            ]
        }
        
        start = time.perf_counter()
        result = orchestrator.execute_workflow(workflow)
        total_time = time.perf_counter() - start
        
        assert total_time < 5.0, f"Complex workflow took {total_time:.1f}s, target < 5s"
        print(f"✅ Complex workflow: {total_time:.2f}s for 19 agents")
        
    def test_parallel_execution_speedup(self):
        """Verify parallel execution provides speedup"""
        from core.agent_executor import AgentExecutor
        
        executor = AgentExecutor()
        tasks = [{"id": i, "work": "process"} for i in range(10)]
        
        # Sequential execution
        start = time.perf_counter()
        for task in tasks:
            executor.execute("process_task", task)
        sequential_time = time.perf_counter() - start
        
        # Parallel execution
        start = time.perf_counter()
        executor.execute_parallel(tasks)
        parallel_time = time.perf_counter() - start
        
        speedup = sequential_time / parallel_time
        assert speedup > 1.5, f"Parallel speedup {speedup:.1f}x below 1.5x target"
        print(f"✅ Parallel speedup: {speedup:.1f}x")
