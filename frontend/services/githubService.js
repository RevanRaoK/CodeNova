import httpClient from './httpClient.js';

/**
 * GitHub integration service for handling repository connections, webhooks, and PR analysis
 */
class GitHubService {
  /**
   * Get connected GitHub repositories for the current user
   * @returns {Promise<Array>} List of connected repositories
   */
  async getRepositories() {
    try {
      const response = await httpClient.get('/github/repositories');
      // Backend returns { repositories: [], total, page, per_page }
      // Return just the repositories array for backward compatibility
      return response.data.repositories || [];
    } catch (error) {
      console.error('Failed to fetch repositories:', error);
      // Return empty array on error to prevent frontend crash
      return [];
    }
  }

  /**
   * Connect a new GitHub repository
   * @param {Object} repoData - Repository connection data
   * @param {string} repoData.repo_url - GitHub repository URL
   * @param {string} repoData.access_token - GitHub access token (optional if using OAuth)
   * @returns {Promise<Object>} Connected repository data
   */
  async connectRepository(repoData) {
    try {
      const response = await httpClient.post('/github/repositories', repoData);
      return response.data;
    } catch (error) {
      console.error('Failed to connect repository:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Disconnect a GitHub repository
   * @param {string} repositoryId - Repository ID to disconnect
   * @returns {Promise<void>}
   */
  async disconnectRepository(repositoryId) {
    try {
      await httpClient.delete(`/github/repositories/${repositoryId}`);
    } catch (error) {
      console.error('Failed to disconnect repository:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get webhook status for a repository
   * @param {string} repositoryId - Repository ID
   * @returns {Promise<Object>} Webhook status information
   */
  async getWebhookStatus(repositoryId) {
    try {
      const response = await httpClient.get(
        `/github/repositories/${repositoryId}/webhook`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get webhook status:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Setup or update webhook for a repository
   * @param {string} repositoryId - Repository ID
   * @param {Object} webhookConfig - Webhook configuration
   * @returns {Promise<Object>} Webhook setup result
   */
  async setupWebhook(repositoryId, webhookConfig = {}) {
    try {
      const response = await httpClient.post(
        `/github/repositories/${repositoryId}/webhook`,
        webhookConfig
      );
      return response.data;
    } catch (error) {
      console.error('Failed to setup webhook:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Trigger full repository code analysis
   * @param {string} repositoryId - Repository ID
   * @param {Object} options - Analysis options
   * @param {string} options.branch - Branch to analyze (default: main)
   * @param {Array<string>} options.filePatterns - File patterns to include
   * @returns {Promise<Object>} Analysis trigger result
   */
  async analyzeRepository(repositoryId, options = {}) {
    try {
      const params = {
        branch: options.branch || 'main',
      };
      if (options.filePatterns) {
        params.file_patterns = options.filePatterns;
      }
      const response = await httpClient.post(
        `/github/repositories/${repositoryId}/analyze`,
        {},
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to trigger repository analysis:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get repository analysis progress
   * @param {string} repositoryId - Repository ID
   * @returns {Promise<Object>} Analysis progress and status
   */
  async getRepositoryAnalysisProgress(repositoryId) {
    try {
      const response = await httpClient.get(
        `/github/repositories/${repositoryId}/analyze/progress`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch analysis progress:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get PR analyses for a repository
   * @param {string} repositoryId - Repository ID
   * @param {Object} params - Query parameters
   * @param {number} params.page - Page number
   * @param {number} params.limit - Items per page
   * @param {string} params.status - Filter by analysis status
   * @returns {Promise<Object>} PR analyses with pagination
   */
  async getPRAnalyses(repositoryId, params = {}) {
    try {
      const response = await httpClient.get(
        `/github/repositories/${repositoryId}/pr-analyses`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch PR analyses:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get specific PR analysis details
   * @param {string} repositoryId - Repository ID
   * @param {string} analysisId - PR analysis ID
   * @returns {Promise<Object>} PR analysis details
   */
  async getPRAnalysis(repositoryId, analysisId) {
    try {
      const response = await httpClient.get(
        `/github/repositories/${repositoryId}/pr-analyses/${analysisId}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch PR analysis:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Trigger manual PR analysis
   * @param {string} repositoryId - Repository ID
   * @param {number} prNumber - Pull request number
   * @returns {Promise<Object>} Analysis trigger result
   */
  async triggerPRAnalysis(repositoryId, prNumber) {
    try {
      const response = await httpClient.post(
        `/github/repositories/${repositoryId}/pr-analyses`,
        {
          pr_number: prNumber,
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to trigger PR analysis:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get repository issues created by the analysis system
   * @param {string} repositoryId - Repository ID
   * @param {Object} params - Query parameters
   * @param {number} params.page - Page number
   * @param {number} params.limit - Items per page
   * @param {string} params.search - Search query
   * @param {string} params.status - Filter by issue status
   * @returns {Promise<Object>} Repository issues with pagination
   */
  async getRepositoryIssues(repositoryId, params = {}) {
    try {
      const response = await httpClient.get(
        `/github/repositories/${repositoryId}/issues`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch repository issues:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get GitHub OAuth authorization URL
   * @param {string} redirectUri - Redirect URI after OAuth
   * @param {Array<string>} scopes - Required OAuth scopes
   * @returns {Promise<Object>} OAuth authorization data
   */
  async getOAuthUrl(redirectUri, scopes = ['repo']) {
    try {
      const response = await httpClient.get('/github/oauth/authorize');
      return response.data;
    } catch (error) {
      console.error('Failed to get OAuth URL:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Complete GitHub OAuth flow
   * @param {string} resultId - OAuth result ID from callback redirect
   * @returns {Promise<Object>} OAuth completion result
   */
  async completeOAuth(resultId) {
    try {
      const response = await httpClient.post('/github/oauth/complete', {
        result_id: resultId,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to complete OAuth:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get current GitHub OAuth status
   * @returns {Promise<Object>} OAuth status information
   */
  async getOAuthStatus() {
    try {
      const response = await httpClient.get('/github/oauth/status');
      return response.data;
    } catch (error) {
      console.error('Failed to get OAuth status:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Revoke GitHub OAuth access
   * @returns {Promise<void>}
   */
  async revokeOAuth() {
    try {
      await httpClient.delete('/github/oauth');
    } catch (error) {
      console.error('Failed to revoke OAuth:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get repository statistics and analytics
   * @param {string} repositoryId - Repository ID
   * @param {Object} params - Query parameters
   * @param {string} params.period - Time period (7d, 30d, 90d)
   * @returns {Promise<Object>} Repository analytics data
   */
  async getRepositoryAnalytics(repositoryId, params = {}) {
    try {
      const response = await httpClient.get(
        `/github/repositories/${repositoryId}/analytics`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch repository analytics:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Handle API errors and provide user-friendly messages
   * @param {Error} error - The error to handle
   * @returns {Error} Processed error with user-friendly message
   */
  handleError(error) {
    if (error.response) {
      const { status, data } = error.response;

      switch (status) {
        case 400:
          return new Error(
            data.detail || 'Invalid request. Please check your input.'
          );
        case 401:
          return new Error('Authentication required. Please log in again.');
        case 403:
          return new Error(
            'Access denied. You may not have permission to access this repository.'
          );
        case 404:
          return new Error('Repository not found or not accessible.');
        case 409:
          return new Error(
            'Repository is already connected or webhook already exists.'
          );
        case 422:
          return new Error(data.detail || 'Invalid data provided.');
        case 429:
          return new Error('Rate limit exceeded. Please try again later.');
        case 500:
          return new Error('Server error. Please try again later.');
        case 502:
          return new Error(
            'GitHub API is temporarily unavailable. Please try again later.'
          );
        default:
          return new Error(data.detail || 'An unexpected error occurred.');
      }
    } else if (error.request) {
      return new Error(
        'Network error. Please check your connection and try again.'
      );
    } else {
      return new Error(error.message || 'An unexpected error occurred.');
    }
  }
}

// Export singleton instance
const githubService = new GitHubService();
export default githubService;
