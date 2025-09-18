#!/usr/bin/env python3
"""
SparkyQualityReviewAgent - Pre-Review Quality Gate for Sparky's Output

This agent acts as a quality gate BEFORE code goes to full review.
It catches common Sparky issues and hands back for improvement,
creating a tight feedback loop that drives continuous quality improvement.

The Flywheel:
1. Sparky generates code
2. Quality review catches issues
3. Sparky fixes issues
4. Quality improves
5. Repeat until excellent
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from core.agent import BaseAgent
from core.tools import Tool, ToolResponse
from core.quality_patterns import get_pattern_manager

# Import telemetry learner if available
try:
    from core.telemetry_learner import TelemetryPatternLearner

    HAS_TELEMETRY_LEARNING = True
except ImportError:
    HAS_TELEMETRY_LEARNING = False


class QualityIssue(Enum):
    """Types of quality issues we commonly see"""

    PLACEHOLDER_CODE = "placeholder_code"
    TODO_COMMENTS = "todo_comments"
    EMPTY_IMPLEMENTATION = "empty_implementation"
    WRONG_LOCATION = "wrong_file_location"
    NO_REAL_LOGIC = "no_real_logic"
    MISSING_IMPORTS = "missing_imports"
    NO_ERROR_HANDLING = "no_error_handling"
    NO_ACTUAL_TESTS = "no_actual_tests"
    GENERIC_NAMES = "generic_variable_names"
    NO_DOCSTRINGS = "missing_docstrings"


@dataclass
class QualityFeedback:
    """Structured feedback for improvement"""

    issue_type: QualityIssue
    severity: str  # "critical", "major", "minor"
    location: str  # file:line or general location
    description: str
    suggestion: str
    example: Optional[str] = None


class CodeQualityAnalyzer(Tool):
    """Analyzes code for common Sparky quality issues using pattern database"""

    def __init__(self):
        super().__init__(
            name="analyze_code_quality",
            description="Deep analysis of code quality issues",
        )
        # Use central pattern manager instead of hardcoding
        self.pattern_manager = get_pattern_manager()

        # Use telemetry learner if available
        self.telemetry_learner = None
        if HAS_TELEMETRY_LEARNING:
            try:
                self.telemetry_learner = TelemetryPatternLearner()
            except Exception:
                pass  # Telemetry not available

    def execute(self, file_path: str) -> ToolResponse:
        """Analyze a file for quality issues using pattern database"""

        if not Path(file_path).exists():
            return ToolResponse(success=False, error=f"File not found: {file_path}")

        with open(file_path, "r") as f:
            content = f.read()
            lines = content.split("\n")

        # Use pattern manager to check code quality
        pattern_matches = self.pattern_manager.check_code_quality(content, file_path)

        # Convert pattern matches to quality feedback
        issues = []
        for match in pattern_matches:
            issues.append(
                QualityFeedback(
                    issue_type=self._map_pattern_to_issue_type(match.pattern_name),
                    severity=match.severity,
                    location=match.location,
                    description=match.description,
                    suggestion=match.suggestion,
                    example=None,
                )
            )

        # Also run specific checks that need line-by-line analysis
        issues.extend(self._check_placeholders(content, lines))
        issues.extend(self._check_todos(content, lines))
        issues.extend(self._check_empty_implementations(content, file_path))
        issues.extend(self._check_real_logic(content, file_path))
        issues.extend(self._check_error_handling(content))

        # Check test quality if it's a test file
        if "test_" in Path(file_path).name:
            issues.extend(self._check_test_quality(content, lines))

        # Calculate quality score
        quality_score = self._calculate_quality_score(issues)

        return ToolResponse(
            success=True,
            data={
                "file": file_path,
                "issues": issues,
                "quality_score": quality_score,
                "needs_rework": quality_score < 70,
                "critical_issues": [i for i in issues if i.severity == "critical"],
            },
        )

    def _map_pattern_to_issue_type(self, pattern_name: str) -> QualityIssue:
        """Map pattern name to quality issue type"""
        mapping = {
            "placeholder_code": QualityIssue.PLACEHOLDER_CODE,
            "generic_implementations": QualityIssue.NO_REAL_LOGIC,
            "missing_error_handling": QualityIssue.NO_ERROR_HANDLING,
            "skeletal_tests": QualityIssue.NO_ACTUAL_TESTS,
            "file_placement": QualityIssue.WRONG_LOCATION,
            "learned_pattern": QualityIssue.NO_REAL_LOGIC,
        }
        return mapping.get(pattern_name, QualityIssue.GENERIC_NAMES)

    def _check_placeholders(
        self, content: str, lines: List[str]
    ) -> List[QualityFeedback]:
        """Check for placeholder implementations"""
        issues = []

        placeholder_patterns = [
            (r"pass\s*$", "Empty pass statement"),
            (r"# placeholder", "Placeholder comment"),
            (r"return True\s*#.*placeholder", "Placeholder return"),
            (r"self\.assertTrue\(True", "Placeholder test assertion"),
            (r'""".*TODO.*"""', "TODO in docstring"),
        ]

        for pattern, description in placeholder_patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        QualityFeedback(
                            issue_type=QualityIssue.PLACEHOLDER_CODE,
                            severity="major",
                            location=f"line {i}",
                            description=f"{description} found",
                            suggestion="Replace with actual implementation",
                            example="# Instead of 'pass', implement the actual logic",
                        )
                    )

        return issues

    def _check_todos(self, content: str, lines: List[str]) -> List[QualityFeedback]:
        """Check for TODO comments"""
        issues = []

        for i, line in enumerate(lines, 1):
            if "TODO" in line or "FIXME" in line or "XXX" in line:
                issues.append(
                    QualityFeedback(
                        issue_type=QualityIssue.TODO_COMMENTS,
                        severity="major",
                        location=f"line {i}",
                        description="TODO comment found",
                        suggestion="Implement the TODO item before submitting",
                        example=None,
                    )
                )

        return issues

    def _check_empty_implementations(
        self, content: str, file_path: str
    ) -> List[QualityFeedback]:
        """Check for empty or minimal implementations"""
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function only has pass or minimal implementation
                if len(node.body) == 1:
                    if isinstance(node.body[0], ast.Pass):
                        issues.append(
                            QualityFeedback(
                                issue_type=QualityIssue.EMPTY_IMPLEMENTATION,
                                severity="critical",
                                location=f"{node.name} at line {node.lineno}",
                                description=f"Function '{node.name}' has empty implementation",
                                suggestion="Add actual implementation logic",
                                example=f"def {node.name}():\n    # Add real logic here\n    result = process_data()\n    return result",
                            )
                        )
                    elif isinstance(node.body[0], ast.Return):
                        # Check if it's just returning a constant
                        if isinstance(
                            node.body[0].value, (ast.Constant, ast.NameConstant)
                        ):
                            issues.append(
                                QualityFeedback(
                                    issue_type=QualityIssue.NO_REAL_LOGIC,
                                    severity="major",
                                    location=f"{node.name} at line {node.lineno}",
                                    description=f"Function '{node.name}' only returns a constant",
                                    suggestion="Add actual processing logic",
                                    example=None,
                                )
                            )

        return issues

    def _check_real_logic(self, content: str, file_path: str) -> List[QualityFeedback]:
        """Check if there's actual business logic"""
        issues = []

        # Count meaningful operations
        meaningful_patterns = [
            r"if\s+.*:",  # Conditionals
            r"for\s+.*:",  # Loops
            r"while\s+.*:",  # While loops
            r"\w+\s*=\s*\w+\.",  # Method calls
            r"with\s+.*:",  # Context managers
            r"try:",  # Try blocks
            r"\w+\[.*\]",  # Dictionary/list access
        ]

        meaningful_count = 0
        for pattern in meaningful_patterns:
            meaningful_count += len(re.findall(pattern, content))

        # If very few meaningful operations, it's likely skeletal
        lines_of_code = len(content.split("\n"))
        if lines_of_code > 50 and meaningful_count < 10:
            issues.append(
                QualityFeedback(
                    issue_type=QualityIssue.NO_REAL_LOGIC,
                    severity="critical",
                    location="entire file",
                    description="File lacks meaningful business logic",
                    suggestion="Add actual implementation with conditions, loops, and data processing",
                    example="Add conditional logic, data transformations, API calls, etc.",
                )
            )

        return issues

    def _check_error_handling(self, content: str) -> List[QualityFeedback]:
        """Check for proper error handling"""
        issues = []

        # Count try/except blocks
        try_count = len(re.findall(r"try:", content))

        # Check for functions that should have error handling
        function_count = len(re.findall(r"def\s+\w+", content))

        if function_count > 3 and try_count == 0:
            issues.append(
                QualityFeedback(
                    issue_type=QualityIssue.NO_ERROR_HANDLING,
                    severity="major",
                    location="entire file",
                    description="No error handling found",
                    suggestion="Add try/except blocks for operations that could fail",
                    example="try:\n    result = risky_operation()\nexcept SpecificError as e:\n    handle_error(e)",
                )
            )

        # Check for bare except
        if "except:" in content or "except Exception:" in content:
            issues.append(
                QualityFeedback(
                    issue_type=QualityIssue.NO_ERROR_HANDLING,
                    severity="minor",
                    location="except clause",
                    description="Bare except clause found",
                    suggestion="Catch specific exceptions",
                    example="except (ValueError, TypeError) as e:",
                )
            )

        return issues

    def _check_test_quality(
        self, content: str, lines: List[str]
    ) -> List[QualityFeedback]:
        """Check if tests actually test something"""
        issues = []

        # Check for meaningful assertions
        assertion_patterns = [
            r"self\.assert",
            r"assert\s+",
            r"pytest\.raises",
        ]

        assertion_count = 0
        for pattern in assertion_patterns:
            assertion_count += len(re.findall(pattern, content))

        # Check for placeholder assertions
        placeholder_assertions = len(re.findall(r"self\.assertTrue\(True", content))
        placeholder_assertions += len(re.findall(r"assert True", content))

        if placeholder_assertions > 0:
            issues.append(
                QualityFeedback(
                    issue_type=QualityIssue.NO_ACTUAL_TESTS,
                    severity="critical",
                    location="test methods",
                    description=f"Found {placeholder_assertions} placeholder assertions",
                    suggestion="Replace with actual test assertions",
                    example="self.assertEqual(result.status, 'success')\nself.assertIn('data', result.output)",
                )
            )

        # Check if tests have setup/teardown
        if "setUp" not in content and "setup_method" not in content:
            issues.append(
                QualityFeedback(
                    issue_type=QualityIssue.NO_ACTUAL_TESTS,
                    severity="minor",
                    location="test class",
                    description="No test setup found",
                    suggestion="Add setUp method to initialize test fixtures",
                    example="def setUp(self):\n    self.test_data = create_test_data()",
                )
            )

        return issues

    def _check_generic_names(self, content: str) -> List[QualityFeedback]:
        """Check for generic variable names"""
        issues = []

        generic_patterns = [
            r"\bdata\b\s*=",
            r"\bresult\b\s*=",
            r"\btemp\b\s*=",
            r"\bval\b\s*=",
            r"\bthing\b\s*=",
            r"\bstuff\b\s*=",
        ]

        generic_count = 0
        for pattern in generic_patterns:
            generic_count += len(re.findall(pattern, content))

        if generic_count > 5:
            issues.append(
                QualityFeedback(
                    issue_type=QualityIssue.GENERIC_NAMES,
                    severity="minor",
                    location="variable names",
                    description=f"Found {generic_count} generic variable names",
                    suggestion="Use descriptive variable names",
                    example="user_profile = ... instead of data = ...",
                )
            )

        return issues

    def _calculate_quality_score(self, issues: List[QualityFeedback]) -> int:
        """Calculate overall quality score"""
        if not issues:
            return 100

        score = 100

        for issue in issues:
            if issue.severity == "critical":
                score -= 15
            elif issue.severity == "major":
                score -= 10
            elif issue.severity == "minor":
                score -= 5

        return max(0, score)


class ImprovementSuggester(Tool):
    """Generates specific improvement suggestions"""

    def __init__(self):
        super().__init__(
            name="suggest_improvements",
            description="Generate actionable improvement suggestions",
        )

    def execute(self, quality_analysis: Dict) -> ToolResponse:
        """Generate improvement plan based on quality analysis"""
        issues = quality_analysis.get("issues", [])

        # Group issues by type
        issues_by_type = {}
        for issue in issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)

        # Generate improvement plan
        improvement_plan = []

        # Priority 1: Fix critical issues
        critical_fixes = []
        for issue in issues:
            if issue.severity == "critical":
                critical_fixes.append(
                    {
                        "action": f"Fix {issue.issue_type.value}",
                        "location": issue.location,
                        "suggestion": issue.suggestion,
                        "example": issue.example,
                    }
                )

        if critical_fixes:
            improvement_plan.append(
                {"priority": 1, "category": "Critical Fixes", "items": critical_fixes}
            )

        # Priority 2: Add missing implementations
        if QualityIssue.EMPTY_IMPLEMENTATION in issues_by_type:
            implementation_fixes = []
            for issue in issues_by_type[QualityIssue.EMPTY_IMPLEMENTATION]:
                implementation_fixes.append(
                    {
                        "action": "Implement function",
                        "location": issue.location,
                        "suggestion": issue.suggestion,
                    }
                )

            improvement_plan.append(
                {
                    "priority": 2,
                    "category": "Add Implementations",
                    "items": implementation_fixes,
                }
            )

        # Priority 3: Improve tests
        if QualityIssue.NO_ACTUAL_TESTS in issues_by_type:
            test_improvements = []
            for issue in issues_by_type[QualityIssue.NO_ACTUAL_TESTS]:
                test_improvements.append(
                    {
                        "action": "Improve test",
                        "location": issue.location,
                        "suggestion": issue.suggestion,
                    }
                )

            improvement_plan.append(
                {"priority": 3, "category": "Enhance Tests", "items": test_improvements}
            )

        return ToolResponse(
            success=True,
            data={
                "improvement_plan": improvement_plan,
                "estimated_improvements": len(critical_fixes) + len(issues) // 2,
                "can_auto_fix": self._can_auto_fix(issues_by_type),
            },
        )

    def _can_auto_fix(self, issues_by_type: Dict) -> bool:
        """Determine if issues can be automatically fixed"""
        auto_fixable = [
            QualityIssue.TODO_COMMENTS,
            QualityIssue.GENERIC_NAMES,
            QualityIssue.NO_DOCSTRINGS,
        ]

        for issue_type in issues_by_type:
            if issue_type not in auto_fixable:
                return False

        return True


