# Multi-Repository Agent Sharing Guide

## Overview
Yes! The 12-factor-agents repository is designed exactly for this purpose - **centralized agent sharing across all your repositories**. Here's how any repo in your GitHub directory can leverage this agent framework.

## Architecture

### Central Agent Repository
```
/Users/dbraman/Documents/GitHub/
├── 12-factor-agents/           # 🏗️ Central agent framework
│   ├── core/                   # Base classes & interfaces  
│   ├── agents/                 # Reusable agent implementations
│   ├── prompts/                # Shared prompt templates
│   ├── shared-state/           # Cross-repo state management
│   └── orchestration/          # Multi-agent pipelines
├── pin-citer/                  # 📄 Citation research project
├── zothein/                    # 🔍 Research assistant  
├── cite-assist/                # 📚 Citation assistance
└── [any other repo]/          # Any project can integrate!
```

## Integration Methods

### Method 1: Symlink Integration (Recommended)

Each repository creates a symlink to the 12-factor-agents framework:

```bash
# From any repository directory
cd /Users/dbraman/Documents/GitHub/pin-citer
ln -s ../12-factor-agents/core .agents/core
ln -s ../12-factor-agents/agents .agents/agents
ln -s ../12-factor-agents/prompts .agents/prompts

# Now pin-citer can use any agent:
from .agents.agents.code_review_agent import CodeReviewAgent
from .agents.core.agent import BaseAgent
```

### Method 2: Git Submodule (Version Controlled)

For production repositories that need version control:

```bash
# From any repository 
cd /Users/dbraman/Documents/GitHub/pin-citer
git submodule add ../12-factor-agents .agents
git commit -m "Add 12-factor-agents framework"

# Update framework when needed
git submodule update --remote .agents
```

### Method 3: Environment-Based (Development)

Set environment variable to point to central framework:

```bash
# In ~/.bashrc or ~/.zshrc
export TWELVE_FACTOR_AGENTS_PATH="/Users/dbraman/Documents/GitHub/12-factor-agents"

# In your Python code
import sys
import os
sys.path.insert(0, os.getenv('TWELVE_FACTOR_AGENTS_PATH'))

from core.agent import BaseAgent
from agents.code_review_agent import CodeReviewAgent
```

## Shared Agent Library

### Currently Available Agents

All repos can immediately use these battle-tested agents:

```python
# Code Quality & Maintenance
from agents.code_review_agent import CodeReviewAgent
from agents.issue_processor_agent import IssueProcessorAgent  
from agents.testing_agent import TestingAgent

# Repository Management
from agents.repository_setup_agent import RepositorySetupAgent
from agents.issue_orchestrator_agent import IssueOrchestratorAgent

# System Migration & Improvement
from agents.uv_migration_agent import UvMigrationAgent
from agents.component_migration_agent import ComponentMigrationAgent

# Workflow Processing
from agents.issue_processor_agent import IssueProcessorAgent
from agents.prompt_management_agent import PromptManagementAgent

# System Infrastructure  
from agents.event_system_agent import EventSystemAgent
```

### Usage Examples

#### pin-citer Integration
```python
# pin_citer/agents/citation_workflow_agent.py
from ..agents.core.agent import BaseAgent
from ..agents.agents.code_review_agent import CodeReviewAgent

class CitationWorkflowAgent(BaseAgent):
    """pin-citer specific workflow using shared infrastructure"""
    
    def __init__(self):
        super().__init__()
        self.code_reviewer = CodeReviewAgent()  # Shared agent
        
    def review_citation_code(self, code_path):
        # Use shared code review capabilities
        return self.code_reviewer.execute_task(f"review {code_path}")
```

#### zothein Integration
```python
# zothein/research_pipeline.py  
from ..agents.core.agent import BaseAgent
from ..agents.agents.testing_agent import TestingAgent

class ResearchPipelineAgent(BaseAgent):
    """Research workflow with shared testing"""
    
    def validate_research_pipeline(self):
        tester = TestingAgent()
        return tester.execute_task("run comprehensive tests")
```

## Shared State Management

### Cross-Repository State
All repos can share state through the centralized system:

```python
# Any repository can access shared state
from .agents.core.state import UnifiedState

# Global state shared across all projects
global_state = UnifiedState(scope="global")
global_state.set("last_successful_build", datetime.now())

# Project-specific state
project_state = UnifiedState(scope="pin-citer") 
project_state.set("citation_cache", citation_data)
```

### State Directory Structure
```
~/.claude-shared-state/
├── global/                     # Shared across all repos
├── by-repo/
│   ├── pin-citer/             # pin-citer specific state
│   ├── zothein/               # zothein specific state
│   └── cite-assist/           # cite-assist specific state
├── locks/                     # Cross-repo coordination
└── events/                    # Shared event system
```

## Shared Prompt Library

### Centralized Prompt Management
```python
# All repos use same prompt system
from .agents.core.prompt_manager import PromptManager

pm = PromptManager()

# Use shared prompts
code_review_prompt = pm.get_prompt("base/code_review", 
                                  language="python", 
                                  complexity="high")

# Add repo-specific prompts  
pm.add_prompt("pin-citer/citation_analysis", custom_prompt)
```

