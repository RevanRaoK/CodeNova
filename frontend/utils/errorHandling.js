/**
 * Error Handling Utilities
 * 
 * Provides centralized error handling and user-friendly error messages
 * for the frontend application.
 * 
 * Requirements covered: 12.3, 12.4, 12.5
 */

import { toast, UserActionToasts } from './toastNotifications';

/**
 * Error types
 */
export const ErrorType = {
  VALIDATION: 'validation_error',
  AUTHENTICATION: 'authentication_error',
  AUTHORIZATION: 'authorization_error',
  NOT_FOUND: 'resource_not_found',
  CONFLICT: 'conflict_error',
  RATE_LIMIT: 'rate_limit_exceeded',
  SERVICE_UNAVAILABLE: 'service_unavailable',
  FILE_UPLOAD: 'file_upload_error',
  ANALYSIS: 'analysis_error',
  NETWORK: 'network_error',
  SERVER: 'internal_error',
  UNKNOWN: 'unknown_error'
};

/**
 * User-friendly error messages
 */
const ERROR_MESSAGES = {
  [ErrorType.VALIDATION]: 'Please check your input and try again.',
  [ErrorType.AUTHENTICATION]: 'Please log in to continue.',
  [ErrorType.AUTHORIZATION]: "You don't have permission to perform this action.",
  [ErrorType.NOT_FOUND]: 'The requested resource was not found.',
  [ErrorType.CONFLICT]: 'This action conflicts with existing data.',
  [ErrorType.RATE_LIMIT]: "You're making too many requests. Please wait and try again.",
  [ErrorType.SERVICE_UNAVAILABLE]: 'This service is temporarily unavailable. Please try again later.',
  [ErrorType.FILE_UPLOAD]: 'There was a problem uploading your file.',
  [ErrorType.ANALYSIS]: 'There was a problem analyzing your code.',
  [ErrorType.NETWORK]: 'Network error. Please check your connection.',
  [ErrorType.SERVER]: 'An unexpected error occurred. Please try again.',
  [ErrorType.UNKNOWN]: 'An unexpected error occurred.'
};

/**
 * Parse error from API response
 */
export function parseApiError(error) {
  // Handle network errors
  if (!error.response) {
    return {
      type: ErrorType.NETWORK,
      message: ERROR_MESSAGES[ErrorType.NETWORK],
      originalError: error
    };
  }

  const { status, data } = error.response;

  // Handle different status codes
  switch (status) {
    case 400:
      return {
        type: ErrorType.VALIDATION,
        message: data?.message || ERROR_MESSAGES[ErrorType.VALIDATION],
        details: data?.details,
        originalError: error
      };

    case 401:
      return {
        type: ErrorType.AUTHENTICATION,
        message: data?.message || ERROR_MESSAGES[ErrorType.AUTHENTICATION],
        originalError: error
      };

    case 403:
      return {
        type: ErrorType.AUTHORIZATION,
        message: data?.message || ERROR_MESSAGES[ErrorType.AUTHORIZATION],
        originalError: error
      };

    case 404:
      return {
        type: ErrorType.NOT_FOUND,
        message: data?.message || ERROR_MESSAGES[ErrorType.NOT_FOUND],
        details: data?.details,
        originalError: error
      };

    case 409:
      return {
        type: ErrorType.CONFLICT,
        message: data?.message || ERROR_MESSAGES[ErrorType.CONFLICT],
        details: data?.details,
        originalError: error
      };

    case 422:
      return {
        type: ErrorType.VALIDATION,
        message: data?.message || 'Invalid input data',
        details: data?.details,
        originalError: error
      };

    case 429:
      return {
        type: ErrorType.RATE_LIMIT,
        message: data?.message || ERROR_MESSAGES[ErrorType.RATE_LIMIT],
        retryAfter: data?.details?.retry_after,
        originalError: error
      };

    case 503:
      return {
        type: ErrorType.SERVICE_UNAVAILABLE,
        message: data?.message || ERROR_MESSAGES[ErrorType.SERVICE_UNAVAILABLE],
        originalError: error
      };

    case 500:
    case 502:
    case 504:
      return {
        type: ErrorType.SERVER,
        message: data?.message || ERROR_MESSAGES[ErrorType.SERVER],
        originalError: error
      };

    default:
      return {
        type: ErrorType.UNKNOWN,
        message: data?.message || ERROR_MESSAGES[ErrorType.UNKNOWN],
        originalError: error
      };
  }
}

/**
 * Handle API error and show appropriate toast
 */
export function handleApiError(error, context = '') {
  const parsedError = parseApiError(error);

  // Log error for debugging
  console.error(`[${context}] API Error:`, parsedError);

  // Show appropriate toast based on error type
  switch (parsedError.type) {
    case ErrorType.VALIDATION:
      if (parsedError.details?.errors) {
        // Show first validation error
        const firstError = parsedError.details.errors[0];
        toast.warning(`${firstError.field}: ${firstError.message}`);
      } else {
        toast.warning(parsedError.message);
      }
      break;

    case ErrorType.AUTHENTICATION:
      toast.error(parsedError.message, {
        action: {
          label: 'Log In',
          onClick: () => window.location.href = '/login'
        }
      });
      break;

    case ErrorType.AUTHORIZATION:
      UserActionToasts.permissionDenied();
      break;

    case ErrorType.RATE_LIMIT:
      if (parsedError.retryAfter) {
        UserActionToasts.rateLimitExceeded(parsedError.retryAfter);
      } else {
        toast.warning(parsedError.message);
      }
      break;

    case ErrorType.NETWORK:
      UserActionToasts.networkError();
      break;

    case ErrorType.SERVER:
      UserActionToasts.serverError();
      break;

    default:
      toast.error(parsedError.message);
  }

  return parsedError;
}

