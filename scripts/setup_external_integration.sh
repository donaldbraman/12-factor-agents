#!/bin/bash
# Setup script for external repositories to integrate with 12-factor-agents framework
# Usage: curl -sSL https://raw.githubusercontent.com/humanlayer/12-factor-agents/main/scripts/setup_external_integration.sh | bash

set -e

echo "🤖 12-Factor Agents Framework Integration Setup"
echo "=============================================="

# Detect current directory and project
PROJECT_DIR=$(pwd)
PROJECT_NAME=$(basename "$PROJECT_DIR")

echo "📁 Setting up integration for project: $PROJECT_NAME"
echo "📍 Project directory: $PROJECT_DIR"

# Check if 12-factor-agents exists at same level
FRAMEWORK_PATH="../12-factor-agents"
if [ ! -d "$FRAMEWORK_PATH" ]; then
    echo "⬇️ Cloning 12-factor-agents framework..."
    cd ..
    if git clone https://github.com/humanlayer/12-factor-agents.git; then
        echo "✅ Framework cloned successfully"
    else
        echo "❌ Failed to clone framework. Please clone manually:"
        echo "   cd .. && git clone https://github.com/humanlayer/12-factor-agents.git"
        exit 1
    fi
    cd "$PROJECT_DIR"
else
    echo "✅ 12-factor-agents framework found"
fi

# Create .agents directory if it doesn't exist
if [ ! -d ".agents" ]; then
    mkdir -p .agents
    echo "📁 Created .agents directory"
fi

cd .agents

# Create symlinks
echo "🔗 Setting up symlinks..."

# Single comprehensive symlink (recommended)
if [ ! -L "framework" ]; then
    ln -s ../../12-factor-agents framework
    echo "✅ Created framework symlink (.agents/framework -> ../../12-factor-agents)"
else
    echo "✅ Framework symlink already exists"
fi

# Optional: Create granular symlinks for more control
create_granular_symlinks() {
    local components=("core" "agents" "docs" "examples" "scripts")
    
    echo "🔧 Creating granular symlinks for fine-grained control..."
    for component in "${components[@]}"; do
        if [ ! -L "$component" ] && [ -d "../../12-factor-agents/$component" ]; then
            ln -s "../../12-factor-agents/$component" "$component"
            echo "✅ Created $component symlink"
        fi
    done
}

# Ask user preference
echo ""
echo "Choose symlink strategy:"
echo "1. Single framework symlink (recommended - provides access to everything)"
echo "2. Granular symlinks (core, agents, docs, examples, scripts separately)"
echo "3. Both (comprehensive + granular for maximum flexibility)"
read -p "Enter choice (1-3) [default: 1]: " choice
choice=${choice:-1}

case $choice in
    2)
        create_granular_symlinks
        ;;
    3)
        create_granular_symlinks
        ;;
    *)
        echo "✅ Using single framework symlink (recommended)"
        ;;
esac

cd ..

# Verify integration
echo ""
echo "🔍 Verifying integration..."

# Check if framework files are accessible
if [ -f ".agents/framework/core/context_bundles.py" ]; then
    echo "✅ Context Bundles available"
else
    echo "❌ Context Bundles not accessible"
fi

if [ -f ".agents/framework/core/background_executor.py" ]; then
    echo "✅ Background Agent Executor available"
else
    echo "❌ Background Agent Executor not accessible"
fi

