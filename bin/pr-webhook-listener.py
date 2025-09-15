#!/usr/bin/env uv run python
"""
PR Webhook Listener - Automatically triggers PR reviews
"""

import hmac
import hashlib
from flask import Flask, request, jsonify
from pathlib import Path
import subprocess
import os
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)


def verify_github_signature(payload, signature):
    """Verify webhook came from GitHub"""
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode()
    if not secret:
        print("⚠️ Warning: GITHUB_WEBHOOK_SECRET not set")
        return True  # Allow for testing, but warn

    expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature or "")


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """Handle GitHub webhook events"""
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_github_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401

    # Parse event
    event_type = request.headers.get("X-GitHub-Event")
    payload = request.json

    print(f"📨 Received {event_type} event")

    if event_type == "pull_request":
        action = payload.get("action")
        print(f"  Action: {action}")

        if action in ["opened", "synchronize", "reopened"]:
            pr = payload["pull_request"]
            repo = payload["repository"]["full_name"]

            print(f"  PR #{pr['number']}: {pr['title']}")
            print(f"  Repository: {repo}")

            # Trigger PR review
            result = trigger_pr_review(pr["number"], repo)

            if result:
                return jsonify({"status": "review_triggered", "pr": pr["number"]}), 200
            else:
                return jsonify({"status": "review_failed", "pr": pr["number"]}), 500

    elif event_type == "pull_request_review_comment":
        # Handle review comments if needed
        print(f"  Review comment on PR #{payload['pull_request']['number']}")

    elif event_type == "ping":
        print("  Webhook configured successfully!")
        return jsonify({"status": "pong"}), 200

    return jsonify({"status": "processed"}), 200


def trigger_pr_review(pr_number: int, repo: str):
    """Trigger PRReviewAgent to review the PR"""
    try:
        print(f"\n🤖 Triggering PRReviewAgent for PR #{pr_number}")

        # Run the agent
        cmd = [
            "uv",
            "run",
            "agent",
            "run",
            "PRReviewAgent",
            f"review PR #{pr_number} in {repo}",
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )

        if result.returncode == 0:
            print("✅ Review completed successfully")
            print(result.stdout)
            return True
        else:
            print("❌ Review failed")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error triggering review: {e}")
        return False


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "pr-webhook-listener"}), 200


@app.route("/", methods=["GET"])
def index():
    """Root endpoint with setup instructions"""
    return """
    <h1>PR Webhook Listener</h1>
    <p>This service listens for GitHub PR webhooks and triggers automated reviews.</p>
    
    <h2>Setup Instructions:</h2>
    <ol>
        <li>Set environment variables:
            <ul>
                <li>GITHUB_TOKEN - Your GitHub personal access token</li>
                <li>GITHUB_WEBHOOK_SECRET - Webhook secret for verification</li>
                <li>ANTHROPIC_API_KEY - Claude API key for reviews</li>
            </ul>
        </li>
        <li>Configure GitHub webhook:
            <ul>
                <li>URL: https://your-domain.com/webhook</li>
                <li>Content type: application/json</li>
                <li>Secret: Same as GITHUB_WEBHOOK_SECRET</li>
                <li>Events: Pull requests</li>
            </ul>
        </li>
    </ol>
    
    <h2>Endpoints:</h2>
    <ul>
        <li>POST /webhook - GitHub webhook endpoint</li>
        <li>GET /health - Health check</li>
        <li>GET / - This page</li>
    </ul>
    
    <p>Status: <strong style="color: green;">Running</strong></p>
    """


if __name__ == "__main__":
    port = int(os.getenv("WEBHOOK_PORT", 8080))

    print(
        f"""
╔══════════════════════════════════════════════════╗
║        PR Webhook Listener Starting...           ║
╚══════════════════════════════════════════════════╝

🌐 Server: http://localhost:{port}
📝 Webhook URL: http://localhost:{port}/webhook
🏥 Health Check: http://localhost:{port}/health

Environment Variables:
  GITHUB_TOKEN: {'✅ Set' if os.getenv('GITHUB_TOKEN') else '❌ Not set'}
  GITHUB_WEBHOOK_SECRET: {'✅ Set' if os.getenv('GITHUB_WEBHOOK_SECRET') else '⚠️ Not set (insecure)'}
  ANTHROPIC_API_KEY: {'✅ Set' if os.getenv('ANTHROPIC_API_KEY') else '❌ Not set'}

Press Ctrl+C to stop
"""
    )

    app.run(host="0.0.0.0", port=port, debug=True)
