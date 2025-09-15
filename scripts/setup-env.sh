#!/bin/bash
# Setup environment for PR Review Agent using existing credentials

echo "🔧 Setting up environment for PR Review Agent..."

# Get GitHub token from gh CLI if available
if command -v gh &> /dev/null; then
    GITHUB_TOKEN=$(gh auth token 2>/dev/null)
    if [ -n "$GITHUB_TOKEN" ]; then
        export GITHUB_TOKEN
        echo "✅ GitHub token loaded from gh CLI"
    else
        echo "❌ No GitHub token found in gh CLI"
    fi
else
    echo "⚠️ GitHub CLI not installed"
fi

# Check for Anthropic API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "⚠️ ANTHROPIC_API_KEY not found in environment"
    echo "   Please set it with: export ANTHROPIC_API_KEY=your_key"
    echo "   Get your key from: https://console.anthropic.com/settings/keys"
else
    echo "✅ Anthropic API key found in environment"
fi

# Set default repo
export GITHUB_DEFAULT_REPO="${GITHUB_DEFAULT_REPO:-donaldbraman/12-factor-agents}"
echo "📦 Default repo: $GITHUB_DEFAULT_REPO"

# Test the setup
echo ""
echo "🧪 Testing PR Review Agent setup..."
echo "-----------------------------------"

# Check if we can authenticate with GitHub
if [ -n "$GITHUB_TOKEN" ]; then
    echo -n "GitHub authentication: "
    if gh api user &>/dev/null; then
        USER=$(gh api user --jq .login)
        echo "✅ Authenticated as $USER"
    else
        echo "❌ Failed to authenticate"
    fi
fi

# Check if we can use the agent
echo -n "PR Review Agent: "
if uv run agent info PRReviewAgent &>/dev/null; then
    echo "✅ Agent available"
else
    echo "❌ Agent not found"
fi

echo ""
echo "-----------------------------------"
if [ -n "$GITHUB_TOKEN" ] && [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✅ Ready to review PRs!"
    echo ""
    echo "Usage examples:"
    echo "  uv run agent run PRReviewAgent 'review PR #123'"
    echo "  uv run agent run PRReviewAgent 'analyze PR #456 in owner/repo'"
else
    echo "⚠️ Missing credentials. Please set:"
    [ -z "$GITHUB_TOKEN" ] && echo "  - GITHUB_TOKEN"
    [ -z "$ANTHROPIC_API_KEY" ] && echo "  - ANTHROPIC_API_KEY"
fi