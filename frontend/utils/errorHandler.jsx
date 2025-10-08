import React from 'react';
import { logger } from './environment';

/**
 * Centralized error handling utility for the application
 */
class ErrorHandler {
     constructor() {
          this.errorListeners = new Set();
          this.errorHistory = [];
          this.maxHistorySize = 100;
     }

     /**
      * Handle API errors with proper user feedback
      */
     handleApiError(error, context = {}) {
          const errorInfo = this.parseApiError(error);

          // Log the error
          logger.error('API Error:', {
               ...errorInfo,
               context,
               timestamp: new Date().toISOString()
          });

          // Add to error history
          this.addToHistory({
               type: 'api',
               ...errorInfo,
               context,
               timestamp: new Date()
          });

          // Notify listeners
          this.notifyListeners({
               type: 'api',
               ...errorInfo,
               context
          });

          return errorInfo;
     }

     /**
      * Handle authentication errors
      */
     handleAuthError(error, context = {}) {
          const errorInfo = {
               type: 'authentication',
               message: this.getAuthErrorMessage(error),
               code: error.response?.status || 'AUTH_ERROR',
               originalError: error
          };

          logger.error('Authentication Error:', {
               ...errorInfo,
               context,
               timestamp: new Date().toISOString()
          });

          this.addToHistory({
               ...errorInfo,
               context,
               timestamp: new Date()
          });

          this.notifyListeners({
               ...errorInfo,
               context
          });

          return errorInfo;
     }

     /**
      * Handle workflow errors
      */
     handleWorkflowError(error, workflowId, step, context = {}) {
          const errorInfo = {
               type: 'workflow',
               workflowId,
               step,
               message: error.message || 'Workflow step failed',
               code: error.code || 'WORKFLOW_ERROR',
               originalError: error
          };

          logger.error('Workflow Error:', {
               ...errorInfo,
               context,
               timestamp: new Date().toISOString()
          });

          this.addToHistory({
               ...errorInfo,
               context,
               timestamp: new Date()
          });

          this.notifyListeners({
               ...errorInfo,
               context
          });

          return errorInfo;
     }

     /**
      * Handle component errors (React Error Boundary)
      */
     handleComponentError(error, errorInfo, context = {}) {
          const errorData = {
               type: 'component',
               message: error.message || 'Component error occurred',
               stack: error.stack,
               componentStack: errorInfo.componentStack,
               code: 'COMPONENT_ERROR',
               originalError: error
          };

          logger.error('Component Error:', {
               ...errorData,
               context,
               timestamp: new Date().toISOString()
          });

          this.addToHistory({
               ...errorData,
               context,
               timestamp: new Date()
          });

          this.notifyListeners({
               ...errorData,
               context
          });

          return errorData;
     }

     /**
      * Handle network errors
      */
     handleNetworkError(error, context = {}) {
          const errorInfo = {
               type: 'network',
               message: 'Network connection failed. Please check your internet connection.',
               code: 'NETWORK_ERROR',
               isRetryable: true,
               originalError: error
          };

          logger.error('Network Error:', {
               ...errorInfo,
               context,
               timestamp: new Date().toISOString()
          });

          this.addToHistory({
               ...errorInfo,
               context,
               timestamp: new Date()
          });

          this.notifyListeners({
               ...errorInfo,
               context
          });

          return errorInfo;
     }

     /**
      * Parse API errors into user-friendly format
      */
     parseApiError(error) {
          if (error.response) {
               const { status, data } = error.response;

               return {
                    message: this.getApiErrorMessage(status, data),
                    code: status,
                    details: data,
                    isRetryable: this.isRetryableError(status)
               };
          } else if (error.request) {
               return this.handleNetworkError(error);
          } else {
               return {
                    message: error.message || 'An unexpected error occurred',
                    code: 'UNKNOWN_ERROR',
                    isRetryable: false
               };
          }
     }

     /**
      * Get user-friendly API error messages
      */
     getApiErrorMessage(status, data) {
          const detail = data?.detail || data?.message;

          switch (status) {
               case 400:
                    return detail || 'Invalid request. Please check your input and try again.';
               case 401:
                    return 'You are not authorized. Please log in and try again.';
               case 403:
                    return 'You do not have permission to perform this action.';
               case 404:
                    return 'The requested resource was not found.';
               case 409:
                    return detail || 'A conflict occurred. The resource may already exist.';
               case 422:
                    return detail || 'Validation failed. Please check your input.';
               case 429:
                    return 'Too many requests. Please wait a moment and try again.';
               case 500:
                    return 'Server error. Please try again later.';
               case 502:
                    return 'Service temporarily unavailable. Please try again later.';
               case 503:
                    return 'Service maintenance in progress. Please try again later.';
               default:
                    return detail || 'An error occurred. Please try again.';
          }
     }

     /**
      * Get user-friendly authentication error messages
      */
     getAuthErrorMessage(error) {
          if (error.response?.status === 401) {
               return 'Invalid credentials. Please check your email and password.';
          } else if (error.response?.status === 403) {
               return 'Account access denied. Please contact support.';
          } else if (error.response?.status === 429) {
               return 'Too many login attempts. Please try again later.';
          } else {
               return error.message || 'Authentication failed. Please try again.';
          }
     }

     /**
      * Determine if an error is retryable
      */
     isRetryableError(status) {
          return [408, 429, 500, 502, 503, 504].includes(status);
     }

