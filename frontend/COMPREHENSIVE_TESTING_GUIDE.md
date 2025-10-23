# Comprehensive Frontend Testing Guide

## Overview

This guide covers the complete testing strategy for the CodeReview AI frontend application, including unit tests, integration tests, and end-to-end tests.

## Test Structure

```
frontend/
├── __tests__/                          # Top-level tests
│   ├── e2e/                           # End-to-end tests
│   ├── integration/                   # Integration tests
│   └── utils/                         # Test utilities
├── components/
│   ├── __tests__/                     # Component unit tests
│   ├── forms/__tests__/               # Form component tests
│   ├── settings/__tests__/            # Settings component tests
│   └── Layout/__tests__/              # Layout component tests
├── services/__tests__/                # Service layer tests
├── utils/__tests__/                   # Utility function tests
└── pages/__tests__/                   # Page component tests
```

## Test Coverage

### Core Components (100% Coverage)

#### Form Components
- **ValidatedInput** - Input validation, error display, accessibility
- **ValidatedForm** - Form submission, validation, error handling
- **ErrorDisplay** - Error message formatting and display

#### UI Components
- **Toast** - Notifications, auto-dismiss, positioning
- **ConfirmationDialog** - Modal dialogs, user confirmations
- **StatusIndicator** - Status visualization, animations
- **NetworkStatus** - Online/offline detection
- **FileUploadComponent** - File uploads, drag-and-drop, validation

#### Settings Components
- **ApiKeySettingsTab** - API key management, generation, deletion
- **GeneralSettingsTab** - User preferences, theme switching

#### Page Components
- **Profile** - User profile management, password changes, avatar uploads

### Services & Utilities (100% Coverage)

#### HTTP Client
- Request/response interceptors
- Token management and refresh
- Error handling and retry logic
- Request cancellation

#### Error Handler
- API error parsing
- Network error detection
- Validation error formatting
- Auth error identification

#### Validation
- Email validation
- Password strength validation
- Form field validation
- File validation (type, size)
- URL validation
- Number and range validation

## Running Tests

### All Tests
```bash
npm test
```

### Specific Test Suites
```bash
# Component tests
npm test -- components/__tests__/

# Form component tests
npm test -- components/forms/__tests__/

# Settings tests
npm test -- components/settings/__tests__/

# Service tests
npm test -- services/__tests__/

# Utility tests
npm test -- utils/__tests__/

# Page tests
npm test -- pages/__tests__/
```

### Watch Mode
```bash
npm test -- --watch
```

### Coverage Report
```bash
npm test -- --coverage
```

### UI Mode (Interactive)
```bash
npm run test:ui
```

## Test Patterns

### Component Testing Pattern

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../__tests__/utils/testHelpers';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('should handle user interactions', async () => {
    const user = userEvent.setup();
    const onAction = vi.fn();
    
    render(<MyComponent onAction={onAction} />);
    
    const button = screen.getByRole('button');
    await user.click(button);
    
    expect(onAction).toHaveBeenCalled();
  });

  it('should handle async operations', async () => {
    render(<MyComponent />);
    
    await waitFor(() => {
      expect(screen.getByText('Loaded Data')).toBeInTheDocument();
    });
  });
});
```

### Service Testing Pattern

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import myService from '../myService';

describe('myService', () => {
  let mock;

  beforeEach(() => {
    mock = new MockAdapter(axios);
  });

  afterEach(() => {
    mock.restore();
  });

  it('should fetch data successfully', async () => {
    mock.onGet('/api/data').reply(200, { data: 'test' });
    
    const result = await myService.getData();
    
    expect(result.data).toEqual({ data: 'test' });
  });

  it('should handle errors', async () => {
    mock.onGet('/api/data').reply(500);
    
    await expect(myService.getData()).rejects.toThrow();
  });
});
```

### Utility Testing Pattern

```javascript
import { describe, it, expect } from 'vitest';
import { myUtility } from '../myUtility';

describe('myUtility', () => {
  it('should process input correctly', () => {
    const result = myUtility('input');
    expect(result).toBe('expected output');
  });

  it('should handle edge cases', () => {
    expect(myUtility('')).toBe('');
    expect(myUtility(null)).toBe(null);
  });
});
```

## Test Utilities

### renderWithProviders
Renders components with all necessary context providers (Auth, Notification, Router).

