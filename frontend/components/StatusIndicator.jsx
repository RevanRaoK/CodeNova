import React from 'react';
import { 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Clock,
  AlertCircle
} from 'lucide-react';

const StatusIndicator = ({ 
  status, 
  message, 
  progress = 0, 
  showProgress = false,
  size = 'md',
  className = ''
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'loading':
      case 'analyzing':
      case 'processing':
        return {
          icon: Loader2,
          iconClass: 'text-blue-500 animate-spin',
          bgClass: 'bg-blue-50 border-blue-200',
          textClass: 'text-blue-800',
          progressClass: 'bg-blue-600'
        };
      case 'success':
      case 'completed':
        return {
          icon: CheckCircle,
          iconClass: 'text-green-500',
          bgClass: 'bg-green-50 border-green-200',
          textClass: 'text-green-800',
          progressClass: 'bg-green-600'
        };
      case 'error':
      case 'failed':
        return {
          icon: XCircle,
          iconClass: 'text-red-500',
          bgClass: 'bg-red-50 border-red-200',
          textClass: 'text-red-800',
          progressClass: 'bg-red-600'
        };
      case 'warning':
        return {
          icon: AlertCircle,
          iconClass: 'text-yellow-500',
          bgClass: 'bg-yellow-50 border-yellow-200',
          textClass: 'text-yellow-800',
          progressClass: 'bg-yellow-600'
        };
      case 'pending':
      case 'waiting':
        return {
          icon: Clock,
          iconClass: 'text-gray-500',
          bgClass: 'bg-gray-50 border-gray-200',
          textClass: 'text-gray-800',
          progressClass: 'bg-gray-600'
        };
      default:
        return {
          icon: Clock,
          iconClass: 'text-gray-500',
          bgClass: 'bg-gray-50 border-gray-200',
          textClass: 'text-gray-800',
          progressClass: 'bg-gray-600'
        };
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          container: 'p-3',
          icon: 'h-4 w-4',
          text: 'text-sm',
          progress: 'h-1'
        };
      case 'lg':
        return {
          container: 'p-6',
          icon: 'h-6 w-6',
          text: 'text-base',
          progress: 'h-3'
        };
      default: // md
        return {
          container: 'p-4',
          icon: 'h-5 w-5',
          text: 'text-sm',
          progress: 'h-2'
        };
    }
  };

  const config = getStatusConfig();
  const sizeClasses = getSizeClasses();
  const IconComponent = config.icon;

  return (
    <div className={`
      border rounded-lg ${config.bgClass} ${sizeClasses.container} ${className}
    `}>
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <IconComponent className={`${sizeClasses.icon} ${config.iconClass}`} />
        </div>
        <div className="ml-3 flex-1">
          <p className={`font-medium ${config.textClass} ${sizeClasses.text}`}>
            {message}
          </p>
          {showProgress && (
            <div className="mt-2">
              <div className={`bg-gray-200 rounded-full ${sizeClasses.progress}`}>
                <div
                  className={`${config.progressClass} ${sizeClasses.progress} rounded-full transition-all duration-300 ease-out`}
                  style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                />
              </div>
              <p className="text-xs text-gray-600 mt-1">
                {Math.round(progress)}% complete
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatusIndicator;