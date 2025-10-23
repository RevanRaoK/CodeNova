#!/bin/bash

# Task 12: Frontend Unit and Integration Tests
# Run all tests created for this task

echo "=========================================="
echo "Task 12: Frontend Unit and Integration Tests"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running Component Tests...${NC}"
npm test -- --run components/__tests__/MultiFileUploadZone.test.jsx
npm test -- --run components/__tests__/IssueTrendsChart.test.jsx
npm test -- --run components/__tests__/CriticalityDistributionChart.test.jsx
npm test -- --run components/admin/__tests__/UserManagementPanel.test.jsx

echo ""
echo -e "${BLUE}Running Service Tests...${NC}"
npm test -- --run services/__tests__/fileUploadService.test.js

echo ""
echo -e "${BLUE}Running Hook Tests...${NC}"
npm test -- --run hooks/__tests__/useFileUpload.test.js
npm test -- --run hooks/__tests__/useAdminAnalytics.test.js

echo ""
echo -e "${BLUE}Running Integration Tests...${NC}"
npm test -- --run __tests__/integration/fileUpload.integration.test.jsx
npm test -- --run __tests__/integration/adminWorkflow.integration.test.jsx

echo ""
echo -e "${GREEN}=========================================="
echo "Test Execution Complete!"
echo "==========================================${NC}"
echo ""
echo "To run with coverage:"
echo "  npm run test:coverage"
echo ""
echo "To run all tests:"
echo "  npm test -- --run"
