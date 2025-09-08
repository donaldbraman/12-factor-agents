#!/bin/bash
# Setup script for 12-factor-agents framework

echo "🚀 Setting up 12-factor-agents framework..."

# Create shared state directory
mkdir -p ~/.claude-shared-state/{global,by-repo,locks,history,events,pids}

# Make CLI executable
chmod +x bin/agent 2>/dev/null || true

# Create initial registry
echo '{"agents": {}}' > ~/.claude-shared-state/agent-registry.json

# Install Python dependencies (if any)
if [ -f requirements.txt ]; then
    echo "📦 Installing Python dependencies..."
    uv pip install -r requirements.txt
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. In your project: ln -s $(pwd)/core .claude/agents"
echo "2. Run an agent: ./bin/agent list"
echo ""
