import React, { useState, useRef, useCallback } from 'react';
import {
  UploadIcon,
  XIcon,
  FileTextIcon,
  CheckCircleIcon,
  AlertCircleIcon,
  LoaderIcon,
  TrashIcon,
  RefreshCwIcon
} from 'lucide-react';
import analysisService from '../services/analysisService.js';
import { useNotification } from '../contexts/NotificationContext';

/**
 * MultiFileUploadZone - Enhanced file upload component with drag-drop, progress tracking, and validation
 * Supports batch file uploads for code analysis
 */
const MultiFileUploadZone = ({ onUploadComplete, maxFiles = 10, maxSize = 5 * 1024 * 1024 }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [validationErrors, setValidationErrors] = useState({});
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const dragCounter = useRef(0);

  const { showSuccess, showError, showInfo, showLoading, removeNotification } = useNotification();

  // Handle file selection from input
  const handleFileSelect = useCallback((event) => {
    const selectedFiles = Array.from(event.target.files);
    addFiles(selectedFiles);
  }, []);

  // Add files to the upload queue with validation
  const addFiles = useCallback((newFiles) => {
    const validFiles = [];
    const newErrors = {};

    newFiles.forEach((file) => {
      try {
        // Check if file already exists
        if (files.some(f => f.name === file.name && f.size === file.size)) {
          newErrors[file.name] = 'File already added';
          return;
        }

        // Validate file
        analysisService.validateFile(file);

        // Check max files limit
        if (files.length + validFiles.length >= maxFiles) {
          newErrors[file.name] = `Maximum ${maxFiles} files allowed`;
          return;
        }

        validFiles.push({
          file,
          id: `${file.name}-${file.size}-${Date.now()}`,
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'pending',
          language: analysisService.detectLanguageFromFilename(file.name)
        });
      } catch (error) {
        newErrors[file.name] = error.message;
      }
    });

    setFiles(prev => [...prev, ...validFiles]);
    setValidationErrors(prev => ({ ...prev, ...newErrors }));
  }, [files, maxFiles]);

  // Drag and drop handlers
  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragOver(true);
    }
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setIsDragOver(false);
    }
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    dragCounter.current = 0;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files);
      addFiles(droppedFiles);
      e.dataTransfer.clearData();
    }
  }, [addFiles]);

  // Remove file from queue
  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      const file = files.find(f => f.id === fileId);
      if (file) {
        delete newErrors[file.name];
      }
      return newErrors;
    });
    setUploadProgress(prev => {
      const newProgress = { ...prev };
      delete newProgress[fileId];
      return newProgress;
    });
  };

  // Upload files with notifications
  const handleUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    const filesToUpload = files.filter(f => f.status === 'pending');

    const loadingId = showLoading(`Uploading ${filesToUpload.length} file(s)...`);

    try {
      // Upload files as a batch (async analysis)
      console.log('Uploading files:', filesToUpload.map(f => f.file.name));
      const result = await analysisService.uploadMultipleFiles(
        filesToUpload.map(f => f.file),
        {
          autoAnalyze: true // Process in background
        }
      );
      console.log('Upload result:', result);

      // Mark all as completed
      setFiles(prev => prev.map(f =>
        f.status === 'pending' ? { ...f, status: 'completed' } : f
      ));

      removeNotification(loadingId);

      // Show success notification with batch info
      const batchInfo = result.batchId ? ` (Batch ID: ${result.batchId.slice(0, 8)}...)` : '';
      showSuccess(
        `${filesToUpload.length} file(s) uploaded successfully${batchInfo}! Analysis is running in the background. Check your analysis history to see results.`,
        { duration: 10000 }
      );

      // Call callback if provided
      if (onUploadComplete) {
        onUploadComplete(result);
      }

      // Clear files after a delay
      setTimeout(() => {
        setFiles([]);
      }, 2000);

    } catch (error) {
      console.error('Upload failed:', error);
      removeNotification(loadingId);

      setFiles(prev => prev.map(f =>
        f.status === 'pending' ? { ...f, status: 'error', error: error.message } : f
      ));

      showError(error.message || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };



  // Open file dialog
  const openFileDialog = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Get status icon
  const getStatusIcon = (file) => {
    switch (file.status) {
      case 'uploading':
        return <LoaderIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <FileTextIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const canUpload = files.length > 0 && !uploading;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Upload Code Files</h2>
        <p className="text-sm text-gray-500 mt-1">Upload one or more files for analysis</p>
      </div>

      {/* Content */}
      <div>
        {/* Upload Zone */}
        <div
          className={`
              relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 mb-6
              ${isDragOver ? 'border-indigo-400 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'}
              ${uploading ? 'pointer-events-none opacity-75' : 'cursor-pointer'}
            `}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={!uploading ? openFileDialog : undefined}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileSelect}
            disabled={uploading}
            accept=".js,.jsx,.ts,.tsx,.py,.java,.c,.cpp,.cs,.go,.rs,.php,.rb,.swift,.kt,.scala"
          />

          <UploadIcon className={`mx-auto h-12 w-12 mb-4 ${isDragOver ? 'text-indigo-500' : 'text-gray-400'}`} />
          <p className="text-lg font-medium text-gray-900 mb-2">
            Drop files here or click to browse
          </p>
          <p className="text-sm text-gray-500">
            Maximum {maxFiles} files, up to 5MB each
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Supported: JavaScript, TypeScript, Python, Java, C/C++, and more
          </p>
        </div>

        {/* Validation Errors */}
        {Object.keys(validationErrors).length > 0 && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <h4 className="text-sm font-medium text-red-800 mb-2">File Validation Errors:</h4>
            <ul className="text-sm text-red-700 space-y-1">
              {Object.entries(validationErrors).map(([fileName, error]) => (
                <li key={fileName}>
                  <strong>{fileName}:</strong> {error}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* File List */}
        {files.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-900">
              Files to Upload ({files.length}/{maxFiles})
            </h4>

            {files.map((file) => (
              <div key={file.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                {getStatusIcon(file)}

                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(file.size)} • {file.language}
                  </p>

                  {/* Progress bar */}
                  {file.status === 'pending' && uploadProgress[file.id] && (
                    <div className="mt-2">
                      <div className="bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress[file.id]}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {uploadProgress[file.id]}% uploaded
                      </p>
                    </div>
                  )}

                  {/* Error message */}
                  {file.error && (
                    <p className="text-xs text-red-600 mt-1">{file.error}</p>
                  )}
                </div>

                {file.status === 'pending' && (
                  <button
                    onClick={() => removeFile(file.id)}
                    className="text-gray-400 hover:text-red-600 transition-colors"
                    title="Remove file"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-end mt-6 pt-6 border-t border-gray-200">
        <button
          onClick={handleUpload}
          disabled={!canUpload}
          className="px-6 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
        >
          {uploading && <LoaderIcon className="h-4 w-4 animate-spin" />}
          <span>{uploading ? 'Uploading...' : 'Upload & Queue Analysis'}</span>
        </button>
      </div>
    </div>
  );
};

export default MultiFileUploadZone;
