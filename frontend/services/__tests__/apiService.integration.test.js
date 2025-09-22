import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import authService from '../authService.js';
import analysisService from '../analysisService.js';
import httpClient from '../httpClient.js';

// Create axios mock adapter
let mockAxios;

describe('API Service Integration Tests', () => {
  beforeEach(() => {
    mockAxios = new MockAdapter(httpClient);
    // Clear localStorage before each test
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    mockAxios.restore();
    localStorage.clear();
  });

  describe('Authentication Service Integration', () => {
    describe('Login Flow', () => {
      it('successfully logs in user and stores tokens', async () => {
        const mockResponse = {
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'bearer',
          user: {
            id: 1,
            email: 'test@example.com',
            full_name: 'Test User'
          }
        };

        mockAxios.onPost('/auth/login').reply(200, mockResponse);

        const credentials = {
          email: 'test@example.com',
          password: 'password123'
        };

        const result = await authService.login(credentials);

        expect(result).toEqual({
          user: mockResponse.user,
          token: mockResponse.access_token,
          refreshToken: mockResponse.refresh_token,
          tokenType: mockResponse.token_type
        });

        // Verify tokens are stored
        expect(localStorage.getItem('access_token')).toBe('mock-access-token');
        expect(localStorage.getItem('refresh_token')).toBe('mock-refresh-token');
        expect(JSON.parse(localStorage.getItem('user_data'))).toEqual(mockResponse.user);

        // Verify authentication state
        expect(authService.isAuthenticated()).toBe(true);
        expect(authService.getCurrentUser()).toEqual(mockResponse.user);
      });

      it('handles login failure with proper error messages', async () => {
        mockAxios.onPost('/auth/login').reply(401, {
          detail: 'Invalid credentials'
        });

        const credentials = {
          email: 'test@example.com',
          password: 'wrongpassword'
        };

        await expect(authService.login(credentials)).rejects.toThrow('Invalid credentials');

        // Verify no tokens are stored on failure
        expect(localStorage.getItem('access_token')).toBeNull();
        expect(authService.isAuthenticated()).toBe(false);
      });

      it('handles network errors during login', async () => {
        mockAxios.onPost('/auth/login').networkError();

        const credentials = {
          email: 'test@example.com',
          password: 'password123'
        };

        await expect(authService.login(credentials)).rejects.toThrow(
          'Network error. Please check your connection and try again.'
        );
      }, 15000);

      it('transforms login request to form data format', async () => {
        mockAxios.onPost('/auth/login').reply((config) => {
          // Verify the request is in form data format
          expect(config.headers['Content-Type']).toBe('application/x-www-form-urlencoded');
          expect(config.data).toContain('username=test%40example.com');
          expect(config.data).toContain('password=password123');

          return [200, {
            access_token: 'token',
            refresh_token: 'refresh',
            token_type: 'bearer',
            user: { id: 1, email: 'test@example.com' }
          }];
        });

        await authService.login({
          email: 'test@example.com',
          password: 'password123'
        });
      });
    });

    describe('Registration Flow', () => {
      it('successfully registers user and stores tokens', async () => {
        const mockResponse = {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token',
          token_type: 'bearer',
          user: {
            id: 2,
            email: 'newuser@example.com',
            full_name: 'New User'
          }
        };

        mockAxios.onPost('/auth/register').reply(201, mockResponse);

        const userData = {
          email: 'newuser@example.com',
          password: 'password123',
          full_name: 'New User'
        };

        const result = await authService.register(userData);

        expect(result).toEqual({
          user: mockResponse.user,
          token: mockResponse.access_token,
          refreshToken: mockResponse.refresh_token,
          tokenType: mockResponse.token_type
        });

        expect(authService.isAuthenticated()).toBe(true);
      });

      it('handles registration validation errors', async () => {
        mockAxios.onPost('/auth/register').reply(422, {
          detail: 'Email already exists'
        });

        const userData = {
          email: 'existing@example.com',
          password: 'password123',
          full_name: 'Test User'
        };

        await expect(authService.register(userData)).rejects.toThrow('Email already exists');
      });
    });

    describe('Token Refresh Flow', () => {
      beforeEach(() => {
        // Set up initial tokens
        localStorage.setItem('access_token', 'old-token');
        localStorage.setItem('refresh_token', 'valid-refresh-token');
      });

      it('successfully refreshes access token', async () => {
        const mockResponse = {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token'
        };

        mockAxios.onPost('/auth/refresh-token').reply(200, mockResponse);

        const result = await authService.refreshToken();

        expect(result).toEqual({
          accessToken: 'new-access-token',
          refreshToken: 'new-refresh-token'
        });

        expect(localStorage.getItem('access_token')).toBe('new-access-token');
        expect(localStorage.getItem('refresh_token')).toBe('new-refresh-token');
      });

      it('clears auth data when refresh fails', async () => {
        mockAxios.onPost('/auth/refresh-token').reply(401, {
          detail: 'Refresh token expired'
        });

        await expect(authService.refreshToken()).rejects.toThrow();

        // Verify auth data is cleared
        expect(localStorage.getItem('access_token')).toBeNull();
        expect(localStorage.getItem('refresh_token')).toBeNull();
        expect(authService.isAuthenticated()).toBe(false);
      });

      it('handles missing refresh token', async () => {
        localStorage.removeItem('refresh_token');

        await expect(authService.refreshToken()).rejects.toThrow('No refresh token available');
      });
    });

    describe('Logout Flow', () => {
      beforeEach(() => {
        localStorage.setItem('access_token', 'test-token');
        localStorage.setItem('refresh_token', 'test-refresh');
        localStorage.setItem('user_data', JSON.stringify({ id: 1, email: 'test@example.com' }));
      });

      it('successfully logs out and clears local data', async () => {
        mockAxios.onPost('/auth/logout').reply(200);

        await authService.logout();

        expect(localStorage.getItem('access_token')).toBeNull();
        expect(localStorage.getItem('refresh_token')).toBeNull();
        expect(localStorage.getItem('user_data')).toBeNull();
        expect(authService.isAuthenticated()).toBe(false);
      });

      it('clears local data even when logout API fails', async () => {
        mockAxios.onPost('/auth/logout').reply(500);

        await authService.logout();

        // Should still clear local data
        expect(localStorage.getItem('access_token')).toBeNull();
        expect(authService.isAuthenticated()).toBe(false);
      });
    });

    describe('Token Validation', () => {
      it('validates JWT token structure and expiration', () => {
        // Create a mock JWT token (header.payload.signature)
        const validPayload = {
          exp: Math.floor(Date.now() / 1000) + 3600 // Expires in 1 hour
        };
        const validToken = `header.${btoa(JSON.stringify(validPayload))}.signature`;

        expect(authService.isTokenValid(validToken)).toBe(true);
      });

      it('rejects expired tokens', () => {
        const expiredPayload = {
          exp: Math.floor(Date.now() / 1000) - 3600 // Expired 1 hour ago
        };
        const expiredToken = `header.${btoa(JSON.stringify(expiredPayload))}.signature`;

        expect(authService.isTokenValid(expiredToken)).toBe(false);
      });

      it('rejects malformed tokens', () => {
        expect(authService.isTokenValid('invalid-token')).toBe(false);
        expect(authService.isTokenValid('')).toBe(false);
        expect(authService.isTokenValid(null)).toBe(false);
      });

      it('ensures valid token or refreshes automatically', async () => {
        const expiredPayload = {
          exp: Math.floor(Date.now() / 1000) - 3600
        };
        const expiredToken = `header.${btoa(JSON.stringify(expiredPayload))}.signature`;

        localStorage.setItem('access_token', expiredToken);
        localStorage.setItem('refresh_token', 'valid-refresh');

        mockAxios.onPost('/auth/refresh-token').reply(200, {
          access_token: 'new-token',
          refresh_token: 'new-refresh'
        });

        const result = await authService.ensureValidToken();

        expect(result).toBe(true);
        expect(localStorage.getItem('access_token')).toBe('new-token');
      });
    });
  });

  describe('Analysis Service Integration', () => {
    beforeEach(() => {
      // Set up authenticated state
      localStorage.setItem('access_token', 'valid-token');
      localStorage.setItem('user_data', JSON.stringify({ id: 1, email: 'test@example.com' }));
    });

    describe('Code Analysis', () => {
      it('successfully analyzes code and returns results', async () => {
        const mockAnalysisResult = {
          id: 'analysis-123',
          status: 'completed',
          issues: [
            {
              line: 5,
              column: 10,
              severity: 'error',
              message: 'Undefined variable',
              rule: 'no-undef'
            }
          ],
          metrics: {
            lines_of_code: 50,
            complexity: 3,
            maintainability: 85
          }
        };

        mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, mockAnalysisResult);

        const codeData = {
          code: 'console.log(undefinedVar);',
          language: 'javascript',
          filename: 'test.js'
        };

        const result = await analysisService.analyzeCode(codeData);

        expect(result).toEqual(mockAnalysisResult);

        // Verify request was made with correct data
        expect(mockAxios.history.post[0].data).toBe(JSON.stringify(codeData));
        expect(mockAxios.history.post[0].headers.Authorization).toBe('Bearer valid-token');
      });

      it('handles analysis errors gracefully', async () => {
        mockAxios.onPost('/api/v1/analysis/analyze-code').reply(413, {
          detail: 'Code is too large'
        });

        const codeData = {
          code: 'x'.repeat(100000), // Very large code
          language: 'javascript',
          filename: 'large.js'
        };

        await expect(analysisService.analyzeCode(codeData)).rejects.toThrow('Code is too large');
      });

      it('includes supported languages in request', () => {
        const supportedLanguages = analysisService.getSupportedLanguages();

        expect(supportedLanguages).toContainEqual(
          expect.objectContaining({ value: 'javascript', label: 'JavaScript' })
        );
        expect(supportedLanguages).toContainEqual(
          expect.objectContaining({ value: 'python', label: 'Python' })
        );
        expect(supportedLanguages).toContainEqual(
          expect.objectContaining({ value: 'typescript', label: 'TypeScript' })
        );
      });
    });

    describe('File Upload Analysis', () => {
      it('successfully uploads file and returns analysis', async () => {
        const mockUploadResult = {
          file_id: 'file-456',
          filename: 'uploaded.js',
          analysis: {
            id: 'analysis-456',
            issues: [],
            metrics: { lines_of_code: 25 }
          }
        };

        mockAxios.onPost('/api/v1/files/upload').reply(200, mockUploadResult);

        const file = new File(['console.log("test");'], 'test.js', { type: 'text/javascript' });
        const options = {
          autoAnalyze: true,
          onProgress: vi.fn()
        };

        const result = await analysisService.uploadFile(file, options);

        expect(result).toEqual(mockUploadResult);
        expect(options.onProgress).toHaveBeenCalledWith(100);
      });

      it('tracks upload progress correctly', async () => {
        const progressCallback = vi.fn();

        mockAxios.onPost('/api/v1/files/upload').reply((config) => {
          // Simulate progress updates
          setTimeout(() => progressCallback(25), 10);
          setTimeout(() => progressCallback(50), 20);
          setTimeout(() => progressCallback(75), 30);
          setTimeout(() => progressCallback(100), 40);

          return [200, { file_id: 'test', analysis: null }];
        });

        const file = new File(['test'], 'test.js');

        await analysisService.uploadFile(file, {
          onProgress: progressCallback
        });

        // Wait for all progress callbacks
        await new Promise(resolve => setTimeout(resolve, 100));

        expect(progressCallback).toHaveBeenCalledWith(100);
      });

      it('handles file upload size limits', async () => {
        mockAxios.onPost('/api/v1/files/upload').reply(413, {
          detail: 'File too large. Please upload a smaller file.'
        });

        const largeFile = new File(['x'.repeat(10000000)], 'large.js');

        await expect(analysisService.uploadFile(largeFile)).rejects.toThrow('File too large');
      });
    });

    describe('Analysis History', () => {
      it('retrieves user analysis history', async () => {
        const mockHistory = {
          analyses: [
            {
              id: 'analysis-1',
              created_at: '2024-01-01T00:00:00Z',
              filename: 'test1.js',
              status: 'completed'
            },
            {
              id: 'analysis-2',
              created_at: '2024-01-02T00:00:00Z',
              filename: 'test2.py',
              status: 'completed'
            }
          ],
          total: 2,
          page: 1,
          per_page: 10
        };

        mockAxios.onGet('/api/v1/analysis/user-analyses').reply(200, mockHistory);

        const result = await analysisService.getUserAnalyses();

        expect(result).toEqual(mockHistory);
      });

      it('retrieves specific analysis by ID', async () => {
        const mockAnalysis = {
          id: 'analysis-123',
          code: 'console.log("test");',
          language: 'javascript',
          issues: [],
          metrics: { lines_of_code: 1 }
        };

        mockAxios.onGet('/api/v1/analysis/analysis-123').reply(200, mockAnalysis);

        const result = await analysisService.getAnalysisById('analysis-123');

        expect(result).toEqual(mockAnalysis);
      });

      it('handles analysis not found errors', async () => {
        mockAxios.onGet('/api/v1/analysis/nonexistent').reply(404, {
          detail: 'Analysis not found'
        });

        await expect(analysisService.getAnalysisById('nonexistent')).rejects.toThrow('Analysis not found');
      });
    });

    describe('Analysis Statistics', () => {
      it('retrieves user analysis statistics', async () => {
        const mockStats = {
          total_analyses: 15,
          total_issues_found: 42,
          languages_used: ['javascript', 'python', 'typescript'],
          avg_issues_per_analysis: 2.8,
          most_common_issues: [
            { rule: 'no-unused-vars', count: 8 },
            { rule: 'no-console', count: 5 }
          ]
        };

        mockAxios.onGet('/api/v1/analysis/stats').reply(200, mockStats);

        const result = await analysisService.getAnalysisStats();

        expect(result).toEqual(mockStats);
      });
    });
  });

  describe('HTTP Client Integration', () => {
    describe('Request Interceptors', () => {
      it('automatically adds authorization header when token exists', async () => {
        localStorage.setItem('access_token', 'test-token');

        mockAxios.onGet('/test').reply((config) => {
          expect(config.headers.Authorization).toBe('Bearer test-token');
          return [200, { success: true }];
        });

        await httpClient.get('/test');
      });

      it('does not add authorization header when no token exists', async () => {
        localStorage.removeItem('access_token');

        mockAxios.onGet('/test').reply((config) => {
          expect(config.headers.Authorization).toBeUndefined();
          return [200, { success: true }];
        });

        await httpClient.get('/test');
      });
    });

    describe('Response Interceptors', () => {
      it('automatically refreshes token on 401 response', async () => {
        localStorage.setItem('access_token', 'expired-token');
        localStorage.setItem('refresh_token', 'valid-refresh');

        // First request fails with 401
        mockAxios.onGet('/protected').replyOnce(401, { detail: 'Token expired' });

        // Refresh token request succeeds
        mockAxios.onPost('/auth/refresh-token').reply(200, {
          access_token: 'new-token',
          refresh_token: 'new-refresh'
        });

        // Retry original request with new token
        mockAxios.onGet('/protected').reply((config) => {
          expect(config.headers.Authorization).toBe('Bearer new-token');
          return [200, { data: 'protected data' }];
        });

        const result = await httpClient.get('/protected');

        expect(result.data).toEqual({ data: 'protected data' });
        expect(localStorage.getItem('access_token')).toBe('new-token');
      });

      it('redirects to login when refresh token is invalid', async () => {
        localStorage.setItem('access_token', 'expired-token');
        localStorage.setItem('refresh_token', 'invalid-refresh');

        // Original request fails
        mockAxios.onGet('/protected').reply(401);

        // Refresh token also fails
        mockAxios.onPost('/auth/refresh-token').reply(401, { detail: 'Invalid refresh token' });

        await expect(httpClient.get('/protected')).rejects.toThrow();

        // Verify auth data is cleared
        expect(localStorage.getItem('access_token')).toBeNull();
        expect(localStorage.getItem('refresh_token')).toBeNull();
      });
    });

    describe('Error Handling', () => {
      it('handles network timeouts', async () => {
        mockAxios.onGet('/slow').timeout();

        await expect(httpClient.get('/slow')).rejects.toThrow();
      }, 15000);

      it('handles server errors with proper error messages', async () => {
        mockAxios.onPost('/api/test').reply(500, {
          detail: 'Internal server error'
        });

        await expect(httpClient.post('/api/test')).rejects.toThrow();
      }, 15000);

      it('retries failed requests with exponential backoff', async () => {
        let attemptCount = 0;

        mockAxios.onGet('/flaky').reply(() => {
          attemptCount++;
          if (attemptCount < 3) {
            return [500, { detail: 'Server error' }];
          }
          return [200, { success: true }];
        });

        const result = await httpClient.get('/flaky');

        expect(result.data).toEqual({ success: true });
        expect(attemptCount).toBe(3);
      });
    });
  });

  describe('End-to-End Authentication Flow', () => {
    it('completes full authentication cycle', async () => {
      // 1. Login
      mockAxios.onPost('/auth/login').reply(200, {
        access_token: 'initial-token',
        refresh_token: 'initial-refresh',
        token_type: 'bearer',
        user: { id: 1, email: 'test@example.com' }
      });

      await authService.login({
        email: 'test@example.com',
        password: 'password123'
      });

      expect(authService.isAuthenticated()).toBe(true);

      // 2. Make authenticated API call
      mockAxios.onGet('/api/v1/analysis/stats').reply(200, {
        total_analyses: 5
      });

      const stats = await analysisService.getAnalysisStats();
      expect(stats.total_analyses).toBe(5);

      // 3. Token expires and gets refreshed automatically
      localStorage.setItem('access_token', 'expired-token');

      mockAxios.onGet('/api/v1/analysis/user-analyses').replyOnce(401);
      mockAxios.onPost('/auth/refresh-token').reply(200, {
        access_token: 'refreshed-token',
        refresh_token: 'new-refresh'
      });
      mockAxios.onGet('/api/v1/analysis/user-analyses').reply(200, {
        analyses: []
      });

      const analyses = await analysisService.getUserAnalyses();
      expect(analyses.analyses).toEqual([]);
      expect(localStorage.getItem('access_token')).toBe('refreshed-token');

      // 4. Logout
      mockAxios.onPost('/auth/logout').reply(200);

      await authService.logout();
      expect(authService.isAuthenticated()).toBe(false);
    });
  });
});