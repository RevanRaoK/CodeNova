import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import { AuthProvider } from '../../contexts/AuthContext';
import { NotificationProvider } from '../../contexts/NotificationContext';
import NotificationManager from '../../components/NotificationManager';
import { CodeReview } from '../../pages/CodeReview';
import { Login } from '../../pages/Login';
import httpClient from '../../services/httpClient';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ onMount, onChange, value, ...props }) => {
    React.useEffect(() => {
      if (onMount) {
        const mockEditor = {
          getValue: () => value,
          setValue: vi.fn(),
          getModel: () => ({ uri: { toString: () => 'test' } }),
          setPosition: vi.fn(),
          revealLineInCenter: vi.fn(),
          focus: vi.fn(),
          setSelection: vi.fn(),
          layout: vi.fn(),
          onMouseDown: vi.fn(),
          addCommand: vi.fn()
        };
        const mockMonaco = {
          editor: {
            setTheme: vi.fn(),
            setModelLanguage: vi.fn(),
            setModelMarkers: vi.fn()
          },
          languages: {
            typescript: {
              javascriptDefaults: { setEagerModelSync: vi.fn(), setCompilerOptions: vi.fn() },
              typescriptDefaults: { setEagerModelSync: vi.fn(), setCompilerOptions: vi.fn() }
            }
          },
          KeyMod: { CtrlCmd: 2048 },
          KeyCode: { KeyS: 49 },
          MarkerSeverity: { Error: 8, Warning: 4, Info: 1 }
        };
        onMount(mockEditor, mockMonaco);
      }
    }, [onMount]);

    return (
      <div data-testid="monaco-editor">
        <textarea
          data-testid="monaco-textarea"
          value={value}
          onChange={(e) => onChange && onChange(e.target.value)}
        />
      </div>
    );
  }
}));

// Mock file utils
vi.mock('../../utils/fileUtils', () => ({
  SUPPORTED_LANGUAGES: [
    { id: 'javascript', name: 'JavaScript' },
    { id: 'python', name: 'Python' },
    { id: 'typescript', name: 'TypeScript' }
  ],
  processUploadedFile: vi.fn(),
  formatFileSize: vi.fn((size) => `${size} bytes`),
  isDragAndDropSupported: vi.fn(() => true),
  getLanguageFromFilename: vi.fn(() => 'javascript')
}));

// Test wrapper component
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <NotificationProvider>
      <AuthProvider>
        {children}
        <NotificationManager />
      </AuthProvider>
    </NotificationProvider>
  </BrowserRouter>
);

