#!/usr/bin/env python3
"""
SPARKY 6.0: Async Edition with Launch/Pause/Resume
Factor 6 Compliant: Full async lifecycle management

Key capabilities:
- Launch async tasks
- Pause for external events (test results, human approval)
- Resume from saved state
- Learn from execution results
"""

import json
import pickle
import subprocess
import asyncio
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
import uuid
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.prompt_manager import PromptManager


class AgentState(Enum):
    """States for SPARKY's lifecycle"""

    INITIALIZED = auto()
    RUNNING = auto()
    PAUSED = auto()
    WAITING_FOR_TESTS = auto()
    WAITING_FOR_APPROVAL = auto()
    LEARNING = auto()
    COMPLETED = auto()
    FAILED = auto()


class PauseReason(Enum):
    """Reasons why SPARKY might pause"""

    TEST_SUITE_RUNNING = auto()
    HUMAN_APPROVAL_NEEDED = auto()
    EXTERNAL_DEPENDENCY = auto()
    RATE_LIMITED = auto()
    LEARNING_CHECKPOINT = auto()
    ERROR_RECOVERY = auto()


@dataclass
class ExecutionContext:
    """Complete context for resumable execution"""

    agent_id: str
    issue_file: Path
    issue_content: str
    current_state: AgentState
    pause_reason: Optional[PauseReason] = None
    actions_planned: List[Dict[str, Any]] = field(default_factory=list)
    actions_completed: List[Dict[str, Any]] = field(default_factory=list)
    actions_pending: List[Dict[str, Any]] = field(default_factory=list)
    test_results: Optional[Dict[str, Any]] = None
    learning_insights: List[str] = field(default_factory=list)
    checkpoint_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    resume_token: Optional[str] = None
    webhook_url: Optional[str] = None


@dataclass
class TestSuiteResult:
    """Results from external test suite"""

    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    failure_details: List[Dict[str, str]] = field(default_factory=list)
    coverage_percent: Optional[float] = None


class StateManager:
    """Manages persistent state for async operations"""

    def __init__(self, state_dir: Path = None):
        if state_dir is None:
            state_dir = Path.home() / ".sparky" / "state"
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save_context(self, context: ExecutionContext) -> str:
        """Save context to disk and return path"""
        context.last_updated = datetime.now()
        state_file = self.state_dir / f"{context.agent_id}.pkl"

        with open(state_file, "wb") as f:
            pickle.dump(context, f)

        # Also save human-readable JSON
        json_file = self.state_dir / f"{context.agent_id}.json"
        json_data = {
            "agent_id": context.agent_id,
            "state": context.current_state.name,
            "pause_reason": context.pause_reason.name if context.pause_reason else None,
            "actions_completed": len(context.actions_completed),
            "actions_pending": len(context.actions_pending),
            "created_at": context.created_at.isoformat(),
            "last_updated": context.last_updated.isoformat(),
            "resume_token": context.resume_token,
        }

        with open(json_file, "w") as f:
            json.dump(json_data, f, indent=2)

        return str(state_file)

    def load_context(self, agent_id: str) -> Optional[ExecutionContext]:
        """Load context from disk"""
        state_file = self.state_dir / f"{agent_id}.pkl"

        if not state_file.exists():
            return None

        with open(state_file, "rb") as f:
            return pickle.load(f)

    def list_paused_agents(self) -> List[Dict[str, Any]]:
        """List all paused agents"""
        paused = []

        for json_file in self.state_dir.glob("*.json"):
            with open(json_file) as f:
                data = json.load(f)
                if data["state"] in [
                    "PAUSED",
                    "WAITING_FOR_TESTS",
                    "WAITING_FOR_APPROVAL",
                ]:
                    paused.append(data)

        return paused


