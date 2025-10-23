#!/bin/bash

# Test runner script for CodeNova backend
# This script runs different test suites based on arguments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}CodeNova Backend Test Runner${NC}"
echo "================================"

# Parse arguments
TEST_TYPE=${1:-all}
COVERAGE=${2:-true}

# Function to run tests
run_tests() {
    local marker=$1
    local description=$2
    
    echo -e "\n${YELLOW}Running $description...${NC}"
    
    if [ "$COVERAGE" = "true" ]; then
        python -m pytest -m "$marker" --cov=app --cov-report=term-missing
    else
        python -m pytest -m "$marker"
    fi
}

# Run tests based on type
case $TEST_TYPE in
    unit)
        echo "Running unit tests only..."
        run_tests "unit" "Unit Tests"
        ;;
    
    integration)
        echo "Running integration tests only..."
        run_tests "integration" "Integration Tests"
        ;;
    
    api)
        echo "Running API tests only..."
        run_tests "api" "API Tests"
        ;;
    
    fast)
        echo "Running fast tests (excluding slow tests)..."
        python -m pytest -m "not slow" --cov=app --cov-report=term-missing
        ;;
    
    all)
        echo "Running all tests..."
        
        # Run unit tests
        run_tests "unit" "Unit Tests"
        
        # Run integration tests
        run_tests "integration" "Integration Tests"
        
        # Generate final coverage report
        echo -e "\n${YELLOW}Generating coverage report...${NC}"
        python -m pytest --cov=app --cov-report=html --cov-report=term-missing
        
        echo -e "\n${GREEN}All tests completed!${NC}"
        echo "Coverage report available at: htmlcov/index.html"
        ;;
    
    coverage)
        echo "Running tests with detailed coverage..."
        python -m pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml
        echo -e "\n${GREEN}Coverage reports generated:${NC}"
        echo "  - HTML: htmlcov/index.html"
        echo "  - XML: coverage.xml"
        ;;
    
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo "Usage: $0 [unit|integration|api|fast|all|coverage] [true|false]"
        echo ""
        echo "Test types:"
        echo "  unit        - Run unit tests only"
        echo "  integration - Run integration tests only"
        echo "  api         - Run API tests only"
        echo "  fast        - Run fast tests (exclude slow tests)"
        echo "  all         - Run all tests (default)"
        echo "  coverage    - Run all tests with detailed coverage"
        echo ""
        echo "Coverage (second argument):"
        echo "  true  - Generate coverage report (default)"
        echo "  false - Skip coverage report"
        exit 1
        ;;
esac

# Check if tests passed
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Tests passed successfully!${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Tests failed!${NC}"
    exit 1
fi
