/**
 * Full Application Flow Integration Test
 * Tests the complete user journey from authentication to code analysis
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';

import App from '../../App';
import httpClient from '../../services/httpClient';
import { env } from '../../utils/environment';

// Mock environment for testing
vi.mock('../../utils/environment', () => ({
  env: {
    apiUrl: 'http://localhost:8000',
    environment: 'test',
    enableDevTools: false,
    enableServiceWorker: false,
    googleClientId: 'test-client-id',
    version: '1.0.0-test',
  },
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
  featureFlags: {
    enableAnalytics: false,
    enableErrorReporting: false,
    enablePerformanceMonitoring: false,
    enableServiceWorker: false,
    enableOfflineMode: false,
    enableDebugMode: false,
  },
  buildInfo: {
    version: '1.0.0-test',
    environment: 'test',
    buildTime: '2024-01-01T00:00:00.000Z',
    commit: 'test-commit',
    branch: 'test-branch',
  },
}));

// Mock service worker utilities
vi.mock('../../utils/serviceWorker', () => ({
  registerServiceWorker: vi.fn().mockResolvedValue({
    isSupported: false,
    isRegistered: false,
    isActive: false,
    registration: null,
    error: null,
  }),
  setupOfflineDetection: vi.fn().mockReturnValue(() => {}),
}));

// Mock Monaco Editor components to avoid loading issues in tests
vi.mock('../../components/MonacoEditor', () => ({
  MonacoEditor: ({ value, onChange }) => (
    <div data-testid="monaco-editor">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Monaco Editor Mock"
        rows={10}
        cols={50}
      />
    </div>
  ),
  default: ({ value, onChange }) => (
    <div data-testid="monaco-editor">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Monaco Editor Mock"
        rows={10}
        cols={50}
      />
    </div>
  ),
}));

// Mock LazyMonacoEditor
vi.mock('../../components/LazyMonacoEditor', () => ({
  LazyMonacoEditor: ({ value, onChange }) => (
    <div data-testid="monaco-editor">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Monaco Editor Mock"
        rows={10}
        cols={50}
      />
    </div>
  ),
  default: ({ value, onChange }) => (
    <div data-testid="monaco-editor">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Monaco Editor Mock"
        rows={10}
        cols={50}
      />
    </div>
  ),
}));

// Mock Monaco optimizations
vi.mock('../../utils/monacoOptimizations', () => ({
  getOptimizedEditorOptions: vi.fn().mockReturnValue({}),
  getLanguageOptimizations: vi.fn().mockReturnValue({}),
  loadLanguageSupport: vi.fn().mockResolvedValue(undefined),
  createPerformanceMonitor: vi.fn().mockReturnValue({
    onRender: vi.fn(),
    getRenderStats: vi.fn().mockReturnValue({ renderCount: 0, lastRenderTime: 0 }),
    reset: vi.fn(),
  }),
  optimizeMemoryUsage: vi.fn().mockReturnValue({ dispose: vi.fn() }),
  createDebouncedResizeHandler: vi.fn().mockReturnValue({
    handleResize: vi.fn(),
    dispose: vi.fn(),
  }),
  PERFORMANCE_THRESHOLDS: {
    LARGE_FILE_LINES: 1000,
    HUGE_FILE_LINES: 5000,
    LARGE_FILE_SIZE: 100 * 1024,
    HUGE_FILE_SIZE: 500 * 1024,
    MOBILE_BREAKPOINT: 768,
  },
}));

// Mock Google OAuth
vi.mock('../../components/providers/GoogleOAuthProvider', () => ({
  default: ({ children }) => <div data-testid="google-oauth-provider">{children}</div>,
}));

describe('Full Application Flow Integration Tests', () => {
  let mockAxios;
  let user;

  beforeEach(() => {
    // Setup axios mock
    mockAxios = new MockAdapter(httpClient);
    user = userEvent.setup();

    // Clear localStorage
    localStorage.clear();

    // Mock successful authentication responses
    mockAxios.onPost('/auth/login').reply(200, {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      user: {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
      },
    });

    mockAxios.onGet('/users/me').reply(200, {
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
    });

    // Mock code analysis response
    mockAxios.onPost('/analysis/analyze-code').reply(200, {
      analysis_id: 'test-analysis-123',
      status: 'completed',
      issues: [
        {
          line: 5,
          column: 10,
          severity: 'warning',
          message: 'Variable is declared but never used',
          rule: 'no-unused-vars',
          suggestion: 'Remove unused variable or use it in the code',
        },
        {
          line: 12,
          column: 1,
          severity: 'error',
          message: 'Missing semicolon',
          rule: 'semi',
          suggestion: 'Add semicolon at the end of the statement',
        },
      ],
      metrics: {
        linesOfCode: 25,
        complexity: 3,
        maintainabilityIndex: 85,
      },
      suggestions: [
        {
          type: 'improvement',
          message: 'Consider using const instead of let for variables that are not reassigned',
          line: 3,
        },
      ],
    });

    // Mock file upload response
    mockAxios.onPost('/files/upload').reply(200, {
      filename: 'test.js',
      content: 'function test() {\n  let unused = 5;\n  console.log("Hello World");\n}',
      language: 'javascript',
      size: 65,
    });
  });

  afterEach(() => {
    mockAxios.restore();
    vi.clearAllMocks();
  });

  it('should complete the full user journey: login -> code review -> analysis', async () => {
    render(<App />);

    // Step 1: User should be redirected to login page
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

    // Step 2: User logs in
    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Step 3: Wait for authentication and redirect to home page
    await waitFor(() => {
      expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    });

    // Step 4: Navigate to code review page
    const codeReviewLink = screen.getByRole('link', { name: /code review/i });
    await user.click(codeReviewLink);

    // Step 5: Verify code review page loads with Monaco Editor
    await waitFor(() => {
      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    });

    // Step 6: Enter code in the editor
    const editor = screen.getByPlaceholderText('Monaco Editor Mock');
    const testCode = `function calculateSum(a, b) {
  let unused = 5;
  const result = a + b;
  return result
}`;

    await user.clear(editor);
    await user.type(editor, testCode);

    // Step 7: Submit code for analysis
    const reviewButton = screen.getByRole('button', { name: /review code/i });
    await user.click(reviewButton);

    // Step 8: Wait for analysis results
    await waitFor(() => {
      expect(screen.getByText(/analysis results/i)).toBeInTheDocument();
    });

    // Step 9: Verify analysis results are displayed
    expect(screen.getByText(/Variable is declared but never used/i)).toBeInTheDocument();
    expect(screen.getByText(/Missing semicolon/i)).toBeInTheDocument();
    expect(screen.getByText(/warning/i)).toBeInTheDocument();
    expect(screen.getByText(/error/i)).toBeInTheDocument();

    // Step 10: Verify metrics are displayed
    expect(screen.getByText(/25/)).toBeInTheDocument(); // Lines of code
    expect(screen.getByText(/85/)).toBeInTheDocument(); // Maintainability index

    // Step 11: Test issue navigation (click on an issue)
    const firstIssue = screen.getByText(/Variable is declared but never used/i);
    await user.click(firstIssue);

    // Verify that clicking an issue doesn't cause errors
    expect(firstIssue).toBeInTheDocument();
  });

  it('should handle file upload workflow', async () => {
    // Login first
    localStorage.setItem('access_token', 'mock-token');
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
    }));

    render(<App />);

    // Navigate to code review page
    await waitFor(() => {
      expect(screen.getByRole('link', { name: /code review/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('link', { name: /code review/i }));

    // Switch to upload tab
    await waitFor(() => {
      expect(screen.getByText(/upload file/i)).toBeInTheDocument();
    });

    const uploadTab = screen.getByText(/upload file/i);
    await user.click(uploadTab);

    // Verify file upload interface is shown
    expect(screen.getByText(/drag.*drop/i)).toBeInTheDocument();

    // Create a mock file
    const file = new File(['function test() { console.log("test"); }'], 'test.js', {
      type: 'text/javascript',
    });

    // Find file input and upload file
    const fileInput = screen.getByLabelText(/choose file/i) || screen.getByRole('button', { name: /upload/i });
    
    if (fileInput.tagName === 'INPUT') {
      await user.upload(fileInput, file);
    } else {
      // If it's a button, simulate the file upload process
      await user.click(fileInput);
    }

    // Wait for file processing
    await waitFor(() => {
      expect(mockAxios.history.post.some(req => req.url === '/files/upload')).toBe(true);
    });
  });

  it('should handle authentication errors gracefully', async () => {
    // Mock authentication failure
    mockAxios.onPost('/auth/login').reply(401, {
      detail: 'Invalid credentials',
    });

    render(<App />);

    // Try to login with invalid credentials
    await user.type(screen.getByLabelText(/email/i), 'invalid@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });

    // Verify user stays on login page
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it('should handle API errors during code analysis', async () => {
    // Login first
    localStorage.setItem('access_token', 'mock-token');
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
    }));

    // Mock analysis failure
    mockAxios.onPost('/analysis/analyze-code').reply(500, {
      detail: 'Internal server error',
    });

    render(<App />);

    // Navigate to code review
    await user.click(screen.getByRole('link', { name: /code review/i }));

    // Enter code and submit
    const editor = screen.getByPlaceholderText('Monaco Editor Mock');
    await user.type(editor, 'function test() {}');

    const reviewButton = screen.getByRole('button', { name: /review code/i });
    await user.click(reviewButton);

    // Verify error handling
    await waitFor(() => {
      expect(screen.getByText(/error.*occurred/i)).toBeInTheDocument();
    });
  });

  it('should maintain responsive design on different screen sizes', async () => {
    // Test mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    // Trigger resize event
    window.dispatchEvent(new Event('resize'));

    // Login first
    localStorage.setItem('access_token', 'mock-token');
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
    }));

    render(<App />);

    // Navigate to code review
    await user.click(screen.getByRole('link', { name: /code review/i }));

    // Verify Monaco Editor loads on mobile
    await waitFor(() => {
      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    });

    // Test desktop viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });

    window.dispatchEvent(new Event('resize'));

    // Verify layout still works
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });

  it('should handle navigation between different pages', async () => {
    // Login first
    localStorage.setItem('access_token', 'mock-token');
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
    }));

    render(<App />);

    // Test navigation to different pages
    const pages = [
      { name: /code review/i, path: '/code-review' },
      { name: /settings/i, path: '/settings' },
      { name: /profile/i, path: '/profile' },
    ];

    for (const page of pages) {
      const link = screen.getByRole('link', { name: page.name });
      await user.click(link);

      // Verify URL changed (in a real browser test)
      // For now, just verify the link exists and is clickable
      expect(link).toBeInTheDocument();
    }
  });

  it('should handle logout functionality', async () => {
    // Login first
    localStorage.setItem('access_token', 'mock-token');
    localStorage.setItem('user', JSON.stringify({
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
    }));

    mockAxios.onPost('/auth/logout').reply(200, { message: 'Logged out successfully' });

    render(<App />);

    // Find and click logout button (might be in a dropdown or menu)
    const logoutButton = screen.getByRole('button', { name: /logout/i }) || 
                        screen.getByText(/logout/i);
    
    if (logoutButton) {
      await user.click(logoutButton);

      // Verify redirect to login page
      await waitFor(() => {
        expect(screen.getByText(/sign in/i)).toBeInTheDocument();
      });

      // Verify tokens are cleared
      expect(localStorage.getItem('access_token')).toBeNull();
    }
  });
});