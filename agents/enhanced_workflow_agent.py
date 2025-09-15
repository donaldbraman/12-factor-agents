"""
Enhanced Workflow Agent
Demonstrates pin-citer inspired patterns integrated with 12-factor methodology.

This agent showcases:
- Advanced checkpoint system with progress tracking
- Multi-stage pipeline architecture
- Progress-aware orchestration
- Enhanced error handling and recovery
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from core.agent import BaseAgent
from core.pipeline import MultiStagePipeline, PipelineStage, PipelineDecision
from core.orchestrator import ProgressAwareOrchestrator, WorkflowPhase
from core.tools import Tool, ToolResponse
from core.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


class DocumentAnalysisStage(PipelineStage):
    """
    Document analysis stage inspired by pin-citer's deterministic filtering.
    Demonstrates Factor 10: Small, focused agents.
    """

    def __init__(self):
        super().__init__("document_analysis", 1)
        self.supported_formats = [".txt", ".md", ".py", ".js", ".json"]

    async def process_async(
        self, data: Any, context: Optional[Dict] = None
    ) -> tuple[Any, Dict]:
        """Analyze document for processability"""
        file_path = Path(str(data))

        metadata = {
            "confidence": 0.95,
            "method": "document_analysis",
            "file_exists": file_path.exists(),
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "file_extension": file_path.suffix,
        }

        # Check if file exists and is supported format
        if not file_path.exists():
            metadata["reason"] = f"File does not exist: {file_path}"
            metadata["decision"] = "SKIP"
            return "SKIP", metadata

        if file_path.suffix not in self.supported_formats:
            metadata["reason"] = f"Unsupported format: {file_path.suffix}"
            metadata["decision"] = "SKIP"
            return "SKIP", metadata

        # File is processable
        metadata["reason"] = f"File ready for processing: {file_path.name}"
        metadata["decision"] = "PROCESS"
        return "PROCESS", metadata

    def should_exit(self, result: Any, metadata: Dict) -> bool:
        """Exit early for files that should be skipped"""
        return result == "SKIP"


class ContentExtractionStage(PipelineStage):
    """
    Content extraction stage.
    Demonstrates sophisticated error handling with context preservation.
    """

    def __init__(self):
        super().__init__("content_extraction", 2)

    async def process_async(
        self, data: Any, context: Optional[Dict] = None
    ) -> tuple[Any, Dict]:
        """Extract content from file"""
        file_path = Path(str(data))

        metadata = {
            "confidence": 0.9,
            "method": "content_extraction",
            "lines_extracted": 0,
            "encoding": "utf-8",
        }

        try:
            # Read file content
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            metadata.update(
                {
                    "lines_extracted": len(lines),
                    "characters": len(content),
                    "reason": f"Successfully extracted {len(lines)} lines",
                }
            )

            return {
                "file_path": str(file_path),
                "content": content,
                "lines": lines,
                "metadata": metadata,
            }, metadata

        except UnicodeDecodeError:
            # Try different encoding
            try:
                content = file_path.read_text(encoding="latin-1")
                metadata["encoding"] = "latin-1"
                metadata["reason"] = "Extracted with latin-1 encoding"
                return {"file_path": str(file_path), "content": content}, metadata
            except Exception as e:
                metadata["reason"] = f"Encoding error: {str(e)}"
                raise

        except Exception as e:
            metadata["reason"] = f"Extraction failed: {str(e)}"
            raise

    def should_exit(self, result: Any, metadata: Dict) -> bool:
        """Continue to next stage for further processing"""
        return False


class QualityAssuranceStage(PipelineStage):
    """
    Quality assurance stage.
    Demonstrates pin-citer's quality control patterns.
    """

    def __init__(self):
        super().__init__("quality_assurance", 3)
        self.min_content_length = 10
        self.max_content_length = 1_000_000

    async def process_async(
        self, data: Any, context: Optional[Dict] = None
    ) -> tuple[Any, Dict]:
        """Validate content quality"""
        content_data = data
        content = content_data.get("content", "")

        metadata = {
            "confidence": 0.85,
            "method": "quality_assurance",
            "quality_score": 0.0,
            "issues": [],
        }

        quality_score = 1.0
        issues = []

        # Check content length
        if len(content) < self.min_content_length:
            issues.append("Content too short")
            quality_score -= 0.3
        elif len(content) > self.max_content_length:
            issues.append("Content too long")
            quality_score -= 0.2

        # Check for basic structure
        lines = content_data.get("lines", [])
        if not lines:
            issues.append("No content lines")
            quality_score -= 0.5

        # Check for suspicious content patterns
        suspicious_patterns = ["<?php", "<script>", "eval("]
        for pattern in suspicious_patterns:
            if pattern in content.lower():
                issues.append(f"Suspicious pattern detected: {pattern}")
                quality_score -= 0.4

        metadata.update(
            {
                "quality_score": max(0.0, quality_score),
                "issues": issues,
                "reason": f"Quality score: {quality_score:.2f}, Issues: {len(issues)}",
            }
        )

        # Add quality metrics to content data
        content_data["quality"] = {
            "score": quality_score,
            "issues": issues,
            "passed": quality_score >= 0.6,
        }

        return content_data, metadata

    def should_exit(self, result: Any, metadata: Dict) -> bool:
        """Exit if quality is too low"""
        quality_score = metadata.get("quality_score", 0.0)
        return quality_score < 0.3


class EnhancedWorkflowAgent(BaseAgent):
    """
    Enhanced workflow agent demonstrating pin-citer inspired patterns.

    Features:
    - Multi-stage pipeline processing
    - Progress-aware orchestration
    - Enhanced checkpoint system
    - Sophisticated error handling
    - Git context tracking
    """

    def __init__(self, agent_id: str = None):
        super().__init__(agent_id)

        # Set up multi-stage pipeline
        self.pipeline = MultiStagePipeline(f"{self.agent_id}_pipeline")
        self.pipeline.add_stage(DocumentAnalysisStage())
        self.pipeline.add_stage(ContentExtractionStage())
        self.pipeline.add_stage(QualityAssuranceStage())

        # Set up workflow orchestrator
        self.orchestrator = ProgressAwareOrchestrator(
            f"enhanced_workflow_{self.agent_id}"
        )

        # Register custom phase processors
        self.orchestrator.register_phase_processor(
            WorkflowPhase.ANALYSIS, self._analysis_phase
        )
        self.orchestrator.register_phase_processor(
            WorkflowPhase.PROCESSING, self._processing_phase
        )

        # Set up workflow stages for progress tracking
        self.set_workflow_stages(
            [
                "initialization",
                "file_discovery",
                "pipeline_processing",
                "quality_validation",
                "result_compilation",
            ]
        )

        logger.info(
            f"EnhancedWorkflowAgent initialized with {len(self.pipeline.stages)} pipeline stages"
        )

    def register_tools(self) -> List[Tool]:
        """Register agent-specific tools"""
        return [
            Tool(
                name="process_files",
                description="Process files through enhanced pipeline",
                parameters={"file_paths": "list", "options": "dict"},
            ),
            Tool(
                name="get_processing_stats",
                description="Get detailed processing statistics",
                parameters={},
            ),
            Tool(
                name="retry_failed_items",
                description="Retry processing of failed items",
                parameters={"error_threshold": "float"},
            ),
        ]

    async def _analysis_phase(self, workflow_data: Dict):
        """Custom analysis phase implementing pin-citer patterns"""
        logger.info("Starting analysis phase with enhanced patterns")

        # Discover files to process
        self.set_progress(0.2, "file_discovery")
        file_paths = workflow_data.get("file_paths", [])

        if not file_paths:
            # Auto-discover files in current directory
            file_paths = list(Path(".").glob("**/*.py"))[:10]  # Limit for demo

        workflow_data["discovered_files"] = [str(p) for p in file_paths]

        # Analyze file characteristics
        self.set_progress(0.25, "file_analysis")
        file_stats = {}
        for file_path in file_paths:
            path_obj = Path(file_path)
            if path_obj.exists():
                file_stats[file_path] = {
                    "size": path_obj.stat().st_size,
                    "extension": path_obj.suffix,
                    "exists": True,
                }
            else:
                file_stats[file_path] = {"exists": False}

        workflow_data["file_stats"] = file_stats
        self.set_progress(0.3, "analysis_completed")

        logger.info(f"Analysis phase completed. Discovered {len(file_paths)} files")

    async def _processing_phase(self, workflow_data: Dict):
        """Custom processing phase using multi-stage pipeline"""
        logger.info("Starting processing phase with pipeline")

        file_paths = workflow_data.get("discovered_files", [])
        if not file_paths:
            workflow_data["processing_results"] = []
            return

        self.set_progress(0.5, "pipeline_processing")

        # Process files through pipeline
        results = await self.pipeline.process_batch_async(file_paths)

        # Analyze results
        successful = [r for r in results if r[0] != PipelineDecision.EXIT_FAILURE]
        failed = [r for r in results if r[0] == PipelineDecision.EXIT_FAILURE]

        workflow_data["processing_results"] = {
            "total_processed": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) if results else 0.0,
            "detailed_results": [metadata for _, metadata in results],
        }

        # Track files that were processed
        for file_path in file_paths:
            self.add_file_modified(file_path)

        self.set_progress(0.7, "processing_completed")

        logger.info(
            f"Processing completed. {len(successful)}/{len(results)} successful"
        )

    def execute_task(
        self, task: str, context: Optional[ExecutionContext] = None
    ) -> ToolResponse:
        """
        Execute enhanced workflow task.
        Demonstrates comprehensive pin-citer patterns.
        """
        try:
            # Parse task parameters
            task_params = self._parse_task_parameters(task)

            # Set Git context if available
            if "branch" in task_params:
                self.set_git_context(branch=task_params["branch"])
            if "issue_number" in task_params:
                self.set_git_context(issue_number=task_params["issue_number"])

            # Start orchestrated workflow
            self.set_progress(0.0, "initialization")

            result = asyncio.run(self.orchestrator.start_workflow_async(task_params))

            # Enhanced result with comprehensive metadata
            if result.success:
                self.set_progress(1.0, "completed")

                enhanced_data = {
                    **result.data,
                    "agent_stats": self.get_status(),
                    "pipeline_stats": self.pipeline.get_pipeline_stats(),
                    "checkpoint_info": {
                        "checkpoint_path": str(self.checkpoint_path),
                        "last_checkpoint": self.workflow_data.get("last_checkpoint"),
                    },
                }

                return ToolResponse(
                    success=True,
                    data=enhanced_data,
                    metadata={
                        "agent_id": self.agent_id,
                        "execution_pattern": "pin_citer_inspired",
                        "twelve_factor_compliance": True,
                    },
                )
            else:
                # Handle failure with enhanced error context
                self.handle_error(
                    Exception(result.error or "Workflow execution failed"),
                    "enhanced_workflow",
                )
                return result

        except Exception as e:
            self.handle_error(e, "task_execution")
            return ToolResponse(
                success=False,
                error=str(e),
                metadata={
                    "agent_id": self.agent_id,
                    "error_context": self.error_context,
                },
            )

    def _parse_task_parameters(self, task: str) -> Dict[str, Any]:
        """Parse task string to extract parameters"""
        # Simple implementation - can be enhanced based on needs
        params = {"task_description": task}

        # Extract file paths if mentioned
        lines = task.split("\n")
        file_paths = []
        for line in lines:
            line = line.strip()
            if line.endswith(".py") or line.endswith(".js") or line.endswith(".md"):
                file_paths.append(line)

        if file_paths:
            params["file_paths"] = file_paths

        return params

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply action with enhanced error handling"""
        try:
            action_type = action.get("type", "unknown")

            if action_type == "retry_failed":
                # Retry failed pipeline items
                threshold = action.get("error_threshold", 0.5)
                # Implementation would retry based on checkpoint data
                return ToolResponse(success=True, data={"retried": 0})

            elif action_type == "get_stats":
                return ToolResponse(
                    success=True,
                    data={
                        "agent_stats": self.get_status(),
                        "pipeline_stats": self.pipeline.get_pipeline_stats(),
                    },
                )

            else:
                return ToolResponse(
                    success=False, error=f"Unknown action type: {action_type}"
                )

        except Exception as e:
            self.handle_error(e, f"action_{action_type}")
            return ToolResponse(success=False, error=str(e))

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status demonstrating pin-citer patterns.
        Shows enhanced checkpoint data, progress tracking, and error context.
        """
        status = self.get_status()

        # Add pipeline information
        if hasattr(self, "pipeline"):
            status["pipeline_stats"] = self.pipeline.get_pipeline_stats()

        # Add orchestrator information
        if hasattr(self, "orchestrator"):
            status["orchestrator_status"] = self.orchestrator.get_workflow_status()

        # Add pin-citer inspired metadata
        status["pin_citer_patterns"] = {
            "advanced_checkpointing": True,
            "progress_tracking": self.progress,
            "multi_stage_pipeline": len(getattr(self, "pipeline", {}).stages or []),
            "error_context_preservation": bool(self.error_context),
            "workflow_specific_data": bool(self.workflow_data),
            "git_context_tracking": {
                "branch": self.branch,
                "issue_number": self.issue_number,
            },
        }

        return status


# Example usage and testing
async def demo_enhanced_workflow():
    """Demonstrate enhanced workflow agent with pin-citer patterns"""
    agent = EnhancedWorkflowAgent()

    # Simulate a complex workflow
    task = """
    Process the following files:
    ./core/agent.py
    ./core/pipeline.py
    ./core/orchestrator.py
    
    branch: feature/pin-citer-integration
    issue_number: 14
    """

    print("Starting enhanced workflow demonstration...")
    result = agent.execute_task(task)

    print(f"Workflow completed: {result.success}")
    print(f"Agent Status: {agent.get_comprehensive_status()}")

    return result


if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_enhanced_workflow())
