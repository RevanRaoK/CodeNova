import { useState, useCallback, useRef } from 'react';
import fileUploadService from '../services/fileUploadService';
import { useNotification } from '../contexts/NotificationContext';
import { logger } from '../utils/environment';

/**
 * Custom hook for handling file uploads with progress tracking
 * @param {Object} options - Configuration options
 * @param {Function} options.onUploadComplete - Callback when upload completes
 * @param {Function} options.onUploadError - Callback when upload fails
 * @param {Function} options.onValidationError - Callback when validation fails
 * @param {number} options.maxFileSize - Maximum file size in bytes
 * @param {Array<string>} options.allowedExtensions - Allowed file extensions
 * @returns {Object} Upload state and controls
 */
export const useFileUpload = (options = {}) => {
  const {
    onUploadComplete,
    onUploadError,
    onValidationError,
    maxFileSize = 5 * 1024 * 1024, // 5MB default
    allowedExtensions
  } = options;

  const { showSuccess, showError, showWarning } = useNotification();

  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [batchId, setBatchId] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);

  const abortControllerRef = useRef(null);

  /**
   * Select files for upload
   * @param {FileList|Array} files - Files to select
   */
  const selectFiles = useCallback((files) => {
    if (!files || files.length === 0) {
      setSelectedFiles([]);
      setValidationErrors([]);
      return;
    }

    // Validate files
    const validation = fileUploadService.validateFiles(files, {
      maxFileSize,
      allowedExtensions
    });

    setSelectedFiles(validation.valid);
    setValidationErrors(validation.invalid);

    // Show validation warnings
    if (validation.invalid.length > 0) {
      const errorMessages = validation.invalid.map(({ file, errors }) => 
        `${file.name}: ${errors.join(', ')}`
      );
      
      showWarning(`${validation.invalid.length} file(s) failed validation:\n${errorMessages.join('\n')}`);
      
      if (onValidationError) {
        onValidationError(validation.invalid);
      }
    }

    // Show success message for valid files
    if (validation.valid.length > 0) {
      logger.debug(`Selected ${validation.valid.length} valid file(s) for upload`);
    }
  }, [maxFileSize, allowedExtensions, showWarning, onValidationError]);

  /**
   * Add files to existing selection
   * @param {FileList|Array} files - Files to add
   */
  const addFiles = useCallback((files) => {
    const newFiles = Array.from(files);
    const combined = [...selectedFiles, ...newFiles];
    selectFiles(combined);
  }, [selectedFiles, selectFiles]);

  /**
   * Remove a file from selection
   * @param {number} index - Index of file to remove
   */
  const removeFile = useCallback((index) => {
    const updated = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(updated);
  }, [selectedFiles]);

  /**
   * Clear all selected files
   */
  const clearFiles = useCallback(() => {
    setSelectedFiles([]);
    setValidationErrors([]);
    setUploadProgress(0);
    setUploadError(null);
    setBatchId(null);
    setUploadResult(null);
  }, []);

  /**
   * Upload selected files
   * @param {Object} uploadOptions - Upload options
   * @param {string} uploadOptions.language - Programming language
   * @returns {Promise<Object>} Upload result
   */
  const uploadFiles = useCallback(async (uploadOptions = {}) => {
    if (selectedFiles.length === 0) {
      showError('No files selected for upload');
      return null;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setUploadError(null);
    setUploadResult(null);

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController();

    try {
      logger.debug(`Starting upload of ${selectedFiles.length} file(s)`);

      const result = await fileUploadService.uploadFilesBatch(selectedFiles, {
        ...uploadOptions,
        onProgress: (progress) => {
          setUploadProgress(progress);
          logger.debug(`Upload progress: ${progress}%`);
        }
      });

      logger.debug('Upload completed:', result);

      setBatchId(result.batch_id);
      setUploadResult(result);
      setUploadProgress(100);

      showSuccess(`Successfully uploaded ${result.total_files} file(s)`);

      if (onUploadComplete) {
        onUploadComplete(result);
      }

      return result;
    } catch (error) {
      logger.error('Upload failed:', error);
      
      setUploadError(error.message || 'Upload failed');
      showError(error.message || 'Failed to upload files');

      if (onUploadError) {
        onUploadError(error);
      }

      return null;
    } finally {
      setIsUploading(false);
      abortControllerRef.current = null;
    }
  }, [selectedFiles, showSuccess, showError, onUploadComplete, onUploadError]);

  /**
   * Cancel ongoing upload
   */
  const cancelUpload = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      
      setIsUploading(false);
      setUploadProgress(0);
      
      showWarning('Upload cancelled');
      logger.debug('Upload cancelled by user');
    }
  }, [showWarning]);

  /**
   * Retry upload with same files
   */
  const retryUpload = useCallback(async (uploadOptions = {}) => {
    return await uploadFiles(uploadOptions);
  }, [uploadFiles]);

  /**
   * Get upload statistics
   */
  const getUploadStats = useCallback(() => {
    if (selectedFiles.length === 0) {
      return null;
    }

    const totalSize = selectedFiles.reduce((sum, file) => sum + file.size, 0);
    const estimate = fileUploadService.estimateUploadTime(selectedFiles);

    return {
      fileCount: selectedFiles.length,
      totalSize,
      totalSizeMB: (totalSize / 1024 / 1024).toFixed(2),
      estimatedTime: estimate.formattedTime,
      files: selectedFiles.map(file => ({
        name: file.name,
        size: file.size,
        sizeMB: (file.size / 1024 / 1024).toFixed(2),
        type: file.type,
        language: fileUploadService.detectLanguage(file.name)
      }))
    };
  }, [selectedFiles]);

  /**
   * Validate a single file
   * @param {File} file - File to validate
   * @returns {Object} Validation result
   */
  const validateFile = useCallback((file) => {
    const validation = fileUploadService.validateFiles([file], {
      maxFileSize,
      allowedExtensions
    });

    return {
      isValid: validation.isValid,
      errors: validation.invalid.length > 0 ? validation.invalid[0].errors : []
    };
  }, [maxFileSize, allowedExtensions]);

  return {
    // State
    selectedFiles,
    uploadProgress,
    isUploading,
    uploadError,
    batchId,
    uploadResult,
    validationErrors,
    hasFiles: selectedFiles.length > 0,
    hasValidationErrors: validationErrors.length > 0,

    // Actions
    selectFiles,
    addFiles,
    removeFile,
    clearFiles,
    uploadFiles,
    cancelUpload,
    retryUpload,
    validateFile,

    // Utilities
    getUploadStats,
    getSupportedExtensions: fileUploadService.getSupportedExtensions.bind(fileUploadService),
    detectLanguage: fileUploadService.detectLanguage.bind(fileUploadService)
  };
};

export default useFileUpload;
