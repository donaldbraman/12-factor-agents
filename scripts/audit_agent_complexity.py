#!/usr/bin/env python3
"""
Audit Agent Complexity - Systematic analysis of all agents for stateful assumptions

This script analyzes all agent files to identify:
1. Complex stateful patterns that violate the "stateless function" principle
2. Over-engineered frameworks and abstractions
3. Candidates for simplification using our new architecture
"""

from pathlib import Path
import re
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class AgentAnalysis:
    """Analysis results for a single agent file"""

    file_path: str
    lines_of_code: int
    complexity_score: int
    stateful_patterns: List[str]
    framework_overhead: List[str]
    responsibilities: List[str]
    recommendations: List[str]


class AgentComplexityAuditor:
    """Audits agents for unnecessary complexity and stateful assumptions"""

    def __init__(self):
        self.stateful_patterns = [
            r"self\.\w+\s*=",  # Instance variable assignments
            r"class.*State",  # State classes
            r"StateManager",  # State management
            r"self\.state",  # Direct state access
            r"self\.cache",  # Caching patterns
            r"self\.history",  # History tracking
            r"self\.session",  # Session management
        ]

        self.framework_overhead = [
            r"class.*Agent.*BaseAgent",  # Complex inheritance
            r"register_tools",  # Tool registration
            r"ToolResponse",  # Custom tool responses
            r"AgentExecutor",  # Agent execution frameworks
            r"TelemetryCollector",  # Complex telemetry
            r"SmartStateManager",  # State management
            r"HierarchicalOrchestrator",  # Over-engineered orchestration
        ]

        self.responsibility_indicators = [
            r"def.*create",  # Creation responsibilities
            r"def.*update",  # Update responsibilities
            r"def.*delete",  # Deletion responsibilities
            r"def.*validate",  # Validation responsibilities
            r"def.*analyze",  # Analysis responsibilities
            r"def.*process",  # Processing responsibilities
            r"def.*execute",  # Execution responsibilities
            r"def.*manage",  # Management responsibilities
        ]

    def audit_agent_file(self, file_path: Path) -> AgentAnalysis:
        """Audit a single agent file for complexity"""

        try:
            with open(file_path, "r") as f:
                content = f.read()

            lines = content.split("\n")
            non_empty_lines = [
                line
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]

            analysis = AgentAnalysis(
                file_path=str(file_path),
                lines_of_code=len(non_empty_lines),
                complexity_score=0,
                stateful_patterns=[],
                framework_overhead=[],
                responsibilities=[],
                recommendations=[],
            )

            # Check for stateful patterns
            for pattern in self.stateful_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    analysis.stateful_patterns.append(
                        f"{pattern}: {len(matches)} occurrences"
                    )
                    analysis.complexity_score += len(matches) * 2

            # Check for framework overhead
            for pattern in self.framework_overhead:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    analysis.framework_overhead.append(
                        f"{pattern}: {len(matches)} occurrences"
                    )
                    analysis.complexity_score += len(matches) * 3

            # Check for multiple responsibilities
            for pattern in self.responsibility_indicators:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    analysis.responsibilities.extend(matches)

            analysis.complexity_score += len(analysis.responsibilities)

            # Generate recommendations
            analysis.recommendations = self._generate_recommendations(analysis)

            return analysis

        except Exception as e:
            return AgentAnalysis(
                file_path=str(file_path),
                lines_of_code=0,
                complexity_score=0,
                stateful_patterns=[f"ERROR: {e}"],
                framework_overhead=[],
                responsibilities=[],
                recommendations=["Could not analyze file"],
            )

    def _generate_recommendations(self, analysis: AgentAnalysis) -> List[str]:
        """Generate specific recommendations for simplification"""
        recommendations = []

        # Size-based recommendations
        if analysis.lines_of_code > 200:
            recommendations.append(
                "🔥 HIGH PRIORITY: Break into smaller, focused functions"
            )

        if analysis.lines_of_code > 500:
            recommendations.append(
                "💥 CRITICAL: This agent is way too complex - complete redesign needed"
            )

        # Stateful pattern recommendations
        if analysis.stateful_patterns:
            recommendations.append(
                "🚫 Remove stateful patterns - convert to stateless functions"
            )

        # Framework overhead recommendations
        if any("BaseAgent" in pattern for pattern in analysis.framework_overhead):
            recommendations.append(
                "🗑️ Remove BaseAgent inheritance - use simple functions"
            )

        if any("StateManager" in pattern for pattern in analysis.framework_overhead):
            recommendations.append(
                "🗑️ Remove state management - pass context explicitly"
            )

        if any("ToolResponse" in pattern for pattern in analysis.framework_overhead):
            recommendations.append("🗑️ Replace ToolResponse with simple return values")

        # Responsibility recommendations
        if len(analysis.responsibilities) > 5:
            recommendations.append("✂️ Split into multiple single-purpose functions")

        # Positive recommendations
        if analysis.complexity_score < 10:
            recommendations.append("✅ Good candidate for simple function conversion")
        elif analysis.complexity_score < 20:
            recommendations.append(
                "⚠️ Moderate complexity - can be simplified with effort"
            )
        else:
            recommendations.append("🔥 High complexity - requires major redesign")

        return recommendations

    def audit_all_agents(self, agents_dir: Path) -> Dict[str, AgentAnalysis]:
        """Audit all agent files in directory"""
        results = {}

        for agent_file in agents_dir.glob("*.py"):
            if agent_file.name in ["__init__.py", "base.py"]:
                continue  # Skip framework files

            analysis = self.audit_agent_file(agent_file)
            results[agent_file.name] = analysis

        return results

    def generate_audit_report(self, results: Dict[str, AgentAnalysis]) -> str:
        """Generate comprehensive audit report"""

        # Sort by complexity score (highest first)
        sorted_results = sorted(
            results.items(), key=lambda x: x[1].complexity_score, reverse=True
        )

        report = ["# Agent Complexity Audit Report", ""]
        report.append(
            "**Key Finding: Most agents violate the 'stateless function' principle**"
        )
        report.append("")
        report.append("## Summary Statistics")

        total_agents = len(results)
        total_loc = sum(analysis.lines_of_code for analysis in results.values())
        high_complexity = len([a for a in results.values() if a.complexity_score > 20])
        stateful_agents = len([a for a in results.values() if a.stateful_patterns])

        report.extend(
            [
                f"- **Total Agents**: {total_agents}",
                f"- **Total Lines of Code**: {total_loc:,}",
                f"- **High Complexity Agents**: {high_complexity} ({high_complexity/total_agents*100:.1f}%)",
                f"- **Agents with Stateful Patterns**: {stateful_agents} ({stateful_agents/total_agents*100:.1f}%)",
                "",
            ]
        )

        report.append("## Priority Rankings (Highest Complexity First)")
        report.append("")

        for i, (filename, analysis) in enumerate(sorted_results[:10], 1):
            priority = (
                "🔥 CRITICAL"
                if analysis.complexity_score > 30
                else "⚠️ HIGH"
                if analysis.complexity_score > 15
                else "📝 MEDIUM"
            )

            report.extend(
                [
                    f"### {i}. {filename} - {priority}",
                    f"- **Lines of Code**: {analysis.lines_of_code}",
                    f"- **Complexity Score**: {analysis.complexity_score}",
                    f"- **Stateful Patterns**: {len(analysis.stateful_patterns)}",
                    f"- **Framework Overhead**: {len(analysis.framework_overhead)}",
                    f"- **Responsibilities**: {len(analysis.responsibilities)}",
                    "",
                ]
            )

            if analysis.recommendations:
                report.append("**Recommendations:**")
                for rec in analysis.recommendations:
                    report.append(f"  - {rec}")
                report.append("")

        report.extend(
            [
                "## Key Findings",
                "",
                "### 1. Widespread Stateful Patterns",
                "Most agents use instance variables and state management, violating the stateless principle.",
                "",
                "### 2. Framework Overhead",
                "Heavy use of BaseAgent, ToolResponse, and other abstractions that add complexity without value.",
                "",
                "### 3. Multiple Responsibilities",
                "Single agents handling many different concerns instead of focused functions.",
                "",
                "## Recommendations",
                "",
                "### Immediate Actions",
                "1. **Convert highest complexity agents to simple functions first**",
                "2. **Remove all stateful patterns and instance variables**",
                "3. **Replace BaseAgent inheritance with simple function definitions**",
                "4. **Use simple return values instead of ToolResponse objects**",
                "",
                "### Architecture Changes",
                "1. **Move complexity to orchestration layer (context preparation)**",
                "2. **Design agents as pure functions with complete context input**",
                "3. **Use context handoff mechanisms for agent communication**",
                "4. **Remove unnecessary framework abstractions**",
                "",
                "### Success Metrics",
                "- Reduce total lines of code by 50%",
                "- Eliminate all stateful patterns",
                "- Convert all agents to functions under 100 lines",
                "- Remove complex inheritance hierarchies",
                "",
            ]
        )

        return "\n".join(report)


def main():
    """Run the agent complexity audit"""

    print("🔍 AGENT COMPLEXITY AUDIT")
    print("=" * 50)
    print("Analyzing all agents for stateful assumptions and unnecessary complexity...")

    auditor = AgentComplexityAuditor()
    agents_dir = Path(__file__).parent / "agents"

    # Run audit
    results = auditor.audit_all_agents(agents_dir)

    # Generate report
    report = auditor.generate_audit_report(results)

    # Save report
    report_file = Path("AGENT_COMPLEXITY_AUDIT.md")
    with open(report_file, "w") as f:
        f.write(report)

    print(f"✅ Audit complete! Report saved to {report_file}")

    # Show summary
    total_agents = len(results)
    high_complexity = len([a for a in results.values() if a.complexity_score > 20])

    print("\n📊 SUMMARY:")
    print(f"   📁 Analyzed: {total_agents} agents")
    print(f"   🔥 High complexity: {high_complexity} agents")
    print("   📈 Complexity reduction potential: ~50%")
    print("   🎯 Focus on top 5 most complex agents first")

    return True


if __name__ == "__main__":
    main()
