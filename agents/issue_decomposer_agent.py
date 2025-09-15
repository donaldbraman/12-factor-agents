"""
IssueDecomposerAgent - Breaks down complex issues into manageable subtasks.
Inspired by the hierarchical orchestrator pattern for intelligent task decomposition.
"""

import json
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent  # noqa: E402
from core.tools import Tool, ToolResponse  # noqa: E402
from core.execution_context import ExecutionContext  # noqa: E402


class IssueComplexity(Enum):
    """Issue complexity levels for decomposition decisions"""

    ATOMIC = "atomic"  # Single simple change
    SIMPLE = "simple"  # One agent can handle
    MODERATE = "moderate"  # Multiple related changes
    COMPLEX = "complex"  # Multiple files/agents needed
    ENTERPRISE = "enterprise"  # System-wide changes


@dataclass
class SubIssue:
    """A decomposed sub-issue"""

    title: str
    description: str
    target_file: Optional[str] = None
    assignee: Optional[str] = None
    type: str = "bug"
    priority: str = "medium"
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ComplexityAnalyzerTool(Tool):
    """Analyze issue complexity for decomposition decisions"""

    def __init__(self):
        super().__init__(
            name="analyze_complexity",
            description="Analyze issue complexity and decomposition needs",
        )

    def execute(self, issue_content: str) -> ToolResponse:
        """Analyze complexity of an issue"""
        try:
            content_lower = issue_content.lower()

            # Enterprise indicators - system-wide changes
            enterprise_keywords = [
                "refactor entire",
                "system-wide",
                "complete overhaul",
                "full stack",
                "migrate entire system",
                "rewrite",
            ]

            # Complex indicators - multiple files/agents
            complex_keywords = [
                "multiple files",
                "update.*and.*",
                "fix.*and.*",
                "documentation.*code",
                "examples.*tests",
                "all.*files",
                r"###.*1\.",
                r"###.*2\.",
                r"###.*3\.",  # Numbered sections indicate complexity
            ]

            # Moderate indicators - related changes
            moderate_keywords = [
                "update",
                "fix",
                "add.*to",
                "improve",
                "enhance",
                "modify",
            ]

            # Simple indicators - single focused change
            simple_keywords = [
                "typo",
                "spelling",
                "single file",
                "one line",
                "minor fix",
                "change.*to",
                "fix.*in",
                "simple",
                "small",
                "quick",
            ]

            # Count file references (only actual file paths)
            # Look for patterns like: path/to/file.ext, ./file.py, /absolute/path.txt
            # Exclude email addresses, URLs, and version numbers
            file_refs = len(
                re.findall(
                    r"(?:^|[\s\"'/])(?:[./]?[\w/-]+/)?[\w-]+\.(?:py|js|ts|md|txt|json|yaml|yml|toml|cfg|conf|sh|bash|gitignore)(?:$|[\s\"'])",
                    issue_content,
                )
            )

            # Count sections/problems
            sections = len(re.findall(r"###?\s+\d+\.", issue_content))

            # Check if it's a simple current/should pattern
            has_simple_change = bool(
                re.search(r"current.*should|change.*to|fix.*typo", content_lower)
            )

            # Determine complexity (be more conservative)
            if any(keyword in content_lower for keyword in enterprise_keywords):
                complexity = IssueComplexity.ENTERPRISE
                confidence = 0.9
            elif (
                any(keyword in content_lower for keyword in complex_keywords)
                or file_refs > 3
                or sections > 3
            ):
                complexity = IssueComplexity.COMPLEX
                confidence = 0.8
            elif (
                any(keyword in content_lower for keyword in simple_keywords)
                or has_simple_change
            ):
                complexity = IssueComplexity.SIMPLE
                confidence = 0.8
            elif (
                any(keyword in content_lower for keyword in moderate_keywords)
                or file_refs > 1
                or sections > 1
            ):
                complexity = IssueComplexity.MODERATE
                confidence = 0.7
            else:
                complexity = IssueComplexity.ATOMIC
                confidence = 0.6

            return ToolResponse(
                success=True,
                data={
                    "complexity": complexity.value,
                    "confidence": confidence,
                    "file_refs": file_refs,
                    "sections": sections,
                    "indicators": {
                        "enterprise": any(
                            k in content_lower for k in enterprise_keywords
                        ),
                        "complex": any(k in content_lower for k in complex_keywords),
                        "moderate": any(k in content_lower for k in moderate_keywords),
                        "simple": any(k in content_lower for k in simple_keywords),
                    },
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"issue_content": {"type": "string"}},
            "required": ["issue_content"],
        }