class SparkyQualityReviewAgent(BaseAgent):
    """
    Pre-review quality gate that catches common issues and drives improvement.

    This creates the quality flywheel:
    1. Review generated code
    2. Identify specific issues
    3. Generate improvement plan
    4. Hand back for fixes
    5. Re-review until quality threshold met
    """

    def __init__(self):
        super().__init__()
        self.analyzer = CodeQualityAnalyzer()
        self.suggester = ImprovementSuggester()
        self.quality_threshold = 70  # Minimum quality score to pass
        self.max_iterations = 3  # Maximum improvement iterations

    def register_tools(self) -> List[Tool]:
        """Register quality review tools"""
        return [self.analyzer, self.suggester]

    def execute_task(self, task: str) -> ToolResponse:
        """
        Review code quality and iterate until acceptable.

        Args:
            task: Path to file or directory to review
        """
        # Parse task to get file path
        file_path = self._extract_file_path(task)

        if not file_path:
            return ToolResponse(
                success=False, error="Could not extract file path from task"
            )

        # Quality improvement loop
        iteration = 0
        quality_history = []

        while iteration < self.max_iterations:
            iteration += 1

            # Analyze current quality
            analysis = self.analyzer.execute(file_path)

            if not analysis.success:
                return analysis

            quality_score = analysis.data["quality_score"]
            quality_history.append(quality_score)

            print(f"\n🔍 Quality Review Iteration {iteration}")
            print(f"   Score: {quality_score}/100")

            # Check if quality is acceptable
            if quality_score >= self.quality_threshold:
                print(
                    f"✅ Quality threshold met! ({quality_score} >= {self.quality_threshold})"
                )
                return ToolResponse(
                    success=True,
                    data={
                        "passed_review": True,
                        "final_score": quality_score,
                        "iterations": iteration,
                        "quality_history": quality_history,
                    },
                )

            # Generate improvement suggestions
            suggestions = self.suggester.execute(analysis.data)

            if not suggestions.success:
                return suggestions

            print(f"   Found {len(analysis.data['issues'])} issues to fix")

            # If we can't improve further, return current state
            if iteration > 1 and quality_history[-1] <= quality_history[-2]:
                print("   ⚠️ Quality not improving, stopping iterations")
                break

            # Hand back for improvement (in real use, this would trigger Sparky)
            handback_result = self._handback_for_improvement(
                file_path, suggestions.data["improvement_plan"]
            )

            if not handback_result:
                break

        # Final review failed to meet threshold
        return ToolResponse(
            success=False,
            data={
                "passed_review": False,
                "final_score": quality_history[-1] if quality_history else 0,
                "iterations": iteration,
                "quality_history": quality_history,
                "blocking_issues": [
                    i for i in analysis.data["issues"] if i.severity == "critical"
                ],
            },
            error=f"Quality score {quality_history[-1]} below threshold {self.quality_threshold}",
        )

    def _extract_file_path(self, task: str) -> Optional[str]:
        """Extract file path from task description"""
        # Look for file path patterns
        if Path(task).exists():
            return task

        # Try to extract from task description
        path_match = re.search(r"(?:file:|path:)\s*(\S+)", task)
        if path_match:
            path = path_match.group(1)
            if Path(path).exists():
                return path

        return None

    def _handback_for_improvement(
        self, file_path: str, improvement_plan: List[Dict]
    ) -> bool:
        """
        Hand back to Sparky for improvement.
        In production, this would trigger Sparky to fix the issues.
        """
        print("\n📝 Improvement Plan:")
        for category in improvement_plan:
            print(f"\n   Priority {category['priority']}: {category['category']}")
            for item in category["items"][:3]:  # Show first 3 items
                print(f"      - {item['action']} at {item['location']}")
                print(f"        {item['suggestion']}")

        # In production, this would trigger Sparky to fix issues
        # For now, return True to simulate improvement
        return True


if __name__ == "__main__":
    # Demo the quality review agent
    reviewer = SparkyQualityReviewAgent()

    # Test with a sample file (would be Sparky's output)
    test_file = "agents/intelligent_issue_agent.py"

    result = reviewer.execute_task(test_file)

    if result.success:
        print("\n✅ Code passed quality review!")
        print(f"   Final score: {result.data['final_score']}/100")
        print(f"   Iterations: {result.data['iterations']}")
    else:
        print("\n❌ Code needs improvement")
        print(f"   Final score: {result.data.get('final_score', 0)}/100")
        if result.data.get("blocking_issues"):
            print(f"   Blocking issues: {len(result.data['blocking_issues'])}")
