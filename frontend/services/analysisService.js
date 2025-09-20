import httpClient from './httpClient.js';

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
   * Get analysis result by ID
   * @param {string|number} analysisId - The analysis ID
   * @returns {Promise<Object>} Analysis result data
   */
  async getAnalysisById(analysisId) {
    try {
      const response = await httpClient.get(`/analysis/${analysisId}`);
      return this.processAnalysisResponse(response.data);
    } catch (error) {
      console.error('Failed to fetch analysis:', error);
      throw this.handleAnalysisError(error);
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
   * Get user's analysis history
   * @param {Object} [options] - Query options
   * @param {number} [options.limit] - Maximum number of results
   * @param {number} [options.offset] - Offset for pagination
   * @returns {Promise<Object>} List of user's analyses
   */
  async getUserAnalyses(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.limit) params.append('limit', options.limit);
      if (options.offset) params.append('offset', options.offset);

      const response = await httpClient.get(`/analysis/user?${params}`);
      
      return {
        analyses: response.data.analyses?.map(analysis => this.processAnalysisResponse(analysis)) || [],
        total: response.data.total || 0,
        limit: response.data.limit || 10,
        offset: response.data.offset || 0
      };
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
      
      if (options.autoAnalyze !== undefined) {
        formData.append('auto_analyze', options.autoAnalyze.toString());
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
        size: response.data.size,
        uploadId: response.data.upload_id
      };

      // If analysis was requested and included in response
      if (response.data.analysis) {
        result.analysis = this.processAnalysisResponse(response.data.analysis);
      }

      return result;
    } catch (error) {
      console.error('File upload failed:', error);
      throw this.handleAnalysisError(error);
    }
  }

  /**
   * Delete an analysis
   * @param {string|number} analysisId - The analysis ID to delete
   * @returns {Promise<void>}
   */
  async deleteAnalysis(analysisId) {
    try {
      await httpClient.delete(`/analysis/${analysisId}`);
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
      const response = await httpClient.get('/analysis/stats');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch analysis stats:', error);
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
      id: analysisData.id,
      status: analysisData.status,
      language: analysisData.language,
      filename: analysisData.filename,
      createdAt: analysisData.created_at,
      completedAt: analysisData.completed_at,
      issues: this.processIssues(analysisData.issues || []),
      metrics: this.processMetrics(analysisData.metrics || {}),
      suggestions: analysisData.suggestions || [],
      summary: analysisData.summary || null
    };
  }

  /**
   * Process and normalize code issues
   * @param {Array} issues - Raw issues array from API
   * @returns {Array} Processed issues array
   */
  processIssues(issues) {
    return issues.map(issue => ({
      id: issue.id || `${issue.line}-${issue.column}-${Date.now()}`,
      line: issue.line,
      column: issue.column || 0,
      severity: issue.severity || 'info',
      message: issue.message,
      rule: issue.rule || 'unknown',
      suggestion: issue.suggestion || null,
      category: issue.category || 'general'
    }));
  }

  /**
   * Process and normalize code metrics
   * @param {Object} metrics - Raw metrics object from API
   * @returns {Object} Processed metrics object
   */
  processMetrics(metrics) {
    return {
      linesOfCode: metrics.lines_of_code || metrics.linesOfCode || 0,
      complexity: metrics.complexity || 0,
      maintainabilityIndex: metrics.maintainability_index || metrics.maintainabilityIndex || 0,
      duplicateLines: metrics.duplicate_lines || metrics.duplicateLines || 0,
      testCoverage: metrics.test_coverage || metrics.testCoverage || null
    };
  }

  /**
   * Validate uploaded file
   * @param {File} file - File to validate
   * @throws {Error} If file is invalid
   */
  validateFile(file) {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
      'text/plain',
      'text/javascript',
      'application/javascript',
      'text/x-python',
      'text/x-java-source',
      'text/x-c',
      'text/x-c++',
      'text/x-csharp',
      'text/html',
      'text/css',
      'application/json',
      'text/xml',
      'application/xml'
    ];

    const allowedExtensions = [
      '.js', '.jsx', '.ts', '.tsx',
      '.py', '.java', '.c', '.cpp', '.cc', '.cxx',
      '.cs', '.html', '.htm', '.css', '.json',
      '.xml', '.php', '.rb', '.go', '.rs',
      '.swift', '.kt', '.scala', '.sh', '.bash'
    ];

    if (!file) {
      throw new Error('No file provided');
    }

    if (file.size > maxSize) {
      throw new Error(`File size exceeds maximum limit of ${maxSize / (1024 * 1024)}MB`);
    }

    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    const isValidType = allowedTypes.includes(file.type) || 
                       allowedExtensions.includes(fileExtension);

    if (!isValidType) {
      throw new Error(`File type not supported. Allowed extensions: ${allowedExtensions.join(', ')}`);
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