describe('End-to-End Code Review Workflow', () => {
  let mockAxios;
  let user;

  beforeEach(() => {
    mockAxios = new MockAdapter(httpClient);
    user = userEvent.setup();
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    mockAxios.restore();
    localStorage.clear();
  });

  describe('Complete Authentication and Code Review Flow', () => {
    it('completes full workflow from login to code analysis', async () => {
      // Step 1: User logs in
      mockAxios.onPost('/auth/login').reply(200, {
        access_token: 'test-token',
        refresh_token: 'test-refresh',
        token_type: 'bearer',
        user: {
          id: 1,
          email: 'test@example.com',
          full_name: 'Test User'
        }
      });

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // Fill login form
      await user.type(screen.getByPlaceholderText('Email address'), 'test@example.com');
      await user.type(screen.getByPlaceholderText('Password'), 'password123');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Wait for login success notification
      await waitFor(() => {
        expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
      });

      // Step 2: Navigate to code review (simulate navigation)
      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      // Verify code review page loads
      expect(screen.getByText('Code Review')).toBeInTheDocument();
      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();

      // Step 3: Enter code in editor
      const codeInput = screen.getByTestId('monaco-textarea');
      await user.clear(codeInput);
      await user.type(codeInput, 'console.log(undefinedVariable);');

      // Step 4: Analyze code
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-123',
        status: 'completed',
        issues: [
          {
            line: 1,
            column: 12,
            severity: 'error',
            message: "'undefinedVariable' is not defined",
            rule: 'no-undef'
          }
        ],
        metrics: {
          lines_of_code: 1,
          complexity: 1,
          maintainability: 90
        }
      });

      const analyzeButton = screen.getByRole('button', { name: /analyze code/i });
      await user.click(analyzeButton);

      // Verify analysis starts
      await waitFor(() => {
        expect(screen.getByText(/analyzing your code/i)).toBeInTheDocument();
      });

      // Wait for analysis completion
      await waitFor(() => {
        expect(screen.getByText(/analysis complete/i)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Step 5: Verify results are displayed
      await waitFor(() => {
        expect(screen.getByText('Review Results')).toBeInTheDocument();
        expect(screen.getByText("'undefinedVariable' is not defined")).toBeInTheDocument();
      });

      // Verify issue details
      const issueElement = screen.getByText("'undefinedVariable' is not defined");
      expect(issueElement).toBeInTheDocument();
      
      // Check if severity is displayed
      const errorElements = screen.getAllByText(/error/i);
      expect(errorElements.length).toBeGreaterThan(0);
    });

    it('handles file upload and analysis workflow', async () => {
      // Setup authenticated state
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('user_data', JSON.stringify({
        id: 1,
        email: 'test@example.com'
      }));

      const { processUploadedFile } = await import('../../utils/fileUtils');
      processUploadedFile.mockResolvedValue({
        content: 'function test() {\n  console.log("Hello World");\n}',
        language: 'javascript',
        filename: 'test.js',
        size: 45
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      // Step 1: Switch to file upload tab
      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      // Step 2: Upload file
      mockAxios.onPost('/api/v1/files/upload').reply(200, {
        file_id: 'file-456',
        filename: 'test.js',
        analysis: {
          id: 'analysis-456',
          issues: [],
          metrics: {
            lines_of_code: 3,
            complexity: 1,
            maintainability: 95
          }
        }
      });

      // Simulate file upload
      const file = new File(['function test() { console.log("Hello"); }'], 'test.js', {
        type: 'text/javascript'
      });

      // Find file input and upload
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) {
        await user.upload(fileInput, file);
      }

      // Wait for upload success
      await waitFor(() => {
        expect(screen.getByText(/file.*loaded successfully/i)).toBeInTheDocument();
      });

      // Verify editor switches to editor tab and shows content
      await waitFor(() => {
        expect(screen.getByDisplayValue(/function test/)).toBeInTheDocument();
      });

      // Verify analysis results are shown
      await waitFor(() => {
        expect(screen.getByText(/no issues found/i)).toBeInTheDocument();
      });
    });

    it('handles analysis errors gracefully', async () => {
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('user_data', JSON.stringify({ id: 1 }));

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      // Enter code
      const codeInput = screen.getByTestId('monaco-textarea');
      await user.type(codeInput, 'console.log("test");');

      // Mock analysis failure
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(500, {
        detail: 'Analysis service temporarily unavailable'
      });

      const analyzeButton = screen.getByRole('button', { name: /analyze code/i });
      await user.click(analyzeButton);

      // Wait for error notification
      await waitFor(() => {
        expect(screen.getByText(/analysis service temporarily unavailable/i)).toBeInTheDocument();
      });

      // Verify retry option is available
      expect(screen.getByText(/retry/i)).toBeInTheDocument();
    });

    it('handles token expiration during analysis', async () => {
      // Setup with expired token
      const expiredPayload = {
        exp: Math.floor(Date.now() / 1000) - 3600 // Expired 1 hour ago
      };
      const expiredToken = `header.${btoa(JSON.stringify(expiredPayload))}.signature`;
      
      localStorage.setItem('access_token', expiredToken);
      localStorage.setItem('refresh_token', 'valid-refresh');
      localStorage.setItem('user_data', JSON.stringify({ id: 1 }));

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      // Enter code
      const codeInput = screen.getByTestId('monaco-textarea');
      await user.type(codeInput, 'console.log("test");');

      // Mock token refresh and analysis
      mockAxios.onPost('/api/v1/analysis/analyze-code').replyOnce(401);
      mockAxios.onPost('/auth/refresh').reply(200, {
        access_token: 'new-token',
        refresh_token: 'new-refresh'
      });
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-789',
        issues: [],
        metrics: { lines_of_code: 1 }
      });

      const analyzeButton = screen.getByRole('button', { name: /analyze code/i });
      await user.click(analyzeButton);

      // Wait for successful analysis after token refresh
      await waitFor(() => {
        expect(screen.getByText(/no issues found/i)).toBeInTheDocument();
      });

      // Verify token was refreshed
      expect(localStorage.getItem('access_token')).toBe('new-token');
    });
  });

  describe('Responsive Design and Mobile Workflow', () => {
    beforeEach(() => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375, // iPhone width
      });
    });

    it('adapts interface for mobile devices', async () => {
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('user_data', JSON.stringify({ id: 1 }));

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      // Verify mobile-friendly layout
      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
      
      // Check that tabs are still functional on mobile
      const tabs = screen.getAllByRole('button');
      const editorTab = tabs.find(tab => tab.textContent.includes('Code Editor'));
      const uploadTab = tabs.find(tab => tab.textContent.includes('Upload File'));
      
      expect(editorTab).toBeInTheDocument();
      expect(uploadTab).toBeInTheDocument();

      // Test tab switching on mobile
      await user.click(uploadTab);
      await user.click(editorTab);
      
      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    });

    it('handles touch interactions properly', async () => {
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('user_data', JSON.stringify({ id: 1 }));

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      // Simulate touch events
      const codeInput = screen.getByTestId('monaco-textarea');
      
      fireEvent.touchStart(codeInput);
      fireEvent.touchEnd(codeInput);
      
      await user.type(codeInput, 'console.log("mobile test");');
      
      expect(codeInput.value).toContain('mobile test');
    });
  });

  describe('Error Recovery and Edge Cases', () => {
    it('recovers from network failures', async () => {
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('user_data', JSON.stringify({ id: 1 }));

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const codeInput = screen.getByTestId('monaco-textarea');
      await user.type(codeInput, 'console.log("test");');

      // First request fails with network error
      mockAxios.onPost('/api/v1/analysis/analyze-code').networkErrorOnce();
      
      // Second request succeeds
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-retry',
        issues: [],
        metrics: { lines_of_code: 1 }
      });

      const analyzeButton = screen.getByRole('button', { name: /analyze code/i });
      await user.click(analyzeButton);

      // Wait for network error notification
      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });

      // Click retry
      const retryButton = screen.getByText(/retry/i);
      await user.click(retryButton);

      // Wait for successful analysis
      await waitFor(() => {
        expect(screen.getByText(/no issues found/i)).toBeInTheDocument();
      });
    });

    it('handles empty code submission', async () => {
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('user_data', JSON.stringify({ id: 1 }));

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      // Try to analyze without entering code
      const analyzeButton = screen.getByRole('button', { name: /analyze code/i });
      await user.click(analyzeButton);

      // Should show warning about empty code
      await waitFor(() => {
        expect(screen.getByText(/please enter some code/i)).toBeInTheDocument();
      });
    });

    it('handles large code files appropriately', async () => {
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('user_data', JSON.stringify({ id: 1 }));

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      // Enter large code content
      const largeCode = 'console.log("test");\n'.repeat(1000);
      const codeInput = screen.getByTestId('monaco-textarea');
      await user.clear(codeInput);
      await user.type(codeInput, largeCode);

      // Mock response for large file
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(413, {
        detail: 'Code file too large. Maximum size is 1MB.'
      });

      const analyzeButton = screen.getByRole('button', { name: /analyze code/i });
      await user.click(analyzeButton);

      // Wait for size limit error
      await waitFor(() => {
        expect(screen.getByText(/code file too large/i)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility and Keyboard Navigation', () => {
    it('supports keyboard navigation throughout the workflow', async () => {
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('user_data', JSON.stringify({ id: 1 }));

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      // Test tab navigation
      await user.tab(); // Should focus first interactive element
      await user.tab(); // Move to next element
      
      // Test keyboard shortcuts in editor
      const codeInput = screen.getByTestId('monaco-textarea');
      await user.click(codeInput);
      await user.type(codeInput, 'console.log("test");');
      
      // Test Enter key to submit (if implemented)
      await user.keyboard('{Control>}s{/Control}'); // Ctrl+S shortcut
      
      expect(codeInput.value).toContain('test');
    });

    it('provides proper ARIA labels and screen reader support', () => {
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('user_data', JSON.stringify({ id: 1 }));

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      // Check for proper ARIA labels
      const analyzeButton = screen.getByRole('button', { name: /analyze code/i });
      expect(analyzeButton).toBeInTheDocument();
      
      // Check for proper heading structure
      const mainHeading = screen.getByRole('heading', { name: /code review/i });
      expect(mainHeading).toBeInTheDocument();
      
      // Check for proper form labels
      const languageSelect = screen.getByRole('combobox');
      expect(languageSelect).toBeInTheDocument();
    });
  });

  describe('Performance and Loading States', () => {
    it('shows appropriate loading states during analysis', async () => {
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('user_data', JSON.stringify({ id: 1 }));

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const codeInput = screen.getByTestId('monaco-textarea');
      await user.type(codeInput, 'console.log("test");');

      // Mock slow analysis response
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(() => {
        return new Promise(resolve => {
          setTimeout(() => {
            resolve([200, {
              id: 'slow-analysis',
              issues: [],
              metrics: { lines_of_code: 1 }
            }]);
          }, 1000);
        });
      });

      const analyzeButton = screen.getByRole('button', { name: /analyze code/i });
      await user.click(analyzeButton);

      // Verify loading state is shown
      expect(screen.getByText(/analyzing your code/i)).toBeInTheDocument();
      expect(analyzeButton).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(screen.getByText(/no issues found/i)).toBeInTheDocument();
      }, { timeout: 2000 });

      // Verify button is re-enabled
      expect(analyzeButton).not.toBeDisabled();
    });

    it('handles concurrent analysis requests properly', async () => {
      localStorage.setItem('access_token', 'test-token');
      localStorage.setItem('user_data', JSON.stringify({ id: 1 }));

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const codeInput = screen.getByTestId('monaco-textarea');
      await user.type(codeInput, 'console.log("test");');

      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'concurrent-analysis',
        issues: [],
        metrics: { lines_of_code: 1 }
      });

      const analyzeButton = screen.getByRole('button', { name: /analyze code/i });
      
      // Click multiple times rapidly
      await user.click(analyzeButton);
      await user.click(analyzeButton);
      await user.click(analyzeButton);

      // Should only make one request and show one result
      await waitFor(() => {
        expect(screen.getByText(/no issues found/i)).toBeInTheDocument();
      });

      // Verify only one analysis request was made
      expect(mockAxios.history.post.length).toBe(1);
    });
  });
});