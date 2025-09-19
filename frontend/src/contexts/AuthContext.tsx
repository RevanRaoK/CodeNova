import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

type User = {
  id: number;
  email: string;
  name: string;
  role: string;
  isVerified: boolean;
};

type AuthTokens = {
  accessToken: string;
  refreshToken: string;
};

type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const tokens = getTokens();
        if (tokens) {
          const decoded = jwtDecode<{ sub: string; email: string; role: string }>(tokens.accessToken);
          setUser({
            id: parseInt(decoded.sub),
            email: decoded.email,
            name: '', // We'll fetch the full user profile in a real app
            role: decoded.role,
            isVerified: true, // This should come from the token or user profile
          });
          
          // Set up the API client with the access token
          api.setAccessToken(tokens.accessToken);
          
          // Schedule token refresh before it expires
          scheduleTokenRefresh();
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error);
        logout();
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const getTokens = (): AuthTokens | null => {
    const accessToken = localStorage.getItem('accessToken');
    const refreshToken = localStorage.getItem('refreshToken');
    
    if (accessToken && refreshToken) {
      return { accessToken, refreshToken };
    }
    return null;
  };

  const setTokens = (tokens: AuthTokens) => {
    localStorage.setItem('accessToken', tokens.accessToken);
    localStorage.setItem('refreshToken', tokens.refreshToken);
    api.setAccessToken(tokens.accessToken);
  };

  const clearTokens = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    api.clearAccessToken();
  };

  const scheduleTokenRefresh = useCallback(() => {
    const tokens = getTokens();
    if (!tokens) return;

    try {
      const { exp } = jwtDecode<{ exp: number }>(tokens.accessToken);
      const expiresIn = exp * 1000 - Date.now();
      const refreshThreshold = 5 * 60 * 1000; // 5 minutes before expiration
      
      // Schedule refresh 5 minutes before token expires
      const timeout = Math.max(expiresIn - refreshThreshold, 0);
      
      const refreshTimeout = setTimeout(async () => {
        const success = await refreshToken();
        if (success) {
          scheduleTokenRefresh(); // Schedule next refresh
        } else {
          logout();
        }
      }, timeout);

      return () => clearTimeout(refreshTimeout);
    } catch (error) {
      console.error('Error scheduling token refresh:', error);
      logout();
    }
  }, []);

  const refreshToken = async (): Promise<boolean> => {
    const tokens = getTokens();
    if (!tokens?.refreshToken) return false;

    try {
      const response = await api.post('/auth/refresh-token', {
        refreshToken: tokens.refreshToken,
      });

      setTokens({
        accessToken: response.data.access_token,
        refreshToken: tokens.refreshToken, // Use the same refresh token
      });

      return true;
    } catch (error) {
      console.error('Failed to refresh token:', error);
      return false;
    }
  };

  const login = async (email: string, password: string) => {
    try {
      setLoading(true);
      const response = await api.post('/auth/login', { email, password });
      
      const { access_token, refresh_token } = response.data;
      setTokens({ accessToken: access_token, refreshToken: refresh_token });
      
      const decoded = jwtDecode<{ sub: string; email: string; role: string }>(access_token);
      setUser({
        id: parseInt(decoded.sub),
        email: decoded.email,
        name: '', // Fetch full user profile in a real app
        role: decoded.role,
        isVerified: true,
      });
      
      scheduleTokenRefresh();
      navigate('/');
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (name: string, email: string, password: string) => {
    try {
      setLoading(true);
      await api.post('/auth/register', { name, email, password });
      // After successful signup, log the user in
      await login(email, password);
    } catch (error) {
      console.error('Signup failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    // Call the logout API if needed
    api.post('/auth/logout').catch(console.error);
    
    // Clear all auth state
    clearTokens();
    setUser(null);
    queryClient.clear();
    
    // Redirect to login
    navigate('/login');
  };

  const value = {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    signup,
    logout,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
