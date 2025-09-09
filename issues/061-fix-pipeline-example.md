# Issue #061: Fix Pipeline Example in Integration Guide

## Description
The pipeline example in INTEGRATION-GUIDE.md has a critical bug that prevents execution.

## Problem
```python
# Current broken code:
pipeline = MultiStagePipeline()
```
This fails with AttributeError: 'MultiStagePipeline' object has no attribute 'stages'

## Solution
```python
# Fixed code:
pipeline = MultiStagePipeline(stages=[
    CodeReviewAgent(),
    TestingAgent(),
    DeploymentAgent()
])
```

## Implementation
Update `/docs/INTEGRATION-GUIDE.md` section "Using Pipelines" with the corrected initialization.

## Type
bug

## Priority
high

## Status
open

## Assignee
issue_fixer_agent