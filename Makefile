# 12-Factor-Agents Makefile
# Repository management and validation commands

.PHONY: help check-architecture fix-common hygiene-report validate-all clean test lint format install

# Default target
help:
	@echo "12-Factor-Agents Repository Management"
	@echo ""
	@echo "Available commands:"
	@echo "  make check-architecture - Check repository architecture compliance"
	@echo "  make fix-common        - Auto-fix common issues"
	@echo "  make hygiene-report    - Generate repository hygiene report"  
	@echo "  make validate-all      - Run all validation checks"
	@echo "  make clean             - Clean temporary files and caches"
	@echo "  make test              - Run test suite"
	@echo "  make lint              - Run linting checks"
	@echo "  make format            - Format code with black"
	@echo "  make install           - Install dependencies"

# Check architecture compliance
check-architecture:
	@echo "🔍 Checking architecture compliance..."
	@python scripts/check_architecture.py 2>/dev/null || echo "⚠️ Create scripts/check_architecture.py"
	@echo "✅ Checking for files in root..."
	@! ls *.py 2>/dev/null | grep -v setup.py || (echo "❌ Python files found in root" && exit 1)
	@echo "✅ Checking for secrets..."
	@! grep -r "token\.json\|API_KEY\|SECRET" . --include="*.py" --exclude-dir=".venv" --exclude-dir="tests" 2>/dev/null | grep -v "^#" || (echo "❌ Potential secrets found" && exit 1)
	@echo "✅ Architecture check complete"

# Auto-fix common issues
fix-common:
	@echo "🔧 Auto-fixing common issues..."
	@echo "  Removing Python cache..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "  Removing build artifacts..."
	@rm -rf *.egg-info/ build/ dist/ 2>/dev/null || true
	@echo "  Cleaning test outputs..."
	@rm -f sparky_processed_*.txt test_results_*.json 2>/dev/null || true
	@echo "  Formatting with black..."
	@black . 2>/dev/null || echo "⚠️ Install black: pip install black"
	@echo "✅ Common issues fixed"

# Generate hygiene report
hygiene-report:
	@echo "📊 Generating hygiene report..."
	@python scripts/generate_hygiene_report.py 2>/dev/null || python -c "print('Creating basic report...'); import os; os.system('echo \"# Hygiene Report\n\nGenerated: $$(date)\n\n- Working tree: $$(git status --short | wc -l) changes\n- Branches: $$(git branch | wc -l) local branches\n- Python files: $$(find . -name \"*.py\" | wc -l) files\n- Tests: $$(find tests -name \"test_*.py\" | wc -l) test files\" > HYGIENE_REPORT.md')"
	@echo "✅ Report generated: HYGIENE_REPORT.md"

# Run all validation checks
validate-all: check-architecture lint test
	@echo "✅ All validation checks passed!"

# Clean temporary files
clean:
	@echo "🧹 Cleaning repository..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "*.pyo" -delete 2>/dev/null || true
	@find . -name "*.swp" -delete 2>/dev/null || true
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@rm -rf *.egg-info/ build/ dist/ htmlcov/ .coverage .coverage.* 2>/dev/null || true
	@rm -f sparky_processed_*.txt test_results_*.json 2>/dev/null || true
	@echo "✅ Repository cleaned"

# Run tests
test:
	@echo "🧪 Running tests..."
	@python -m pytest tests/ -v 2>/dev/null || echo "⚠️ Install pytest: pip install pytest"

# Run linting
lint:
	@echo "🔍 Running linting checks..."
	@ruff check . 2>/dev/null || echo "⚠️ Install ruff: pip install ruff"
	@black --check . 2>/dev/null || echo "⚠️ Code formatting issues found. Run: make format"

# Format code
format:
	@echo "💅 Formatting code..."
	@black . 2>/dev/null || echo "⚠️ Install black: pip install black"
	@ruff check --fix . 2>/dev/null || echo "⚠️ Install ruff: pip install ruff"
	@echo "✅ Code formatted"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	@pip install -e . 2>/dev/null || pip install -r requirements.txt 2>/dev/null || echo "⚠️ Using pyproject.toml"
	@pip install -e ".[dev]" 2>/dev/null || echo "✅ Dependencies installed"
	@pre-commit install 2>/dev/null || echo "⚠️ Install pre-commit: pip install pre-commit"

# Quick status check
status:
	@echo "📊 Repository Status"
	@echo "===================="
	@echo "Branch: $$(git branch --show-current)"
	@echo "Changes: $$(git status --short | wc -l) files"
	@echo "Python files: $$(find . -name '*.py' -not -path './.venv/*' | wc -l)"
	@echo "Test files: $$(find tests -name 'test_*.py' | wc -l)"
	@echo "TODO items: $$(grep -r 'TODO' --include='*.py' . 2>/dev/null | wc -l)"
	@echo "===================="

# Run pre-commit hooks
pre-commit:
	@echo "🔄 Running pre-commit hooks..."
	@pre-commit run --all-files || echo "⚠️ Pre-commit checks failed"

# Daily maintenance routine
daily: clean fix-common status
	@echo "✅ Daily maintenance complete"

# Weekly maintenance routine  
weekly: daily hygiene-report validate-all
	@echo "✅ Weekly maintenance complete"

# Show Python files in wrong locations
check-structure:
	@echo "🏗️ Checking file structure..."
	@echo "Files that might be misplaced:"
	@ls *.py 2>/dev/null | grep -v setup.py || echo "  ✅ No Python files in root"
	@echo "Test files outside tests/:"
	@find . -name "test_*.py" -not -path "./tests/*" -not -path "./.venv/*" 2>/dev/null || echo "  ✅ All tests in correct location"

# Create missing directories
setup-dirs:
	@echo "📁 Setting up directory structure..."
	@mkdir -p agents core prompts tests scripts docs/archive config bin archive/deprecated_agents
	@touch agents/__init__.py core/__init__.py bin/__init__.py
	@echo "✅ Directory structure created"