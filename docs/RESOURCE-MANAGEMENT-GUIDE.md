# Resource Management & Optimal Agent Limits

## TL;DR - The Problem You're Solving

You're absolutely right! The default `max_agents=25` is a **starting recommendation**, not a universal constant. System capacity varies dramatically:

- **Low-end systems:** May throttle at 5-10 agents
- **Mid-range systems:** Comfortable with 15-25 agents  
- **High-end systems:** Can handle 50-100+ agents
- **Server systems:** May support hundreds of agents

**The key insight:** More agents ≠ better performance if you overwhelm the system.

## The Sweet Spot Formula

**Optimal Agent Count = MIN(CPU_cores × 3, Available_RAM_GB × 5, Thermal_Limit)**

Example calculations:
- **8-core, 16GB laptop:** MIN(24, 80, thermal_limit) = ~20-25 agents
- **4-core, 8GB laptop:** MIN(12, 40, thermal_limit) = ~10-12 agents  
- **16-core, 64GB workstation:** MIN(48, 320, thermal_limit) = ~40-50 agents

## Automatic Detection & Adaptive Scaling

### Enhanced Background Executor

```python
class AdaptiveBackgroundAgentExecutor(BackgroundAgentExecutor):
    def __init__(self, max_parallel_agents: int = None):
        # Auto-detect optimal limit if not specified
        if max_parallel_agents is None:
            max_parallel_agents = self._detect_optimal_limit()
            
        super().__init__(max_parallel_agents=max_parallel_agents)
        
        # Adaptive scaling
        self.adaptive_scaling = True
        self.performance_monitor = PerformanceMonitor()
        self.scale_down_threshold = 0.9  # Scale down if resource usage > 90%
        self.scale_up_threshold = 0.6    # Scale up if resource usage < 60%
        
    def _detect_optimal_limit(self) -> int:
        """Automatically detect optimal agent limit for this system"""
        cpu_cores = psutil.cpu_count(logical=False)  # Physical cores
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Conservative formula
        cpu_based = cpu_cores * 2  # 2 agents per physical core
        memory_based = int(memory_gb * 3)  # 3 agents per GB RAM
        thermal_limit = self._estimate_thermal_limit()
        
        optimal = min(cpu_based, memory_based, thermal_limit)
        
        # Apply safety margins
        if optimal > 50:
            optimal = int(optimal * 0.8)  # 20% safety margin for high-end
        elif optimal > 20:
            optimal = int(optimal * 0.85)  # 15% safety margin for mid-range
        else:
            optimal = int(optimal * 0.9)   # 10% safety margin for low-end
            
        return max(5, optimal)  # Minimum 5 agents
        
    def _estimate_thermal_limit(self) -> int:
        """Estimate thermal constraints based on system type"""
        # Check if this looks like a laptop (battery present)
        try:
            battery = psutil.sensors_battery()
            if battery:
                return 20  # Laptop thermal limit
        except:
            pass
            
        # Desktop/server - higher thermal headroom
        return 100
```

### Dynamic Resource Monitoring

```python
class PerformanceMonitor:
    def __init__(self):
        self.baseline_metrics = self._capture_baseline()
        self.danger_zone_entered = False
        
    async def should_scale_down(self) -> bool:
        """Check if we should reduce agent count due to resource pressure"""
        current = self._capture_metrics()
        
        # Multiple red flags = scale down
        red_flags = 0
        
        if current.cpu_percent > 90:
            red_flags += 2
        elif current.cpu_percent > 80:
            red_flags += 1
            
        if current.memory_percent > 95:
            red_flags += 3  # Memory pressure is critical
        elif current.memory_percent > 85:
            red_flags += 1
            
        if current.disk_io_wait > 10:  # High I/O wait
            red_flags += 1
            
        if current.load_average > psutil.cpu_count() * 2:
            red_flags += 1
            
        return red_flags >= 2
        
    async def should_scale_up(self) -> bool:
        """Check if we have headroom to increase agent count"""
        current = self._capture_metrics()
        
        # Conservative scaling up
        return (
            current.cpu_percent < 60 and
            current.memory_percent < 70 and
            current.load_average < psutil.cpu_count() * 0.8
        )
```

## Testing Your System's Limits

### Run the Optimizer

```bash
# This tests your specific system to find optimal limits
uv run scripts/test_optimal_agent_limits.py
```

**This script will:**
1. Start with 5 agents, gradually increase
2. Monitor CPU, memory, disk I/O, response time
3. Detect when system becomes stressed
4. Find your optimal, conservative, and maximum limits
5. Generate custom recommendations

### Expected Output

```
🔍 OPTIMAL AGENT LIMIT TESTING
==================================================
System: 8 cores, 16.0GB RAM

📈 Results for 10 agents:
  Successful spawns: 10/10
  Peak CPU: 45.2%
  Peak Memory: 62.1%
  ✅ OPTIMAL: 10 agents ran smoothly with good resource utilization

📈 Results for 30 agents:
  Successful spawns: 28/30
  Peak CPU: 89.4%
  Peak Memory: 91.2%
  ⚠️ RISKY: 30 agents pushed resources to critical levels

🎯 FINAL RECOMMENDATIONS
==================================================
📊 CONSERVATIVE LIMIT: 15 agents (Safe for production)
🚀 OPTIMAL LIMIT: 20 agents (Best performance without major stress)
⚠️ MAXIMUM LIMIT: 25 agents (Never exceed this)
```

