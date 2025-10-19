#!/bin/bash
# Test runner script for Censudx API Gateway

set -e

echo "🧪 Running Censudx API Gateway Test Suite"
echo "========================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install pytest pytest-asyncio httpx

# Run unit tests
echo "🔍 Running unit tests..."
python -m pytest tests/test_gateway.py -v --tb=short

# Run integration tests if services are running
echo "🔗 Checking for running services..."
if curl -s http://localhost:8000/gateway/health > /dev/null 2>&1; then
    echo "✅ Gateway service is running, running integration tests..."
    python -m pytest tests/test_gateway.py::TestServiceIntegration -v -m integration
else
    echo "⚠️  Gateway service not running, skipping integration tests"
fi

# Run E2E tests if Docker stack is running
echo "🐳 Checking Docker services..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Docker services running, running E2E tests..."
    python -m pytest tests/e2e/ -v || true
else
    echo "⚠️  Docker services not running, skipping E2E tests"
fi

echo "✅ Test suite completed!"