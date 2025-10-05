import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import FileUploadComponent from '../FileUploadComponent.jsx';
import fileService from '../../services/fileService.js';
import * as fileUtils from '../../utils/fileUtils.ts';

// Mock the file service
vi.mock('../../services/fileService.js', () => ({
     default: {
          uploadFile: vi.fn()
     }
}));

// Mock file utils
vi.mock('../../utils/fileUtils.ts', () => ({
     validateFile: vi.fn(),
     formatFileSize: vi.fn(),
     isDragAndDropSupported: vi.fn()
}));

describe('FileUploadComponent', () => {
     const mockOnClose = vi.fn();
     const mockOnSuccess = vi.fn();

     beforeEach(() => {
          fileUtils.validateFile.mockReturnValue({ isValid: true });
          fileUtils.formatFileSize.mockImplementation((size) => `${size} bytes`);
          fileUtils.isDragAndDropSupported.mockReturnValue(true);
          fileService.uploadFile.mockResolvedValue({
               id: 'file-123',
               filename: 'test.txt',
               file_size: 100
          });
     });

     afterEach(() => {
          vi.clearAllMocks();
     });

     it('renders upload component correctly', () => {
          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          expect(screen.getByText('Upload Files')).toBeInTheDocument();
          expect(screen.getByText('Drop files here or click to browse')).toBeInTheDocument();
          expect(screen.getByText('Maximum 10 files, up to 1MB each')).toBeInTheDocument();
     });

     it('handles file selection from input', async () => {
          const user = userEvent.setup();
          const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });

          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          // Get the hidden file input
          const fileInput = screen.getByRole('button', { name: /drop files here or click to browse/i })
               .parentElement.querySelector('input[type="file"]');

          // Simulate file selection
          await user.upload(fileInput, mockFile);

          await waitFor(() => {
               expect(screen.getByText('test.txt')).toBeInTheDocument();
               expect(screen.getByText('Files to Upload (1/10)')).toBeInTheDocument();
          });

          expect(fileUtils.validateFile).toHaveBeenCalledWith(mockFile);
     });

     it('handles drag and drop', async () => {
          const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });

          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          const dropZone = screen.getByText('Drop files here or click to browse').closest('div');

          // Simulate drag enter
          fireEvent.dragEnter(dropZone, {
               dataTransfer: {
                    items: [mockFile],
                    types: ['Files']
               }
          });

          // Simulate drop
          fireEvent.drop(dropZone, {
               dataTransfer: {
                    files: [mockFile],
                    clearData: vi.fn()
               }
          });

          await waitFor(() => {
               expect(screen.getByText('test.txt')).toBeInTheDocument();
          });
     });

     it('validates files and shows errors', async () => {
          const user = userEvent.setup();
          const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });

          fileUtils.validateFile.mockReturnValue({
               isValid: false,
               error: 'File too large'
          });

          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          const fileInput = screen.getByRole('button', { name: /drop files here or click to browse/i })
               .parentElement.querySelector('input[type="file"]');

          await user.upload(fileInput, mockFile);

          await waitFor(() => {
               expect(screen.getByText('Upload Errors:')).toBeInTheDocument();
               expect(screen.getByText('test.txt: File too large')).toBeInTheDocument();
          });
     });

     it('prevents duplicate files', async () => {
          const user = userEvent.setup();
          const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });

          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          const fileInput = screen.getByRole('button', { name: /drop files here or click to browse/i })
               .parentElement.querySelector('input[type="file"]');

          // Upload same file twice
          await user.upload(fileInput, mockFile);
          await user.upload(fileInput, mockFile);

          await waitFor(() => {
               expect(screen.getByText('test.txt: File already added')).toBeInTheDocument();
          });
     });

     it('enforces maximum file limit', async () => {
          const user = userEvent.setup();
          const mockFiles = Array.from({ length: 12 }, (_, i) =>
               new File(['content'], `test${i}.txt`, { type: 'text/plain' })
          );

          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} maxFiles={10} />);

          const fileInput = screen.getByRole('button', { name: /drop files here or click to browse/i })
               .parentElement.querySelector('input[type="file"]');

          await user.upload(fileInput, mockFiles);

          await waitFor(() => {
               expect(screen.getByText(/Maximum 10 files allowed/)).toBeInTheDocument();
          });
     });

     it('removes files from queue', async () => {
          const user = userEvent.setup();
          const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });

          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          const fileInput = screen.getByRole('button', { name: /drop files here or click to browse/i })
               .parentElement.querySelector('input[type="file"]');

          await user.upload(fileInput, mockFile);

          await waitFor(() => {
               expect(screen.getByText('test.txt')).toBeInTheDocument();
          });

          // Remove file
          const removeButton = screen.getByTitle('Remove file');
          await user.click(removeButton);

          expect(screen.queryByText('test.txt')).not.toBeInTheDocument();
     });

     it('uploads files successfully', async () => {
          const user = userEvent.setup();
          const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });

          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          const fileInput = screen.getByRole('button', { name: /drop files here or click to browse/i })
               .parentElement.querySelector('input[type="file"]');

          await user.upload(fileInput, mockFile);

          await waitFor(() => {
               expect(screen.getByText('Upload Files')).toBeInTheDocument();
          });

          const uploadButton = screen.getByRole('button', { name: 'Upload Files' });
          await user.click(uploadButton);

          await waitFor(() => {
               expect(fileService.uploadFile).toHaveBeenCalledWith(mockFile, expect.any(Object));
               expect(mockOnSuccess).toHaveBeenCalledWith([{
                    id: 'file-123',
                    filename: 'test.txt',
                    file_size: 100
               }]);
          });
     });

     it('handles upload progress', async () => {
          const user = userEvent.setup();
          const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });

          fileService.uploadFile.mockImplementation((file, options) => {
               // Simulate progress
               if (options.onProgress) {
                    setTimeout(() => options.onProgress(50), 100);
                    setTimeout(() => options.onProgress(100), 200);
               }
               return Promise.resolve({
                    id: 'file-123',
                    filename: 'test.txt',
                    file_size: 100
               });
          });

          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          const fileInput = screen.getByRole('button', { name: /drop files here or click to browse/i })
               .parentElement.querySelector('input[type="file"]');

          await user.upload(fileInput, mockFile);

          const uploadButton = screen.getByRole('button', { name: 'Upload Files' });
          await user.click(uploadButton);

          // Should show uploading state
          await waitFor(() => {
               expect(screen.getByText('Uploading...')).toBeInTheDocument();
          });

          // Should show progress
          await waitFor(() => {
               expect(screen.getByText('50% uploaded')).toBeInTheDocument();
          }, { timeout: 200 });
     });

     it('handles upload errors', async () => {
          const user = userEvent.setup();
          const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });

          fileService.uploadFile.mockRejectedValue(new Error('Upload failed'));

          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          const fileInput = screen.getByRole('button', { name: /drop files here or click to browse/i })
               .parentElement.querySelector('input[type="file"]');

          await user.upload(fileInput, mockFile);

          const uploadButton = screen.getByRole('button', { name: 'Upload Files' });
          await user.click(uploadButton);

          await waitFor(() => {
               expect(screen.getByText('test.txt: Upload failed')).toBeInTheDocument();
          });

          // Should not call onSuccess
          expect(mockOnSuccess).not.toHaveBeenCalled();
     });

     it('shows completed status for uploaded files', async () => {
          const user = userEvent.setup();
          const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });

          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          const fileInput = screen.getByRole('button', { name: /drop files here or click to browse/i })
               .parentElement.querySelector('input[type="file"]');

          await user.upload(fileInput, mockFile);

          const uploadButton = screen.getByRole('button', { name: 'Upload Files' });
          await user.click(uploadButton);

          await waitFor(() => {
               expect(screen.getByText('1 of 1 files uploaded')).toBeInTheDocument();
               expect(screen.getByText('Close')).toBeInTheDocument();
          });
     });

     it('closes modal when close button is clicked', async () => {
          const user = userEvent.setup();
          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          const closeButton = screen.getByRole('button', { name: /close/i });
          await user.click(closeButton);

          expect(mockOnClose).toHaveBeenCalled();
     });

     it('disables upload when no files selected', () => {
          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          const uploadButton = screen.queryByRole('button', { name: 'Upload Files' });
          expect(uploadButton).not.toBeInTheDocument();
     });

     it('shows different file icons based on file type', async () => {
          const user = userEvent.setup();
          const mockFiles = [
               new File(['content'], 'test.js', { type: 'text/javascript' }),
               new File(['content'], 'image.png', { type: 'image/png' }),
               new File(['content'], 'document.pdf', { type: 'application/pdf' })
          ];

          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          const fileInput = screen.getByRole('button', { name: /drop files here or click to browse/i })
               .parentElement.querySelector('input[type="file"]');

          for (const file of mockFiles) {
               await user.upload(fileInput, file);
          }

          await waitFor(() => {
               expect(screen.getByText('test.js')).toBeInTheDocument();
               expect(screen.getByText('image.png')).toBeInTheDocument();
               expect(screen.getByText('document.pdf')).toBeInTheDocument();
          });
     });

     it('handles drag and drop when not supported', () => {
          fileUtils.isDragAndDropSupported.mockReturnValue(false);

          render(<FileUploadComponent onClose={mockOnClose} onSuccess={mockOnSuccess} />);

          expect(screen.getByText('Click to select files')).toBeInTheDocument();
     });
});