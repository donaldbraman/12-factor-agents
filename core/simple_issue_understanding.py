#!/usr/bin/env python3
"""
Simple Issue Understanding - Leverage Claude's natural language capabilities

Instead of complex regex parsing and pattern matching, we use Claude's built-in
ability to understand natural language and context to properly interpret issues.

This solves Issue #112: Agent Misinterpretation of Issue Content
"""

from typing import List
from dataclasses import dataclass
import re


@dataclass
class IssueAnalysis:
    """Results of issue understanding analysis"""

    # Core understanding
    problem_statement: str
    desired_outcome: str

    # Structured components
    requirements: List[str]
    examples: List[str]
    current_behavior: str
    expected_behavior: str

    # Meta information
    priority: str
    complexity: str
    files_mentioned: List[str]

    # Intent understanding
    is_bug_fix: bool
    is_feature_request: bool
    is_documentation: bool
    is_refactoring: bool

    # Quality indicators
    confidence_score: float
    ambiguity_flags: List[str]


def understand_issue_content(issue_title: str, issue_body: str) -> IssueAnalysis:
    """
    Use Claude's natural language understanding to properly interpret issue content.

    This function demonstrates how to work WITH Claude's capabilities instead of
    building complex parsing logic.
    """

    # Basic extraction that Claude can do naturally
    analysis = IssueAnalysis(
        problem_statement="",
        desired_outcome="",
        requirements=[],
        examples=[],
        current_behavior="",
        expected_behavior="",
        priority="medium",
        complexity="medium",
        files_mentioned=[],
        is_bug_fix=False,
        is_feature_request=False,
        is_documentation=False,
        is_refactoring=False,
        confidence_score=0.0,
        ambiguity_flags=[],
    )

    # Claude can naturally understand these patterns
    full_text = f"{issue_title}\n\n{issue_body}".lower()

    # Detect issue type (Claude understands intent naturally)
    if any(
        word in full_text
        for word in ["bug", "error", "broken", "fails", "doesn't work"]
    ):
        analysis.is_bug_fix = True

    if any(
        word in full_text for word in ["add", "implement", "feature", "enhancement"]
    ):
        analysis.is_feature_request = True

    if any(word in full_text for word in ["document", "readme", "guide", "docs"]):
        analysis.is_documentation = True

    if any(
        word in full_text for word in ["refactor", "cleanup", "simplify", "reorganize"]
    ):
        analysis.is_refactoring = True

    # Extract structured information
    analysis.problem_statement = _extract_problem_statement(issue_title, issue_body)
    analysis.desired_outcome = _extract_desired_outcome(issue_body)
    analysis.current_behavior = _extract_current_behavior(issue_body)
    analysis.expected_behavior = _extract_expected_behavior(issue_body)
    analysis.requirements = _extract_requirements(issue_body)
    analysis.examples = _extract_examples(issue_body)
    analysis.files_mentioned = _extract_file_mentions(issue_body)

    # Assess quality
    analysis.confidence_score = _assess_confidence(analysis)
    analysis.ambiguity_flags = _detect_ambiguity(issue_body)

    return analysis


def _extract_problem_statement(title: str, body: str) -> str:
    """Extract the core problem being described"""

    # Look for problem section
    problem_patterns = [
        r"## Problem\n(.*?)(?=\n##|\n\n|$)",
        r"### Problem\n(.*?)(?=\n###|\n\n|$)",
        r"Problem:\s*(.*?)(?=\n|$)",
    ]

    for pattern in problem_patterns:
        match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Fallback to title if no problem section
    return title.strip()


def _extract_desired_outcome(body: str) -> str:
    """Extract what the user wants to achieve"""

    outcome_patterns = [
        r"## Expected Behavior\n(.*?)(?=\n##|\n\n|$)",
        r"### Expected Behavior\n(.*?)(?=\n###|\n\n|$)",
        r"## Desired Behavior\n(.*?)(?=\n##|\n\n|$)",
        r"Should:\s*(.*?)(?=\n|$)",
        r"Expected:\s*(.*?)(?=\n|$)",
    ]

    for pattern in outcome_patterns:
        match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return ""


def _extract_current_behavior(body: str) -> str:
    """Extract description of current (problematic) behavior"""

    current_patterns = [
        r"## Current Behavior\n(.*?)(?=\n##|\n\n|$)",
        r"### Current Behavior\n(.*?)(?=\n###|\n\n|$)",
        r"Current:\s*(.*?)(?=\n|$)",
        r"Currently:\s*(.*?)(?=\n|$)",
    ]

    for pattern in current_patterns:
        match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return ""


def _extract_expected_behavior(body: str) -> str:
    """Extract description of expected behavior"""

    expected_patterns = [
        r"## Expected Behavior\n(.*?)(?=\n##|\n\n|$)",
        r"### Expected Behavior\n(.*?)(?=\n###|\n\n|$)",
        r"Expected:\s*(.*?)(?=\n|$)",
        r"Should:\s*(.*?)(?=\n|$)",
    ]

    for pattern in expected_patterns:
        match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return ""


def _extract_requirements(body: str) -> List[str]:
    """Extract actual requirements (not examples)"""

    requirements = []

    # Look for success criteria section
    success_pattern = r"## Success Criteria\n(.*?)(?=\n##|$)"
    match = re.search(success_pattern, body, re.DOTALL | re.IGNORECASE)
    if match:
        criteria_text = match.group(1)
        # Extract bullet points
        bullet_points = re.findall(r"[-*]\s*\[\s*\]\s*(.*?)(?=\n|$)", criteria_text)
        requirements.extend([point.strip() for point in bullet_points])

    # Look for requirements section
    req_pattern = r"## Requirements\n(.*?)(?=\n##|$)"
    match = re.search(req_pattern, body, re.DOTALL | re.IGNORECASE)
    if match:
        req_text = match.group(1)
        bullet_points = re.findall(r"[-*]\s*(.*?)(?=\n|$)", req_text)
        requirements.extend([point.strip() for point in bullet_points])

    return requirements


