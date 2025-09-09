#!/usr/bin/env uv run python
"""
Quick system analysis to determine optimal concurrent agent limits
without running complex executor tests.
"""
import psutil
import platform
from pathlib import Path


def analyze_system():
    """Analyze system capabilities and provide agent limit recommendations"""

    print("🔍 QUICK SYSTEM ANALYSIS FOR OPTIMAL AGENT LIMITS")
    print("=" * 55)

    # Basic system info
    system = platform.system()
    machine = platform.machine()

    # CPU information
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_count_physical = psutil.cpu_count(logical=False)

    # Memory information
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024**3)
    memory_available_gb = memory.available / (1024**3)

    # Disk information
    disk = psutil.disk_usage("/")
    disk_free_gb = disk.free / (1024**3)

    # Current system load
    current_cpu = psutil.cpu_percent(interval=1)
    current_memory = memory.percent

    # Detect system type
    system_type = detect_system_type()

    print("🖥️  SYSTEM SPECIFICATIONS")
    print(f"   Platform: {system} {machine}")
    print(f"   CPU Cores: {cpu_count_physical} physical, {cpu_count_logical} logical")
    print(f"   Total RAM: {memory_gb:.1f} GB")
    print(f"   Available RAM: {memory_available_gb:.1f} GB")
    print(f"   Free Disk: {disk_free_gb:.1f} GB")
    print(f"   System Type: {system_type}")
    print()

    print("📊 CURRENT SYSTEM LOAD")
    print(f"   CPU Usage: {current_cpu:.1f}%")
    print(f"   Memory Usage: {current_memory:.1f}%")
    print()

    # Calculate optimal limits
    conservative_limit = calculate_conservative_limit(
        cpu_count_physical, memory_gb, system_type
    )
    optimal_limit = calculate_optimal_limit(cpu_count_physical, memory_gb, system_type)
    maximum_limit = calculate_maximum_limit(cpu_count_physical, memory_gb, system_type)

    # Performance estimates
    single_agent_memory_mb = estimate_agent_memory_usage()
    parallel_memory_usage_gb = (optimal_limit * single_agent_memory_mb) / 1024

    print("🎯 AGENT LIMIT RECOMMENDATIONS")
    print(f"   📊 CONSERVATIVE: {conservative_limit} agents")
    print("      └─ Safe for production, low resource usage")
    print(f"   🚀 OPTIMAL: {optimal_limit} agents")
    print("      └─ Best performance without system stress")
    print(f"   ⚠️  MAXIMUM: {maximum_limit} agents")
    print("      └─ Absolute limit before potential throttling")
    print()

    print("📈 PERFORMANCE ESTIMATES")
    print(f"   Single Agent Memory: ~{single_agent_memory_mb}MB")
    print(f"   {optimal_limit} Agents Memory: ~{parallel_memory_usage_gb:.1f}GB")
    print(
        f"   Memory Utilization: {(parallel_memory_usage_gb / memory_gb * 100):.1f}% of total RAM"
    )
    print()

    # Warnings and recommendations
    warnings = generate_warnings(
        current_cpu, current_memory, memory_available_gb, optimal_limit, system_type
    )

    if warnings:
        print("⚠️  SYSTEM WARNINGS")
        for warning in warnings:
            print(f"   {warning}")
        print()

    # Usage recommendations
    print("💡 USAGE RECOMMENDATIONS")
    print(f"   • Development/Testing: Use {conservative_limit} agents")
    print(f"   • Production Workloads: Use {optimal_limit} agents")
    print(
        f"   • High-Performance Bursts: Up to {maximum_limit} agents (monitor closely)"
    )
    print(f"   • Never exceed: {maximum_limit} agents")
    print()

    # Configuration examples
    print("⚙️  CONFIGURATION EXAMPLES")
    print()
    print("   Pin-Citer WorkflowOrchestrator:")
    print("   ```python")
    print("   self.background_executor = BackgroundAgentExecutor(")
    print(f"       max_parallel_agents={optimal_limit}  # Optimal for your system")
    print("   )")
    print("   ```")
    print()
    print("   Cite-Assist Configuration:")
    print("   ```python")
    print("   # .env file")
    print(f"   MAX_CONCURRENT_AGENTS={optimal_limit}")
    print(f"   SYSTEM_TYPE={system_type}")
    print("   ```")

    return {
        "system_info": {
            "platform": f"{system} {machine}",
            "cpu_cores_physical": cpu_count_physical,
            "cpu_cores_logical": cpu_count_logical,
            "memory_gb": memory_gb,
            "available_memory_gb": memory_available_gb,
            "system_type": system_type,
        },
        "current_load": {"cpu_percent": current_cpu, "memory_percent": current_memory},
        "recommendations": {
            "conservative": conservative_limit,
            "optimal": optimal_limit,
            "maximum": maximum_limit,
        },
    }


