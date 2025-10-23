import axios from 'axios';
import { env, logger } from '../utils/environment';
import { ErrorParser, RetryManager, ERROR_TYPES } from '../utils/errorHandler.js';

// Create Axios instance with base configuration
const httpClient = axios.create({
  baseURL: `${env.apiUrl}/api/v1`,
  timeout: 300000, // 5 minutes timeout for file uploads
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication
httpClient.interceptors.request.use(
  (config) => {
    // Add auth token to requests if available
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Log request for debugging
    logger.debug(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    
    return config;
  },
  (error) => {
    logger.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
httpClient.interceptors.response.use(
  (response) => {
    // Log successful response
    logger.debug(`Response received from ${response.config.url}:`, response.status);
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 Unauthorized responses with token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Attempt to refresh token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(
            `${httpClient.defaults.baseURL}/auth/refresh-token`,
            { refresh_token: refreshToken }
          );
          
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return httpClient(originalRequest);
        }
      } catch (refreshError) {
        logger.error('Token refresh failed:', refreshError);
        // Clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Create authentication error
        const authError = handleHttpError(refreshError);
        authError.context.requiresLogin = true;
        
        // Dispatch custom event for auth error handling
        window.dispatchEvent(new CustomEvent('auth-error', { detail: authError }));
        
        return Promise.reject(authError);
      }
    }
    
    // Handle rate limiting with retry-after header
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'];
      if (retryAfter) {
        const delay = parseInt(retryAfter) * 1000; // Convert to milliseconds
        logger.warn(`Rate limited. Retrying after ${delay}ms`);
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return httpClient(originalRequest);
      }
    }
    
    // Create enhanced error object
    const enhancedError = handleHttpError(error);
    
    // For retryable errors, attempt retry with exponential backoff
    if (enhancedError.retryable && !originalRequest._retryAttempt) {
      originalRequest._retryAttempt = true;
      try {
        return await retryManager.execute(
          () => httpClient(originalRequest),
          { originalError: error }
        );
      } catch (retryError) {
        // If retry fails, return the already enhanced error (don't call handleHttpError again)
        return Promise.reject(retryError);
      }
    }
    
    return Promise.reject(enhancedError);
  }
);

// Enhanced retry manager for HTTP requests
const retryManager = new RetryManager({
  maxRetries: 3,
  strategy: 'exponential',
  baseDelay: 1000,
  maxDelay: 10000,
  retryCondition: (error) => {
    // Retry on network errors, timeouts, and 5xx server errors
    if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNABORTED') {
      return true;
    }
    
    if (error.response) {
      const status = error.response.status;
      // Retry on server errors (5xx) and rate limiting (429)
      return status >= 500 || status === 429;
    }
    
    return false;
  },
  onRetry: (error, attempt, delay) => {
    logger.warn(`Retrying HTTP request (attempt ${attempt}) in ${delay}ms:`, {
      url: error.config?.url,
      method: error.config?.method,
      error: error.message
    });
  }
});

// Enhanced error handler that creates user-friendly errors
const handleHttpError = (error) => {
  const parsedError = ErrorParser.parse(error, {
    url: error.config?.url,
    method: error.config?.method,
    timestamp: new Date().toISOString()
  });
  
  // Log the error for debugging
  logger.error('HTTP Error:', {
    type: parsedError.type,
    message: parsedError.message,
    userMessage: parsedError.userMessage,
    context: parsedError.context
  });
  
  return parsedError;
};

export default httpClient;

// Enhanced HTTP methods with built-in error handling and validation
const enhancedHttpClient = {

  // Enhanced methods with retry and validation
  async getWithRetry(url, config = {}, retryOptions = {}) {
    const customRetryManager = new RetryManager({
      maxRetries: 3,
      strategy: 'exponential',
      ...retryOptions
    });

    return await customRetryManager.execute(
      () => this.get(url, config),
      { operation: 'get', url }
    );
  },

  async postWithRetry(url, data, config = {}, retryOptions = {}) {
    const customRetryManager = new RetryManager({
      maxRetries: 2, // Fewer retries for POST to avoid duplicate operations
      strategy: 'linear',
      ...retryOptions
    });

    return await customRetryManager.execute(
      () => this.post(url, data, config),
      { operation: 'post', url }
    );
  },

  // File upload with progress tracking and error handling
  async uploadFile(url, file, options = {}) {
    const {
      onProgress,
      onError,
      validateFile = true,
      maxSize = 5 * 1024 * 1024, // 5MB default
      allowedTypes = []
    } = options;

    // Validate file if requested
    if (validateFile) {
      if (file.size > maxSize) {
        throw new Error(`File size (${(file.size / 1024 / 1024).toFixed(2)}MB) exceeds maximum allowed size (${(maxSize / 1024 / 1024).toFixed(2)}MB)`);
      }

      if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
        throw new Error(`File type ${file.type} is not allowed. Allowed types: ${allowedTypes.join(', ')}`);
      }
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await httpClient.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percentCompleted);
          }
        },
      });

      return response;
    } catch (error) {
      // Error is already enhanced by the interceptor
      if (onError) {
        onError(error);
      }
      throw error;
    }
  },

  // Batch requests with error handling
  async batchRequests(requests, options = {}) {
    const {
      failFast = false,
      maxConcurrent = 5
    } = options;

    const results = [];
    const errors = [];

    // Process requests in batches to avoid overwhelming the server
    for (let i = 0; i < requests.length; i += maxConcurrent) {
      const batch = requests.slice(i, i + maxConcurrent);
      
      const batchPromises = batch.map(async (request, index) => {
        try {
          const { method, url, data, config } = request;
          let response;

          switch (method.toLowerCase()) {
            case 'get':
              response = await this.get(url, config);
              break;
            case 'post':
              response = await this.post(url, data, config);
              break;
            case 'put':
              response = await this.put(url, data, config);
              break;
            case 'patch':
              response = await this.patch(url, data, config);
              break;
            case 'delete':
              response = await this.delete(url, config);
              break;
            default:
              throw new Error(`Unsupported HTTP method: ${method}`);
          }

          return { success: true, data: response.data, index: i + index };
        } catch (error) {
          // Error is already enhanced by the interceptor
          if (failFast) {
            throw error;
          }

          return { success: false, error: error, index: i + index };
        }
      });

      const batchResults = await Promise.all(batchPromises);
      
      batchResults.forEach(result => {
        if (result.success) {
          results[result.index] = result.data;
        } else {
          errors[result.index] = result.error;
        }
      });
    }

    return { results, errors, hasErrors: errors.length > 0 };
  },

  // Health check method
  async healthCheck() {
    try {
      const response = await this.get('/health', { timeout: 5000 });
      return { healthy: true, data: response.data };
    } catch (error) {
      // Error is already enhanced by the interceptor
      return { healthy: false, error: error };
    }
  },

  // Network status check
  async checkNetworkStatus() {
    try {
      // Try to fetch a small resource to check connectivity
      await fetch('/favicon.ico', { 
        method: 'HEAD', 
        cache: 'no-cache',
        mode: 'no-cors'
      });
      return { online: true };
    } catch (error) {
      return { online: false, error: error.message };
    }
  }
};

// Export the enhanced client separately (don't merge with httpClient to avoid recursion)
export { enhancedHttpClient };