     /**
      * Add error to history
      */
     addToHistory(errorData) {
          this.errorHistory.unshift(errorData);

          // Keep history size manageable
          if (this.errorHistory.length > this.maxHistorySize) {
               this.errorHistory = this.errorHistory.slice(0, this.maxHistorySize);
          }
     }

     /**
      * Get error history
      */
     getErrorHistory(limit = 10) {
          return this.errorHistory.slice(0, limit);
     }

     /**
      * Clear error history
      */
     clearErrorHistory() {
          this.errorHistory = [];
     }

     /**
      * Add error listener
      */
     addErrorListener(listener) {
          this.errorListeners.add(listener);

          // Return unsubscribe function
          return () => {
               this.errorListeners.delete(listener);
          };
     }

     /**
      * Notify all error listeners
      */
     notifyListeners(errorData) {
          this.errorListeners.forEach(listener => {
               try {
                    listener(errorData);
               } catch (error) {
                    logger.error('Error listener failed:', error);
               }
          });
     }

     /**
      * Create error recovery suggestions
      */
     getRecoverySuggestions(errorData) {
          const suggestions = [];

          switch (errorData.type) {
               case 'network':
                    suggestions.push(
                         'Check your internet connection',
                         'Try refreshing the page',
                         'Wait a moment and try again'
                    );
                    break;

               case 'authentication':
                    suggestions.push(
                         'Check your login credentials',
                         'Try logging out and back in',
                         'Clear your browser cache'
                    );
                    break;

               case 'api':
                    if (errorData.isRetryable) {
                         suggestions.push(
                              'Wait a moment and try again',
                              'Check your internet connection'
                         );
                    } else {
                         suggestions.push(
                              'Check your input and try again',
                              'Contact support if the problem persists'
                         );
                    }
                    break;

               case 'workflow':
                    suggestions.push(
                         'Try restarting the process',
                         'Check that all required fields are filled',
                         'Contact support if the issue continues'
                    );
                    break;

               default:
                    suggestions.push(
                         'Try refreshing the page',
                         'Contact support if the problem persists'
                    );
          }

          return suggestions;
     }

     /**
      * Format error for display
      */
     formatErrorForDisplay(errorData) {
          return {
               title: this.getErrorTitle(errorData.type),
               message: errorData.message,
               suggestions: this.getRecoverySuggestions(errorData),
               canRetry: errorData.isRetryable || false,
               timestamp: errorData.timestamp || new Date()
          };
     }

     /**
      * Get error title based on type
      */
     getErrorTitle(type) {
          switch (type) {
               case 'network':
                    return 'Connection Error';
               case 'authentication':
                    return 'Authentication Error';
               case 'api':
                    return 'Service Error';
               case 'workflow':
                    return 'Process Error';
               case 'component':
                    return 'Application Error';
               default:
                    return 'Error';
          }
     }

     /**
      * Create retry function for retryable errors
      */
     createRetryFunction(originalFunction, context = {}) {
          return async (retryCount = 0, maxRetries = 3) => {
               try {
                    return await originalFunction();
               } catch (error) {
                    const errorInfo = this.handleApiError(error, context);

                    if (errorInfo.isRetryable && retryCount < maxRetries) {
                         const delay = Math.min(1000 * Math.pow(2, retryCount), 10000); // Exponential backoff

                         logger.info(`Retrying operation in ${delay}ms (attempt ${retryCount + 1}/${maxRetries})`);

                         await new Promise(resolve => setTimeout(resolve, delay));
                         return this.createRetryFunction(originalFunction, context)(retryCount + 1, maxRetries);
                    }

                    throw error;
               }
          };
     }
}

// Export singleton instance
const errorHandler = new ErrorHandler();
export default errorHandler;

// Export React Error Boundary component
export class ErrorBoundary extends React.Component {
     constructor(props) {
          super(props);
          this.state = { hasError: false, error: null, errorInfo: null };
     }

     static getDerivedStateFromError(error) {
          return { hasError: true };
     }

     componentDidCatch(error, errorInfo) {
          const errorData = errorHandler.handleComponentError(error, errorInfo, {
               component: this.props.name || 'Unknown'
          });

          this.setState({
               error: errorData,
               errorInfo
          });
     }

     render() {
          if (this.state.hasError) {
               if (this.props.fallback) {
                    return this.props.fallback(this.state.error);
               }

               return (
                    <div className="min-h-screen flex items-center justify-center bg-gray-50">
                         <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
                              <div className="flex items-center mb-4">
                                   <div className="flex-shrink-0">
                                        <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                        </svg>
                                   </div>
                                   <div className="ml-3">
                                        <h3 className="text-lg font-medium text-gray-900">
                                             Something went wrong
                                        </h3>
                                   </div>
                              </div>

                              <div className="mb-4">
                                   <p className="text-sm text-gray-600">
                                        {this.state.error?.message || 'An unexpected error occurred'}
                                   </p>
                              </div>

                              <div className="flex space-x-3">
                                   <button
                                        onClick={() => window.location.reload()}
                                        className="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                   >
                                        Reload Page
                                   </button>
                                   <button
                                        onClick={() => this.setState({ hasError: false, error: null, errorInfo: null })}
                                        className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                                   >
                                        Try Again
                                   </button>
                              </div>
                         </div>
                    </div>
               );
          }

          return this.props.children;
     }
}