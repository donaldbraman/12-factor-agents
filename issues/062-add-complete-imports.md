# Issue #062: Add Complete Imports to Integration Guide Examples

## Description
Multiple code examples in INTEGRATION-GUIDE.md are missing required imports, preventing standalone execution.

## Problems to Fix

### 1. Pipeline Example (Line ~195)
Missing: `import asyncio`

### 2. Event-Driven Example (Line ~238)
Missing: `from core.triggers import LocalEventSystem`

### 3. State Management Example (Line ~265)
Missing: `from core.state import UnifiedState`

## Solution
Add all necessary imports at the beginning of each code block:

```python
# Complete example with all imports
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / ".agents"))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse
from orchestration.pipeline import MultiStagePipeline
from core.triggers import LocalEventSystem
from core.state import UnifiedState
```

## Implementation
Update each code example in `/docs/INTEGRATION-GUIDE.md` to be self-contained with all required imports.

## Type
documentation

## Priority
high

## Status
open

## Assignee
issue_fixer_agent