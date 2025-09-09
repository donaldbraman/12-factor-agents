"""
Simple primer functions for Dynamic Context Priming System.
Used as fallback when template files are not available or fail to render.
"""


def _prime_feature_development(variables):
    """Generate feature development primer content"""
    # Handle both 'task_description' and 'task' variables
    task = variables.get(
        "task_description", variables.get("task", "Feature development task")
    )
    priority = variables.get("priority", "Medium")
    requirements = variables.get("requirements", [])

    content = "# Feature Development Context\n\n"
    content += f"**Task:** {task}\n"
    content += f"**Priority:** {priority}\n\n"

    if requirements:
        content += "## Requirements:\n"
        for req in requirements:
            content += f"- {req}\n"
        content += "\n"

    content += "## Development Guidelines:\n"
    content += "- Follow 12-factor agent methodology\n"
    content += "- Implement with context preservation\n"
    content += "- Use structured ToolResponse pattern\n"
    content += "- Add comprehensive error handling\n"

    return content


def _prime_bug_fix(variables):
    """Generate bug fix primer content"""
    bug_description = variables.get("bug_description", "Bug fix task")
    severity = variables.get("severity", "Medium")
    symptoms = variables.get("symptoms", [])

    content = "# Bug Fix Context\n\n"
    content += f"**Issue:** {bug_description}\n"
    content += f"**Severity:** {severity}\n\n"

    if symptoms:
        content += "## Symptoms:\n"
        for symptom in symptoms:
            content += f"- {symptom}\n"
        content += "\n"

    content += "## Fix Guidelines:\n"
    content += "- Identify root cause\n"
    content += "- Implement minimal fix\n"
    content += "- Add regression tests\n"
    content += "- Verify no side effects\n"

    return content


def _prime_refactoring(variables):
    """Generate refactoring primer content"""
    target = variables.get("target_description", "Refactoring task")
    objective = variables.get("objective", "Code quality improvement")

    content = "# Refactoring Context\n\n"
    content += f"**Target:** {target}\n"
    content += f"**Objective:** {objective}\n\n"

    content += "## Refactoring Guidelines:\n"
    content += "- Make incremental changes\n"
    content += "- Maintain functionality\n"
    content += "- Improve code readability\n"
    content += "- Run tests after each change\n"

    return content


def _prime_testing(variables):
    """Generate testing primer content"""
    test_target = variables.get("test_target", "Testing task")
    test_type = variables.get("test_type", "Unit Tests")
    test_areas = variables.get("test_areas", [])

    content = "# Testing Context\n\n"
    content += f"**Target:** {test_target}\n"
    content += f"**Type:** {test_type}\n\n"

    if test_areas:
        content += "## Test Areas:\n"
        for area in test_areas:
            content += f"- {area}\n"
        content += "\n"

    content += "## Testing Guidelines:\n"
    content += "- Write clear test names\n"
    content += "- Test edge cases\n"
    content += "- Aim for high coverage\n"
    content += "- Use appropriate fixtures\n"

    return content


def _prime_documentation(variables):
    """Generate documentation primer content"""
    doc_target = variables.get("doc_target", "Documentation task")
    doc_type = variables.get("doc_type", "Technical Documentation")
    audience = variables.get("audience", "Developers")

    content = "# Documentation Context\n\n"
    content += f"**Target:** {doc_target}\n"
    content += f"**Type:** {doc_type}\n"
    content += f"**Audience:** {audience}\n\n"

    content += "## Documentation Guidelines:\n"
    content += "- Write clear, concise content\n"
    content += "- Include practical examples\n"
    content += "- Maintain consistent style\n"
    content += "- Update with code changes\n"

    return content


def _prime_research(variables):
    """Generate research primer content"""
    research_goal = variables.get("research_goal", "Research task")
    domain = variables.get("domain", "Software Engineering")
    questions = variables.get("research_questions", [])

    content = "# Research Context\n\n"
    content += f"**Goal:** {research_goal}\n"
    content += f"**Domain:** {domain}\n\n"

    if questions:
        content += "## Research Questions:\n"
        for question in questions:
            content += f"- {question}\n"
        content += "\n"

    content += "## Research Guidelines:\n"
    content += "- Use reliable sources\n"
    content += "- Document findings clearly\n"
    content += "- Validate with experiments\n"
    content += "- Provide actionable insights\n"

    return content


def _prime_optimization(variables):
    """Generate optimization primer content"""
    optimization_target = variables.get("optimization_target", "Optimization task")
    performance_goal = variables.get("performance_goal", "Improve performance")
    bottlenecks = variables.get("bottlenecks", [])

    content = "# Optimization Context\n\n"
    content += f"**Target:** {optimization_target}\n"
    content += f"**Goal:** {performance_goal}\n\n"

    if bottlenecks:
        content += "## Identified Bottlenecks:\n"
        for bottleneck in bottlenecks:
            content += f"- {bottleneck}\n"
        content += "\n"

    content += "## Optimization Guidelines:\n"
    content += "- Profile before optimizing\n"
    content += "- Measure improvements\n"
    content += "- Avoid premature optimization\n"
    content += "- Consider maintainability\n"

    return content


def _prime_migration(variables):
    """Generate migration primer content"""
    migration_type = variables.get("migration_type", "Migration task")
    source = variables.get("source_system", "Legacy System")
    target = variables.get("target_system", "New System")

    content = "# Migration Context\n\n"
    content += f"**Type:** {migration_type}\n"
    content += f"**From:** {source}\n"
    content += f"**To:** {target}\n\n"

    content += "## Migration Guidelines:\n"
    content += "- Plan migration phases\n"
    content += "- Validate data integrity\n"
    content += "- Implement rollback plan\n"
    content += "- Test thoroughly\n"

    return content
