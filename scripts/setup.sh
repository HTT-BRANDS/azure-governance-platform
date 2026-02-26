#!/bin/bash
# Setup script for Azure Governance Platform

set -e

echo "=== Azure Governance Platform Setup ==="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$PYTHON_VERSION" < "3.11" ]]; then
    echo "Error: Python 3.11+ is required. Found: $PYTHON_VERSION"
    exit 1
fi
echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
fi
echo "✓ Virtual environment ready"

# Activate virtual environment
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
uv pip install -e . --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
echo "✓ Dependencies installed"

# Copy .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✓ .env file created - please edit with your Azure credentials"
else
    echo "✓ .env file already exists"
fi

# Create data directory
mkdir -p data
echo "✓ Data directory ready"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your Azure credentials"
echo "  2. Run: uvicorn app.main:app --reload"
echo "  3. Open: http://localhost:8000"
echo ""
