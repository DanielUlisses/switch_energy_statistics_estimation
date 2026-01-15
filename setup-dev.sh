#!/bin/bash

# Development Environment Setup Script
# Run this script to set up pre-commit hooks and development dependencies

set -e

echo "🔧 Setting up development environment..."

# Check if we're in the right directory
if [ ! -f ".pre-commit-config.yaml" ]; then
    echo "❌ Error: .pre-commit-config.yaml not found. Please run this script from the repository root."
    exit 1
fi

# Check if Python virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install --upgrade pip
pip install black isort yamllint pre-commit

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install

# Run pre-commit on all files to ensure everything is properly formatted
echo "🎨 Running pre-commit on all files..."
pre-commit run --all-files || {
    echo "⚠️  Some files were reformatted. Please review the changes and commit them."
    exit 0
}

echo "✅ Development environment setup complete!"
echo ""
echo "📝 Development workflow:"
echo "  1. Make your changes"
echo "  2. Run 'git add .' to stage files"
echo "  3. Run 'git commit' - pre-commit hooks will automatically run"
echo "  4. If hooks fail, fix the issues and commit again"
echo "  5. Push your changes"
echo ""
echo "🔧 Useful commands:"
echo "  - Run pre-commit manually: pre-commit run --all-files"
echo "  - Format Python files: black custom_components/"
echo "  - Sort imports: isort custom_components/"
echo "  - Format/lint Python: black custom_components/"
