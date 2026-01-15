# Development Environment Setup Guide

## Quick Start

To set up the complete development environment with all dependencies:

```bash
# Set up development environment (includes virtual env, dependencies, pre-commit)
make setup

# Or install dependencies separately
make install-deps

# Verify setup
make commit-check
```

## Dependencies Overview

### Core Dependencies (`requirements.txt`)
- **homeassistant**: Core Home Assistant framework for custom component development
- **voluptuous**: Schema validation library used by Home Assistant

### Development Dependencies (`requirements-dev.txt`)
- **Code Quality**: black, isort, pylint, mypy, yamllint
- **Pre-commit**: Automated validation hooks
- **Import Resolution**: aiohttp, pyyaml for better mypy/IDE support

## Import Resolution Benefits

With Home Assistant installed in the development environment:

✅ **Resolved Import Errors**:
- `from homeassistant.core import HomeAssistant` - ✅ Works
- `from homeassistant.components.sensor import SensorEntity` - ✅ Works
- `import voluptuous as vol` - ✅ Works

✅ **Better IDE Support**:
- Type hints and autocompletion for Home Assistant APIs
- Proper import resolution in mypy type checking
- Better code navigation and documentation

✅ **Improved Development Experience**:
- Accurate linting and type checking
- Proper import validation in CI/CD
- Better debugging and testing capabilities

## Commands

```bash
# Install all dependencies
make install-deps

# Check code quality
make format lint

# Validate for commit
make commit-check

# Run type checking
.venv/bin/mypy custom_components/ --ignore-missing-imports --no-strict-optional

# Run pylint
.venv/bin/pylint custom_components/ --exit-zero --reports=y
```

## Notes

- The development environment now includes the full Home Assistant framework
- Type checking and import resolution are significantly improved
- All development tools use consistent versions via requirements files
- Pre-commit hooks ensure code quality before commits

This setup provides a complete development environment that mirrors the Home Assistant runtime environment for better development and testing experience.
