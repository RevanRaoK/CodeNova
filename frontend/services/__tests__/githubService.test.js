import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import githubService from '../githubService.js';
import httpClient from '../httpClient.js';

// Mock the httpClient
vi.mock('../httpClient.js', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  }
}));

describe('GitHubService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('getRepositories', () => {
    it('should fetch repositories successfully', async () => {
      const mockRepositories = [
        { id: '1', name: 'repo1', url: 'https://github.com/user/repo1' },
        { id: '2', name: 'repo2', url: 'https://github.com/user/repo2' }
      ];

      httpClient.get.mockResolvedValue({ data: mockRepositories });

      const result = await githubService.getRepositories();

      expect(httpClient.get).toHaveBeenCalledWith('/github/repositories');
      expect(result).toEqual(mockRepositories);
    });

    it('should handle errors when fetching repositories', async () => {
      const mockError = new Error('Network error');
      mockError.response = { status: 500, data: { detail: 'Server error' } };

      httpClient.get.mockRejectedValue(mockError);

      await expect(githubService.getRepositories()).rejects.toThrow('Server error. Please try again later.');
    });
  });

  describe('connectRepository', () => {
    it('should connect repository successfully', async () => {
      const repoData = {
        repo_url: 'https://github.com/user/repo',
        access_token: 'token123'
      };
      const mockResponse = { id: '1', ...repoData, connected: true };

      httpClient.post.mockResolvedValue({ data: mockResponse });

      const result = await githubService.connectRepository(repoData);

      expect(httpClient.post).toHaveBeenCalledWith('/github/repositories', repoData);
      expect(result).toEqual(mockResponse);
    });

    it('should handle repository already connected error', async () => {
      const repoData = { repo_url: 'https://github.com/user/repo' };
      const mockError = new Error('Conflict');
      mockError.response = { status: 409, data: { detail: 'Repository already connected' } };

      httpClient.post.mockRejectedValue(mockError);

      await expect(githubService.connectRepository(repoData)).rejects.toThrow('Repository is already connected or webhook already exists.');
    });
  });

  describe('disconnectRepository', () => {
    it('should disconnect repository successfully', async () => {
      const repositoryId = 'repo123';

      httpClient.delete.mockResolvedValue({});

      await githubService.disconnectRepository(repositoryId);

      expect(httpClient.delete).toHaveBeenCalledWith('/github/repositories/repo123');
    });

    it('should handle repository not found error', async () => {
      const repositoryId = 'nonexistent';
      const mockError = new Error('Not found');
      mockError.response = { status: 404, data: { detail: 'Repository not found' } };

      httpClient.delete.mockRejectedValue(mockError);

      await expect(githubService.disconnectRepository(repositoryId)).rejects.toThrow('Repository not found or not accessible.');
    });
  });

  describe('getWebhookStatus', () => {
    it('should get webhook status successfully', async () => {
      const repositoryId = 'repo123';
      const mockStatus = { active: true, url: 'https://api.example.com/webhook' };

      httpClient.get.mockResolvedValue({ data: mockStatus });

      const result = await githubService.getWebhookStatus(repositoryId);

      expect(httpClient.get).toHaveBeenCalledWith('/github/repositories/repo123/webhook');
      expect(result).toEqual(mockStatus);
    });

    it('should handle webhook not found', async () => {
      const repositoryId = 'repo123';
      const mockError = new Error('Not found');
      mockError.response = { status: 404, data: { detail: 'Webhook not found' } };

      httpClient.get.mockRejectedValue(mockError);

      await expect(githubService.getWebhookStatus(repositoryId)).rejects.toThrow('Repository not found or not accessible.');
    });
  });

  describe('setupWebhook', () => {
    it('should setup webhook successfully', async () => {
      const repositoryId = 'repo123';
      const webhookConfig = { events: ['pull_request', 'push'] };
      const mockResponse = { id: 'webhook123', active: true };

      httpClient.post.mockResolvedValue({ data: mockResponse });

      const result = await githubService.setupWebhook(repositoryId, webhookConfig);

      expect(httpClient.post).toHaveBeenCalledWith('/github/repositories/repo123/webhook', webhookConfig);
      expect(result).toEqual(mockResponse);
    });

    it('should setup webhook with default config', async () => {
      const repositoryId = 'repo123';
      const mockResponse = { id: 'webhook123', active: true };

      httpClient.post.mockResolvedValue({ data: mockResponse });

      const result = await githubService.setupWebhook(repositoryId);

      expect(httpClient.post).toHaveBeenCalledWith('/github/repositories/repo123/webhook', {});
      expect(result).toEqual(mockResponse);
    });

    it('should handle permission denied error', async () => {
      const repositoryId = 'repo123';
      const mockError = new Error('Forbidden');
      mockError.response = { status: 403, data: { detail: 'Insufficient permissions' } };

      httpClient.post.mockRejectedValue(mockError);

      await expect(githubService.setupWebhook(repositoryId)).rejects.toThrow('Access denied. You may not have permission to access this repository.');
    });
  });

  describe('getPRAnalyses', () => {
    it('should get PR analyses successfully', async () => {
      const repositoryId = 'repo123';
      const params = { page: 1, limit: 10, status: 'completed' };
      const mockResponse = {
        analyses: [
          { id: 'analysis1', pr_number: 1, status: 'completed' },
          { id: 'analysis2', pr_number: 2, status: 'completed' }
        ],
        pagination: { page: 1, limit: 10, total: 2 }
      };

      httpClient.get.mockResolvedValue({ data: mockResponse });

      const result = await githubService.getPRAnalyses(repositoryId, params);

      expect(httpClient.get).toHaveBeenCalledWith('/github/repositories/repo123/pr-analyses', { params });
      expect(result).toEqual(mockResponse);
    });

    it('should get PR analyses with default params', async () => {
      const repositoryId = 'repo123';
      const mockResponse = { analyses: [], pagination: { page: 1, limit: 20, total: 0 } };

      httpClient.get.mockResolvedValue({ data: mockResponse });

      const result = await githubService.getPRAnalyses(repositoryId);

      expect(httpClient.get).toHaveBeenCalledWith('/github/repositories/repo123/pr-analyses', { params: {} });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getPRAnalysis', () => {
    it('should get specific PR analysis successfully', async () => {
      const repositoryId = 'repo123';
      const analysisId = 'analysis123';
      const mockAnalysis = {
        id: 'analysis123',
        pr_number: 1,
        status: 'completed',
        results: { issues: [], suggestions: [] }
      };

      httpClient.get.mockResolvedValue({ data: mockAnalysis });

      const result = await githubService.getPRAnalysis(repositoryId, analysisId);

      expect(httpClient.get).toHaveBeenCalledWith('/github/repositories/repo123/pr-analyses/analysis123');
      expect(result).toEqual(mockAnalysis);
    });

    it('should handle analysis not found', async () => {
      const repositoryId = 'repo123';
      const analysisId = 'nonexistent';
      const mockError = new Error('Not found');
      mockError.response = { status: 404, data: { detail: 'Analysis not found' } };

      httpClient.get.mockRejectedValue(mockError);

      await expect(githubService.getPRAnalysis(repositoryId, analysisId)).rejects.toThrow('Repository not found or not accessible.');
    });
  });

  describe('triggerPRAnalysis', () => {
    it('should trigger PR analysis successfully', async () => {
      const repositoryId = 'repo123';
      const prNumber = 42;
      const mockResponse = { analysis_id: 'analysis123', status: 'queued' };

      httpClient.post.mockResolvedValue({ data: mockResponse });

      const result = await githubService.triggerPRAnalysis(repositoryId, prNumber);

      expect(httpClient.post).toHaveBeenCalledWith('/github/repositories/repo123/pr-analyses', {
        pr_number: prNumber
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle invalid PR number', async () => {
      const repositoryId = 'repo123';
      const prNumber = 999;
      const mockError = new Error('Bad request');
      mockError.response = { status: 400, data: { detail: 'PR not found' } };

      httpClient.post.mockRejectedValue(mockError);

      await expect(githubService.triggerPRAnalysis(repositoryId, prNumber)).rejects.toThrow('Invalid request. Please check your input.');
    });
  });

  describe('getRepositoryIssues', () => {
    it('should get repository issues successfully', async () => {
      const repositoryId = 'repo123';
      const params = { page: 1, limit: 10, search: 'bug', status: 'open' };
      const mockResponse = {
        issues: [
          { id: 'issue1', title: 'Bug in component', status: 'open' },
          { id: 'issue2', title: 'Another bug', status: 'open' }
        ],
        pagination: { page: 1, limit: 10, total: 2 }
      };

      httpClient.get.mockResolvedValue({ data: mockResponse });

      const result = await githubService.getRepositoryIssues(repositoryId, params);

      expect(httpClient.get).toHaveBeenCalledWith('/github/repositories/repo123/issues', { params });
      expect(result).toEqual(mockResponse);
    });

    it('should get repository issues with default params', async () => {
      const repositoryId = 'repo123';
      const mockResponse = { issues: [], pagination: { page: 1, limit: 20, total: 0 } };

      httpClient.get.mockResolvedValue({ data: mockResponse });

      const result = await githubService.getRepositoryIssues(repositoryId);

      expect(httpClient.get).toHaveBeenCalledWith('/github/repositories/repo123/issues', { params: {} });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('OAuth methods', () => {
    describe('getOAuthUrl', () => {
      it('should get OAuth URL successfully', async () => {
        const redirectUri = 'https://app.example.com/callback';
        const scopes = ['repo', 'user'];
        const mockResponse = {
          authorization_url: 'https://github.com/login/oauth/authorize?client_id=123&redirect_uri=...',
          state: 'random-state-string'
        };

        httpClient.post.mockResolvedValue({ data: mockResponse });

        const result = await githubService.getOAuthUrl(redirectUri, scopes);

        expect(httpClient.post).toHaveBeenCalledWith('/github/oauth/authorize', {
          redirect_uri: redirectUri,
          scopes
        });
        expect(result).toEqual(mockResponse);
      });

      it('should get OAuth URL with default scopes', async () => {
        const redirectUri = 'https://app.example.com/callback';
        const mockResponse = {
          authorization_url: 'https://github.com/login/oauth/authorize?client_id=123&redirect_uri=...',
          state: 'random-state-string'
        };

        httpClient.post.mockResolvedValue({ data: mockResponse });

        const result = await githubService.getOAuthUrl(redirectUri);

        expect(httpClient.post).toHaveBeenCalledWith('/github/oauth/authorize', {
          redirect_uri: redirectUri,
          scopes: ['repo']
        });
        expect(result).toEqual(mockResponse);
      });
    });

    describe('completeOAuth', () => {
      it('should complete OAuth successfully', async () => {
        const code = 'oauth-code-123';
        const state = 'state-string';
        const mockResponse = {
          access_token: 'token123',
          user: { login: 'testuser', id: 12345 }
        };

        httpClient.post.mockResolvedValue({ data: mockResponse });

        const result = await githubService.completeOAuth(code, state);

        expect(httpClient.post).toHaveBeenCalledWith('/github/oauth/callback', {
          code,
          state
        });
        expect(result).toEqual(mockResponse);
      });

      it('should handle invalid OAuth code', async () => {
        const code = 'invalid-code';
        const state = 'state-string';
        const mockError = new Error('Bad request');
        mockError.response = { status: 400, data: { detail: 'Invalid authorization code' } };

        httpClient.post.mockRejectedValue(mockError);

        await expect(githubService.completeOAuth(code, state)).rejects.toThrow('Invalid request. Please check your input.');
      });
    });

    describe('getOAuthStatus', () => {
      it('should get OAuth status successfully', async () => {
        const mockStatus = {
          connected: true,
          user: { login: 'testuser', id: 12345 },
          scopes: ['repo', 'user']
        };

        httpClient.get.mockResolvedValue({ data: mockStatus });

        const result = await githubService.getOAuthStatus();

        expect(httpClient.get).toHaveBeenCalledWith('/github/oauth/status');
        expect(result).toEqual(mockStatus);
      });

      it('should handle unauthorized status check', async () => {
        const mockError = new Error('Unauthorized');
        mockError.response = { status: 401, data: { detail: 'Not authenticated' } };

        httpClient.get.mockRejectedValue(mockError);

        await expect(githubService.getOAuthStatus()).rejects.toThrow('Authentication required. Please log in again.');
      });
    });

    describe('revokeOAuth', () => {
      it('should revoke OAuth successfully', async () => {
        httpClient.delete.mockResolvedValue({});

        await githubService.revokeOAuth();

        expect(httpClient.delete).toHaveBeenCalledWith('/github/oauth');
      });

      it('should handle revoke error', async () => {
        const mockError = new Error('Server error');
        mockError.response = { status: 500, data: { detail: 'Failed to revoke token' } };

        httpClient.delete.mockRejectedValue(mockError);

        await expect(githubService.revokeOAuth()).rejects.toThrow('Server error. Please try again later.');
      });
    });
  });

  describe('getRepositoryAnalytics', () => {
    it('should get repository analytics successfully', async () => {
      const repositoryId = 'repo123';
      const params = { period: '30d' };
      const mockAnalytics = {
        period: '30d',
        pr_count: 15,
        analysis_count: 12,
        issues_found: 45,
        issues_resolved: 38,
        trends: { pr_frequency: 'increasing', issue_resolution_rate: 0.84 }
      };

      httpClient.get.mockResolvedValue({ data: mockAnalytics });

      const result = await githubService.getRepositoryAnalytics(repositoryId, params);

      expect(httpClient.get).toHaveBeenCalledWith('/github/repositories/repo123/analytics', { params });
      expect(result).toEqual(mockAnalytics);
    });

    it('should get repository analytics with default params', async () => {
      const repositoryId = 'repo123';
      const mockAnalytics = {
        period: '7d',
        pr_count: 3,
        analysis_count: 2,
        issues_found: 8,
        issues_resolved: 6
      };

      httpClient.get.mockResolvedValue({ data: mockAnalytics });

      const result = await githubService.getRepositoryAnalytics(repositoryId);

      expect(httpClient.get).toHaveBeenCalledWith('/github/repositories/repo123/analytics', { params: {} });
      expect(result).toEqual(mockAnalytics);
    });
  });

  describe('handleError', () => {
    it('should handle 400 Bad Request error', () => {
      const error = new Error('Bad Request');
      error.response = { status: 400, data: { detail: 'Invalid input' } };

      const result = githubService.handleError(error);

      expect(result.message).toBe('Invalid input');
    });

    it('should handle 401 Unauthorized error', () => {
      const error = new Error('Unauthorized');
      error.response = { status: 401, data: {} };

      const result = githubService.handleError(error);

      expect(result.message).toBe('Authentication required. Please log in again.');
    });

    it('should handle 403 Forbidden error', () => {
      const error = new Error('Forbidden');
      error.response = { status: 403, data: {} };

      const result = githubService.handleError(error);

      expect(result.message).toBe('Access denied. You may not have permission to access this repository.');
    });

    it('should handle 404 Not Found error', () => {
      const error = new Error('Not Found');
      error.response = { status: 404, data: {} };

      const result = githubService.handleError(error);

      expect(result.message).toBe('Repository not found or not accessible.');
    });

    it('should handle 409 Conflict error', () => {
      const error = new Error('Conflict');
      error.response = { status: 409, data: {} };

      const result = githubService.handleError(error);

      expect(result.message).toBe('Repository is already connected or webhook already exists.');
    });

    it('should handle 422 Unprocessable Entity error', () => {
      const error = new Error('Unprocessable Entity');
      error.response = { status: 422, data: { detail: 'Validation failed' } };

      const result = githubService.handleError(error);

      expect(result.message).toBe('Validation failed');
    });

    it('should handle 429 Rate Limited error', () => {
      const error = new Error('Too Many Requests');
      error.response = { status: 429, data: {} };

      const result = githubService.handleError(error);

      expect(result.message).toBe('Rate limit exceeded. Please try again later.');
    });

    it('should handle 500 Internal Server Error', () => {
      const error = new Error('Internal Server Error');
      error.response = { status: 500, data: {} };

      const result = githubService.handleError(error);

      expect(result.message).toBe('Server error. Please try again later.');
    });

    it('should handle 502 Bad Gateway error', () => {
      const error = new Error('Bad Gateway');
      error.response = { status: 502, data: {} };

      const result = githubService.handleError(error);

      expect(result.message).toBe('GitHub API is temporarily unavailable. Please try again later.');
    });

    it('should handle unknown HTTP error', () => {
      const error = new Error('Unknown Error');
      error.response = { status: 418, data: { detail: 'I am a teapot' } };

      const result = githubService.handleError(error);

      expect(result.message).toBe('I am a teapot');
    });

    it('should handle network error (no response)', () => {
      const error = new Error('Network Error');
      error.request = {};

      const result = githubService.handleError(error);

      expect(result.message).toBe('Network error. Please check your connection and try again.');
    });

    it('should handle generic error', () => {
      const error = new Error('Something went wrong');

      const result = githubService.handleError(error);

      expect(result.message).toBe('Something went wrong');
    });

    it('should handle error without message', () => {
      const error = new Error();

      const result = githubService.handleError(error);

      expect(result.message).toBe('An unexpected error occurred.');
    });
  });

  describe('Edge cases and error scenarios', () => {
    it('should handle empty response data', async () => {
      httpClient.get.mockResolvedValue({ data: null });

      const result = await githubService.getRepositories();

      expect(result).toBeNull();
    });

    it('should handle malformed error response', async () => {
      const mockError = new Error('Malformed');
      mockError.response = { status: 400 }; // No data property

      httpClient.get.mockRejectedValue(mockError);

      await expect(githubService.getRepositories()).rejects.toThrow('Invalid request. Please check your input.');
    });

    it('should handle timeout errors', async () => {
      const mockError = new Error('timeout of 5000ms exceeded');
      mockError.code = 'ECONNABORTED';

      httpClient.get.mockRejectedValue(mockError);

      await expect(githubService.getRepositories()).rejects.toThrow('timeout of 5000ms exceeded');
    });

    it('should handle concurrent requests properly', async () => {
      const mockRepo1 = { id: '1', name: 'repo1' };
      const mockRepo2 = { id: '2', name: 'repo2' };

      httpClient.get
        .mockResolvedValueOnce({ data: mockRepo1 })
        .mockResolvedValueOnce({ data: mockRepo2 });

      const [result1, result2] = await Promise.all([
        githubService.getPRAnalysis('repo1', 'analysis1'),
        githubService.getPRAnalysis('repo2', 'analysis2')
      ]);

      expect(result1).toEqual(mockRepo1);
      expect(result2).toEqual(mockRepo2);
      expect(httpClient.get).toHaveBeenCalledTimes(2);
    });
  });
}); httpClient.js;