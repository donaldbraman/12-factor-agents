"""
FailureAnalysisAgent - Researches failed tasks and creates actionable follow-up issues.
When an agent fails, this agent investigates the failure and creates better, more detailed tasks.

Implements 12-Factor Agent principles:
- Factor 8: Own Your Control Flow (structured failure analysis)
- Factor 9: Compact Errors into Context Window (error summarization)
- Factor 10: Small, Focused Agents (specialized failure analysis)
- Factor 12: Stateless Reducer (clear failure → actionable issue transformation)
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse


@dataclass
class FailureContext:
    """Context information about a failed task"""

    original_issue_number: str
    failed_agent: str
    failure_message: str
    issue_content: str
    expected_outcome: str
    sub_issue_number: Optional[str] = None


class FailureInvestigationTool(Tool):
    """Investigate why a task failed and determine root cause"""

    def __init__(self):
        super().__init__(
            name="investigate_failure",
            description="Analyze task failure and determine root cause",
        )

    def execute(self, failure_context: FailureContext) -> ToolResponse:
        """Investigate the failure and identify the root cause"""
        try:
            analysis = {
                "root_cause": self._identify_root_cause(failure_context),
                "missing_information": self._identify_missing_info(failure_context),
                "actionable_next_steps": self._generate_next_steps(failure_context),
                "difficulty_assessment": self._assess_difficulty(failure_context),
            }

            return ToolResponse(success=True, data=analysis)

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def _identify_root_cause(self, context: FailureContext) -> str:
        """Identify the root cause of the failure"""
        failure_msg = context.failure_message.lower()
        issue_content = context.issue_content.lower()

        # Common failure patterns
        if "could not determine" in failure_msg:
            if "current" not in issue_content or "should" not in issue_content:
                return "MISSING_CURRENT_STATE"
            elif not re.search(r"[/\w.-]+\.\w+", context.issue_content):
                return "MISSING_TARGET_FILE"
            else:
                return "VAGUE_REQUIREMENTS"

        elif "file not found" in failure_msg:
            return "INVALID_FILE_PATH"

        elif "syntax" in failure_msg:
            return "MALFORMED_ISSUE_CONTENT"

        elif "permission" in failure_msg:
            return "ACCESS_DENIED"

        else:
            return "UNKNOWN_FAILURE"

    def _identify_missing_info(self, context: FailureContext) -> List[str]:
        """Identify what information is missing to complete the task"""
        missing = []
        content = context.issue_content

        # Check for specific patterns needed by IssueFixerAgent
        if not re.search(r"## Current\s*(?:Code|Text)", content, re.IGNORECASE):
            missing.append("Current state/code block")

        if not re.search(
            r"## (?:Required|Should|New)\s*(?:Code|Text|Change)", content, re.IGNORECASE
        ):
            missing.append("Required change/target state")

        if not re.search(r"[/\w.-]+\.\w+", content):
            missing.append("Specific target file path")

        if not re.search(
            r"(?:line\s+\d+|function\s+\w+|class\s+\w+)", content, re.IGNORECASE
        ):
            missing.append("Specific location within file")

        # Check for ambiguous language
        ambiguous_terms = ["somehow", "better", "improve", "fix", "update"]
        for term in ambiguous_terms:
            if term in content.lower() and len(content.split()) < 50:
                missing.append("Specific implementation details")
                break

        return missing

    def _generate_next_steps(self, context: FailureContext) -> List[str]:
        """Generate specific next steps to resolve the failure"""
        root_cause = self._identify_root_cause(context)

        if root_cause == "MISSING_CURRENT_STATE":
            return [
                "Examine the target file to identify current state",
                "Document the exact current code/text that needs changing",
                "Create clear Current/Required change blocks",
                "Specify exact line numbers or function names",
            ]

        elif root_cause == "MISSING_TARGET_FILE":
            return [
                "Identify the specific file that needs modification",
                "Verify the file exists in the codebase",
                "Document the full file path",
                "Confirm write permissions to the file",
            ]

        elif root_cause == "VAGUE_REQUIREMENTS":
            return [
                "Break down the vague requirement into specific actions",
                "Identify concrete, measurable outcomes",
                "Create step-by-step implementation plan",
                "Define clear success criteria",
            ]

        else:
            return [
                "Research the specific failure message",
                "Investigate similar successful tasks",
                "Consult documentation for the failed agent",
                "Create more detailed task specification",
            ]

    def _assess_difficulty(self, context: FailureContext) -> str:
        """Assess the difficulty of fixing this failure"""
        missing_info = self._identify_missing_info(context)
        root_cause = self._identify_root_cause(context)

        if len(missing_info) <= 1 and root_cause in [
            "MISSING_TARGET_FILE",
            "MISSING_CURRENT_STATE",
        ]:
            return "EASY"  # Just need more specific info
        elif len(missing_info) <= 3 and root_cause in ["VAGUE_REQUIREMENTS"]:
            return "MODERATE"  # Need clarification and research
        else:
            return "HARD"  # Complex investigation required

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"failure_context": {"type": "object"}},
            "required": ["failure_context"],
        }


class ActionableIssueCreatorTool(Tool):
    """Create a new, more actionable issue based on failure analysis"""

    def __init__(self):
        super().__init__(
            name="create_actionable_issue",
            description="Create a new issue with better specifications",
        )

    def execute(
        self, failure_context: FailureContext, analysis: Dict[str, Any]
    ) -> ToolResponse:
        """Create a new issue that addresses the failure"""
        try:
            # Find next available issue number
            issues_dir = Path("issues")
            existing_nums = set()
            for issue_file in issues_dir.glob("*.md"):
                match = re.match(r"(\d+)", issue_file.stem)
                if match:
                    existing_nums.add(int(match.group(1)))

            next_num = max(existing_nums) + 1 if existing_nums else 200
            issue_num = str(next_num).zfill(3)

            # Create detailed issue content
            issue_content = self._generate_issue_content(
                issue_num, failure_context, analysis
            )

            # Write issue file
            filename = f"{issue_num}-research-failed-{failure_context.original_issue_number}.md"
            issue_path = issues_dir / filename
            issue_path.write_text(issue_content)

            return ToolResponse(
                success=True,
                data={
                    "new_issue_number": issue_num,
                    "file_path": str(issue_path),
                    "difficulty": analysis["difficulty_assessment"],
                    "root_cause": analysis["root_cause"],
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def _generate_issue_content(
        self, issue_num: str, context: FailureContext, analysis: Dict[str, Any]
    ) -> str:
        """Generate comprehensive issue content"""

        # Create title based on root cause
        root_cause = analysis["root_cause"]
        if root_cause == "MISSING_CURRENT_STATE":
            title = f"Research and Document Current State for Issue #{context.original_issue_number}"
        elif root_cause == "MISSING_TARGET_FILE":
            title = f"Identify Target File for Issue #{context.original_issue_number}"
        elif root_cause == "VAGUE_REQUIREMENTS":
            title = f"Clarify Requirements for Issue #{context.original_issue_number}"
        else:
            title = f"Investigate Failure for Issue #{context.original_issue_number}"

        # Build actionable steps
        steps = "\n".join(
            f"{i+1}. {step}" for i, step in enumerate(analysis["actionable_next_steps"])
        )

        # Build missing info checklist
        missing_checklist = ""
        if analysis["missing_information"]:
            missing_checklist = (
                "## Missing Information to Gather\n"
                + "\n".join(f"- [ ] {info}" for info in analysis["missing_information"])
                + "\n\n"
            )

        return f"""# Issue #{issue_num}: {title}

