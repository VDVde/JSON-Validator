.PHONY: install install-dev test test-cov lint format clean validate help

PYTHON := python3
PIP := pip

help:
	@echo "VDV463 Validator - Available commands:"
	@echo ""
	@echo "  make install       Install production dependencies"
	@echo "  make install-dev   Install development dependencies"
	@echo "  make test          Run tests"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make lint          Run linters (flake8, mypy)"
	@echo "  make format        Format code (black, isort)"
	@echo "  make clean         Remove generated files"
	@echo "  make validate      Validate example messages"
	@echo ""

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements-dev.txt
	pre-commit install

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	rm -rf dist build *.egg-info
	rm -f *_validation_*.json report.xml
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

validate:
	$(PYTHON) src/vdv463_validator.py tests/fixtures/v1.1/valid/*.json --quiet

validate-strict:
	$(PYTHON) src/vdv463_validator.py tests/fixtures/v1.1/valid/*.json \
		--quiet --fail-level WARNING
