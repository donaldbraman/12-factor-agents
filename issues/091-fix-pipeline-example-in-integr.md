# Issue #091: Fix Pipeline Example in INTEGRATION-GUIDE.md

## Description
Fix Pipeline Example in INTEGRATION-GUIDE.md

## Problem
The current code needs updating to fix functionality.

## Current Code
```
python
self.pipeline = MultiStagePipeline()
self.pipeline.add_stage(ProcessingStage())
```

## Required Change
```  
python
self.pipeline = MultiStagePipeline(stages=[ProcessingStage()])
# Or initialize empty and add stages
self.pipeline = MultiStagePipeline(stages=[])
self.pipeline.add_stage(ProcessingStage())
```

## Actionable Steps (Factor 8: Own Your Control Flow)
1. Locate the target file: self.pipeline
2. Find the current code block
3. Replace with the new implementation
4. Verify the change works correctly

## Definition of Done
- [ ] Code replacement completed
- [ ] No syntax errors
- [ ] Functionality verified

## Files to Update
- self.pipeline

## Parent Issue
064

## Type
bug

## Priority
high

## Status
open

## Assignee
issue_fixer_agent

## Target File
self.pipeline
