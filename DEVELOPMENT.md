# Development Guide

This repository contains multiple Home Assistant custom integrations. Follow this guide to set up your development environment.

## Quick Setup with Make

For the fastest setup, use the provided Makefile:

```bash
# Set up complete development environment
make setup

# Or see all available targets
make help
```

## Quick Setup Script

Alternatively, run the setup script directly:

```bash
./setup-dev.sh
```

This will:
- Create a Python virtual environment (.venv)
- Install development dependencies (black, isort, yamllint, pre-commit)
- Set up pre-commit hooks
- Format all existing files

## Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install black isort yamllint pre-commit

# Install pre-commit hooks
pre-commit install
```

## Pre-commit Hooks

The following hooks run automatically on every commit:

### Code Quality
- **Black**: Python code formatting
- **isort**: Import sorting (compatible with Black)

### File Quality
- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline
- **mixed-line-ending**: Fix mixed line endings

### Syntax Validation
- **check-yaml**: Validate YAML files
- **check-json**: Validate JSON files
- **check-toml**: Validate TOML files
- **yamllint**: Advanced YAML linting

### Git Safety
- **check-merge-conflict**: Prevent merge conflict markers
- **check-case-conflict**: Prevent case-sensitive filename conflicts

## Manual Commands

### Using Make Targets

```bash
# Format all Python files
make format

# Lint Python files
make lint

# Lint YAML files
make yaml-lint

# Run all pre-commit hooks
make pre-commit

# Validate component manifests
make validate-manifests

# Clean up generated files
make clean

# Show component versions
make version

# Show environment info
make info
```

### Using Tools Directly

```bash
# Format all Python files
.venv/bin/black custom_components/

# Sort all imports
.venv/bin/isort custom_components/

# Check Python formatting
.venv/bin/black --check --diff custom_components/

# Lint YAML files
.venv/bin/yamllint .github/

# Run all pre-commit hooks
.venv/bin/pre-commit run --all-files

# Run specific hook
.venv/bin/pre-commit run black
```

## Development Workflow

### Using Make (Recommended)

```bash
# 1. Initial setup
make setup

# 2. Check code quality before committing
make commit-check

# 3. Format code
make format

# 4. Run linting
make lint

# 5. Run all quality checks
make check-all

# 6. See available commands
make help
```

### Using Direct Commands

1. **Make changes** to the code
2. **Stage files**: `git add .`
3. **Commit**: `git commit -m "Your message"`
   - Pre-commit hooks run automatically
   - If hooks fail, fix the issues and commit again
4. **Push**: `git push`

## Pre-commit Hook Configuration

The hooks are configured in `.pre-commit-config.yaml`:

- **Python files**: Only runs on `custom_components/*.py`
- **Line length**: 88 characters (Black default)
- **Import style**: Black-compatible with isort
- **YAML linting**: 120 character line limit, relaxed rules

## Skipping Hooks (Not Recommended)

In rare cases, you can skip hooks:

```bash
# Skip all hooks
git commit --no-verify -m "Emergency commit"

# Skip specific hook
SKIP=black git commit -m "Skip black only"
```

## CI/CD Integration

The repository also has GitHub Actions workflows that run the same checks:

- **PR Validation**: Runs on pull requests
- **Release**: Runs on master/main branch pushes

This ensures code quality both locally and in CI/CD.

## Components Structure

```
custom_components/
├── switch_energy_statistics_estimation/    # Switch Energy Component
│   ├── __init__.py
│   ├── manifest.json
│   ├── config_flow.py
│   ├── sensor.py
│   ├── services.py
│   └── hacs.json
└── energy_generation_report/              # Energy Report Component
    ├── __init__.py
    ├── manifest.json
    ├── config_flow.py
    ├── sensor.py
    └── hacs.json
```

Each component is independent with its own:
- Version tracking via component-specific tags
- HACS configuration
- Release artifacts

## Testing Changes

Before submitting a PR:

1. **Run all hooks**: `pre-commit run --all-files`
2. **Test component loading**: Check that Home Assistant can load the components
3. **Verify HACS compatibility**: Check that `hacs.json` files are valid
4. **Check workflows**: Ensure GitHub Actions workflows pass

## Troubleshooting

### Pre-commit Hook Failures

If hooks fail:
1. Read the error messages carefully
2. Fix the reported issues
3. Stage the fixed files: `git add .`
4. Commit again: `git commit -m "Fix formatting"`

### Black vs. Other Formatters

If you use other formatters, they might conflict with Black:
- **isort**: Configured to be Black-compatible
- **autopep8**: May conflict - use Black instead
- **yapf**: May conflict - use Black instead

### Virtual Environment Issues

If you have Python environment issues:
1. Delete `.venv` directory
2. Run `./setup-dev.sh` again
3. Or manually create: `python3 -m venv .venv`
