"""Memory usage benchmarks"""
import pytest
import psutil
import signal
import os
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

def timeout_handler(signum, frame):
    raise TimeoutError("Benchmark exceeded time limit")

class TestMemoryUsage:
    """Validate memory efficiency targets"""
    
    @pytest.fixture(autouse=True)
    def setup_timeout(self):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        yield
        signal.alarm(0)
        
    def test_agent_memory_footprint(self):
        """Test single agent memory usage < 500MB"""
        from agents.base import BaseAgent
        
        process = psutil.Process(os.getpid())
        baseline = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create agent
        agent = BaseAgent("test_agent")
        agent.initialize()
        
        # Measure after creation
        current = process.memory_info().rss / 1024 / 1024
        agent_memory = current - baseline
        
        assert agent_memory < 500, f"Agent uses {agent_memory:.0f}MB, target < 500MB"
        print(f"✅ Agent memory footprint: {agent_memory:.0f}MB")
        
    def test_multi_agent_memory_scaling(self):
        """Test memory scaling with multiple agents"""
        from agents.base import BaseAgent
        
        process = psutil.Process(os.getpid())
        baseline = process.memory_info().rss / 1024 / 1024
        
        agents = []
        for i in range(10):
            agent = BaseAgent(f"agent_{i}")
            agent.initialize()
            agents.append(agent)
            
        current = process.memory_info().rss / 1024 / 1024
        total_memory = current - baseline
        per_agent = total_memory / 10
        
        assert per_agent < 100, f"Per-agent memory {per_agent:.0f}MB exceeds 100MB"
        print(f"✅ Memory scaling: {per_agent:.0f}MB per agent")
        
    def test_memory_cleanup(self):
        """Test memory is properly released"""
        from agents.base import BaseAgent
        import gc
        
        process = psutil.Process(os.getpid())
        baseline = process.memory_info().rss / 1024 / 1024
        
        # Create and destroy agents
        for _ in range(5):
            agents = [BaseAgent(f"agent_{i}") for i in range(20)]
            del agents
            gc.collect()
            
        final = process.memory_info().rss / 1024 / 1024
        leak = final - baseline
        
        assert leak < 50, f"Memory leak {leak:.0f}MB detected"
        print(f"✅ Memory cleanup: {leak:.0f}MB retained after cleanup")
