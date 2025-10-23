import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MultiFileUploadZone from '../MultiFileUploadZone';
import analysisService from '../../services/analysisService';

// Mock the analysis service
vi.mock('../../services/analysisService', () => ({
  default: {
    validateFile: vi.fn(),
    detectLanguageFromFilename: vi.fn(),
    uploadMultipleFiles: vi.fn()
  }
}));

describe('MultiFileUploadZone', () => {
  const mockOnUploadComplete = vi.fn();
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock implementations
    analysisService.validateFile.mockImplementation(() => true);
    analysisService.detectLanguageFromFilename.mockImplementation((filename) => {
      const ext = filename.split('.').pop();
      return ext === 'py' ? 'python' : ext === 'js' ? 'javascript' : 'unknown';
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should render the upload zone', () => {
    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Upload Code Files')).toBeInTheDocument();
    expect(screen.getByText(/Drop files here or click to browse/i)).toBeInTheDocument();
  });

  it('should display max files limit', () => {
    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
        maxFiles={5}
      />
    );

    expect(screen.getByText(/Maximum 5 files/i)).toBeInTheDocument();
  });

  it('should handle file selection', async () => {
    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    const file = new File(['console.log("test")'], 'test.js', { type: 'text/javascript' });
    const input = document.querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByText('test.js')).toBeInTheDocument();
    });
  });

  it('should validate files on selection', async () => {
    analysisService.validateFile.mockImplementation((file) => {
      if (file.size > 5 * 1024 * 1024) {
        throw new Error('File size exceeds maximum');
      }
    });

    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    const largeFile = new File(['x'.repeat(6 * 1024 * 1024)], 'large.js', { type: 'text/javascript' });
    const input = document.querySelector('input[type="file"]');

    await userEvent.upload(input, largeFile);

    await waitFor(() => {
      expect(screen.getByText(/File Validation Errors/i)).toBeInTheDocument();
    });
  });

  it('should prevent duplicate files', async () => {
    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    const file = new File(['test'], 'test.js', { type: 'text/javascript' });
    const input = document.querySelector('input[type="file"]');

    // Upload same file twice
    await userEvent.upload(input, file);
    
    await waitFor(() => {
      expect(screen.getByText('test.js')).toBeInTheDocument();
    });

    // Try to upload the same file again
    await userEvent.upload(input, file);

    // The component should still only show 1 file (duplicate prevented)
    await waitFor(() => {
      const fileItems = screen.getAllByText('test.js');
      expect(fileItems).toHaveLength(1);
    });
  });

  it('should enforce max files limit', async () => {
    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
        maxFiles={2}
      />
    );

    const files = [
      new File(['test1'], 'test1.js', { type: 'text/javascript' }),
      new File(['test2'], 'test2.js', { type: 'text/javascript' }),
      new File(['test3'], 'test3.js', { type: 'text/javascript' })
    ];

    const input = document.querySelector('input[type="file"]');
    await userEvent.upload(input, files);

    await waitFor(() => {
      expect(screen.getByText(/Maximum 2 files allowed/i)).toBeInTheDocument();
    });
  });

  it('should remove files from queue', async () => {
    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    const file = new File(['test'], 'test.js', { type: 'text/javascript' });
    const input = document.querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByText('test.js')).toBeInTheDocument();
    });

    const removeButton = screen.getByTitle('Remove file');
    fireEvent.click(removeButton);

    await waitFor(() => {
      expect(screen.queryByText('test.js')).not.toBeInTheDocument();
    });
  });

  it('should upload files successfully', async () => {
    analysisService.uploadMultipleFiles.mockResolvedValue({
      batchId: 'batch-123',
      files: [
        { filename: 'test.js', status: 'completed' }
      ],
      total_files: 1
    });

    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    const file = new File(['test'], 'test.js', { type: 'text/javascript' });
    const input = document.querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    const uploadButton = screen.getByText('Upload Files');
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(analysisService.uploadMultipleFiles).toHaveBeenCalled();
      expect(mockOnUploadComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          batchId: 'batch-123'
        })
      );
    });
  });

  it('should handle upload errors', async () => {
    analysisService.uploadMultipleFiles.mockRejectedValue(
      new Error('Upload failed')
    );

    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    const file = new File(['test'], 'test.js', { type: 'text/javascript' });
    const input = document.querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    const uploadButton = screen.getByText('Upload Files');
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByText(/Upload failed/i)).toBeInTheDocument();
    });
  });

  it('should show upload progress', async () => {
    let progressCallback;
    analysisService.uploadMultipleFiles.mockImplementation((files, options) => {
      progressCallback = options.onProgress;
      return new Promise((resolve) => {
        setTimeout(() => {
          progressCallback(0, 50);
          setTimeout(() => {
            progressCallback(0, 100);
            resolve({
              batchId: 'batch-123',
              files: [{ filename: 'test.js', status: 'completed' }]
            });
          }, 100);
        }, 100);
      });
    });

    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    const file = new File(['test'], 'test.js', { type: 'text/javascript' });
    const input = document.querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    const uploadButton = screen.getByText('Upload Files');
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByText(/50% uploaded/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should handle drag and drop', async () => {
    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    const dropZone = screen.getByText(/Drop files here or click to browse/i).closest('div');
    const file = new File(['test'], 'test.js', { type: 'text/javascript' });

    fireEvent.dragEnter(dropZone, {
      dataTransfer: {
        items: [{ kind: 'file', type: 'text/javascript' }],
        files: [file]
      }
    });

    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [file],
        clearData: vi.fn()
      }
    });

    await waitFor(() => {
      expect(screen.getByText('test.js')).toBeInTheDocument();
    });
  });

  it('should retry failed uploads', async () => {
    let callCount = 0;
    analysisService.uploadMultipleFiles.mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.reject(new Error('Upload failed'));
      }
      return Promise.resolve({
        batchId: 'batch-123',
        files: [{ filename: 'test.js', status: 'completed' }]
      });
    });

    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    const file = new File(['test'], 'test.js', { type: 'text/javascript' });
    const input = document.querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    const uploadButton = screen.getByText('Upload Files');
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByText(/Retry Failed/i)).toBeInTheDocument();
    });

    const retryButton = screen.getByText(/Retry Failed/i);
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(mockOnUploadComplete).toHaveBeenCalled();
    });
  });

  it('should close modal', () => {
    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    const closeButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should detect file language', async () => {
    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    const file = new File(['print("test")'], 'test.py', { type: 'text/x-python' });
    const input = document.querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    await waitFor(() => {
      // Look for the specific text that shows the language for the file
      expect(screen.getByText(/13 B • python/i)).toBeInTheDocument();
    });
  });

  it('should format file sizes correctly', async () => {
    render(
      <MultiFileUploadZone 
        onUploadComplete={mockOnUploadComplete}
        onClose={mockOnClose}
      />
    );

    const file = new File(['x'.repeat(1024 * 1024)], 'test.js', { type: 'text/javascript' });
    const input = document.querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByText(/1\.0 MB/i)).toBeInTheDocument();
    });
  });
});
