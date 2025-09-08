# Seamless Integration Guide: Symlink Strategy for External Repositories

This guide shows how external repositories can seamlessly integrate with the 12-factor-agents framework using a single symlink setup, providing access to code, documentation, examples, and all resources locally.

## Overview

The symlink strategy allows external repos to:
- ✅ Access all framework code without copying
- ✅ Read documentation and guides locally
- ✅ Use examples and templates directly
- ✅ Stay automatically updated with framework improvements
- ✅ Maintain clean separation between framework and application code

## Recommended Symlink Structure

### Single Symlink Approach (Recommended)

Create one symlink to the entire 12-factor-agents repository:

```bash
# In your project root
ln -s ../12-factor-agents .framework

# Or relative to your .agents directory  
mkdir -p .agents
cd .agents
ln -s ../../12-factor-agents framework
```

This provides access to everything:

```
your-project/
├── .agents/
│   ├── framework -> ../../12-factor-agents  [SYMLINK]
│   └── your_project/                        [Your agents]
│       ├── domain_specific_agent.py
│       └── workflow_agent.py
```

### Granular Symlink Approach (Pin-Citer Style)

For more control, create specific symlinks:

```bash
cd .agents
ln -s ../../12-factor-agents/core core
ln -s ../../12-factor-agents/agents agents  
ln -s ../../12-factor-agents/docs docs
ln -s ../../12-factor-agents/examples examples
ln -s ../../12-factor-agents/scripts scripts
```

Structure:
```
your-project/
├── .agents/
│   ├── core -> ../../12-factor-agents/core           [SYMLINK]
│   ├── agents -> ../../12-factor-agents/agents       [SYMLINK] 
│   ├── docs -> ../../12-factor-agents/docs          [SYMLINK]
│   ├── examples -> ../../12-factor-agents/examples   [SYMLINK]
│   ├── scripts -> ../../12-factor-agents/scripts     [SYMLINK]
│   └── your_project/                                 [Your agents]
```

## Usage Examples

### Code Imports

```python
# Import framework components
from .framework.core.context_bundles import ContextBundle, BundleEnabledAgent
from .framework.core.background_executor import BackgroundAgentExecutor
from .framework.agents.base import BaseAgent

# Or with granular symlinks
from .core.context_bundles import ContextBundle
from .agents.base import BaseAgent
```

### Documentation Access

```python
# Read documentation locally in your IDE/editor
# .agents/framework/docs/12-FACTOR-AGENTS.md
# .agents/framework/docs/CONTEXT-BUNDLES.md  
# .agents/framework/docs/BACKGROUND-EXECUTOR.md

# Or access setup scripts
# .agents/framework/scripts/setup_project.py
# .agents/framework/examples/context_bundle_example.py
```

### Launch Scripts

```python
# Use framework launcher directly
from .framework.scripts.launch_agent import launch_agent

# Or copy and customize
cp .agents/framework/scripts/launch_agent.py .agents/scripts/custom_launcher.py
```

## Integration Workflows

### New Context-Conserving Features

External repos can immediately use our new features:

```python
# Context Bundles for perfect handoffs
from .framework.core.context_bundles import ContextBundle, BundleEnabledAgent

class YourAgent(BundleEnabledAgent):
    def __init__(self):
        super().__init__(session_id="your_session")
        
    async def process_task(self, task):
        # Your existing logic with perfect context preservation
        result = await self.your_domain_logic(task)
        
        # Create context bundle for handoff
        context = ContextBundle(
            execution_state={"result": result},
            conversation_history=self.conversation_log,
            domain_context={"domain": "your_domain"},
            handoff_instructions="Continue processing with result",
            success_criteria=["Task completed", "Quality verified"]
        )
        
        # Hand off to next agent with zero context loss
        return await self.handoff_to_agent("next_agent", context)
```

```python
# Background Agent Executor for concurrent processing
from .framework.core.background_executor import BackgroundAgentExecutor

class YourWorkflowOrchestrator:
    def __init__(self):
        self.executor = BackgroundAgentExecutor(max_parallel_agents=20)
        
    async def process_multiple_tasks(self, tasks):
        # Launch tasks concurrently (fire-and-forget)
        task_ids = []
        for task in tasks:
            task_id = await self.executor.spawn_background_agent(
                agent_class="YourDomainAgent",
                task=f"process_{task.id}",
                workflow_data=task.to_dict()
            )
            task_ids.append(task_id)
            
        # Continue working while background tasks run
        return task_ids
```

### R&D Framework Integration

```python
# Access R&D patterns and optimization
from .framework.core.context_optimizer import ContextOptimizer

# Use documented patterns
# .agents/framework/docs/CONTEXT-OPTIMIZATION.md
# .agents/framework/examples/r_and_d_example.py
```

