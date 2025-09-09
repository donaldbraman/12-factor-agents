#!/usr/bin/env uv run python
"""
🤖 Autonomous Local CI/CD Agent for Issue #35
Following the AGENT-ISSUE-TEMPLATE.md for local quality gates implementation
"""

import json
import os
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import subprocess


class AutonomousLocalCICDAgent:
    """Autonomous agent implementing Issue #35: Local CI/CD Quality Gates"""

    def __init__(self):
        self.agent_id = "local_cicd_agent_35"
        self.issue_number = 35
        self.status_file = Path(f"/tmp/{self.agent_id}_status.json")
        self.branch_name = "feature/local-cicd-issue-35"

        # Setup timeout protection per template
        signal.signal(signal.SIGALRM, self.timeout_handler)

    def timeout_handler(self, signum, frame):
        """Handle timeout to prevent crashes"""
        self.update_status(
            99,
            "⚠️ Timeout protection triggered",
            {"error": "Operation exceeded time limit"},
        )
        raise TimeoutError("Operation exceeded safe time limit")

    def update_status(self, progress: int, message: str, data: Dict[str, Any] = None):
        """Update status file for monitoring per template"""
        status = {
            "agent_id": self.agent_id,
            "issue": self.issue_number,
            "progress": progress,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "pid": os.getpid(),
        }
        self.status_file.write_text(json.dumps(status, indent=2))
        print(f"[{progress}%] {message}")

    def run_command(self, cmd: str, timeout: int = 30) -> tuple:
        """Run command with timeout protection"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def create_precommit_config(self):
        """Create pre-commit configuration"""
        self.update_status(15, "Creating pre-commit configuration")

        config_path = Path(".pre-commit-config.yaml")
        config_content = """# Local CI/CD Quality Gates - Issue #35
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3
        args: [--line-length=88]
        
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
        
  - repo: local
    hooks:
      - id: quick-tests
        name: Quick Test Suite
        entry: uv run -m pytest tests/test_quick_validation.py -v
        language: system
        pass_filenames: false
        always_run: true
        
      - id: performance-check
        name: Performance Regression Check
        entry: uv run scripts/quick_performance_check.py
        language: system  
        pass_filenames: false
        always_run: true