### Prompt Sharing Structure
```
12-factor-agents/prompts/
├── base/                      # Shared by all repos
│   ├── code_review.prompt
│   ├── error_handling.prompt  
│   └── system.prompt
├── specialized/               # Domain-specific shared prompts
│   ├── research.prompt        # For research repos
│   ├── citation.prompt        # For citation repos
│   └── testing.prompt         # For testing workflows
└── repo-specific/             # Project customizations
    ├── pin-citer/
    ├── zothein/ 
    └── cite-assist/
```

## Event System Integration

### Cross-Repository Events
Repositories can communicate through shared events:

```python
# pin-citer triggers event
from .agents.core.triggers import LocalEventSystem

event_system = LocalEventSystem()
event_system.emit("citation_completed", {
    "repo": "pin-citer",
    "document_id": doc_id,
    "citation_count": count
})

# zothein listens for events
@event_system.on("citation_completed")
def handle_citation_completion(event_data):
    # Update research database with citations
    pass
```

## Repository-Specific Customization

### Custom Agents
Each repo can create domain-specific agents while using shared infrastructure:

```python
# pin_citer/agents/bluebook_citation_agent.py
from ...agents.core.agent import BaseAgent

class BluebookCitationAgent(BaseAgent):
    """pin-citer specific agent for legal citations"""
    
    def __init__(self):
        super().__init__()
        # Use shared prompt system for domain-specific prompts
        self.prompt_manager.load_domain_prompts("legal-citations")
```

### Domain-Specific Extensions
```python  
# zothein/agents/research_analysis_agent.py
from ...agents.core.agent import BaseAgent
from ...agents.agents.code_review_agent import CodeReviewAgent

class ResearchAnalysisAgent(BaseAgent):
    """Extends shared agents with research-specific capabilities"""
    
    def __init__(self):
        super().__init__()
        self.code_reviewer = CodeReviewAgent()
        
    def analyze_research_code(self, code):
        # Combine shared code review with research-specific analysis
        base_review = self.code_reviewer.execute_task(f"review {code}")
        research_analysis = self._analyze_research_patterns(code)
        return self._merge_analyses(base_review, research_analysis)
```

## CLI Integration

### Shared CLI Commands
All repositories can use shared CLI tools:

```bash
# From any repository with 12-factor-agents linked
uv run agent list                          # List available agents
uv run agent run CodeReviewAgent "review" # Run code review
uv run agent orchestrate pipeline-name     # Run orchestration pipeline
```

### Repository-Specific CLI
```bash  
# pin-citer specific commands
uv run agent run BluebookCitationAgent "analyze citations"
uv run agent orchestrate citation-workflow

# zothein specific commands  
uv run agent run ResearchAnalysisAgent "analyze research"
uv run agent orchestrate research-workflow
```

## Setup Instructions

### Quick Setup for Any Repository

1. **Navigate to your repository**:
   ```bash
   cd /Users/dbraman/Documents/GitHub/your-repo
   ```

2. **Create symlink to agents**:
   ```bash
   ln -s ../12-factor-agents/core .agents/core
   ln -s ../12-factor-agents/agents .agents/agents
   ```

3. **Test integration**:
   ```python
   # test_agent_integration.py
   import sys
   sys.path.insert(0, '.agents')
   
   from core.agent import BaseAgent
   from agents.code_review_agent import CodeReviewAgent
   
   # Test basic functionality
   reviewer = CodeReviewAgent()
   result = reviewer.execute_task("review README.md")
   print(f"Integration successful: {result.success}")
   ```

4. **Add to .gitignore**:
   ```bash
   echo ".agents/" >> .gitignore  # If using symlinks
   ```

## Benefits of Shared Architecture

### For Development
- ✅ **Code Reuse**: Write once, use everywhere
- ✅ **Consistency**: Same patterns across all projects  
- ✅ **Testing**: Shared test infrastructure
- ✅ **Maintenance**: Single codebase for agent improvements

### For Production
- ✅ **Reliability**: Battle-tested agents across projects
- ✅ **Monitoring**: Centralized agent health tracking
- ✅ **Updates**: Framework improvements benefit all repos
- ✅ **Documentation**: Single source of truth

### For Collaboration
- ✅ **Knowledge Sharing**: Agents capture domain expertise
- ✅ **Cross-Project Learning**: Patterns spread between teams
- ✅ **Reduced Duplication**: No reimplementing common functionality
- ✅ **Faster Development**: Focus on business logic, not infrastructure

## Next Steps

1. **Choose Integration Method**: Symlink recommended for development
2. **Test Integration**: Run setup in one repository first  
3. **Migrate Existing Agents**: Move repo-specific agents to shared framework
4. **Document Domain Patterns**: Capture repository-specific knowledge
5. **Set Up Monitoring**: Track agent usage across repositories

The 12-factor-agents framework is ready to serve as your **central agent hub** for all GitHub repositories! 🚀

---
*Multi-repository agent sharing enables unprecedented code reuse and consistency across your entire development ecosystem.*