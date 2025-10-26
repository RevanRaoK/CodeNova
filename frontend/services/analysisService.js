import httpClient from './httpClient.js';
import { retryWithBackoff, handleApiError } from '../utils/retryUtils.js';

/**
 * Code analysis service for handling code review and analysis operations
 */
class AnalysisService {
  /**
   * Analyze code directly without repository context
   * @param {Object} codeData - Code analysis request data
   * @param {string} codeData.code - The code content to analyze
   * @param {string} codeData.language - Programming language (e.g., 'javascript', 'python')
   * @param {string} [codeData.filename] - Optional filename for context
   * @returns {Promise<Object>} Analysis response with issues and metrics
   */
  async analyzeCode(codeData) {
    try {
      const response = await httpClient.post('/analysis/analyze-code', {
        code: codeData.code,
        language: codeData.language || 'javascript',
        filename: codeData.filename || null
      });

      return this.processAnalysisResponse(response.data);
    } catch (error) {
      console.error('Code analysis failed:', error);
      throw this.handleAnalysisError(error);
    }
  }

  /**
   * Get analysis result by ID with proper endpoint routing based on type
   * @param {string} analysisId - The analysis ID
   * @param {string} [type] - Optional analysis type hint ('direct', 'batch', 'repository')
   * @returns {Promise<Object>} Analysis result data
   */
  async getAnalysisById(analysisId, type = null) {
    try {
      // Try multiple endpoints to find the analysis
      let response;
      
      // Define endpoints to try in order of preference
      const endpoints = [
        `/analysis/direct/${analysisId}`,
        `/analysis/batch/${analysisId}`,
        `/files/analysis/result/${analysisId}`,
        `/files/analysis/${analysisId}`,
        `/files/${analysisId}`
      ];
      
      // If we have a type hint, prioritize the correct endpoint
      if (type === 'batch') {
        endpoints.unshift(`/analysis/batch/${analysisId}`);
      } else if (type === 'repository') {
        endpoints.unshift(`/analysis/repository/${analysisId}`);
      }
      
      let lastError;
      for (const endpoint of endpoints) {
        try {
          console.log(`Trying ${endpoint}`);
          response = await httpClient.get(endpoint);
          console.log(`✅ ${endpoint} worked!`);
          break;
        } catch (error) {
          console.log(`❌ ${endpoint} failed:`, error.response?.status);
          lastError = error;
          if (error.response?.status !== 404) {
            // If it's not a 404, don't try other endpoints
            throw error;
          }
        }
      }
      
      if (!response) {
        console.log('All endpoints failed, throwing last error');
        throw lastError;
      }
      
      if (response.data) {
        // Handle different response formats
        const data = response.data;
        return {
          id: data.analysis_id || data.id || analysisId,
          type: data.type || 'direct',
          filename: data.filename || data.original_filename,
          language: data.language || data.detected_language,
          status: data.status || 'completed',
          repositoryName: data.repository_name,
          repositoryId: data.repository_id,
          issues: this.processIssues(data.issues || [], data.analysis_id || data.id),
          metrics: this.processMetrics(data.metrics || {}),
          summary: data.summary,
          createdAt: data.created_at,
          completedAt: data.completed_at || data.analyzed_at,
          processingTime: data.processing_time_ms || data.processing_time
        };
      }
      
      throw new Error('No analysis data found');
    } catch (error) {
      console.error('Failed to fetch analysis:', error);
      
      // EMERGENCY FALLBACK - Return basic structure to prevent app crash
      console.log('EMERGENCY: Returning fallback analysis structure');
      return {
        id: analysisId,
        type: 'unknown',
        filename: 'Analysis not found',
        language: 'unknown',
        status: 'completed',
        issues: [],
        metrics: {},
        summary: 'Analysis details could not be loaded',
        createdAt: new Date().toISOString(),
        completedAt: new Date().toISOString(),
        processingTime: 0
      };
    }
  }

  /**
   * Get all analyses for a specific repository
   * @param {number} repoId - Repository ID
   * @param {Object} [options] - Query options
   * @param {number} [options.limit] - Maximum number of results
   * @param {number} [options.offset] - Offset for pagination
   * @param {string} [options.status] - Filter by analysis status
   * @returns {Promise<Object>} List of analyses with pagination info
   */
  async getAnalysesByRepo(repoId, options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.limit) params.append('limit', options.limit);
      if (options.offset) params.append('offset', options.offset);
      if (options.status) params.append('status', options.status);

