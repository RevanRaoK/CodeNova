import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MultiFileUploadZone from '../../components/MultiFileUploadZone';
import analysisService from '../../services/analysisService';

vi.mock('../../services/analysisService', () => ({
  default: {
    validateFile: vi.fn(),
    detectLanguageFromFilename: vi.fn(),
    uploadMultipleFiles: vi.fn()
  }
}));

describe('File Upload Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    analysisService.validateFile.mockImplementation(() => true);
    analysisService.detectLanguageFromFilename.mockImplementation((filename) => {
      const ext = filename.split('.').pop();
      return ext === 'py' ? 'python' : 'javascript';
    });
  });

  it('should complete full upload workflow', async () => {
    const onUploadComplete = vi.fn();
    const onClose = vi.fn();

    analysisService.uploadMultipleFiles.mockResolvedValue({
      batchId: 'batch-123',
      files: [
        { filename: 'test1.js', status: 'completed' },
        { filename: 'test2.py', status: 'completed' }
      ],
      total_files: 2
    });

    render(
      <MultiFileUploadZone 
        onUploadComplete={onUploadComplete}
        onClose={onClose}
      />
    );

    // Select files
    const files = [
      new File(['console.log("test")'], 'test1.js', { type: 'text/javascript' }),
      new File(['print("test")'], 'test2.py', { type: 'text/x-python' })
    ];

    const input = document.querySelector('input[type="file"]');
    await userEvent.upload(input, files);

    // Verify files are displayed
    await waitFor(() => {
      expect(screen.getByText('test1.js')).toBeInTheDocument();
      expect(screen.getByText('test2.py')).toBeInTheDocument();
    });

    // Upload files
    const uploadButton = screen.getByText('Upload Files');
    fireEvent.click(uploadButton);

    // Verify upload completion
    await waitFor(() => {
      expect(onUploadComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          batchId: 'batch-123',
          total_files: 2
        })
      );
    });
  });

  it('should handle validation and retry workflow', async () => {
    const onUploadComplete = vi.fn();
    let uploadAttempts = 0;

    analysisService.uploadMultipleFiles.mockImplementation(() => {
      uploadAttempts++;
      if (uploadAttempts === 1) {
        return Promise.reject(new Error('Network error'));
      }
      return Promise.resolve({
        batchId: 'batch-123',
        files: [{ filename: 'test.js', status: 'completed' }]
      });
    });

    render(
      <MultiFileUploadZone 
        onUploadComplete={onUploadComplete}
        onClose={vi.fn()}
      />
    );

    // Upload file
    const file = new File(['test'], 'test.js', { type: 'text/javascript' });
    const input = document.querySelector('input[type="file"]');
    await userEvent.upload(input, file);

    const uploadButton = screen.getByText('Upload Files');
    fireEvent.click(uploadButton);

    // Wait for error
    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });

    // Retry
    const retryButton = screen.getByText(/Retry Failed/i);
    fireEvent.click(retryButton);

    // Verify success
    await waitFor(() => {
      expect(onUploadComplete).toHaveBeenCalled();
    });
  });
});
