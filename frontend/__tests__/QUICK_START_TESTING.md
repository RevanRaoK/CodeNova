# Quick Start: Running Task 12 Tests

## Quick Commands

### Run All Task 12 Tests
```bash
cd frontend
./run-task12-tests.sh
```

### Run All Tests with Coverage
```bash
npm run test:coverage
```

### Run Specific Test File
```bash
npm test -- --run components/__tests__/MultiFileUploadZone.test.jsx
```

### Run Tests in Watch Mode
```bash
npm run test:watch
```

## Test Files Overview

### Component Tests (66 tests)
- `components/__tests__/MultiFileUploadZone.test.jsx` - 15 tests
- `components/__tests__/IssueTrendsChart.test.jsx` - 14 tests
- `components/__tests__/CriticalityDistributionChart.test.jsx` - 18 tests
- `components/admin/__tests__/UserManagementPanel.test.jsx` - 19 tests

### Service Tests (27 tests)
- `services/__tests__/fileUploadService.test.js` - 27 tests

### Hook Tests (23 tests)
- `hooks/__tests__/useFileUpload.test.js` - 20 tests
- `hooks/__tests__/useAdminAnalytics.test.js` - 3 tests

### Integration Tests (3 tests)
- `__tests__/integration/fileUpload.integration.test.jsx` - 2 tests
- `__tests__/integration/adminWorkflow.integration.test.jsx` - 1 test

## Total: 119 Tests

## Expected Results
- ✅ All 119 tests should pass
- ✅ Coverage: 75-85% for tested components
- ✅ Duration: ~8-10 seconds

## Troubleshooting

### Tests Failing?
1. Ensure all dependencies are installed: `npm install`
2. Clear cache: `npm run clean:cache`
3. Check mock setup in test files

### Coverage Not Showing?
```bash
npm run test:coverage
# Then open: frontend/coverage/index.html
```

## Documentation
- Full Summary: `__tests__/TASK_12_TEST_SUMMARY.md`
- Completion Report: `__tests__/TASK_12_COMPLETION_REPORT.md`