class IssueDecomposerTool(Tool):
    """Decompose complex issues into manageable sub-issues"""

    def __init__(self):
        super().__init__(
            name="decompose_issue",
            description="Break down complex issue into sub-issues",
        )
        self.strategies = {
            IssueComplexity.ATOMIC: self._atomic_strategy,
            IssueComplexity.SIMPLE: self._simple_strategy,
            IssueComplexity.MODERATE: self._moderate_strategy,
            IssueComplexity.COMPLEX: self._complex_strategy,
            IssueComplexity.ENTERPRISE: self._enterprise_strategy,
        }

    def execute(
        self, issue_content: str, complexity: str, issue_title: str = "Complex Issue"
    ) -> ToolResponse:
        """Decompose issue based on complexity"""
        try:
            complexity_enum = IssueComplexity(complexity)
            strategy = self.strategies.get(complexity_enum, self._moderate_strategy)

            sub_issues = strategy(issue_content, issue_title)

            return ToolResponse(
                success=True,
                data={
                    "complexity": complexity,
                    "sub_issues": [
                        {
                            "title": sub.title,
                            "description": sub.description,
                            "target_file": sub.target_file,
                            "assignee": sub.assignee,
                            "type": sub.type,
                            "priority": sub.priority,
                            "dependencies": sub.dependencies,
                        }
                        for sub in sub_issues
                    ],
                    "total_sub_issues": len(sub_issues),
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def _atomic_strategy(self, content: str, title: str) -> List[SubIssue]:
        """No decomposition needed for atomic issues"""
        return [
            SubIssue(
                title=title,
                description="Issue is atomic and cannot be decomposed further",
                assignee="issue_fixer_agent",
            )
        ]

    def _simple_strategy(self, content: str, title: str) -> List[SubIssue]:
        """Simple decomposition - single agent handles it"""
        return [
            SubIssue(
                title=f"Execute: {title}",
                description=content[:500] + "..." if len(content) > 500 else content,
                assignee="issue_fixer_agent",
            )
        ]

    def _moderate_strategy(self, content: str, title: str) -> List[SubIssue]:
        """
        Moderate decomposition using agent intelligence with heuristic guidance.

        Typically breaks into 2-3 focused tasks that can work together.
        Uses heuristics to guide agent understanding rather than rigid patterns.
        """

        # Heuristic: Moderate issues typically benefit from focused implementation + validation

        implementation_task = SubIssue(
            title=f"Implement: {title}",
            description=f"""**Objective**: Implement the functionality described in this moderate complexity issue.

**Original Issue**:
{content}

**Your Intelligence Task**: 
Use your understanding to implement what's needed. This is moderate complexity so:

- Analyze the requirements and understand what needs to be built
- Identify which files, components, or systems need modification
- Implement the changes with proper error handling and code quality
- Follow existing patterns and conventions in the codebase
- Test your changes as you implement

**Heuristic Guidance**:
- Look for specific file mentions, code snippets, or technical specs
- Notice Current/Should patterns that indicate what to change
- Identify integration points with existing functionality  
- Consider edge cases and error conditions
- Ensure backwards compatibility unless explicitly changing

**Implementation Approach**:
1. Understand the requirements thoroughly
2. Identify target files and components
3. Implement changes following existing patterns
4. Add proper error handling and validation
5. Test functionality works as expected
6. Document any important decisions or changes

**Success Criteria**:
- All requirements from the issue are implemented
- Code follows project conventions and quality standards
- Implementation handles edge cases appropriately  
- Changes integrate properly with existing systems
- Functionality is tested and working""",
            assignee="issue_fixer_agent",
            priority="high",
            type="implementation",
        )

        validation_task = SubIssue(
            title=f"Test and validate: {title}",
            description=f"""**Objective**: Test the implementation to ensure it works correctly and meets requirements.

**Context**:
{content}

**Your Intelligence Task**:
Validate that the implementation works properly:

- Test the implemented functionality end-to-end
- Verify edge cases and error conditions are handled
- Check integration with existing systems  
- Ensure user experience meets expectations
- Validate that all requirements from the original issue are satisfied

**Heuristic Guidance**:
- Review what was implemented against the original requirements
- Create test scenarios for normal usage and edge cases
- Test integration points and data flows
- Verify error handling and user experience
- Check for any performance or security considerations

**Testing Approach**:
1. Review implementation against original requirements
2. Test normal usage scenarios
3. Test edge cases and error conditions
4. Validate integration points work correctly
5. Check user experience and workflows
6. Verify no regressions were introduced
7. Document any issues found

**Success Criteria**:
- All functionality works as specified
- Edge cases are handled properly
- No regressions in existing functionality
- User experience is smooth and intuitive
- Implementation is ready for production use""",
            assignee="qa_agent",
            priority="medium",
            type="validation",
            dependencies=["Implement"],
        )

        return [implementation_task, validation_task]

    def _complex_strategy(self, content: str, title: str) -> List[SubIssue]:
        """
        Complex decomposition using agent intelligence with heuristic guidance.

        Instead of rigid regex patterns, provide intelligent heuristics that let
        the agent understand and decompose naturally. Based on orchestration patterns:
        - Planning phase (understanding and design)
        - Implementation phase (core execution)
        - Validation phase (testing and verification)
        """
        # Heuristic: Complex issues typically benefit from a three-phase approach:
        # 1. Planning/Analysis phase - understand what needs to be done
        # 2. Implementation phase - do the core work
        # 3. Validation phase - ensure it works correctly

        planning_task = SubIssue(
            title=f"Plan approach for: {title}",
            description=f"""**Objective**: Analyze this complex issue and create a detailed implementation plan.

**Original Issue**:
{content}

**Your Intelligence Task**: 
Use your understanding to break down what needs to be done. Consider:

- What are the core requirements and goals?
- What files, components, or systems need to be created/modified?
- What's the logical sequence of implementation steps?
- What dependencies exist between different parts?
- What could go wrong and how to handle edge cases?
- How will we know when it's complete?

**Heuristic Guidance**:
- Look for numbered sections, bullet points, or step indicators
- Identify file paths, code snippets, or technical specifications  
- Notice Current/Required patterns or before/after descriptions
- Spot integration points with existing systems
- Consider user experience and validation needs

**Output Expected**:
Create a clear, actionable plan that subsequent tasks can follow:
1. Specific files/components to create or modify
2. Implementation order with rationale
3. Key technical decisions and approaches
4. Testing and validation strategy
5. Definition of success

**Success Criteria**:
- Plan addresses all requirements from the original issue
- Implementation steps are specific and actionable
- Dependencies and risks are identified
- Success measures are clear and testable""",
            assignee="code_review_agent",
            priority="high",
            type="planning",
        )

        implementation_task = SubIssue(
            title=f"Implement core functionality: {title}",
            description=f"""**Objective**: Execute the implementation plan to build the required functionality.

**Context**: 
{content}

**Your Intelligence Task**:
Following the planning task output, implement the core functionality using your programming knowledge:

- Understand the requirements deeply from both the original issue and the plan
- Write clean, maintainable, well-structured code
- Follow existing patterns and conventions in the codebase
- Handle edge cases and error conditions appropriately
- Add proper documentation and comments where needed

**Heuristic Guidance**:
- Review the implementation plan first to understand the approach
- Start with core functionality before edge cases
- Test your implementation as you build
- Ensure integration with existing systems
- Follow security and performance best practices

**Implementation Approach**:
1. Review and understand the planning task output
2. Set up any necessary scaffolding or structure
3. Implement core functionality step by step
4. Add error handling and edge case management
5. Ensure code quality and maintainability
6. Document any important implementation decisions

**Success Criteria**:
- All core functionality from requirements is implemented
- Code follows project standards and best practices
- Implementation is robust with proper error handling
- Integration points work correctly with existing systems
- Code is well-documented and maintainable""",
            assignee="issue_fixer_agent",
            priority="medium",
            type="implementation",
            dependencies=["Plan approach"],
        )

        validation_task = SubIssue(
            title=f"Validate and test: {title}",
            description=f"""**Objective**: Thoroughly validate that the implementation meets all requirements and works correctly.

**Context**:
{content}

**Your Intelligence Task**:
Use your testing knowledge to comprehensively validate the implementation:

- Test all functionality end-to-end from user perspective
- Verify edge cases and error conditions are handled properly
- Ensure integration with existing systems works smoothly
- Validate user experience meets expectations
- Check for performance issues or regressions
- Confirm security considerations are addressed

**Heuristic Guidance**:
- Review what was implemented against original requirements
- Create test scenarios covering normal and edge cases
- Test integration points and data flows
- Validate user workflows and experience
- Check for performance, security, and reliability

**Validation Approach**:
1. Review implementation against original requirements
2. Create comprehensive test scenarios and test data
3. Execute functional testing of all features
4. Test error conditions and edge cases
5. Validate integration and user experience
6. Performance and security validation if applicable
7. Document any issues found and verify fixes

**Success Criteria**:
- All functionality works as specified in requirements
- Edge cases and error conditions are handled properly
- No regressions in existing functionality
- User experience is smooth and intuitive
- Performance is acceptable for expected usage
- Implementation is ready for production use""",
            assignee="qa_agent",
            priority="medium",
            type="validation",
            dependencies=["Implement core functionality"],
        )

        return [planning_task, implementation_task, validation_task]

    def _enterprise_strategy(self, content: str, title: str) -> List[SubIssue]:
        """
        Enterprise decomposition following 12-Factor principles:
        - Factor 10: Small, focused agents (atomic tasks)
        - Factor 1: One Codebase (identify specific files/components)
        - Factor 8: Own Your Control Flow (clear dependencies)
        """

        # Extract concrete implementation areas from content
        impl_areas = re.findall(r"[-•]\s+([^\n]+)", content)
        if not impl_areas:
            # Default areas if none specified
            impl_areas = [
                "Core framework",
                "API design",
                "Testing framework",
                "Documentation",
            ]

        sub_issues = []

        # Factor 10: Create small, focused tasks instead of generic phases
        for i, area in enumerate(impl_areas[:6]):  # Limit to 6 for manageability
            area_clean = area.strip().lower()

            # Create specific, actionable task based on area
            if "core" in area_clean or "framework" in area_clean:
                sub_issues.append(
                    SubIssue(
                        title=f"Create {area.strip()} foundation",
                        description=f"""Create foundational structure for {area.strip().lower()}.

## Actionable Steps:
1. Create base classes and interfaces
2. Implement core abstractions
3. Add error handling
4. Write unit tests

## Files to Create/Update:
- core/{area.strip().lower().replace(' ', '_')}.py
- tests/test_{area.strip().lower().replace(' ', '_')}.py

## Definition of Done:
- [ ] Base structure created
- [ ] Tests pass
- [ ] Documentation added""",
                        assignee="issue_fixer_agent",
                        priority="high" if i < 2 else "medium",
                    )
                )

            elif "api" in area_clean or "interface" in area_clean:
                sub_issues.append(
                    SubIssue(
                        title=f"Design and implement {area.strip()}",
                        description=f"""Design and implement {area.strip().lower()} with RESTful patterns.

## Actionable Steps:
1. Define API endpoints and schemas
2. Implement request/response handling
3. Add input validation
4. Create API documentation

## Files to Create/Update:
- api/endpoints.py
- api/schemas.py
- api/validation.py
- docs/api.md

## Definition of Done:
- [ ] API endpoints working
- [ ] Validation implemented
- [ ] Documentation complete""",
                        assignee="issue_fixer_agent",
                        priority="high" if i < 2 else "medium",
                    )
                )

            elif "test" in area_clean:
                sub_issues.append(
                    SubIssue(
                        title=f"Implement {area.strip().lower()} with coverage",
                        description=f"""Create comprehensive {area.strip().lower()} with coverage reporting.

## Actionable Steps:
1. Set up test framework configuration
2. Create test utilities and fixtures
3. Implement integration tests
4. Add coverage reporting

## Files to Create/Update:
- tests/conftest.py
- tests/integration/test_system.py
- .github/workflows/test.yml
- pyproject.toml (test config)

## Definition of Done:
- [ ] Test framework configured
- [ ] Coverage >80%
- [ ] CI/CD integration working""",
                        assignee="testing_agent",
                        priority="medium",
                    )
                )

            elif "doc" in area_clean:
                sub_issues.append(
                    SubIssue(
                        title=f"Create {area.strip().lower()} with examples",
                        description=f"""Create comprehensive {area.strip().lower()} with practical examples.

## Actionable Steps:
1. Write getting started guide
2. Create API reference
3. Add code examples
4. Set up documentation site

## Files to Create/Update:
- docs/getting-started.md
- docs/api-reference.md  
- docs/examples/
- docs/README.md

## Definition of Done:
- [ ] Documentation complete
- [ ] Examples working
- [ ] Site generated""",
                        assignee="issue_fixer_agent",
                        priority="low",
                    )
                )

            else:
                # Generic area - make it specific
                sub_issues.append(
                    SubIssue(
                        title=f"Implement {area.strip()} module",
                        description=f"""Implement {area.strip()} as a focused module following 12-Factor principles.

## Actionable Steps:
1. Define clear interfaces
2. Implement core functionality  
3. Add error handling
4. Create tests

## Files to Create/Update:
- src/{area.strip().lower().replace(' ', '_')}.py
- tests/test_{area.strip().lower().replace(' ', '_')}.py

## Definition of Done:
- [ ] Module implemented
- [ ] Tests passing
- [ ] Integration verified""",
                        assignee="issue_fixer_agent",
                        priority="medium",
                    )
                )

        return sub_issues

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "issue_content": {"type": "string"},
                "complexity": {"type": "string"},
                "issue_title": {"type": "string"},
            },
            "required": ["issue_content", "complexity"],
        }


