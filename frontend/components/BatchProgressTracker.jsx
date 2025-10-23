import React, { useState, useEffect, useRef } from 'react';
import {
  CheckCircleIcon,
  AlertCircleIcon,
  XCircleIcon,
  ClockIcon,
  LoaderIcon,
  FileTextIcon,
  PauseCircleIcon,
  PlayCircleIcon,
} from 'lucide-react';
import { analysisService } from '../services/apiService';
import { formatFileSize } from '../utils/fileUtils';

export function BatchProgressTracker({
  batchId,
  onComplete,
  onError,
  autoRefresh = true,
  refreshInterval = 2000, // 2 seconds
  className = '',
}) {
  const [batchStatus, setBatchStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPaused, setIsPaused] = useState(false);
  const intervalRef = useRef(null);
  const mountedRef = useRef(true);

  // Fetch batch status
  const fetchBatchStatus = async () => {
    if (!batchId || isPaused) return;

    try {
      setError(null);
      const status = await analysisService.getBatchAnalysisStatus(batchId);
      
      if (mountedRef.current) {
        setBatchStatus(status);
        setIsLoading(false);

        // Check if batch is complete
        if (status.status === 'completed' || status.status === 'failed' || status.status === 'partial') {
          // Stop auto-refresh
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }

          // Notify parent component
          if (status.status === 'completed' || status.status === 'partial') {
            onComplete?.(status);
          } else if (status.status === 'failed') {
            onError?.(new Error('Batch processing failed'));
          }
        }
      }
    } catch (err) {
      console.error('Failed to fetch batch status:', err);
      if (mountedRef.current) {
        setError(err.message || 'Failed to fetch batch status');
        setIsLoading(false);
        onError?.(err);
      }
    }
  };

  // Start auto-refresh
  const startAutoRefresh = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    if (autoRefresh && !isPaused) {
      intervalRef.current = setInterval(fetchBatchStatus, refreshInterval);
    }
  };

  // Stop auto-refresh
  const stopAutoRefresh = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  // Toggle pause/resume
  const togglePause = () => {
    setIsPaused(!isPaused);
  };

  // Initialize and cleanup
  useEffect(() => {
    mountedRef.current = true;
    
    // Initial fetch
    fetchBatchStatus();

    // Setup auto-refresh
    if (autoRefresh && !isPaused) {
      intervalRef.current = setInterval(fetchBatchStatus, refreshInterval);
    }

    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [batchId]); // Only re-run when batchId changes

  // Handle pause/resume
  useEffect(() => {
    if (isPaused) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    } else if (autoRefresh && batchStatus && !['completed', 'failed', 'partial'].includes(batchStatus.status)) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      intervalRef.current = setInterval(fetchBatchStatus, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isPaused, autoRefresh, refreshInterval]);

  // Get status icon and color
  const getStatusIcon = (status, animated = false) => {
    const animationClass = animated ? 'animate-spin' : '';
    
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'processing':
        return <LoaderIcon className={`h-5 w-5 text-blue-500 ${animationClass}`} />;
      case 'partial':
        return <AlertCircleIcon className="h-5 w-5 text-orange-500" />;
      default:
        return <ClockIcon className={`h-5 w-5 text-gray-400 ${animationClass}`} />;
    }
  };

  // Get progress bar color
  const getProgressColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'processing':
        return 'bg-blue-500';
      case 'partial':
        return 'bg-orange-500';
      default:
        return 'bg-gray-400';
    }
  };

  // Get file status display
  const getFileStatusDisplay = (file) => {
    switch (file.status) {
      case 'completed':
        return (
          <div className="flex items-center space-x-2">
            <CheckCircleIcon className="h-4 w-4 text-green-500" />
            <span className="text-green-700 text-sm">
              {file.issues_count} issues found
            </span>
          </div>
        );
      case 'failed':
        return (
          <div className="flex items-center space-x-2">
            <XCircleIcon className="h-4 w-4 text-red-500" />
            <span className="text-red-700 text-sm">
              {file.error_message || 'Processing failed'}
            </span>
          </div>
        );
      case 'processing':
      case 'analyzing':
        return (
          <div className="flex items-center space-x-2">
            <LoaderIcon className="h-4 w-4 text-blue-500 animate-spin" />
            <span className="text-blue-700 text-sm">Processing...</span>
          </div>
        );
      default:
        return (
          <div className="flex items-center space-x-2">
            <ClockIcon className="h-4 w-4 text-gray-400" />
            <span className="text-gray-600 text-sm">Waiting...</span>
          </div>
        );
    }
  };

  if (isLoading && !batchStatus) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <LoaderIcon className="mx-auto h-8 w-8 text-blue-500 animate-spin" />
        <p className="mt-2 text-gray-600">Loading batch status...</p>
      </div>
    );
  }

  if (error && !batchStatus) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <XCircleIcon className="mx-auto h-8 w-8 text-red-500" />
        <p className="mt-2 text-red-600">Error: {error}</p>
        <button
          onClick={fetchBatchStatus}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!batchStatus) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <p className="text-gray-500">No batch status available</p>
      </div>
    );
  }

  const isComplete = ['completed', 'failed', 'partial'].includes(batchStatus.status);
  const progressPercentage = batchStatus.progress_percentage || 0;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Overall Progress */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            {getStatusIcon(batchStatus.status, !isComplete)}
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Batch Processing Progress
              </h3>
              <p className="text-sm text-gray-500">
                Batch ID: {batchStatus.batch_id}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {!isComplete && (
              <button
                onClick={togglePause}
                className="p-2 text-gray-400 hover:text-gray-600"
                title={isPaused ? 'Resume updates' : 'Pause updates'}
              >
                {isPaused ? (
                  <PlayCircleIcon className="h-5 w-5" />
                ) : (
                  <PauseCircleIcon className="h-5 w-5" />
                )}
              </button>
            )}
            <button
              onClick={fetchBatchStatus}
              disabled={isLoading}
              className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{Math.round(progressPercentage)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${getProgressColor(batchStatus.status)}`}
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {batchStatus.total_files}
            </div>
            <div className="text-sm text-gray-500">Total Files</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {batchStatus.processed_files}
            </div>
            <div className="text-sm text-gray-500">Processed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {batchStatus.successful_files}
            </div>
            <div className="text-sm text-gray-500">Successful</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {batchStatus.failed_files}
            </div>
            <div className="text-sm text-gray-500">Failed</div>
          </div>
        </div>

        {/* Timing Information */}
        {(batchStatus.estimated_completion_time || batchStatus.processing_time_seconds) && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex justify-between text-sm text-gray-600">
              {batchStatus.estimated_completion_time && !isComplete && (
                <span>
                  Estimated completion: {new Date(batchStatus.estimated_completion_time).toLocaleTimeString()}
                </span>
              )}
              {batchStatus.processing_time_seconds && (
                <span>
                  Processing time: {batchStatus.processing_time_seconds.toFixed(1)}s
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Individual File Progress */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h4 className="text-lg font-medium text-gray-900">
            File Processing Status
          </h4>
        </div>

        <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
          {batchStatus.files && batchStatus.files.length > 0 ? (
            batchStatus.files.map((file, index) => (
              <div key={index} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <FileTextIcon className="h-5 w-5 text-gray-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.filename}
                      </p>
                      <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                        <span>#{file.file_index + 1}</span>
                        {file.processing_time_seconds && (
                          <span>{file.processing_time_seconds.toFixed(1)}s</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex-shrink-0">
                    {getFileStatusDisplay(file)}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-gray-500">
              <FileTextIcon className="mx-auto h-8 w-8 text-gray-400 mb-2" />
              <p>No file information available</p>
            </div>
          )}
        </div>
      </div>

      {/* Status Message */}
      {isComplete && (
        <div className={`rounded-lg p-4 ${
          batchStatus.status === 'completed' ? 'bg-green-50 border border-green-200' :
          batchStatus.status === 'failed' ? 'bg-red-50 border border-red-200' :
          'bg-orange-50 border border-orange-200'
        }`}>
          <div className="flex items-center">
            {getStatusIcon(batchStatus.status)}
            <div className="ml-3">
              <h4 className={`text-sm font-medium ${
                batchStatus.status === 'completed' ? 'text-green-800' :
                batchStatus.status === 'failed' ? 'text-red-800' :
                'text-orange-800'
              }`}>
                {batchStatus.status === 'completed' && 'Batch processing completed successfully!'}
                {batchStatus.status === 'failed' && 'Batch processing failed'}
                {batchStatus.status === 'partial' && 'Batch processing completed with some failures'}
              </h4>
              <p className={`text-sm mt-1 ${
                batchStatus.status === 'completed' ? 'text-green-700' :
                batchStatus.status === 'failed' ? 'text-red-700' :
                'text-orange-700'
              }`}>
                {batchStatus.status === 'completed' && 
                  `All ${batchStatus.successful_files} files processed successfully.`}
                {batchStatus.status === 'failed' && 
                  `${batchStatus.failed_files} files failed to process.`}
                {batchStatus.status === 'partial' && 
                  `${batchStatus.successful_files} files succeeded, ${batchStatus.failed_files} failed.`}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}