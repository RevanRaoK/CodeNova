/**
 * Admin Error Handler Utility
 * 
 * Provides centralized error handling for admin components with consistent
 * error messages, logging, and state management.
 * 
 * Requirements covered: 12.5
 */

import { toast } from './toastNotifications.js';

/**
 * Error types for categorization
 */
export const ErrorType = {
  NETWORK: 'network',
  AUTHENTICATION: 'authentication',
  AUTHORIZATION: 'authorization',
  VALIDATION: 'validation',
  NOT_FOUND: 'not_found',
  CONFLICT: 'conflict',
  SERVER: 'server',
  TIMEOUT: 'timeout',
  RATE_LIMIT: 'rate_limit',
  UNKNOWN: 'unknown'
};

/**
 * Categorize error based on error object
 */
function categorizeError(error) {
  if (error.message?.includes('Network error') || error.code === 'NETWORK_ERROR') {
    return ErrorType.NETWORK;
  }
  
  if (error.message?.includes('Authentication required') || error.response?.status === 401) {
    return ErrorType.AUTHENTICATION;
  }
  
  if (error.message?.includes('Access denied') || error.response?.status === 403) {
    return ErrorType.AUTHORIZATION;
  }
  
  if (error.message?.includes('Invalid data') || error.response?.status === 422) {
    return ErrorType.VALIDATION;
  }
  
  if (error.message?.includes('not found') || error.response?.status === 404) {
    return ErrorType.NOT_FOUND;
  }
  
  if (error.message?.includes('already exist') || error.response?.status === 409) {
    return ErrorType.CONFLICT;
  }
  
  if (error.message?.includes('Server error') || error.response?.status >= 500) {
    return ErrorType.SERVER;
  }
  
  if (error.message?.includes('timeout') || error.code === 'ECONNABORTED') {
    return ErrorType.TIMEOUT;
  }
  
  if (error.response?.status === 429) {
    return ErrorType.RATE_LIMIT;
  }
  
  return ErrorType.UNKNOWN;
}

/**
 * Get user-friendly error message based on error type and context
 */
function getErrorMessage(error, context = {}) {
  const errorType = categorizeError(error);
  const { operation = 'operation', resource = 'resource' } = context;
  
  switch (errorType) {
    case ErrorType.NETWORK:
      return `Network error during ${operation}. Please check your connection and try again.`;
    
    case ErrorType.AUTHENTICATION:
      return 'Your session has expired. Please log in again.';
    
    case ErrorType.AUTHORIZATION:
      return `Access denied. You don't have permission to ${operation}.`;
    
    case ErrorType.VALIDATION:
      return `Invalid data provided for ${operation}. Please check your input.`;
    
    case ErrorType.NOT_FOUND:
      return `${resource} not found. It may have been deleted or moved.`;
    
    case ErrorType.CONFLICT:
      return `${resource} already exists or conflicts with existing data.`;
    
    case ErrorType.SERVER:
      return `Server error during ${operation}. Please try again in a few moments.`;
    
    case ErrorType.TIMEOUT:
      return `Request timeout during ${operation}. Please try again.`;
    
    case ErrorType.RATE_LIMIT:
      return `Too many requests. Please wait a moment before trying again.`;
    
    default:
      return error.message || `An unexpected error occurred during ${operation}.`;
  }
}

/**
 * Handle admin API errors with comprehensive logging and user feedback
 */
export function handleAdminError(error, options = {}) {
  const {
    operation = 'operation',
    resource = 'resource',
    showToast = true,
    logToConsole = true,
    onError = null,
    context = {}
  } = options;
  
  // Log error for debugging
  if (logToConsole) {
    console.error(`Admin ${operation} error:`, {
      error,
      context,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    });
  }
  
  // Get user-friendly error message
  const errorMessage = getErrorMessage(error, { operation, resource });
  
  // Show toast notification
  if (showToast) {
    const errorType = categorizeError(error);
    
    if (errorType === ErrorType.AUTHENTICATION) {
      toast.error(errorMessage, {
        duration: 7000,
        action: {
          label: 'Login',
          onClick: () => window.location.href = '/login'
        }
      });
    } else if (errorType === ErrorType.NETWORK || errorType === ErrorType.TIMEOUT) {
      toast.error(errorMessage, {
        duration: 5000,
        action: {
          label: 'Retry',
          onClick: () => window.location.reload()
        }
      });
    } else {
      toast.error(errorMessage);
    }
  }
  
  // Call custom error handler if provided
  if (onError && typeof onError === 'function') {
    onError(error, errorMessage);
  }
  
  return {
    error,
    message: errorMessage,
    type: categorizeError(error)
  };
}