class SubIssueCreatorTool(Tool):
    """Create actual issue files for sub-issues"""

    def __init__(self):
        super().__init__(
            name="create_sub_issues",
            description="Create issue files for decomposed sub-issues",
        )

    def execute(self, sub_issues: List[Dict], parent_issue_num: str) -> ToolResponse:
        """Create issue files for sub-issues"""
        try:
            created_issues = []
            issues_dir = Path("issues")

            # Find next available issue numbers
            existing_nums = set()
            for issue_file in issues_dir.glob("*.md"):
                match = re.match(r"(\d+)", issue_file.stem)
                if match:
                    existing_nums.add(int(match.group(1)))

            next_num = max(existing_nums) + 1 if existing_nums else 1

            for i, sub_issue in enumerate(sub_issues):
                issue_num = str(next_num + i).zfill(3)
                filename = f"{issue_num}-{sub_issue['title'].lower().replace(' ', '-').replace(':', '')[:30]}.md"
                file_path = issues_dir / filename

                # Create issue content
                content = f"""# Issue #{issue_num}: {sub_issue['title']}

## Description
{sub_issue['description']}

## Parent Issue
{parent_issue_num}

## Type
{sub_issue['type']}

## Priority
{sub_issue['priority']}

## Status
open

## Assignee
{sub_issue['assignee']}
"""

                if sub_issue.get("target_file"):
                    content += f"\n## Target File\n{sub_issue['target_file']}\n"

                if sub_issue.get("dependencies"):
                    deps = ", ".join(
                        f"#{parent_issue_num.zfill(3)}-{d}"
                        for d in sub_issue["dependencies"]
                    )
                    content += f"\n## Dependencies\n{deps}\n"

                file_path.write_text(content)
                created_issues.append(
                    {
                        "issue_number": issue_num,
                        "file_path": str(file_path),
                        "title": sub_issue["title"],
                        "assignee": sub_issue["assignee"],
                    }
                )

            return ToolResponse(
                success=True,
                data={
                    "created_issues": created_issues,
                    "total_created": len(created_issues),
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "sub_issues": {"type": "array"},
                "parent_issue_num": {"type": "string"},
            },
            "required": ["sub_issues", "parent_issue_num"],
        }


