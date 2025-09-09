"""
Tests for Dynamic Context Priming System.

Tests all primer functionality including template rendering, variable handling,
performance tracking, and primer chaining.
"""

import pytest
import tempfile
import json
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.dynamic_primer import DynamicContextPrimer, PrimerResult


class TestDynamicContextPrimer:
    """Test Dynamic Context Priming System"""

    def test_initialization(self):
        """Test primer initialization"""
        primer = DynamicContextPrimer()

        # Should have built-in primers
        assert len(primer.primer_registry) >= 8
        assert "feature_development" in primer.primer_registry
        assert "bug_fix" in primer.primer_registry
        assert "refactoring" in primer.primer_registry
        assert "testing" in primer.primer_registry
        assert "documentation" in primer.primer_registry
        assert "research" in primer.primer_registry
        assert "optimization" in primer.primer_registry
        assert "migration" in primer.primer_registry

    def test_register_custom_primer(self):
        """Test registering custom primer function"""
        primer = DynamicContextPrimer()

        def custom_primer(variables):
            return f"Custom primer with {variables.get('task', 'unknown task')}"

        # Register custom primer
        primer.register_primer("custom", custom_primer)

        # Verify registration
        assert "custom" in primer.primer_registry
        assert primer.primer_registry["custom"] == custom_primer

    def test_feature_development_primer(self):
        """Test feature development primer"""
        primer = DynamicContextPrimer()

        variables = {
            "task_description": "Add user authentication",
            "priority": "High",
            "complexity": "Medium",
            "requirements": ["Login functionality", "Password reset"],
            "project_name": "MyApp",
        }

        result = primer.prime("feature_development", variables)

        assert isinstance(result, PrimerResult)
        assert result.success
        assert "Add user authentication" in result.content
        assert "High" in result.content  # Priority
        assert "Login functionality" in result.content
        assert result.primer_type == "feature_development"
        assert result.generation_time > 0

    def test_bug_fix_primer(self):
        """Test bug fix primer"""
        primer = DynamicContextPrimer()

        variables = {
            "bug_description": "Login fails with invalid credentials",
            "severity": "Critical",
            "symptoms": ["Users cannot log in", "Error 500 returned"],
            "affected_files": ["auth.py", "login.html"],
        }

        result = primer.prime("bug_fix", variables)

        assert result.success
        assert "Login fails with invalid credentials" in result.content
        assert "Critical" in result.content
        assert "Users cannot log in" in result.content
        assert "auth.py" in result.content

    def test_refactoring_primer(self):
        """Test refactoring primer"""
        primer = DynamicContextPrimer()

        variables = {
            "target_description": "User authentication module",
            "objective": "Improve code maintainability",
            "current_issues": ["Duplicate code", "Complex functions"],
            "affected_modules": ["auth.py", "user_manager.py"],
        }

        result = primer.prime("refactoring", variables)

        assert result.success
        assert "User authentication module" in result.content
        assert "Improve code maintainability" in result.content
        assert "Duplicate code" in result.content
        assert "auth.py" in result.content

    def test_testing_primer(self):
        """Test testing primer"""
        primer = DynamicContextPrimer()

        variables = {
            "test_target": "Authentication system",
            "test_type": "Unit and Integration",
            "coverage_goal": "90%",
            "test_areas": ["Login flow", "Password validation", "Session management"],
        }

        result = primer.prime("testing", variables)

        assert result.success
        assert "Authentication system" in result.content
        assert "Unit and Integration" in result.content
        assert "90%" in result.content
        assert "Login flow" in result.content

    def test_documentation_primer(self):
        """Test documentation primer"""
        primer = DynamicContextPrimer()

        variables = {
            "doc_target": "API Documentation",
            "doc_type": "Technical Reference",
            "audience": "Developers",
            "sections": ["Authentication", "User Management", "API Endpoints"],
        }

        result = primer.prime("documentation", variables)

        assert result.success
        assert "API Documentation" in result.content
        assert "Technical Reference" in result.content
        assert "Developers" in result.content
        assert "Authentication" in result.content

    def test_research_primer(self):
        """Test research primer"""
        primer = DynamicContextPrimer()

        variables = {
            "research_goal": "Evaluate authentication frameworks",
            "domain": "Web Security",
            "research_questions": [
                "Which framework is most secure?",
                "Performance comparison",
            ],
            "topics": ["OAuth 2.0", "JWT", "Session-based auth"],
        }

        result = primer.prime("research", variables)

        assert result.success
        assert "Evaluate authentication frameworks" in result.content
        assert "Web Security" in result.content
        assert "Which framework is most secure?" in result.content
        assert "OAuth 2.0" in result.content

    def test_optimization_primer(self):
        """Test optimization primer"""
        primer = DynamicContextPrimer()

        variables = {
            "optimization_target": "Database queries",
            "performance_goal": "Reduce response time by 50%",
            "bottlenecks": ["N+1 queries", "Missing indexes"],
            "current_metrics": {
                "avg_response_time": "500ms",
                "queries_per_request": "15",
            },
        }

        result = primer.prime("optimization", variables)

        assert result.success
        assert "Database queries" in result.content
        assert "Reduce response time by 50%" in result.content
        assert "N+1 queries" in result.content
        assert "500ms" in result.content

    def test_migration_primer(self):
        """Test migration primer"""
        primer = DynamicContextPrimer()

        variables = {
            "migration_type": "Database Migration",
            "source_system": "MySQL",
            "target_system": "PostgreSQL",
            "scope_items": ["User data", "Authentication tables", "Application logs"],
        }

        result = primer.prime("migration", variables)

        assert result.success
        assert "Database Migration" in result.content
        assert "MySQL" in result.content
        assert "PostgreSQL" in result.content
        assert "User data" in result.content

    def test_invalid_primer_type(self):
        """Test handling invalid primer type"""
        primer = DynamicContextPrimer()

        result = primer.prime("nonexistent_primer", {})

        assert not result.success
        assert "Unknown primer type" in result.error_message
        assert result.content == ""

    def test_primer_with_missing_template(self):
        """Test primer when template file is missing"""
        primer = DynamicContextPrimer()

        # Mock template directory to not exist
        with patch.object(Path, "exists", return_value=False):
            result = primer.prime("feature_development", {"task": "test"})

        # Should fall back to built-in primer function
        assert result.success
        assert "test" in result.content

    def test_template_rendering_error(self):
        """Test handling template rendering errors"""
        primer = DynamicContextPrimer()

        # Create invalid template
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("{{ invalid_syntax }}")
            invalid_template = Path(f.name)

        try:
            with patch.object(primer, "_get_template_path") as mock_path:
                mock_path.return_value = invalid_template

                result = primer.prime("feature_development", {})

                # Should fall back to built-in function
                assert result.success  # Built-in function should work

        finally:
            invalid_template.unlink()

    def test_performance_tracking(self):
        """Test performance tracking in primer results"""
        primer = DynamicContextPrimer()

        result = primer.prime("feature_development", {"task": "test task"})

        assert result.generation_time > 0
        assert result.generation_time < 1.0  # Should be fast

    def test_empty_variables(self):
        """Test primer with empty variables"""
        primer = DynamicContextPrimer()

        result = primer.prime("feature_development", {})

        assert result.success
        assert result.content  # Should have default content

    def test_complex_variable_types(self):
        """Test primer with complex variable types"""
        primer = DynamicContextPrimer()

        variables = {
            "requirements": ["Req 1", "Req 2", "Req 3"],
            "metrics": {"cpu": "50%", "memory": "2GB"},
            "config": {"debug": True, "timeout": 30},
            "nested": {"level1": {"level2": "value"}},
        }

        result = primer.prime("feature_development", variables)

        assert result.success
        assert "Req 1" in result.content
        assert "Req 2" in result.content

    def test_primer_chaining(self):
        """Test chaining multiple primers"""
        primer = DynamicContextPrimer()

        # First primer: feature development
        variables1 = {
            "task_description": "Add authentication",
            "requirements": ["Login", "Logout", "Password reset"],
        }

        result1 = primer.prime("feature_development", variables1)
        assert result1.success

        # Second primer: testing (based on feature)
        variables2 = {
            "test_target": "Authentication feature",
            "test_areas": ["Login flow", "Security validation"],
            "base_context": result1.content,  # Chain previous result
        }

        result2 = primer.prime("testing", variables2)
        assert result2.success
        assert "Authentication feature" in result2.content

        # Results should be independent but related
        assert result1.primer_type == "feature_development"
        assert result2.primer_type == "testing"

    def test_template_variable_validation(self):
        """Test that templates handle missing variables gracefully"""
        primer = DynamicContextPrimer()

        # Provide partial variables
        variables = {
            "task_description": "Test task"
            # Missing many optional variables
        }

        result = primer.prime("feature_development", variables)

        assert result.success
        assert "Test task" in result.content
        # Should handle missing variables with defaults

    @pytest.mark.asyncio
    async def test_concurrent_primer_generation(self):
        """Test concurrent primer generation"""
        import asyncio

        primer = DynamicContextPrimer()

        async def generate_primer(primer_type, task_id):
            # Simulate async primer generation
            await asyncio.sleep(0.01)  # Small delay
            return primer.prime(primer_type, {"task": f"task_{task_id}"})

        # Generate multiple primers concurrently
        tasks = [generate_primer("feature_development", i) for i in range(5)]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.success
            assert f"task_{i}" in result.content

    def test_primer_result_serialization(self):
        """Test PrimerResult can be serialized"""
        primer = DynamicContextPrimer()

        result = primer.prime("feature_development", {"task": "test"})

        # Convert to dict
        result_dict = {
            "success": result.success,
            "content": result.content,
            "primer_type": result.primer_type,
            "generation_time": result.generation_time,
            "error_message": result.error_message,
        }

        # Should be JSON serializable
        json_str = json.dumps(result_dict)
        assert json_str

        # Should be deserializable
        decoded = json.loads(json_str)
        assert decoded["success"] == result.success
        assert decoded["primer_type"] == result.primer_type

    def test_primer_registry_immutability(self):
        """Test that primer registry is protected"""
        primer = DynamicContextPrimer()

        original_count = len(primer.primer_registry)

        # Try to modify registry directly (should not affect internal state)
        try:
            # This might work or raise an error depending on implementation
            external_ref = primer.primer_registry
            external_ref["malicious"] = lambda x: "hack"
        except:
            pass  # Expected for protected registries

        # Register proper way
        primer.register_primer("legitimate", lambda x: "good")

        # Should only have the legitimate addition
        assert "legitimate" in primer.primer_registry
        assert len(primer.primer_registry) == original_count + 1

    def test_large_variable_handling(self):
        """Test handling of large variable sets"""
        primer = DynamicContextPrimer()

        # Create large variable set
        large_variables = {f"var_{i}": f"value_{i}" for i in range(100)}
        large_variables.update(
            {
                "task_description": "Large variable test",
                "requirements": [f"req_{i}" for i in range(50)],
            }
        )

        result = primer.prime("feature_development", large_variables)

        assert result.success
        assert "Large variable test" in result.content
        # Should handle large variable sets without issues


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