class LearningEngine:
    """Learn from execution results to improve future performance"""

    def __init__(self):
        self.insights_file = Path.home() / ".sparky" / "learning" / "insights.json"
        self.insights_file.parent.mkdir(parents=True, exist_ok=True)
        self.insights = self._load_insights()

    def _load_insights(self) -> Dict[str, Any]:
        """Load accumulated insights"""
        if self.insights_file.exists():
            with open(self.insights_file) as f:
                return json.load(f)
        return {
            "patterns": {},
            "success_rates": {},
            "common_failures": [],
            "optimization_hints": [],
        }

    def learn_from_test_results(
        self, context: ExecutionContext, results: TestSuiteResult
    ) -> List[str]:
        """Analyze test results and extract learnings"""
        insights = []

        # Track success patterns
        if results.failed == 0:
            insights.append(
                f"✅ All tests passed! Pattern successful: {context.actions_completed[-1]}"
            )
            self._record_success_pattern(context.actions_completed[-1])
        else:
            # Analyze failures
            for failure in results.failure_details:
                if "timeout" in failure.get("error", "").lower():
                    insights.append("⚠️ Timeout detected - may need async handling")
                elif "connection" in failure.get("error", "").lower():
                    insights.append("⚠️ Connection issue - add retry logic")
                elif "assertion" in failure.get("error", "").lower():
                    insights.append("⚠️ Logic error - review test expectations")

        # Learn from coverage
        if results.coverage_percent and results.coverage_percent < 80:
            insights.append(
                f"📊 Coverage only {results.coverage_percent}% - add more tests"
            )

        # Save insights
        self.insights["last_run"] = {
            "agent_id": context.agent_id,
            "timestamp": datetime.now().isoformat(),
            "test_results": asdict(results),
            "insights": insights,
        }
        self._save_insights()

        return insights

    def _record_success_pattern(self, action: Dict[str, Any]):
        """Record successful action patterns"""
        pattern_key = (
            f"{action.get('type', 'unknown')}_{action.get('target', 'unknown')}"
        )
        if pattern_key not in self.insights["patterns"]:
            self.insights["patterns"][pattern_key] = {"count": 0, "success": 0}

        self.insights["patterns"][pattern_key]["count"] += 1
        self.insights["patterns"][pattern_key]["success"] += 1

    def _save_insights(self):
        """Persist insights to disk"""
        with open(self.insights_file, "w") as f:
            json.dump(self.insights, f, indent=2)

    def suggest_optimizations(self, context: ExecutionContext) -> List[str]:
        """Suggest optimizations based on learning"""
        suggestions = []

        # Check for repeated patterns
        for action in context.actions_planned:
            pattern_key = (
                f"{action.get('type', 'unknown')}_{action.get('target', 'unknown')}"
            )
            if pattern_key in self.insights["patterns"]:
                pattern = self.insights["patterns"][pattern_key]
                success_rate = pattern["success"] / pattern["count"]
                if success_rate < 0.5:
                    suggestions.append(
                        f"⚠️ Pattern '{pattern_key}' has low success rate: {success_rate:.1%}"
                    )

        return suggestions


