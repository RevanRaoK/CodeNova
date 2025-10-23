/**
 * Utility functions for handling retries and error recovery
 */

/**
 * Retry a function with exponential backoff
 * @param {Function} fn - Function to retry
 * @param {Object} options - Retry options
 * @param {number} options.maxRetries - Maximum number of retries (default: 3)
 * @param {number} options.baseDelay - Base delay in milliseconds (default: 1000)
 * @param {number} options.maxDelay - Maximum delay in milliseconds (default: 10000)
 * @param {Function} options.shouldRetry - Function to determine if error should be retried
 * @returns {Promise} Promise that resolves with the function result or rejects with the last error
 */
export async function retryWithBackoff(fn, options = {}) {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    maxDelay = 10000,
    shouldRetry = (error) => isRetryableError(error)
  } = options;

  let lastError;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      // Don't retry on the last attempt or if error is not retryable
      if (attempt === maxRetries || !shouldRetry(error)) {
        throw error;
      }
      
      // Calculate delay with exponential backoff and jitter
      const delay = Math.min(
        baseDelay * Math.pow(2, attempt) + Math.random() * 1000,
        maxDelay
      );
      
      console.warn(`Attempt ${attempt + 1} failed, retrying in ${delay}ms:`, error.message);
      await sleep(delay);
    }
  }
  
  throw lastError;
}

/**
 * Determine if an error is retryable
 * @param {Error} error - The error to check
 * @returns {boolean} True if the error should be retried
 */
export function isRetryableError(error) {
  // Network errors
  if (error.code === 'NETWORK_ERROR' || error.message.includes('Network Error')) {
    return true;
  }
  
  // HTTP status codes that should be retried
  if (error.response) {
    const status = error.response.status;
    return status >= 500 || status === 408 || status === 429;
  }
  
  // Timeout errors
  if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
    return true;
  }
  
  return false;
}

/**
 * Sleep for a specified number of milliseconds
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise} Promise that resolves after the delay
 */
export function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Create a retry wrapper for API calls
 * @param {Function} apiCall - The API call function
 * @param {Object} retryOptions - Retry options
 * @returns {Function} Wrapped function with retry logic
 */
export function withRetry(apiCall, retryOptions = {}) {
  return async (...args) => {
    return retryWithBackoff(() => apiCall(...args), retryOptions);
  };
}

/**
 * Handle API errors with user-friendly messages
 * @param {Error} error - The error to handle
 * @param {Object} options - Error handling options
 * @param {string} options.operation - Description of the operation that failed
 * @param {Function} options.onRetry - Callback for retry attempts
 * @returns {Object} Error information object
 */
export function handleApiError(error, options = {}) {
  const { operation = 'operation', onRetry } = options;
  
  let userMessage = `Failed to ${operation}`;
  let canRetry = isRetryableError(error);
  let errorCode = 'UNKNOWN_ERROR';
  
  if (error.response) {
    const status = error.response.status;
    const data = error.response.data;
    
    switch (status) {
      case 400:
        userMessage = data?.detail || `Invalid request for ${operation}`;
        errorCode = 'BAD_REQUEST';
        canRetry = false;
        break;
      case 401:
        userMessage = 'Authentication required. Please log in again.';
        errorCode = 'UNAUTHORIZED';
        canRetry = false;
        break;
      case 403:
        userMessage = `Access denied for ${operation}`;
        errorCode = 'FORBIDDEN';
        canRetry = false;
        break;
      case 404:
        userMessage = `Resource not found for ${operation}`;
        errorCode = 'NOT_FOUND';
        canRetry = false;
        break;
      case 408:
        userMessage = `Request timeout for ${operation}. Please try again.`;
        errorCode = 'TIMEOUT';
        canRetry = true;
        break;
      case 413:
        userMessage = 'File too large. Please upload a smaller file.';
        errorCode = 'FILE_TOO_LARGE';
        canRetry = false;
        break;
      case 422:
        userMessage = data?.detail || `Validation error for ${operation}`;
        errorCode = 'VALIDATION_ERROR';
        canRetry = false;
        break;
      case 429:
        userMessage = `Too many requests. Please wait before trying ${operation} again.`;
        errorCode = 'RATE_LIMITED';
        canRetry = true;
        break;
      case 500:
        userMessage = `Server error during ${operation}. Please try again.`;
        errorCode = 'SERVER_ERROR';
        canRetry = true;
        break;
      case 503:
        userMessage = `Service temporarily unavailable for ${operation}. Please try again later.`;
        errorCode = 'SERVICE_UNAVAILABLE';
        canRetry = true;
        break;
      default:
        userMessage = `Unexpected error during ${operation}. Please try again.`;
        errorCode = 'UNKNOWN_HTTP_ERROR';
        canRetry = status >= 500;
    }
  } else if (error.request) {
    userMessage = `Network error during ${operation}. Please check your connection and try again.`;
    errorCode = 'NETWORK_ERROR';
    canRetry = true;
  } else {
    userMessage = error.message || `Unexpected error during ${operation}`;
    errorCode = 'UNKNOWN_ERROR';
    canRetry = false;
  }
  
  return {
    message: userMessage,
    originalError: error,
    canRetry,
    errorCode,
    onRetry: canRetry ? onRetry : null
  };
}

/**
 * Create a debounced function that delays execution
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, delay) {
  let timeoutId;
  
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

/**
 * Create a throttled function that limits execution frequency
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
export function throttle(func, limit) {
  let inThrottle;
  
  return function (...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}