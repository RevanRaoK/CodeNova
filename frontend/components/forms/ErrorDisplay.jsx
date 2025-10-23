import React from 'react';
import { 
  AlertCircleIcon, 
  XCircleIcon, 
  WifiOffIcon, 
  RefreshCwIcon, 
  InfoIcon,
  CheckCircleIcon,
  AlertTriangle
} from 'lucide-react';
import { ERROR_TYPES, ERROR_SEVERITY } from '../../utils/errorHandler.js';

/**
 * Comprehensive error display component with different styles and actions
 */
const ErrorDisplay = ({
  error,
  onRetry,
  onDismiss,
  showRetry = true,
  showDismiss = true,
  showSuggestions = true,
  className = '',
  variant = 'default', // default, inline, toast, banner
  size = 'medium' // small, medium, large
}) => {
  if (!error) return null;

  // Get error properties
  const errorType = error.type || ERROR_TYPES.UNKNOWN;
  const errorSeverity = error.severity || ERROR_SEVERITY.MEDIUM;
  const userMessage = error.userMessage || error.message || 'An error occurred';
  const canRetry = error.retryable && onRetry && showRetry;
  const suggestions = error.suggestions || getErrorSuggestions(errorType);

  // Get icon based on error type and severity
  const getErrorIcon = () => {
    const iconProps = {
      className: getIconClasses()
    };

    switch (errorType) {
      case ERROR_TYPES.NETWORK:
        return <WifiOffIcon {...iconProps} />;
      case ERROR_TYPES.VALIDATION:
        return <AlertTriangle {...iconProps} />;
      case ERROR_TYPES.AUTHENTICATION:
      case ERROR_TYPES.AUTHORIZATION:
        return <XCircleIcon {...iconProps} />;
      case ERROR_TYPES.SERVER:
        return <AlertCircleIcon {...iconProps} />;
      default:
        return <AlertCircleIcon {...iconProps} />;
    }
  };

  // Get icon size classes
  const getIconClasses = () => {
    const baseClasses = 'flex-shrink-0';
    const sizeClasses = {
      small: 'h-4 w-4',
      medium: 'h-5 w-5',
      large: 'h-6 w-6'
    };
    const colorClasses = getColorClasses().icon;
    
    return `${baseClasses} ${sizeClasses[size]} ${colorClasses}`;
  };

  // Get color classes based on error severity
  const getColorClasses = () => {
    switch (errorSeverity) {
      case ERROR_SEVERITY.LOW:
        return {
          container: 'bg-blue-50 border-blue-200',
          icon: 'text-blue-500',
          title: 'text-blue-800',
          message: 'text-blue-700',
          button: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
        };
      case ERROR_SEVERITY.MEDIUM:
        return {
          container: 'bg-yellow-50 border-yellow-200',
          icon: 'text-yellow-500',
          title: 'text-yellow-800',
          message: 'text-yellow-700',
          button: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500'
        };
      case ERROR_SEVERITY.HIGH:
        return {
          container: 'bg-red-50 border-red-200',
          icon: 'text-red-500',
          title: 'text-red-800',
          message: 'text-red-700',
          button: 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
        };
      case ERROR_SEVERITY.CRITICAL:
        return {
          container: 'bg-red-100 border-red-300',
          icon: 'text-red-600',
          title: 'text-red-900',
          message: 'text-red-800',
          button: 'bg-red-700 hover:bg-red-800 focus:ring-red-600'
        };
      default:
        return {
          container: 'bg-gray-50 border-gray-200',
          icon: 'text-gray-500',
          title: 'text-gray-800',
          message: 'text-gray-700',
          button: 'bg-gray-600 hover:bg-gray-700 focus:ring-gray-500'
        };
    }
  };

  // Get container classes based on variant
  const getContainerClasses = () => {
    const colors = getColorClasses();
    const baseClasses = `border rounded-lg ${colors.container}`;
    
    const variantClasses = {
      default: 'p-4',
      inline: 'p-3',
      toast: 'p-4 shadow-lg',
      banner: 'p-3 border-l-4 border-r-0 border-t-0 border-b-0 rounded-none'
    };

    const sizeClasses = {
      small: 'text-sm',
      medium: 'text-base',
      large: 'text-lg'
    };

    return `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;
  };

  // Get error suggestions
  const getErrorSuggestions = (type) => {
    const suggestionMap = {
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
        'Reduce the frequency of your requests'
      ]
    };

    return suggestionMap[type] || [];
  };

  // Get error title
  const getErrorTitle = () => {
    const titleMap = {
      [ERROR_TYPES.NETWORK]: 'Connection Error',
      [ERROR_TYPES.VALIDATION]: 'Validation Error',
      [ERROR_TYPES.AUTHENTICATION]: 'Authentication Required',
      [ERROR_TYPES.AUTHORIZATION]: 'Access Denied',
      [ERROR_TYPES.SERVER]: 'Server Error',
      [ERROR_TYPES.RATE_LIMIT]: 'Rate Limit Exceeded',
      [ERROR_TYPES.FILE_UPLOAD]: 'Upload Error',
      [ERROR_TYPES.API_KEY]: 'API Key Error'
    };

    return titleMap[errorType] || 'Error';
  };

  const colors = getColorClasses();

  return (
    <div className={getContainerClasses()} role="alert">
      <div className="flex items-start">
        {/* Error icon */}
        <div className="flex-shrink-0">
          {getErrorIcon()}
        </div>

        {/* Error content */}
        <div className="ml-3 flex-1">
          {/* Error title and message */}
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className={`font-medium ${colors.title}`}>
                {getErrorTitle()}
              </h3>
              <p className={`mt-1 ${colors.message}`}>
                {userMessage}
              </p>
            </div>

            {/* Dismiss button */}
            {showDismiss && onDismiss && (
              <button
                type="button"
                onClick={onDismiss}
                className={`ml-3 -mx-1.5 -my-1.5 rounded-md p-1.5 inline-flex items-center justify-center ${colors.message} hover:bg-opacity-20 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent focus:ring-current`}
              >
                <span className="sr-only">Dismiss</span>
                <XCircleIcon className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Error suggestions */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="mt-3">
              <h4 className={`text-sm font-medium ${colors.title}`}>
                Suggestions:
              </h4>
              <ul className={`mt-1 text-sm ${colors.message} list-disc list-inside space-y-1`}>
                {suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Error details (for development) */}
          {process.env.NODE_ENV === 'development' && error.context && (
            <details className="mt-3">
              <summary className={`text-sm font-medium ${colors.title} cursor-pointer`}>
                Technical Details
              </summary>
              <pre className={`mt-2 text-xs ${colors.message} bg-white bg-opacity-50 p-2 rounded overflow-auto`}>
                {JSON.stringify(error.context, null, 2)}
              </pre>
            </details>
          )}

          {/* Action buttons */}
          {(canRetry || error.context?.requiresLogin) && (
            <div className="mt-4 flex space-x-3">
              {canRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className={`inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white ${colors.button} focus:outline-none focus:ring-2 focus:ring-offset-2`}
                >
                  <RefreshCwIcon className="h-4 w-4 mr-1" />
                  Try Again
                </button>
              )}

              {error.context?.requiresLogin && (
                <button
                  type="button"
                  onClick={() => window.location.href = '/login'}
                  className={`inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white ${colors.button} focus:outline-none focus:ring-2 focus:ring-offset-2`}
                >
                  Log In
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Success message component with similar styling
 */
export const SuccessDisplay = ({
  message,
  onDismiss,
  showDismiss = true,
  className = '',
  variant = 'default',
  size = 'medium'
}) => {
  if (!message) return null;

  const getContainerClasses = () => {
    const baseClasses = 'border rounded-lg bg-green-50 border-green-200';
    
    const variantClasses = {
      default: 'p-4',
      inline: 'p-3',
      toast: 'p-4 shadow-lg',
      banner: 'p-3 border-l-4 border-r-0 border-t-0 border-b-0 rounded-none'
    };

    const sizeClasses = {
      small: 'text-sm',
      medium: 'text-base',
      large: 'text-lg'
    };

    return `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;
  };

  const getIconClasses = () => {
    const sizeClasses = {
      small: 'h-4 w-4',
      medium: 'h-5 w-5',
      large: 'h-6 w-6'
    };
    
    return `flex-shrink-0 text-green-500 ${sizeClasses[size]}`;
  };

  return (
    <div className={getContainerClasses()} role="alert">
      <div className="flex items-start">
        <CheckCircleIcon className={getIconClasses()} />
        <div className="ml-3 flex-1">
          <p className="text-green-800">{message}</p>
        </div>
        {showDismiss && onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="ml-3 -mx-1.5 -my-1.5 rounded-md p-1.5 inline-flex items-center justify-center text-green-500 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-green-50 focus:ring-green-600"
          >
            <span className="sr-only">Dismiss</span>
            <XCircleIcon className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * Warning message component
 */
export const WarningDisplay = ({
  message,
  onDismiss,
  showDismiss = true,
  className = '',
  variant = 'default',
  size = 'medium'
}) => {
  if (!message) return null;

  const getContainerClasses = () => {
    const baseClasses = 'border rounded-lg bg-yellow-50 border-yellow-200';
    
    const variantClasses = {
      default: 'p-4',
      inline: 'p-3',
      toast: 'p-4 shadow-lg',
      banner: 'p-3 border-l-4 border-r-0 border-t-0 border-b-0 rounded-none'
    };

    const sizeClasses = {
      small: 'text-sm',
      medium: 'text-base',
      large: 'text-lg'
    };

    return `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;
  };

  const getIconClasses = () => {
    const sizeClasses = {
      small: 'h-4 w-4',
      medium: 'h-5 w-5',
      large: 'h-6 w-6'
    };
    
    return `flex-shrink-0 text-yellow-500 ${sizeClasses[size]}`;
  };

  return (
    <div className={getContainerClasses()} role="alert">
      <div className="flex items-start">
        <AlertTriangle className={getIconClasses()} />
        <div className="ml-3 flex-1">
          <p className="text-yellow-800">{message}</p>
        </div>
        {showDismiss && onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="ml-3 -mx-1.5 -my-1.5 rounded-md p-1.5 inline-flex items-center justify-center text-yellow-500 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-yellow-50 focus:ring-yellow-600"
          >
            <span className="sr-only">Dismiss</span>
            <XCircleIcon className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorDisplay;