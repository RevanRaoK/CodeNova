#!/bin/bash

# End-to-End and Performance Test Runner
# Runs comprehensive E2E, performance, and security tests

set -e

echo "========================================="
echo "CodeNova E2E and Performance Test Suite"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set PYTHONPATH to include backend directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
echo "PYTHONPATH set to: $(pwd)"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: No virtual environment detected${NC}"
    echo "Consider activating your virtual environment first"
    echo ""
fi

# Function to run tests with timing
run_test_suite() {
    local test_name=$1
    local test_path=$2
    local markers=$3
    
    echo -e "${YELLOW}Running $test_name...${NC}"
    start_time=$(date +%s)
    
    # Run without coverage for E2E tests
    if pytest "$test_path" -m "$markers" -v --tb=short --no-cov 2>/dev/null || \
       pytest "$test_path" -m "$markers" -v --tb=short; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo -e "${GREEN}✓ $test_name completed in ${duration}s${NC}"
        echo ""
        return 0
    else
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo -e "${RED}✗ $test_name failed after ${duration}s${NC}"
        echo ""
        return 1
    fi
}

# Parse command line arguments
RUN_E2E=true
RUN_PERFORMANCE=true
RUN_SECURITY=true
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --e2e-only)
            RUN_PERFORMANCE=false
            RUN_SECURITY=false
            shift
            ;;
        --performance-only)
            RUN_E2E=false
            RUN_SECURITY=false
            shift
            ;;
        --security-only)
            RUN_E2E=false
            RUN_PERFORMANCE=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --e2e-only          Run only E2E tests"
            echo "  --performance-only  Run only performance tests"
            echo "  --security-only     Run only security tests"
            echo "  --verbose           Show detailed output"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Track results
FAILED_SUITES=()

# Run E2E tests
if [ "$RUN_E2E" = true ]; then
    echo "========================================="
    echo "1. End-to-End Tests"
    echo "========================================="
    echo ""
    
    if ! run_test_suite "User Workflows" "tests/e2e/test_user_workflows.py" "e2e"; then
        FAILED_SUITES+=("User Workflows E2E")
    fi
    
    if ! run_test_suite "Admin Workflows" "tests/e2e/test_admin_workflows.py" "e2e"; then
        FAILED_SUITES+=("Admin Workflows E2E")
    fi
fi

# Run Performance tests
if [ "$RUN_PERFORMANCE" = true ]; then
    echo "========================================="
    echo "2. Performance and Load Tests"
    echo "========================================="
    echo ""
    
    echo -e "${YELLOW}Note: Performance tests may take several minutes${NC}"
    echo ""
    
    if ! run_test_suite "Load Testing" "tests/performance/test_load_testing.py" "performance"; then
        FAILED_SUITES+=("Load Testing")
    fi
fi

# Run Security tests
if [ "$RUN_SECURITY" = true ]; then
    echo "========================================="
    echo "3. Security Tests"
    echo "========================================="
    echo ""
    
    if ! run_test_suite "Security Testing" "tests/security/test_security.py" "security"; then
        FAILED_SUITES+=("Security Testing")
    fi
fi

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo ""

if [ ${#FAILED_SUITES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All test suites passed!${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ ${#FAILED_SUITES[@]} test suite(s) failed:${NC}"
    for suite in "${FAILED_SUITES[@]}"; do
        echo -e "${RED}  - $suite${NC}"
    done
    echo ""
    exit 1
fi
