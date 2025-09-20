import React, { useEffect, useState } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Info,
  X,
  Loader2
} from 'lucide-react';

const Toast = ({ notification, onRemove }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    // Trigger entrance animation
    const timer = setTimeout(() => setIsVisible(true), 10);
    return () => clearTimeout(timer);
  }, []);

  const handleRemove = () => {
    setIsExiting(true);
    setTimeout(() => {
      onRemove(notification.id);
    }, 300); // Match exit animation duration
  };

  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-400" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-400" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-400" />;
      case 'loading':
        return <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />;
      default:
        return <Info className="h-5 w-5 text-blue-400" />;
    }
  };

  const getBackgroundColor = () => {
    switch (notification.type) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'loading':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  const getTextColor = () => {
    switch (notification.type) {
      case 'success':
        return 'text-green-800';
      case 'error':
        return 'text-red-800';
      case 'warning':
        return 'text-yellow-800';
      case 'loading':
        return 'text-blue-800';
      default:
        return 'text-blue-800';
    }
  };

  return (
    <div
      className={`
        max-w-sm w-full border rounded-lg shadow-lg pointer-events-auto
        transform transition-all duration-300 ease-in-out
        ${getBackgroundColor()}
        ${isVisible && !isExiting 
          ? 'translate-x-0 opacity-100' 
          : isExiting 
          ? 'translate-x-full opacity-0' 
          : 'translate-x-full opacity-0'
        }
      `}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            {getIcon()}
          </div>
          <div className="ml-3 w-0 flex-1">
            {notification.title && (
              <p className={`text-sm font-medium ${getTextColor()}`}>
                {notification.title}
              </p>
            )}
            <p className={`text-sm ${notification.title ? 'mt-1' : ''} ${getTextColor()}`}>
              {notification.message}
            </p>
            {notification.action && (
              <div className="mt-3">
                <button
                  onClick={notification.action.onClick}
                  className={`
                    text-sm font-medium underline hover:no-underline
                    ${notification.type === 'success' ? 'text-green-600 hover:text-green-500' :
                      notification.type === 'error' ? 'text-red-600 hover:text-red-500' :
                      notification.type === 'warning' ? 'text-yellow-600 hover:text-yellow-500' :
                      'text-blue-600 hover:text-blue-500'
                    }
                  `}
                >
                  {notification.action.label}
                </button>
              </div>
            )}
          </div>
          <div className="ml-4 flex-shrink-0 flex">
            <button
              onClick={handleRemove}
              className={`
                rounded-md inline-flex focus:outline-none focus:ring-2 focus:ring-offset-2
                ${notification.type === 'success' ? 'text-green-400 hover:text-green-500 focus:ring-green-500' :
                  notification.type === 'error' ? 'text-red-400 hover:text-red-500 focus:ring-red-500' :
                  notification.type === 'warning' ? 'text-yellow-400 hover:text-yellow-500 focus:ring-yellow-500' :
                  'text-blue-400 hover:text-blue-500 focus:ring-blue-500'
                }
              `}
            >
              <span className="sr-only">Close</span>
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Toast;