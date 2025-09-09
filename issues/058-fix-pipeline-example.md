# Issue #058: Fix Pipeline Architecture example in Integration Guide

## Description
The Pipeline Architecture example in the Integration Guide (lines 69-81) has errors.

## Problem
The example shows:
```python
pipeline = MultiStagePipeline()
pipeline.add_stage(ProcessingStage())
```

But this fails with:
```
AttributeError: 'MultiStagePipeline' object has no attribute 'stages'
```

## Solution Needed
- Fix the Pipeline example to show correct initialization
- Add a working example that users can copy and run
- Test all examples before documenting

## Location
/docs/INTEGRATION-GUIDE.md lines 69-81

## Type
documentation

## Priority
high

## Status
open