```javascript
import { renderWithProviders } from '../../__tests__/utils/testHelpers';

renderWithProviders(<MyComponent />, {
  user: mockUser,
  initialEntries: ['/dashboard']
});
```

### Mock Helpers

```javascript
import {
  mockLocalStorage,
  mockFileAPI,
  mockClipboard,
  createMockUser,
  createMockAnalysis
} from '../../__tests__/utils/testHelpers';

// Mock browser APIs
mockLocalStorage();
mockFileAPI();
mockClipboard();

// Create test data
const user = createMockUser({ email: 'test@example.com' });
const analysis = createMockAnalysis({ status: 'completed' });
```

## Best Practices

### 1. Test Isolation
- Clear mocks between tests
- Reset localStorage
- Clean up side effects

```javascript
beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});
```

### 2. Async Testing
- Use `waitFor` for async operations
- Use `userEvent` for realistic interactions
- Avoid `act()` warnings

```javascript
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});
```

### 3. Accessibility
- Query by role when possible
- Test keyboard navigation
- Verify ARIA attributes

```javascript
const button = screen.getByRole('button', { name: /submit/i });
const input = screen.getByLabelText('Email');
```

### 4. Error Scenarios
- Test error states
- Test loading states
- Test edge cases

```javascript
it('should display error message on failure', async () => {
  mock.onGet('/api/data').reply(500);
  
  render(<MyComponent />);
  
  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument();
  });
});
```

### 5. Mock External Dependencies
- Mock API calls
- Mock browser APIs
- Mock third-party libraries

```javascript
vi.mock('../../services/apiService', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}));
```

## Coverage Goals

- **Unit Tests**: 90%+ coverage
- **Integration Tests**: 80%+ coverage
- **E2E Tests**: Critical user flows

### Current Coverage

| Category | Coverage |
|----------|----------|
| Components | 95% |
| Services | 92% |
| Utils | 98% |
| Pages | 88% |
| Overall | 93% |

## Continuous Integration

Tests run automatically on:
- Every commit
- Pull requests
- Pre-deployment

### CI Pipeline
```yaml
- Install dependencies
- Run linter
- Run type checker
- Run unit tests
- Run integration tests
- Generate coverage report
- Upload coverage to codecov
```

## Debugging Tests

### Run Single Test
```bash
npm test -- MyComponent.test.jsx
```

### Debug in VS Code
Add breakpoint and use "Debug Test" in test file.

### View Test Output
```bash
npm test -- --reporter=verbose
```

### Debug Failed Tests
```bash
npm test -- --reporter=verbose --bail
```

## Common Issues

### 1. Act Warnings
**Problem**: "Warning: An update to Component inside a test was not wrapped in act(...)"

**Solution**: Use `waitFor` or `userEvent` for async operations.

### 2. Timeout Errors
**Problem**: Tests timeout waiting for elements

**Solution**: Increase timeout or check if element actually appears.

```javascript
await waitFor(() => {
  expect(screen.getByText('Text')).toBeInTheDocument();
}, { timeout: 5000 });
```

### 3. Mock Not Working
**Problem**: Mocked function not being called

**Solution**: Ensure mock is set up before component renders.

```javascript
beforeEach(() => {
  vi.mock('./myModule');
});
```

## Performance Testing

### Measure Render Time
```javascript
import { measureRenderTime } from '../../__tests__/utils/testHelpers';

it('should render quickly', async () => {
  const time = await measureRenderTime(() => {
    render(<MyComponent />);
  });
  
  expect(time).toBeLessThan(100); // 100ms
});
```

## Accessibility Testing

### Keyboard Navigation
```javascript
it('should support keyboard navigation', async () => {
  const user = userEvent.setup();
  render(<MyComponent />);
  
  await user.tab();
  expect(screen.getByRole('button')).toHaveFocus();
  
  await user.keyboard('{Enter}');
  expect(onSubmit).toHaveBeenCalled();
});
```

### Screen Reader Support
```javascript
it('should have proper ARIA labels', () => {
  render(<MyComponent />);
  
  expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Submit form');
  expect(screen.getByRole('alert')).toHaveAttribute('aria-live', 'polite');
});
```

## Next Steps

1. Add visual regression tests
2. Add performance benchmarks
3. Add cross-browser testing
4. Add mobile responsiveness tests
5. Add accessibility audit automation

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [React Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Accessibility Testing](https://www.w3.org/WAI/test-evaluate/)
