#!/bin/bash
set -e

# 12-Factor Agents New Repository Setup Script
# Usage: ./setup-new-repo.sh [target-directory]

TARGET_DIR=${1:-$(pwd)}
FRAMEWORK_REPO="https://github.com/donaldbraman/12-factor-agents.git"

echo "🚀 Setting up 12-Factor Agents in: $TARGET_DIR"

cd "$TARGET_DIR"

# Check if we're in a git repo
if [ ! -d .git ]; then
    echo "⚠️  Not a git repository. Initialize with: git init --initial-branch=main"
    exit 1
fi

# Add submodule
echo "📦 Adding agents-framework submodule..."
git submodule add "$FRAMEWORK_REPO" agents-framework
git submodule update --init --recursive

# Create directories
echo "📁 Creating directory structure..."
mkdir -p bin issues

# Create wrapper script
echo "🔧 Creating CLI wrapper..."
cat > bin/agent << 'EOF'
#!/usr/bin/env python3
"""
Wrapper script for 12-factor-agents CLI in new repositories.
This allows './bin/agent' to work from any repo that includes the framework.
"""
import sys
import os
from pathlib import Path

# Find the agents-framework directory
script_dir = Path(__file__).parent.parent
agents_framework = script_dir / "agents-framework"

if not agents_framework.exists():
    print("Error: agents-framework not found. Please ensure it's installed as:")
    print("  git submodule add https://github.com/donaldbraman/12-factor-agents.git agents-framework")
    sys.exit(1)

# Add framework to path and run the CLI
sys.path.insert(0, str(agents_framework))
agent_cli = agents_framework / "bin" / "agent.py"

if not agent_cli.exists():
    print(f"Error: {agent_cli} not found")
    sys.exit(1)

# Execute the agent CLI with all arguments, but from the repo root
import subprocess
# Run from the parent repo, not the framework directory
result = subprocess.run([sys.executable, str(agent_cli)] + sys.argv[1:], cwd=str(script_dir))
sys.exit(result.returncode)
EOF

chmod +x bin/agent

# Create test issue
echo "📝 Creating test issue..."
cat > issues/001-test-setup.md << 'EOF'
# Issue #001: Test Agent Setup

## Description
Verify that the 12-factor agents system is properly installed and working.

## Current
```bash
# No agent system
```

## Required
```bash  
# Working agent system
./bin/agent list
./bin/agent run SmartIssueAgent "001"
```

## Files
- bin/agent (executable wrapper)
- agents-framework/ (submodule)

## Success Criteria
- [ ] CLI lists all available agents
- [ ] SmartIssueAgent can process this issue
- [ ] System is ready for production use

## Type
test

## Priority
high

## Status
open

## Assignee
smart_issue_agent
EOF

# Test installation
echo "🧪 Testing installation..."
if ./bin/agent list > /dev/null 2>&1; then
    echo "✅ Agent CLI working!"
else
    echo "❌ Agent CLI failed. Check installation."
    exit 1
fi

# Add to git
echo "💾 Committing changes..."
git add .
git commit -m "Add 12-factor agents framework

🤖 Generated with 12-factor agents setup script

Co-Authored-By: Agent Setup Script <noreply@anthropic.com>"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Test the system: ./bin/agent run SmartIssueAgent \"001\""
echo "  2. Read the guide: agents-framework/docs/NEW-REPO-GUIDE.md"  
echo "  3. Create real issues and start automating!"
echo ""
echo "Available agents:"
./bin/agent list | head -10