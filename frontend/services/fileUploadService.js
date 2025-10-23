/**
 * File Upload Service - Handles batch file uploads and analysis
 */

import httpClient from './httpClient.js';

class FileUploadService {
  constructor() {
    this.baseURL = '/files';
  }

  /**
   * Upload multiple files as a batch for analysis
   * @param {FileList|Array} files - Files to upload
   * @param {Object} options - Upload options
   * @param {string} options.language - Programming language (optional, auto-detected)
   * @param {Function} options.onProgress - Progress callback (fileIndex, progress)
   * @param {Function} options.onFileComplete - Callback when individual file completes
   * @returns {Promise<Object>} Batch upload result
   */
  async uploadFilesBatch(files, options = {}) {
    try {
      const formData = new FormData();
      
      // Add all files to form data
      Array.from(files).forEach((file) => {
        formData.append('files', file);
      });
      
      // Add language if specified
      if (options.language) {
        formData.append('language', options.language);
      }

      const response = await httpClient.post(`${this.baseURL}/upload-batch`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (options.onProgress) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            options.onProgress(percentCompleted);
          }
        },
      });

      return response.data;
    } catch (error) {
      console.error('Failed to upload files batch:', error);
      throw this.handleUploadError(error);
    }
  }

  /**
   * Get batch upload status
   * @param {string} batchId - Batch ID
   * @returns {Promise<Object>} Batch status information
   */
  async getBatchStatus(batchId) {
    try {
      const response = await httpClient.get(`${this.baseURL}/batch/${batchId}/status`);
      return response.data;
    } catch (error) {
      console.error('Failed to get batch status:', error);
      throw this.handleUploadError(error);
    }
  }

  /**
   * Get list of files in a batch
   * @param {string} batchId - Batch ID
   * @returns {Promise<Object>} List of files in the batch
   */
  async getBatchFiles(batchId) {
    try {
      const response = await httpClient.get(`${this.baseURL}/batch/${batchId}/files`);
      return response.data;
    } catch (error) {
      console.error('Failed to get batch files:', error);
      throw this.handleUploadError(error);
    }
  }

  /**
   * Get individual file status from a batch
   * @param {string} batchId - Batch ID
   * @param {string} fileId - File ID
   * @returns {Promise<Object>} File status information
   */
  async getFileStatus(batchId, fileId) {
    try {
      const response = await httpClient.get(`${this.baseURL}/batch/${batchId}/files/${fileId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get file status:', error);
      throw this.handleUploadError(error);
    }
  }

  /**
   * Cancel a batch upload
   * @param {string} batchId - Batch ID to cancel
   * @returns {Promise<Object>} Cancellation result
   */
  async cancelBatch(batchId) {
    try {
      const response = await httpClient.post(`${this.baseURL}/batch/${batchId}/cancel`);
      return response.data;
    } catch (error) {
      console.error('Failed to cancel batch:', error);
      throw this.handleUploadError(error);
    }
  }

  /**
   * Retry failed files in a batch
   * @param {string} batchId - Batch ID
   * @param {Array<string>} fileIds - Optional array of specific file IDs to retry
   * @returns {Promise<Object>} Retry result
   */
  async retryFailedFiles(batchId, fileIds = null) {
    try {
      const response = await httpClient.post(`${this.baseURL}/batch/${batchId}/retry`, {
        file_ids: fileIds
      });
      return response.data;
    } catch (error) {
      console.error('Failed to retry files:', error);
      throw this.handleUploadError(error);
    }
  }

  /**
   * Validate files before upload
   * @param {FileList|Array} files - Files to validate
   * @param {Object} options - Validation options
   * @param {number} options.maxFileSize - Maximum file size in bytes (default: 5MB)
   * @param {Array<string>} options.allowedExtensions - Allowed file extensions
   * @returns {Object} Validation result with valid and invalid files
   */
  validateFiles(files, options = {}) {
    const {
      maxFileSize = 5 * 1024 * 1024, // 5MB default
      allowedExtensions = [
        'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'cpp', 'c', 'cs',
        'go', 'rs', 'php', 'rb', 'swift', 'kt', 'scala', 'html', 'css'
      ]
    } = options;

    const validFiles = [];
    const invalidFiles = [];

    Array.from(files).forEach((file) => {
      const errors = [];

      // Check file size
      if (file.size > maxFileSize) {
        errors.push(`File size (${(file.size / 1024 / 1024).toFixed(2)}MB) exceeds maximum (${(maxFileSize / 1024 / 1024).toFixed(2)}MB)`);
      }

      // Check file extension
      const extension = file.name.split('.').pop().toLowerCase();
      if (!allowedExtensions.includes(extension)) {
        errors.push(`File type .${extension} is not supported`);
      }

      // Check if file is empty
      if (file.size === 0) {
        errors.push('File is empty');
      }

      if (errors.length > 0) {
        invalidFiles.push({ file, errors });
      } else {
        validFiles.push(file);
      }
    });

    return {
      valid: validFiles,
      invalid: invalidFiles,
      isValid: invalidFiles.length === 0,
      totalFiles: files.length,
      validCount: validFiles.length,
      invalidCount: invalidFiles.length
    };
  }

  /**
   * Get supported file extensions
   * @returns {Array<string>} List of supported extensions
   */
  getSupportedExtensions() {
    return [
      'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'cpp', 'c', 'cs',
      'go', 'rs', 'php', 'rb', 'swift', 'kt', 'scala', 'html', 'css'
    ];
  }

  /**
   * Detect programming language from file extension
   * @param {string} filename - File name
   * @returns {string} Detected language
   */
  detectLanguage(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    
    const languageMap = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'jsx': 'javascript',
      'tsx': 'typescript',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'cs': 'csharp',
      'go': 'go',
      'rs': 'rust',
      'php': 'php',
      'rb': 'ruby',
      'swift': 'swift',
      'kt': 'kotlin',
      'scala': 'scala',
      'html': 'html',
      'css': 'css'
    };

    return languageMap[extension] || 'unknown';
  }

  /**
   * Handle upload-related errors
   * @param {Error} error - The error to handle
   * @returns {Error} Processed error with user-friendly message
   */
  handleUploadError(error) {
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          return new Error(data.detail || 'Invalid file upload request. Please check your files.');
        case 401:
          return new Error('Authentication required. Please log in.');
        case 403:
          return new Error('Access forbidden. You may not have permission to upload files.');
        case 413:
          return new Error('File size too large. Please upload smaller files.');
        case 415:
          return new Error('Unsupported file type. Please upload code files only.');
        case 422:
          return new Error(data.detail || 'File validation failed. Please check your files.');
        case 429:
          return new Error('Too many upload requests. Please try again later.');
        case 500:
          return new Error('Server error during file upload. Please try again later.');
        default:
          return new Error(data.detail || 'File upload failed. Please try again.');
      }
    } else if (error.request) {
      return new Error('Network error. Please check your connection and try again.');
    } else {
      return new Error(error.message || 'An unexpected error occurred during file upload.');
    }
  }

  /**
   * Calculate estimated upload time
   * @param {FileList|Array} files - Files to upload
   * @param {number} uploadSpeed - Upload speed in bytes per second (default: 1MB/s)
   * @returns {Object} Estimated time information
   */
  estimateUploadTime(files, uploadSpeed = 1024 * 1024) {
    const totalSize = Array.from(files).reduce((sum, file) => sum + file.size, 0);
    const estimatedSeconds = totalSize / uploadSpeed;
    
    return {
      totalSize,
      totalSizeMB: (totalSize / 1024 / 1024).toFixed(2),
      estimatedSeconds: Math.ceil(estimatedSeconds),
      estimatedMinutes: Math.ceil(estimatedSeconds / 60),
      formattedTime: this.formatTime(estimatedSeconds)
    };
  }

  /**
   * Format time in seconds to human-readable format
   * @param {number} seconds - Time in seconds
   * @returns {string} Formatted time string
   */
  formatTime(seconds) {
    if (seconds < 60) {
      return `${Math.ceil(seconds)} seconds`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.ceil(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  }
}

// Create and export singleton instance
const fileUploadService = new FileUploadService();
export default fileUploadService;
