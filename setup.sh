#!/bin/bash
# 12-Factor Agents Framework Setup

echo "🚀 Setting up 12-Factor Agents Framework"

# Install dependencies with uv
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "Installing Python dependencies..."
uv sync

echo "Installing pre-commit hooks..."
make install-hooks

echo "✅ Setup complete! See README.md for usage."
