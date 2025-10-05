import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import httpClient from '../httpClient.js';
import fileService from '../fileService.js';

describe('FileService', () => {
  let mockAxios;

  beforeEach(() => {
    mockAxios = new MockAdapter(httpClient);
  });

  afterEach(() => {
    mockAxios.restore();
    vi.clearAllMocks();
  });

  describe('uploadFile', () => {
    it('should upload a file successfully', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      const mockResponse = {
        id: 'file-123',
        filename: 'test.txt',
        file_size: 12,
        content_type: 'text/plain',
        spaces_url: 'https://spaces.example.com/file-123'
      };

      mockAxios.onPost('/api/files/upload').reply(200, mockResponse);

      const result = await fileService.uploadFile(mockFile);

      expect(result).toEqual(mockResponse);
      expect(mockAxios.history.post).toHaveLength(1);
      expect(mockAxios.history.post[0].url).toBe('/api/files/upload');
    });

    it('should handle upload progress callback', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      const mockResponse = { id: 'file-123' };
      const onProgress = vi.fn();

      mockAxios.onPost('/api/files/upload').reply((config) => {
        // Simulate progress event
        if (config.onUploadProgress) {
          config.onUploadProgress({ loaded: 50, total: 100 });
        }
        return [200, mockResponse];
      });

      await fileService.uploadFile(mockFile, { onProgress });

      expect(onProgress).toHaveBeenCalledWith(50);
    });

    it('should handle upload error', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      
      mockAxios.onPost('/api/files/upload').reply(400, {
        message: 'File too large'
      });

      await expect(fileService.uploadFile(mockFile)).rejects.toThrow();
    });
  });

  describe('uploadMultipleFiles', () => {
    it('should upload multiple files successfully', async () => {
      const mockFiles = [
        new File(['content 1'], 'test1.txt', { type: 'text/plain' }),
        new File(['content 2'], 'test2.txt', { type: 'text/plain' })
      ];
      const mockResponses = [
        { id: 'file-123', filename: 'test1.txt' },
        { id: 'file-124', filename: 'test2.txt' }
      ];

      // Mock each request separately with different responses
      mockAxios.onPost('/api/files/upload').replyOnce(200, mockResponses[0]);
      mockAxios.onPost('/api/files/upload').replyOnce(200, mockResponses[1]);

      const results = await fileService.uploadMultipleFiles(mockFiles);

      expect(results).toHaveLength(2);
      expect(results).toEqual(expect.arrayContaining(mockResponses));
    });
  });

  describe('getFiles', () => {
    it('should fetch files with default parameters', async () => {
      const mockResponse = {
        files: [
          { id: 'file-123', filename: 'test.txt' },
          { id: 'file-124', filename: 'test2.txt' }
        ],
        total: 2,
        total_pages: 1
      };

      mockAxios.onGet().reply(200, mockResponse);

      const result = await fileService.getFiles();

      expect(result).toEqual(mockResponse);
      expect(mockAxios.history.get[0].url).toContain('/api/files?');
    });

    it('should fetch files with filters', async () => {
      const filters = {
        page: 2,
        limit: 10,
        search: 'test',
        fileType: 'image',
        sortBy: 'filename',
        sortOrder: 'asc'
      };

      mockAxios.onGet().reply(200, { files: [] });

      await fileService.getFiles(filters);

      const url = mockAxios.history.get[0].url;
      expect(url).toContain('page=2');
      expect(url).toContain('limit=10');
      expect(url).toContain('search=test');
      expect(url).toContain('file_type=image');
      expect(url).toContain('sort_by=filename');
      expect(url).toContain('sort_order=asc');
    });
  });

  describe('getFileById', () => {
    it('should fetch file by ID', async () => {
      const mockFile = { id: 'file-123', filename: 'test.txt' };
      
      mockAxios.onGet('/api/files/file-123').reply(200, mockFile);

      const result = await fileService.getFileById('file-123');

      expect(result).toEqual(mockFile);
    });
  });

  describe('getDownloadUrl', () => {
    it('should get download URL for file', async () => {
      const mockResponse = {
        url: 'https://spaces.example.com/signed-url',
        expires_at: '2024-01-01T00:00:00Z'
      };
      
      mockAxios.onGet('/api/files/file-123/download').reply(200, mockResponse);

      const result = await fileService.getDownloadUrl('file-123');

      expect(result).toEqual(mockResponse);
    });
  });

  describe('downloadFile', () => {
    it('should download file content as blob', async () => {
      const mockBlob = new Blob(['file content'], { type: 'text/plain' });
      
      mockAxios.onGet('/api/files/file-123/content').reply(200, mockBlob);

      const result = await fileService.downloadFile('file-123');

      expect(result).toBeInstanceOf(Blob);
      expect(mockAxios.history.get[0].responseType).toBe('blob');
    });
  });

  describe('deleteFile', () => {
    it('should delete a file successfully', async () => {
      const mockResponse = { success: true, message: 'File deleted' };
      
      mockAxios.onDelete('/api/files/file-123').reply(200, mockResponse);

      const result = await fileService.deleteFile('file-123');

      expect(result).toEqual(mockResponse);
    });
  });

  describe('deleteMultipleFiles', () => {
    it('should delete multiple files successfully', async () => {
      const fileIds = ['file-123', 'file-124'];
      const mockResponse = { success: true, deleted_count: 2 };
      
      mockAxios.onDelete('/api/files/bulk').reply(200, mockResponse);

      const result = await fileService.deleteMultipleFiles(fileIds);

      expect(result).toEqual(mockResponse);
      expect(JSON.parse(mockAxios.history.delete[0].data)).toEqual({
        file_ids: fileIds
      });
    });
  });

  describe('updateFileMetadata', () => {
    it('should update file metadata', async () => {
      const metadata = { description: 'Updated description' };
      const mockResponse = { id: 'file-123', ...metadata };
      
      mockAxios.onPatch('/api/files/file-123').reply(200, mockResponse);

      const result = await fileService.updateFileMetadata('file-123', metadata);

      expect(result).toEqual(mockResponse);
      expect(JSON.parse(mockAxios.history.patch[0].data)).toEqual(metadata);
    });
  });

  describe('getFilePreview', () => {
    it('should get file preview with default options', async () => {
      const mockPreview = {
        content: 'file content preview',
        line_count: 10,
        truncated: false
      };
      
      mockAxios.onGet().reply(200, mockPreview);

      const result = await fileService.getFilePreview('file-123');

      expect(result).toEqual(mockPreview);
      expect(mockAxios.history.get[0].url).toContain('/api/files/file-123/preview?');
    });

    it('should get file preview with options', async () => {
      const options = { maxLines: 500, format: 'html' };
      
      mockAxios.onGet().reply(200, { content: 'preview' });

      await fileService.getFilePreview('file-123', options);

      const url = mockAxios.history.get[0].url;
      expect(url).toContain('max_lines=500');
      expect(url).toContain('format=html');
    });
  });

  describe('getStorageUsage', () => {
    it('should get storage usage statistics', async () => {
      const mockUsage = {
        total_files: 10,
        total_size: 1024000,
        used_space: '1.02 MB',
        available_space: '98.98 MB'
      };
      
      mockAxios.onGet('/api/files/usage').reply(200, mockUsage);

      const result = await fileService.getStorageUsage();

      expect(result).toEqual(mockUsage);
    });
  });

  describe('searchFiles', () => {
    it('should search files with query', async () => {
      const query = 'test';
      const mockResults = {
        files: [{ id: 'file-123', filename: 'test.txt' }],
        total: 1
      };
      
      mockAxios.onGet().reply(200, mockResults);

      const result = await fileService.searchFiles(query);

      expect(result).toEqual(mockResults);
      const url = mockAxios.history.get[0].url;
      expect(url).toContain('q=test');
    });

    it('should search files with filters', async () => {
      const query = 'test';
      const filters = {
        fileType: 'image',
        dateFrom: '2024-01-01',
        dateTo: '2024-01-31',
        page: 1,
        limit: 20
      };
      
      mockAxios.onGet().reply(200, { files: [] });

      await fileService.searchFiles(query, filters);

      const url = mockAxios.history.get[0].url;
      expect(url).toContain('q=test');
      expect(url).toContain('file_type=image');
      expect(url).toContain('date_from=2024-01-01');
      expect(url).toContain('date_to=2024-01-31');
      expect(url).toContain('page=1');
      expect(url).toContain('limit=20');
    });
  });
});