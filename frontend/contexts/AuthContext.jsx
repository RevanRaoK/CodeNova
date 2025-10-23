import React, { createContext, useContext, useState, useEffect } from 'react';
import authService from '../services/authService';
import { useNotification } from './NotificationContext';

const AuthContext = createContext();

export { AuthContext };

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Get notification functions, but handle case where NotificationProvider might not be available yet
  let showSuccess, showError, showWarning;
  try {
    const notification = useNotification();
    showSuccess = notification.showSuccess;
    showError = notification.showError;
    showWarning = notification.showWarning;
  } catch (error) {
    // NotificationProvider not available, use console fallbacks
    showSuccess = (msg) => console.log('Success:', msg);
    showError = (msg) => console.error('Error:', msg);
    showWarning = (msg) => console.warn('Warning:', msg);
  }

  useEffect(() => {
    // Check if user is already authenticated on app load
    const checkAuthStatus = async () => {
      try {
        const currentUser = authService.getCurrentUser();
        const currentToken = authService.getToken();
        const hasValidToken = authService.isAuthenticated();

        if (currentUser && hasValidToken && currentToken) {
          // Verify token is still valid
          const tokenValid = await authService.ensureValidToken();
          if (tokenValid) {
            // If preferences are not in localStorage, fetch them
            if (!currentUser.preferences && currentUser.id) {
              try {
                const userService = (await import('../services/userService')).default;
                const preferences = await userService.getUserPreferences(currentUser.id);
                currentUser.preferences = preferences;
                authService.setUserData(currentUser); // Update localStorage
              } catch (prefError) {
                console.warn('Could not load user preferences on auth check:', prefError);
              }
            }
            setUser(currentUser);
            setToken(currentToken);
            setIsAuthenticated(true);
          } else {
            // Token expired, clear auth data
            authService.clearAuthData();
            setUser(null);
            setToken(null);
            setIsAuthenticated(false);
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        authService.clearAuthData();
        setUser(null);
        setToken(null);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = async (credentials) => {
    try {
      setIsLoading(true);
      const result = await authService.login(credentials);
      
      // Fetch user preferences after login
      try {
        const userService = (await import('../services/userService')).default;
        const preferences = await userService.getUserPreferences(result.user.id);
        result.user.preferences = preferences;
      } catch (prefError) {
        console.warn('Could not load user preferences:', prefError);
        // Continue with login even if preferences fail to load
      }
      
      setUser(result.user);
      setToken(result.token);
      setIsAuthenticated(true);
      authService.setUserData(result.user); // Update localStorage with preferences
      showSuccess(`Welcome back, ${result.user.username || result.user.email}!`);
      return result;
    } catch (error) {
      setUser(null);
      setToken(null);
      setIsAuthenticated(false);
      showError(error.message || 'Login failed. Please check your credentials.');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData) => {
    try {
      setIsLoading(true);
      const result = await authService.register(userData);
      
      // Fetch user preferences after registration
      try {
        const userService = (await import('../services/userService')).default;
        const preferences = await userService.getUserPreferences(result.user.id);
        result.user.preferences = preferences;
      } catch (prefError) {
        console.warn('Could not load user preferences:', prefError);
      }
      
      setUser(result.user);
      setToken(result.token);
      setIsAuthenticated(true);
      authService.setUserData(result.user); // Update localStorage with preferences
      showSuccess('Account created successfully! Welcome to CodeNova AI.');
      return result;
    } catch (error) {
      setUser(null);
      setToken(null);
      setIsAuthenticated(false);
      showError(error.message || 'Registration failed. Please try again.');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setIsLoading(true);
      await authService.logout();
      showSuccess('You have been logged out successfully.');
    } catch (error) {
      console.error('Logout error:', error);
      showWarning('Logout completed with some issues.');
    } finally {
      setUser(null);
      setToken(null);
      setIsAuthenticated(false);
      setIsLoading(false);
    }
  };

  const refreshToken = async () => {
    try {
      const result = await authService.refreshToken();
      setToken(result.accessToken);
      return result;
    } catch (error) {
      // If refresh fails, logout user
      setUser(null);
      setToken(null);
      setIsAuthenticated(false);
      showWarning('Your session has expired. Please log in again.');
      throw error;
    }
  };

  const loginWithGoogle = async (credentialResponse) => {
    console.log('🔐 AuthContext: Starting Google login', credentialResponse);
    try {
      setIsLoading(true);
      console.log('📡 Calling authService.loginWithGoogle...');
      const result = await authService.loginWithGoogle(credentialResponse);
      console.log('✅ AuthService response:', result);

      // Fetch user preferences after login
      try {
        const userService = (await import('../services/userService')).default;
        const preferences = await userService.getUserPreferences(result.user.id);
        result.user.preferences = preferences;
      } catch (prefError) {
        console.warn('Could not load user preferences:', prefError);
      }

      setUser(result.user);
      setToken(result.token);
      setIsAuthenticated(true);
      authService.setUserData(result.user); // Update localStorage with preferences
      console.log('🎉 User state updated, showing success message');
      showSuccess(`Welcome, ${result.user.full_name || result.user.email}!`);
      return result;
    } catch (error) {
      console.error('❌ AuthContext: Google login failed:', error);
      setUser(null);
      setToken(null);
      setIsAuthenticated(false);
      showError(error.message || 'Google login failed. Please try again.');
      throw error;
    } finally {
      setIsLoading(false);
      console.log('🏁 AuthContext: Login process completed');
    }
  };

  // Method to update user data (for profile updates)
  const updateUser = (userData) => {
    setUser(prevUser => {
      const updatedUser = {
        ...prevUser,
        ...userData
      };
      // Also update localStorage so changes persist across sessions
      authService.setUserData(updatedUser);
      return updatedUser;
    });
  };

  const value = {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshToken,
    loginWithGoogle,
    setUser: updateUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};