class AsyncSparky:
    """SPARKY 6.0 with async lifecycle management"""

    def __init__(self):
        self.prompt_manager = PromptManager()
        self.state_manager = StateManager()
        self.learning_engine = LearningEngine()

    async def launch(self, issue_file: Path) -> ExecutionContext:
        """Launch a new SPARKY agent"""

        # Create new context
        context = ExecutionContext(
            agent_id=str(uuid.uuid4())[:8],
            issue_file=issue_file,
            issue_content=issue_file.read_text(),
            current_state=AgentState.INITIALIZED,
            resume_token=str(uuid.uuid4()),
        )

        print(f"🚀 Launching SPARKY agent: {context.agent_id}")
        print(f"   Resume token: {context.resume_token}")

        # Create feature branch
        branch_name = f"sparky/{context.agent_id}-{issue_file.stem}"
        context.checkpoint_data["branch_name"] = branch_name

        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name], check=True, capture_output=True
            )
            print(f"   Feature branch: {branch_name}")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Branch creation failed: {e}")
            # Continue anyway - might be testing

        # Plan actions (simplified for demo)
        context.actions_planned = self._plan_actions(context.issue_content)
        context.actions_pending = context.actions_planned.copy()

        # Get optimization suggestions
        suggestions = self.learning_engine.suggest_optimizations(context)
        if suggestions:
            print("💡 Learning engine suggestions:")
            for suggestion in suggestions:
                print(f"   {suggestion}")
                context.learning_insights.append(suggestion)

        # Start execution
        context.current_state = AgentState.RUNNING
        return await self._execute(context)

    async def _execute(self, context: ExecutionContext) -> ExecutionContext:
        """Execute actions until pause or completion"""

        while context.actions_pending and context.current_state == AgentState.RUNNING:
            action = context.actions_pending[0]

            print(f"⚡ Executing: {action['description']}")

            # Simulate action execution
            result = await self._execute_action(action)

            # Move action from pending to completed
            context.actions_pending.pop(0)
            context.actions_completed.append({**action, "result": result})

            # Check if we should pause
            if self._should_pause(action, result):
                return await self._pause(context, action, result)

        # All actions completed - commit and create PR
        await self._finalize_changes(context)

        context.current_state = AgentState.COMPLETED
        self.state_manager.save_context(context)
        print(f"✅ Agent {context.agent_id} completed successfully!")

        return context

    async def _finalize_changes(self, context: ExecutionContext):
        """Commit changes and create PR"""
        branch_name = context.checkpoint_data.get("branch_name")
        if not branch_name:
            return

        try:
            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "diff", "--name-only"], capture_output=True, text=True
            )

            if not result.stdout.strip():
                print("   No changes to commit")
                return

            # Add and commit changes
            subprocess.run(["git", "add", "."], check=True)

            commit_msg = f"SPARKY {context.agent_id}: {context.issue_file.stem}\n\nActions completed: {len(context.actions_completed)}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)

            print(f"   📝 Committed changes on {branch_name}")

            # Push branch
            subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)

            # Create PR
            pr_title = f"SPARKY {context.agent_id}: {context.issue_file.stem}"
            pr_body = f"Automated fix for {context.issue_file.name}\n\nActions: {len(context.actions_completed)}\nLearning insights: {len(context.learning_insights)}"

            subprocess.run(
                [
                    "gh",
                    "pr",
                    "create",
                    "--title",
                    pr_title,
                    "--body",
                    pr_body,
                    "--head",
                    branch_name,
                ],
                check=True,
            )

            print(f"   🚀 Created PR for {branch_name}")

        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Git operation failed: {e}")
            # Don't fail the whole operation

    async def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action"""
        action_type = action.get("type", "unknown")

        if action_type == "run_tests":
            # Trigger test suite
            print("   🧪 Triggering test suite...")
            return {
                "status": "tests_triggered",
                "command": "pytest tests/",
                "async": True,
            }
        elif action_type == "modify_file":
            # Simulate file modification
            await asyncio.sleep(0.1)  # Simulate work
            return {
                "status": "success",
                "file": action.get("file", "unknown"),
                "changes": action.get("changes", 0),
            }
        else:
            # Generic action
            await asyncio.sleep(0.1)  # Simulate work
            return {"status": "success"}

    def _should_pause(self, action: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Determine if we should pause after this action"""

        # Pause for async test results
        if action.get("type") == "run_tests" and result.get("async"):
            return True

        # Pause for human approval on destructive actions
        if action.get("requires_approval"):
            return True

        # Pause at learning checkpoints
        if action.get("learning_checkpoint"):
            return True

        return False

    async def _pause(
        self, context: ExecutionContext, action: Dict[str, Any], result: Dict[str, Any]
    ) -> ExecutionContext:
        """Pause execution and save state"""

        # Determine pause reason
        if action.get("type") == "run_tests":
            context.pause_reason = PauseReason.TEST_SUITE_RUNNING
            context.current_state = AgentState.WAITING_FOR_TESTS
            print("⏸️  Pausing for test results...")
            print(f"   Resume with: sparky resume {context.agent_id}")
        elif action.get("requires_approval"):
            context.pause_reason = PauseReason.HUMAN_APPROVAL_NEEDED
            context.current_state = AgentState.WAITING_FOR_APPROVAL
            print("⏸️  Pausing for human approval...")
            print(f"   Approve with: sparky approve {context.agent_id}")
        elif action.get("learning_checkpoint"):
            context.pause_reason = PauseReason.LEARNING_CHECKPOINT
            context.current_state = AgentState.LEARNING
            print("⏸️  Pausing for learning analysis...")
        else:
            context.pause_reason = PauseReason.EXTERNAL_DEPENDENCY
            context.current_state = AgentState.PAUSED

        # Save state
        state_file = self.state_manager.save_context(context)
        print(f"💾 State saved to: {state_file}")

        # Set up webhook if configured
        if context.webhook_url:
            print(f"🔔 Webhook configured: {context.webhook_url}")

        return context

    async def resume(
        self, agent_id: str, event_data: Dict[str, Any] = None
    ) -> Optional[ExecutionContext]:
        """Resume a paused agent"""

        # Load saved context
        context = self.state_manager.load_context(agent_id)
        if not context:
            print(f"❌ Agent {agent_id} not found")
            return None

        print(f"▶️  Resuming agent {agent_id}")
        print(f"   State: {context.current_state.name}")
        print(f"   Actions completed: {len(context.actions_completed)}")
        print(f"   Actions remaining: {len(context.actions_pending)}")

        # Ensure we're on the right branch
        branch_name = context.checkpoint_data.get("branch_name")
        if branch_name:
            try:
                subprocess.run(
                    ["git", "checkout", branch_name], check=True, capture_output=True
                )
                print(f"   Checked out branch: {branch_name}")
            except subprocess.CalledProcessError:
                print(f"   ⚠️  Could not checkout {branch_name}")

        # Handle different resume scenarios
        if context.current_state == AgentState.WAITING_FOR_TESTS:
            # Process test results
            if event_data and "test_results" in event_data:
                results = TestSuiteResult(**event_data["test_results"])
                context.test_results = asdict(results)

                # Learn from results
                insights = self.learning_engine.learn_from_test_results(
                    context, results
                )
                context.learning_insights.extend(insights)

                print(
                    f"📊 Test Results: {results.passed} passed, {results.failed} failed"
                )

                if insights:
                    print("🧠 Learning insights:")
                    for insight in insights:
                        print(f"   {insight}")

                # Decide next action based on results
                if results.failed > 0:
                    # Add fix actions
                    fix_actions = self._generate_fix_actions(results.failure_details)
                    context.actions_pending = fix_actions + context.actions_pending
                    print(f"🔧 Added {len(fix_actions)} fix actions")

        elif context.current_state == AgentState.WAITING_FOR_APPROVAL:
            # Check approval
            if event_data and event_data.get("approved"):
                print("✅ Approval received")
            else:
                print("❌ Approval denied - stopping")
                context.current_state = AgentState.FAILED
                self.state_manager.save_context(context)
                return context

        # Continue execution
        context.current_state = AgentState.RUNNING
        return await self._execute(context)

    def _plan_actions(self, issue_content: str) -> List[Dict[str, Any]]:
        """Plan actions based on issue content"""
        actions = []

        # Simplified planning for demo
        if "test" in issue_content.lower():
            actions.append(
                {
                    "type": "modify_file",
                    "description": "Fix the identified issue",
                    "file": "src/main.py",
                    "changes": 5,
                }
            )
            actions.append(
                {
                    "type": "run_tests",
                    "description": "Run test suite to verify fix",
                    "async": True,
                }
            )
            actions.append(
                {
                    "type": "create_pr",
                    "description": "Create pull request",
                    "requires_approval": True,
                }
            )
        else:
            actions.append(
                {
                    "type": "analyze",
                    "description": "Analyze the issue",
                    "learning_checkpoint": True,
                }
            )
            actions.append({"type": "implement", "description": "Implement solution"})

        return actions

    def _generate_fix_actions(
        self, failure_details: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Generate actions to fix test failures"""
        fix_actions = []

        for failure in failure_details:
            fix_actions.append(
                {
                    "type": "fix_test",
                    "description": f"Fix failing test: {failure.get('test', 'unknown')}",
                    "error": failure.get("error", ""),
                    "file": failure.get("file", "unknown"),
                }
            )

        # Re-run tests after fixes
        fix_actions.append(
            {
                "type": "run_tests",
                "description": "Re-run tests after fixes",
                "async": True,
            }
        )

        return fix_actions

    def status(self, agent_id: str = None) -> None:
        """Show status of agent(s)"""

        if agent_id:
            # Show specific agent
            context = self.state_manager.load_context(agent_id)
            if not context:
                print(f"❌ Agent {agent_id} not found")
                return

            print(f"📊 Agent {agent_id} Status:")
            print(f"   State: {context.current_state.name}")
            print(f"   Created: {context.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Updated: {context.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Issue: {context.issue_file.name}")
            print(
                f"   Progress: {len(context.actions_completed)}/{len(context.actions_planned)} actions"
            )

            if context.pause_reason:
                print(f"   Pause reason: {context.pause_reason.name}")

            if context.learning_insights:
                print(f"   Insights: {len(context.learning_insights)}")
                for insight in context.learning_insights[-3:]:
                    print(f"     - {insight}")
        else:
            # Show all paused agents
            paused = self.state_manager.list_paused_agents()

            if not paused:
                print("No paused agents")
                return

            print(f"📋 Paused Agents ({len(paused)}):")
            for agent in paused:
                print(
                    f"   {agent['agent_id']}: {agent['state']} - {agent['pause_reason']}"
                )
                print(
                    f"      Actions: {agent['actions_completed']}/{agent['actions_completed'] + agent['actions_pending']}"
                )
                print(f"      Resume token: {agent['resume_token']}")


async def main():
    """CLI interface for SPARKY 6.0"""
    import sys

    sparky = AsyncSparky()

    if len(sys.argv) < 2:
        print("SPARKY 6.0 - Async Edition")
        print("\nUsage:")
        print("  sparky launch <issue_file>     - Launch new agent")
        print("  sparky resume <agent_id>        - Resume paused agent")
        print("  sparky status [agent_id]        - Show agent status")
        print("  sparky approve <agent_id>       - Approve pending action")
        sys.exit(1)

    command = sys.argv[1]

    if command == "launch" and len(sys.argv) >= 3:
        issue_file = Path(sys.argv[2])
        if not issue_file.exists():
            print(f"❌ Issue file not found: {issue_file}")
            sys.exit(1)

        context = await sparky.launch(issue_file)

    elif command == "resume" and len(sys.argv) >= 3:
        agent_id = sys.argv[2]

        # Check for test results in environment
        event_data = {}
        if len(sys.argv) >= 4:
            # Parse test results if provided
            try:
                event_data = json.loads(sys.argv[3])
            except:
                # Try as test result shorthand
                parts = sys.argv[3].split("/")
                if len(parts) == 2:
                    event_data = {
                        "test_results": {
                            "passed": int(parts[0]),
                            "failed": int(parts[1]),
                            "skipped": 0,
                            "duration_seconds": 45.2,
                        }
                    }

        await sparky.resume(agent_id, event_data)

    elif command == "status":
        agent_id = sys.argv[2] if len(sys.argv) >= 3 else None
        sparky.status(agent_id)

    elif command == "approve" and len(sys.argv) >= 3:
        agent_id = sys.argv[2]
        await sparky.resume(agent_id, {"approved": True})

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
