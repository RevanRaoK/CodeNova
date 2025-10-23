#!/bin/bash

# CodeNova Platform - Comprehensive Test Suite Runner
# This script runs all tests and generates a comprehensive report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${BOLD}${BLUE}================================================================================================${NC}"
echo -e "${BOLD}${BLUE}CODENOVA PLATFORM - COMPREHENSIVE TEST SUITE${NC}"
echo -e "${BOLD}${BLUE}================================================================================================${NC}\n"

# Track overall status
OVERALL_STATUS=0

# Store the root directory
ROOT_DIR="$(pwd)"

# Create test results directory
mkdir -p "${ROOT_DIR}/test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="${ROOT_DIR}/test_results/test_report_${TIMESTAMP}.txt"

echo "Test Report - $(date)" > "$REPORT_FILE"
echo "================================================================================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Function to log results
log_result() {
    echo "$1" | tee -a "$REPORT_FILE"
}

# Function to run tests with error handling
run_test_suite() {
    local test_name="$1"
    local test_command="$2"
    local test_dir="$3"
    
    echo -e "\n${BOLD}${BLUE}Running: ${test_name}${NC}"
    log_result ""
    log_result "================================================================================================"
    log_result "TEST SUITE: ${test_name}"
    log_result "================================================================================================"
    
    if [ -n "$test_dir" ]; then
        cd "$test_dir"
    fi
    
    if eval "$test_command" >> "$REPORT_FILE" 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC} - ${test_name}"
        log_result "STATUS: PASSED"
        if [ -n "$test_dir" ]; then
            cd - > /dev/null
        fi
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} - ${test_name}"
        log_result "STATUS: FAILED"
        OVERALL_STATUS=1
        if [ -n "$test_dir" ]; then
            cd - > /dev/null
        fi
        return 1
    fi
}

# Set test database URL to use a separate test database
export DATABASE_URL="postgresql://postgres:codenova_secure_password@localhost:5432/codenova_test_db"

# Create/recreate test database
echo -e "\n${BOLD}${BLUE}Setting up test database...${NC}"
PGPASSWORD=codenova_secure_password psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS codenova_test_db;" 2>/dev/null || true
PGPASSWORD=codenova_secure_password psql -h localhost -U postgres -c "CREATE DATABASE codenova_test_db;" 2>/dev/null || echo "Test database already exists or couldn't be created"

# 1. Backend Unit Tests
echo -e "\n${BOLD}${YELLOW}[1/6] Backend Unit Tests${NC}"
run_test_suite \
    "Backend Unit Tests" \
    "python -m pytest -v --tb=short --maxfail=10 -x" \
    "backend"

# 2. Backend Integration Tests
echo -e "\n${BOLD}${YELLOW}[2/6] Backend Integration Tests${NC}"
run_test_suite \
    "Backend Integration Tests" \
    "python -m pytest -v --tb=short -k integration" \
    "backend"

# 3. Backend API Tests
echo -e "\n${BOLD}${YELLOW}[3/6] Backend API Endpoint Tests${NC}"
run_test_suite \
    "Backend API Tests" \
    "python -m pytest -v --tb=short test_*_endpoints.py test_*_api.py" \
    "backend"

# 4. Frontend Unit Tests
echo -e "\n${BOLD}${YELLOW}[4/6] Frontend Unit Tests${NC}"
if [ -d "frontend" ]; then
    run_test_suite \
        "Frontend Unit Tests" \
        "npm test -- --run --reporter=verbose" \
        "frontend"
else
    echo -e "${YELLOW}⚠ SKIPPED${NC} - Frontend directory not found"
    log_result "Frontend Unit Tests: SKIPPED (directory not found)"
fi

# 5. Frontend Integration Tests
echo -e "\n${BOLD}${YELLOW}[5/6] Frontend Integration Tests${NC}"
if [ -d "frontend/__tests__/integration" ]; then
    run_test_suite \
        "Frontend Integration Tests" \
        "npm test -- --run --reporter=verbose __tests__/integration/" \
        "frontend"
else
    echo -e "${YELLOW}⚠ SKIPPED${NC} - Frontend integration tests not found"
    log_result "Frontend Integration Tests: SKIPPED (directory not found)"
fi

# 6. System Integration Verification
echo -e "\n${BOLD}${YELLOW}[6/6] System Integration Verification${NC}"
run_test_suite \
    "System Integration Verification" \
    "python verify_final_integration.py" \
    "."

# Generate summary
echo -e "\n${BOLD}${BLUE}================================================================================================${NC}"
echo -e "${BOLD}${BLUE}TEST SUMMARY${NC}"
echo -e "${BOLD}${BLUE}================================================================================================${NC}\n"

log_result ""
log_result "================================================================================================"
log_result "FINAL SUMMARY"
log_result "================================================================================================"

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✓ ALL TEST SUITES PASSED${NC}"
    log_result "OVERALL STATUS: ALL TESTS PASSED"
    echo -e "${GREEN}The system is ready for deployment!${NC}\n"
else
    echo -e "${RED}${BOLD}✗ SOME TEST SUITES FAILED${NC}"
    log_result "OVERALL STATUS: SOME TESTS FAILED"
    echo -e "${RED}Please review the failures and fix issues before deployment.${NC}\n"
fi

echo -e "Detailed report saved to: ${BOLD}${REPORT_FILE}${NC}\n"
log_result ""
log_result "Report generated at: $(date)"
log_result "================================================================================================"

exit $OVERALL_STATUS
