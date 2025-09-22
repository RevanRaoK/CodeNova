import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import { AuthProvider, useAuth } from '../AuthContext';
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

// Mock authService to avoid circular dependencies
vi.mock('../../services/authService', () => ({
  default: {
    getCurrentUser: vi.fn(() => null),
    getToken: vi.fn(() => null),
    isAuthenticated: vi.fn(() => false),
    ensureValidToken: vi.fn(() => Promise.resolve(false)),
    clearAuthData: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn()
  }
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
    mockAxios.onPost('/auth/login').reply(200, mockAuthResponses.loginSuccess);
    mockAxios.onPost('/auth/register').reply(201, mockAuthResponses.registerSuccess);
    mockAxios.onPost('/auth/logout').reply(200, mockAuthResponses.logoutSuccess);
    mockAxios.onPost('/auth/refresh-token').reply(200, mockAuthResponses.refreshSuccess);
  });

  afterEach(() => {
    mockAxios.restore();
    localStorage.clear();
  });

  describe('Initial State', () => {
    it('initializes with unauthenticated state', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initialization to complete
      await waitFor(() => {
        expect(result.current).toBeTruthy();
        expect(result.current.isLoading).toBe(false);
      }, { timeout: 5000 });

      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('restores authenticated state from localStorage', async () => {
      // Setup localStorage with valid auth data
      localStorage.setItem('access_token', mockTokens.validToken);
      localStorage.setItem('refresh_token', mockTokens.refreshToken);
      localStorage.setItem('user_data', JSON.stringify(mockUsers.validUser));

      // Mock authService methods for this test
      const authService = await import('../../services/authService');
      authService.default.getCurrentUser.mockReturnValue(mockUsers.validUser);
      authService.default.getToken.mockReturnValue(mockTokens.validToken);
      authService.default.isAuthenticated.mockReturnValue(true);
      authService.default.ensureValidToken.mockResolvedValue(true);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      }, { timeout: 5000 });

      expect(result.current.user).toEqual(mockUsers.validUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('clears invalid auth data on initialization', async () => {
      // Setup localStorage with expired token
      localStorage.setItem('access_token', mockTokens.expiredToken);
      localStorage.setItem('user_data', JSON.stringify(mockUsers.validUser));

      // Mock authService methods for this test
      const authService = await import('../../services/authService');
      authService.default.getCurrentUser.mockReturnValue(mockUsers.validUser);
      authService.default.getToken.mockReturnValue(mockTokens.expiredToken);
      authService.default.isAuthenticated.mockReturnValue(true);
      authService.default.ensureValidToken.mockResolvedValue(false);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      }, { timeout: 5000 });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Login', () => {
    it('successfully logs in user', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      }, { timeout: 5000 });

      // Mock successful login
      const authService = await import('../../services/authService');
      authService.default.login.mockResolvedValue({
        user: mockUsers.validUser,
        token: mockTokens.validToken,
        refreshToken: mockTokens.refreshToken,
        tokenType: 'bearer'
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
      expect(mockNotification.showSuccess).toHaveBeenCalledWith(
        expect.stringContaining('Welcome back')
      );
    });

    it('handles login failure', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      }, { timeout: 5000 });

      // Mock failed login
      const authService = await import('../../services/authService');
      authService.default.login.mockRejectedValue(new Error('Invalid credentials'));

      await act(async () => {
        await expect(result.current.login({
          email: 'test@example.com',
          password: 'wrongpassword'
        })).rejects.toThrow('Invalid credentials');
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(mockNotification.showError).toHaveBeenCalledWith(
        expect.stringContaining('Invalid credentials')
      );
    });

    it('handles network errors during login', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      }, { timeout: 5000 });

      // Mock network error
      const authService = await import('../../services/authService');
      authService.default.login.mockRejectedValue(new Error('Network error'));

      await act(async () => {
        await expect(result.current.login({
          email: 'test@example.com',
          password: 'password123'
        })).rejects.toThrow('Network error');
      });

      expect(mockNotification.showError).toHaveBeenCalled();
    });

    it('sets loading state during login', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      }, { timeout: 5000 });

      // Mock delayed login
      const authService = await import('../../services/authService');
      let resolveLogin;
      authService.default.login.mockImplementation(() => {
        return new Promise(resolve => {
          resolveLogin = () => resolve({
            user: mockUsers.validUser,
            token: mockTokens.validToken,
            refreshToken: mockTokens.refreshToken,
            tokenType: 'bearer'
          });
        });
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
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      }, { timeout: 5000 });

      // Mock successful registration
      const authService = await import('../../services/authService');
      authService.default.register.mockResolvedValue({
        user: { ...mockUsers.validUser, email: 'newuser@example.com' },
        token: mockTokens.validToken,
        refreshToken: mockTokens.refreshToken,
        tokenType: 'bearer'
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
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      }, { timeout: 5000 });

      // Mock failed registration
      const authService = await import('../../services/authService');
      authService.default.register.mockRejectedValue(new Error('Email already exists'));

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
      const authService = await import('../../services/authService');
      authService.default.getCurrentUser.mockReturnValue(mockUsers.validUser);
      authService.default.getToken.mockReturnValue(mockTokens.validToken);
      authService.default.isAuthenticated.mockReturnValue(true);
      authService.default.ensureValidToken.mockResolvedValue(true);
      authService.default.logout.mockResolvedValue();

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial auth check to complete
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      }, { timeout: 5000 });

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(mockNotification.showSuccess).toHaveBeenCalledWith(
        expect.stringContaining('logged out successfully')
      );
    });

    it('clears local data even when logout API fails', async () => {
      // Setup authenticated state
      const authService = await import('../../services/authService');
      authService.default.getCurrentUser.mockReturnValue(mockUsers.validUser);
      authService.default.getToken.mockReturnValue(mockTokens.validToken);
      authService.default.isAuthenticated.mockReturnValue(true);
      authService.default.ensureValidToken.mockResolvedValue(true);
      authService.default.logout.mockRejectedValue(new Error('Server error'));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      }, { timeout: 5000 });

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(mockNotification.showWarning).toHaveBeenCalledWith(
        expect.stringContaining('completed with some issues')
      );
    });
  });

  describe('Token Refresh', () => {
    it('successfully refreshes token', async () => {
      // Setup authenticated state
      const authService = await import('../../services/authService');
      authService.default.getCurrentUser.mockReturnValue(mockUsers.validUser);
      authService.default.getToken.mockReturnValue(mockTokens.validToken);
      authService.default.isAuthenticated.mockReturnValue(true);
      authService.default.ensureValidToken.mockResolvedValue(true);
      authService.default.refreshToken.mockResolvedValue({
        accessToken: 'new-access-token',
        refreshToken: 'new-refresh-token'
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial auth check
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      }, { timeout: 5000 });

      await act(async () => {
        const refreshResult = await result.current.refreshToken();
        expect(refreshResult.accessToken).toBe('new-access-token');
      });

      expect(result.current.token).toBe('new-access-token');
    });

    it('clears auth data when refresh fails', async () => {
      // Setup authenticated state
      const authService = await import('../../services/authService');
      authService.default.getCurrentUser.mockReturnValue(mockUsers.validUser);
      authService.default.getToken.mockReturnValue(mockTokens.validToken);
      authService.default.isAuthenticated.mockReturnValue(true);
      authService.default.ensureValidToken.mockResolvedValue(true);
      authService.default.refreshToken.mockRejectedValue(new Error('Refresh failed'));

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial auth check
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      }, { timeout: 5000 });

      await act(async () => {
        await expect(result.current.refreshToken()).rejects.toThrow();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
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
        const { result } = renderHook(() => useAuth(), { wrapper });

        // Wait for initial loading to complete
        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        }, { timeout: 5000 });

        // Mock error for this specific case
        const authService = await import('../../services/authService');
        authService.default.login.mockRejectedValue(new Error(expectedMessage));

        await act(async () => {
          await expect(result.current.login({
            email: 'test@example.com',
            password: 'password123'
          })).rejects.toThrow(expectedMessage);
        });
      }
    });

    it('handles malformed error responses', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      }, { timeout: 5000 });

      // Mock malformed error
      const authService = await import('../../services/authService');
      authService.default.login.mockRejectedValue(new Error('Malformed response'));

      await act(async () => {
        await expect(result.current.login({
          email: 'test@example.com',
          password: 'password123'
        })).rejects.toThrow();
      });
    });
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
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      }, { timeout: 5000 });

      // Mock successful login
      const authService = await import('../../services/authService');
      authService.default.login.mockResolvedValue({
        user: mockUsers.validUser,
        token: mockTokens.validToken,
        refreshToken: mockTokens.refreshToken,
        tokenType: 'bearer'
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
      const authService = await import('../../services/authService');
      authService.default.getCurrentUser.mockReturnValue(mockUsers.validUser);
      authService.default.getToken.mockReturnValue(mockTokens.validToken);
      authService.default.isAuthenticated.mockReturnValue(true);
      authService.default.ensureValidToken.mockResolvedValue(true);
      authService.default.logout.mockResolvedValue();
      authService.default.login.mockResolvedValue({
        user: mockUsers.validUser,
        token: mockTokens.validToken,
        refreshToken: mockTokens.refreshToken,
        tokenType: 'bearer'
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      }, { timeout: 5000 });

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
    });
  });

  describe('Memory Leaks and Cleanup', () => {
    it('cleans up properly when component unmounts', async () => {
      // Mock successful login
      const authService = await import('../../services/authService');
      authService.default.login.mockResolvedValue({
        user: mockUsers.validUser,
        token: mockTokens.validToken,
        refreshToken: mockTokens.refreshToken,
        tokenType: 'bearer'
      });

      const { result, unmount } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      }, { timeout: 5000 });

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