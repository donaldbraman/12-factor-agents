"""
Multi-Stage Pipeline Framework
Inspired by pin-citer's sophisticated 4-stage cascade architecture.
Implements 12-factor agent principles with complex workflow support.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from .agent import BaseAgent
from .tools import ToolResponse

logger = logging.getLogger(__name__)


class PipelineStage(ABC):
    """
    Abstract base class for pipeline stages.
    Factor 10: Small, focused agents - each stage has single responsibility.
    """
    
    def __init__(self, stage_name: str, stage_id: int):
        self.stage_name = stage_name
        self.stage_id = stage_id
        self.stats = {"processed": 0, "exits": 0, "errors": 0}
    
    @abstractmethod
    async def process_async(self, data: Any, context: Optional[Dict] = None) -> Tuple[Any, Dict]:
        """
        Process data through this stage.
        
        Returns:
            Tuple of (result, metadata)
        """
        pass
    
    @abstractmethod
    def should_exit(self, result: Any, metadata: Dict) -> bool:
        """
        Determine if pipeline should exit after this stage.
        Factor 8: Own your control flow.
        """
        pass
    
    def get_stats(self) -> Dict[str, int]:
        """Get stage processing statistics"""
        return self.stats.copy()


class PipelineDecision(Enum):
    """Pipeline decision outcomes"""
    CONTINUE = "continue"
    EXIT_SUCCESS = "exit_success" 
    EXIT_FAILURE = "exit_failure"
    RETRY_STAGE = "retry_stage"


class MultiStagePipeline(BaseAgent):
    """
    Multi-stage pipeline agent implementing pin-citer's cascade pattern.
    
    Key features from pin-citer analysis:
    - Stage-specific early exits for efficiency
    - Comprehensive metadata tracking
    - Progress-aware orchestration
    - Error context preservation
    """
    
    def __init__(self, agent_id: str = None):
        super().__init__(agent_id)
        self.stages: List[PipelineStage] = []
        self.pipeline_stats = {
            "total_processed": 0,
            "stage_exits": {},
            "processing_times": {}
        }
        
    def register_tools(self) -> List:
        """Pipeline uses tools from individual stages"""
        tools = []
        for stage in self.stages:
            if hasattr(stage, 'register_tools'):
                tools.extend(stage.register_tools())
        return tools
    
    def add_stage(self, stage: PipelineStage):
        """Add stage to pipeline"""
        self.stages.append(stage)
        self.pipeline_stats["stage_exits"][stage.stage_name] = 0
        self.pipeline_stats["processing_times"][stage.stage_name] = []
        
        # Update total stages for progress tracking
        self.total_stages = len(self.stages)
        stage_names = [s.stage_name for s in self.stages]
        self.set_workflow_stages(stage_names)
    
    async def process_item_async(
        self,
        item: Any,
        context: Optional[Dict] = None,
        item_index: int = 0
    ) -> Tuple[PipelineDecision, Dict]:
        """
        Process single item through complete pipeline.
        Implements pin-citer's sophisticated cascade logic.
        """
        start_time = time.time()
        metadata = {
            "item_index": item_index,
            "stages_used": [],
            "processing_time_ms": 0,
            "decision": None,
            "stage_metadata": {}
        }
        
        self.pipeline_stats["total_processed"] += 1
        current_data = item
        
        # Process through each stage
        for stage in self.stages:
            stage_start = time.time()
            
            try:
                # Update progress
                self.set_progress(
                    stage.stage_id / len(self.stages),
                    stage.stage_name
                )
                
                # Process through stage
                result, stage_meta = await stage.process_async(current_data, context)
                
                # Track statistics
                stage.stats["processed"] += 1
                metadata["stages_used"].append(stage.stage_id)
                metadata["stage_metadata"][stage.stage_name] = stage_meta
                
                # Record processing time
                stage_time = (time.time() - stage_start) * 1000
                self.pipeline_stats["processing_times"][stage.stage_name].append(stage_time)
                
                # Check for early exit (pin-citer efficiency pattern)
                if stage.should_exit(result, stage_meta):
                    stage.stats["exits"] += 1
                    self.pipeline_stats["stage_exits"][stage.stage_name] += 1
                    
                    metadata["decision"] = PipelineDecision.EXIT_SUCCESS
                    metadata["exit_stage"] = stage.stage_name
                    metadata["exit_reason"] = stage_meta.get("reason", "Stage determined exit")
                    break
                
                # Update data for next stage
                current_data = result
                
            except Exception as e:
                # Enhanced error handling (pin-citer pattern)
                stage.stats["errors"] += 1
                self.handle_error(e, f"Stage {stage.stage_name}")
                
                metadata["decision"] = PipelineDecision.EXIT_FAILURE
                metadata["error_stage"] = stage.stage_name
                metadata["error"] = str(e)
                break
        
        # If no early exit, pipeline completed successfully
        if metadata["decision"] is None:
            metadata["decision"] = PipelineDecision.CONTINUE
            self.set_progress(1.0, "completed")
        
        metadata["processing_time_ms"] = (time.time() - start_time) * 1000
        metadata["final_result"] = current_data
        
        return metadata["decision"], metadata
    
    def process_item(
        self,
        item: Any,
        context: Optional[Dict] = None,
        item_index: int = 0
    ) -> Tuple[PipelineDecision, Dict]:
        """Synchronous wrapper for process_item_async"""
        return asyncio.run(self.process_item_async(item, context, item_index))
    
    async def process_batch_async(self, items: List[Any]) -> List[Tuple[PipelineDecision, Dict]]:
        """
        Process batch of items through pipeline.
        Implements context tracking between items (pin-citer pattern).
        """
        results = []
        context = {}
        
        for i, item in enumerate(items):
            # Build contextual information
            if i > 0:
                # Add previous item context
                prev_result = results[-1]
                context["previous_result"] = prev_result[1].get("final_result")
                context["previous_decision"] = prev_result[0]
            
            if i < len(items) - 1:
                context["next_item"] = items[i + 1]
            
            # Process item
            decision, metadata = await self.process_item_async(item, context, i)
            results.append((decision, metadata))
            
            # Small delay to avoid overwhelming downstream systems
            if len(self.stages) > 1:
                await asyncio.sleep(0.05)
        
        return results
    
    def execute_task(self, task: str) -> ToolResponse:
        """
        Execute pipeline task.
        Factor 10: Single responsibility - pipeline orchestration.
        """
        try:
            # Parse task to extract items to process
            items = self._parse_task_to_items(task)
            
            if not items:
                return ToolResponse(
                    success=False,
                    error="No items to process in task",
                    metadata={"agent_id": self.agent_id}
                )
            
            # Process all items
            results = asyncio.run(self.process_batch_async(items))
            
            # Aggregate results
            success_count = sum(1 for decision, _ in results 
                              if decision != PipelineDecision.EXIT_FAILURE)
            
            return ToolResponse(
                success=success_count > 0,
                data={
                    "processed_count": len(results),
                    "success_count": success_count,
                    "results": [metadata for _, metadata in results]
                },
                metadata={
                    "agent_id": self.agent_id,
                    "pipeline_stats": self.get_pipeline_stats()
                }
            )
            
        except Exception as e:
            self.handle_error(e, "pipeline_execution")
            return ToolResponse(
                success=False,
                error=str(e),
                metadata={"agent_id": self.agent_id}
            )
    
    def _parse_task_to_items(self, task: str) -> List[Any]:
        """
        Parse task string to items for processing.
        Override in subclasses for domain-specific parsing.
        """
        # Default implementation - split by lines
        return [line.strip() for line in task.split('\n') if line.strip()]
    
    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply action to pipeline state"""
        action_type = action.get("type", "unknown")
        
        if action_type == "add_stage":
            stage_data = action.get("stage_data", {})
            # This would be implemented based on specific stage types
            return ToolResponse(success=True, data={"action": "stage_added"})
        
        elif action_type == "reset_stats":
            self.reset_pipeline_stats()
            return ToolResponse(success=True, data={"action": "stats_reset"})
        
        else:
            return ToolResponse(
                success=False,
                error=f"Unknown action type: {action_type}"
            )
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics (pin-citer pattern)"""
        stats = self.pipeline_stats.copy()
        
        # Add stage-specific stats
        stats["stage_stats"] = {}
        for stage in self.stages:
            stage_stats = stage.get_stats()
            # Add average processing time
            times = self.pipeline_stats["processing_times"][stage.stage_name]
            stage_stats["avg_processing_time_ms"] = sum(times) / len(times) if times else 0
            stats["stage_stats"][stage.stage_name] = stage_stats
        
        # Calculate efficiency metrics
        total = stats["total_processed"]
        if total > 0:
            stats["exit_efficiency"] = {}
            for stage_name, exits in stats["stage_exits"].items():
                stats["exit_efficiency"][stage_name] = (exits / total) * 100
        
        return stats
    
    def reset_pipeline_stats(self):
        """Reset all pipeline statistics"""
        self.pipeline_stats["total_processed"] = 0
        
        for stage in self.stages:
            stage.stats = {"processed": 0, "exits": 0, "errors": 0}
            self.pipeline_stats["stage_exits"][stage.stage_name] = 0
            self.pipeline_stats["processing_times"][stage.stage_name] = []
        
        logger.info(f"Pipeline statistics reset for {self.agent_id}")


# Example stage implementations inspired by pin-citer's stages
class DeterministicFilterStage(PipelineStage):
    """
    Example deterministic filtering stage.
    Based on pin-citer's Stage 1 pattern.
    """
    
    def __init__(self):
        super().__init__("deterministic_filter", 1)
        self.patterns = {
            "skip": ["skip", "ignore", "pass"],
            "process": ["analyze", "review", "check"]
        }
    
    async def process_async(self, data: Any, context: Optional[Dict] = None) -> Tuple[Any, Dict]:
        """Apply deterministic rules to filter data"""
        data_str = str(data).lower()
        
        metadata = {
            "confidence": 1.0,
            "method": "deterministic",
            "matched_patterns": []
        }
        
        # Check skip patterns
        for pattern in self.patterns["skip"]:
            if pattern in data_str:
                metadata["matched_patterns"].append(f"skip:{pattern}")
                metadata["reason"] = f"Skip pattern matched: {pattern}"
                return "SKIP", metadata
        
        # Check process patterns  
        for pattern in self.patterns["process"]:
            if pattern in data_str:
                metadata["matched_patterns"].append(f"process:{pattern}")
                metadata["reason"] = f"Process pattern matched: {pattern}"
                return "PROCESS", metadata
        
        # Default to uncertain
        metadata["reason"] = "No deterministic patterns matched"
        return "UNCERTAIN", metadata
    
    def should_exit(self, result: Any, metadata: Dict) -> bool:
        """Exit early for definitive decisions"""
        return result in ["SKIP", "PROCESS"]


class ClassificationStage(PipelineStage):
    """
    Example classification stage.
    Based on pin-citer's Stage 2 taxonomic classification pattern.
    """
    
    def __init__(self):
        super().__init__("classification", 2)
    
    async def process_async(self, data: Any, context: Optional[Dict] = None) -> Tuple[Any, Dict]:
        """Classify data using contextual analysis"""
        # Simplified classification logic
        data_str = str(data)
        
        metadata = {
            "confidence": 0.8,
            "method": "classification",
            "context_used": bool(context)
        }
        
        # Simple heuristic classification
        if len(data_str) < 10:
            classification = "SHORT"
            metadata["reason"] = "Short content classification"
        elif "error" in data_str.lower():
            classification = "ERROR"
            metadata["reason"] = "Error content detected"
        else:
            classification = "STANDARD"
            metadata["reason"] = "Standard content classification"
        
        return classification, metadata
    
    def should_exit(self, result: Any, metadata: Dict) -> bool:
        """Continue to next stage for further analysis"""
        return False