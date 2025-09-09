"""
Progress-Aware Workflow Orchestrator
Inspired by pin-citer's sophisticated workflow orchestration system.
Implements 12-factor agent principles with granular progress tracking.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Callable, Any

from .agent import BaseAgent
from .tools import ToolResponse

logger = logging.getLogger(__name__)


class WorkflowPhase(Enum):
    """
    Workflow phases based on pin-citer's orchestration pattern.
    Each phase has specific progress milestones.
    """

    INITIALIZATION = ("initialization", 0.1)
    ANALYSIS = ("analysis", 0.3)
    PROCESSING = ("processing", 0.6)
    APPROVAL = ("approval", 0.8)
    FINALIZATION = ("finalization", 1.0)

    def __init__(self, phase_name: str, progress_milestone: float):
        self.phase_name = phase_name
        self.progress_milestone = progress_milestone


class WorkflowStatus(Enum):
    """Workflow execution status"""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProgressAwareOrchestrator(BaseAgent):
    """
    Orchestrator implementing pin-citer's progress-aware workflow patterns.

    Key features learned from pin-citer:
    - Granular progress tracking (0.2, 0.5, 0.7, 0.9, 1.0)
    - Phase-based workflow execution
    - Comprehensive checkpoint persistence
    - Human-in-the-loop approval points
    - Error recovery with context preservation
    """

    def __init__(self, workflow_name: str = "generic_workflow", agent_id: str = None):
        super().__init__(agent_id)
        self.workflow_name = workflow_name
        self.workflow_status = WorkflowStatus.PENDING
        self.current_phase = WorkflowPhase.INITIALIZATION
        self.phases_completed = []

        # Workflow configuration
        self.approval_required_phases = [
            WorkflowPhase.PROCESSING,
            WorkflowPhase.FINALIZATION,
        ]
        self.approval_callbacks: Dict[WorkflowPhase, Callable] = {}
        self.phase_processors: Dict[WorkflowPhase, Callable] = {}

        # Progress tracking (pin-citer pattern)
        self.workflow_data.update(
            {
                "workflow_name": workflow_name,
                "start_time": None,
                "end_time": None,
                "phase_durations": {},
                "approval_history": [],
            }
        )

        # Set up default phase progression
        phase_names = [phase.phase_name for phase in WorkflowPhase]
        self.set_workflow_stages(phase_names)

        logger.info(f"ProgressAwareOrchestrator initialized: {workflow_name}")

    def register_tools(self) -> List:
        """Orchestrator tools for workflow management"""
        from .tools import Tool

        return [
            Tool(
                name="start_workflow",
                description="Start workflow execution",
                parameters={"workflow_data": "dict"},
            ),
            Tool(
                name="pause_workflow",
                description="Pause workflow at current phase",
                parameters={},
            ),
            Tool(
                name="resume_workflow",
                description="Resume paused workflow",
                parameters={},
            ),
            Tool(
                name="approve_phase",
                description="Approve workflow phase for continuation",
                parameters={"phase": "str", "approved": "bool", "comments": "str"},
            ),
            Tool(
                name="get_workflow_status",
                description="Get current workflow status and progress",
                parameters={},
            ),
        ]

    def register_phase_processor(self, phase: WorkflowPhase, processor: Callable):
        """Register custom processor for workflow phase"""
        self.phase_processors[phase] = processor
        logger.info(f"Registered processor for phase: {phase.phase_name}")

    def register_approval_callback(self, phase: WorkflowPhase, callback: Callable):
        """Register callback for human approval at phase"""
        self.approval_callbacks[phase] = callback
        logger.info(f"Registered approval callback for phase: {phase.phase_name}")

    async def start_workflow_async(self, initial_data: Dict = None) -> ToolResponse:
        """
        Start workflow execution with progress tracking.
        Implements pin-citer's comprehensive orchestration pattern.
        """
        if self.workflow_status != WorkflowStatus.PENDING:
            return ToolResponse(
                success=False,
                error=f"Workflow already in progress. Current status: {self.workflow_status.value}",
                metadata={"agent_id": self.agent_id},
            )

        try:
            # Initialize workflow
            self.workflow_status = WorkflowStatus.RUNNING
            self.workflow_data["start_time"] = datetime.now().isoformat()
            self.workflow_data["initial_data"] = initial_data or {}

            # Start with initialization phase
            self.current_phase = WorkflowPhase.INITIALIZATION
            self.set_progress(0.0, self.current_phase.phase_name)

            logger.info(f"Starting workflow: {self.workflow_name}")

            # Process through all phases
            for phase in WorkflowPhase:
                if self.workflow_status != WorkflowStatus.RUNNING:
                    break

                await self._process_phase(phase)

                # Check if workflow was paused or failed
                if self.workflow_status in [
                    WorkflowStatus.PAUSED,
                    WorkflowStatus.FAILED,
                ]:
                    break

            # Complete workflow if all phases successful
            if self.workflow_status == WorkflowStatus.RUNNING:
                self.workflow_status = WorkflowStatus.COMPLETED
                self.workflow_data["end_time"] = datetime.now().isoformat()
                self.set_progress(1.0, "completed")

            return ToolResponse(
                success=self.workflow_status == WorkflowStatus.COMPLETED,
                data={
                    "workflow_status": self.workflow_status.value,
                    "phases_completed": [p.phase_name for p in self.phases_completed],
                    "final_progress": self.progress,
                },
                metadata={
                    "agent_id": self.agent_id,
                    "workflow_data": self.workflow_data,
                },
            )

        except Exception as e:
            self.handle_error(e, "workflow_execution")
            self.workflow_status = WorkflowStatus.FAILED
            return ToolResponse(
                success=False, error=str(e), metadata={"agent_id": self.agent_id}
            )

    async def _process_phase(self, phase: WorkflowPhase):
        """
        Process individual workflow phase with progress tracking.
        Pin-citer pattern: granular progress within phases.
        """
        phase_start = datetime.now()

        try:
            logger.info(f"Starting phase: {phase.phase_name}")
            self.current_phase = phase

            # Update progress to phase milestone
            self.set_progress(phase.progress_milestone, phase.phase_name)

            # Check for human approval requirement
            if phase in self.approval_required_phases:
                approval_result = await self._request_approval(phase)
                if not approval_result:
                    self.workflow_status = WorkflowStatus.PAUSED
                    logger.info(
                        f"Workflow paused pending approval for phase: {phase.phase_name}"
                    )
                    return

            # Process phase with custom processor or default
            if phase in self.phase_processors:
                await self.phase_processors[phase](self.workflow_data)
            else:
                await self._default_phase_processor(phase)

            # Mark phase as completed
            self.phases_completed.append(phase)

            # Record phase duration
            duration = (datetime.now() - phase_start).total_seconds()
            self.workflow_data["phase_durations"][phase.phase_name] = duration

            logger.info(f"Completed phase: {phase.phase_name} in {duration:.2f}s")

        except Exception as e:
            self.handle_error(e, f"phase_{phase.phase_name}")
            self.workflow_status = WorkflowStatus.FAILED
            raise

    async def _request_approval(self, phase: WorkflowPhase) -> bool:
        """
        Request human approval for phase continuation.
        Factor 7: Contact humans with tool calls.
        """
        approval_data = {
            "workflow_name": self.workflow_name,
            "phase": phase.phase_name,
            "progress": self.progress,
            "data_summary": self._get_approval_summary(),
            "timestamp": datetime.now().isoformat(),
        }

        # Use callback if registered
        if phase in self.approval_callbacks:
            try:
                result = await self.approval_callbacks[phase](approval_data)
                self.workflow_data["approval_history"].append(
                    {
                        "phase": phase.phase_name,
                        "approved": result,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                return result
            except Exception as e:
                logger.error(f"Approval callback failed for {phase.phase_name}: {e}")
                return False

        # Default: automatic approval (override in subclasses for human approval)
        logger.info(f"Auto-approving phase: {phase.phase_name}")
        return True

    def _get_approval_summary(self) -> Dict[str, Any]:
        """Get summary data for human approval"""
        return {
            "current_phase": self.current_phase.phase_name,
            "progress": self.progress,
            "phases_completed": len(self.phases_completed),
            "files_modified": len(self.files_modified),
            "workflow_duration": self._get_workflow_duration(),
        }

    def _get_workflow_duration(self) -> float:
        """Get workflow duration in seconds"""
        if not self.workflow_data.get("start_time"):
            return 0.0

        start = datetime.fromisoformat(self.workflow_data["start_time"])
        end = datetime.now()
        if self.workflow_data.get("end_time"):
            end = datetime.fromisoformat(self.workflow_data["end_time"])

        return (end - start).total_seconds()

    async def _default_phase_processor(self, phase: WorkflowPhase):
        """Default phase processing logic"""
        logger.info(f"Processing phase: {phase.phase_name} with default processor")

        # Simulate phase work with progress updates
        phase_steps = 5
        for step in range(phase_steps):
            # Simulate work
            await asyncio.sleep(0.1)

            # Update progress within phase
            phase_progress = (step + 1) / phase_steps
            step_progress = phase.progress_milestone + (
                phase_progress * 0.05
            )  # Small increment
            self.set_progress(min(step_progress, phase.progress_milestone))

    def pause_workflow(self) -> ToolResponse:
        """
        Pause workflow execution.
        Factor 6: Simple pause API with state persistence.
        """
        if self.workflow_status != WorkflowStatus.RUNNING:
            return ToolResponse(
                success=False,
                error=f"Cannot pause workflow in status: {self.workflow_status.value}",
            )

        self.workflow_status = WorkflowStatus.PAUSED
        self.status = "paused"
        self.save_checkpoint()

        logger.info(f"Workflow paused at phase: {self.current_phase.phase_name}")

        return ToolResponse(
            success=True,
            data={
                "status": "paused",
                "current_phase": self.current_phase.phase_name,
                "progress": self.progress,
            },
        )

    def resume_workflow(self) -> ToolResponse:
        """
        Resume paused workflow.
        Factor 6: Simple resume API with state restoration.
        """
        if self.workflow_status != WorkflowStatus.PAUSED:
            return ToolResponse(
                success=False,
                error=f"Cannot resume workflow in status: {self.workflow_status.value}",
            )

        # Load checkpoint and resume
        if self.load_checkpoint():
            self.workflow_status = WorkflowStatus.RUNNING
            self.status = "running"

            logger.info(f"Workflow resumed at phase: {self.current_phase.phase_name}")

            # Continue workflow from current phase
            asyncio.create_task(self._continue_from_current_phase())

            return ToolResponse(
                success=True,
                data={
                    "status": "resumed",
                    "current_phase": self.current_phase.phase_name,
                    "progress": self.progress,
                },
            )
        else:
            return ToolResponse(
                success=False, error="Failed to load workflow checkpoint"
            )

    async def _continue_from_current_phase(self):
        """Continue workflow execution from current phase"""
        remaining_phases = [p for p in WorkflowPhase if p not in self.phases_completed]

        for phase in remaining_phases:
            if self.workflow_status != WorkflowStatus.RUNNING:
                break
            await self._process_phase(phase)

    def execute_task(self, task: str) -> ToolResponse:
        """
        Execute workflow orchestration task.
        Factor 10: Single responsibility - workflow orchestration.
        """
        try:
            # Parse task for workflow parameters
            task_data = self._parse_workflow_task(task)

            # Start workflow
            result = asyncio.run(self.start_workflow_async(task_data))
            return result

        except Exception as e:
            self.handle_error(e, "task_execution")
            return ToolResponse(
                success=False, error=str(e), metadata={"agent_id": self.agent_id}
            )

    def _parse_workflow_task(self, task: str) -> Dict[str, Any]:
        """Parse task string to workflow parameters"""
        # Simple implementation - override in subclasses
        return {"task_description": task}

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply action to workflow state"""
        action_type = action.get("type", "unknown")

        if action_type == "pause":
            return self.pause_workflow()
        elif action_type == "resume":
            return self.resume_workflow()
        elif action_type == "approve_phase":
            phase_name = action.get("phase")
            approved = action.get("approved", False)
            # Implementation for manual approval
            return ToolResponse(success=True, data={"approved": approved})
        else:
            return ToolResponse(
                success=False, error=f"Unknown action type: {action_type}"
            )

    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Get comprehensive workflow status.
        Pin-citer pattern: detailed progress and context information.
        """
        status = self.get_status()

        # Add workflow-specific information
        status.update(
            {
                "workflow_name": self.workflow_name,
                "workflow_status": self.workflow_status.value,
                "current_phase": self.current_phase.phase_name,
                "phases_completed": [p.phase_name for p in self.phases_completed],
                "total_phases": len(WorkflowPhase),
                "workflow_duration": self._get_workflow_duration(),
                "approval_history": self.workflow_data.get("approval_history", []),
            }
        )

        return status


# Example usage: Citation Analysis Workflow (inspired by pin-citer domain)
class CitationAnalysisOrchestrator(ProgressAwareOrchestrator):
    """
    Example orchestrator for citation analysis workflow.
    Demonstrates pin-citer domain patterns adapted to 12-factor methodology.
    """

    def __init__(self, agent_id: str = None):
        super().__init__("citation_analysis", agent_id)

        # Register custom phase processors
        self.register_phase_processor(WorkflowPhase.ANALYSIS, self._analyze_documents)
        self.register_phase_processor(WorkflowPhase.PROCESSING, self._process_citations)
        self.register_phase_processor(WorkflowPhase.FINALIZATION, self._generate_output)

    async def _analyze_documents(self, workflow_data: Dict):
        """Analyze documents for citation opportunities"""
        logger.info("Analyzing documents for citations...")

        # Simulate document analysis with progress updates
        documents = workflow_data.get("documents", [])
        for i, doc in enumerate(documents):
            await asyncio.sleep(0.2)  # Simulate analysis
            progress = 0.3 + (i + 1) / len(documents) * 0.2  # 0.3 to 0.5
            self.set_progress(progress, "analyzing_documents")

    async def _process_citations(self, workflow_data: Dict):
        """Process identified citations"""
        logger.info("Processing citations...")

        # Simulate citation processing
        citations = workflow_data.get("citations", [])
        for i, citation in enumerate(citations):
            await asyncio.sleep(0.1)  # Simulate processing
            progress = 0.5 + (i + 1) / len(citations) * 0.2  # 0.5 to 0.7
            self.set_progress(progress, "processing_citations")

    async def _generate_output(self, workflow_data: Dict):
        """Generate final citation output"""
        logger.info("Generating citation output...")

        # Simulate output generation
        await asyncio.sleep(0.3)
        self.set_progress(0.9, "generating_output")

        # Add final results to workflow data
        workflow_data["output_generated"] = True
        workflow_data["citation_count"] = len(workflow_data.get("citations", []))