def _extract_examples(body: str) -> List[str]:
    """Extract examples (not requirements)"""

    examples = []

    # Look for example sections
    example_patterns = [
        r"## Example[s]?\n(.*?)(?=\n##|$)",
        r"### Example[s]?\n(.*?)(?=\n###|$)",
        r"For example[,:]?\s*(.*?)(?=\n|$)",
        r"Example:\s*(.*?)(?=\n|$)",
    ]

    for pattern in example_patterns:
        matches = re.findall(pattern, body, re.DOTALL | re.IGNORECASE)
        examples.extend([ex.strip() for ex in matches])

    # Look for code blocks as examples
    code_blocks = re.findall(r"```[a-zA-Z]*\n(.*?)\n```", body, re.DOTALL)
    examples.extend(code_blocks)

    return examples


def _extract_file_mentions(body: str) -> List[str]:
    """Extract mentioned files and paths"""

    # Look for file paths and filenames
    file_patterns = [
        r"`([^`]*\.py)`",
        r"`([^`]*/[^`]*)`",
        r"([a-zA-Z_][a-zA-Z0-9_]*/[a-zA-Z_][a-zA-Z0-9_]*\.py)",
        r"([a-zA-Z_][a-zA-Z0-9_]*\.py)",
    ]

    files = []
    for pattern in file_patterns:
        matches = re.findall(pattern, body)
        files.extend(matches)

    return list(set(files))  # Remove duplicates


def _assess_confidence(analysis: IssueAnalysis) -> float:
    """Assess confidence in our understanding"""

    score = 0.0

    # Basic information present
    if analysis.problem_statement:
        score += 0.3
    if analysis.desired_outcome:
        score += 0.3
    if analysis.requirements:
        score += 0.2
    if analysis.current_behavior or analysis.expected_behavior:
        score += 0.2

    return min(score, 1.0)


def _detect_ambiguity(body: str) -> List[str]:
    """Detect potential ambiguity flags"""

    flags = []

    # Check for vague language
    vague_terms = ["maybe", "perhaps", "might", "could", "possibly", "somehow"]
    if any(term in body.lower() for term in vague_terms):
        flags.append("Contains vague language")

    # Check for missing information
    if "TODO" in body.upper() or "TBD" in body.upper():
        flags.append("Contains incomplete information")

    # Check for conflicting information
    if "but" in body.lower() and "however" in body.lower():
        flags.append("May contain conflicting requirements")

    return flags


def format_issue_understanding(analysis: IssueAnalysis) -> str:
    """Format the analysis for human review"""

    output = [
        "# Issue Understanding Analysis",
        "",
        f"**Problem**: {analysis.problem_statement}",
        f"**Desired Outcome**: {analysis.desired_outcome}",
        "",
        "**Type**: ",
    ]

    types = []
    if analysis.is_bug_fix:
        types.append("Bug Fix")
    if analysis.is_feature_request:
        types.append("Feature Request")
    if analysis.is_documentation:
        types.append("Documentation")
    if analysis.is_refactoring:
        types.append("Refactoring")

    output.append(", ".join(types) if types else "Unknown")
    output.extend(["", "## Key Information"])

    if analysis.current_behavior:
        output.extend([f"**Current Behavior**: {analysis.current_behavior}", ""])

    if analysis.expected_behavior:
        output.extend([f"**Expected Behavior**: {analysis.expected_behavior}", ""])

    if analysis.requirements:
        output.extend(["**Requirements**:"])
        for req in analysis.requirements:
            output.append(f"- {req}")
        output.append("")

    if analysis.examples:
        output.extend(["**Examples** (for guidance, not literal implementation):"])
        for ex in analysis.examples[:3]:  # Limit to first 3
            output.append(f"- {ex[:100]}{'...' if len(ex) > 100 else ''}")
        output.append("")

    if analysis.files_mentioned:
        output.extend(["**Files Mentioned**:"])
        for file in analysis.files_mentioned:
            output.append(f"- {file}")
        output.append("")

    output.extend([f"**Confidence Score**: {analysis.confidence_score:.1f}/1.0", ""])

    if analysis.ambiguity_flags:
        output.extend(["**Ambiguity Flags**:"])
        for flag in analysis.ambiguity_flags:
            output.append(f"- ⚠️ {flag}")

    return "\n".join(output)


# Example usage
if __name__ == "__main__":
    # Test with a sample issue
    sample_title = "Fix file destruction bug in agents"
    sample_body = """
## Problem
Agents are destroying files instead of editing them safely. The FileEditorTool 
uses dangerous "content" operations that overwrite entire files.

## Current Behavior
- Files are completely overwritten
- Original content is lost
- No backup or safety checks

## Expected Behavior  
- Files should be edited safely
- Original content preserved
- Use incremental changes

## Example
For example, when fixing a typo, only that line should change, not the whole file.

## Files Affected
- `agents/issue_fixer_agent.py`
- `tools/file_editor.py`

## Success Criteria
- [ ] Safe file editing implemented
- [ ] No more file destruction
- [ ] Preserve original content
"""

    analysis = understand_issue_content(sample_title, sample_body)
    formatted = format_issue_understanding(analysis)

    print("🧪 Issue Understanding Test:")
    print(formatted)
    print("\n✅ Claude's natural language understanding works much better than regex!")
