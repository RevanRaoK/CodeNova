# Testing Documentation

This document provides an overview of the comprehensive testing suite implemented for the CodeReview AI frontend application.

## Test Structure

The testing suite is organized into three main categories:

### 1. Unit Tests (`components/__tests__/`)
- **MonacoEditor.unit.test.jsx**: Comprehensive unit tests for the Monaco Editor component
- **NotificationSystem.test.jsx**: Tests for the notification system components
- **ReviewResults.test.jsx**: Tests for the review results display component

### 2. Integration Tests (`services/__tests__/`, `contexts/__tests__/`)
- **apiService.integration.test.js**: Integration tests for API service layer
- **AuthContext.test.jsx**: Tests for authentication context and state management
- **ReviewResults.integration.test.jsx**: Integration tests for review results with API

### 3. End-to-End Tests (`__tests__/e2e/`)
- **codeReviewWorkflow.test.jsx**: Complete workflow tests from login to code analysis

## Test Utilities

### Mock API Responses (`__tests__/utils/mockApiResponses.js`)
Provides consistent mock data for:
- Authentication responses (login, register, logout, token refresh)
- Code analysis responses (success, failure, file upload)
- Error responses for different HTTP status codes
- Mock file data for testing file uploads

### Test Helpers (`__tests__/utils/testHelpers.jsx`)
Utility functions for:
- Rendering components with all necessary providers
- Mocking browser APIs (localStorage, FileReader, etc.)
- Creating mock users and analysis results
- Performance testing helpers

## Test Coverage

### Monaco Editor Component
- ✅ Basic functionality (rendering, value changes, callbacks)
- ✅ Language switching and theme changes
- ✅ File upload and drag-and-drop functionality
- ✅ Issue highlighting and navigation
- ✅ Error handling and validation
- ✅ Responsive design and accessibility
- ✅ Read-only mode behavior

### API Service Layer
- ✅ Authentication flow (login, register, logout, token refresh)
- ✅ Code analysis API integration
- ✅ File upload functionality
- ✅ Error handling and retry logic
- ✅ Request/response interceptors
- ✅ Token management and automatic refresh

### Authentication Context
- ✅ State management and persistence
- ✅ Login/logout workflows
- ✅ Token validation and refresh
- ✅ Error handling and user feedback
- ✅ Concurrent operations handling

### End-to-End Workflows
- ✅ Complete authentication and code review flow
- ✅ File upload and analysis workflow
- ✅ Error recovery and edge cases
- ✅ Responsive design testing
- ✅ Accessibility and keyboard navigation
- ✅ Performance and loading states

## Running Tests

### All Tests
```bash
npm test
```

### Specific Test Categories
```bash
# Unit tests only
npm test -- --run components/__tests__/

# Integration tests only
npm test -- --run services/__tests__/ contexts/__tests__/

# End-to-end tests only
npm test -- --run __tests__/e2e/

# Specific test file
npm test -- --run NotificationSystem.test.jsx
```

### Watch Mode
```bash
npm test -- --watch
```

### Coverage Report
```bash
npm test -- --coverage
```

## Test Configuration

### Vitest Configuration (`vitest.config.js`)
- Uses jsdom environment for DOM testing
- Includes React plugin for JSX support
- Configured with global test utilities
- Monaco Editor alias for import resolution

### Setup Files (`src/setupTests.js`)
- Imports jest-dom matchers
- Global test configuration

## Mocking Strategy

### External Dependencies
- **Monaco Editor**: Mocked with simplified interface for testing
- **Axios**: Mocked using axios-mock-adapter for API testing
- **File APIs**: Custom mocks for File, FileReader, and drag-and-drop
- **Browser APIs**: Mocked localStorage, clipboard, and media queries

### Component Mocking
- **Notification System**: Mocked for isolated component testing
- **Router**: BrowserRouter wrapper for navigation testing
- **Context Providers**: Full provider stack for integration testing

## Test Data Management

### Consistent Mock Data
- Centralized mock responses in `mockApiResponses.js`
- Reusable test data generators
- Validation helpers for response structures

### Test Isolation
- Each test clears localStorage and mocks before running
- Independent test data to prevent cross-test contamination
- Proper cleanup in afterEach hooks

## Performance Testing

### Render Performance
- Measures component render times
- Validates performance under different conditions
- Tests with large datasets and files

### Memory Leak Detection
- Tests component cleanup on unmount
- Validates proper event listener removal
- Checks for memory leaks in long-running tests

## Accessibility Testing

### Keyboard Navigation
- Tests tab order and keyboard shortcuts
- Validates focus management
- Screen reader compatibility

### ARIA Labels
- Proper semantic markup testing
- Role and label validation
- Accessibility tree structure

## Error Scenarios

### Network Failures
- Connection timeouts and network errors
- Server error responses (4xx, 5xx)
- Retry logic and error recovery

### User Input Validation
- Invalid file types and sizes
- Malformed code input
- Edge cases and boundary conditions

### Authentication Errors
- Token expiration and refresh failures
- Invalid credentials and permissions
- Session management edge cases

## Continuous Integration

### Test Pipeline
- All tests run on every commit
- Separate jobs for unit, integration, and e2e tests
- Coverage reporting and quality gates

### Quality Metrics
- Minimum 80% code coverage requirement
- Performance benchmarks for critical paths
- Accessibility compliance validation

## Best Practices

### Test Organization
- Descriptive test names and grouping
- Arrange-Act-Assert pattern
- Single responsibility per test

### Mock Management
- Minimal mocking for better confidence
- Realistic mock data and responses
- Clear mock setup and teardown

### Async Testing
- Proper async/await usage
- waitFor for DOM updates
- act() for React state updates

### Debugging
- Detailed error messages
- Screen debug utilities
- Console output for test failures

## Future Improvements

### Planned Enhancements
- Visual regression testing
- Cross-browser compatibility tests
- Performance benchmarking suite
- Automated accessibility audits

### Test Maintenance
- Regular mock data updates
- Test refactoring for maintainability
- Documentation updates with new features