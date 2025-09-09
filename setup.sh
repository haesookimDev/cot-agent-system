#!/bin/bash

# CoT Agent System Setup Script
# This script sets up the development environment for the CoT Agent System

set -e

echo "🚀 CoT Agent System Setup"
echo "========================="

# Check if Python 3.13+ is available
echo "🐍 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2 || echo "0.0")
REQUIRED_VERSION="3.13"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.13+ is required. Current version: $PYTHON_VERSION"
    echo "Please install Python 3.13+ and try again."
    exit 1
fi

echo "✅ Python version: $(python3 --version)"

# Check if uv is available (preferred) or fall back to pip
if command -v uv &> /dev/null; then
    echo "📦 Using uv package manager"
    PACKAGE_MANAGER="uv"
elif command -v pip &> /dev/null; then
    echo "📦 Using pip package manager"
    PACKAGE_MANAGER="pip"
else
    echo "❌ Neither uv nor pip found. Please install one of them."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment..."
    if [ "$PACKAGE_MANAGER" = "uv" ]; then
        uv venv
    else
        python3 -m venv .venv
    fi
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
if [ "$PACKAGE_MANAGER" = "uv" ]; then
    uv pip install -e .
    echo "📥 Installing development dependencies..."
    uv pip install -e ".[dev]"
else
    pip install -e .
    echo "📥 Installing development dependencies..."
    pip install -e ".[dev]"
fi

echo "✅ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating environment configuration file..."
    cat > .env << EOF
# OpenAI API Configuration (required for LLM functionality)
# OPENAI_API_KEY=your_openai_api_key_here

# Alternative LLM providers (uncomment to use)
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here

# Agent Configuration
COT_MODEL=gpt-3.5-turbo
COT_TEMPERATURE=0.7
COT_MAX_TOKENS=1000
COT_MAX_ITERATIONS=5
COT_THINKING_DEPTH=3

# Logging
LOG_LEVEL=INFO
EOF
    echo "✅ Environment file created (.env)"
    echo "💡 Edit .env to add your API keys"
else
    echo "✅ Environment file already exists"
fi

# Run tests to verify installation
echo "🧪 Running tests to verify installation..."
if python -m pytest tests/ -v; then
    echo "✅ All tests passed"
else
    echo "⚠️  Some tests failed, but installation completed"
fi

# Display usage information
echo ""
echo "🎉 Setup complete!"
echo ""
echo "📚 Usage:"
echo "  # Activate virtual environment (if not already active)"
echo "  source .venv/bin/activate"
echo ""
echo "  # Run CLI help"
echo "  cot-agent --help"
echo ""
echo "  # Run example (no API keys required)"
echo "  cot-agent example"
echo ""
echo "  # Interactive mode (requires API keys)"
echo "  cot-agent process --interactive"
echo ""
echo "  # Process a single query"
echo "  cot-agent process 'Help me plan my day'"
echo ""
echo "  # Run examples"
echo "  python examples/basic_usage.py"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file to add your API keys"
echo "2. Try the example: cot-agent example"
echo "3. Read the documentation in README.md"
echo ""
echo "💡 For development:"
echo "  # Run tests"
echo "  python -m pytest"
echo ""
echo "  # Format code"
echo "  black src/ tests/ examples/"
echo "  isort src/ tests/ examples/"
echo ""
echo "  # Type checking"
echo "  mypy src/"
