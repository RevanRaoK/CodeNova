import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import { AuthProvider } from '../../contexts/AuthContext';
import { NotificationProvider } from '../../contexts/NotificationContext';
import NotificationManager from '../../components/NotificationManager';
import { CodeReview } from '../../pages/CodeReview';
import httpClient from '../../services/httpClient';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange }) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange && onChange(e.target.value)}
    />
  )
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

describe('Multi-File Upload E2E Workflow', () => {
  let mockAxios;
  let user;

  beforeEach(() => {
    mockAxios = new MockAdapter(httpClient);
    user = userEvent.setup();
    localStorage.clear();
    
    // Setup authenticated user
    localStorage.setItem('access_token', 'test-token');
    localStorage.setItem('user_data', JSON.stringify({
      id: 1,
      email: 'test@example.com'
    }));
    
    vi.clearAllMocks();
  });

  afterEach(() => {
    mockAxios.restore();
    localStorage.clear();
  });

  describe('Single File Upload Workflow', () => {
    it('uploads and analyzes a single file successfully', async () => {
      mockAxios.onPost('/api/v1/files/upload').reply(200, {
        file_id: 'file-123',
        filename: 'test.js',
        size: 1024
      });

      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-123',
        status: 'completed',
        issues: [
          {
            line: 5,
            severity: 'warning',
            message: 'Unused variable',
            suggestion: 'Remove unused variable or use it'
          }
        ],
        metrics: {
          lines_of_code: 50,
          complexity: 3
        }
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      // Switch to upload tab
      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      // Upload file
      const file = new File(['console.log("test");'], 'test.js', {
        type: 'text/javascript'
      });

      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, file);

      // Verify upload success
      await waitFor(() => {
        expect(screen.getByText(/file uploaded successfully/i)).toBeInTheDocument();
      });

      // Verify analysis results
      await waitFor(() => {
        expect(screen.getByText(/unused variable/i)).toBeInTheDocument();
      });
    });

    it('validates file type before upload', async () => {
      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      // Try to upload invalid file type
      const file = new File(['test content'], 'test.exe', {
        type: 'application/x-msdownload'
      });

      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, file);

      // Verify validation error
      await waitFor(() => {
        expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
      });

      // Verify no upload request was made
      expect(mockAxios.history.post.length).toBe(0);
    });

    it('validates file size before upload', async () => {
      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      // Create large file (> 1MB)
      const largeContent = 'x'.repeat(2 * 1024 * 1024); // 2MB
      const file = new File([largeContent], 'large.js', {
        type: 'text/javascript'
      });

      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, file);

      // Verify size validation error
      await waitFor(() => {
        expect(screen.getByText(/file too large/i)).toBeInTheDocument();
      });
    });
  });

  describe('Multiple File Upload Workflow', () => {
    it('uploads and analyzes multiple files successfully', async () => {
      const batchId = 'batch-456';

      mockAxios.onPost('/api/v1/files/upload-multiple').reply(200, {
        batch_id: batchId,
        files: [
          { file_id: 'file-1', filename: 'app.js', size: 1024 },
          { file_id: 'file-2', filename: 'utils.js', size: 512 },
          { file_id: 'file-3', filename: 'config.js', size: 256 }
        ]
      });

      mockAxios.onGet(`/api/v1/files/upload-status/${batchId}`).reply(200, {
        batch_id: batchId,
        status: 'processing',
        total_files: 3,
        processed_files: 1
      });

      mockAxios.onGet(`/api/v1/files/analysis-results/${batchId}`).reply(200, {
        batch_id: batchId,
        status: 'completed',
        results: [
          {
            file_id: 'file-1',
            filename: 'app.js',
            issues: [
              { line: 10, severity: 'error', message: 'Syntax error' }
            ]
          },
          {
            file_id: 'file-2',
            filename: 'utils.js',
            issues: []
          },
          {
            file_id: 'file-3',
            filename: 'config.js',
            issues: [
              { line: 5, severity: 'warning', message: 'Deprecated API' }
            ]
          }
        ]
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      // Upload multiple files
      const files = [
        new File(['console.log("app");'], 'app.js', { type: 'text/javascript' }),
        new File(['export const util = () => {};'], 'utils.js', { type: 'text/javascript' }),
        new File(['module.exports = {};'], 'config.js', { type: 'text/javascript' })
      ];

      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, files);

      // Verify file list is displayed
      await waitFor(() => {
        expect(screen.getByText('app.js')).toBeInTheDocument();
        expect(screen.getByText('utils.js')).toBeInTheDocument();
        expect(screen.getByText('config.js')).toBeInTheDocument();
      });

      // Click analyze all
      const analyzeButton = screen.getByRole('button', { name: /analyze all/i });
      await user.click(analyzeButton);

      // Verify upload request
      await waitFor(() => {
        expect(mockAxios.history.post.some(req => 
          req.url.includes('upload-multiple')
        )).toBe(true);
      });

      // Verify progress tracking
      await waitFor(() => {
        expect(screen.getByText(/processing/i)).toBeInTheDocument();
      });

      // Wait for completion
      await waitFor(() => {
        expect(screen.getByText(/analysis complete/i)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Verify results for all files
      expect(screen.getByText(/syntax error/i)).toBeInTheDocument();
      expect(screen.getByText(/deprecated api/i)).toBeInTheDocument();
    });

    it('shows progress for each file during batch processing', async () => {
      const batchId = 'batch-789';

      mockAxios.onPost('/api/v1/files/upload-multiple').reply(200, {
        batch_id: batchId,
        files: [
          { file_id: 'file-1', filename: 'file1.js' },
          { file_id: 'file-2', filename: 'file2.js' }
        ]
      });

      // Mock progressive status updates
      let statusCallCount = 0;
      mockAxios.onGet(`/api/v1/files/upload-status/${batchId}`).reply(() => {
        statusCallCount++;
        if (statusCallCount === 1) {
          return [200, {
            status: 'processing',
            total_files: 2,
            processed_files: 0,
            current_file: 'file1.js'
          }];
        } else if (statusCallCount === 2) {
          return [200, {
            status: 'processing',
            total_files: 2,
            processed_files: 1,
            current_file: 'file2.js'
          }];
        } else {
          return [200, {
            status: 'completed',
            total_files: 2,
            processed_files: 2
          }];
        }
      });

      mockAxios.onGet(`/api/v1/files/analysis-results/${batchId}`).reply(200, {
        results: []
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      const files = [
        new File(['code1'], 'file1.js', { type: 'text/javascript' }),
        new File(['code2'], 'file2.js', { type: 'text/javascript' })
      ];

      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, files);

      const analyzeButton = screen.getByRole('button', { name: /analyze all/i });
      await user.click(analyzeButton);

      // Verify progress indicators
      await waitFor(() => {
        expect(screen.getByText(/0 of 2/i)).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText(/1 of 2/i)).toBeInTheDocument();
      }, { timeout: 3000 });

      await waitFor(() => {
        expect(screen.getByText(/2 of 2/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('handles partial batch failures gracefully', async () => {
      const batchId = 'batch-error';

      mockAxios.onPost('/api/v1/files/upload-multiple').reply(200, {
        batch_id: batchId,
        files: [
          { file_id: 'file-1', filename: 'good.js' },
          { file_id: 'file-2', filename: 'bad.js' }
        ]
      });

      mockAxios.onGet(`/api/v1/files/upload-status/${batchId}`).reply(200, {
        status: 'completed_with_errors',
        total_files: 2,
        processed_files: 2,
        failed_files: 1
      });

      mockAxios.onGet(`/api/v1/files/analysis-results/${batchId}`).reply(200, {
        results: [
          {
            file_id: 'file-1',
            filename: 'good.js',
            status: 'success',
            issues: []
          },
          {
            file_id: 'file-2',
            filename: 'bad.js',
            status: 'failed',
            error: 'Analysis timeout'
          }
        ]
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      const files = [
        new File(['good code'], 'good.js', { type: 'text/javascript' }),
        new File(['bad code'], 'bad.js', { type: 'text/javascript' })
      ];

      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, files);

      const analyzeButton = screen.getByRole('button', { name: /analyze all/i });
      await user.click(analyzeButton);

      // Wait for completion
      await waitFor(() => {
        expect(screen.getByText(/completed with errors/i)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Verify error details
      expect(screen.getByText(/analysis timeout/i)).toBeInTheDocument();

      // Verify retry option for failed file
      const retryButton = screen.getByRole('button', { name: /retry.*bad\.js/i });
      expect(retryButton).toBeInTheDocument();
    });

    it('allows filtering results by filename', async () => {
      const batchId = 'batch-filter';

      mockAxios.onPost('/api/v1/files/upload-multiple').reply(200, {
        batch_id: batchId,
        files: [
          { file_id: 'file-1', filename: 'app.js' },
          { file_id: 'file-2', filename: 'test.js' }
        ]
      });

      mockAxios.onGet(`/api/v1/files/upload-status/${batchId}`).reply(200, {
        status: 'completed',
        total_files: 2,
        processed_files: 2
      });

      mockAxios.onGet(`/api/v1/files/analysis-results/${batchId}`).reply(200, {
        results: [
          {
            filename: 'app.js',
            issues: [
              { line: 1, message: 'App issue' }
            ]
          },
          {
            filename: 'test.js',
            issues: [
              { line: 1, message: 'Test issue' }
            ]
          }
        ]
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      const files = [
        new File(['app'], 'app.js', { type: 'text/javascript' }),
        new File(['test'], 'test.js', { type: 'text/javascript' })
      ];

      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, files);

      const analyzeButton = screen.getByRole('button', { name: /analyze all/i });
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/analysis complete/i)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Filter by filename
      const filterInput = screen.getByPlaceholderText(/filter by filename/i);
      await user.type(filterInput, 'app.js');

      // Verify only app.js results are shown
      await waitFor(() => {
        expect(screen.getByText(/app issue/i)).toBeInTheDocument();
        expect(screen.queryByText(/test issue/i)).not.toBeInTheDocument();
      });

      // Clear filter
      await user.clear(filterInput);

      // Verify all results are shown again
      await waitFor(() => {
        expect(screen.getByText(/app issue/i)).toBeInTheDocument();
        expect(screen.getByText(/test issue/i)).toBeInTheDocument();
      });
    });
  });

  describe('File Upload Error Handling', () => {
    it('handles network errors during upload', async () => {
      mockAxios.onPost('/api/v1/files/upload-multiple').networkError();

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      const file = new File(['code'], 'test.js', { type: 'text/javascript' });
      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, file);

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      await user.click(analyzeButton);

      // Verify network error message
      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });

      // Verify retry option
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    it('handles server errors during upload', async () => {
      mockAxios.onPost('/api/v1/files/upload-multiple').reply(500, {
        detail: 'Internal server error'
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      const file = new File(['code'], 'test.js', { type: 'text/javascript' });
      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, file);

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      await user.click(analyzeButton);

      // Verify error message
      await waitFor(() => {
        expect(screen.getByText(/internal server error/i)).toBeInTheDocument();
      });
    });

    it('validates all files before starting batch upload', async () => {
      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      // Mix of valid and invalid files
      const files = [
        new File(['code'], 'valid.js', { type: 'text/javascript' }),
        new File(['exe'], 'invalid.exe', { type: 'application/x-msdownload' }),
        new File(['code'], 'valid2.py', { type: 'text/x-python' })
      ];

      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, files);

      // Verify validation errors for invalid files
      await waitFor(() => {
        expect(screen.getByText(/invalid\.exe.*invalid file type/i)).toBeInTheDocument();
      });

      // Verify analyze button shows warning
      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      expect(analyzeButton).toBeDisabled();
    });
  });
});
