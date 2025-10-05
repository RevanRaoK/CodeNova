import React, { useState, useRef, useCallback } from 'react';
import {
     UploadIcon,
     XIcon,
     FileTextIcon,
     ImageIcon,
     FileIcon,
     CheckCircleIcon,
     AlertCircleIcon,
     LoaderIcon,
     TrashIcon
} from 'lucide-react';
import fileService from '../services/fileService.js';
import { validateFile, formatFileSize, isDragAndDropSupported } from '../utils/fileUtils.ts';

const FileUploadComponent = ({ onClose, onSuccess, maxFiles = 10 }) => {
     const [files, setFiles] = useState([]);
     const [uploading, setUploading] = useState(false);
     const [uploadProgress, setUploadProgress] = useState({});
     const [errors, setErrors] = useState({});
     const [isDragOver, setIsDragOver] = useState(false);
     const fileInputRef = useRef(null);
     const dragCounter = useRef(0);

     // Check if drag and drop is supported
     const dragDropSupported = isDragAndDropSupported();

     // Handle file selection from input
     const handleFileSelect = useCallback((event) => {
          const selectedFiles = Array.from(event.target.files);
          addFiles(selectedFiles);
     }, []);

     // Add files to the upload queue
     const addFiles = useCallback((newFiles) => {
          const validFiles = [];
          const newErrors = {};

          newFiles.forEach((file) => {
               // Check if file already exists
               if (files.some(f => f.name === file.name && f.size === file.size)) {
                    newErrors[file.name] = 'File already added';
                    return;
               }

               // Validate file
               const validation = validateFile(file);
               if (!validation.isValid) {
                    newErrors[file.name] = validation.error;
                    return;
               }

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
                    status: 'pending' // pending, uploading, completed, error
               });
          });

          setFiles(prev => [...prev, ...validFiles]);
          setErrors(prev => ({ ...prev, ...newErrors }));
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
          setErrors(prev => {
               const newErrors = { ...prev };
               const file = files.find(f => f.id === fileId);
               if (file) {
                    delete newErrors[file.name];
               }
               return newErrors;
          });
     };

     // Upload files
     const handleUpload = async () => {
          if (files.length === 0) return;

          setUploading(true);
          const uploadedFiles = [];
          const failedFiles = [];

          try {
               // Upload files one by one to track individual progress
               for (const fileItem of files) {
                    if (fileItem.status === 'completed') continue;

                    try {
                         // Update status to uploading
                         setFiles(prev => prev.map(f =>
                              f.id === fileItem.id ? { ...f, status: 'uploading' } : f
                         ));

                         // Upload file with progress tracking
                         const result = await fileService.uploadFile(fileItem.file, {
                              onProgress: (progress) => {
                                   setUploadProgress(prev => ({
                                        ...prev,
                                        [fileItem.id]: progress
                                   }));
                              }
                         });

                         // Update status to completed
                         setFiles(prev => prev.map(f =>
                              f.id === fileItem.id ? { ...f, status: 'completed', result } : f
                         ));

                         uploadedFiles.push(result);

                    } catch (error) {
                         console.error(`Failed to upload ${fileItem.name}:`, error);

                         // Update status to error
                         setFiles(prev => prev.map(f =>
                              f.id === fileItem.id ? { ...f, status: 'error' } : f
                         ));

                         setErrors(prev => ({
                              ...prev,
                              [fileItem.name]: error.response?.data?.message || 'Upload failed'
                         }));

                         failedFiles.push(fileItem);
                    }
               }

               // Call success callback if any files were uploaded
               if (uploadedFiles.length > 0) {
                    onSuccess(uploadedFiles);
               }

               // If all files failed, don't close the modal
               if (failedFiles.length === files.length) {
                    setUploading(false);
                    return;
               }

          } catch (error) {
               console.error('Upload process failed:', error);
               setErrors(prev => ({
                    ...prev,
                    general: 'Upload process failed. Please try again.'
               }));
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

     // Get file icon
     const getFileIcon = (file) => {
          const extension = file.name.split('.').pop()?.toLowerCase();

          if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(extension)) {
               return <ImageIcon className="h-6 w-6 text-green-500" />;
          }

          if (['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'cpp', 'c', 'cs', 'go', 'rs', 'php', 'rb'].includes(extension)) {
               return <FileTextIcon className="h-6 w-6 text-blue-500" />;
          }

          return <FileIcon className="h-6 w-6 text-gray-500" />;
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
                    return null;
          }
     };

     const hasErrors = Object.keys(errors).length > 0;
     const canUpload = files.length > 0 && !uploading;
     const allCompleted = files.length > 0 && files.every(f => f.status === 'completed');

     return (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
               <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-gray-200">
                         <h2 className="text-xl font-semibold text-gray-900">Upload Files</h2>
                         <button
                              onClick={onClose}
                              className="text-gray-400 hover:text-gray-600 transition-colors"
                         >
                              <XIcon className="h-6 w-6" />
                         </button>
                    </div>

                    {/* Content */}
                    <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
                         {/* Upload Zone */}
                         <div
                              className={`
              relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 mb-6
              ${isDragOver
                                        ? 'border-indigo-400 bg-indigo-50'
                                        : 'border-gray-300 hover:border-gray-400'
                                   }
              ${uploading ? 'pointer-events-none opacity-75' : 'cursor-pointer'}
            `}
                              onDragEnter={dragDropSupported ? handleDragEnter : undefined}
                              onDragLeave={dragDropSupported ? handleDragLeave : undefined}
                              onDragOver={dragDropSupported ? handleDragOver : undefined}
                              onDrop={dragDropSupported ? handleDrop : undefined}
                              onClick={!uploading ? openFileDialog : undefined}
                         >
                              {/* Hidden file input */}
                              <input
                                   ref={fileInputRef}
                                   type="file"
                                   multiple
                                   className="hidden"
                                   onChange={handleFileSelect}
                                   disabled={uploading}
                              />

                              <UploadIcon className={`mx-auto h-12 w-12 mb-4 ${isDragOver ? 'text-indigo-500' : 'text-gray-400'}`} />
                              <p className="text-lg font-medium text-gray-900 mb-2">
                                   {dragDropSupported ? 'Drop files here or click to browse' : 'Click to select files'}
                              </p>
                              <p className="text-sm text-gray-500">
                                   Maximum {maxFiles} files, up to 1MB each
                              </p>
                         </div>

                         {/* Error Messages */}
                         {hasErrors && (
                              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                                   <h4 className="text-sm font-medium text-red-800 mb-2">Upload Errors:</h4>
                                   <ul className="text-sm text-red-700 space-y-1">
                                        {Object.entries(errors).map(([fileName, error]) => (
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
                                             {getFileIcon(file)}

                                             <div className="flex-1 min-w-0">
                                                  <p className="text-sm font-medium text-gray-900 truncate">
                                                       {file.name}
                                                  </p>
                                                  <p className="text-xs text-gray-500">
                                                       {formatFileSize(file.size)}
                                                  </p>

                                                  {/* Progress bar for uploading files */}
                                                  {file.status === 'uploading' && uploadProgress[file.id] && (
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
                                             </div>

                                             <div className="flex items-center space-x-2">
                                                  {getStatusIcon(file)}

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
                                        </div>
                                   ))}
                              </div>
                         )}
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
                         <div className="text-sm text-gray-600">
                              {files.length > 0 && (
                                   <span>
                                        {files.filter(f => f.status === 'completed').length} of {files.length} files uploaded
                                   </span>
                              )}
                         </div>

                         <div className="flex space-x-3">
                              <button
                                   onClick={onClose}
                                   className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                              >
                                   {allCompleted ? 'Close' : 'Cancel'}
                              </button>

                              {!allCompleted && (
                                   <button
                                        onClick={handleUpload}
                                        disabled={!canUpload}
                                        className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                                   >
                                        {uploading && <LoaderIcon className="h-4 w-4 animate-spin" />}
                                        <span>{uploading ? 'Uploading...' : 'Upload Files'}</span>
                                   </button>
                              )}
                         </div>
                    </div>
               </div>
          </div>
     );
};

export default FileUploadComponent;