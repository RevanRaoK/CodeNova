import api from './api';

// Types for authentication
export interface LoginCredentials {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface SignupData {
  email: string;
  password: string;
  full_name: string;
  confirm_password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'USER' | 'ADMIN';
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

class AuthService {
  /**
   * Login user with email and password
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response = await api.post('/auth/login', {
        username: credentials.email, // Backend expects 'username' field
        password: credentials.password,
      });

      const { access_token, refresh_token, token_type, user } = response.data;

      // Store tokens in localStorage
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // Store user data
      localStorage.setItem('user', JSON.stringify(user));

      return {
        user,
        tokens: {
          access_token,
          refresh_token,
          token_type,
        },
      };
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  }

  /**
   * Register new user
   */
  async signup(signupData: SignupData): Promise<AuthResponse> {
    try {
      // Validate password confirmation
      if (signupData.password !== signupData.confirm_password) {
        throw new Error('Passwords do not match');
      }

      const response = await api.post('/auth/register', {
        email: signupData.email,
        password: signupData.password,
        full_name: signupData.full_name,
      });

      const { access_token, refresh_token, token_type, user } = response.data;

      // Store tokens in localStorage
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // Store user data
      localStorage.setItem('user', JSON.stringify(user));

      return {
        user,
        tokens: {
          access_token,
          refresh_token,
          token_type,
        },
      };
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  }

  /**
   * Logout user and clear stored data
   */
  async logout(): Promise<void> {
    try {
      // Call logout endpoint to invalidate tokens on server
      await api.post('/auth/logout');
    } catch (error) {
      // Continue with logout even if server call fails
      console.warn('Logout API call failed:', error);
    } finally {
      // Clear all stored auth data
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(): Promise<string> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await api.post('/auth/refresh', {
        refresh_token: refreshToken,
      });

      const { access_token } = response.data;
      localStorage.setItem('access_token', access_token);

      return access_token;
    } catch (error: any) {
      // Clear tokens if refresh fails
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      throw new Error(error.response?.data?.detail || 'Token refresh failed');
    }
  }

  /**
   * Get current user from localStorage
   */
  getCurrentUser(): User | null {
    try {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('Error parsing user data:', error);
      return null;
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token');
    const user = this.getCurrentUser();
    return !!(token && user);
  }

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  /**
   * Get refresh token
   */
  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  /**
   * Clear all authentication data
   */
  clearAuthData(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService;
