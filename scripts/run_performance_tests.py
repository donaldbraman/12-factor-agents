#!/usr/bin/env python3
"""Performance test runner with reporting"""
import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_performance_suite():
    """Run all performance tests and generate report"""
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "summary": {
            "passed": 0,
            "failed": 0,
            "total": 0
        }
    }
    
    test_files = [
        "tests/performance/test_context_efficiency.py",
        "tests/performance/test_orchestration_overhead.py",
        "tests/performance/test_memory_usage.py",
        "tests/performance/test_e2e_performance.py"
    ]
    
    for test_file in test_files:
        print(f"\n🧪 Running {test_file}...")
        result = subprocess.run(
            f"python -m pytest {test_file} -v",
            shell=True,
            capture_output=True,
            text=True
        )
        
        test_name = Path(test_file).stem
        results["tests"][test_name] = {
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr
        }
        
        if result.returncode == 0:
            results["summary"]["passed"] += 1
            print(f"✅ {test_name} passed")
        else:
            results["summary"]["failed"] += 1
            print(f"❌ {test_name} failed")
            
        results["summary"]["total"] += 1
    
    # Save report
    report_path = Path("tests/performance/performance_report.json")
    report_path.write_text(json.dumps(results, indent=2))
    
    print(f"\n📊 Performance Report:")
    print(f"  Passed: {results['summary']['passed']}/{results['summary']['total']}")
    print(f"  Report: {report_path}")
    
    return results["summary"]["failed"] == 0

if __name__ == "__main__":
    import sys
    success = run_performance_suite()
    sys.exit(0 if success else 1)