## Setup Automation

### Quick Setup Script

Create this in your project root:

```bash
#!/bin/bash
# setup_framework_integration.sh

echo "Setting up 12-factor-agents framework integration..."

# Ensure 12-factor-agents is cloned at same level
if [ ! -d "../12-factor-agents" ]; then
    echo "Cloning 12-factor-agents framework..."
    cd ..
    git clone https://github.com/humanlayer/12-factor-agents.git
    cd -
fi

# Create .agents directory if it doesn't exist
mkdir -p .agents

# Create symlinks
cd .agents
if [ ! -L "framework" ]; then
    ln -s ../../12-factor-agents framework
    echo "✅ Created framework symlink"
else
    echo "✅ Framework symlink already exists"
fi

# Verify setup
if [ -f "framework/core/context_bundles.py" ]; then
    echo "✅ Framework integration successful"
    echo "✅ Context Bundles available"
    echo "✅ Background Executor available" 
    echo "✅ Documentation accessible at .agents/framework/docs/"
else
    echo "❌ Setup failed - check symlink"
fi
```

### Python Path Setup

Add to your agents' `__init__.py`:

```python
import sys
from pathlib import Path

# Add framework to Python path
framework_path = Path(__file__).parent / "framework"
if framework_path.exists():
    sys.path.insert(0, str(framework_path))
    
# Now you can import framework components directly
try:
    from core.context_bundles import ContextBundle
    from core.background_executor import BackgroundAgentExecutor
    print("✅ Framework integration successful")
except ImportError as e:
    print(f"❌ Framework import failed: {e}")
```

## Benefits for External Repos

### Immediate Access to New Features

- **Context Bundles**: Perfect handoffs with zero context loss
- **Background Executor**: 20-30+ concurrent agents 
- **R&D Framework**: Systematic context optimization
- **All Documentation**: Local access to guides, patterns, examples

### Automatic Updates

```bash
# In 12-factor-agents repo
git pull

# External repos automatically get updates via symlinks
# No manual syncing required!
```

### Development Workflow

```python
# External repo can:
1. Read framework docs locally: .agents/framework/docs/
2. Copy examples: cp .agents/framework/examples/context_example.py ./
3. Use scripts: .agents/framework/scripts/benchmark.py  
4. Import components: from .framework.core import *
5. Extend base classes: class MyAgent(framework.agents.base.BaseAgent)
```

## Real-World Example: Pin-Citer Integration

Pin-citer already uses this pattern successfully:

```
pin-citer/
├── .agents/
│   ├── core -> ../../12-factor-agents/core       [Framework code]
│   ├── docs -> ../../12-factor-agents/docs       [Framework docs] 
│   ├── pin_citer/                                [Their agents]
│   │   ├── citation_pipeline_agent.py
│   │   └── zotero_search_agent.py
│   └── scripts/                                  [Their scripts]
```

They can:
- Import framework: `from core.context_bundles import ContextBundle`
- Read docs locally: `cat .agents/docs/CONTEXT-BUNDLES.md`
- Use examples: `cp .agents/examples/context_example.py ./pin_citer/`

## Migration Path

### For Existing Projects

1. **Backup current setup**
2. **Clone 12-factor-agents** at same directory level
3. **Create symlinks** using setup script above
4. **Update imports** to use symlinked paths
5. **Test integration** with simple imports
6. **Gradually adopt** new context-conserving features

### Validation

```python
# Test script to verify integration
import sys
from pathlib import Path

def test_framework_integration():
    """Test that framework integration is working"""
    
    # Test symlink exists
    framework_path = Path(".agents/framework")
    if not framework_path.exists():
        print("❌ Framework symlink missing")
        return False
        
    # Test imports work
    sys.path.insert(0, str(framework_path))
    try:
        from core.context_bundles import ContextBundle
        from core.background_executor import BackgroundAgentExecutor
        print("✅ Core imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
        
    # Test documentation accessible  
    docs_path = framework_path / "docs"
    if not docs_path.exists():
        print("❌ Documentation not accessible")
        return False
        
    print("✅ Framework integration fully working")
    print(f"✅ {len(list(docs_path.glob('*.md')))} documentation files accessible")
    return True

if __name__ == "__main__":
    test_framework_integration()
```

## Conclusion

The symlink strategy provides:
- **Zero-copy integration** - no code duplication
- **Automatic updates** - pull framework, external repos benefit immediately  
- **Full resource access** - code, docs, examples, scripts all available locally
- **Clean separation** - framework vs application code stays organized
- **IDE/editor support** - local files work with autocomplete, go-to-definition, etc.

This makes adopting our context-conserving agentic workflows as simple as creating a symlink and updating imports. External repos get all the benefits with minimal integration effort.