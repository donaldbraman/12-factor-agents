# Local CI/CD Quality Gates - Issue #35
.PHONY: test quick-test perf-test format lint install-hooks help test-cov coverage coverage-html coverage-report

help:  ## Show this help message
	@echo "Local CI/CD Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

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

test-cov:  ## Run tests with coverage
	uv run pytest --cov=agents --cov=core --cov=bin --cov=orchestration \
		--cov-report=term-missing --cov-report=xml --cov-report=html \
		tests/

coverage:  ## Run coverage analysis
	uv run pytest --cov=agents --cov=core --cov=bin --cov=orchestration \
		--cov-report=term-missing tests/

coverage-html:  ## Generate HTML coverage report
	uv run pytest --cov=agents --cov=core --cov=bin --cov=orchestration \
		--cov-report=html tests/
	@echo "HTML coverage report generated in htmlcov/"

coverage-report:  ## Show detailed coverage report
	uv run coverage report --show-missing

clean:  ## Clean up test artifacts
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -f .coverage
