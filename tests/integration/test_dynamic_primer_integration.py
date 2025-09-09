"""
Integration tests for Dynamic Context Priming System.

Tests real-world usage scenarios, CLI integration, template file handling,
and integration with other 12-factor agent components.
"""

import pytest
import tempfile
import json
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.dynamic_primer import DynamicContextPrimer
from core.cli_primer import main as cli_main


class TestDynamicPrimerIntegration:
    """Integration tests for Dynamic Context Priming System"""

    def test_end_to_end_feature_development_workflow(self):
        """Test complete feature development workflow with primer"""
        primer = DynamicContextPrimer()

        # Phase 1: Feature development primer
        feature_variables = {
            "task_description": "Implement user profile management",
            "priority": "High",
            "complexity": "Medium",
            "requirements": [
                "User can view profile",
                "User can edit profile",
                "Profile validation",
                "Profile picture upload",
            ],
            "acceptance_criteria": [
                "Profile page loads under 2 seconds",
                "All fields are validated",
                "Changes are saved automatically",
            ],
            "project_name": "12-Factor Agents",
            "language": "Python",
            "related_files": [
                "core/user_manager.py",
                "api/profile_endpoints.py",
                "tests/test_profile.py",
            ],
        }

        feature_result = primer.prime("feature_development", feature_variables)

        assert feature_result.success
        assert "Implement user profile management" in feature_result.content
        assert "Profile page loads under 2 seconds" in feature_result.content
        assert "core/user_manager.py" in feature_result.content

        # Phase 2: Testing primer for the feature
        testing_variables = {
            "test_target": "User profile management",
            "test_type": "Unit and Integration",
            "coverage_goal": "95%",
            "test_areas": [
                "Profile CRUD operations",
                "Input validation",
                "File upload handling",
                "API endpoint testing",
            ],
            "unit_tests": [
                "test_profile_creation",
                "test_profile_update",
                "test_profile_validation",
            ],
            "integration_tests": [
                "test_profile_api_flow",
                "test_file_upload_integration",
            ],
        }

        testing_result = primer.prime("testing", testing_variables)

        assert testing_result.success
        assert "User profile management" in testing_result.content
        assert "95%" in testing_result.content
        assert "test_profile_creation" in testing_result.content

        # Phase 3: Documentation primer
        doc_variables = {
            "doc_target": "User Profile Management API",
            "doc_type": "API Documentation",
            "audience": "Frontend Developers",
            "sections": [
                "Authentication Requirements",
                "Profile Endpoints",
                "Request/Response Formats",
                "Error Handling",
                "Rate Limiting",
            ],
        }

        doc_result = primer.prime("documentation", doc_variables)

        assert doc_result.success
        assert "User Profile Management API" in doc_result.content
        assert "Frontend Developers" in doc_result.content
        assert "Profile Endpoints" in doc_result.content

        # Verify workflow consistency
        assert all(
            result.generation_time < 1.0
            for result in [feature_result, testing_result, doc_result]
        )

    def test_bug_fix_to_testing_workflow(self):
        """Test bug fix to testing primer workflow"""
        primer = DynamicContextPrimer()

        # Bug fix primer
        bug_variables = {
            "bug_description": "Memory leak in background agent executor",
            "severity": "Critical",
            "issue_id": "#123",
            "symptoms": [
                "Memory usage continuously increases",
                "System becomes unresponsive after 1 hour",
                "Agent cleanup not properly executed",
            ],
            "affected_files": [
                "core/background_executor.py:245",
                "core/apple_silicon_executor.py:156",
            ],
            "proposed_solution": "Implement proper cleanup in executor destructor",
        }

        bug_result = primer.prime("bug_fix", bug_variables)

        # Testing primer for the fix
        testing_variables = {
            "test_target": "Memory leak fix in background executor",
            "test_type": "Memory and Performance",
            "test_areas": [
                "Memory usage monitoring",
                "Agent lifecycle testing",
                "Cleanup verification",
                "Long-running stability",
            ],
            "performance_targets": [
                "Memory usage stays below 100MB",
                "No memory leaks after 1000 agent spawns",
                "Cleanup completes within 1 second",
            ],
        }

        testing_result = primer.prime("testing", testing_variables)

        assert bug_result.success and testing_result.success
        assert "Memory leak in background agent executor" in bug_result.content
        assert "Memory usage monitoring" in testing_result.content

    def test_template_file_integration(self):
        """Test integration with actual template files"""
        primer = DynamicContextPrimer()

        # Verify template files exist
        template_dir = Path("primers/templates")
        assert template_dir.exists(), "Template directory should exist"

        expected_templates = [
            "feature_development.md",
            "bug_fix.md",
            "refactoring.md",
            "testing.md",
            "documentation.md",
            "research.md",
            "optimization.md",
            "migration.md",
        ]

        for template_name in expected_templates:
            template_path = template_dir / template_name
            assert template_path.exists(), f"Template {template_name} should exist"

            # Test template can be loaded and rendered
            content = template_path.read_text()
            assert "Generated by Dynamic Context Primer" in content
            assert "{{" in content or "{%" in content  # Should have Jinja2 syntax

        # Test using template files vs built-in functions
        variables = {"task_description": "Test task"}

        result_with_template = primer.prime("feature_development", variables)
        assert result_with_template.success
        assert "Test task" in result_with_template.content

    def test_cli_create_command(self):
        """Test CLI create command"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test_primer.md"

            # Mock sys.argv for CLI
            test_args = [
                "cli_primer.py",
                "create",
                "feature_development",
                "-v",
                "task_description=Test CLI task",
                "-v",
                "priority=High",
                "-o",
                str(output_file),
            ]

            with patch("sys.argv", test_args):
                result = cli_main()

            assert result == 0  # Success
            assert output_file.exists()

            content = output_file.read_text()
            assert "Test CLI task" in content
            assert "High" in content

    def test_cli_list_command(self):
        """Test CLI list command"""
        test_args = ["cli_primer.py", "list"]

        with patch("sys.argv", test_args):
            # Capture output
            with patch("builtins.print") as mock_print:
                result = cli_main()

        assert result == 0

        # Check that primers were listed
        printed_output = " ".join([str(call) for call in mock_print.call_args_list])
        assert "feature_development" in printed_output
        assert "bug_fix" in printed_output

    def test_cli_interactive_mode(self, monkeypatch):
        """Test CLI interactive mode"""
        inputs = ["1", "TestProject", "Add new feature", "High", "Medium", "n"]
        input_iterator = iter(inputs)

        def mock_input(prompt):
            return next(input_iterator, "")

        monkeypatch.setattr("builtins.input", mock_input)

        test_args = ["cli_primer.py", "interactive"]

        with patch("sys.argv", test_args):
            result = cli_main()

        assert result == 0

    def test_variables_file_integration(self):
        """Test loading variables from JSON file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            variables = {
                "task_description": "JSON file task",
                "priority": "Medium",
                "requirements": ["Req 1", "Req 2"],
                "project_name": "Test Project",
            }
            json.dump(variables, f)
            vars_file = Path(f.name)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_file = Path(tmpdir) / "json_primer.md"

                test_args = [
                    "cli_primer.py",
                    "create",
                    "feature_development",
                    "--variables-file",
                    str(vars_file),
                    "-o",
                    str(output_file),
                ]

                with patch("sys.argv", test_args):
                    result = cli_main()

                assert result == 0
                assert output_file.exists()

                content = output_file.read_text()
                assert "JSON file task" in content
                assert "Medium" in content
                assert "Req 1" in content

        finally:
            vars_file.unlink()

    def test_template_validation_command(self):
        """Test template validation command"""
        # Test with valid template
        template_file = Path("primers/templates/feature_development.md")

        test_args = ["cli_primer.py", "validate", str(template_file)]

        with patch("sys.argv", test_args):
            with patch("builtins.print") as mock_print:
                result = cli_main()

        assert result == 0

        printed_output = " ".join([str(call) for call in mock_print.call_args_list])
        assert "Template syntax is valid" in printed_output

    def test_primer_performance_under_load(self):
        """Test primer performance under load"""
        primer = DynamicContextPrimer()

        # Generate many primers quickly
        results = []
        for i in range(50):
            variables = {
                "task_description": f"Task {i}",
                "priority": "Medium" if i % 2 else "High",
            }
            result = primer.prime("feature_development", variables)
            results.append(result)

        # All should succeed
        assert all(r.success for r in results)

        # Average generation time should be reasonable
        avg_time = sum(r.generation_time for r in results) / len(results)
        assert avg_time < 0.1  # Should be very fast

        # Memory usage should be reasonable
        import psutil

        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        assert memory_mb < 500  # Should not use excessive memory

    def test_multi_primer_workflow_chain(self):
        """Test chaining multiple different primer types"""
        primer = DynamicContextPrimer()

        # Research -> Feature Development -> Testing -> Optimization

        # 1. Research primer
        research_vars = {
            "research_goal": "Evaluate caching strategies",
            "research_questions": [
                "Which caching library performs best?",
                "What are memory vs speed tradeoffs?",
            ],
        }
        research_result = primer.prime("research", research_vars)

        # 2. Feature development based on research
        feature_vars = {
            "task_description": "Implement Redis caching layer",
            "requirements": [
                "Cache frequently accessed data",
                "Implement cache invalidation",
                "Monitor cache hit rates",
            ],
        }
        feature_result = primer.prime("feature_development", feature_vars)

        # 3. Testing for the feature
        testing_vars = {
            "test_target": "Redis caching implementation",
            "test_areas": [
                "Cache hit/miss scenarios",
                "Invalidation logic",
                "Performance benchmarks",
            ],
        }
        testing_result = primer.prime("testing", testing_vars)

        # 4. Optimization primer
        optimization_vars = {
            "optimization_target": "Cache performance",
            "performance_goal": "Sub-millisecond cache access",
            "bottlenecks": ["Network latency", "Serialization overhead"],
        }
        optimization_result = primer.prime("optimization", optimization_vars)

        # All should succeed and be related
        all_results = [
            research_result,
            feature_result,
            testing_result,
            optimization_result,
        ]
        assert all(r.success for r in all_results)

        # Content should be related across primers
        cache_mentions = sum(
            1 for result in all_results if "cach" in result.content.lower()
        )
        assert cache_mentions >= 3  # Most should mention caching

    def test_error_handling_integration(self):
        """Test error handling in various integration scenarios"""
        primer = DynamicContextPrimer()

        # Test with invalid primer type
        result = primer.prime("nonexistent", {"task": "test"})
        assert not result.success
        assert result.error_message

        # Test CLI with invalid primer type
        test_args = ["cli_primer.py", "create", "invalid_primer"]

        with patch("sys.argv", test_args):
            result = cli_main()

        assert result == 1  # Error code

        # Test template validation with missing file
        test_args = ["cli_primer.py", "validate", "nonexistent_template.md"]

        with patch("sys.argv", test_args):
            result = cli_main()

        assert result == 1  # Error code

    def test_concurrent_cli_usage(self):
        """Test concurrent CLI usage scenarios"""
        import concurrent.futures

        def run_cli_create(primer_type, task_id):
            """Run CLI create command with unique task"""
            with tempfile.TemporaryDirectory() as tmpdir:
                output_file = Path(tmpdir) / f"primer_{task_id}.md"

                test_args = [
                    "cli_primer.py",
                    "create",
                    primer_type,
                    "-v",
                    f"task_description=Concurrent task {task_id}",
                    "-o",
                    str(output_file),
                ]

                with patch("sys.argv", test_args):
                    result = cli_main()

                if output_file.exists():
                    content = output_file.read_text()
                    return result, content
                else:
                    return result, ""

        # Run multiple CLI commands concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(run_cli_create, "feature_development", i)
                for i in range(3)
            ]

            results = [future.result() for future in futures]

        # All should succeed
        for result_code, content in results:
            assert result_code == 0
            assert content  # Should have content

    def test_primer_system_with_real_12_factor_workflow(self):
        """Test primer system integration with 12-factor agent workflow"""
        primer = DynamicContextPrimer()

        # Simulate a real 12-factor agent implementation workflow

        # 1. Research existing patterns
        research_vars = {
            "research_goal": "Understand 12-factor agent requirements",
            "domain": "12-Factor Methodology",
            "research_questions": [
                "What are the key principles?",
                "How do we maintain state?",
                "What tools are needed?",
            ],
        }
        research_result = primer.prime("research", research_vars)

        # 2. Feature development for new agent
        feature_vars = {
            "task_description": "Create specialized data analysis agent",
            "requirements": [
                "Follow 12-factor principles",
                "Implement ToolResponse pattern",
                "Support async execution",
                "Include comprehensive logging",
            ],
            "framework": "12-Factor Agents",
            "language": "Python",
        }
        feature_result = primer.prime("feature_development", feature_vars)

        # 3. Testing the implementation
        testing_vars = {
            "test_target": "Data analysis agent",
            "test_type": "Unit, Integration, and E2E",
            "framework": "pytest",
            "test_areas": [
                "Tool registration",
                "Task execution",
                "State management",
                "Error handling",
            ],
        }
        testing_result = primer.prime("testing", testing_vars)

        # Verify 12-factor compliance mentioned
        assert "12-factor" in feature_result.content.lower()
        assert "ToolResponse" in feature_result.content
        assert "pytest" in testing_result.content

        # All primers should complete quickly (12-factor principle: fast startup)
        assert all(
            r.generation_time < 0.5
            for r in [research_result, feature_result, testing_result]
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
