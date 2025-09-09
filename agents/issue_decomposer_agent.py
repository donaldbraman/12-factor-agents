"""
IssueDecomposerAgent - Breaks down complex issues into manageable subtasks.
Inspired by the hierarchical orchestrator pattern for intelligent task decomposition.
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse


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
                "###.*1\.",
                "###.*2\.",
                "###.*3\.",  # Numbered sections indicate complexity
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

            # Count file references
            file_refs = len(re.findall(r"[/\w.-]+\.\w+", issue_content))

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
        Moderate decomposition following 12-Factor Agent principles:
        - Factor 10: Small, focused agents (specific file-based tasks)
        - Factor 1: Natural Language to Tool Calls (extract actionable changes)
        - Factor 12: Stateless Reducer (clear input/output per task)
        """

        # Factor 4: Extract structured file information
        files = re.findall(r"([/\w.-]+\.\w+)", content)

        if files:
            # Factor 10: Create focused tasks per file
            sub_issues = []
            for i, file_path in enumerate(set(files)):
                file_name = Path(file_path).name

                # Extract context about this specific file from content
                file_context = ""
                lines = content.split("\n")
                for j, line in enumerate(lines):
                    if file_path in line or file_name in line:
                        # Get surrounding context (3 lines before and after)
                        start = max(0, j - 3)
                        end = min(len(lines), j + 4)
                        file_context = "\n".join(lines[start:end])
                        break

                description = f"""Update {file_name} according to the requirements.

## Target File
{file_path}

## Context from Main Issue
{file_context if file_context else 'General update required based on main issue requirements.'}

## Actionable Steps (Factor 8: Own Your Control Flow)
1. Open and review {file_path}
2. Identify specific sections that need changes
3. Apply the required modifications
4. Verify syntax and functionality
5. Test the changes work as expected

## Definition of Done (Factor 12: Stateless Reducer)
- [ ] File modifications completed
- [ ] No syntax errors introduced
- [ ] Changes align with requirements
- [ ] Integration verified

## Implementation Notes
- Follow existing code style and patterns
- Preserve existing functionality unless explicitly changing it
- Add appropriate error handling if needed"""

                sub_issues.append(
                    SubIssue(
                        title=f"Update {file_name}",
                        description=description,
                        target_file=file_path,
                        assignee="issue_fixer_agent",
                        priority="high" if i == 0 else "medium",
                    )
                )
            return sub_issues
        else:
            # No specific files - break into focused phases following 12-Factor
            return [
                SubIssue(
                    title=f"Plan implementation for {title}",
                    description=f"""Plan the implementation approach for: {title}

## Context
{content.strip()[:400]}{'...' if len(content) > 400 else ''}

## Actionable Steps (Factor 8: Own Your Control Flow)
1. Review all requirements in detail
2. Identify specific files and components to modify
3. Determine the order of implementation
4. Plan testing approach
5. Document the implementation plan

## Definition of Done
- [ ] Implementation plan documented
- [ ] Files and components identified
- [ ] Dependencies mapped
- [ ] Testing plan created

## Output (Factor 4: Structured Outputs)
Create a clear plan that subsequent tasks can follow.""",
                    assignee="code_review_agent",
                    priority="high",
                ),
                SubIssue(
                    title=f"Implement core changes for {title}",
                    description=f"""Implement the main functionality for: {title}

## Prerequisites  
Complete the planning task first to understand the approach.

## Actionable Steps (Factor 8: Own Your Control Flow)
1. Follow the implementation plan from previous task
2. Make the core code changes
3. Ensure proper error handling
4. Maintain code quality standards
5. Document any important changes

## Definition of Done (Factor 12: Stateless Reducer)
- [ ] Core implementation completed
- [ ] Code follows project standards
- [ ] Error handling implemented
- [ ] Changes documented

## Dependencies
- Planning task must be completed first""",
                    assignee="issue_fixer_agent",
                    dependencies=["1"],
                    priority="high",
                ),
                SubIssue(
                    title=f"Test and validate {title}",
                    description=f"""Test and validate the implementation for: {title}

## Prerequisites
Core implementation must be completed.

## Actionable Steps (Factor 8: Own Your Control Flow)
1. Review the implemented changes
2. Create appropriate test cases
3. Run existing tests to ensure no regressions
4. Test the new functionality thoroughly
5. Document test results

## Definition of Done (Factor 12: Stateless Reducer)
- [ ] Test cases created
- [ ] All tests passing
- [ ] No regressions introduced
- [ ] Functionality verified

## Dependencies  
- Core implementation must be completed first""",
                    assignee="testing_agent",
                    dependencies=["2"],
                    priority="medium",
                ),
            ]

    def _complex_strategy(self, content: str, title: str) -> List[SubIssue]:
        """
        Complex decomposition following 12-Factor Agent principles:
        - Factor 10: Small, focused agents (one clear task each)
        - Factor 4: Tools are Structured Outputs (clear, actionable tasks)
        - Factor 8: Own Your Control Flow (explicit step-by-step actions)
        """
        sub_issues = []

        # Look for numbered sections in the issue (like "### 1. Fix CLI Commands")
        sections = re.findall(
            r"###?\s+(\d+\.?\s+[^\n]+)\n(.*?)(?=###?\s+\d+\.|\Z)", content, re.DOTALL
        )

        if sections:
            # Factor 10: Create small, focused tasks for each section
            for i, (section_title, section_content) in enumerate(sections):
                clean_title = re.sub(r"^\d+\.?\s*", "", section_title).strip()

                # Factor 4: Extract structured information
                files = re.findall(r"([/\w.-]+\.\w+)", section_content)
                target_file = files[0] if files else None

                # Extract Current/Should be patterns (Factor 1: Natural Language to Tool Calls)
                current_should_pairs = re.findall(
                    r"Current[^:]*:\s*```([^`]*)```.*?Should be:\s*```([^`]*)```",
                    section_content,
                    re.DOTALL | re.IGNORECASE,
                )

                # Factor 8: Create explicit, actionable description
                if current_should_pairs:
                    old_code, new_code = current_should_pairs[0]
                    description = f"""{clean_title}

## Problem
The current code needs updating to fix functionality.

## Current Code
```
{old_code.strip()}
```

## Required Change
```  
{new_code.strip()}
```

## Actionable Steps (Factor 8: Own Your Control Flow)
1. Locate the target file: {target_file or 'identified file'}
2. Find the current code block
3. Replace with the new implementation
4. Verify the change works correctly

## Definition of Done
- [ ] Code replacement completed
- [ ] No syntax errors
- [ ] Functionality verified

## Files to Update
- {target_file or 'target file from context'}"""
                else:
                    # Extract actionable content from section
                    action_items = re.findall(
                        r"(?:^|\n)[-•*]\s*([^\n]+)", section_content
                    )
                    steps = "\n".join(
                        f"{i+1}. {item.strip()}" for i, item in enumerate(action_items)
                    )

                    description = f"""{clean_title}

## Task Description  
{section_content.strip() if section_content.strip() else f'Complete {clean_title.lower()}'}

## Actionable Steps (Factor 8: Own Your Control Flow)
{steps if steps else f'''1. Analyze requirements for {clean_title.lower()}
2. Implement the necessary changes
3. Test the implementation
4. Update documentation if needed'''}

## Definition of Done
- [ ] Implementation completed
- [ ] Requirements met
- [ ] Testing verified

## Files to Update
- {target_file or 'files identified from requirements'}"""

                # Factor 10: Assign to focused, specialized agents
                content_lower = section_content.lower()
                if "test" in content_lower or "testing" in content_lower:
                    assignee = "testing_agent"
                elif (
                    "readme" in content_lower
                    or "doc" in content_lower
                    or "integration-guide" in content_lower
                    or "documentation" in content_lower
                ):
                    assignee = "issue_fixer_agent"
                elif (
                    "pipeline" in content_lower
                    or "code" in content_lower
                    or "import" in content_lower
                ):
                    assignee = "issue_fixer_agent"
                else:
                    assignee = "issue_fixer_agent"

                sub_issues.append(
                    SubIssue(
                        title=clean_title,
                        description=description,
                        target_file=target_file,
                        assignee=assignee,
                        priority="high" if i < 2 else "medium",
                    )
                )
        else:
            # Factor 10: Break into small, focused tasks instead of generic phases
            # Extract key files and areas from content
            files = list(set(re.findall(r"([/\w.-]+\.\w+)", content)))

            if files:
                # Create focused tasks per file
                for i, file_path in enumerate(files[:4]):  # Limit to 4 files
                    file_name = Path(file_path).name
                    sub_issues.append(
                        SubIssue(
                            title=f"Update {file_name}",
                            description=f"""Update {file_path} according to requirements in: {title}

## Context
Extracted from the main issue requirements.

## Actionable Steps (Factor 8: Own Your Control Flow)
1. Review the main issue requirements for {file_name}
2. Identify specific changes needed
3. Implement the updates
4. Test the changes
5. Verify integration

## Files to Update
- {file_path}

## Definition of Done
- [ ] File updated per requirements
- [ ] No breaking changes introduced
- [ ] Integration verified""",
                            target_file=file_path,
                            assignee="issue_fixer_agent",
                            priority="high" if i < 2 else "medium",
                        )
                    )
            else:
                # Generic fallback - still apply 12-factor principles
                sub_issues.append(
                    SubIssue(
                        title=f"Implement {title}",
                        description=f"""Implement the requirements for: {title}

## Context
{content.strip()[:500]}{'...' if len(content) > 500 else ''}

## Actionable Steps (Factor 8: Own Your Control Flow)
1. Analyze the complete requirements
2. Identify specific files and components to change
3. Implement the necessary changes
4. Test the implementation
5. Verify all requirements are met

## Definition of Done
- [ ] All requirements implemented
- [ ] Testing completed
- [ ] Documentation updated""",
                        assignee="issue_fixer_agent",
                        priority="high",
                    )
                )

        return sub_issues

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

    def execute_task(self, task: str) -> ToolResponse:
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
