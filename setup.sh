#!/bin/bash
# 12-Factor Agents Framework Setup

echo "🚀 Setting up 12-Factor Agents Framework"
echo "=" * 50

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv (our Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "✅ uv installed successfully"
else
    echo "✅ uv is already installed"
fi

echo ""
echo "🔧 Installing Python dependencies with uv..."
uv sync

echo ""
echo "🪝 Installing pre-commit hooks..."
uv run pre-commit install

echo ""
echo "🔗 Making CLI tools executable..."
chmod +x bin/agent.py 2>/dev/null || true
chmod +x bin/event.py 2>/dev/null || true

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Quick commands to get started:"
echo "  List agents:     uv run agent list"
echo "  Agent info:      uv run agent info <name>"
echo "  Run agent:       uv run agent run <name> '<task>'"
echo "  Run tests:       make test"
echo "  Format code:     make format"
echo "  Lint code:       make lint"
echo ""
echo "📖 See README.md for full documentation."
echo "💡 Try 'uv run agent list' to see all available agents!"