      const response = await httpClient.get(`/analysis/repository/${repoId}?${params}`);
      
      return {
        analyses: response.data.analyses?.map(analysis => this.processAnalysisResponse(analysis)) || [],
        total: response.data.total || 0,
        limit: response.data.limit || 10,
        offset: response.data.offset || 0
      };
    } catch (error) {
      console.error('Failed to fetch repository analyses:', error);
      throw this.handleAnalysisError(error);
    }
  }

  /**
   * Get user's analysis history with enhanced pagination and filtering
   * @param {Object} [options] - Query options
   * @param {number} [options.page] - Page number (1-based)
   * @param {number} [options.page_size] - Items per page
   * @param {string} [options.language] - Filter by programming language
   * @param {string} [options.status] - Filter by analysis status
   * @returns {Promise<Object>} List of user's analyses with pagination info
   */
  async getUserAnalyses(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.page) params.append('page', options.page);
      if (options.page_size) params.append('page_size', options.page_size);
      if (options.language) params.append('language', options.language);
      if (options.status) params.append('status', options.status);

      // Use the analysis history endpoint that includes all types of analyses
      const response = await httpClient.get(`/analysis/direct/history?${params}`);
      
      if (response.data && response.data.analyses) {
        const analyses = response.data.analyses.map(analysis => ({
          id: analysis.analysis_id,
          filename: analysis.filename,
          language: analysis.language,
          status: analysis.status,
          type: analysis.type, // 'direct', 'repository', or 'batch'
          repositoryName: analysis.repository_name, // For repository analyses
          batchId: analysis.batch_id, // For batch analyses
          createdAt: analysis.created_at,
          completedAt: analysis.completed_at,
          issuesCount: analysis.issues_count || 0,
          errorsCount: analysis.errors_count || 0,
          warningsCount: analysis.warnings_count || 0,
          suggestionsCount: analysis.suggestions_count || 0,
          linesOfCode: analysis.lines_of_code || 0
        }));
        
        return {
          analyses,
          total_count: response.data.total_count || 0,
          page: response.data.page || 1,
          page_size: response.data.page_size || 20,
          has_next: response.data.has_next || false,
          has_previous: response.data.has_previous || false
        };
      }
      
      throw new Error('No analysis data found');
    } catch (error) {
      console.error('Failed to fetch user analyses:', error);
      throw this.handleAnalysisError(error);
    }
  }

  /**
   * Upload and analyze a code file
   * @param {File} file - The file to upload and analyze
   * @param {Object} [options] - Upload options
   * @param {string} [options.language] - Override language detection
   * @param {boolean} [options.autoAnalyze] - Whether to automatically analyze after upload
   * @returns {Promise<Object>} File upload response and optional analysis result
   */
  async uploadFile(file, options = {}) {
    try {
      // Validate file
      this.validateFile(file);

      const formData = new FormData();
      formData.append('file', file);
      
      if (options.language) {
        formData.append('language', options.language);
      }

      const response = await httpClient.post('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        // Track upload progress
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log(`Upload progress: ${percentCompleted}%`);
          
          // Emit custom event for progress tracking
          if (options.onProgress) {
            options.onProgress(percentCompleted);
          }
        }
      });

      const result = {
        filename: response.data.filename,
        content: response.data.content,
        language: response.data.language,
        sizeBytes: response.data.size_bytes,
        sizeKB: response.data.size_kb,
        linesCount: response.data.lines_count,
        uploadId: response.data.upload_id,
        uploadedAt: response.data.uploaded_at,
        contentType: response.data.content_type
      };

      return result;
    } catch (error) {
      console.error('File upload failed:', error);
      throw this.handleAnalysisError(error);
    }
  }

  /**
   * Upload and analyze multiple code files
   * @param {File[]} files - Array of files to upload and analyze
   * @param {Object} [options] - Upload options
   * @param {Function} [options.onProgress] - Progress callback (fileIndex, progress)
   * @param {boolean} [options.autoAnalyze] - Whether to automatically analyze after upload
   * @returns {Promise<Object>} Batch upload response with analysis results
   */
  async uploadMultipleFiles(files, options = {}) {
    try {
      // Validate all files first
      files.forEach((file, index) => {
        try {
          this.validateFile(file);
        } catch (error) {
          throw new Error(`File ${index + 1} (${file.name}): ${error.message}`);
        }
      });

      const formData = new FormData();
      
      // Append all files
      files.forEach((file, index) => {
        formData.append('files', file);
      });

      // Add options
      if (options.autoAnalyze !== undefined) {
        formData.append('auto_analyze', options.autoAnalyze);
      }

      const response = await httpClient.post('/files/upload-multiple-batch', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        // Track upload progress
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log(`Multi-file upload progress: ${percentCompleted}%`);
          
          // For multi-file uploads, we'll distribute progress across files
          if (options.onProgress) {
            const progressPerFile = percentCompleted / files.length;
            files.forEach((_, index) => {
              options.onProgress(index, Math.min(100, progressPerFile * (index + 1)));
            });
          }
        }
      });

      const result = {
        batchId: response.data.batch_id,
        totalFiles: response.data.total_files,
        processedFiles: response.data.processed_files,
        status: response.data.status,
        files: response.data.files?.map(fileResult => ({
          filename: fileResult.filename,
          language: fileResult.language,
          sizeBytes: fileResult.size_bytes,
          linesCount: fileResult.lines_count,
          uploadId: fileResult.upload_id,
          status: fileResult.status,
          issues: this.processIssues(fileResult.issues || [], fileResult.analysis_id),
          metrics: this.processMetrics(fileResult.metrics || {}),
          error: fileResult.error
        })) || [],
        uploadedAt: response.data.uploaded_at,
        estimatedProcessingTime: response.data.estimated_processing_time
      };

      return result;
    } catch (error) {
      console.error('Multi-file upload failed:', error);
      throw this.handleAnalysisError(error);
    }
  }

  /**
   * Get batch analysis status and results
   * @param {string} batchId - The batch ID to check
   * @returns {Promise<Object>} Batch status and results
   */
  async getBatchAnalysisStatus(batchId) {
    try {
      const response = await retryWithBackoff(
        () => httpClient.get(`/files/batch/${batchId}/status`),
        {
          maxRetries: 2,
          baseDelay: 1000,
          shouldRetry: (error) => {
            // Retry on network errors and 5xx status codes
            return !error.response || error.response.status >= 500;
          }
        }
      );
      
      return {
        batch_id: response.data.batch_id,
        status: response.data.status,
        progress_percentage: response.data.progress_percentage,
        total_files: response.data.total_files,
        processed_files: response.data.processed_files,
        successful_files: response.data.successful_files,
        failed_files: response.data.failed_files,
        created_at: response.data.created_at,
        started_at: response.data.started_at,
        completed_at: response.data.completed_at,
        estimated_completion_time: response.data.estimated_completion_time,
        processing_time_seconds: response.data.processing_time_seconds,
        files: response.data.files?.map(fileResult => ({
          filename: fileResult.filename,
          language: fileResult.language,
          status: fileResult.status,
          file_index: fileResult.file_index,
          issues_count: fileResult.issues_count,
          errors_count: fileResult.errors_count,
          warnings_count: fileResult.warnings_count,
          processing_time_seconds: fileResult.processing_time_seconds,
          error_message: fileResult.error_message,
          issues: this.processIssues(fileResult.issues || [], fileResult.analysis_id),
          metrics: this.processMetrics(fileResult.metrics || {})
        })) || []
      };
    } catch (error) {
      console.error('Failed to fetch batch status:', error);
      const errorInfo = handleApiError(error, { operation: 'fetch batch status' });
      throw new Error(errorInfo.message);
    }
  }

  /**
   * Get batch analysis results
   * @param {string} batchId - The batch ID to get results for
   * @returns {Promise<Object>} Batch analysis results
   */
  async getBatchAnalysisResults(batchId) {
    try {
      const response = await retryWithBackoff(
        () => httpClient.get(`/files/batch/${batchId}/results`),
        {
          maxRetries: 2,
          baseDelay: 1000,
          shouldRetry: (error) => {
            // Retry on network errors and 5xx status codes
            return !error.response || error.response.status >= 500;
          }
        }
      );
      
      return {
        batch_id: response.data.batch_id,
        status: response.data.status,
        total_files: response.data.total_files,
        successful_files: response.data.successful_files,
        success_rate: response.data.success_rate,
        completed_at: response.data.completed_at,
        processing_time_seconds: response.data.processing_time_seconds,
        combined_results: response.data.combined_results,
        files: response.data.files?.map(fileResult => ({
          filename: fileResult.filename,
          language: fileResult.language,
          file_size_kb: fileResult.file_size_kb,
          lines_count: fileResult.lines_count,
          issues_count: fileResult.issues_count,
          errors_count: fileResult.errors_count,
          warnings_count: fileResult.warnings_count,
          suggestions_count: fileResult.suggestions_count,
          issues: this.processIssues(fileResult.issues || [], fileResult.analysis_id),
          metrics: this.processMetrics(fileResult.metrics || {}),
          summary: fileResult.summary
        })) || []
      };
    } catch (error) {
      console.error('Failed to fetch batch results:', error);
      const errorInfo = handleApiError(error, { operation: 'fetch batch results' });
      throw new Error(errorInfo.message);
    }
  }

  /**
   * Delete a direct analysis
   * @param {string} analysisId - The analysis ID to delete
   * @returns {Promise<void>}
   */
  async deleteAnalysis(analysisId) {
    try {
      await httpClient.delete(`/analysis/direct/${analysisId}`);
    } catch (error) {
      console.error('Failed to delete analysis:', error);
      throw this.handleAnalysisError(error);
    }
  }

  /**
   * Get analysis statistics for the current user
   * @returns {Promise<Object>} Analysis statistics
   */
  async getAnalysisStats() {
    try {
      const response = await httpClient.get('/analysis/direct/stats');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch analysis stats:', error);
      throw this.handleAnalysisError(error);
    }
  }

  /**
   * Get supported file extensions and upload limits
   * @returns {Promise<Object>} Supported extensions and limits
   */
  async getSupportedExtensions() {
    try {
      const response = await httpClient.get('/files/supported-extensions');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch supported extensions:', error);
      throw this.handleAnalysisError(error);
    }
  }

  /**
   * Process and normalize analysis response data
   * @param {Object} analysisData - Raw analysis data from API
   * @returns {Object} Processed analysis data
   */
  processAnalysisResponse(analysisData) {
    return {
      id: analysisData.analysis_id || analysisData.id,
      status: analysisData.status,
      language: analysisData.language,
      filename: analysisData.filename,
      createdAt: analysisData.created_at,
      completedAt: analysisData.completed_at,
      issues: this.processIssues(analysisData.issues || [], analysisData.id),
      metrics: this.processMetrics(analysisData.metrics || {}),
      summary: analysisData.summary || null,
      fileSizeBytes: analysisData.file_size_bytes,
      processingTimeMs: analysisData.processing_time_ms,
      aiModelUsed: analysisData.ai_model_used
    };
  }

  /**
   * Process batch analysis response data
   * @param {Object} data - Raw batch analysis response data
   * @returns {Object} Processed analysis data
   */
  processBatchAnalysisResponse(data) {
    const allIssues = [];
    const allMetrics = {};
    
    if (data.files && Array.isArray(data.files)) {
      data.files.forEach(file => {
        if (file.issues) {
          allIssues.push(...this.processIssues(file.issues, file.analysis_id));
        }
        if (file.metrics) {
          Object.assign(allMetrics, this.processMetrics(file.metrics));
        }
      });
    }

    return {
      id: data.batch_id,
      filename: `Batch Analysis (${data.total_files} files)`,
      language: 'multiple',
      status: data.status,
      issues: allIssues,
      metrics: allMetrics,
      createdAt: data.created_at,
      completedAt: data.completed_at,
      processingTime: data.processing_time_seconds,
      totalFiles: data.total_files,
      successfulFiles: data.successful_files,
      failedFiles: data.failed_files
    };
  }

  /**
   * Process and normalize analysis history item
   * @param {Object} historyItem - Raw history item data from API
   * @returns {Object} Processed history item data
   */
  processAnalysisHistoryItem(historyItem) {
    return {
      id: historyItem.analysis_id,
      status: historyItem.status,
      language: historyItem.language,
      filename: historyItem.filename,
      issuesCount: historyItem.issues_count,
      errorsCount: historyItem.errors_count,
      warningsCount: historyItem.warnings_count,
      linesOfCode: historyItem.lines_of_code,
      createdAt: historyItem.created_at,
      completedAt: historyItem.completed_at
    };
  }

  /**
   * Process and normalize code issues
   * @param {Array} issues - Raw issues array from API
   * @returns {Array} Processed issues array
   */
  processIssues(issues, analysisId = 'unknown') {
    return issues.map((issue, index) => {
      let issueId = issue.id || issue.issue_id;
      
      // If no proper ID, generate a more robust fallback one
      if (!issueId) {
        issueId = this.generateFallbackId(issue, analysisId);
        console.warn('Generated fallback ID for issue:', issueId, issue);
      }
      
      return {
        id: issueId,
        line: issue.line,
        column: issue.column || 0,
        severity: issue.severity || 'info',
        message: issue.message,
        rule: issue.rule || 'unknown',
        suggestion: issue.suggestion || null,
        category: issue.category || 'general',
        codeExample: issue.code_example || issue.codeExample || null,
        documentation: issue.documentation || null,
        filePath: issue.file_path || null // Add file path for repository analyses
      };
    });
  }

  /**
   * Generate a simple hash for issue ID (fallback when backend doesn't provide proper ID)
   * @param {string} input - Input string to hash
   * @returns {string} Hash-based ID
   */
  generateSimpleHash(input) {
    if (!input || typeof input !== 'string') {
      console.warn('Invalid input for hash generation:', input);
      return '00000000';
    }
    
    let hash = 0;
    for (let i = 0; i < input.length; i++) {
      const char = input.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    const result = Math.abs(hash).toString(16).padStart(8, '0');
    console.log('Generated hash:', result, 'from input:', input);
    return result;
  }

  /**
   * Generate a more robust fallback ID that matches backend expectations
   * @param {Object} issue - Issue object
   * @param {string} analysisId - Analysis ID for context
   * @returns {string} Fallback ID
   */
  generateFallbackId(issue, analysisId = 'unknown') {
    // Create a more robust fallback ID that includes analysis context
    const fallbackInput = `${analysisId}-${issue.line || 0}-${issue.column || 0}-${issue.rule || 'unknown'}-${issue.message || ''}`;
    const hash = this.generateSimpleHash(fallbackInput);
    
    // Ensure we have a valid hash, fallback to timestamp if needed
    const validHash = hash && hash !== '00000000' ? hash : Date.now().toString(16).slice(-8);
    const fallbackId = `fallback-${validHash}`;
    
    console.log('Generated fallback ID:', fallbackId, 'from input:', fallbackInput, 'hash:', hash);
    return fallbackId;
  }

  /**
   * Process and normalize code metrics
   * @param {Object} metrics - Raw metrics object from API
   * @returns {Object} Processed metrics object
   */
  processMetrics(metrics) {
    return {
      linesOfCode: metrics.lines_of_code || metrics.linesOfCode || 0,
      totalLines: metrics.total_lines || metrics.totalLines || 0,
      complexity: metrics.complexity || 0,
      maintainabilityIndex: metrics.maintainability_index || metrics.maintainabilityIndex || 0,
      duplicateLines: metrics.duplicate_lines || metrics.duplicateLines || 0,
      testCoverage: metrics.test_coverage || metrics.testCoverage || null,
      commentLines: metrics.comment_lines || metrics.commentLines || 0,
      blankLines: metrics.blank_lines || metrics.blankLines || 0,
      functionCount: metrics.function_count || metrics.functionCount || 0,
      classCount: metrics.class_count || metrics.classCount || 0,
      commentRatio: metrics.comment_ratio || metrics.commentRatio || 0,
      complexityPerFunction: metrics.complexity_per_function || metrics.complexityPerFunction || null
    };
  }

  /**
   * Validate uploaded file (enhanced with dynamic limits)
   * @param {File} file - File to validate
   * @param {Object} [limits] - Optional limits from server
   * @throws {Error} If file is invalid
   */
  validateFile(file, limits = null) {
    // Use server-provided limits or fallback to defaults
    const maxSizeKB = limits?.max_file_size_kb || 5120; // 5MB default
    const maxSizeBytes = maxSizeKB * 1024;
    const maxLines = limits?.max_lines || 10000;
    const supportedExtensions = limits?.supported_extensions || [
      '.js', '.jsx', '.ts', '.tsx',
      '.py', '.java', '.c', '.cpp', '.cc', '.cxx',
      '.cs', '.html', '.htm', '.css', '.json',
      '.xml', '.php', '.rb', '.go', '.rs',
      '.swift', '.kt', '.scala', '.sh', '.bash'
    ];

    if (!file) {
      throw new Error('No file provided');
    }

    if (file.size > maxSizeBytes) {
      throw new Error(`File size exceeds maximum limit of ${maxSizeKB / 1024}MB`);
    }

    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    const isValidExtension = supportedExtensions.includes(fileExtension);

    if (!isValidExtension) {
      throw new Error(`File type not supported. Allowed extensions: ${supportedExtensions.join(', ')}`);
    }

    // Additional validation for text files
    if (file.type && !file.type.startsWith('text/') && 
        !['application/javascript', 'application/json', 'application/xml'].includes(file.type)) {
      console.warn('File MIME type may not be supported:', file.type);
    }
  }

  /**
   * Handle analysis-related errors
   * @param {Error} error - The error to handle
   * @returns {Error} Processed error with user-friendly message
   */
  handleAnalysisError(error) {
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          return new Error(data.detail || 'Invalid request. Please check your input.');
        case 401:
          return new Error('Authentication required. Please log in.');
        case 403:
          return new Error('Access forbidden. You may not have permission for this operation.');
        case 404:
          return new Error('Analysis not found.');
        case 413:
          return new Error('File too large. Please upload a smaller file.');
        case 415:
          return new Error('Unsupported file type.');
        case 422:
          return new Error(data.detail || 'Validation error. Please check your input.');
        case 429:
          return new Error('Too many requests. Please try again later.');
        case 500:
          return new Error('Server error during analysis. Please try again later.');
        case 503:
          return new Error('Analysis service temporarily unavailable. Please try again later.');
        default:
          return new Error(data.detail || 'Analysis failed. Please try again.');
      }
    } else if (error.request) {
      return new Error('Network error. Please check your connection and try again.');
    } else {
      return new Error(error.message || 'An unexpected error occurred during analysis.');
    }
  }

  /**
   * Get supported programming languages
   * @returns {Array} List of supported languages
   */
  getSupportedLanguages() {
    return [
      { value: 'javascript', label: 'JavaScript', extensions: ['.js', '.jsx'] },
      { value: 'typescript', label: 'TypeScript', extensions: ['.ts', '.tsx'] },
      { value: 'python', label: 'Python', extensions: ['.py'] },
      { value: 'java', label: 'Java', extensions: ['.java'] },
      { value: 'c', label: 'C', extensions: ['.c'] },
      { value: 'cpp', label: 'C++', extensions: ['.cpp', '.cc', '.cxx'] },
      { value: 'csharp', label: 'C#', extensions: ['.cs'] },
      { value: 'html', label: 'HTML', extensions: ['.html', '.htm'] },
      { value: 'css', label: 'CSS', extensions: ['.css'] },
      { value: 'json', label: 'JSON', extensions: ['.json'] },
      { value: 'xml', label: 'XML', extensions: ['.xml'] },
      { value: 'php', label: 'PHP', extensions: ['.php'] },
      { value: 'ruby', label: 'Ruby', extensions: ['.rb'] },
      { value: 'go', label: 'Go', extensions: ['.go'] },
      { value: 'rust', label: 'Rust', extensions: ['.rs'] },
      { value: 'swift', label: 'Swift', extensions: ['.swift'] },
      { value: 'kotlin', label: 'Kotlin', extensions: ['.kt'] },
      { value: 'scala', label: 'Scala', extensions: ['.scala'] },
      { value: 'shell', label: 'Shell', extensions: ['.sh', '.bash'] }
    ];
  }

  /**
   * Detect programming language from filename
   * @param {string} filename - The filename to analyze
   * @returns {string} Detected language or 'text' as fallback
   */
  detectLanguageFromFilename(filename) {
    if (!filename) return 'text';
    
    const extension = '.' + filename.split('.').pop().toLowerCase();
    const languages = this.getSupportedLanguages();
    
    for (const lang of languages) {
      if (lang.extensions.includes(extension)) {
        return lang.value;
      }
    }
    
    return 'text';
  }
}

// Export singleton instance
const analysisService = new AnalysisService();
export default analysisService;