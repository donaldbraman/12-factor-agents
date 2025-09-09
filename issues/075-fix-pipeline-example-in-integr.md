# Issue #075: Fix Pipeline Example in INTEGRATION-GUIDE.md

## Description
Fix Pipeline Example in INTEGRATION-GUIDE.md

Specific changes needed:
Current broken:
```python
self.pipeline = MultiStagePipeline()
self.pipeline.add_stage(ProcessingStage())
```

Should be:
```python
self.pipeline = MultiStagePipeline(stages=[ProcessingStage()])
# Or initialize empty and add stages
self.pipeline = MultiStagePipeline(stages=[])
self.pipeline.add_stage(ProcessingStage())
```

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
