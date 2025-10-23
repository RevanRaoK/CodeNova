import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadIcon, FileTextIcon, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { useNotification } from '../contexts/NotificationContext';
import analysisService from '../services/analysisService';

/**
 * FileUploadIntegration - Integrated component that handles file upload and automatically
 * triggers analysis workflow, connecting upload -> analysis -> feedback flow
 */
const FileUploadIntegration = ({ onAnalysisComplete, autoNavigate = false }) => {
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [analysisResults, setAnalysisResults] = useState(null);
  const navigate = useNavigate();
  const { showSuccess, showError, showInfo, showLoading, removeNotification } = useNotification();

  // Handle file selection and upload
  const handleFileUpload = useCallback(async (files) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    const loadingId = showLoading(`Uploading ${files.length} file(s)...`);

    try {
      // Upload files
      const uploadResult = await analysisService.uploadMultipleFiles(files);
      
      setUploadedFiles(uploadResult.files || []);
      removeNotification(loadingId);
      showSuccess(`Successfully uploaded ${files.length} file(s)`);

      // Automatically start analysis
      setAnalyzing(true);
      const analysisLoadingId = showLoading('Analyzing uploaded files...');

      try {
        // Wait for batch analysis to complete
        const batchId = uploadResult.batch_id;
        const results = await pollBatchStatus(batchId);
        
        setAnalysisResults(results);
        removeNotification(analysisLoadingId);
        showSuccess('Analysis complete!');

        // Call completion callback
        if (onAnalysisComplete) {
          onAnalysisComplete(results);
        }

        // Auto-navigate to results if enabled
        if (autoNavigate) {
          navigate('/analysis-history');
        }
      } catch (analysisError) {
        removeNotification(analysisLoadingId);
        showError(`Analysis failed: ${analysisError.message}`);
      } finally {
        setAnalyzing(false);
      }
    } catch (uploadError) {
      removeNotification(loadingId);
      showError(`Upload failed: ${uploadError.message}`);
    } finally {
      setUploading(false);
    }
  }, [showSuccess, showError, showInfo, showLoading, removeNotification, onAnalysisComplete, autoNavigate, navigate]);

  // Poll batch status until complete
  const pollBatchStatus = async (batchId, maxAttempts = 30) => {
    for (let i = 0; i < maxAttempts; i++) {
      const status = await analysisService.getBatchStatus(batchId);
      
      if (status.status === 'completed') {
        return await analysisService.getBatchAnalysisResults(batchId);
      }
      
      if (status.status === 'failed') {
        throw new Error('Batch analysis failed');
      }

      // Wait 2 seconds before next poll
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    throw new Error('Analysis timeout');
  };

  // Handle drag and drop
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = Array.from(e.dataTransfer.files);
    handleFileUpload(files);
  }, [handleFileUpload]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const isProcessing = uploading || analyzing;

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-all
          ${isProcessing ? 'border-gray-300 bg-gray-50 cursor-not-allowed' : 'border-indigo-300 hover:border-indigo-400 cursor-pointer'}
        `}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => !isProcessing && document.getElementById('file-upload-input').click()}
      >
        <input
          id="file-upload-input"
          type="file"
          multiple
          className="hidden"
          onChange={(e) => handleFileUpload(Array.from(e.target.files))}
          disabled={isProcessing}
          accept=".js,.jsx,.ts,.tsx,.py,.java,.c,.cpp,.cs,.go,.rs,.php,.rb,.swift,.kt,.scala"
        />

        {isProcessing ? (
          <div className="flex flex-col items-center">
            <Loader2 className="h-12 w-12 text-indigo-600 animate-spin mb-4" />
            <p className="text-lg font-medium text-gray-900">
              {uploading ? 'Uploading files...' : 'Analyzing code...'}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Please wait while we process your files
            </p>
          </div>
        ) : (
          <>
            <UploadIcon className="mx-auto h-12 w-12 text-indigo-500 mb-4" />
            <p className="text-lg font-medium text-gray-900 mb-2">
              Upload files for analysis
            </p>
            <p className="text-sm text-gray-500">
              Drop files here or click to browse
            </p>
            <p className="text-xs text-gray-400 mt-2">
              Supported: JavaScript, TypeScript, Python, Java, C/C++, and more
            </p>
          </>
        )}
      </div>

      {/* Upload Status */}
      {uploadedFiles.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-900 mb-3">
            Uploaded Files ({uploadedFiles.length})
          </h3>
          <div className="space-y-2">
            {uploadedFiles.map((file, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center space-x-2">
                  <FileTextIcon className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-700">{file.filename}</span>
                </div>
                {file.status === 'completed' && (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                )}
                {file.status === 'failed' && (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                )}
                {file.status === 'processing' && (
                  <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Analysis Results Summary */}
      {analysisResults && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-900 mb-3">
            Analysis Complete
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-3 bg-green-50 rounded">
              <p className="text-2xl font-bold text-green-600">
                {analysisResults.successful_files || 0}
              </p>
              <p className="text-xs text-gray-600">Files Analyzed</p>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded">
              <p className="text-2xl font-bold text-blue-600">
                {analysisResults.total_issues || 0}
              </p>
              <p className="text-xs text-gray-600">Issues Found</p>
            </div>
          </div>
          <button
            onClick={() => navigate('/analysis-history')}
            className="mt-4 w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            View Detailed Results
          </button>
        </div>
      )}
    </div>
  );
};

export default FileUploadIntegration;
