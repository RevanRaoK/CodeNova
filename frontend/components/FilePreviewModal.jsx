import React, { useState, useEffect } from 'react';
import {
     XIcon,
     DownloadIcon,
     FileTextIcon,
     ImageIcon,
     FileIcon,
     LoaderIcon,
     AlertCircleIcon,
     EyeOffIcon,
     ZoomInIcon,
     ZoomOutIcon
} from 'lucide-react';
import fileService from '../services/fileService.js';
import { formatFileSize } from '../utils/fileUtils.ts';

const FilePreviewModal = ({ file, onClose }) => {
     const [previewData, setPreviewData] = useState(null);
     const [loading, setLoading] = useState(true);
     const [error, setError] = useState(null);
     const [imageZoom, setImageZoom] = useState(1);

     // Load preview data
     useEffect(() => {
          const loadPreview = async () => {
               try {
                    setLoading(true);
                    setError(null);

                    // Get file preview
                    const preview = await fileService.getFilePreview(file.id, {
                         maxLines: 1000 // Limit preview to 1000 lines for performance
                    });

                    setPreviewData(preview);
               } catch (err) {
                    console.error('Failed to load preview:', err);
                    setError('Failed to load file preview');
               } finally {
                    setLoading(false);
               }
          };

          if (file) {
               loadPreview();
          }
     }, [file]);

     // Handle download
     const handleDownload = async () => {
          try {
               const downloadData = await fileService.getDownloadUrl(file.id);

               // Create temporary link and trigger download
               const link = document.createElement('a');
               link.href = downloadData.url;
               link.download = file.filename;
               document.body.appendChild(link);
               link.click();
               document.body.removeChild(link);
          } catch (err) {
               console.error('Download failed:', err);
               setError('Failed to download file');
          }
     };

     // Get file type for preview
     const getFileType = () => {
          const extension = file.filename.split('.').pop()?.toLowerCase();

          if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(extension)) {
               return 'image';
          }

          if (['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'cpp', 'c', 'cs', 'go', 'rs', 'php', 'rb', 'html', 'css', 'scss', 'json', 'xml', 'yaml', 'md', 'sql', 'sh'].includes(extension)) {
               return 'code';
          }

          if (['txt', 'log', 'csv'].includes(extension)) {
               return 'text';
          }

          return 'other';
     };

     // Get language for syntax highlighting
     const getLanguage = () => {
          const extension = file.filename.split('.').pop()?.toLowerCase();
          const languageMap = {
               'js': 'javascript',
               'jsx': 'javascript',
               'ts': 'typescript',
               'tsx': 'typescript',
               'py': 'python',
               'java': 'java',
               'cpp': 'cpp',
               'c': 'c',
               'cs': 'csharp',
               'go': 'go',
               'rs': 'rust',
               'php': 'php',
               'rb': 'ruby',
               'html': 'html',
               'css': 'css',
               'scss': 'scss',
               'json': 'json',
               'xml': 'xml',
               'yaml': 'yaml',
               'yml': 'yaml',
               'md': 'markdown',
               'sql': 'sql',
               'sh': 'bash'
          };

          return languageMap[extension] || 'text';
     };

     // Render preview content based on file type
     const renderPreviewContent = () => {
          if (loading) {
               return (
                    <div className="flex items-center justify-center h-64">
                         <div className="text-center">
                              <LoaderIcon className="h-8 w-8 text-indigo-600 animate-spin mx-auto mb-2" />
                              <p className="text-gray-600">Loading preview...</p>
                         </div>
                    </div>
               );
          }

          if (error) {
               return (
                    <div className="flex items-center justify-center h-64">
                         <div className="text-center">
                              <AlertCircleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
                              <p className="text-red-600 mb-4">{error}</p>
                              <button
                                   onClick={handleDownload}
                                   className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                              >
                                   Download File
                              </button>
                         </div>
                    </div>
               );
          }

          if (!previewData) {
               return (
                    <div className="flex items-center justify-center h-64">
                         <div className="text-center">
                              <EyeOffIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                              <p className="text-gray-600 mb-4">Preview not available for this file type</p>
                              <button
                                   onClick={handleDownload}
                                   className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                              >
                                   Download File
                              </button>
                         </div>
                    </div>
               );
          }

          const fileType = getFileType();

          switch (fileType) {
               case 'image':
                    return (
                         <div className="text-center">
                              <div className="mb-4 flex items-center justify-center space-x-2">
                                   <button
                                        onClick={() => setImageZoom(Math.max(0.25, imageZoom - 0.25))}
                                        className="p-2 text-gray-600 hover:text-gray-800 border rounded"
                                        title="Zoom Out"
                                   >
                                        <ZoomOutIcon className="h-4 w-4" />
                                   </button>
                                   <span className="text-sm text-gray-600">{Math.round(imageZoom * 100)}%</span>
                                   <button
                                        onClick={() => setImageZoom(Math.min(3, imageZoom + 0.25))}
                                        className="p-2 text-gray-600 hover:text-gray-800 border rounded"
                                        title="Zoom In"
                                   >
                                        <ZoomInIcon className="h-4 w-4" />
                                   </button>
                              </div>
                              <div className="overflow-auto max-h-96">
                                   <img
                                        src={previewData.url || previewData.content}
                                        alt={file.filename}
                                        style={{ transform: `scale(${imageZoom})`, transformOrigin: 'center' }}
                                        className="max-w-full h-auto"
                                        onError={() => setError('Failed to load image')}
                                   />
                              </div>
                         </div>
                    );

               case 'code':
               case 'text':
                    return (
                         <div className="bg-gray-900 rounded-lg overflow-hidden">
                              <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
                                   <span className="text-sm text-gray-300">{getLanguage()}</span>
                                   <span className="text-sm text-gray-400">
                                        {previewData.line_count} lines
                                        {previewData.truncated && ' (truncated)'}
                                   </span>
                              </div>
                              <pre className="p-4 text-sm text-gray-100 overflow-auto max-h-96 whitespace-pre-wrap">
                                   <code>{previewData.content}</code>
                              </pre>
                              {previewData.truncated && (
                                   <div className="bg-yellow-50 border-t border-yellow-200 p-3">
                                        <p className="text-sm text-yellow-800">
                                             File preview is truncated. Download the full file to see all content.
                                        </p>
                                   </div>
                              )}
                         </div>
                    );

               default:
                    return (
                         <div className="flex items-center justify-center h-64">
                              <div className="text-center">
                                   <FileIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                                   <p className="text-gray-600 mb-2">Preview not supported for this file type</p>
                                   <p className="text-sm text-gray-500 mb-4">
                                        File type: {file.content_type || 'Unknown'}
                                   </p>
                                   <button
                                        onClick={handleDownload}
                                        className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                                   >
                                        Download File
                                   </button>
                              </div>
                         </div>
                    );
          }
     };

     // Get file icon
     const getFileIcon = () => {
          const fileType = getFileType();

          switch (fileType) {
               case 'image':
                    return <ImageIcon className="h-6 w-6 text-green-500" />;
               case 'code':
                    return <FileTextIcon className="h-6 w-6 text-blue-500" />;
               default:
                    return <FileIcon className="h-6 w-6 text-gray-500" />;
          }
     };

     return (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
               <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-gray-200">
                         <div className="flex items-center space-x-3">
                              {getFileIcon()}
                              <div>
                                   <h2 className="text-xl font-semibold text-gray-900">{file.filename}</h2>
                                   <p className="text-sm text-gray-500">
                                        {formatFileSize(file.file_size)} • {file.content_type || 'Unknown type'}
                                   </p>
                              </div>
                         </div>

                         <div className="flex items-center space-x-2">
                              <button
                                   onClick={handleDownload}
                                   className="p-2 text-gray-600 hover:text-indigo-600 transition-colors"
                                   title="Download"
                              >
                                   <DownloadIcon className="h-5 w-5" />
                              </button>
                              <button
                                   onClick={onClose}
                                   className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                                   title="Close"
                              >
                                   <XIcon className="h-5 w-5" />
                              </button>
                         </div>
                    </div>

                    {/* Content */}
                    <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
                         {renderPreviewContent()}
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
                         <div className="text-sm text-gray-600">
                              Created: {new Date(file.created_at).toLocaleDateString('en-US', {
                                   year: 'numeric',
                                   month: 'long',
                                   day: 'numeric',
                                   hour: '2-digit',
                                   minute: '2-digit'
                              })}
                         </div>

                         <button
                              onClick={onClose}
                              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                         >
                              Close
                         </button>
                    </div>
               </div>
          </div>
     );
};

export default FilePreviewModal;