## Pin-Citer Integration Example

### Before (Fixed Limit)

```python
# pin-citer's workflow_orchestrator.py - BEFORE
self.background_executor = BackgroundAgentExecutor(max_parallel_agents=25)  # Fixed!
```

**Problem:** May overwhelm weak systems or underutilize powerful systems.

### After (Adaptive)

```python
# pin-citer's workflow_orchestrator.py - AFTER
class WorkflowOrchestrator:
    def __init__(self, enable_background_execution: bool = True):
        # Auto-detect optimal limit for this system
        if enable_background_execution:
            try:
                from core.background_executor import BackgroundAgentExecutor
                
                # Run quick system assessment
                optimal_limit = self._detect_system_capacity()
                self.background_executor = BackgroundAgentExecutor(
                    max_parallel_agents=optimal_limit
                )
                
                logger.info(f"🚀 BackgroundExecutor initialized with {optimal_limit} agents (auto-detected)")
                
            except ImportError:
                logger.warning("BackgroundExecutor not available")
                self.enable_background_execution = False
                
    def _detect_system_capacity(self) -> int:
        """Quick system capacity detection"""
        cpu_cores = psutil.cpu_count(logical=False)
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Conservative formula for pin-citer workloads
        capacity = min(cpu_cores * 2, int(memory_gb * 2))
        
        # Pin-citer specific limits based on workload type
        if capacity > 30:
            return 25  # Pin-citer rarely needs >25 agents
        elif capacity > 15:
            return capacity - 5  # Conservative margin
        else:
            return max(5, capacity)  # Minimum viable
```

## Warning Signs of Overload

### System Stress Indicators

```python
# Monitor these in production
def check_system_health():
    warnings = []
    
    cpu = psutil.cpu_percent(interval=1)
    if cpu > 90:
        warnings.append(f"⚠️ High CPU: {cpu:.1f}%")
        
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        warnings.append(f"⚠️ High Memory: {memory.percent:.1f}%")
        
    # Check if system is responsive
    start = time.time()
    time.sleep(0.01)  # Tiny delay
    response_time = time.time() - start
    
    if response_time > 0.1:  # Should be ~0.01s
        warnings.append(f"⚠️ System lag: {response_time:.3f}s")
        
    return warnings
```

### Production Monitoring

```python
# Add to your agent orchestrator
class ProductionWorkflowOrchestrator(WorkflowOrchestrator):
    async def process_document_with_monitoring(self, doc_url, **kwargs):
        # Pre-flight check
        health_warnings = self.check_system_health()
        if health_warnings:
            logger.warning(f"System stress detected: {health_warnings}")
            # Reduce agent count temporarily
            original_limit = self.background_executor.max_parallel_agents
            self.background_executor.max_parallel_agents = max(5, original_limit // 2)
            
        try:
            result = await self.process_document(doc_url, **kwargs)
        finally:
            # Restore original limit
            if health_warnings:
                self.background_executor.max_parallel_agents = original_limit
                
        return result
```

## Recommended Limits by System Type

### Development Laptops
```python
# MacBook Air, ThinkPad, etc.
conservative_limit = 8
optimal_limit = 12  
maximum_limit = 15
```

### Gaming/Workstation Laptops  
```python
# Gaming laptops, MacBook Pro, etc.
conservative_limit = 15
optimal_limit = 20
maximum_limit = 30
```

### Desktop Workstations
```python
# High-end desktops, Mac Studio, etc.
conservative_limit = 25
optimal_limit = 40
maximum_limit = 60
```

### Server Systems
```python
# Dedicated servers, cloud instances
conservative_limit = 50
optimal_limit = 100
maximum_limit = 200
```

## Configuration Examples

### Environment-Based Configuration

```python
# .env or config file
SYSTEM_TYPE=laptop  # laptop, desktop, server
AGENT_LIMIT_MODE=auto  # auto, conservative, optimal, maximum

# In code
def get_agent_limit():
    mode = os.getenv('AGENT_LIMIT_MODE', 'auto')
    system_type = os.getenv('SYSTEM_TYPE', 'auto')
    
    if mode == 'auto':
        return auto_detect_optimal_limit()
    elif mode == 'conservative':
        return get_conservative_limit(system_type)
    elif mode == 'optimal':
        return get_optimal_limit(system_type)
    else:
        return get_maximum_limit(system_type)
```

### User-Configurable Limits

```python
# Allow users to override
class UserConfigurableExecutor(BackgroundAgentExecutor):
    def __init__(self, user_preference: str = "auto"):
        if user_preference == "performance":
            limit = self._detect_optimal_limit()
        elif user_preference == "conservative": 
            limit = self._detect_optimal_limit() * 0.7
        elif user_preference == "maximum":
            limit = self._detect_maximum_safe_limit()
        else:  # auto
            limit = self._detect_optimal_limit()
            
        super().__init__(max_parallel_agents=int(limit))
```

## Next Steps

1. **Run the test:** `uv run scripts/test_optimal_agent_limits.py`
2. **Update your config:** Use detected limits in pin-citer/cite-assist
3. **Add monitoring:** Implement system health checks
4. **Start conservative:** Begin with lower limits, scale up gradually
5. **Monitor production:** Watch for performance degradation signs

The goal is **sustainable performance** - better to run 15 agents smoothly than 30 agents that throttle your entire machine!