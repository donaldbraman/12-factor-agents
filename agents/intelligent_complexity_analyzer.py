"""
Intelligent Complexity Analyzer - Uses agent intelligence instead of keywords
"""

import re
from typing import Dict, Any, Tuple
from enum import Enum

from core.tools import Tool, ToolResponse


class IssueComplexity(Enum):
    """Issue complexity levels"""

    ATOMIC = "atomic"  # Single, trivial change
    SIMPLE = "simple"  # Straightforward fix, one file
    MODERATE = "moderate"  # Multiple files or complex logic
    COMPLEX = "complex"  # Multi-step, requires coordination
    ENTERPRISE = "enterprise"  # System-wide changes


class IntelligentComplexityAnalyzer(Tool):
    """
    Analyzes issue complexity using semantic understanding rather than keywords.
    """

    def __init__(self):
        super().__init__(
            name="intelligent_complexity_analysis",
            description="Analyze issue complexity using intelligent reasoning",
        )

    def execute(self, issue_content: str) -> ToolResponse:
        """
        Intelligently analyze issue complexity using semantic understanding.

        Instead of keyword matching, this:
        1. Understands the actual requirements
        2. Evaluates the scope of changes
        3. Considers dependencies and impacts
        4. Makes intelligent decomposition decisions
        """
        try:
            # Use agent intelligence to understand the issue
            analysis = self._intelligent_analysis(issue_content)

            return ToolResponse(
                success=True,
                data={
                    "complexity": analysis["complexity"],
                    "confidence": analysis["confidence"],
                    "reasoning": analysis["reasoning"],
                    "decomposition_needed": analysis["decomposition_needed"],
                    "recommended_approach": analysis["recommended_approach"],
                    "estimated_effort": analysis["estimated_effort"],
                    "risk_factors": analysis["risk_factors"],
                },
            )

        except Exception as e:
            return ToolResponse(success=False, error=str(e))

    def _intelligent_analysis(self, issue_content: str) -> Dict[str, Any]:
        """
        Use intelligence to understand the issue rather than pattern matching.

        This method should:
        - Understand what the issue is asking for
        - Evaluate the real complexity (not just count keywords)
        - Consider the actual work required
        - Make smart decisions about decomposition
        """

        # Parse the issue to understand its structure
        understanding = self._understand_issue(issue_content)

        # Evaluate the actual work required
        work_assessment = self._assess_required_work(understanding)

        # Determine complexity based on actual understanding
        complexity, confidence = self._determine_intelligent_complexity(
            understanding, work_assessment
        )

        # Decide if decomposition is actually helpful
        decomposition_needed = self._should_decompose(
            complexity, understanding, work_assessment
        )

        # Provide reasoning for the decision
        reasoning = self._generate_reasoning(
            understanding, work_assessment, complexity, decomposition_needed
        )

        return {
            "complexity": complexity.value,
            "confidence": confidence,
            "reasoning": reasoning,
            "decomposition_needed": decomposition_needed,
            "recommended_approach": work_assessment["approach"],
            "estimated_effort": work_assessment["effort"],
            "risk_factors": work_assessment["risks"],
        }

    def _understand_issue(self, issue_content: str) -> Dict[str, Any]:
        """
        Parse and understand the issue semantically.
        """

        # Extract structured sections
        sections = {
            "problem": self._extract_section(
                issue_content, ["problem", "issue", "bug", "description"]
            ),
            "current": self._extract_section(issue_content, ["current", "existing"]),
            "desired": self._extract_section(
                issue_content, ["desired", "should", "expected"]
            ),
            "files": self._extract_file_references(issue_content),
            "code_blocks": self._extract_code_blocks(issue_content),
            "requirements": self._extract_requirements(issue_content),
            "examples": self._identify_examples(issue_content),
        }

        # Understand the intent
        intent = self._determine_intent(sections)

        # Identify if this is documentation, code, or configuration
        change_type = self._identify_change_type(sections)

        # Check if requirements are clear (Current/Should pattern is very clear!)
        has_clear_requirements = bool(sections["requirements"]) or (
            bool(sections["current"]) and bool(sections["desired"])
        )

        return {
            "sections": sections,
            "intent": intent,
            "change_type": change_type,
            "has_clear_requirements": has_clear_requirements,
            "has_examples": bool(sections["examples"]),
            "file_count": len(sections["files"]),
            "has_code_changes": bool(sections["code_blocks"]),
        }

    def _assess_required_work(self, understanding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the actual work required based on understanding.
        """

        work_items = []
        risks = []

        # Documentation changes are usually simple
        if understanding["change_type"] == "documentation":
            if understanding["file_count"] == 1:
                effort = "minimal"
                approach = "direct_edit"
            else:
                effort = "small"
                approach = "sequential_edits"

        # Code changes require more analysis
        elif understanding["change_type"] == "code":
            if understanding["has_code_changes"]:
                # Has before/after examples
                effort = "small"
                approach = "guided_implementation"
            elif understanding["file_count"] > 3:
                effort = "moderate"
                approach = "phased_implementation"
                risks.append("multiple_file_coordination")
            else:
                effort = "small"
                approach = "direct_implementation"

        # Configuration changes
        elif understanding["change_type"] == "configuration":
            effort = "minimal"
            approach = "direct_edit"

        # Mixed or unclear
        else:
            if understanding["has_clear_requirements"]:
                effort = "moderate"
                approach = "requirement_driven"
            else:
                effort = "large"
                approach = "exploratory"
                risks.append("unclear_requirements")

        return {
            "effort": effort,
            "approach": approach,
            "risks": risks,
            "work_items": work_items,
        }

    def _determine_intelligent_complexity(
        self, understanding: Dict[str, Any], work_assessment: Dict[str, Any]
    ) -> Tuple[IssueComplexity, float]:
        """
        Determine complexity based on actual understanding, not keywords.
        """

        # Simple heuristics based on real understanding
        effort = work_assessment["effort"]
        file_count = understanding["file_count"]
        has_risks = len(work_assessment["risks"]) > 0

        # Documentation updates are almost always simple
        if understanding["change_type"] == "documentation":
            if file_count <= 1 and not has_risks:
                return IssueComplexity.SIMPLE, 0.9
            elif file_count <= 3:
                return IssueComplexity.MODERATE, 0.8
            else:
                return IssueComplexity.COMPLEX, 0.7

        # Code changes vary based on scope
        elif understanding["change_type"] == "code":
            if effort == "minimal":
                return IssueComplexity.ATOMIC, 0.9
            elif effort == "small" and file_count <= 2:
                return IssueComplexity.SIMPLE, 0.85
            elif effort == "moderate" or file_count > 2:
                return IssueComplexity.MODERATE, 0.8
            elif has_risks or file_count > 5:
                return IssueComplexity.COMPLEX, 0.75
            else:
                return IssueComplexity.MODERATE, 0.7

        # Configuration is usually simple
        elif understanding["change_type"] == "configuration":
            return IssueComplexity.SIMPLE, 0.9

        # When unclear, be conservative but not excessive
        else:
            if understanding["has_clear_requirements"]:
                return IssueComplexity.MODERATE, 0.6
            else:
                return IssueComplexity.COMPLEX, 0.5

    def _should_decompose(
        self,
        complexity: IssueComplexity,
        understanding: Dict[str, Any],
        work_assessment: Dict[str, Any],
    ) -> bool:
        """
        Intelligently decide if decomposition actually helps.

        Key insight: Don't decompose simple tasks!
        """

        # Never decompose atomic or simple tasks
        if complexity in [IssueComplexity.ATOMIC, IssueComplexity.SIMPLE]:
            return False

        # Documentation rarely benefits from decomposition
        if understanding["change_type"] == "documentation":
            return understanding["file_count"] > 3

        # Only decompose moderate if there are clear separate concerns
        if complexity == IssueComplexity.MODERATE:
            return understanding["file_count"] > 3 or len(work_assessment["risks"]) > 1

        # Complex and enterprise usually benefit from decomposition
        return True

    def _generate_reasoning(
        self,
        understanding: Dict[str, Any],
        work_assessment: Dict[str, Any],
        complexity: IssueComplexity,
        decomposition_needed: bool,
    ) -> str:
        """
        Generate human-readable reasoning for the complexity decision.
        """

        reasoning_parts = []

        # Explain what we understood
        reasoning_parts.append(
            f"This appears to be a {understanding['change_type']} change"
        )

        if understanding["file_count"] > 0:
            reasoning_parts.append(f"affecting {understanding['file_count']} file(s)")

        # Explain complexity decision
        reasoning_parts.append(
            f"The complexity is {complexity.value} because {work_assessment['effort']} effort is required"
        )

        # Explain decomposition decision
        if decomposition_needed:
            reasoning_parts.append(
                "Decomposition recommended to manage separate concerns"
            )
        else:
            reasoning_parts.append("No decomposition needed - can be handled directly")

        return ". ".join(reasoning_parts) + "."

    def _extract_section(self, content: str, markers: list) -> str:
        """Extract content under section markers."""
        for marker in markers:
            pattern = rf"#*\s*{marker}.*?\n(.*?)(?=\n#|\Z)"
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_file_references(self, content: str) -> list:
        """Extract actual file references, not just any word with an extension."""
        # Look for actual file paths, not email or versions
        # Updated pattern to better match file paths
        file_pattern = r"(?:^|[\s\"'/])((?:[./]?[\w/-]+/)?[\w-]+\.(?:py|js|ts|md|txt|json|yaml|yml|toml|cfg|conf|sh|bash|gitignore))(?:$|[\s\"'])"
        matches = re.findall(file_pattern, content, re.MULTILINE)
        # Clean up matches and remove duplicates
        files = []
        for match in matches:
            # Strip leading/trailing whitespace and quotes
            clean_match = match.strip().strip('"').strip("'")
            if clean_match and clean_match not in files:
                files.append(clean_match)
        return files

    def _extract_code_blocks(self, content: str) -> list:
        """Extract code blocks from markdown."""
        pattern = r"```[\w]*\n(.*?)```"
        return re.findall(pattern, content, re.DOTALL)

    def _extract_requirements(self, content: str) -> list:
        """Extract clear requirements or success criteria."""
        requirements = []

        # Look for success criteria section
        criteria_section = self._extract_section(
            content, ["success criteria", "requirements", "acceptance"]
        )
        if criteria_section:
            # Extract bullet points
            requirements.extend(re.findall(r"[-*]\s+(.+)", criteria_section))

        # Look for numbered requirements
        requirements.extend(re.findall(r"\d+\.\s+(.+)", content))

        return requirements

    def _identify_examples(self, content: str) -> list:
        """Identify parts that are examples, not requirements."""
        examples = []

        # Look for example sections
        example_section = self._extract_section(
            content, ["example", "for instance", "e.g."]
        )
        if example_section:
            examples.append(example_section)

        # Look for code blocks marked as examples
        example_blocks = re.findall(
            r"#\s*Example:?\n```[\w]*\n(.*?)```", content, re.DOTALL
        )
        examples.extend(example_blocks)

        return examples

    def _determine_intent(self, sections: Dict[str, Any]) -> str:
        """Determine what the issue is actually asking for."""

        # Check for clear patterns
        if sections["current"] and sections["desired"]:
            return "change"
        elif "bug" in sections.get("problem", "").lower():
            return "fix"
        elif "add" in sections.get("problem", "").lower():
            return "addition"
        elif "document" in sections.get("problem", "").lower():
            return "documentation"
        else:
            return "unknown"

    def _identify_change_type(self, sections: Dict[str, Any]) -> str:
        """Identify if this is documentation, code, or configuration."""

        # Check file extensions
        files = sections.get("files", [])
        if files:
            if any(f.endswith(".md") for f in files):
                return "documentation"
            elif any(f.endswith((".yaml", ".yml", ".toml", ".json")) for f in files):
                return "configuration"
            elif any(f.endswith((".py", ".js", ".ts")) for f in files):
                return "code"

        # Check content
        if sections.get("code_blocks"):
            return "code"
        elif "document" in sections.get("problem", "").lower():
            return "documentation"

        return "unknown"

    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema for tool interface"""
        return {
            "type": "object",
            "properties": {
                "issue_content": {
                    "type": "string",
                    "description": "The issue content to analyze",
                }
            },
            "required": ["issue_content"],
        }
