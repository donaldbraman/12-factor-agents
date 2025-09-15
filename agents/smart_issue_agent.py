"""
SmartIssueAgent - Universal issue handler with automatic complexity detection.
Users can submit ANY issue to this agent and it will automatically:
1. Detect complexity 
2. Handle simple issues directly
3. Decompose complex issues and orchestrate sub-agents
4. Provide unified results

This provides the ideal UX: one agent handles everything, no matter the complexity.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse
from core.execution_context import ExecutionContext
from agents.issue_decomposer_agent import IssueDecomposerAgent
from agents.issue_fixer_agent import IssueFixerAgent


class SmartIssueProcessor(Tool):
    """Intelligently process any issue regardless of complexity"""

    def __init__(self):
        super().__init__(
            name="process_issue_smartly",
            description="Automatically detect complexity and handle any issue appropriately",
        )
        self.decomposer = IssueDecomposerAgent()
        self.fixer = IssueFixerAgent()

    def execute(self, issue_identifier: str) -> ToolResponse:
        """Process issue with automatic complexity detection and handling"""
        try:
            print(f"\n🧠 Smart processing issue: {issue_identifier}")

            # Circuit Breaker: Check if this issue should be blocked from retry
            if self._should_block_retry(issue_identifier):
                print("🚫 Circuit breaker: Issue already failed once, routing to human")
                return ToolResponse(
                    success=False,
                    error="Circuit breaker activated - issue requires human intervention",
                )

            # Step 1: Let decomposer analyze complexity
            print("🔍 Analyzing complexity...")
            decompose_result = self.decomposer.execute_task(issue_identifier)

            if not decompose_result.success:
                return decompose_result

            # Step 2: Decision based on complexity
            if not decompose_result.data["decomposed"]:
                # Simple enough - handle directly
                complexity = decompose_result.data.get("complexity", {}).get(
                    "complexity", "simple"
                )
                print(f"✅ Issue is {complexity} - handling directly")

                # Use IssueFixerAgent to handle it
                fix_result = self.fixer.execute_task(issue_identifier)

                return ToolResponse(
                    success=fix_result.success,
                    data={
                        "strategy": "direct_handling",
                        "complexity": complexity,
                        "result": fix_result.data,
                        "error": fix_result.error if not fix_result.success else None,
                    },
                )

            else:
                # Complex - was decomposed into sub-issues
                print(
                    f"🧩 Issue decomposed into {len(decompose_result.data['created_files']['created_issues'])} sub-issues"
                )
                print("🚀 Processing sub-issues...")

                sub_issues = decompose_result.data["created_files"]["created_issues"]
                sub_results = []

                # Process each sub-issue
                for sub_issue in sub_issues:
                    issue_num = sub_issue["issue_number"]
                    print(f"   📋 Processing #{issue_num}: {sub_issue['title']}")

                    # Route to appropriate agent based on assignee
                    if sub_issue["assignee"] in [
                        "issue_fixer_agent",
                        "IssueFixerAgent",
                    ]:
                        result = self.fixer.execute_task(issue_num)
                    elif sub_issue["assignee"] in ["testing_agent", "TestingAgent"]:
                        # For now, we'll use fixer for testing tasks too
                        # In future, could route to actual TestingAgent
                        result = self.fixer.execute_task(issue_num)
                    else:
                        # Default to fixer
                        result = self.fixer.execute_task(issue_num)

                    # Handle failure with FailureAnalysisAgent
                    if not result.success:
                        print(f"      ❌ Failed: {result.error}")
                        print("      🔬 Triggering failure analysis...")

                        # Get sub-issue content for analysis
                        sub_issue_path = Path("issues") / f"{issue_num}*.md"
                        sub_issue_files = list(Path("issues").glob(f"{issue_num}*.md"))
                        sub_issue_content = ""
                        if sub_issue_files:
                            sub_issue_content = sub_issue_files[0].read_text()

                        # Create failure context for analysis
                        failure_context = {
                            "original_issue": issue_identifier,
                            "failed_agent": sub_issue["assignee"],
                            "failure_message": result.error or "Task execution failed",
                            "issue_content": sub_issue_content,
                            "expected_outcome": f"Complete task: {sub_issue['title']}",
                            "sub_issue_number": issue_num,
                        }

                        # Trigger failure analysis
                        try:
                            from agents.failure_analysis_agent import (
                                FailureAnalysisAgent,
                            )

                            failure_agent = FailureAnalysisAgent()
                            analysis_result = failure_agent.execute_task(
                                json.dumps(failure_context)
                            )

                            if analysis_result.success:
                                print(
                                    f"      🎯 Analysis complete - created issue #{analysis_result.data['new_issue']['new_issue_number']}"
                                )
                                failure_analysis = analysis_result.data
                            else:
                                print(
                                    f"      ⚠️ Analysis failed: {analysis_result.error}"
                                )
                                failure_analysis = None
                        except Exception as e:
                            print(f"      ⚠️ Could not run failure analysis: {e}")
                            failure_analysis = None
                    else:
                        print("      ✅ Completed")
                        failure_analysis = None

                    sub_results.append(
                        {
                            "issue_number": issue_num,
                            "title": sub_issue["title"],
                            "assignee": sub_issue["assignee"],
                            "success": result.success,
                            "result": result.data,
                            "error": result.error if not result.success else None,
                            "failure_analysis": failure_analysis,
                        }
                    )

                # Compile overall result
                successful = [r for r in sub_results if r["success"]]
                overall_success = len(successful) == len(sub_results)

                print(
                    f"\n📊 Overall result: {len(successful)}/{len(sub_results)} sub-issues completed"
                )

                return ToolResponse(
                    success=overall_success,
                    data={
                        "strategy": "decomposition_and_orchestration",
                        "complexity": decompose_result.data["complexity"],
                        "total_sub_issues": len(sub_results),
                        "successful_sub_issues": len(successful),
                        "sub_results": sub_results,
                        "decomposition_data": decompose_result.data,
                    },
                )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"issue_identifier": {"type": "string"}},
            "required": ["issue_identifier"],
        }

    def _should_block_retry(self, issue_identifier: str) -> bool:
        """Circuit breaker: Block retry if issue already failed once"""
        try:
            # Check if this is already a research issue (never retry research issues)
            if self._is_research_issue(issue_identifier):
                return True

            # Check if original issue already has failure tracking
            return self._has_previous_failure(issue_identifier)

        except Exception:
            # If we can't determine, allow retry (fail open)
            return False

    def _is_research_issue(self, issue_identifier: str) -> bool:
        """Check if this is a research issue created by failure analysis"""
        try:
            issue_files = list(Path("issues").glob(f"{issue_identifier}*.md"))
            if not issue_files:
                return False

            content = issue_files[0].read_text()
            return (
                "This issue was created by FailureAnalysisAgent" in content
                or "research-failed-" in issue_files[0].name.lower()
            )
        except Exception:
            return False

    def _has_previous_failure(self, issue_identifier: str) -> bool:
        """Check if issue has already been through failure analysis"""
        try:
            # Look for existing research issues that reference this as parent
            research_files = list(Path("issues").glob("*research-failed-*.md"))
            for research_file in research_files:
                content = research_file.read_text()
                if f"Parent Issue\n{issue_identifier}" in content:
                    return True
            return False
        except Exception:
            return False


class SmartIssueAgent(BaseAgent):
    """
    Universal issue handler - the single agent users interact with.

    Automatically:
    - Detects issue complexity
    - Handles simple issues directly
    - Decomposes and orchestrates complex issues
    - Provides unified results

    Users never need to worry about which agent to use or how complex their issue is.
    """

    def register_tools(self) -> List[Tool]:
        """Register smart processing tool"""
        return [SmartIssueProcessor()]

    def execute_task(
        self, task: str, context: Optional[ExecutionContext] = None
    ) -> ToolResponse:
        """
        Intelligently handle any issue regardless of complexity.
        Task format: issue number or path to issue file
        """

        print(f"\n🧠 SmartIssueAgent processing: {task}")
        print("=" * 60)

        # Use smart processor
        processor = self.tools[0]
        result = processor.execute(task)

        if result.success:
            strategy = result.data.get("strategy", "unknown")

            if strategy == "direct_handling":
                print(
                    f"\n✅ Issue handled directly as {result.data['complexity']} complexity"
                )
                self.state.set(f"smart_issue_{task}_strategy", "direct")

            elif strategy == "decomposition_and_orchestration":
                total = result.data["total_sub_issues"]
                successful = result.data["successful_sub_issues"]
                print(
                    f"\n🎯 Complex issue orchestrated: {successful}/{total} sub-issues completed"
                )
                self.state.set(f"smart_issue_{task}_strategy", "orchestrated")
                self.state.set(
                    f"smart_issue_{task}_sub_results", result.data["sub_results"]
                )

            # Update overall state
            self.state.set(f"smart_issue_{task}_completed", True)
            self.state.set(f"smart_issue_{task}_result", result.data)

        else:
            print(f"\n❌ SmartIssueAgent failed: {result.error}")

        return result

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply smart processing action"""
        action_type = action.get("type", "process")

        if action_type == "process":
            return self.execute_task(action.get("issue", ""))

        return ToolResponse(success=False, error=f"Unknown action type: {action_type}")

    def _should_block_retry(self, issue_identifier: str) -> bool:
        """Circuit breaker: Block retry if issue already failed once"""
        try:
            # Check if this is already a research issue (never retry research issues)
            if self._is_research_issue(issue_identifier):
                return True

            # Check if original issue already has failure tracking
            return self._has_previous_failure(issue_identifier)

        except Exception:
            # If we can't determine, allow retry (fail open)
            return False

    def _is_research_issue(self, issue_identifier: str) -> bool:
        """Check if this is a research issue created by failure analysis"""
        try:
            issue_files = list(Path("issues").glob(f"{issue_identifier}*.md"))
            if not issue_files:
                return False

            content = issue_files[0].read_text()
            return (
                "This issue was created by FailureAnalysisAgent" in content
                or "research-failed-" in issue_files[0].name.lower()
            )
        except Exception:
            return False

    def _has_previous_failure(self, issue_identifier: str) -> bool:
        """Check if issue has already been through failure analysis"""
        try:
            # Look for existing research issues that reference this as parent
            research_files = list(Path("issues").glob("*research-failed-*.md"))
            for research_file in research_files:
                content = research_file.read_text()
                if f"Parent Issue\n{issue_identifier}" in content:
                    return True
            return False
        except Exception:
            return False


# Self-test when run directly
# Usage: uv run agents/smart_issue_agent.py
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        issue = sys.argv[1]
    else:
        # Test with a simple issue first
        issue = "061"

    print(f"🧠 Testing SmartIssueAgent with issue #{issue}...")
    agent = SmartIssueAgent()

    result = agent.execute_task(issue)

    if result.success:
        print(f"\n✅ SmartIssueAgent successfully processed issue #{issue}!")
        strategy = result.data.get("strategy", "unknown")
        print(f"Strategy used: {strategy}")

        if strategy == "decomposition_and_orchestration":
            successful = result.data.get("successful_sub_issues", 0)
            total = result.data.get("total_sub_issues", 0)
            print(f"Sub-issues: {successful}/{total} completed")

        print("\nDetailed results:")
        print(json.dumps(result.data, indent=2))
    else:
        print(f"\n❌ SmartIssueAgent failed: {result.error}")