/**
 * Retry mechanism for failed operations
 */
export async function retryOperation(
  operation,
  options = {}
) {
  const {
    maxRetries = 3,
    delay = 1000,
    backoff = 2,
    onRetry = null
  } = options;

  let lastError;
  let currentDelay = delay;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;

      if (attempt < maxRetries) {
        // Check if error is retryable
        const parsedError = parseApiError(error);
        const retryableErrors = [
          ErrorType.NETWORK,
          ErrorType.SERVER,
          ErrorType.SERVICE_UNAVAILABLE
        ];

        if (!retryableErrors.includes(parsedError.type)) {
          // Don't retry non-retryable errors
          throw error;
        }

        // Call onRetry callback if provided
        if (onRetry) {
          onRetry(attempt + 1, maxRetries, currentDelay);
        }

        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, currentDelay));
        currentDelay *= backoff;
      }
    }
  }

  throw lastError;
}

/**
 * Wrap async operation with error handling and toast notifications
 */
export async function withErrorHandling(
  operation,
  options = {}
) {
  const {
    loadingMessage = 'Loading...',
    successMessage = 'Success!',
    errorMessage = null,
    showLoading = true,
    showSuccess = true,
    showError = true,
    context = '',
    retry = false,
    retryOptions = {}
  } = options;

  let loadingToastId;

  try {
    // Show loading toast
    if (showLoading) {
      loadingToastId = toast.loading(loadingMessage);
    }

    // Execute operation with optional retry
    const result = retry
      ? await retryOperation(operation, retryOptions)
      : await operation();

    // Remove loading toast
    if (loadingToastId) {
      toast.remove(loadingToastId);
    }

    // Show success toast
    if (showSuccess) {
      toast.success(successMessage);
    }

    return result;
  } catch (error) {
    // Remove loading toast
    if (loadingToastId) {
      toast.remove(loadingToastId);
    }

    // Show error toast
    if (showError) {
      if (errorMessage) {
        toast.error(errorMessage);
      } else {
        handleApiError(error, context);
      }
    }

    throw error;
  }
}

/**
 * Validation error formatter
 */
export function formatValidationErrors(errors) {
  if (!errors || !Array.isArray(errors)) {
    return [];
  }

  return errors.map(error => ({
    field: error.field,
    message: error.message
  }));
}

/**
 * Check if error is a specific type
 */
export function isErrorType(error, type) {
  const parsedError = parseApiError(error);
  return parsedError.type === type;
}

/**
 * Get user-friendly error message
 */
export function getUserFriendlyMessage(error) {
  const parsedError = parseApiError(error);
  return parsedError.message;
}

/**
 * Error boundary helper
 */
export class ErrorBoundaryHelper {
  static logError(error, errorInfo) {
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    // In production, you might want to send this to an error tracking service
    // like Sentry, LogRocket, etc.
  }

  static getFallbackMessage(error) {
    if (process.env.NODE_ENV === 'development') {
      return error.toString();
    }
    return 'Something went wrong. Please refresh the page and try again.';
  }
}

/**
 * Form validation helper
 */
export class FormValidationHelper {
  static validateRequired(value, fieldName) {
    if (!value || (typeof value === 'string' && !value.trim())) {
      return `${fieldName} is required`;
    }
    return null;
  }

  static validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return 'Please enter a valid email address';
    }
    return null;
  }

  static validatePassword(password) {
    if (password.length < 8) {
      return 'Password must be at least 8 characters long';
    }
    if (!/[A-Z]/.test(password)) {
      return 'Password must contain at least one uppercase letter';
    }
    if (!/[a-z]/.test(password)) {
      return 'Password must contain at least one lowercase letter';
    }
    if (!/[0-9]/.test(password)) {
      return 'Password must contain at least one number';
    }
    return null;
  }

  static validateMinLength(value, minLength, fieldName) {
    if (value.length < minLength) {
      return `${fieldName} must be at least ${minLength} characters`;
    }
    return null;
  }

  static validateMaxLength(value, maxLength, fieldName) {
    if (value.length > maxLength) {
      return `${fieldName} must be no more than ${maxLength} characters`;
    }
    return null;
  }

  static validateUrl(url) {
    try {
      new URL(url);
      return null;
    } catch {
      return 'Please enter a valid URL';
    }
  }

  static validateFileSize(file, maxSizeMB) {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      return `File size must be less than ${maxSizeMB}MB`;
    }
    return null;
  }

  static validateFileType(file, allowedTypes) {
    const fileExtension = file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(`.${fileExtension}`)) {
      return `File type .${fileExtension} is not allowed`;
    }
    return null;
  }
}

export default {
  parseApiError,
  handleApiError,
  retryOperation,
  withErrorHandling,
  formatValidationErrors,
  isErrorType,
  getUserFriendlyMessage,
  ErrorBoundaryHelper,
  FormValidationHelper
};