if [ -d ".agents/framework/docs" ]; then
    doc_count=$(ls .agents/framework/docs/*.md 2>/dev/null | wc -l)
    echo "✅ Documentation accessible ($doc_count guides available)"
else
    echo "❌ Documentation not accessible"
fi

if [ -d ".agents/framework/examples" ]; then
    example_count=$(ls .agents/framework/examples/*.py 2>/dev/null | wc -l)
    echo "✅ Examples accessible ($example_count examples available)"
else
    echo "❌ Examples not accessible"
fi

# Create integration test file
echo ""
echo "🧪 Creating integration test file..."

cat > test_framework_integration.py << 'EOF'
#!/usr/bin/env python3
"""
Test script to verify 12-factor-agents framework integration
Run this to ensure everything is working correctly.
"""
import sys
import os
from pathlib import Path

def test_framework_integration():
    """Test that framework integration is working"""
    
    print("🧪 Testing 12-Factor Agents Framework Integration")
    print("=" * 50)
    
    # Test symlink exists
    framework_path = Path(".agents/framework")
    if not framework_path.exists():
        print("❌ Framework symlink missing")
        print("   Run setup script: ./scripts/setup_external_integration.sh")
        return False
    else:
        print("✅ Framework symlink exists")
        
    # Add framework to path
    sys.path.insert(0, str(framework_path))
    
    # Test core imports
    try:
        from core.context_bundles import ContextBundle, BundleEnabledAgent
        print("✅ Context Bundles import successful")
    except ImportError as e:
        print(f"❌ Context Bundles import failed: {e}")
        return False
        
    try:
        from core.background_executor import BackgroundAgentExecutor
        print("✅ Background Agent Executor import successful")
    except ImportError as e:
        print(f"❌ Background Agent Executor import failed: {e}")
        return False
        
    try:
        from agents.base import BaseAgent
        print("✅ Base Agent import successful")
    except ImportError as e:
        print(f"❌ Base Agent import failed: {e}")
        return False
    
    # Test documentation accessibility
    docs_path = framework_path / "docs"
    if docs_path.exists():
        doc_files = list(docs_path.glob('*.md'))
        print(f"✅ {len(doc_files)} documentation files accessible")
        
        # List key documentation
        key_docs = [
            "12-FACTOR-AGENTS.md",
            "CONTEXT-BUNDLES.md", 
            "BACKGROUND-EXECUTOR.md",
            "SYMLINK-INTEGRATION-GUIDE.md"
        ]
        
        for doc in key_docs:
            if (docs_path / doc).exists():
                print(f"   📖 {doc} available")
    else:
        print("❌ Documentation not accessible")
        return False
    
    # Test examples accessibility
    examples_path = framework_path / "examples"
    if examples_path.exists():
        example_files = list(examples_path.glob('*.py'))
        print(f"✅ {len(example_files)} example files accessible")
    else:
        print("⚠️  Examples directory not accessible (optional)")
    
    # Test basic functionality
    try:
        # Test Context Bundle creation
        bundle = ContextBundle(
            execution_state={"test": "value"},
            conversation_history=["test message"],
            domain_context={"domain": "test"},
            handoff_instructions="test handoff",
            success_criteria=["test complete"]
        )
        print("✅ Context Bundle creation successful")
        
        # Test Background Executor creation
        executor = BackgroundAgentExecutor(max_parallel_agents=5)
        print("✅ Background Agent Executor creation successful")
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False
    
    print("")
    print("🎉 SUCCESS: Framework integration fully working!")
    print("")
    print("Next steps:")
    print("1. Read documentation: .agents/framework/docs/")
    print("2. Check examples: .agents/framework/examples/")  
    print("3. Start using Context Bundles for perfect handoffs")
    print("4. Use Background Executor for concurrent processing")
    
    return True

if __name__ == "__main__":
    success = test_framework_integration()
    sys.exit(0 if success else 1)
EOF

echo "✅ Created test_framework_integration.py"

# Make test file executable
chmod +x test_framework_integration.py

# Create quick start guide
echo ""
echo "📝 Creating quick start guide..."

cat > FRAMEWORK_INTEGRATION.md << 'EOF'
# 12-Factor Agents Framework Integration

This project is now integrated with the 12-factor-agents framework via symlinks.

## Quick Start

### Test Integration
```bash
python test_framework_integration.py
```

### Use Context Bundles (Perfect Handoffs)
```python
from .agents.framework.core.context_bundles import ContextBundle, BundleEnabledAgent

class YourAgent(BundleEnabledAgent):
    async def process_task(self, task):
        # Your logic here
        result = await self.your_domain_logic(task)
        
        # Create context bundle for perfect handoff
        context = ContextBundle(
            execution_state={"result": result},
            conversation_history=self.conversation_log,
            domain_context={"domain": "your_domain"},
            handoff_instructions="Continue with result",
            success_criteria=["Task completed"]
        )
        
        return await self.handoff_to_agent("next_agent", context)
```

### Use Background Agent Executor (Concurrent Processing)
```python
from .agents.framework.core.background_executor import BackgroundAgentExecutor

class YourOrchestrator:
    def __init__(self):
        self.executor = BackgroundAgentExecutor(max_parallel_agents=20)
        
    async def process_multiple_tasks(self, tasks):
        # Launch multiple agents concurrently
        task_ids = []
        for task in tasks:
            task_id = await self.executor.spawn_background_agent(
                agent_class="YourDomainAgent",
                task=f"process_{task.id}",
                workflow_data=task.to_dict()
            )
            task_ids.append(task_id)
            
        return task_ids  # Continue working while tasks run in background
```

## Available Resources

### Documentation (Local Access)
- `.agents/framework/docs/12-FACTOR-AGENTS.md` - Core methodology
- `.agents/framework/docs/CONTEXT-BUNDLES.md` - Perfect handoffs guide
- `.agents/framework/docs/BACKGROUND-EXECUTOR.md` - Concurrent processing guide
- `.agents/framework/docs/SYMLINK-INTEGRATION-GUIDE.md` - This integration pattern

### Examples
- `.agents/framework/examples/` - Working code examples
- Copy and modify: `cp .agents/framework/examples/context_example.py ./`

### Scripts
- `.agents/framework/scripts/` - Utility scripts
- Launch agents: `.agents/framework/scripts/launch_agent.py`

## Updates

To get framework updates:
```bash
cd ../12-factor-agents
git pull
# Your project automatically gets updates via symlinks!
```

## Support

- Documentation: `.agents/framework/docs/`
- Issues: https://github.com/humanlayer/12-factor-agents/issues
- Examples: `.agents/framework/examples/`
EOF

echo "✅ Created FRAMEWORK_INTEGRATION.md"

# Test the integration
echo ""
echo "🧪 Running integration test..."
if python3 test_framework_integration.py; then
    echo ""
    echo "🎉 SUCCESS: Integration complete!"
    echo ""
    echo "📖 Next steps:"
    echo "1. Read FRAMEWORK_INTEGRATION.md for usage guide"
    echo "2. Explore .agents/framework/docs/ for comprehensive documentation" 
    echo "3. Check .agents/framework/examples/ for working code examples"
    echo "4. Start using Context Bundles and Background Executor in your agents"
    echo ""
    echo "🔗 Your project can now use:"
    echo "   ✅ Context Bundles for perfect handoffs"
    echo "   ✅ Background Agent Executor for 20-30+ concurrent agents"
    echo "   ✅ R&D Framework for context optimization"
    echo "   ✅ All documentation and examples locally accessible"
else
    echo ""
    echo "⚠️  Integration test failed. Check the output above for issues."
    echo "💡 Try running: python3 test_framework_integration.py"
fi