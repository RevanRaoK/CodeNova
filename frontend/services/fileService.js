/**
 * File Service - Handles file storage operations with Digital Ocean Spaces
 */

import httpClient from './httpClient.js';

class FileService {
  constructor() {
    this.baseURL = '/api/files';
  }

  /**
   * Upload a file to storage
   * @param {File} file - The file to upload
   * @param {Object} metadata - Additional metadata for the file
   * @returns {Promise<Object>} Upload result with file information
   */
  async uploadFile(file, metadata = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Add metadata
    Object.keys(metadata).forEach(key => {
      formData.append(key, metadata[key]);
    });

    const response = await httpClient.post(`${this.baseURL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (metadata.onProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          metadata.onProgress(percentCompleted);
        }
      },
    });

    return response.data;
  }

  /**
   * Upload multiple files
   * @param {FileList|Array} files - Files to upload
   * @param {Object} options - Upload options
   * @returns {Promise<Array>} Array of upload results
   */
  async uploadMultipleFiles(files, options = {}) {
    const uploadPromises = Array.from(files).map((file, index) => {
      const metadata = {
        ...options,
        onProgress: options.onProgress 
          ? (progress) => options.onProgress(index, progress)
          : undefined
      };
      return this.uploadFile(file, metadata);
    });

    return Promise.all(uploadPromises);
  }

  /**
   * Get list of user's files
   * @param {Object} filters - Filtering options
   * @returns {Promise<Object>} Files list with pagination
   */
  async getFiles(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.search) params.append('search', filters.search);
    if (filters.fileType) params.append('file_type', filters.fileType);
    if (filters.sortBy) params.append('sort_by', filters.sortBy);
    if (filters.sortOrder) params.append('sort_order', filters.sortOrder);

    const response = await httpClient.get(`${this.baseURL}?${params}`);
    return response.data;
  }

  /**
   * Get file metadata by ID
   * @param {string} fileId - File ID
   * @returns {Promise<Object>} File metadata
   */
  async getFileById(fileId) {
    const response = await httpClient.get(`${this.baseURL}/${fileId}`);
    return response.data;
  }

  /**
   * Get secure download URL for a file
   * @param {string} fileId - File ID
   * @returns {Promise<Object>} Download URL and metadata
   */
  async getDownloadUrl(fileId) {
    const response = await httpClient.get(`${this.baseURL}/${fileId}/download`);
    return response.data;
  }

  /**
   * Download file content
   * @param {string} fileId - File ID
   * @returns {Promise<Blob>} File content as blob
   */
  async downloadFile(fileId) {
    const response = await httpClient.get(`${this.baseURL}/${fileId}/content`, {
      responseType: 'blob'
    });
    return response.data;
  }

  /**
   * Delete a file
   * @param {string} fileId - File ID
   * @returns {Promise<Object>} Deletion result
   */
  async deleteFile(fileId) {
    const response = await httpClient.delete(`${this.baseURL}/${fileId}`);
    return response.data;
  }

  /**
   * Delete multiple files
   * @param {Array<string>} fileIds - Array of file IDs
   * @returns {Promise<Object>} Bulk deletion result
   */
  async deleteMultipleFiles(fileIds) {
    const response = await httpClient.delete(`${this.baseURL}/bulk`, {
      data: { file_ids: fileIds }
    });
    return response.data;
  }

  /**
   * Update file metadata
   * @param {string} fileId - File ID
   * @param {Object} metadata - Updated metadata
   * @returns {Promise<Object>} Updated file information
   */
  async updateFileMetadata(fileId, metadata) {
    const response = await httpClient.patch(`${this.baseURL}/${fileId}`, metadata);
    return response.data;
  }

  /**
   * Get file preview (for supported formats)
   * @param {string} fileId - File ID
   * @param {Object} options - Preview options
   * @returns {Promise<Object>} Preview data
   */
  async getFilePreview(fileId, options = {}) {
    const params = new URLSearchParams();
    if (options.maxLines) params.append('max_lines', options.maxLines);
    if (options.format) params.append('format', options.format);

    const response = await httpClient.get(`${this.baseURL}/${fileId}/preview?${params}`);
    return response.data;
  }

  /**
   * Get storage usage statistics
   * @returns {Promise<Object>} Storage usage data
   */
  async getStorageUsage() {
    const response = await httpClient.get(`${this.baseURL}/usage`);
    return response.data;
  }

  /**
   * Search files
   * @param {string} query - Search query
   * @param {Object} filters - Additional filters
   * @returns {Promise<Object>} Search results
   */
  async searchFiles(query, filters = {}) {
    const params = new URLSearchParams();
    params.append('q', query);
    
    if (filters.fileType) params.append('file_type', filters.fileType);
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    if (filters.page) params.append('page', filters.page);
    if (filters.limit) params.append('limit', filters.limit);

    const response = await httpClient.get(`${this.baseURL}/search?${params}`);
    return response.data;
  }
}

// Create and export singleton instance
const fileService = new FileService();
export default fileService;