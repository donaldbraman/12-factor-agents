# 12-Factor Agents for New Repositories
**Add intelligent agent automation to any repository in 5 minutes.**

## Prerequisites
- Python 3.8+ 
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Installation

### Option 1: Automated Setup (Recommended)
```bash
# In your repository root
curl -sSL https://raw.githubusercontent.com/donaldbraman/12-factor-agents/main/bin/setup-new-repo.sh | bash

# Or download and run manually
wget https://raw.githubusercontent.com/donaldbraman/12-factor-agents/main/bin/setup-new-repo.sh
chmod +x setup-new-repo.sh
./setup-new-repo.sh

# Test installation
./bin/agent list
./bin/agent run SmartIssueAgent "001"
```

### Option 2: Manual Git Submodule
```bash
# In your repository root
git submodule add https://github.com/donaldbraman/12-factor-agents.git agents-framework
git submodule update --init --recursive

# Create wrapper script for easy access
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

# Test installation
./bin/agent list
```

### Option 3: Direct Clone (Development)
```bash
# Clone into your repo
git clone https://github.com/donaldbraman/12-factor-agents.git agents-framework
cd agents-framework

# Test installation  
uv run python bin/agent.py list
```

### Option 4: Copy Core Files (Not Recommended)
```bash
# Download essential files only
mkdir -p {core,agents,bin}
curl -O https://raw.githubusercontent.com/donaldbraman/12-factor-agents/main/bin/agent.py
curl -O https://raw.githubusercontent.com/donaldbraman/12-factor-agents/main/core/agent.py
# ... (download other essential files)

# Note: This requires manual updates
```

## Quick Start

### 1. Create Your First Issue
```bash
mkdir -p issues
cat > issues/001-update-readme.md << 'EOF'
# Issue #001: Update README with Agent Integration

## Description
Add a section to README.md explaining the new agent system.

## Current
```markdown
# Test Project
```

## Required
```markdown  
# Test Project

## Agent Automation
This project uses 12-factor agents for intelligent task automation.

Run any task: `./bin/agent run SmartIssueAgent "issue-number"`
```

## Files
- README.md (append to end of file)

## Success Criteria
- [ ] README includes agent section
- [ ] Instructions are clear and actionable
EOF
```

### 2. Test the System
```bash
# From your repo root (Option 1 - submodule)
./bin/agent run SmartIssueAgent "001"

# Or (Option 2 - direct clone)
cd agents-framework && uv run python bin/agent.py run SmartIssueAgent "001"

# Expected output:
# ✅ Issue is simple - handling directly
# ✅ Task completed successfully
```

### 3. You're Ready!
```bash
# Submit any issue to the universal agent
./bin/agent run SmartIssueAgent "your-issue-number"
```

## Repository Structure

After installation, your repo should look like:

```
your-repo/
├── agents-framework/           # Git submodule
│   ├── bin/agent.py           # CLI tool  
│   ├── core/                  # Base classes
│   ├── agents/                # All agent implementations
│   └── docs/                  # Documentation
├── bin/agent -> agents-framework/bin/agent.py  # Symlink
├── issues/                    # Your issues go here
│   ├── 001-test-automation.md
│   └── 002-next-task.md
└── your-project-files...
```

## Creating Issues That Work

### ✅ Good Issue Format
```markdown
# Issue #042: Update API Documentation

## Description
API docs are outdated and missing new endpoints.

## Current
```python
# old_api.py
def get_users():
    return {"users": []}
```

## Required
```python  
# updated_api.py
def get_users():
    return {"users": [], "total": 0, "page": 1}

def get_user(id):
    return {"user": user_data}
```

## Files
- api/handlers.py (lines 45-60)  
- docs/api.md (endpoint section)

## Success Criteria
- [ ] New endpoints documented
- [ ] Examples include response format
- [ ] All existing docs updated
```

**Why this works:**
- Clear Current/Required blocks
- Specific file paths and line numbers
- Actionable success criteria
- Concrete examples

### ❌ Poor Issue Format
```markdown
# Issue: Make things better

Please improve our codebase somehow.
```

**Why this fails:**
- No specific changes defined
- No target files identified  
- No success criteria
- Vague requirements

## Complexity Levels

The system automatically handles any complexity:

### Atomic/Simple → Direct Processing
```
Your Issue → SmartIssueAgent → Direct Fix → ✅ Done
```

### Moderate/Complex → Auto-Decomposition  
```
Your Issue → SmartIssueAgent → 3 Sub-Issues → 3 Agents → ✅ Done
```

### Enterprise → Hierarchical Orchestration
```  
Your Issue → SmartIssueAgent → 6 Sub-Issues → Multiple Agents → ✅ Done
```

**You never need to think about complexity.** Submit any issue and get results.

## Advanced Configuration

### Custom Agent Directory
```bash
# Point to different agent location
export AGENTS_PATH="/path/to/your/agents"
./bin/agent list
```

### Custom Issue Directory  
```bash
# Use different issues folder
export ISSUES_PATH="/path/to/your/issues"
./bin/agent run SmartIssueAgent "001"
```

### Integration with CI/CD
```yaml
# .github/workflows/agent-automation.yml
name: Agent Automation
on: [issues, pull_request]

jobs:
  process-issues:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: true
      - uses: astral-sh/setup-uv@v1
      - name: Process Issue
        run: ./bin/agent run SmartIssueAgent "${{ github.event.issue.number }}"
```

## Troubleshooting

### Command Not Found
```bash
# If ./bin/agent doesn't work
ls -la bin/agent  # Check symlink exists
chmod +x bin/agent  # Make executable
```

### Import Errors  
```bash
# If Python can't find modules
cd agents-framework  # Run from framework directory
uv run python bin/agent.py list  # Use full path
```

### No Issues Found
```bash
# Verify issue file exists  
ls issues/001*.md
# Check issue number format
./bin/agent run SmartIssueAgent "001"  # Not "#001" 
```

### Permission Errors
```bash
# Fix file permissions
chmod +x agents-framework/bin/agent.py
chmod -R 755 agents-framework/
```

## Production Deployment

### Repository Maintenance
```bash
# Update to latest framework
git submodule update --remote agents-framework

# Check system health
./bin/agent info SmartIssueAgent

# Backup issue history  
tar -czf issues-backup-$(date +%Y%m%d).tar.gz issues/
```

### Scaling Considerations
- **Issue Growth**: System handles 1000+ issues efficiently
- **Agent Performance**: Each agent is stateless and fast
- **Resource Usage**: Minimal overhead, Python process per execution
- **Concurrent Processing**: Safe for parallel issue execution

## Success Metrics

After 1 week of usage, you should see:
- ✅ **90%+ issue automation** (manual intervention drops dramatically)
- ✅ **Faster task completion** (decomposition speeds up complex work)  
- ✅ **Better task specification** (clear current/required patterns emerge)
- ✅ **Reduced context switching** (one universal agent handles everything)

---

## Next Steps

1. **Start small**: Create 2-3 test issues
2. **Submit them**: Use SmartIssueAgent for everything
3. **Learn the patterns**: Notice what works best
4. **Scale up**: Submit real work through the system
5. **Customize**: Add project-specific agents if needed

**You now have production-ready agent automation in your repository.**

---
*Built with [12-Factor Agent principles](https://github.com/humanlayer/12-factor-agents) for enterprise reliability.*