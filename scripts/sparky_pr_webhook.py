#!/usr/bin/env python3
"""
Sparky PR Webhook Alert

Creates a GitHub webhook payload that can trigger immediate alerts
when Sparky creates a PR. This provides instant notification.
"""

from pathlib import Path


def create_sparky_alert_webhook():
    """Create webhook configuration for Sparky PR alerts"""

    alert_script = """#!/bin/bash
# GitHub Actions workflow for Sparky PR alerts
# Place in .github/workflows/sparky-pr-alert.yml

name: Sparky PR Alert
on:
  pull_request:
    types: [opened]

jobs:
  sparky-alert:
    runs-on: ubuntu-latest
    steps:
      - name: Check if Sparky PR
        id: check-sparky
        run: |
          if [[ "${{ github.event.pull_request.body }}" == *"🤖 Generated with"* ]] || 
             [[ "${{ github.event.pull_request.body }}" == *"Co-Authored-By: Claude"* ]] ||
             [[ "${{ github.event.pull_request.title }}" == *"fix"* ]] ||
             [[ "${{ github.event.pull_request.title }}" == *"improve"* ]]; then
            echo "sparky=true" >> $GITHUB_OUTPUT
          fi
      
      - name: Send Sparky Alert
        if: steps.check-sparky.outputs.sparky == 'true'
        run: |
          echo "🚨🚨🚨 URGENT SPARKY PR ALERT 🚨🚨🚨"
          echo "PR #${{ github.event.pull_request.number }}: ${{ github.event.pull_request.title }}"
          echo "URL: ${{ github.event.pull_request.html_url }}"
          echo "🚨 REQUIRES EXTREME REVIEW - SELF-MODIFYING AI 🚨"
          
          # Post to Slack/Discord if configured
          curl -X POST -H 'Content-type: application/json' \\
            --data "{\\"text\\":\\"🚨 SPARKY PR ALERT: #${{ github.event.pull_request.number }} - ${{ github.event.pull_request.title }} - REQUIRES EXTREME REVIEW\\"}" \\
            $SLACK_WEBHOOK_URL || true
"""

    print("🔗 GitHub Webhook Setup for Sparky PR Alerts")
    print("=" * 50)
    print("1. Create .github/workflows/sparky-pr-alert.yml:")
    print(alert_script)
    print("=" * 50)
    print("2. Configure webhook in GitHub repository settings")
    print("3. Add Slack/Discord webhook URL as secret")
    print("=" * 50)

    # Save the workflow file
    workflow_dir = Path(__file__).parent.parent / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)

    workflow_file = workflow_dir / "sparky-pr-alert.yml"
    with open(workflow_file, "w") as f:
        f.write(
            alert_script.replace(
                "#!/bin/bash\\n# GitHub Actions workflow for Sparky PR alerts\\n# Place in .github/workflows/sparky-pr-alert.yml\\n\\n",
                "",
            )
        )

    print(f"✅ Created: {workflow_file}")


if __name__ == "__main__":
    create_sparky_alert_webhook()
