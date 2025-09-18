#!/usr/bin/env python3
"""
Quality Flywheel Startup Script

Starts all monitoring systems for the complete quality flywheel:
1. Sister repo watcher (processes incoming reports)
2. Sparky PR monitor (urgent alerts for self-improvement PRs)
"""

import subprocess
import time
from pathlib import Path


def start_monitors():
    """Start all quality flywheel monitors"""
    print("🚀 Starting Quality Flywheel Monitoring Systems")
    print("=" * 60)

    base_dir = Path(__file__).parent.parent

    # Start sister repo watcher
    print("👀 Starting sister repo watcher...")
    sister_cmd = [
        "uv",
        "run",
        "python",
        "scripts/sister_repo_watcher.py",
        "--watch",
        "10",
    ]
    sister_process = subprocess.Popen(sister_cmd, cwd=base_dir)
    print(f"✅ Sister repo watcher started (PID: {sister_process.pid})")

    # Start Sparky PR monitor
    print("🤖 Starting Sparky PR monitor...")
    sparky_cmd = [
        "uv",
        "run",
        "python",
        "scripts/sparky_pr_monitor.py",
        "--watch",
        "30",
    ]
    sparky_process = subprocess.Popen(sparky_cmd, cwd=base_dir)
    print(f"✅ Sparky PR monitor started (PID: {sparky_process.pid})")

    print("=" * 60)
    print("🎯 Quality Flywheel ACTIVE!")
    print("📊 Sister repos can drop reports → Auto GitHub issues")
    print("🚨 Sparky PRs → URGENT review alerts")
    print("🔄 Continuous improvement loop running")
    print("=" * 60)
    print("Press Ctrl+C to stop all monitors")

    try:
        # Keep main process alive and monitor subprocesses
        while True:
            time.sleep(5)

            # Check if processes are still running
            if sister_process.poll() is not None:
                print("❌ Sister repo watcher stopped")
                break
            if sparky_process.poll() is not None:
                print("❌ Sparky PR monitor stopped")
                break

    except KeyboardInterrupt:
        print("\\n🛑 Stopping quality flywheel monitors...")

        # Terminate processes
        sister_process.terminate()
        sparky_process.terminate()

        # Wait for clean shutdown
        sister_process.wait(timeout=5)
        sparky_process.wait(timeout=5)

        print("✅ Quality flywheel stopped")


if __name__ == "__main__":
    start_monitors()
