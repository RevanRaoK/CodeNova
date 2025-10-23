import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import fileUploadService from '../fileUploadService';
import httpClient from '../httpClient';

// Mock httpClient
vi.mock('../httpClient', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}));

describe('FileUploadService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('uploadFilesBatch', () => {
    it('should upload files successfully', async () => {
      const mockResponse = {
        data: {
          batch_id: 'batch-123',
          total_files: 2,
          files: [
            { file_id: 'file-1', filename: 'test1.js', status: 'queued' },
            { file_id: 'file-2', filename: 'test2.js', status: 'queued' }
          ]
        }
      };

      httpClient.post.mockResolvedValue(mockResponse);

      const files = [
        new File(['test1'], 'test1.js', { type: 'text/javascript' }),
        new File(['test2'], 'test2.js', { type: 'text/javascript' })
      ];

      const result = await fileUploadService.uploadFilesBatch(files);

      expect(httpClient.post).toHaveBeenCalledWith(
        '/files/upload-batch',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      );

      expect(result).toEqual(mockResponse.data);
    });

    it('should include language in request', async () => {
      httpClient.post.mockResolvedValue({ data: {} });

      const files = [new File(['test'], 'test.js', { type: 'text/javascript' })];

      await fileUploadService.uploadFilesBatch(files, { language: 'javascript' });

      const formData = httpClient.post.mock.calls[0][1];
      expect(formData.get('language')).toBe('javascript');
    });

    it('should call progress callback', async () => {
      const onProgress = vi.fn();
      
      httpClient.post.mockImplementation((url, data, config) => {
        // Simulate progress
        config.onUploadProgress({ loaded: 50, total: 100 });
        return Promise.resolve({ data: {} });
      });

      const files = [new File(['test'], 'test.js', { type: 'text/javascript' })];

      await fileUploadService.uploadFilesBatch(files, { onProgress });

      expect(onProgress).toHaveBeenCalledWith(50);
    });

    it('should handle upload errors', async () => {
      httpClient.post.mockRejectedValue({
        response: {
          status: 400,
          data: { detail: 'Invalid file' }
        }
      });

      const files = [new File(['test'], 'test.js', { type: 'text/javascript' })];

      await expect(fileUploadService.uploadFilesBatch(files)).rejects.toThrow();
    });
  });

  describe('getBatchStatus', () => {
    it('should get batch status successfully', async () => {
      const mockResponse = {
        data: {
          batch_id: 'batch-123',
          status: 'processing',
          completed_files: 1,
          total_files: 2
        }
      };

      httpClient.get.mockResolvedValue(mockResponse);

      const result = await fileUploadService.getBatchStatus('batch-123');

      expect(httpClient.get).toHaveBeenCalledWith('/files/batch/batch-123/status');
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle errors', async () => {
      httpClient.get.mockRejectedValue(new Error('Not found'));

      await expect(fileUploadService.getBatchStatus('invalid')).rejects.toThrow();
    });
  });

  describe('validateFiles', () => {
    it('should validate files successfully', () => {
      const files = [
        new File(['test'], 'test.js', { type: 'text/javascript' }),
        new File(['test'], 'test.py', { type: 'text/x-python' })
      ];

      const result = fileUploadService.validateFiles(files);

      expect(result.isValid).toBe(true);
      expect(result.validCount).toBe(2);
      expect(result.invalidCount).toBe(0);
    });

    it('should reject files exceeding size limit', () => {
      const largeFile = new File(['x'.repeat(6 * 1024 * 1024)], 'large.js', { 
        type: 'text/javascript' 
      });

      const result = fileUploadService.validateFiles([largeFile]);

      expect(result.isValid).toBe(false);
      expect(result.invalidCount).toBe(1);
      expect(result.invalid[0].errors[0]).toContain('exceeds maximum');
    });

    it('should reject unsupported file types', () => {
      const invalidFile = new File(['test'], 'test.exe', { type: 'application/x-msdownload' });

      const result = fileUploadService.validateFiles([invalidFile]);

      expect(result.isValid).toBe(false);
      expect(result.invalidCount).toBe(1);
      expect(result.invalid[0].errors[0]).toContain('not supported');
    });

    it('should reject empty files', () => {
      const emptyFile = new File([], 'empty.js', { type: 'text/javascript' });

      const result = fileUploadService.validateFiles([emptyFile]);

      expect(result.isValid).toBe(false);
      expect(result.invalid[0].errors[0]).toContain('empty');
    });

    it('should use custom max file size', () => {
      const file = new File(['x'.repeat(2 * 1024 * 1024)], 'test.js', { 
        type: 'text/javascript' 
      });

      const result = fileUploadService.validateFiles([file], {
        maxFileSize: 1 * 1024 * 1024 // 1MB
      });

      expect(result.isValid).toBe(false);
    });

    it('should use custom allowed extensions', () => {
      const file = new File(['test'], 'test.py', { type: 'text/x-python' });

      const result = fileUploadService.validateFiles([file], {
        allowedExtensions: ['js', 'ts']
      });

      expect(result.isValid).toBe(false);
    });

    it('should separate valid and invalid files', () => {
      const files = [
        new File(['test'], 'test.js', { type: 'text/javascript' }),
        new File(['x'.repeat(6 * 1024 * 1024)], 'large.js', { type: 'text/javascript' }),
        new File(['test'], 'test.py', { type: 'text/x-python' })
      ];

      const result = fileUploadService.validateFiles(files);

      expect(result.validCount).toBe(2);
      expect(result.invalidCount).toBe(1);
    });
  });

  describe('detectLanguage', () => {
    it('should detect JavaScript', () => {
      expect(fileUploadService.detectLanguage('test.js')).toBe('javascript');
      expect(fileUploadService.detectLanguage('test.jsx')).toBe('javascript');
    });

    it('should detect TypeScript', () => {
      expect(fileUploadService.detectLanguage('test.ts')).toBe('typescript');
      expect(fileUploadService.detectLanguage('test.tsx')).toBe('typescript');
    });

    it('should detect Python', () => {
      expect(fileUploadService.detectLanguage('test.py')).toBe('python');
    });

    it('should detect Java', () => {
      expect(fileUploadService.detectLanguage('Test.java')).toBe('java');
    });

    it('should detect C/C++', () => {
      expect(fileUploadService.detectLanguage('test.c')).toBe('c');
      expect(fileUploadService.detectLanguage('test.cpp')).toBe('cpp');
    });

    it('should return unknown for unsupported extensions', () => {
      expect(fileUploadService.detectLanguage('test.xyz')).toBe('unknown');
    });

    it('should be case insensitive', () => {
      expect(fileUploadService.detectLanguage('test.JS')).toBe('javascript');
      expect(fileUploadService.detectLanguage('test.PY')).toBe('python');
    });
  });

  describe('getSupportedExtensions', () => {
    it('should return array of supported extensions', () => {
      const extensions = fileUploadService.getSupportedExtensions();

      expect(Array.isArray(extensions)).toBe(true);
      expect(extensions).toContain('js');
      expect(extensions).toContain('py');
      expect(extensions).toContain('java');
    });
  });

  describe('estimateUploadTime', () => {
    it('should estimate upload time', () => {
      const files = [
        new File(['x'.repeat(1024 * 1024)], 'test1.js', { type: 'text/javascript' }),
        new File(['x'.repeat(1024 * 1024)], 'test2.js', { type: 'text/javascript' })
      ];

      const estimate = fileUploadService.estimateUploadTime(files);

      expect(estimate.totalSize).toBe(2 * 1024 * 1024);
      expect(estimate.totalSizeMB).toBe('2.00');
      expect(estimate.estimatedSeconds).toBeGreaterThan(0);
      expect(estimate.formattedTime).toBeTruthy();
    });

    it('should format time correctly for seconds', () => {
      const files = [new File(['x'.repeat(1024)], 'test.js', { type: 'text/javascript' })];

      const estimate = fileUploadService.estimateUploadTime(files, 1024); // 1KB/s

      expect(estimate.formattedTime).toContain('second');
    });

    it('should format time correctly for minutes', () => {
      const files = [new File(['x'.repeat(100 * 1024)], 'test.js', { type: 'text/javascript' })];

      const estimate = fileUploadService.estimateUploadTime(files, 1024); // 1KB/s

      expect(estimate.formattedTime).toContain('m');
    });
  });

  describe('handleUploadError', () => {
    it('should handle 400 errors', () => {
      const error = {
        response: {
          status: 400,
          data: { detail: 'Bad request' }
        }
      };

      const result = fileUploadService.handleUploadError(error);

      expect(result.message).toContain('Bad request');
    });

    it('should handle 401 errors', () => {
      const error = {
        response: {
          status: 401,
          data: {}
        }
      };

      const result = fileUploadService.handleUploadError(error);

      expect(result.message).toContain('Authentication required');
    });

    it('should handle 413 errors', () => {
      const error = {
        response: {
          status: 413,
          data: {}
        }
      };

      const result = fileUploadService.handleUploadError(error);

      expect(result.message).toContain('File size too large');
    });

    it('should handle network errors', () => {
      const error = {
        request: {},
        message: 'Network error'
      };

      const result = fileUploadService.handleUploadError(error);

      expect(result.message).toContain('Network error');
    });

    it('should handle unknown errors', () => {
      const error = new Error('Unknown error');

      const result = fileUploadService.handleUploadError(error);

      expect(result.message).toBeTruthy();
    });
  });

  describe('retryFailedFiles', () => {
    it('should retry failed files', async () => {
      const mockResponse = {
        data: {
          batch_id: 'batch-123',
          retried_files: 2
        }
      };

      httpClient.post.mockResolvedValue(mockResponse);

      const result = await fileUploadService.retryFailedFiles('batch-123');

      expect(httpClient.post).toHaveBeenCalledWith(
        '/files/batch/batch-123/retry',
        { file_ids: null }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('should retry specific files', async () => {
      httpClient.post.mockResolvedValue({ data: {} });

      await fileUploadService.retryFailedFiles('batch-123', ['file-1', 'file-2']);

      expect(httpClient.post).toHaveBeenCalledWith(
        '/files/batch/batch-123/retry',
        { file_ids: ['file-1', 'file-2'] }
      );
    });
  });

  describe('cancelBatch', () => {
    it('should cancel batch upload', async () => {
      const mockResponse = {
        data: {
          batch_id: 'batch-123',
          status: 'cancelled'
        }
      };

      httpClient.post.mockResolvedValue(mockResponse);

      const result = await fileUploadService.cancelBatch('batch-123');

      expect(httpClient.post).toHaveBeenCalledWith('/files/batch/batch-123/cancel');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getBatchFiles', () => {
    it('should get batch files', async () => {
      const mockResponse = {
        data: {
          files: [
            { file_id: 'file-1', filename: 'test1.js' },
            { file_id: 'file-2', filename: 'test2.js' }
          ]
        }
      };

      httpClient.get.mockResolvedValue(mockResponse);

      const result = await fileUploadService.getBatchFiles('batch-123');

      expect(httpClient.get).toHaveBeenCalledWith('/files/batch/batch-123/files');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getFileStatus', () => {
    it('should get file status', async () => {
      const mockResponse = {
        data: {
          file_id: 'file-1',
          status: 'completed'
        }
      };

      httpClient.get.mockResolvedValue(mockResponse);

      const result = await fileUploadService.getFileStatus('batch-123', 'file-1');

      expect(httpClient.get).toHaveBeenCalledWith('/files/batch/batch-123/files/file-1');
      expect(result).toEqual(mockResponse.data);
    });
  });
});
