import React, { useState } from 'react';
import { useNotification } from '../contexts/NotificationContext';
import StatusIndicator from '../components/StatusIndicator';

export function NotificationDemo() {
  const { 
    showSuccess, 
    showError, 
    showWarning, 
    showInfo, 
    showLoading, 
    showConfirmation,
    removeNotification 
  } = useNotification();
  
  const [analysisStatus, setAnalysisStatus] = useState('pending');
  const [progress, setProgress] = useState(0);

  const handleShowToasts = () => {
    showSuccess('This is a success message!', { title: 'Success' });
    setTimeout(() => showError('This is an error message!', { title: 'Error' }), 500);
    setTimeout(() => showWarning('This is a warning message!', { title: 'Warning' }), 1000);
    setTimeout(() => showInfo('This is an info message!', { title: 'Information' }), 1500);
  };

  const handleShowLoadingToast = () => {
    const loadingId = showLoading('Processing your request...', { 
      title: 'Please Wait' 
    });
    
    setTimeout(() => {
      removeNotification(loadingId);
      showSuccess('Processing completed successfully!');
    }, 3000);
  };

  const handleShowConfirmation = async () => {
    const confirmed = await showConfirmation({
      title: 'Delete Item',
      message: 'Are you sure you want to delete this item? This action cannot be undone.',
      confirmText: 'Delete',
      cancelText: 'Cancel',
      type: 'danger'
    });
    
    if (confirmed) {
      showSuccess('Item deleted successfully!');
    } else {
      showInfo('Deletion cancelled.');
    }
  };

  const handleAnalysisDemo = () => {
    setAnalysisStatus('analyzing');
    setProgress(0);
    
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + Math.random() * 15;
        if (newProgress >= 100) {
          clearInterval(interval);
          setAnalysisStatus('completed');
          setProgress(100);
          showSuccess('Code analysis completed successfully!');
          return 100;
        }
        return newProgress;
      });
    }, 300);
  };

  const resetAnalysis = () => {
    setAnalysisStatus('pending');
    setProgress(0);
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">Notification System Demo</h1>
      
      <div className="space-y-8">
        {/* Toast Notifications Section */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-xl font-semibold mb-4">Toast Notifications</h2>
          <p className="text-gray-600 mb-4">
            Toast notifications appear in the top-right corner and auto-dismiss after a few seconds.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleShowToasts}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Show All Toast Types
            </button>
            <button
              onClick={handleShowLoadingToast}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
            >
              Show Loading Toast
            </button>
          </div>
        </div>

        {/* Confirmation Dialogs Section */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-xl font-semibold mb-4">Confirmation Dialogs</h2>
          <p className="text-gray-600 mb-4">
            Confirmation dialogs require user interaction before proceeding with important actions.
          </p>
          <button
            onClick={handleShowConfirmation}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Show Confirmation Dialog
          </button>
        </div>

        {/* Status Indicators Section */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-xl font-semibold mb-4">Status Indicators</h2>
          <p className="text-gray-600 mb-4">
            Status indicators show the current state of operations with progress tracking.
          </p>
          
          <div className="space-y-4">
            <StatusIndicator
              status={analysisStatus}
              message={
                analysisStatus === 'pending' ? 'Ready to analyze code' :
                analysisStatus === 'analyzing' ? 'Analyzing your code...' :
                'Analysis completed successfully!'
              }
              progress={progress}
              showProgress={analysisStatus === 'analyzing'}
              size="md"
            />
            
            <div className="flex gap-3">
              <button
                onClick={handleAnalysisDemo}
                disabled={analysisStatus === 'analyzing'}
                className={`px-4 py-2 rounded-md transition-colors ${
                  analysisStatus === 'analyzing'
                    ? 'bg-gray-400 cursor-not-allowed text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {analysisStatus === 'analyzing' ? 'Analyzing...' : 'Start Analysis'}
              </button>
              
              {analysisStatus !== 'pending' && (
                <button
                  onClick={resetAnalysis}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                >
                  Reset
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Status Examples Section */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-xl font-semibold mb-4">Status Indicator Examples</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <StatusIndicator
              status="success"
              message="Operation completed successfully"
              size="sm"
            />
            <StatusIndicator
              status="error"
              message="Operation failed with errors"
              size="sm"
            />
            <StatusIndicator
              status="warning"
              message="Operation completed with warnings"
              size="sm"
            />
            <StatusIndicator
              status="loading"
              message="Processing request..."
              size="sm"
            />
          </div>
        </div>

        {/* Integration Examples */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-xl font-semibold mb-4">Integration Examples</h2>
          <p className="text-gray-600 mb-4">
            These notifications are already integrated into the application:
          </p>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            <li><strong>Authentication:</strong> Login/logout success and error messages</li>
            <li><strong>Code Analysis:</strong> Analysis progress, success, and error notifications</li>
            <li><strong>File Upload:</strong> Upload progress and completion notifications</li>
            <li><strong>Form Validation:</strong> Error messages for invalid inputs</li>
            <li><strong>Confirmation Dialogs:</strong> Before replacing code or deleting data</li>
          </ul>
        </div>
      </div>
    </div>
  );
}