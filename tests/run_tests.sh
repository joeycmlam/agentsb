#!/bin/bash
# Test runner script for document conversion features

set -e

echo "Running tests for document reading features..."

# Check if we're in the right directory
if [ ! -f "src/document_converter.py" ]; then
    echo "Error: Must be run from the project root directory"
    exit 1
fi

# Install test requirements if needed
echo "Installing test dependencies..."
pip install -q -r tests/requirements-test.txt

# Set up Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the tests
echo "Running unit tests..."
python -m pytest tests/ -v --tb=short

echo "Running security validation tests..."
python -m pytest tests/test_mcp_server.py::TestMcpServerSecurity -v

echo "Running integration tests..."
python -m pytest tests/test_mcp_server.py::TestMcpServerIntegration -v

echo ""
echo "✅ All tests completed successfully!"
echo ""
echo "To run tests manually:"
echo "  python -m pytest tests/test_document_converter.py -v"
echo "  python -m pytest tests/test_mcp_server.py -v"
echo ""
echo "To run with coverage:"
echo "  pip install pytest-cov"
echo "  python -m pytest tests/ --cov=src --cov-report=html"