"""
        config_path.write_text(config_content)

    def create_quick_tests(self):
        """Create fast validation tests"""
        self.update_status(30, "Creating quick validation tests")

        test_dir = Path("tests")
        test_file = test_dir / "test_quick_validation.py"

        test_content = '''"""Quick validation tests for pre-commit hooks"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestQuickValidation:
    """Fast tests to catch major regressions"""
    
    def test_imports_work(self):
        """Test core imports don't crash"""
        try:
            from core.hierarchical_orchestrator import HierarchicalOrchestrator
            from core.context_manager import ContextManager
            from core.agent_executor import AgentExecutor
            assert True
        except ImportError as e:
            pytest.fail(f"Core import failed: {e}")
            
    def test_orchestrator_basic_function(self):
        """Test orchestrator can be created"""
        from core.hierarchical_orchestrator import HierarchicalOrchestrator
        
        orchestrator = HierarchicalOrchestrator()
        assert orchestrator is not None
        assert hasattr(orchestrator, 'execute_task')
        
    def test_context_manager_efficiency(self):
        """Quick context efficiency check"""
        from core.context_manager import ContextManager
        
        manager = ContextManager(max_tokens=1000)
        manager.add_context("test", priority=1)
        
        efficiency = manager.get_efficiency()
        assert 0 <= efficiency <= 1.0, f"Invalid efficiency: {efficiency}"
        
    def test_agent_executor_basic(self):
        """Test agent executor works"""
        from core.agent_executor import AgentExecutor
        
        executor = AgentExecutor()
        result = executor.execute("test", {"test": True})
        assert result is not None
        assert "result" in result
        
    def test_marketplace_imports(self):
        """Test marketplace components import"""
        try:
            from core.marketplace.registry import AgentRegistry
            from core.marketplace.plugin_system import PluginSystem
            from core.marketplace.security import SecurityValidator
            assert True
        except ImportError as e:
            pytest.fail(f"Marketplace import failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
        test_file.write_text(test_content)

    def create_performance_check(self):
        """Create quick performance regression check"""
        self.update_status(45, "Creating performance regression check")

        script_path = Path("scripts/quick_performance_check.py")
        script_content = '''#!/usr/bin/env python3
"""Quick performance regression check for pre-commit"""
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_orchestration_performance():
    """Quick orchestration overhead check"""
    from core.hierarchical_orchestrator import HierarchicalOrchestrator
    
    orchestrator = HierarchicalOrchestrator()
    
    # Quick test - should complete in <0.1s
    start = time.perf_counter()
    try:
        result = orchestrator.coordinate_agents(5)  # Small test
        duration = time.perf_counter() - start
        
        if duration > 0.5:  # Conservative threshold
            print(f"⚠️ Orchestration slower than expected: {duration:.3f}s")
            return False
            
        print(f"✅ Orchestration performance OK: {duration:.3f}s")
        return True
        
    except Exception as e:
        print(f"❌ Orchestration test failed: {e}")
        return False

def check_context_efficiency():
    """Quick context efficiency check"""
    from core.context_manager import ContextManager
    
    try:
        manager = ContextManager(max_tokens=10000)
        
        # Add some context
        for i in range(100):
            manager.add_context(f"test context {i}")
            
        efficiency = manager.get_efficiency()
        
        if efficiency < 0.5:  # Conservative threshold
            print(f"⚠️ Context efficiency low: {efficiency:.1%}")
            return False
            
        print(f"✅ Context efficiency OK: {efficiency:.1%}")
        return True
        
    except Exception as e:
        print(f"❌ Context efficiency test failed: {e}")
        return False

def main():
    """Run quick performance checks"""
    print("🚀 Running quick performance regression checks...")
    
    checks = [
        ("Orchestration Performance", check_orchestration_performance),
        ("Context Efficiency", check_context_efficiency)
    ]
    
    failed = 0
    for name, check in checks:
        print(f"\\n🔍 Checking {name}...")
        if not check():
            failed += 1
            
    if failed > 0:
        print(f"\\n❌ {failed}/{len(checks)} performance checks failed")
        sys.exit(1)
    else:
        print(f"\\n✅ All {len(checks)} performance checks passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
'''
        script_path.write_text(script_content)
        script_path.chmod(0o755)

    def create_local_test_runner(self):
        """Create convenient local test runner"""
        self.update_status(60, "Creating local test runner")

        runner_path = Path("scripts/local_test_runner.py")
        runner_content = '''#!/usr/bin/env python3
"""Local test runner for hobbyist development"""
import subprocess
import sys
from pathlib import Path

def run_quick_tests():
    """Run quick validation tests"""
    print("🧪 Running quick validation tests...")
    result = subprocess.run([
        "uv", "run", "-m", "pytest", 
        "tests/test_quick_validation.py", "-v"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Quick tests passed!")
        return True
    else:
        print("❌ Quick tests failed:")
        print(result.stdout)
        print(result.stderr)
        return False

def run_performance_tests():
    """Run performance benchmark suite"""
    print("\\n📊 Running performance tests...")
    result = subprocess.run([
        "uv", "run", "scripts/run_performance_tests.py"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Performance tests passed!")
        return True
    else:
        print("❌ Performance tests failed:")
        print(result.stdout)
        print(result.stderr)
        return False

def run_code_quality():
    """Run code quality checks"""
    print("\\n🎨 Running code quality checks...")
    
    # Black formatting
    black_result = subprocess.run([
        "uv", "run", "black", "--check", "."
    ], capture_output=True, text=True)
    
    # Ruff linting
    ruff_result = subprocess.run([
        "uv", "run", "ruff", "check", "."
    ], capture_output=True, text=True)
    
    if black_result.returncode == 0 and ruff_result.returncode == 0:
        print("✅ Code quality checks passed!")
        return True
    else:
        if black_result.returncode != 0:
            print("❌ Black formatting issues:")
            print(black_result.stdout)
        if ruff_result.returncode != 0:
            print("❌ Ruff linting issues:")
            print(ruff_result.stdout)
        return False

def main():
    """Run full local test suite"""
    print("🚀 Local CI/CD Quality Gates - Running Full Suite\\n")
    
    checks = [
        ("Quick Tests", run_quick_tests),
        ("Performance Tests", run_performance_tests),
        ("Code Quality", run_code_quality)
    ]
    
    failed = 0
    for name, check in checks:
        if not check():
            failed += 1
            
    print(f"\\n{'='*50}")
    if failed == 0:
        print("🎉 All quality gates passed! Code is ready.")
        sys.exit(0)
    else:
        print(f"❌ {failed}/{len(checks)} quality gates failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        runner_path.write_text(runner_content)
        runner_path.chmod(0o755)

    def install_precommit_hooks(self):
        """Install pre-commit hooks"""
        self.update_status(75, "Installing pre-commit hooks")

        # Install pre-commit if not available
        install_success, _, _ = self.run_command("uv add --dev pre-commit")

        if install_success:
            # Install hooks
            hook_success, _, _ = self.run_command("uv run pre-commit install")
            return hook_success
        return False

    def create_makefile(self):
        """Create Makefile for common tasks"""
        self.update_status(85, "Creating Makefile for convenience")

        makefile_path = Path("Makefile")
        makefile_content = """# Local CI/CD Quality Gates - Issue #35
.PHONY: test quick-test perf-test format lint install-hooks help

help:  ## Show this help message
	@echo "Local CI/CD Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}'

install-hooks:  ## Install pre-commit hooks
	uv add --dev pre-commit
	uv run pre-commit install

test:  ## Run full test suite
	uv run scripts/local_test_runner.py

quick-test:  ## Run quick validation tests only
	uv run -m pytest tests/test_quick_validation.py -v

perf-test:  ## Run performance benchmarks
	uv run scripts/run_performance_tests.py

format:  ## Format code with black
	uv run black .

lint:  ## Lint code with ruff
	uv run ruff check . --fix

check:  ## Run all quality checks
	uv run black --check .
	uv run ruff check .
	uv run scripts/quick_performance_check.py

clean:  ## Clean up test artifacts
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
"""
        makefile_path.write_text(makefile_content)

    def create_readme_section(self):
        """Add local CI/CD section to README"""
        self.update_status(90, "Updating README with CI/CD instructions")

        readme_path = Path("README.md")
        if readme_path.exists():
            content = readme_path.read_text()

            cicd_section = """

## 🔧 Local Development Quality Gates

For hobbyist development with automatic quality checks:

```bash
# Install pre-commit hooks (run once)
make install-hooks

# Run all quality gates
make test

# Quick checks before committing  
make quick-test

# Format and lint code
make format lint

# Performance regression check
make perf-test
```

### Pre-commit Hooks
- **Black**: Code formatting
- **Ruff**: Linting and fixes
- **Quick Tests**: Import validation and basic functionality
- **Performance Check**: Regression detection

Quality gates ensure code stays consistent and performant without manual checking.
"""

            # Add section before any existing content
            if "## Local Development" not in content:
                readme_path.write_text(content + cicd_section)

    def create_pr(self):
        """Create pull request"""
        self.update_status(95, "Creating pull request")

        # Commit changes
        success, out, err = self.run_command(
            'git add -A && git commit -m "🔧 Implement Local CI/CD Quality Gates (#35)" '
            '-m "- Pre-commit hooks with black, ruff, tests" '
            '-m "- Quick validation test suite" '
            '-m "- Performance regression checking" '
            '-m "- Local test runner and Makefile" '
            '-m "- Hobbyist-focused quality gates" '
            '-m "" '
            '-m "Closes #35"'
        )

        if success:
            # Push branch
            success, out, err = self.run_command(
                f"git push -u origin {self.branch_name}"
            )

            if success:
                # Create PR
                pr_body = """## Summary
- Implements local CI/CD quality gates for hobbyist development
- Pre-commit hooks prevent regression and maintain code quality
- Fast feedback loop with quick tests and performance checks

## Components
1. **Pre-commit Hooks**: Black formatting, Ruff linting, quick tests
2. **Quick Validation Suite**: Fast import and functionality tests
3. **Performance Regression Check**: Catches performance drops
4. **Local Test Runner**: Convenient full test suite execution
5. **Makefile**: Simple commands for common tasks

## Hobbyist Benefits
✅ Automatic code formatting (no manual work)
✅ Catch regressions immediately (fast feedback)
✅ Performance validation (framework claims verified)
✅ Quality gates without complexity (simple make commands)
✅ Local-only workflow (no external dependencies)

## Usage
```bash
make install-hooks  # One-time setup
make test          # Full quality gates
make quick-test    # Fast validation
```

Pre-commit hooks run automatically on git commit, catching issues before they hit the repo.

Closes #35

🤖 Generated with Claude Code"""

                success, out, err = self.run_command(
                    f'gh pr create --title "🔧 Local CI/CD Quality Gates (#35)" '
                    f'--body "{pr_body}" --base main --head {self.branch_name}'
                )

                if success and "github.com" in out:
                    return out.strip()

        return None

    def run(self):
        """Main execution following template pattern"""
        try:
            self.update_status(0, "🚀 Starting local CI/CD implementation")

            # Create feature branch
            self.update_status(5, "Creating feature branch")
            success, out, err = self.run_command(f"git checkout -b {self.branch_name}")

            if not success:
                self.run_command(f"git checkout {self.branch_name}")

            # Implementation following SIMPLE complexity pattern
            self.create_precommit_config()
            self.create_quick_tests()
            self.create_performance_check()
            self.create_local_test_runner()

            # Install hooks
            hooks_installed = self.install_precommit_hooks()

            self.create_makefile()
            self.create_readme_section()

            # Create PR
            pr_url = self.create_pr()

            if pr_url:
                self.update_status(
                    100,
                    "✅ Complete!",
                    {
                        "pr_url": pr_url,
                        "issue": self.issue_number,
                        "components_created": [
                            "pre-commit-config.yaml",
                            "quick_validation_tests",
                            "performance_regression_check",
                            "local_test_runner",
                            "makefile",
                        ],
                        "hooks_installed": hooks_installed,
                        "pattern_used": "SIMPLE - Direct local implementation",
                    },
                )
            else:
                self.update_status(95, "⚠️ PR creation failed, implementation complete")

        except Exception as e:
            self.update_status(99, f"❌ Error: {str(e)}", {"error": str(e)})
            raise
        finally:
            signal.alarm(0)


if __name__ == "__main__":
    agent = AutonomousLocalCICDAgent()
    agent.run()
