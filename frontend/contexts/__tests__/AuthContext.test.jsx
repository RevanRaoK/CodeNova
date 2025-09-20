import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import { AuthProvider, useAuth } from '../AuthContext';
import { NotificationProvider } from '../NotificationContext';
import httpClient from '../../services/httpClient';
import { mockAuthResponses, mockUsers, mockTokens } from '../../__tests__/utils/mockApiResponses';

// Mock the notification context
const mockNotification = {
  showSuccess: vi.fn(),
  showError: vi.fn(),
  showWarning: vi.fn()
};

// Mock the NotificationContext at the module level
vi.mock('../NotificationContext', () => ({
  NotificationProvider: ({ children }) => children,
  useNotification: () => mockNotification
}));

describe('AuthContext', () => {
  let mockAxios;

  const wrapper = ({ children }) => (
    <AuthProvider>
      {children}
    </AuthProvider>
  );

  beforeEach(() => {
    mockAxios = new MockAdapter(httpClient);
    localStorage.clear();
    vi.clearAllMocks();
    
    // Setup default mock responses for common endpoints
    mockAxios.onPost('/auth/login').reply(404);
    mockAxios.onPost('/auth/register').reply(404);
    mockAxios.onPost('/auth/logout').reply(404);
    mockAxios.onPost('/auth/refresh').reply(404);
  });

  afterEach(() => {
    mockAxios.restore();
    localStorage.clear();
  });

  describe('Initial State', () => {
    it('initializes with unauthenticated state', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Initially loading
      expect(result.current.isLoading).toBe(true);

      // Wait for initialization to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('restores authenticated state from localStorage', async () => {
      // Setup localStorage with valid auth data
      localStorage.setItem('access_token', mockTokens.validToken);
      localStorage.setItem('refresh_token', mockTokens.refreshToken);
      localStorage.setItem('user_data', JSON.stringify(mockUsers.validUser));

      // Mock token validation endpoint - return success to indicate token is still valid
      mockAxios.onPost('/auth/refresh').reply(200, mockAuthResponses.refreshSuccess);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user).toEqual(mockUsers.validUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('clears invalid auth data on initialization', async () => {
      // Setup localStorage with expired token
      localStorage.setItem('access_token', mockTokens.expiredToken);
      localStorage.setItem('user_data', JSON.stringify(mockUsers.validUser));

      // Mock failed token validation
      mockAxios.onPost('/auth/refresh').reply(401, mockAuthResponses.refreshFailure);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorage.getItem('access_token')).toBeNull();
    });
  });

  describe('Login', () => {
    it('successfully logs in user', async () => {
      mockAxios.reset();
      mockAxios.onPost('/auth/login').reply(200, mockAuthResponses.loginSuccess);

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        const loginResult = await result.current.login({
          email: 'test@example.com',
          password: 'password123'
        });

        expect(loginResult).toEqual({
          user: mockUsers.validUser,
          token: mockTokens.validToken,
          refreshToken: mockTokens.refreshToken,
          tokenType: 'bearer'
        });
      });

      expect(result.current.user).toEqual(mockUsers.validUser);
      expect(result.current.token).toBe(mockTokens.validToken);
      expect(result.current.isAuthenticated).toBe(true);
      expect(localStorage.getItem('access_token')).toBe(mockTokens.validToken);
      expect(mockNotification.showSuccess).toHaveBeenCalledWith(
        expect.stringContaining('Welcome back')
      );
    });

    it('handles login failure', async () => {
      mockAxios.reset();
      mockAxios.onPost('/auth/login').reply(401, mockAuthResponses.loginFailure);

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await expect(result.current.login({
          email: 'test@example.com',
          password: 'wrongpassword'
        })).rejects.toThrow('Invalid credentials');
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(mockNotification.showError).toHaveBeenCalledWith(
        expect.stringContaining('Invalid credentials')
      );
    });

    it('handles network errors during login', async () => {
      mockAxios.reset();
      mockAxios.onPost('/auth/login').networkError();

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await expect(result.current.login({
          email: 'test@example.com',
          password: 'password123'
        })).rejects.toThrow('Network error');
      });

      expect(mockNotification.showError).toHaveBeenCalled();
    }, 10000);

    it('sets loading state during login', async () => {
      mockAxios.reset();
      let resolveLogin;
      mockAxios.onPost('/auth/login').reply(() => {
        return new Promise(resolve => {
          resolveLogin = () => resolve([200, mockAuthResponses.loginSuccess]);
        });
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Start login
      let loginPromise;
      act(() => {
        loginPromise = result.current.login({
          email: 'test@example.com',
          password: 'password123'
        });
      });

      // Should be loading
      expect(result.current.isLoading).toBe(true);

      // Complete login
      await act(async () => {
        resolveLogin();
        await loginPromise;
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('Registration', () => {
    it('successfully registers user', async () => {
      mockAxios.reset();
      mockAxios.onPost('/auth/register').reply(201, mockAuthResponses.registerSuccess);

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        const registerResult = await result.current.register({
          email: 'newuser@example.com',
          password: 'password123',
          full_name: 'New User'
        });

        expect(registerResult.user.email).toBe('newuser@example.com');
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(mockNotification.showSuccess).toHaveBeenCalledWith(
        expect.stringContaining('Account created successfully')
      );
    });

    it('handles registration failure', async () => {
      mockAxios.reset();
      mockAxios.onPost('/auth/register').reply(422, mockAuthResponses.registerFailure);

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await expect(result.current.register({
          email: 'existing@example.com',
          password: 'password123',
          full_name: 'Test User'
        })).rejects.toThrow('Email already exists');
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(mockNotification.showError).toHaveBeenCalledWith(
        expect.stringContaining('Email already exists')
      );
    });
  });

  describe('Logout', () => {
    it('successfully logs out user', async () => {
      // Setup authenticated state
      localStorage.setItem('access_token', mockTokens.validToken);
      localStorage.setItem('refresh_token', mockTokens.refreshToken);
      localStorage.setItem('user_data', JSON.stringify(mockUsers.validUser));

      mockAxios.reset();
      mockAxios.onPost('/auth/logout').reply(200, mockAuthResponses.logoutSuccess);

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial auth check to complete and user to be authenticated
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      }, { timeout: 3000 });

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(mockNotification.showSuccess).toHaveBeenCalledWith(
        expect.stringContaining('logged out successfully')
      );
    });

    it('clears local data even when logout API fails', async () => {
      // Setup authenticated state
      localStorage.setItem('access_token', mockTokens.validToken);
      localStorage.setItem('refresh_token', mockTokens.refreshToken);
      localStorage.setItem('user_data', JSON.stringify(mockUsers.validUser));

      mockAxios.reset();
      mockAxios.onPost('/auth/logout').reply(500);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      }, { timeout: 3000 });

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(mockNotification.showWarning).toHaveBeenCalledWith(
        expect.stringContaining('completed with some issues')
      );
    });
  });

  describe('Token Refresh', () => {
    it('successfully refreshes token', async () => {
      localStorage.setItem('access_token', mockTokens.validToken);
      localStorage.setItem('refresh_token', mockTokens.refreshToken);
      localStorage.setItem('user_data', JSON.stringify(mockUsers.validUser));

      mockAxios.reset();
      mockAxios.onPost('/auth/refresh').reply(200, mockAuthResponses.refreshSuccess);

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial auth check
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      await act(async () => {
        const refreshResult = await result.current.refreshToken();
        expect(refreshResult.accessToken).toBe('new-access-token');
      });

      expect(result.current.token).toBe('new-access-token');
      expect(localStorage.getItem('access_token')).toBe('new-access-token');
    });

    it('clears auth data when refresh fails', async () => {
      localStorage.setItem('access_token', mockTokens.validToken);
      localStorage.setItem('refresh_token', mockTokens.refreshToken);
      localStorage.setItem('user_data', JSON.stringify(mockUsers.validUser));

      mockAxios.reset();
      mockAxios.onPost('/auth/refresh').reply(401, mockAuthResponses.refreshFailure);

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial auth check
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      await act(async () => {
        await expect(result.current.refreshToken()).rejects.toThrow();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(mockNotification.showWarning).toHaveBeenCalledWith(
        expect.stringContaining('session has expired')
      );
    });
  });

  describe('Error Handling', () => {
    it('handles different HTTP error codes appropriately', async () => {
      const errorCases = [
        { status: 400, expectedMessage: 'Invalid request' },
        { status: 401, expectedMessage: 'Invalid credentials' },
        { status: 403, expectedMessage: 'Access forbidden' },
        { status: 422, expectedMessage: 'Validation error' },
        { status: 429, expectedMessage: 'Too many requests' },
        { status: 500, expectedMessage: 'Server error' }
      ];

      for (const { status, expectedMessage } of errorCases) {
        mockAxios.reset();
        mockAxios.onPost('/auth/login').reply(status, { detail: expectedMessage });

        const { result } = renderHook(() => useAuth(), { wrapper });

        // Wait for initial loading to complete
        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });

        await act(async () => {
          await expect(result.current.login({
            email: 'test@example.com',
            password: 'password123'
          })).rejects.toThrow(expectedMessage);
        });
      }
    });

    it('handles malformed error responses', async () => {
      mockAxios.reset();
      mockAxios.onPost('/auth/login').reply(500, 'Invalid JSON');

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await expect(result.current.login({
          email: 'test@example.com',
          password: 'password123'
        })).rejects.toThrow();
      });
    }, 10000);
  });

  describe('Context Provider Error Handling', () => {
    it('throws error when useAuth is used outside AuthProvider', () => {
      // Capture console.error to avoid test noise
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      expect(() => {
        renderHook(() => useAuth());
      }).toThrow('useAuth must be used within an AuthProvider');
      
      consoleSpy.mockRestore();
    });
  });

  describe('Concurrent Operations', () => {
    it('handles concurrent login attempts', async () => {
      mockAxios.reset();
      mockAxios.onPost('/auth/login').reply(200, mockAuthResponses.loginSuccess);

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const credentials = {
        email: 'test@example.com',
        password: 'password123'
      };

      await act(async () => {
        // Start multiple login attempts
        const promises = [
          result.current.login(credentials),
          result.current.login(credentials),
          result.current.login(credentials)
        ];

        const results = await Promise.all(promises);
        
        // All should succeed with same result
        results.forEach(result => {
          expect(result.user).toEqual(mockUsers.validUser);
        });
      });

      expect(result.current.isAuthenticated).toBe(true);
    });

    it('handles login during logout', async () => {
      // Setup authenticated state
      localStorage.setItem('access_token', mockTokens.validToken);
      localStorage.setItem('refresh_token', mockTokens.refreshToken);
      localStorage.setItem('user_data', JSON.stringify(mockUsers.validUser));

      mockAxios.reset();
      mockAxios.onPost('/auth/logout').reply(200);
      mockAxios.onPost('/auth/login').reply(200, mockAuthResponses.loginSuccess);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      await act(async () => {
        // Start logout and login simultaneously
        const logoutPromise = result.current.logout();
        const loginPromise = result.current.login({
          email: 'test@example.com',
          password: 'password123'
        });

        await Promise.all([logoutPromise, loginPromise]);
      });

      // Final state should be authenticated (login wins)
      expect(result.current.isAuthenticated).toBe(true);
    }, 10000);
  });

  describe('Memory Leaks and Cleanup', () => {
    it('cleans up properly when component unmounts', async () => {
      mockAxios.reset();
      mockAxios.onPost('/auth/login').reply(200, mockAuthResponses.loginSuccess);

      const { result, unmount } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.login({
          email: 'test@example.com',
          password: 'password123'
        });
      });

      // Unmount should not cause errors
      expect(() => unmount()).not.toThrow();
    });
  });
});