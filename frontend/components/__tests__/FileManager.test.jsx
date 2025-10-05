import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import FileManager from '../FileManager.jsx';
import fileService from '../../services/fileService.js';

// Mock the file service
vi.mock('../../services/fileService.js', () => ({
     default: {
          getFiles: vi.fn(),
          deleteFile: vi.fn(),
          deleteMultipleFiles: vi.fn(),
          getDownloadUrl: vi.fn(),
          getFilePreview: vi.fn()
     }
}));

// Mock child components to avoid complex rendering issues
vi.mock('../FileUploadComponent.jsx', () => ({
     default: ({ onClose, onSuccess }) => (
          <div data-testid="file-upload-modal">
               <button onClick={() => onSuccess([{ id: 'new-file', filename: 'new.txt' }])}>
                    Upload Success
               </button>
               <button onClick={onClose}>Close</button>
          </div>
     )
}));

vi.mock('../FilePreviewModal.jsx', () => ({
     default: ({ file, onClose }) => (
          <div data-testid="file-preview-modal">
               <span>Preview: {file.filename}</span>
               <button onClick={onClose}>Close Preview</button>
          </div>
     )
}));

vi.mock('../ConfirmationDialog.jsx', () => ({
     default: ({ title, message, onConfirm, onCancel }) => (
          <div data-testid="confirmation-dialog">
               <h3>{title}</h3>
               <p>{message}</p>
               <button onClick={onConfirm}>Confirm</button>
               <button onClick={onCancel}>Cancel</button>
          </div>
     )
}));

vi.mock('../Toast.jsx', () => ({
     default: ({ message, type, onClose }) => (
          <div data-testid="toast" className={`toast-${type}`}>
               {message}
               <button onClick={onClose}>Close Toast</button>
          </div>
     )
}));

describe('FileManager', () => {
     const mockFiles = [
          {
               id: 'file-1',
               filename: 'test.js',
               file_size: 1024,
               content_type: 'text/javascript',
               created_at: '2024-01-01T00:00:00Z'
          },
          {
               id: 'file-2',
               filename: 'image.png',
               file_size: 2048,
               content_type: 'image/png',
               created_at: '2024-01-02T00:00:00Z'
          }
     ];

     const mockFilesResponse = {
          files: mockFiles,
          total: 2,
          total_pages: 1
     };

     beforeEach(() => {
          fileService.getFiles.mockResolvedValue(mockFilesResponse);
          fileService.deleteFile.mockResolvedValue({ success: true });
          fileService.deleteMultipleFiles.mockResolvedValue({ success: true });
          fileService.getDownloadUrl.mockResolvedValue({ url: 'https://example.com/download' });
     });

     afterEach(() => {
          vi.clearAllMocks();
     });

     it('renders file manager with basic elements', async () => {
          render(<FileManager />);

          expect(screen.getByText('File Manager')).toBeInTheDocument();
          expect(screen.getByText('Manage your uploaded files and documents')).toBeInTheDocument();
          expect(screen.getByText('Upload Files')).toBeInTheDocument();
     });

     it('shows loading state initially', () => {
          render(<FileManager />);
          expect(screen.getByText('Loading files...')).toBeInTheDocument();
     });

     it('shows error state when loading fails', async () => {
          fileService.getFiles.mockRejectedValue(new Error('Network error'));

          render(<FileManager />);

          await waitFor(() => {
               expect(screen.getByText('Failed to load files. Please try again.')).toBeInTheDocument();
          });
     });

     it('shows empty state when no files', async () => {
          fileService.getFiles.mockResolvedValue({ files: [], total: 0, total_pages: 0 });

          render(<FileManager />);

          await waitFor(() => {
               expect(screen.getByText('No files uploaded yet.')).toBeInTheDocument();
          });
     });

     it('renders files when loaded successfully', async () => {
          render(<FileManager />);

          await waitFor(() => {
               expect(screen.getByText('test.js')).toBeInTheDocument();
               expect(screen.getByText('image.png')).toBeInTheDocument();
          });

          expect(fileService.getFiles).toHaveBeenCalledWith({
               page: 1,
               limit: 20,
               search: '',
               fileType: '',
               sortBy: 'created_at',
               sortOrder: 'desc'
          });
     });

     it('opens upload modal when upload button is clicked', async () => {
          const user = userEvent.setup();
          render(<FileManager />);

          const uploadButton = screen.getByText('Upload Files');
          await user.click(uploadButton);

          expect(screen.getByTestId('file-upload-modal')).toBeInTheDocument();
     });

     it('handles search functionality', async () => {
          const user = userEvent.setup();
          render(<FileManager />);

          await waitFor(() => {
               expect(screen.getByText('test.js')).toBeInTheDocument();
          });

          const searchInput = screen.getByPlaceholderText('Search files...');
          await user.type(searchInput, 'test');

          const form = searchInput.closest('form');
          fireEvent.submit(form);

          await waitFor(() => {
               expect(fileService.getFiles).toHaveBeenCalledWith(
                    expect.objectContaining({
                         search: 'test'
                    })
               );
          });
     });

     it('handles file preview', async () => {
          const user = userEvent.setup();
          render(<FileManager />);

          await waitFor(() => {
               expect(screen.getByText('test.js')).toBeInTheDocument();
          });

          const previewButtons = screen.getAllByTitle('Preview');
          await user.click(previewButtons[0]);

          expect(screen.getByTestId('file-preview-modal')).toBeInTheDocument();
          expect(screen.getByText('Preview: test.js')).toBeInTheDocument();
     });

     it('handles file deletion confirmation', async () => {
          const user = userEvent.setup();
          render(<FileManager />);

          await waitFor(() => {
               expect(screen.getByText('test.js')).toBeInTheDocument();
          });

          const deleteButtons = screen.getAllByTitle('Delete');
          await user.click(deleteButtons[0]);

          expect(screen.getByTestId('confirmation-dialog')).toBeInTheDocument();
          expect(screen.getByText('Delete Files')).toBeInTheDocument();
     });
});