/**
 * Wrapper for admin API calls with automatic error handling
 */
export async function withErrorHandling(apiCall, options = {}) {
  const {
    operation = 'API call',
    resource = 'resource',
    showLoadingToast = false,
    loadingMessage = 'Loading...',
    successMessage = null,
    onSuccess = null,
    onError = null,
    retries = 0,
    retryDelay = 1000
  } = options;
  
  let loadingToastId = null;
  
  if (showLoadingToast) {
    loadingToastId = toast.loading(loadingMessage);
  }
  
  let lastError = null;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const result = await apiCall();
      
      // Remove loading toast
      if (loadingToastId) {
        toast.remove(loadingToastId);
      }
      
      // Show success message
      if (successMessage) {
        toast.success(successMessage);
      }
      
      // Call success handler
      if (onSuccess && typeof onSuccess === 'function') {
        onSuccess(result);
      }
      
      return result;
    } catch (error) {
      lastError = error;
      
      // If this is not the last attempt and error is retryable, wait and retry
      if (attempt < retries && isRetryableError(error)) {
        console.log(`Attempt ${attempt + 1} failed, retrying in ${retryDelay}ms...`);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
        continue;
      }
      
      // Remove loading toast
      if (loadingToastId) {
        toast.remove(loadingToastId);
      }
      
      // Handle the error
      const errorResult = handleAdminError(error, {
        operation,
        resource,
        onError
      });
      
      throw errorResult.error;
    }
  }
  
  // This should never be reached, but just in case
  throw lastError;
}

/**
 * Check if an error is retryable
 */
function isRetryableError(error) {
  const errorType = categorizeError(error);
  return [
    ErrorType.NETWORK,
    ErrorType.TIMEOUT,
    ErrorType.SERVER,
    ErrorType.RATE_LIMIT
  ].includes(errorType);
}

/**
 * Preserve component state on error
 */
export function preserveStateOnError(currentState, previousState, fallbackState = null) {
  // If we have previous state and current operation failed, preserve previous state
  if (previousState !== null && previousState !== undefined) {
    return previousState;
  }
  
  // If no previous state, use fallback or current state
  return fallbackState !== null ? fallbackState : currentState;
}

/**
 * Create error boundary for admin components
 */
export function createErrorBoundary(componentName) {
  return function errorBoundary(error, errorInfo) {
    console.error(`Error in ${componentName}:`, error, errorInfo);
    
    toast.error(`An error occurred in ${componentName}. Please refresh the page.`, {
      duration: 7000,
      action: {
        label: 'Refresh',
        onClick: () => window.location.reload()
      }
    });
  };
}

/**
 * Validate admin operation permissions
 */
export function validateAdminPermissions(currentUser, requiredRole = 'admin') {
  if (!currentUser) {
    throw new Error('Authentication required. Please log in.');
  }
  
  if (currentUser.role !== requiredRole && currentUser.role !== 'admin') {
    throw new Error(`Access denied. ${requiredRole} privileges required.`);
  }
  
  return true;
}

/**
 * Admin-specific error messages
 */
export const AdminErrorMessages = {
  // User management
  USER_LOAD_FAILED: 'Failed to load users',
  USER_UPDATE_FAILED: 'Failed to update user',
  USER_DELETE_FAILED: 'Failed to delete user',
  USER_CREATE_FAILED: 'Failed to create user',
  ROLE_UPDATE_FAILED: 'Failed to update user role',
  
  // Team management
  TEAM_LOAD_FAILED: 'Failed to load teams',
  TEAM_UPDATE_FAILED: 'Failed to update team',
  TEAM_DELETE_FAILED: 'Failed to delete team',
  TEAM_CREATE_FAILED: 'Failed to create team',
  
  // Analytics
  ANALYTICS_LOAD_FAILED: 'Failed to load analytics data',
  DASHBOARD_LOAD_FAILED: 'Failed to load dashboard metrics',
  
  // Audit logs
  AUDIT_LOGS_LOAD_FAILED: 'Failed to load audit logs',
  
  // General
  PERMISSION_DENIED: 'You do not have permission to perform this action',
  SESSION_EXPIRED: 'Your session has expired. Please log in again.',
  NETWORK_ERROR: 'Network error. Please check your connection.',
  SERVER_ERROR: 'Server error. Please try again later.'
};

export default {
  handleAdminError,
  withErrorHandling,
  preserveStateOnError,
  createErrorBoundary,
  validateAdminPermissions,
  AdminErrorMessages,
  ErrorType
};