## Background
This issue was created by FailureAnalysisAgent to resolve a failed task.

**Original Issue:** #{context.original_issue_number}
**Failed Agent:** {context.failed_agent}
**Failure Reason:** {context.failure_message}
**Root Cause:** {root_cause}
**Difficulty Assessment:** {analysis['difficulty_assessment']}

## Original Task That Failed
{context.issue_content[:500]}{'...' if len(context.issue_content) > 500 else ''}

## Research Required
{missing_checklist}## Actionable Steps (Factor 8: Own Your Control Flow)
{steps}

## Expected Output
Create a new, more specific issue that the {context.failed_agent} can successfully execute. The new issue should include:

1. **Clear Current State**: Exact code/text that exists now
2. **Specific Target**: Exact code/text that should exist after changes
3. **File Path**: Complete path to file(s) that need modification
4. **Location Details**: Line numbers, function names, or specific sections

## Definition of Done
- [ ] Root cause of failure identified and documented
- [ ] Missing information gathered through research
- [ ] New actionable issue created with complete specifications
- [ ] New issue ready for successful execution by original agent

## Files to Research
{self._extract_files_from_content(context.issue_content)}

## Type
research

## Priority
high

## Status
open

## Assignee
code_review_agent

## Parent Issue
{context.original_issue_number}

