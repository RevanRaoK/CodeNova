import React, { useState, useEffect } from 'react';
import { CheckCircleIcon, AlertCircleIcon, LoaderIcon, FileTextIcon, XIcon } from 'lucide-react';
import analysisService from '../services/analysisService.js';

/**
 * BatchUploadProgress - Real-time progress tracker for batch file uploads and analysis
 * Displays status updates using polling
 */
const BatchUploadProgress = ({ batchId, onComplete, onClose }) => {
  const [batchStatus, setBatchStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pollingInterval, setPollingInterval] = useState(null);

  // Fetch batch status
  const fetchBatchStatus = async () => {
    try {
      const status = await analysisService.getBatchAnalysisStatus(batchId);
      setBatchStatus(status);
      setError(null);

      // Stop polling if batch is completed or failed
      if (status.status === 'completed' || status.status === 'failed') {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        
        if (status.status === 'completed' && onComplete) {
          onComplete(status);
        }
      }
    } catch (err) {
      console.error('Failed to fetch batch status:', err);
      setError(err.message || 'Failed to fetch batch status');
    } finally {
      setLoading(false);
    }
  };

  // Start polling for status updates
  useEffect(() => {
    fetchBatchStatus();

    const interval = setInterval(() => {
      fetchBatchStatus();
    }, 2000); // Poll every 2 seconds

    setPollingInterval(interval);

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [batchId]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'processing':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'queued':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getFileStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <AlertCircleIcon className="h-5 w-5 text-red-500" />;
      case 'processing':
        return <LoaderIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <FileTextIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const formatTime = (seconds) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (loading && !batchStatus) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
          <div className="flex items-center justify-center space-x-3">
            <LoaderIcon className="h-6 w-6 text-indigo-600 animate-spin" />
            <span className="text-lg text-gray-700">Loading batch status...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-red-600">Error</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <XIcon className="h-6 w-6" />
            </button>
          </div>
          <div className="flex items-start space-x-3 text-red-600">
            <AlertCircleIcon className="h-5 w-5 mt-0.5 flex-shrink-0" />
            <p>{error}</p>
          </div>
          <div className="mt-4 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!batchStatus) return null;

  const progressPercentage = batchStatus.progress_percentage || 0;
  const isCompleted = batchStatus.status === 'completed';
  const isFailed = batchStatus.status === 'failed';
  const isProcessing = batchStatus.status === 'processing';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Batch Analysis Progress</h2>
            <p className="text-sm text-gray-500 mt-1">Batch ID: {batchStatus.batch_id}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isProcessing}
          >
            <XIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {/* Overall Status */}
          <div className={`p-4 rounded-lg border mb-6 ${getStatusColor(batchStatus.status)}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">Status: {batchStatus.status.toUpperCase()}</span>
              {isProcessing && <LoaderIcon className="h-5 w-5 animate-spin" />}
              {isCompleted && <CheckCircleIcon className="h-5 w-5" />}
              {isFailed && <AlertCircleIcon className="h-5 w-5" />}
            </div>
            
            {/* Progress Bar */}
            <div className="mt-3">
              <div className="flex items-center justify-between text-sm mb-1">
                <span>Progress</span>
                <span>{progressPercentage}%</span>
              </div>
              <div className="bg-white bg-opacity-50 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    isCompleted ? 'bg-green-500' : isFailed ? 'bg-red-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mt-4 text-sm">
              <div>
                <p className="font-medium">Total Files</p>
                <p className="text-2xl">{batchStatus.total_files}</p>
              </div>
              <div>
                <p className="font-medium">Processed</p>
                <p className="text-2xl">{batchStatus.processed_files}</p>
              </div>
              <div>
                <p className="font-medium">Successful</p>
                <p className="text-2xl text-green-600">{batchStatus.successful_files}</p>
              </div>
            </div>

            {batchStatus.processing_time_seconds && (
              <div className="mt-3 text-sm">
                <span className="font-medium">Processing Time:</span> {formatTime(batchStatus.processing_time_seconds)}
              </div>
            )}

            {batchStatus.estimated_completion_time && isProcessing && (
              <div className="mt-2 text-sm">
                <span className="font-medium">Estimated Completion:</span> {new Date(batchStatus.estimated_completion_time).toLocaleTimeString()}
              </div>
            )}
          </div>

          {/* File List */}
          {batchStatus.files && batchStatus.files.length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Files</h3>
              <div className="space-y-2">
                {batchStatus.files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-center space-x-3 flex-1 min-w-0">
                      {getFileStatusIcon(file.status)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {file.filename}
                        </p>
                        <p className="text-xs text-gray-500">
                          {file.language} • {file.status}
                        </p>
                        {file.error_message && (
                          <p className="text-xs text-red-600 mt-1">{file.error_message}</p>
                        )}
                      </div>
                    </div>

                    {file.status === 'completed' && (
                      <div className="text-right text-xs text-gray-600">
                        <p>{file.issues_count || 0} issues</p>
                        {file.processing_time_seconds && (
                          <p>{formatTime(file.processing_time_seconds)}</p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end p-6 border-t border-gray-200 bg-gray-50">
          {isCompleted && (
            <button
              onClick={() => onComplete && onComplete(batchStatus)}
              className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors mr-3"
            >
              View Results
            </button>
          )}
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            {isProcessing ? 'Processing...' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BatchUploadProgress;
