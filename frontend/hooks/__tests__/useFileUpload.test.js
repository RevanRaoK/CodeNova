import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useFileUpload } from '../useFileUpload';
import fileUploadService from '../../services/fileUploadService';

// Mock dependencies
vi.mock('../../services/fileUploadService');
vi.mock('../../contexts/NotificationContext', () => ({
  useNotification: () => ({
    showSuccess: vi.fn(),
    showError: vi.fn(),
    showWarning: vi.fn()
  })
}));
vi.mock('../../utils/environment', () => ({
  logger: {
    debug: vi.fn(),
    error: vi.fn()
  }
}));

describe('useFileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock implementations
    fileUploadService.validateFiles.mockReturnValue({
      valid: [],
      invalid: [],
      isValid: true,
      totalFiles: 0,
      validCount: 0,
      invalidCount: 0
    });
    
    fileUploadService.uploadFilesBatch.mockResolvedValue({
      batch_id: 'batch-123',
      total_files: 1
    });
    
    fileUploadService.detectLanguage.mockReturnValue('javascript');
    fileUploadService.getSupportedExtensions.mockReturnValue(['js', 'py', 'java']);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with empty state', () => {
    const { result } = renderHook(() => useFileUpload());

    expect(result.current.selectedFiles).toEqual([]);
    expect(result.current.uploadProgress).toBe(0);
    expect(result.current.isUploading).toBe(false);
    expect(result.current.uploadError).toBeNull();
    expect(result.current.batchId).toBeNull();
    expect(result.current.hasFiles).toBe(false);
  });

  it('should select files', () => {
    const { result } = renderHook(() => useFileUpload());

    const files = [
      new File(['test'], 'test.js', { type: 'text/javascript' })
    ];

    fileUploadService.validateFiles.mockReturnValue({
      valid: files,
      invalid: [],
      isValid: true,
      totalFiles: 1,
      validCount: 1,
      invalidCount: 0
    });

    act(() => {
      result.current.selectFiles(files);
    });

    expect(result.current.selectedFiles).toEqual(files);
    expect(result.current.hasFiles).toBe(true);
  });

  it('should validate files on selection', () => {
    const { result } = renderHook(() => useFileUpload());

    const files = [
      new File(['test'], 'test.js', { type: 'text/javascript' })
    ];

    act(() => {
      result.current.selectFiles(files);
    });

    expect(fileUploadService.validateFiles).toHaveBeenCalledWith(
      files,
      expect.objectContaining({
        maxFileSize: 5 * 1024 * 1024
      })
    );
  });

  it('should handle validation errors', () => {
    const { result } = renderHook(() => useFileUpload());

    const validFile = new File(['test'], 'test.js', { type: 'text/javascript' });
    const invalidFile = new File(['x'.repeat(10 * 1024 * 1024)], 'large.js', { 
      type: 'text/javascript' 
    });

    fileUploadService.validateFiles.mockReturnValue({
      valid: [validFile],
      invalid: [{ file: invalidFile, errors: ['File too large'] }],
      isValid: false,
      totalFiles: 2,
      validCount: 1,
      invalidCount: 1
    });

    act(() => {
      result.current.selectFiles([validFile, invalidFile]);
    });

    expect(result.current.selectedFiles).toEqual([validFile]);
    expect(result.current.validationErrors).toHaveLength(1);
    expect(result.current.hasValidationErrors).toBe(true);
  });

  it('should add files to existing selection', () => {
    const { result } = renderHook(() => useFileUpload());

    const file1 = new File(['test1'], 'test1.js', { type: 'text/javascript' });
    const file2 = new File(['test2'], 'test2.js', { type: 'text/javascript' });

    fileUploadService.validateFiles.mockReturnValue({
      valid: [file1],
      invalid: [],
      isValid: true,
      totalFiles: 1,
      validCount: 1,
      invalidCount: 0
    });

    act(() => {
      result.current.selectFiles([file1]);
    });

    fileUploadService.validateFiles.mockReturnValue({
      valid: [file1, file2],
      invalid: [],
      isValid: true,
      totalFiles: 2,
      validCount: 2,
      invalidCount: 0
    });

    act(() => {
      result.current.addFiles([file2]);
    });

    expect(result.current.selectedFiles).toHaveLength(2);
  });

  it('should remove file from selection', () => {
    const { result } = renderHook(() => useFileUpload());

    const files = [
      new File(['test1'], 'test1.js', { type: 'text/javascript' }),
      new File(['test2'], 'test2.js', { type: 'text/javascript' })
    ];

    fileUploadService.validateFiles.mockReturnValue({
      valid: files,
      invalid: [],
      isValid: true,
      totalFiles: 2,
      validCount: 2,
      invalidCount: 0
    });

    act(() => {
      result.current.selectFiles(files);
    });

    act(() => {
      result.current.removeFile(0);
    });

    expect(result.current.selectedFiles).toHaveLength(1);
    expect(result.current.selectedFiles[0]).toBe(files[1]);
  });

  it('should clear all files', () => {
    const { result } = renderHook(() => useFileUpload());

    const files = [
      new File(['test'], 'test.js', { type: 'text/javascript' })
    ];

    fileUploadService.validateFiles.mockReturnValue({
      valid: files,
      invalid: [],
      isValid: true,
      totalFiles: 1,
      validCount: 1,
      invalidCount: 0
    });

    act(() => {
      result.current.selectFiles(files);
    });

    act(() => {
      result.current.clearFiles();
    });

    expect(result.current.selectedFiles).toEqual([]);
    expect(result.current.validationErrors).toEqual([]);
    expect(result.current.uploadProgress).toBe(0);
  });

  it('should upload files successfully', async () => {
    const { result } = renderHook(() => useFileUpload());

    const files = [
      new File(['test'], 'test.js', { type: 'text/javascript' })
    ];

    fileUploadService.validateFiles.mockReturnValue({
      valid: files,
      invalid: [],
      isValid: true,
      totalFiles: 1,
      validCount: 1,
      invalidCount: 0
    });

    act(() => {
      result.current.selectFiles(files);
    });

    const mockResult = {
      batch_id: 'batch-123',
      total_files: 1
    };

    fileUploadService.uploadFilesBatch.mockResolvedValue(mockResult);

    let uploadResult;
    await act(async () => {
      uploadResult = await result.current.uploadFiles();
    });

    expect(fileUploadService.uploadFilesBatch).toHaveBeenCalledWith(
      files,
      expect.objectContaining({
        onProgress: expect.any(Function)
      })
    );

    expect(result.current.batchId).toBe('batch-123');
    expect(result.current.uploadResult).toEqual(mockResult);
    expect(uploadResult).toEqual(mockResult);
  });

  it('should track upload progress', async () => {
    const { result } = renderHook(() => useFileUpload());

    const files = [
      new File(['test'], 'test.js', { type: 'text/javascript' })
    ];

    fileUploadService.validateFiles.mockReturnValue({
      valid: files,
      invalid: [],
      isValid: true,
      totalFiles: 1,
      validCount: 1,
      invalidCount: 0
    });

    act(() => {
      result.current.selectFiles(files);
    });

    fileUploadService.uploadFilesBatch.mockImplementation((files, options) => {
      options.onProgress(50);
      return Promise.resolve({ batch_id: 'batch-123' });
    });

    await act(async () => {
      await result.current.uploadFiles();
    });

    expect(result.current.uploadProgress).toBe(100);
  });

  it('should handle upload errors', async () => {
    const { result } = renderHook(() => useFileUpload());

    const files = [
      new File(['test'], 'test.js', { type: 'text/javascript' })
    ];

    fileUploadService.validateFiles.mockReturnValue({
      valid: files,
      invalid: [],
      isValid: true,
      totalFiles: 1,
      validCount: 1,
      invalidCount: 0
    });

    act(() => {
      result.current.selectFiles(files);
    });

    const error = new Error('Upload failed');
    fileUploadService.uploadFilesBatch.mockRejectedValue(error);

    await act(async () => {
      await result.current.uploadFiles();
    });

    expect(result.current.uploadError).toBe('Upload failed');
    expect(result.current.isUploading).toBe(false);
  });

  it('should prevent upload without files', async () => {
    const { result } = renderHook(() => useFileUpload());

    const uploadResult = await act(async () => {
      return await result.current.uploadFiles();
    });

    expect(uploadResult).toBeNull();
    expect(fileUploadService.uploadFilesBatch).not.toHaveBeenCalled();
  });

  it('should call onUploadComplete callback', async () => {
    const onUploadComplete = vi.fn();
    const { result } = renderHook(() => useFileUpload({ onUploadComplete }));

    const files = [
      new File(['test'], 'test.js', { type: 'text/javascript' })
    ];

    fileUploadService.validateFiles.mockReturnValue({
      valid: files,
      invalid: [],
      isValid: true,
      totalFiles: 1,
      validCount: 1,
      invalidCount: 0
    });

    act(() => {
      result.current.selectFiles(files);
    });

    const mockResult = { batch_id: 'batch-123' };
    fileUploadService.uploadFilesBatch.mockResolvedValue(mockResult);

    await act(async () => {
      await result.current.uploadFiles();
    });

    expect(onUploadComplete).toHaveBeenCalledWith(mockResult);
  });

  it('should call onUploadError callback', async () => {
    const onUploadError = vi.fn();
    const { result } = renderHook(() => useFileUpload({ onUploadError }));

    const files = [
      new File(['test'], 'test.js', { type: 'text/javascript' })
    ];

    fileUploadService.validateFiles.mockReturnValue({
      valid: files,
      invalid: [],
      isValid: true,
      totalFiles: 1,
      validCount: 1,
      invalidCount: 0
    });

    act(() => {
      result.current.selectFiles(files);
    });

    const error = new Error('Upload failed');
    fileUploadService.uploadFilesBatch.mockRejectedValue(error);

    await act(async () => {
      await result.current.uploadFiles();
    });

    expect(onUploadError).toHaveBeenCalledWith(error);
  });

  it('should retry upload', async () => {
    const { result } = renderHook(() => useFileUpload());

    const files = [
      new File(['test'], 'test.js', { type: 'text/javascript' })
    ];

    fileUploadService.validateFiles.mockReturnValue({
      valid: files,
      invalid: [],
      isValid: true,
      totalFiles: 1,
      validCount: 1,
      invalidCount: 0
    });

    act(() => {
      result.current.selectFiles(files);
    });

    fileUploadService.uploadFilesBatch.mockResolvedValue({ batch_id: 'batch-123' });

    await act(async () => {
      await result.current.retryUpload();
    });

    expect(fileUploadService.uploadFilesBatch).toHaveBeenCalled();
  });

  it('should get upload stats', () => {
    const { result } = renderHook(() => useFileUpload());

    const files = [
      new File(['x'.repeat(1024 * 1024)], 'test.js', { type: 'text/javascript' })
    ];

    fileUploadService.validateFiles.mockReturnValue({
      valid: files,
      invalid: [],
      isValid: true,
      totalFiles: 1,
      validCount: 1,
      invalidCount: 0
    });

    fileUploadService.estimateUploadTime.mockReturnValue({
      formattedTime: '1 second'
    });

    act(() => {
      result.current.selectFiles(files);
    });

    const stats = result.current.getUploadStats();

    expect(stats).toBeTruthy();
    expect(stats.fileCount).toBe(1);
    expect(stats.files).toHaveLength(1);
  });

  it('should validate single file', () => {
    const { result } = renderHook(() => useFileUpload());

    const file = new File(['test'], 'test.js', { type: 'text/javascript' });

    fileUploadService.validateFiles.mockReturnValue({
      valid: [file],
      invalid: [],
      isValid: true
    });

    const validation = result.current.validateFile(file);

    expect(validation.isValid).toBe(true);
    expect(validation.errors).toEqual([]);
  });

  it('should use custom max file size', () => {
    const customMaxSize = 1 * 1024 * 1024; // 1MB
    const { result } = renderHook(() => useFileUpload({ maxFileSize: customMaxSize }));

    const files = [
      new File(['test'], 'test.js', { type: 'text/javascript' })
    ];

    act(() => {
      result.current.selectFiles(files);
    });

    expect(fileUploadService.validateFiles).toHaveBeenCalledWith(
      files,
      expect.objectContaining({
        maxFileSize: customMaxSize
      })
    );
  });

  it('should use custom allowed extensions', () => {
    const customExtensions = ['js', 'ts'];
    const { result } = renderHook(() => useFileUpload({ allowedExtensions: customExtensions }));

    const files = [
      new File(['test'], 'test.js', { type: 'text/javascript' })
    ];

    act(() => {
      result.current.selectFiles(files);
    });

    expect(fileUploadService.validateFiles).toHaveBeenCalledWith(
      files,
      expect.objectContaining({
        allowedExtensions: customExtensions
      })
    );
  });

  it('should detect language', () => {
    const { result } = renderHook(() => useFileUpload());

    const language = result.current.detectLanguage('test.js');

    expect(fileUploadService.detectLanguage).toHaveBeenCalledWith('test.js');
    expect(language).toBe('javascript');
  });

  it('should get supported extensions', () => {
    const { result } = renderHook(() => useFileUpload());

    const extensions = result.current.getSupportedExtensions();

    expect(fileUploadService.getSupportedExtensions).toHaveBeenCalled();
    expect(extensions).toEqual(['js', 'py', 'java']);
  });
});
