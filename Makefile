#!/usr/bin/env make
# Makefile for Home Assistant Custom Components Development

.PHONY: help setup dev-setup install-hooks format lint test clean check-all commit-check

# Default target
help: ## Show this help message
	@echo "Home Assistant Custom Components Development"
	@echo "============================================="
	@echo ""
	@echo "Available targets:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: dev-setup ## Alias for dev-setup

dev-setup: ## Set up development environment (runs setup-dev.sh)
	@echo "🔧 Setting up development environment..."
	@chmod +x setup-dev.sh
	@./setup-dev.sh

install-deps: ## Install all dependencies from requirements files
	@echo "📦 Installing development dependencies..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@if [ -f "requirements-dev.txt" ]; then \
		.venv/bin/pip install -r requirements-dev.txt; \
	fi
	@if [ -f "requirements.txt" ]; then \
		.venv/bin/pip install -r requirements.txt; \
	fi
	@echo "✅ Dependencies installed!"

install-hooks: ## Install pre-commit hooks only
	@echo "🪝 Installing pre-commit hooks..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@.venv/bin/pre-commit install

format: ## Format all Python code with Black and isort
	@echo "🎨 Formatting Python code..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@.venv/bin/black custom_components/
	@.venv/bin/isort custom_components/

lint: ## Run linting (black check) on Python code
	@echo "🔍 Checking Python code formatting..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@.venv/bin/black --check --diff custom_components/

yaml-lint: ## Lint YAML files
	@echo "📝 Linting YAML files..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@.venv/bin/yamllint .github/

pre-commit: ## Run all pre-commit hooks
	@echo "🚀 Running all pre-commit hooks..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@.venv/bin/pre-commit run --all-files

format-like-precommit: ## Format code exactly like pre-commit hooks do
	@echo "🎨 Formatting code like pre-commit..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@.venv/bin/pre-commit run trailing-whitespace --all-files || true
	@.venv/bin/pre-commit run end-of-file-fixer --all-files || true
	@.venv/bin/pre-commit run isort --all-files || true
	@.venv/bin/pre-commit run black --all-files || true

check-all: format-like-precommit lint yaml-lint ## Run all code quality checks
	@echo "✅ All code quality checks completed!"

commit-check: ## Check if code is ready for commit (runs pre-commit hooks)
	@echo "🔍 Checking if code is ready for commit..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@.venv/bin/pre-commit run --all-files && echo "✅ Code is ready for commit!" || echo "❌ Fix the issues above before committing"

test: ## Run component tests (placeholder for future test implementation)
	@echo "🧪 Running tests..."
	@echo "⚠️  Test implementation coming soon..."

validate-manifests: ## Validate component manifest.json files
	@echo "📋 Validating component manifests..."
	@echo "Switch component manifest:"
	@python -m json.tool custom_components/switch_energy_statistics_estimation/manifest.json > /dev/null && echo "✅ Valid" || echo "❌ Invalid"
	@echo "Energy report component manifest:"
	@python -m json.tool custom_components/energy_generation_report/manifest.json > /dev/null && echo "✅ Valid" || echo "❌ Invalid"

clean: ## Clean up generated files and caches
	@echo "🧹 Cleaning up..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@echo "✅ Cleanup completed!"

reset-env: clean ## Reset development environment (removes .venv)
	@echo "♻️  Resetting development environment..."
	@rm -rf .venv
	@echo "✅ Environment reset! Run 'make setup' to reinstall."

# Development workflow targets
dev-workflow: ## Show recommended development workflow
	@echo "🔄 Recommended Development Workflow"
	@echo "=================================="
	@echo ""
	@echo "1. Initial setup:"
	@echo "   make setup"
	@echo ""
	@echo "2. Before making changes:"
	@echo "   make check-all"
	@echo ""
	@echo "3. After making changes:"
	@echo "   make commit-check"
	@echo ""
	@echo "4. Regular maintenance:"
	@echo "   make format lint"
	@echo ""
	@echo "5. Clean up when needed:"
	@echo "   make clean"

# Quick commands for common tasks
quick-format: ## Quick format (isort then Black)
	@.venv/bin/isort custom_components/ 2>/dev/null || echo "Run 'make setup' first"
	@.venv/bin/black custom_components/ 2>/dev/null || echo "Run 'make setup' first"

quick-lint: ## Quick lint check (black check only)
	@.venv/bin/black --check custom_components/ 2>/dev/null || echo "Run 'make setup' first"
# Version and info targets
version: ## Show component versions
	@echo "📦 Component Versions"
	@echo "===================="
	@echo "Switch Energy Statistics:"
	@grep '"version"' custom_components/switch_energy_statistics_estimation/manifest.json | cut -d'"' -f4
	@echo "Energy Generation Report:"
	@grep '"version"' custom_components/energy_generation_report/manifest.json | cut -d'"' -f4

info: ## Show development environment info
	@echo "ℹ️  Development Environment Info"
	@echo "==============================="
	@echo "Repository: $(shell git remote get-url origin 2>/dev/null || echo 'Not a git repository')"
	@echo "Branch: $(shell git branch --show-current 2>/dev/null || echo 'Not a git repository')"
	@echo "Python: $(shell python3 --version 2>/dev/null || echo 'Python not found')"
	@echo "Virtual Environment: $(shell test -d .venv && echo 'Present' || echo 'Not found - run make setup')"
	@echo "Pre-commit hooks: $(shell test -f .git/hooks/pre-commit && echo 'Installed' || echo 'Not installed')"
	@echo "Components:"
	@echo "  - Switch Energy Statistics: $(shell test -f custom_components/switch_energy_statistics_estimation/manifest.json && echo 'Present' || echo 'Missing')"
	@echo "  - Energy Generation Report: $(shell test -f custom_components/energy_generation_report/manifest.json && echo 'Present' || echo 'Missing')"
