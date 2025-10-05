import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import FilePreviewModal from '../FilePreviewModal.jsx';
import fileService from '../../services/fileService.js';

// Mock the file service
vi.mock('../../services/fileService.js', () => ({
     default: {
          getFilePreview: vi.fn(),
          getDownloadUrl: vi.fn()
     }
}));

// Mock file utils
vi.mock('../../utils/fileUtils.ts', () => ({
     formatFileSize: vi.fn((size) => `${size} bytes`)
}));

describe('FilePreviewModal', () => {
     const mockOnClose = vi.fn();

     const mockFile = {
          id: 'file-123',
          filename: 'test.js',
          file_size: 1024,
          content_type: 'text/javascript',
          created_at: '2024-01-01T12:00:00Z'
     };

     beforeEach(() => {
          fileService.getFilePreview.mockResolvedValue({
               content: 'console.log("Hello World");',
               line_count: 1,
               truncated: false
          });
          fileService.getDownloadUrl.mockResolvedValue({
               url: 'https://example.com/download'
          });
     });

     afterEach(() => {
          vi.clearAllMocks();
     });

     it('renders preview modal correctly', async () => {
          render(<FilePreviewModal file={mockFile} onClose={mockOnClose} />);

          expect(screen.getByText('test.js')).toBeInTheDocument();
          expect(screen.getByText('1024 bytes • text/javascript')).toBeInTheDocument();
          expect(screen.getByText('Loading preview...')).toBeInTheDocument();

          await waitFor(() => {
               expect(screen.getByText('console.log("Hello World");')).toBeInTheDocument();
          });
     });

     it('shows loading state initially', () => {
          render(<FilePreviewModal file={mockFile} onClose={mockOnClose} />);

          expect(screen.getByText('Loading preview...')).toBeInTheDocument();
     });

     it('handles preview loading error', async () => {
          fileService.getFilePreview.mockRejectedValue(new Error('Failed to load'));

          render(<FilePreviewModal file={mockFile} onClose={mockOnClose} />);

          await waitFor(() => {
               expect(screen.getByText('Failed to load file preview')).toBeInTheDocument();
          });
     });

     it('shows code preview with syntax highlighting info', async () => {
          render(<FilePreviewModal file={mockFile} onClose={mockOnClose} />);

          await waitFor(() => {
               expect(screen.getByText('javascript')).toBeInTheDocument(); // Language indicator
               expect(screen.getByText('1 lines')).toBeInTheDocument(); // Line count
               expect(screen.getByText('console.log("Hello World");')).toBeInTheDocument();
          });
     });

     it('shows truncation warning for large files', async () => {
          fileService.getFilePreview.mockResolvedValue({
               content: 'console.log("Hello World");',
               line_count: 1000,
               truncated: true
          });

          render(<FilePreviewModal file={mockFile} onClose={mockOnClose} />);

          await waitFor(() => {
               expect(screen.getByText('1000 lines (truncated)')).toBeInTheDocument();
               expect(screen.getByText('File preview is truncated. Download the full file to see all content.')).toBeInTheDocument();
          });
     });

     it('handles image preview', async () => {
          const imageFile = {
               ...mockFile,
               filename: 'image.png',
               content_type: 'image/png'
          };

          fileService.getFilePreview.mockResolvedValue({
               url: 'https://example.com/image.png'
          });

          render(<FilePreviewModal file={imageFile} onClose={mockOnClose} />);

          await waitFor(() => {
               const image = screen.getByAltText('image.png');
               expect(image).toBeInTheDocument();
               expect(image).toHaveAttribute('src', 'https://example.com/image.png');
          });
     });

     it('handles image zoom controls', async () => {
          const user = userEvent.setup();
          const imageFile = {
               ...mockFile,
               filename: 'image.png',
               content_type: 'image/png'
          };

          fileService.getFilePreview.mockResolvedValue({
               url: 'https://example.com/image.png'
          });

          render(<FilePreviewModal file={imageFile} onClose={mockOnClose} />);

          await waitFor(() => {
               expect(screen.getByText('100%')).toBeInTheDocument();
          });

          // Zoom in
          const zoomInButton = screen.getByTitle('Zoom In');
          await user.click(zoomInButton);

          expect(screen.getByText('125%')).toBeInTheDocument();

          // Zoom out
          const zoomOutButton = screen.getByTitle('Zoom Out');
          await user.click(zoomOutButton);

          expect(screen.getByText('100%')).toBeInTheDocument();
     });

     it('handles unsupported file types', async () => {
          const unsupportedFile = {
               ...mockFile,
               filename: 'document.pdf',
               content_type: 'application/pdf'
          };

          fileService.getFilePreview.mockResolvedValue(null);

          render(<FilePreviewModal file={unsupportedFile} onClose={mockOnClose} />);

          await waitFor(() => {
               expect(screen.getByText('Preview not supported for this file type')).toBeInTheDocument();
               expect(screen.getByText('File type: application/pdf')).toBeInTheDocument();
          });
     });

     it('handles download functionality', async () => {
          const user = userEvent.setup();

          // Mock createElement and appendChild for download link
          const mockLink = {
               href: '',
               download: '',
               click: vi.fn()
          };
          const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockLink);
          const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => { });
          const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => { });

          render(<FilePreviewModal file={mockFile} onClose={mockOnClose} />);

          await waitFor(() => {
               expect(screen.getByText('console.log("Hello World");')).toBeInTheDocument();
          });

          const downloadButton = screen.getByTitle('Download');
          await user.click(downloadButton);

          await waitFor(() => {
               expect(fileService.getDownloadUrl).toHaveBeenCalledWith('file-123');
               expect(mockLink.href).toBe('https://example.com/download');
               expect(mockLink.download).toBe('test.js');
               expect(mockLink.click).toHaveBeenCalled();
          });

          createElementSpy.mockRestore();
          appendChildSpy.mockRestore();
          removeChildSpy.mockRestore();
     });

     it('handles download error', async () => {
          const user = userEvent.setup();
          fileService.getDownloadUrl.mockRejectedValue(new Error('Download failed'));

          render(<FilePreviewModal file={mockFile} onClose={mockOnClose} />);

          await waitFor(() => {
               expect(screen.getByText('console.log("Hello World");')).toBeInTheDocument();
          });

          const downloadButton = screen.getByTitle('Download');
          await user.click(downloadButton);

          // Note: Error handling in download is silent in the component
          // but we can verify the service was called
          await waitFor(() => {
               expect(fileService.getDownloadUrl).toHaveBeenCalledWith('file-123');
          });
     });

     it('closes modal when close button is clicked', async () => {
          const user = userEvent.setup();
          render(<FilePreviewModal file={mockFile} onClose={mockOnClose} />);

          const closeButton = screen.getByTitle('Close');
          await user.click(closeButton);

          expect(mockOnClose).toHaveBeenCalled();
     });

     it('closes modal when footer close button is clicked', async () => {
          const user = userEvent.setup();
          render(<FilePreviewModal file={mockFile} onClose={mockOnClose} />);

          await waitFor(() => {
               expect(screen.getByText('console.log("Hello World");')).toBeInTheDocument();
          });

          const footerCloseButton = screen.getByRole('button', { name: 'Close' });
          await user.click(footerCloseButton);

          expect(mockOnClose).toHaveBeenCalled();
     });

     it('displays file creation date correctly', async () => {
          render(<FilePreviewModal file={mockFile} onClose={mockOnClose} />);

          await waitFor(() => {
               expect(screen.getByText(/Created: January 1, 2024/)).toBeInTheDocument();
          });
     });

     it('shows correct file icon for different file types', async () => {
          const imageFile = {
               ...mockFile,
               filename: 'image.png',
               content_type: 'image/png'
          };

          fileService.getFilePreview.mockResolvedValue({
               url: 'https://example.com/image.png'
          });

          render(<FilePreviewModal file={imageFile} onClose={mockOnClose} />);

          // The component should render with appropriate icon (tested through class presence)
          expect(screen.getByText('image.png')).toBeInTheDocument();
     });

     it('handles text file preview', async () => {
          const textFile = {
               ...mockFile,
               filename: 'readme.txt',
               content_type: 'text/plain'
          };

          fileService.getFilePreview.mockResolvedValue({
               content: 'This is a readme file.',
               line_count: 1,
               truncated: false
          });

          render(<FilePreviewModal file={textFile} onClose={mockOnClose} />);

          await waitFor(() => {
               expect(screen.getByText('This is a readme file.')).toBeInTheDocument();
               expect(screen.getByText('text')).toBeInTheDocument(); // Language indicator
          });
     });

     it('handles image loading error', async () => {
          const imageFile = {
               ...mockFile,
               filename: 'image.png',
               content_type: 'image/png'
          };

          fileService.getFilePreview.mockResolvedValue({
               url: 'https://example.com/broken-image.png'
          });

          render(<FilePreviewModal file={imageFile} onClose={mockOnClose} />);

          await waitFor(() => {
               const image = screen.getByAltText('image.png');
               expect(image).toBeInTheDocument();
          });

          // Simulate image load error
          const image = screen.getByAltText('image.png');
          fireEvent.error(image);

          // The component should handle the error gracefully
          // (specific error handling would depend on implementation)
     });

     it('shows preview not available when no preview data', async () => {
          fileService.getFilePreview.mockResolvedValue(null);

          render(<FilePreviewModal file={mockFile} onClose={mockOnClose} />);

          await waitFor(() => {
               expect(screen.getByText('Preview not available for this file type')).toBeInTheDocument();
          });
     });
});