def detect_system_type():
    """Detect system type based on hardware characteristics"""

    # Check if running on macOS
    if platform.system() == "Darwin":
        machine = platform.machine()
        if "arm" in machine.lower():
            return "apple_silicon_mac"  # M1/M2/M3 Macs
        else:
            return "intel_mac"

    # Check for battery (likely laptop)
    try:
        battery = psutil.sensors_battery()
        if battery:
            return "laptop"
    except:
        pass

    # Check core count to distinguish desktop vs server
    cores = psutil.cpu_count(logical=False)
    memory_gb = psutil.virtual_memory().total / (1024**3)

    if cores >= 16 and memory_gb >= 32:
        return "workstation_or_server"
    elif cores >= 8 and memory_gb >= 16:
        return "desktop"
    else:
        return "laptop"


def calculate_conservative_limit(cpu_cores, memory_gb, system_type):
    """Calculate conservative agent limit"""

    # Base calculation: 1.5 agents per physical core
    cpu_based = int(cpu_cores * 1.5)

    # Memory based: 2 agents per GB (conservative)
    memory_based = int(memory_gb * 2)

    # System type adjustments
    if system_type in ["apple_silicon_mac"]:
        thermal_limit = 20  # Apple Silicon efficient but thermal constrained
    elif system_type == "laptop":
        thermal_limit = 12  # Laptop thermal constraints
    elif system_type == "desktop":
        thermal_limit = 25  # Desktop better cooling
    else:  # workstation_or_server
        thermal_limit = 40  # Server-grade cooling

    conservative = min(cpu_based, memory_based, thermal_limit)

    # Apply safety factor
    conservative = int(conservative * 0.7)  # 30% safety margin

    return max(5, conservative)  # Minimum 5 agents


def calculate_optimal_limit(cpu_cores, memory_gb, system_type):
    """Calculate optimal agent limit for best performance"""

    # Base calculation: 2.5 agents per physical core
    cpu_based = int(cpu_cores * 2.5)

    # Memory based: 3 agents per GB
    memory_based = int(memory_gb * 3)

    # System type adjustments
    if system_type in ["apple_silicon_mac"]:
        thermal_limit = 30  # Apple Silicon very efficient
    elif system_type == "laptop":
        thermal_limit = 18  # Laptop thermal constraints
    elif system_type == "desktop":
        thermal_limit = 35  # Desktop good cooling
    else:  # workstation_or_server
        thermal_limit = 60  # Server-grade systems

    optimal = min(cpu_based, memory_based, thermal_limit)

    # Apply moderate safety factor
    optimal = int(optimal * 0.85)  # 15% safety margin

    return max(8, optimal)  # Minimum 8 agents for optimal


def calculate_maximum_limit(cpu_cores, memory_gb, system_type):
    """Calculate maximum safe agent limit"""

    # Aggressive calculation: 4 agents per physical core
    cpu_based = int(cpu_cores * 4)

    # Memory based: 4 agents per GB
    memory_based = int(memory_gb * 4)

    # System type limits
    if system_type in ["apple_silicon_mac"]:
        thermal_limit = 40  # Push Apple Silicon further
    elif system_type == "laptop":
        thermal_limit = 25  # Laptop maximum before throttling
    elif system_type == "desktop":
        thermal_limit = 50  # Desktop maximum
    else:  # workstation_or_server
        thermal_limit = 100  # Server systems can handle more

    maximum = min(cpu_based, memory_based, thermal_limit)

    return max(12, maximum)  # Minimum 12 agents for maximum


def estimate_agent_memory_usage():
    """Estimate memory usage per agent"""
    # Conservative estimate based on Python + framework overhead
    return 128  # MB per agent


def generate_warnings(
    current_cpu, current_memory, available_memory_gb, optimal_limit, system_type
):
    """Generate system warnings"""
    warnings = []

    if current_cpu > 80:
        warnings.append(
            f"High current CPU usage ({current_cpu:.1f}%) - consider fewer agents"
        )

    if current_memory > 85:
        warnings.append(
            f"High current memory usage ({current_memory:.1f}%) - reduce agent count"
        )

    if available_memory_gb < 2:
        warnings.append(
            f"Low available memory ({available_memory_gb:.1f}GB) - use conservative limits"
        )

    if system_type == "laptop" and optimal_limit > 20:
        warnings.append(
            "Laptop systems may throttle with high agent counts - monitor temperature"
        )

    return warnings


if __name__ == "__main__":
    try:
        results = analyze_system()

        # Save results
        import json

        results_file = Path("system_analysis_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"📁 Results saved to: {results_file}")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        exit(1)
