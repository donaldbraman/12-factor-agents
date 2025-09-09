"""
Agent Handoff and Continuity System
Inspired by cite-assist's sophisticated handoff and work transfer protocols.
Implements 12-factor compliant agent-to-agent work continuity.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any
from enum import Enum

from .agent import BaseAgent
from .tools import Tool, ToolResponse

logger = logging.getLogger(__name__)


class HandoffType(Enum):
    """Types of agent handoffs"""

    WORK_COMPLETION = "work_completion"
    EMERGENCY_HANDOFF = "emergency_handoff"
    SCHEDULED_TRANSITION = "scheduled_transition"
    ERROR_RECOVERY = "error_recovery"
    SKILL_SPECIALIZATION = "skill_specialization"


class HandoffStatus(Enum):
    """Status of handoff process"""

    INITIATED = "initiated"
    DOCUMENTED = "documented"
    VALIDATED = "validated"
    TRANSFERRED = "transferred"
    ACKNOWLEDGED = "acknowledged"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkContext:
    """
    Comprehensive work context for agent handoffs.

    Based on cite-assist's handoff documentation but structured
    for 12-factor compliance with external state management.
    """

    def __init__(self, context_id: str = None):
        self.context_id = (
            context_id or f"context_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.created_at = datetime.now()

        # Work status and progress
        self.work_summary = {
            "phases_completed": [],
            "current_phase": None,
            "next_phases": [],
            "progress_percentage": 0.0,
            "estimated_completion": None,
        }

        # Technical context
        self.technical_context = {
            "files_modified": [],
            "dependencies_added": [],
            "services_created": [],
            "tests_implemented": [],
            "documentation_updated": [],
            "known_issues": [],
        }

        # Domain context
        self.domain_context = {
            "business_requirements": [],
            "stakeholder_feedback": [],
            "user_stories": [],
            "acceptance_criteria": [],
            "edge_cases_identified": [],
        }

        # Operational context
        self.operational_context = {
            "environment_setup": {},
            "configuration_changes": {},
            "deployment_notes": [],
            "monitoring_alerts": [],
            "performance_metrics": {},
        }

        # Handoff metadata
        self.handoff_metadata = {
            "confidence_level": "high",
            "risk_assessment": "low",
            "blockers": [],
            "assumptions": [],
            "recommendations": [],
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert work context to dictionary for serialization"""
        return {
            "context_id": self.context_id,
            "created_at": self.created_at.isoformat(),
            "work_summary": self.work_summary,
            "technical_context": self.technical_context,
            "domain_context": self.domain_context,
            "operational_context": self.operational_context,
            "handoff_metadata": self.handoff_metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkContext":
        """Create work context from dictionary"""
        context = cls(data.get("context_id"))
        context.created_at = datetime.fromisoformat(
            data.get("created_at", datetime.now().isoformat())
        )
        context.work_summary = data.get("work_summary", {})
        context.technical_context = data.get("technical_context", {})
        context.domain_context = data.get("domain_context", {})
        context.operational_context = data.get("operational_context", {})
        context.handoff_metadata = data.get("handoff_metadata", {})
        return context


class HandoffDocument:
    """
    Structured handoff documentation.

    Enhanced version of cite-assist's handoff prompts with
    12-factor compliance and comprehensive context preservation.
    """

    def __init__(self, handoff_id: str = None):
        self.handoff_id = (
            handoff_id or f"handoff_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.created_at = datetime.now()
        self.handoff_type = HandoffType.WORK_COMPLETION
        self.status = HandoffStatus.INITIATED

        self.source_agent = None
        self.target_agent = None
        self.work_context = None

        # Handoff sections (based on cite-assist's structure)
        self.sections = {
            "executive_summary": "",
            "work_completed": [],
            "current_state": {},
            "next_priorities": [],
            "technical_details": {},
            "known_issues": [],
            "recommendations": [],
            "success_criteria": [],
            "risk_assessment": {},
            "validation_checklist": [],
        }

    def generate_handoff_prompt(self) -> str:
        """
        Generate comprehensive handoff prompt for next agent.
        Based on cite-assist's handoff_prompt.md structure but enhanced.
        """
        prompt = f"""# Agent Handoff Documentation

**Handoff ID**: {self.handoff_id}  
**Date**: {self.created_at.strftime('%Y-%m-%d')}  
**Type**: {self.handoff_type.value}  
**Status**: {self.status.value}  

## 🎯 Executive Summary

{self.sections.get('executive_summary', 'Work handoff in progress')}

## ✅ Work Completed Summary

"""

        # Add completed work sections
        for work_item in self.sections.get("work_completed", []):
            prompt += f"### {work_item.get('category', 'Work Item')}\n"
            prompt += f"{work_item.get('description', '')}\n\n"

            if work_item.get("deliverables"):
                prompt += "**Key Deliverables:**\n"
                for deliverable in work_item["deliverables"]:
                    prompt += f"- {deliverable}\n"
                prompt += "\n"

        # Add current state
        prompt += f"""## 🔍 Current State Analysis

### Technical State
- **Files Modified**: {len(self.work_context.technical_context.get('files_modified', []) if self.work_context else [])}
- **Services Created**: {len(self.work_context.technical_context.get('services_created', []) if self.work_context else [])}
- **Tests Implemented**: {len(self.work_context.technical_context.get('tests_implemented', []) if self.work_context else [])}

### Progress Status
- **Current Phase**: {self.work_context.work_summary.get('current_phase', 'Unknown') if self.work_context else 'Unknown'}
- **Progress**: {self.work_context.work_summary.get('progress_percentage', 0)}%
- **Phases Completed**: {len(self.work_context.work_summary.get('phases_completed', []) if self.work_context else [])}

"""

        # Add next priorities
        prompt += "## 🎯 Next Priority Areas for Development\n\n"
        for i, priority in enumerate(self.sections.get("next_priorities", []), 1):
            prompt += f"### Priority {i}: {priority.get('title', 'Task')}\n"
            prompt += f"**Objective**: {priority.get('objective', '')}\n\n"

            if priority.get("tasks"):
                prompt += "**Specific Tasks:**\n"
                for task in priority["tasks"]:
                    prompt += f"- {task}\n"
                prompt += "\n"

        # Add known issues
        if self.sections.get("known_issues"):
            prompt += "## 🔍 Known Issues and Considerations\n\n"
            for issue in self.sections["known_issues"]:
                prompt += f"### {issue.get('title', 'Issue')}\n"
                prompt += f"- **Description**: {issue.get('description', '')}\n"
                prompt += f"- **Impact**: {issue.get('impact', 'Unknown')}\n"
                prompt += f"- **Suggested Resolution**: {issue.get('resolution', 'To be determined')}\n\n"

        # Add technical context
        prompt += """## 🛠️ Technical Context for Next Agent

### Architecture Overview
The current system maintains the following patterns:
- **12-Factor Compliance**: All implementations follow 12-factor methodology
- **External State Management**: State stored in unified external store
- **Structured Error Handling**: Comprehensive error context preservation
- **Progress Tracking**: Granular progress monitoring with pause/resume

### Key Integration Points
"""

        if self.work_context and self.work_context.technical_context.get(
            "services_created"
        ):
            for service in self.work_context.technical_context["services_created"]:
                prompt += f"- **{service}**: Core service implementation\n"

        prompt += "\n### Configuration\n"
        prompt += "All configuration externalized via environment variables. No configuration changes required for basic operation.\n\n"

        # Add recommendations
        if self.sections.get("recommendations"):
            prompt += "## 🚀 Recommendations for Success\n\n"
            for i, rec in enumerate(self.sections["recommendations"], 1):
                prompt += f"{i}. **{rec.get('title', 'Recommendation')}**: {rec.get('description', '')}\n"
            prompt += "\n"

        # Add validation checklist
        prompt += "## ✅ Validation Checklist\n\n"
        for item in self.sections.get("validation_checklist", []):
            status = "✅" if item.get("completed", False) else "⏳"
            prompt += f"- {status} {item.get('description', 'Validation item')}\n"

        # Add final notes
        prompt += f"""

## 🎯 Final Notes

### Handoff Confidence Level
**{self.sections.get('risk_assessment', {}).get('confidence_level', 'Medium')} Confidence** - {self.sections.get('risk_assessment', {}).get('justification', 'Standard handoff process completed')}

### What's Working Well
"""

        for strength in self.sections.get("risk_assessment", {}).get("strengths", []):
            prompt += f"- {strength}\n"

        prompt += "\n### What Needs Attention\n"
        for concern in self.sections.get("risk_assessment", {}).get("concerns", []):
            prompt += f"- {concern}\n"

        prompt += f"""

---

**Ready for Next Phase**: The work is ready for continuation by the next agent with full context preservation and 12-factor compliance maintained.

**Handoff Status**: {self.status.value.upper()}
"""

        return prompt

    def to_dict(self) -> Dict[str, Any]:
        """Convert handoff document to dictionary"""
        return {
            "handoff_id": self.handoff_id,
            "created_at": self.created_at.isoformat(),
            "handoff_type": self.handoff_type.value,
            "status": self.status.value,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "work_context": self.work_context.to_dict() if self.work_context else None,
            "sections": self.sections,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HandoffDocument":
        """Create handoff document from dictionary"""
        doc = cls(data.get("handoff_id"))
        doc.created_at = datetime.fromisoformat(
            data.get("created_at", datetime.now().isoformat())
        )
        doc.handoff_type = HandoffType(
            data.get("handoff_type", HandoffType.WORK_COMPLETION.value)
        )
        doc.status = HandoffStatus(data.get("status", HandoffStatus.INITIATED.value))
        doc.source_agent = data.get("source_agent")
        doc.target_agent = data.get("target_agent")

        if data.get("work_context"):
            doc.work_context = WorkContext.from_dict(data["work_context"])

        doc.sections = data.get("sections", {})
        return doc


class HandoffAgent(BaseAgent):
    """
    Agent specialized in managing work handoffs and continuity.

    Implements cite-assist's handoff patterns with full 12-factor compliance
    including external state management and structured documentation.
    """

    def __init__(self, agent_id: str = None):
        super().__init__(agent_id)

        # Handoff state management
        self.active_handoffs = {}
        self.handoff_history = []

        # Set up handoff workflow stages
        self.set_workflow_stages(
            [
                "context_collection",
                "documentation_generation",
                "validation",
                "transfer",
                "acknowledgment",
            ]
        )

        logger.info(f"HandoffAgent initialized: {self.agent_id}")

    def register_tools(self) -> List[Tool]:
        """Register handoff management tools"""
        return [
            Tool(
                name="initiate_handoff",
                description="Initiate agent-to-agent work handoff",
                parameters={
                    "source_agent": "str",
                    "target_agent": "str",
                    "handoff_type": "str",
                },
            ),
            Tool(
                name="collect_work_context",
                description="Collect comprehensive work context from agent",
                parameters={"agent_id": "str", "context_scope": "str"},
            ),
            Tool(
                name="generate_handoff_document",
                description="Generate structured handoff documentation",
                parameters={"work_context": "dict", "handoff_spec": "dict"},
            ),
            Tool(
                name="validate_handoff",
                description="Validate handoff completeness and accuracy",
                parameters={"handoff_id": "str", "validation_criteria": "dict"},
            ),
            Tool(
                name="complete_handoff",
                description="Complete handoff process and transfer ownership",
                parameters={"handoff_id": "str", "acknowledgment_data": "dict"},
            ),
        ]

    async def execute_task(self, task: str) -> ToolResponse:
        """Execute handoff management task"""
        try:
            # Parse handoff request
            handoff_spec = self._parse_handoff_task(task)

            # Set up progress tracking
            self.set_progress(0.0, "initializing")
            self.workflow_data["handoff_specification"] = handoff_spec

            # Execute handoff workflow
            result = await self._execute_handoff_workflow(handoff_spec)

            # Update final state
            self.set_progress(1.0, "completed")

            return ToolResponse(
                success=result["success"],
                data=result,
                metadata={"agent_id": self.agent_id, "handoff_management": True},
            )

        except Exception as e:
            self.handle_error(e, "handoff_execution")
            return ToolResponse(
                success=False, error=str(e), metadata={"agent_id": self.agent_id}
            )

    async def _execute_handoff_workflow(
        self, handoff_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute complete handoff workflow"""
        workflow_result = {
            "success": False,
            "handoff_id": None,
            "documentation_generated": False,
            "validation_passed": False,
            "transfer_completed": False,
            "errors": [],
        }

        try:
            # Phase 1: Context Collection
            self.set_progress(0.1, "context_collection")
            context = await self._collect_work_context(handoff_spec)
            workflow_result["context_collected"] = True

            # Phase 2: Documentation Generation
            self.set_progress(0.3, "documentation_generation")
            handoff_doc = await self._generate_handoff_document(context, handoff_spec)
            workflow_result["handoff_id"] = handoff_doc.handoff_id
            workflow_result["documentation_generated"] = True

            # Phase 3: Validation
            self.set_progress(0.5, "validation")
            validation_result = await self._validate_handoff_document(handoff_doc)
            workflow_result["validation_passed"] = validation_result["passed"]

            if not validation_result["passed"]:
                workflow_result["errors"].extend(validation_result["errors"])
                return workflow_result

            # Phase 4: Transfer
            self.set_progress(0.7, "transfer")
            transfer_result = await self._execute_handoff_transfer(handoff_doc)
            workflow_result["transfer_completed"] = transfer_result["success"]

            # Phase 5: Acknowledgment
            self.set_progress(0.9, "acknowledgment")
            ack_result = await self._request_handoff_acknowledgment(handoff_doc)
            workflow_result["acknowledgment_received"] = ack_result["acknowledged"]

            # Mark as successful if all phases completed
            workflow_result["success"] = all(
                [
                    workflow_result["context_collected"],
                    workflow_result["documentation_generated"],
                    workflow_result["validation_passed"],
                    workflow_result["transfer_completed"],
                    workflow_result["acknowledgment_received"],
                ]
            )

            # Store handoff in history
            self.handoff_history.append(handoff_doc.to_dict())
            self.save_checkpoint()

            return workflow_result

        except Exception as e:
            workflow_result["errors"].append(str(e))
            self.handle_error(e, "handoff_workflow")
            return workflow_result

    async def _collect_work_context(self, handoff_spec: Dict[str, Any]) -> WorkContext:
        """Collect comprehensive work context from source agent"""
        logger.info("Collecting work context for handoff")

        source_agent_id = handoff_spec.get("source_agent")
        context_scope = handoff_spec.get("context_scope", "complete")

        # Create work context
        context = WorkContext()

        # In a real implementation, this would interface with the actual source agent
        # For now, we'll create a representative context based on handoff spec

        # Populate context based on available information
        if handoff_spec.get("work_summary"):
            context.work_summary.update(handoff_spec["work_summary"])

        if handoff_spec.get("technical_details"):
            context.technical_context.update(handoff_spec["technical_details"])

        if handoff_spec.get("domain_info"):
            context.domain_context.update(handoff_spec["domain_info"])

        # Set confidence level based on context completeness
        completeness_score = self._assess_context_completeness(context)
        if completeness_score > 0.8:
            context.handoff_metadata["confidence_level"] = "high"
        elif completeness_score > 0.6:
            context.handoff_metadata["confidence_level"] = "medium"
        else:
            context.handoff_metadata["confidence_level"] = "low"

        logger.info(
            f"Work context collected with {context.handoff_metadata['confidence_level']} confidence"
        )
        return context

    async def _generate_handoff_document(
        self, context: WorkContext, handoff_spec: Dict[str, Any]
    ) -> HandoffDocument:
        """Generate structured handoff documentation"""
        logger.info("Generating handoff documentation")

        handoff_doc = HandoffDocument()
        handoff_doc.source_agent = handoff_spec.get("source_agent")
        handoff_doc.target_agent = handoff_spec.get("target_agent")
        handoff_doc.handoff_type = HandoffType(
            handoff_spec.get("handoff_type", HandoffType.WORK_COMPLETION.value)
        )
        handoff_doc.work_context = context

        # Generate executive summary
        handoff_doc.sections["executive_summary"] = self._generate_executive_summary(
            context, handoff_spec
        )

        # Generate work completed section
        handoff_doc.sections["work_completed"] = self._generate_work_completed_section(
            context
        )

        # Generate next priorities
        handoff_doc.sections["next_priorities"] = self._generate_next_priorities(
            context, handoff_spec
        )

        # Generate known issues
        handoff_doc.sections["known_issues"] = self._generate_known_issues(context)

        # Generate recommendations
        handoff_doc.sections["recommendations"] = self._generate_recommendations(
            context, handoff_spec
        )

        # Generate validation checklist
        handoff_doc.sections[
            "validation_checklist"
        ] = self._generate_validation_checklist(context)

        # Generate risk assessment
        handoff_doc.sections["risk_assessment"] = self._generate_risk_assessment(
            context, handoff_spec
        )

        handoff_doc.status = HandoffStatus.DOCUMENTED

        # Store in active handoffs
        self.active_handoffs[handoff_doc.handoff_id] = handoff_doc

        logger.info(f"Handoff document generated: {handoff_doc.handoff_id}")
        return handoff_doc

    async def _validate_handoff_document(
        self, handoff_doc: HandoffDocument
    ) -> Dict[str, Any]:
        """Validate handoff document completeness and accuracy"""
        logger.info(f"Validating handoff document: {handoff_doc.handoff_id}")

        validation_result = {
            "passed": False,
            "errors": [],
            "warnings": [],
            "score": 0.0,
        }

        # Validation checks
        checks = {
            "executive_summary_present": bool(
                handoff_doc.sections.get("executive_summary")
            ),
            "work_completed_documented": bool(
                handoff_doc.sections.get("work_completed")
            ),
            "next_priorities_defined": bool(
                handoff_doc.sections.get("next_priorities")
            ),
            "technical_context_complete": bool(
                handoff_doc.work_context and handoff_doc.work_context.technical_context
            ),
            "risk_assessment_present": bool(
                handoff_doc.sections.get("risk_assessment")
            ),
            "validation_checklist_present": bool(
                handoff_doc.sections.get("validation_checklist")
            ),
        }

        # Calculate validation score
        passed_checks = sum(checks.values())
        validation_result["score"] = passed_checks / len(checks)

        # Check for critical failures
        if not checks["executive_summary_present"]:
            validation_result["errors"].append("Missing executive summary")

        if not checks["work_completed_documented"]:
            validation_result["errors"].append("Work completed section is empty")

        # Overall validation result
        validation_result["passed"] = (
            validation_result["score"] >= 0.7 and not validation_result["errors"]
        )

        # Update handoff status
        if validation_result["passed"]:
            handoff_doc.status = HandoffStatus.VALIDATED
        else:
            handoff_doc.status = HandoffStatus.FAILED

        logger.info(
            f"Validation completed: {'PASSED' if validation_result['passed'] else 'FAILED'}"
        )
        return validation_result

    async def _execute_handoff_transfer(
        self, handoff_doc: HandoffDocument
    ) -> Dict[str, Any]:
        """Execute the actual handoff transfer"""
        logger.info(f"Executing handoff transfer: {handoff_doc.handoff_id}")

        # Generate handoff prompt
        handoff_prompt = handoff_doc.generate_handoff_prompt()

        # In a real implementation, this would:
        # 1. Save handoff prompt to external state store
        # 2. Notify target agent
        # 3. Transfer ownership of work items
        # 4. Update system records

        transfer_result = {
            "success": True,
            "handoff_prompt_generated": True,
            "handoff_prompt_length": len(handoff_prompt),
            "target_agent_notified": True,
            "ownership_transferred": True,
        }

        # Update handoff status
        handoff_doc.status = HandoffStatus.TRANSFERRED

        # Store handoff prompt (in real implementation, would use external store)
        handoff_doc.sections["generated_prompt"] = handoff_prompt

        logger.info("Handoff transfer completed successfully")
        return transfer_result

    async def _request_handoff_acknowledgment(
        self, handoff_doc: HandoffDocument
    ) -> Dict[str, Any]:
        """Request acknowledgment from target agent"""
        logger.info(f"Requesting handoff acknowledgment: {handoff_doc.handoff_id}")

        # In a real implementation, this would:
        # 1. Send acknowledgment request to target agent
        # 2. Wait for response with timeout
        # 3. Handle acknowledgment or escalation

        # For demo purposes, simulate acknowledgment
        ack_result = {
            "acknowledged": True,
            "acknowledged_at": datetime.now().isoformat(),
            "target_agent_response": "Handoff received and acknowledged",
            "readiness_confirmed": True,
        }

        # Update handoff status
        handoff_doc.status = HandoffStatus.ACKNOWLEDGED

        logger.info("Handoff acknowledgment received")
        return ack_result

    def _parse_handoff_task(self, task: str) -> Dict[str, Any]:
        """Parse handoff task specification"""
        # Simple implementation - would be enhanced for production
        lines = task.split("\n")

        spec = {
            "handoff_type": HandoffType.WORK_COMPLETION.value,
            "source_agent": "unknown",
            "target_agent": "next_agent",
            "context_scope": "complete",
        }

        # Parse structured task information
        for line in lines:
            if line.startswith("source:"):
                spec["source_agent"] = line.split(":", 1)[1].strip()
            elif line.startswith("target:"):
                spec["target_agent"] = line.split(":", 1)[1].strip()
            elif line.startswith("type:"):
                spec["handoff_type"] = line.split(":", 1)[1].strip()

        return spec

    def _assess_context_completeness(self, context: WorkContext) -> float:
        """Assess completeness of work context"""
        # Simple scoring based on presence of key information
        score = 0.0

        if context.work_summary.get("phases_completed"):
            score += 0.2
        if context.technical_context.get("files_modified"):
            score += 0.2
        if context.domain_context.get("business_requirements"):
            score += 0.2
        if context.operational_context.get("environment_setup"):
            score += 0.2
        if context.handoff_metadata.get("assumptions"):
            score += 0.2

        return score

    def _generate_executive_summary(
        self, context: WorkContext, handoff_spec: Dict[str, Any]
    ) -> str:
        """Generate executive summary for handoff"""
        phases_completed = len(context.work_summary.get("phases_completed", []))
        progress = context.work_summary.get("progress_percentage", 0)

        return f"""Work handoff from {handoff_spec.get('source_agent', 'previous agent')} to {handoff_spec.get('target_agent', 'next agent')}.

**Progress Status**: {progress}% completed with {phases_completed} phases finished.
**Handoff Type**: {handoff_spec.get('handoff_type', 'work_completion')}
**Context Confidence**: {context.handoff_metadata.get('confidence_level', 'medium')}

All work context has been preserved with full 12-factor compliance maintained throughout the transition."""

    def _generate_work_completed_section(
        self, context: WorkContext
    ) -> List[Dict[str, Any]]:
        """Generate work completed section"""
        completed_work = []

        # Add phases completed
        for phase in context.work_summary.get("phases_completed", []):
            completed_work.append(
                {
                    "category": f"Phase: {phase}",
                    "description": f"Successfully completed {phase} phase",
                    "deliverables": [],  # Would be populated from actual context
                }
            )

        # Add technical deliverables
        if context.technical_context.get("files_modified"):
            completed_work.append(
                {
                    "category": "Technical Implementation",
                    "description": "Code implementation and file modifications",
                    "deliverables": context.technical_context["files_modified"],
                }
            )

        return completed_work

    def _generate_next_priorities(
        self, context: WorkContext, handoff_spec: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate next priority areas"""
        priorities = []

        # Add remaining phases
        next_phases = context.work_summary.get("next_phases", [])
        for i, phase in enumerate(next_phases[:3]):  # Top 3 priorities
            priorities.append(
                {
                    "title": f"{phase.title() if isinstance(phase, str) else str(phase)}",
                    "objective": f"Complete {phase} phase of the project",
                    "tasks": [
                        f"Execute {phase} phase tasks",
                        f"Validate {phase} completion",
                    ],
                }
            )

        return priorities

    def _generate_known_issues(self, context: WorkContext) -> List[Dict[str, Any]]:
        """Generate known issues section"""
        issues = []

        # Add issues from context
        for issue_text in context.technical_context.get("known_issues", []):
            issues.append(
                {
                    "title": "Technical Issue",
                    "description": str(issue_text),
                    "impact": "Medium",
                    "resolution": "To be determined by next agent",
                }
            )

        return issues

    def _generate_recommendations(
        self, context: WorkContext, handoff_spec: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for next agent"""
        recommendations = []

        # Add context-based recommendations
        if context.handoff_metadata.get("recommendations"):
            for rec in context.handoff_metadata["recommendations"]:
                recommendations.append(
                    {"title": "Context Recommendation", "description": str(rec)}
                )

        # Add standard recommendations
        recommendations.append(
            {
                "title": "Validate Work Context",
                "description": "Review all handoff documentation and validate current system state",
            }
        )

        recommendations.append(
            {
                "title": "Continue 12-Factor Compliance",
                "description": "Maintain strict 12-factor methodology adherence in all new development",
            }
        )

        return recommendations

    def _generate_validation_checklist(
        self, context: WorkContext
    ) -> List[Dict[str, Any]]:
        """Generate validation checklist"""
        checklist = []

        # Standard validation items
        checklist.append(
            {"description": "Work context reviewed and understood", "completed": False}
        )

        checklist.append(
            {"description": "Technical state validated", "completed": False}
        )

        checklist.append(
            {"description": "Next priorities confirmed", "completed": False}
        )

        return checklist

    def _generate_risk_assessment(
        self, context: WorkContext, handoff_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate risk assessment"""
        confidence = context.handoff_metadata.get("confidence_level", "medium")

        return {
            "confidence_level": confidence,
            "justification": f"Standard handoff process completed with {confidence} confidence level",
            "strengths": [
                "12-factor compliance maintained",
                "Complete work context preserved",
                "Structured handoff documentation",
            ],
            "concerns": [
                "Standard transition risks",
                "Context interpretation accuracy",
            ],
        }

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply action to handoff management"""
        action_type = action.get("type", "unknown")

        if action_type == "emergency_handoff":
            # Trigger emergency handoff procedures
            return ToolResponse(success=True, data={"emergency_handoff": "initiated"})

        elif action_type == "abort_handoff":
            handoff_id = action.get("handoff_id")
            if handoff_id in self.active_handoffs:
                self.active_handoffs[handoff_id].status = HandoffStatus.FAILED
                return ToolResponse(success=True, data={"handoff_aborted": handoff_id})

        else:
            return ToolResponse(
                success=False, error=f"Unknown action type: {action_type}"
            )


# Example usage and testing
async def demo_agent_handoff():
    """Demonstrate agent handoff capabilities"""
    handoff_agent = HandoffAgent()

    # Simulate handoff request
    task = """
    source: development_agent_123
    target: testing_agent_456
    type: work_completion
    
    Handoff development work to testing team for validation and quality assurance.
    Current progress: 75% complete with implementation phase finished.
    """

    print("Executing agent handoff...")
    result = await handoff_agent.execute_task(task)

    print(f"Handoff completed: {result.success}")
    if result.success:
        print(f"Handoff ID: {result.data.get('handoff_id')}")
        print(f"Documentation generated: {result.data.get('documentation_generated')}")
        print(f"Transfer completed: {result.data.get('transfer_completed')}")

    return result


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demo_agent_handoff())
