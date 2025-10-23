/**
 * Error handling utilities (non-React components)
 * For React components, see errorHandler.jsx
 */

// Error types
export const ERROR_TYPES = {
  NETWORK: 'network',
  VALIDATION: 'validation',
  AUTHENTICATION: 'authentication',
  AUTHORIZATION: 'authorization',
  SERVER: 'server',
  CLIENT: 'client',
  TIMEOUT: 'timeout',
  RATE_LIMIT: 'rate_limit',
  FILE_UPLOAD: 'file_upload',
  API_KEY: 'api_key',
  UNKNOWN: 'unknown'
};

// Error severity levels
export const ERROR_SEVERITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
};

// Retry strategies
export const RETRY_STRATEGIES = {
  NONE: 'none',
  IMMEDIATE: 'immediate',
  LINEAR: 'linear',
  EXPONENTIAL: 'exponential',
  CUSTOM: 'custom'
};

/**
 * Enhanced error class with additional context
 */
export class AppError extends Error {
  constructor(message, type = ERROR_TYPES.UNKNOWN, severity = ERROR_SEVERITY.MEDIUM, context = {}) {
    super(message);
    this.name = 'AppError';
    this.type = type;
    this.severity = severity;
    this.context = context;
    this.timestamp = new Date().toISOString();
    this.userMessage = this.generateUserMessage();
    this.retryable = this.isRetryable();
  }

  generateUserMessage() {
    const userMessages = {
      [ERROR_TYPES.NETWORK]: 'Network connection error. Please check your internet connection and try again.',
      [ERROR_TYPES.VALIDATION]: 'Please check your input and correct any errors.',
      [ERROR_TYPES.AUTHENTICATION]: 'Authentication failed. Please log in again.',
      [ERROR_TYPES.AUTHORIZATION]: 'You don\'t have permission to perform this action.',
      [ERROR_TYPES.SERVER]: 'Server error. Please try again later.',
      [ERROR_TYPES.CLIENT]: 'An error occurred. Please refresh the page and try again.',
      [ERROR_TYPES.TIMEOUT]: 'Request timed out. Please try again.',
      [ERROR_TYPES.RATE_LIMIT]: 'Too many requests. Please wait a moment and try again.',
      [ERROR_TYPES.FILE_UPLOAD]: 'File upload failed. Please check the file and try again.',
      [ERROR_TYPES.API_KEY]: 'API key error. Please check your API key configuration.',
      [ERROR_TYPES.UNKNOWN]: 'An unexpected error occurred. Please try again.'
    };

    return userMessages[this.type] || this.message;
  }

  isRetryable() {
    const retryableTypes = [
      ERROR_TYPES.NETWORK,
      ERROR_TYPES.SERVER,
      ERROR_TYPES.TIMEOUT,
      ERROR_TYPES.RATE_LIMIT
    ];
    return retryableTypes.includes(this.type);
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      userMessage: this.userMessage,
      type: this.type,
      severity: this.severity,
      context: this.context,
      timestamp: this.timestamp,
      retryable: this.retryable,
      stack: this.stack
    };
  }
}

/**
 * Error parser to convert various error formats to AppError
 */
export class ErrorParser {
  static parse(error, context = {}) {
    if (error instanceof AppError) {
      return error;
    }

    // Handle Axios/HTTP errors
    if (error.response) {
      return this.parseHttpError(error, context);
    }

    // Handle network errors
    if (error.request) {
      return new AppError(
        'Network request failed',
        ERROR_TYPES.NETWORK,
        ERROR_SEVERITY.HIGH,
        { ...context, originalError: error.message }
      );
    }

    // Handle validation errors
    if (error.name === 'ValidationError') {
      return new AppError(
        error.message,
        ERROR_TYPES.VALIDATION,
        ERROR_SEVERITY.MEDIUM,
        { ...context, validationErrors: error.errors }
      );
    }

    // Handle timeout errors
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      return new AppError(
        'Request timed out',
        ERROR_TYPES.TIMEOUT,
        ERROR_SEVERITY.MEDIUM,
        { ...context, timeout: true }
      );
    }

    // Default error
    return new AppError(
      error.message || 'An unexpected error occurred',
      ERROR_TYPES.UNKNOWN,
      ERROR_SEVERITY.MEDIUM,
      { ...context, originalError: error }
    );
  }

  static parseHttpError(error, context = {}) {
    const { status, data } = error.response;
    const errorMessage = data?.detail || data?.message || error.message;

    switch (status) {
      case 400:
        return new AppError(
          errorMessage || 'Bad request',
          ERROR_TYPES.VALIDATION,
          ERROR_SEVERITY.MEDIUM,
          { ...context, status, validationErrors: data?.errors }
        );

      case 401:
        return new AppError(
          'Authentication required',
          ERROR_TYPES.AUTHENTICATION,
          ERROR_SEVERITY.HIGH,
          { ...context, status, requiresLogin: true }
        );

      case 403:
        return new AppError(
          'Access forbidden',
          ERROR_TYPES.AUTHORIZATION,
          ERROR_SEVERITY.HIGH,
          { ...context, status }
        );

      case 404:
        return new AppError(
          'Resource not found',
          ERROR_TYPES.CLIENT,
          ERROR_SEVERITY.MEDIUM,
          { ...context, status }
        );

      case 409:
        return new AppError(
          errorMessage || 'Conflict with existing data',
          ERROR_TYPES.VALIDATION,
          ERROR_SEVERITY.MEDIUM,
          { ...context, status, conflict: true }
        );

      case 422:
        return new AppError(
          errorMessage || 'Validation failed',
          ERROR_TYPES.VALIDATION,
          ERROR_SEVERITY.MEDIUM,
          { ...context, status, validationErrors: data?.errors }
        );

      case 429:
        return new AppError(
          'Rate limit exceeded',
          ERROR_TYPES.RATE_LIMIT,
          ERROR_SEVERITY.MEDIUM,
          { ...context, status, retryAfter: error.response.headers['retry-after'] }
        );

      case 500:
      case 502:
      case 503:
      case 504:
        return new AppError(
          'Server error',
          ERROR_TYPES.SERVER,
          ERROR_SEVERITY.HIGH,
          { ...context, status }
        );

      default:
        return new AppError(
          errorMessage || 'HTTP error',
          ERROR_TYPES.UNKNOWN,
          ERROR_SEVERITY.MEDIUM,
          { ...context, status }
        );
    }
  }
}

/**
 * Retry mechanism with different strategies
 */
export class RetryManager {
  constructor(options = {}) {
    this.maxRetries = options.maxRetries || 3;
    this.strategy = options.strategy || RETRY_STRATEGIES.EXPONENTIAL;
    this.baseDelay = options.baseDelay || 1000;
    this.maxDelay = options.maxDelay || 10000;
    this.retryCondition = options.retryCondition || this.defaultRetryCondition;
    this.onRetry = options.onRetry || (() => {});
  }

  defaultRetryCondition(error) {
    if (error instanceof AppError) {
      return error.retryable;
    }
    
    // Retry on network errors and 5xx server errors
    return error.code === 'NETWORK_ERROR' || 
           (error.response && error.response.status >= 500);
  }

  calculateDelay(attempt) {
    switch (this.strategy) {
      case RETRY_STRATEGIES.IMMEDIATE:
        return 0;
      
      case RETRY_STRATEGIES.LINEAR:
        return Math.min(this.baseDelay * attempt, this.maxDelay);
      
      case RETRY_STRATEGIES.EXPONENTIAL:
        return Math.min(this.baseDelay * Math.pow(2, attempt - 1), this.maxDelay);
      
      default:
        return this.baseDelay;
    }
  }

  async execute(operation, context = {}) {
    let lastError;
    
    for (let attempt = 1; attempt <= this.maxRetries + 1; attempt++) {
      try {
        const result = await operation();
        return result;
      } catch (error) {
        const parsedError = ErrorParser.parse(error, { ...context, attempt });
        lastError = parsedError;

        // Don't retry if this is the last attempt or error is not retryable
        if (attempt > this.maxRetries || !this.retryCondition(parsedError)) {
          throw parsedError;
        }

        // Calculate delay and wait
        const delay = this.calculateDelay(attempt);
        
        // Notify about retry
        this.onRetry(parsedError, attempt, delay);
        
        if (delay > 0) {
          await this.sleep(delay);
        }
      }
    }

    throw lastError;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * Utility functions for common error scenarios
 */
export const ErrorUtils = {
  // Check if error is a specific type
  isNetworkError: (error) => error instanceof AppError && error.type === ERROR_TYPES.NETWORK,
  isValidationError: (error) => error instanceof AppError && error.type === ERROR_TYPES.VALIDATION,
  isAuthError: (error) => error instanceof AppError && error.type === ERROR_TYPES.AUTHENTICATION,
  isServerError: (error) => error instanceof AppError && error.type === ERROR_TYPES.SERVER,

  // Format error for display
  formatErrorMessage: (error) => {
    if (error instanceof AppError) {
      return error.userMessage;
    }
    return error.message || 'An unexpected error occurred';
  },

  // Get error suggestions
  getErrorSuggestions: (error) => {
    if (!(error instanceof AppError)) return [];

    const suggestions = {
      [ERROR_TYPES.NETWORK]: [
        'Check your internet connection',
        'Try refreshing the page',
        'Contact support if the problem persists'
      ],
      [ERROR_TYPES.VALIDATION]: [
        'Review the form fields for errors',
        'Ensure all required fields are filled',
        'Check the format of your input'
      ],
      [ERROR_TYPES.AUTHENTICATION]: [
        'Log out and log back in',
        'Clear your browser cache',
        'Reset your password if needed'
      ],
      [ERROR_TYPES.SERVER]: [
        'Try again in a few minutes',
        'Contact support if the issue continues',
        'Check our status page for known issues'
      ],
      [ERROR_TYPES.RATE_LIMIT]: [
        'Wait a moment before trying again',
        'Reduce the frequency of your requests',
        'Contact support for higher limits'
      ]
    };

    return suggestions[error.type] || [];
  },

  // Create user-friendly error messages for specific scenarios
  createApiKeyError: (message) => new AppError(
    message,
    ERROR_TYPES.API_KEY,
    ERROR_SEVERITY.MEDIUM,
    { field: 'apiKey' }
  ),

  createValidationError: (field, message) => new AppError(
    message,
    ERROR_TYPES.VALIDATION,
    ERROR_SEVERITY.MEDIUM,
    { field }
  ),

  createFileUploadError: (filename, message) => new AppError(
    message,
    ERROR_TYPES.FILE_UPLOAD,
    ERROR_SEVERITY.MEDIUM,
    { filename }
  )
};

export default {
  AppError,
  ErrorParser,
  RetryManager,
  ErrorUtils,
  ERROR_TYPES,
  ERROR_SEVERITY,
  RETRY_STRATEGIES
};
