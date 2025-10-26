#!/bin/bash
#
# Test Runner Script for Android Crash Monitor
# Runs complete test suite with coverage reporting
#

set -e  # Exit on error

echo "🚀 Android Crash Monitor Test Suite"
echo "===================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install test dependencies
echo "📥 Installing test dependencies..."
pip install -q pytest pytest-cov pytest-xdist pytest-timeout

echo ""
echo "🧪 Running Test Suite..."
echo "========================"
echo ""

# Run different test categories
echo "1️⃣  Running Unit Tests..."
pytest tests/ -m unit -v --tb=short

echo ""
echo "2️⃣  Running Integration Tests..."
pytest tests/ -m integration -v --tb=short

echo ""
echo "3️⃣  Running Feature Tests..."
pytest tests/ -m feature -v --tb=short

echo ""
echo "4️⃣  Running System Tests..."
pytest tests/ -m system -v --tb=short

echo ""
echo "5️⃣  Running Performance Tests (may take longer)..."
pytest tests/ -m performance -v --tb=short --timeout=60

echo ""
echo "📊 Generating Coverage Report..."
echo "================================"
pytest tests/ --cov=src/android_crash_monitor --cov-report=html --cov-report=term-missing -v

echo ""
echo "✅ Test Suite Complete!"
echo ""
echo "📈 Coverage report generated in: htmlcov/index.html"
echo "💡 To view coverage: open htmlcov/index.html"
echo ""