class IssueDecomposerAgent(BaseAgent):
    """
    Agent that analyzes complex issues and decomposes them into manageable sub-tasks.
    Based on the hierarchical orchestrator pattern.
    """

    def register_tools(self) -> List[Tool]:
        """Register decomposition tools"""
        return [ComplexityAnalyzerTool(), IssueDecomposerTool(), SubIssueCreatorTool()]

    def execute_task(
        self, task: str, context: Optional[ExecutionContext] = None
    ) -> ToolResponse:
        """
        Analyze and decompose an issue.
        Task format: issue number or path to issue file
        """

        # Find issue file
        if task.isdigit():
            issue_num = task.zfill(3)
            issue_files = list(Path("issues").glob(f"{issue_num}*.md"))
            if not issue_files:
                return ToolResponse(
                    success=False, error=f"No issue file found for #{issue_num}"
                )
            issue_path = issue_files[0]
        else:
            issue_path = Path(task)
            if not issue_path.exists():
                issue_path = Path("issues") / task
                if not issue_path.exists():
                    return ToolResponse(
                        success=False, error=f"Issue file not found: {task}"
                    )

        print(f"\n🧩 Analyzing issue: {issue_path.name}")

        # Read issue content
        issue_content = issue_path.read_text()
        issue_title = re.search(r"# Issue #\d+: (.+)", issue_content)
        title = issue_title.group(1) if issue_title else "Unknown Issue"
        issue_num = re.search(r"# Issue #(\d+)", issue_content)
        num = issue_num.group(1) if issue_num else "000"

        # Step 1: Analyze complexity
        print("🔍 Analyzing complexity...")
        analyzer = self.tools[0]
        complexity_result = analyzer.execute(issue_content)

        if not complexity_result.success:
            return complexity_result

        complexity_data = complexity_result.data
        print(
            f"📊 Complexity: {complexity_data['complexity']} (confidence: {complexity_data['confidence']:.1%})"
        )

        # Step 2: Check if decomposition is needed
        if complexity_data["complexity"] in ["atomic", "simple"]:
            print("✅ Issue is simple enough, no decomposition needed")
            self.state.set(f"issue_{num}_decomposed", False)
            return ToolResponse(
                success=True,
                data={
                    "decomposed": False,
                    "reason": f"Issue complexity is {complexity_data['complexity']}, no decomposition needed",
                    "complexity": complexity_data,
                },
            )

        # Step 3: Decompose the issue
        print(f"🔨 Decomposing {complexity_data['complexity']} issue...")
        decomposer = self.tools[1]
        decompose_result = decomposer.execute(
            issue_content, complexity_data["complexity"], title
        )

        if not decompose_result.success:
            return decompose_result

        sub_issues_data = decompose_result.data
        print(f"📝 Created {sub_issues_data['total_sub_issues']} sub-issues")

        # Step 4: Create sub-issue files
        print("💾 Creating sub-issue files...")
        creator = self.tools[2]
        creation_result = creator.execute(sub_issues_data["sub_issues"], num)

        if not creation_result.success:
            return creation_result

        # Update state
        self.state.set(f"issue_{num}_decomposed", True)
        self.state.set(
            f"issue_{num}_sub_issues", creation_result.data["created_issues"]
        )

        print("✅ Issue decomposition complete!")
        for issue in creation_result.data["created_issues"]:
            print(
                f"   📋 #{issue['issue_number']}: {issue['title']} → {issue['assignee']}"
            )

        return ToolResponse(
            success=True,
            data={
                "decomposed": True,
                "complexity": complexity_data,
                "sub_issues": sub_issues_data,
                "created_files": creation_result.data,
            },
        )

    def _apply_action(self, action: Dict[str, Any]) -> ToolResponse:
        """Apply decomposition action"""
        action_type = action.get("type", "decompose")

        if action_type == "decompose":
            return self.execute_task(action.get("issue", ""))

        return ToolResponse(success=False, error=f"Unknown action type: {action_type}")


# Self-test when run directly
# Usage: uv run agents/issue_decomposer_agent.py
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        issue = sys.argv[1]
    else:
        # Default to testing with issue 064
        issue = "064"

    print(f"🧩 Testing IssueDecomposerAgent with issue #{issue}...")
    agent = IssueDecomposerAgent()

    result = agent.execute_task(issue)

    if result.success:
        print(f"\n✅ Issue #{issue} analysis complete!")
        print(json.dumps(result.data, indent=2))
    else:
        print(f"\n❌ Failed to analyze issue #{issue}: {result.error}")
