import httpClient from './httpClient.js';

/**
 * Authentication service for handling user login, registration, and token management
 */
class AuthService {
  constructor() {
    this.tokenKey = 'access_token';
    this.refreshTokenKey = 'refresh_token';
    this.userKey = 'user_data';
  }

  /**
   * Login user with email and password
   * @param {Object} credentials - Login credentials
   * @param {string} credentials.email - User email
   * @param {string} credentials.password - User password
   * @returns {Promise<Object>} Authentication response with user data and tokens
   */
  async login(credentials) {
    try {
      const response = await httpClient.post('/auth/login', {
        username: credentials.email, // Backend expects username field
        password: credentials.password
      }, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        transformRequest: [(data) => {
          // Transform to form data as expected by FastAPI OAuth2
          const formData = new URLSearchParams();
          formData.append('username', data.username);
          formData.append('password', data.password);
          return formData;
        }]
      });

      const { access_token, refresh_token, token_type, user } = response.data;
      
      // Store tokens and user data
      this.setToken(access_token);
      this.setRefreshToken(refresh_token);
      this.setUserData(user);

      return {
        user,
        token: access_token,
        refreshToken: refresh_token,
        tokenType: token_type
      };
    } catch (error) {
      console.error('Login failed:', error);
      throw this.handleAuthError(error);
    }
  }

  /**
   * Register new user
   * @param {Object} userData - Registration data
   * @param {string} userData.email - User email
   * @param {string} userData.password - User password
   * @param {string} userData.full_name - User full name
   * @returns {Promise<Object>} Registration response
   */
  async register(userData) {
    try {
      const response = await httpClient.post('/auth/register', {
        email: userData.email,
        password: userData.password,
        full_name: userData.full_name
      });

      const { access_token, refresh_token, token_type, user } = response.data;
      
      // Store tokens and user data
      this.setToken(access_token);
      this.setRefreshToken(refresh_token);
      this.setUserData(user);

      return {
        user,
        token: access_token,
        refreshToken: refresh_token,
        tokenType: token_type
      };
    } catch (error) {
      console.error('Registration failed:', error);
      throw this.handleAuthError(error);
    }
  }

  /**
   * Logout user and clear stored data
   * @returns {Promise<void>}
   */
  async logout() {
    try {
      // Call backend logout endpoint if token exists
      const token = this.getToken();
      if (token) {
        await httpClient.post('/auth/logout');
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with local logout even if API call fails
    } finally {
      // Always clear local storage
      this.clearAuthData();
    }
  }

  /**
   * Refresh access token using refresh token
   * @returns {Promise<Object>} New token data
   */
  async refreshToken() {
    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await httpClient.post('/auth/refresh', {
        refresh_token: refreshToken
      });

      const { access_token, refresh_token: newRefreshToken } = response.data;
      
      // Update stored tokens
      this.setToken(access_token);
      if (newRefreshToken) {
        this.setRefreshToken(newRefreshToken);
      }

      return {
        accessToken: access_token,
        refreshToken: newRefreshToken || refreshToken
      };
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Clear auth data on refresh failure
      this.clearAuthData();
      throw this.handleAuthError(error);
    }
  }

  /**
   * Get current user data
   * @returns {Object|null} User data or null if not authenticated
   */
  getCurrentUser() {
    try {
      const userData = localStorage.getItem(this.userKey);
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Error parsing user data:', error);
      return null;
    }
  }

  /**
   * Check if user is authenticated
   * @returns {boolean} True if user has valid token
   */
  isAuthenticated() {
    const token = this.getToken();
    const user = this.getCurrentUser();
    return !!(token && user);
  }

  /**
   * Get stored access token
   * @returns {string|null} Access token or null
   */
  getToken() {
    return localStorage.getItem(this.tokenKey);
  }

  /**
   * Get stored refresh token
   * @returns {string|null} Refresh token or null
   */
  getRefreshToken() {
    return localStorage.getItem(this.refreshTokenKey);
  }

  /**
   * Store access token
   * @param {string} token - Access token to store
   */
  setToken(token) {
    if (token) {
      localStorage.setItem(this.tokenKey, token);
    }
  }

  /**
   * Store refresh token
   * @param {string} token - Refresh token to store
   */
  setRefreshToken(token) {
    if (token) {
      localStorage.setItem(this.refreshTokenKey, token);
    }
  }

  /**
   * Store user data
   * @param {Object} userData - User data to store
   */
  setUserData(userData) {
    if (userData) {
      localStorage.setItem(this.userKey, JSON.stringify(userData));
    }
  }

  /**
   * Clear all authentication data from localStorage
   */
  clearAuthData() {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.refreshTokenKey);
    localStorage.removeItem(this.userKey);
  }

  /**
   * Handle authentication errors and provide user-friendly messages
   * @param {Error} error - The error to handle
   * @returns {Error} Processed error with user-friendly message
   */
  handleAuthError(error) {
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          return new Error(data.detail || 'Invalid request. Please check your input.');
        case 401:
          return new Error('Invalid credentials. Please check your email and password.');
        case 403:
          return new Error('Access forbidden. Your account may be disabled.');
        case 422:
          return new Error(data.detail || 'Validation error. Please check your input.');
        case 429:
          return new Error('Too many requests. Please try again later.');
        case 500:
          return new Error('Server error. Please try again later.');
        default:
          return new Error(data.detail || 'Authentication failed. Please try again.');
      }
    } else if (error.request) {
      return new Error('Network error. Please check your connection and try again.');
    } else {
      return new Error(error.message || 'An unexpected error occurred.');
    }
  }

  /**
   * Validate token expiration (basic check)
   * @param {string} token - JWT token to validate
   * @returns {boolean} True if token appears to be valid
   */
  isTokenValid(token) {
    if (!token) return false;
    
    try {
      // Basic JWT structure check (header.payload.signature)
      const parts = token.split('.');
      if (parts.length !== 3) return false;
      
      // Decode payload to check expiration
      const payload = JSON.parse(atob(parts[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      
      return payload.exp && payload.exp > currentTime;
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
  }

  /**
   * Auto-refresh token if it's about to expire
   * @returns {Promise<boolean>} True if token is valid or successfully refreshed
   */
  async ensureValidToken() {
    const token = this.getToken();
    
    if (!token) {
      return false;
    }
    
    if (this.isTokenValid(token)) {
      return true;
    }
    
    try {
      await this.refreshToken();
      return true;
    } catch (error) {
      console.error('Auto token refresh failed:', error);
      return false;
    }
  }
}

// Export singleton instance
const authService = new AuthService();
export default authService;