## Failed Sub-Issue
{context.sub_issue_number or 'N/A'}
"""

    def _extract_files_from_content(self, content: str) -> str:
        """Extract file references from content"""
        files = re.findall(r"([/\w.-]+\.\w+)", content)
        if files:
            return "\n".join(f"- {file}" for file in set(files))
        else:
            return "- Files to be determined through research"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "failure_context": {"type": "object"},
                "analysis": {"type": "object"},
            },
            "required": ["failure_context", "analysis"],
        }


class FailureAnalysisAgent(BaseAgent):
    """
    Agent that analyzes failed tasks and creates actionable follow-up issues.

    When other agents fail, this agent:
    1. Investigates the root cause
    2. Identifies missing information
    3. Creates a detailed research task
    4. Generates an actionable follow-up issue

    Implements intelligent failure recovery from the hierarchical orchestrator pattern.
    """

    def register_tools(self) -> List[Tool]:
        """Register failure analysis tools"""
        return [FailureInvestigationTool(), ActionableIssueCreatorTool()]

    def execute_task(self, task: str) -> ToolResponse:
        """
        Analyze a failure and create actionable follow-up.
        Task format: JSON with failure context
        """
        try:
            # Parse task as JSON (passed from SmartIssueAgent)
            failure_data = json.loads(task)

            failure_context = FailureContext(
                original_issue_number=failure_data.get("original_issue", "unknown"),
                failed_agent=failure_data.get("failed_agent", "unknown"),
                failure_message=failure_data.get("failure_message", "unknown"),
                issue_content=failure_data.get("issue_content", ""),
                expected_outcome=failure_data.get(
                    "expected_outcome", "task completion"
                ),
                sub_issue_number=failure_data.get("sub_issue_number"),
            )

            print(f"\n🔬 Analyzing failure from {failure_context.failed_agent}")
            print(f"📋 Original issue: #{failure_context.original_issue_number}")
            print(f"❌ Failure: {failure_context.failure_message}")

            # Step 1: Investigate the failure
            print("\n🔍 Investigating root cause...")
            investigator = self.tools[0]
            investigation_result = investigator.execute(failure_context)

            if not investigation_result.success:
                return investigation_result

            analysis = investigation_result.data
            print(f"🎯 Root cause: {analysis['root_cause']}")
            print(f"📊 Difficulty: {analysis['difficulty_assessment']}")

            # Step 2: Create actionable follow-up issue
            print("\n📝 Creating research issue...")
            creator = self.tools[1]
            creation_result = creator.execute(failure_context, analysis)

            if not creation_result.success:
                return creation_result

            new_issue_data = creation_result.data
            print(f"✅ Created issue #{new_issue_data['new_issue_number']}")
            print(f"📄 File: {new_issue_data['file_path']}")

            # Update state
            self.state.set(
                f"failure_analysis_{failure_context.original_issue_number}",
                {
                    "analyzed": True,
                    "root_cause": analysis["root_cause"],
                    "new_issue": new_issue_data["new_issue_number"],
                    "difficulty": analysis["difficulty_assessment"],
                },
            )

            return ToolResponse(
                success=True,
                data={
                    "analysis": analysis,
                    "new_issue": new_issue_data,
                    "recommendations": analysis["actionable_next_steps"],
                },
            )

        except json.JSONDecodeError:
            return ToolResponse(
                success=False, error="Task must be valid JSON with failure context"
            )
        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply failure analysis action"""
        action_type = action.get("type", "analyze")

        if action_type == "analyze":
            return self.execute_task(action.get("failure_context", "{}"))

        return ToolResponse(success=False, error=f"Unknown action type: {action_type}")


# Self-test when run directly
if __name__ == "__main__":
    import sys

    # Test with sample failure
    sample_failure = {
        "original_issue": "130",
        "failed_agent": "IssueFixerAgent",
        "failure_message": "Could not determine how to fix this issue",
        "issue_content": "Fix BaseAgent test failure",
        "expected_outcome": "Test should pass",
        "sub_issue_number": "138",
    }

    print("🔬 Testing FailureAnalysisAgent...")
    agent = FailureAnalysisAgent()

    result = agent.execute_task(json.dumps(sample_failure))

    if result.success:
        print("\n✅ Failure analysis completed!")
        print(f"Root cause: {result.data['analysis']['root_cause']}")
        print(f"New issue: #{result.data['new_issue']['new_issue_number']}")
        print(json.dumps(result.data, indent=2))
    else:
        print(f"\n❌ Analysis failed: {result.error}")
