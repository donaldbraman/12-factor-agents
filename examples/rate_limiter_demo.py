#!/usr/bin/env python3
"""
Rate Limiter Integration Demo

This script demonstrates how the rate limiter can be used with SmartIssueAgent
and other external service calls to prevent rate limit violations.
"""

import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rate_limiter import (  # noqa: E402
    RateLimiter,
    RateLimitExceeded,
    rate_limit,
    configure_global_rate_limiter,
)


def demo_basic_rate_limiting():
    """Demonstrate basic rate limiting functionality."""
    print("=" * 60)
    print("DEMO 1: Basic Rate Limiting")
    print("=" * 60)

    # Create rate limiter for GitHub API
    limiter = RateLimiter()
    limiter.configure_service("github_api", calls_per_minute=60, burst_capacity=20)

    print("Configured GitHub API: 60 calls/minute, 20 burst capacity")

    # Simulate API calls
    successful_calls = 0
    rate_limited_calls = 0

    for i in range(25):  # Try more than burst capacity
        try:
            limiter.check_rate_limit("github_api", "smart_issue_agent")
            successful_calls += 1
            print(f"✅ Call {i+1}: Success")
        except RateLimitExceeded as e:
            rate_limited_calls += 1
            print(f"❌ Call {i+1}: Rate limited (retry after {e.retry_after:.1f}s)")

    print(
        f"\nResults: {successful_calls} successful, {rate_limited_calls} rate limited"
    )

    # Show status
    status = limiter.get_status("github_api", "smart_issue_agent")
    print(f"Remaining tokens: {status['remaining_tokens']}")


def demo_decorator_usage():
    """Demonstrate rate limiting with decorator."""
    print("\n" + "=" * 60)
    print("DEMO 2: Decorator Usage")
    print("=" * 60)

    # Configure global rate limiter
    configure_global_rate_limiter()

    @rate_limit("openai_api", calls_per_minute=30, burst_capacity=10)
    def call_openai_api(prompt):
        """Simulate calling OpenAI API."""
        return f"Response to: {prompt[:30]}..."

    @rate_limit("slack_api", calls_per_minute=120, burst_capacity=50)
    def send_slack_notification(message):
        """Simulate sending Slack notification."""
        return f"Sent: {message[:20]}..."

    print("Testing OpenAI API calls (30/min, 10 burst):")
    for i in range(12):  # More than burst capacity
        try:
            result = call_openai_api(f"Analyze issue #{i+1}")
            print(f"✅ OpenAI Call {i+1}: {result}")
        except RateLimitExceeded as e:
            print(f"❌ OpenAI Call {i+1}: Rate limited ({e.retry_after:.1f}s)")

    print("\nTesting Slack notifications (120/min, 50 burst):")
    for i in range(5):
        try:
            result = send_slack_notification(f"Issue #{i+1} completed")
            print(f"✅ Slack {i+1}: {result}")
        except RateLimitExceeded as e:
            print(f"❌ Slack {i+1}: Rate limited ({e.retry_after:.1f}s)")


def demo_concurrent_access():
    """Demonstrate thread-safe concurrent access."""
    print("\n" + "=" * 60)
    print("DEMO 3: Concurrent Access")
    print("=" * 60)

    limiter = RateLimiter()
    limiter.configure_service("shared_api", calls_per_minute=60, burst_capacity=15)

    results = []

    def worker_thread(worker_id, num_calls):
        """Simulate a worker making API calls."""
        thread_results = []
        for i in range(num_calls):
            try:
                limiter.check_rate_limit("shared_api", f"agent_{worker_id}")
                thread_results.append(f"Worker {worker_id} Call {i+1}: ✅")
            except RateLimitExceeded as e:
                thread_results.append(
                    f"Worker {worker_id} Call {i+1}: ❌ ({e.retry_after:.1f}s)"
                )
            time.sleep(0.1)  # Small delay between calls
        results.extend(thread_results)

    print("Starting 3 workers, each making 8 calls...")

    # Run workers concurrently
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(worker_thread, worker_id, 8) for worker_id in range(1, 4)
        ]

        for future in as_completed(futures):
            future.result()

    # Print results
    for result in sorted(results):
        print(result)

    successful = len([r for r in results if "✅" in r])
    failed = len([r for r in results if "❌" in r])
    print(f"\nTotal: {successful} successful, {failed} rate limited")


