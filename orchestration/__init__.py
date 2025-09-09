"""
Orchestration package for hierarchical agent coordination.

Provides patterns and utilities for complex task orchestration across
multiple agent levels with intelligent workload distribution.
"""

from .patterns import (
    OrchestrationPattern,
    MapReducePattern,
    PipelinePattern,
    ForkJoinPattern,
    ScatterGatherPattern,
    SagaPattern,
    PatternExecutor,
)

__all__ = [
    "OrchestrationPattern",
    "MapReducePattern",
    "PipelinePattern",
    "ForkJoinPattern",
    "ScatterGatherPattern",
    "SagaPattern",
    "PatternExecutor",
]
