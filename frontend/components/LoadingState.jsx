import React from 'react';
import { Loader2 } from 'lucide-react';

/**
 * LoadingState - Reusable loading state component with different variants
 * 
 * @param {Object} props
 * @param {string} props.variant - Loading variant: 'spinner', 'skeleton', 'pulse', 'dots'
 * @param {string} props.size - Size: 'sm', 'md', 'lg', 'xl'
 * @param {string} props.message - Optional loading message
 * @param {boolean} props.fullScreen - Whether to show full screen loading
 * @param {string} props.className - Additional CSS classes
 */
const LoadingState = ({ 
  variant = 'spinner', 
  size = 'md', 
  message = 'Loading...', 
  fullScreen = false,
  className = '' 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16'
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
    xl: 'text-lg'
  };

  const containerClass = fullScreen
    ? 'fixed inset-0 flex items-center justify-center bg-white bg-opacity-90 z-50'
    : 'flex items-center justify-center p-4';

  // Spinner variant
  if (variant === 'spinner') {
    return (
      <div className={`${containerClass} ${className}`}>
        <div className="flex flex-col items-center space-y-3">
          <Loader2 className={`${sizeClasses[size]} text-indigo-600 animate-spin`} />
          {message && (
            <p className={`${textSizeClasses[size]} text-gray-600 font-medium`}>
              {message}
            </p>
          )}
        </div>
      </div>
    );
  }

  // Dots variant
  if (variant === 'dots') {
    return (
      <div className={`${containerClass} ${className}`}>
        <div className="flex flex-col items-center space-y-3">
          <div className="flex space-x-2">
            <div className={`${sizeClasses[size]} bg-indigo-600 rounded-full animate-bounce`} style={{ animationDelay: '0ms' }}></div>
            <div className={`${sizeClasses[size]} bg-indigo-600 rounded-full animate-bounce`} style={{ animationDelay: '150ms' }}></div>
            <div className={`${sizeClasses[size]} bg-indigo-600 rounded-full animate-bounce`} style={{ animationDelay: '300ms' }}></div>
          </div>
          {message && (
            <p className={`${textSizeClasses[size]} text-gray-600 font-medium`}>
              {message}
            </p>
          )}
        </div>
      </div>
    );
  }

  // Pulse variant
  if (variant === 'pulse') {
    return (
      <div className={`${containerClass} ${className}`}>
        <div className="flex flex-col items-center space-y-3">
          <div className={`${sizeClasses[size]} bg-indigo-600 rounded-full animate-pulse`}></div>
          {message && (
            <p className={`${textSizeClasses[size]} text-gray-600 font-medium animate-pulse`}>
              {message}
            </p>
          )}
        </div>
      </div>
    );
  }

  // Skeleton variant
  if (variant === 'skeleton') {
    return (
      <div className={`${className} space-y-4 p-4`}>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  return null;
};

/**
 * EmptyState - Reusable empty state component
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.icon - Icon component to display
 * @param {string} props.title - Empty state title
 * @param {string} props.description - Empty state description
 * @param {React.ReactNode} props.action - Optional action button/component
 * @param {string} props.className - Additional CSS classes
 */
export const EmptyState = ({ 
  icon: Icon, 
  title, 
  description, 
  action,
  className = '' 
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center ${className}`}>
      {Icon && (
        <div className="mb-4">
          <Icon className="h-12 w-12 text-gray-400" />
        </div>
      )}
      {title && (
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {title}
        </h3>
      )}
      {description && (
        <p className="text-sm text-gray-600 max-w-md mb-4">
          {description}
        </p>
      )}
      {action && (
        <div className="mt-4">
          {action}
        </div>
      )}
    </div>
  );
};

/**
 * ErrorState - Reusable error state component
 * 
 * @param {Object} props
 * @param {string} props.title - Error title
 * @param {string} props.message - Error message
 * @param {Function} props.onRetry - Retry callback
 * @param {string} props.className - Additional CSS classes
 */
export const ErrorState = ({ 
  title = 'Something went wrong', 
  message, 
  onRetry,
  className = '' 
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center ${className}`}>
      <div className="mb-4">
        <svg
          className="h-12 w-12 text-red-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        {title}
      </h3>
      {message && (
        <p className="text-sm text-gray-600 max-w-md mb-4">
          {message}
        </p>
      )}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
};

export default LoadingState;