def demo_service_isolation():
    """Demonstrate that different services have separate limits."""
    print("\n" + "=" * 60)
    print("DEMO 4: Service Isolation")
    print("=" * 60)

    limiter = RateLimiter()
    limiter.configure_service("service_a", calls_per_minute=12, burst_capacity=3)
    limiter.configure_service("service_b", calls_per_minute=12, burst_capacity=3)

    print("Both services configured: 12 calls/min, 3 burst capacity")

    # Use up Service A's capacity
    print("\nUsing up Service A's capacity:")
    for i in range(5):
        try:
            limiter.check_rate_limit("service_a", "agent1")
            print(f"✅ Service A Call {i+1}: Success")
        except RateLimitExceeded as e:
            print(f"❌ Service A Call {i+1}: Rate limited ({e.retry_after:.1f}s)")

    # Service B should still work
    print("\nService B should still work:")
    for i in range(5):
        try:
            limiter.check_rate_limit("service_b", "agent1")
            print(f"✅ Service B Call {i+1}: Success")
        except RateLimitExceeded as e:
            print(f"❌ Service B Call {i+1}: Rate limited ({e.retry_after:.1f}s)")


def demo_smart_issue_agent_integration():
    """Demonstrate integration with SmartIssueAgent-like workflow."""
    print("\n" + "=" * 60)
    print("DEMO 5: SmartIssueAgent Integration")
    print("=" * 60)

    # Configure rate limiter for various external services
    limiter = RateLimiter()
    limiter.configure_service("github_api", calls_per_minute=60, burst_capacity=20)
    limiter.configure_service("openai_api", calls_per_minute=30, burst_capacity=10)
    limiter.configure_service("slack_api", calls_per_minute=120, burst_capacity=50)

    print("Configured services:")
    print("- GitHub API: 60 calls/min, 20 burst")
    print("- OpenAI API: 30 calls/min, 10 burst")
    print("- Slack API: 120 calls/min, 50 burst")

    class MockSmartIssueAgent:
        """Mock SmartIssueAgent to demonstrate rate limiting integration."""

        def __init__(self, agent_id, rate_limiter):
            self.agent_id = agent_id
            self.limiter = rate_limiter

        def process_issue(self, issue_id):
            """Process an issue with rate-limited external calls."""
            print(f"\n🧠 Agent {self.agent_id} processing issue #{issue_id}")

            steps = [
                ("github_api", "Fetching issue details from GitHub"),
                ("openai_api", "Analyzing issue complexity"),
                ("github_api", "Checking related issues"),
                ("openai_api", "Generating solution"),
                ("github_api", "Creating pull request"),
                ("slack_api", "Sending completion notification"),
            ]

            for service, description in steps:
                try:
                    self.limiter.check_rate_limit(service, self.agent_id)
                    print(f"   ✅ {description}")
                except RateLimitExceeded as e:
                    print(
                        f"   ❌ {description} - Rate limited (retry after {e.retry_after:.1f}s)"
                    )
                    return False

            return True

    # Create multiple agents
    agents = [MockSmartIssueAgent(f"agent_{i}", limiter) for i in range(1, 4)]

    # Simulate processing multiple issues
    print("\nProcessing issues...")
    for issue_id in range(1, 8):
        agent = agents[(issue_id - 1) % len(agents)]
        success = agent.process_issue(issue_id)
        if success:
            print(f"   ✅ Issue #{issue_id} completed by {agent.agent_id}")
        else:
            print(f"   ❌ Issue #{issue_id} rate limited for {agent.agent_id}")


def main():
    """Run all demonstrations."""
    print("🚀 Rate Limiter Integration Demonstration")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        demo_basic_rate_limiting()
        demo_decorator_usage()
        demo_concurrent_access()
        demo_service_isolation()
        demo_smart_issue_agent_integration()

        print("\n" + "=" * 60)
        print("✅ All demonstrations completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
