import React, { useState, useEffect, useCallback } from 'react';
import {
     FolderIcon,
     UploadIcon,
     SearchIcon,
     FilterIcon,
     DownloadIcon,
     TrashIcon,
     EyeIcon,
     MoreVerticalIcon,
     CheckIcon,
     XIcon,
     AlertCircleIcon,
     FileTextIcon,
     ImageIcon,
     FileIcon
} from 'lucide-react';
import fileService from '../services/fileService.js';
import { formatFileSize } from '../utils/fileUtils.ts';
import FileUploadComponent from './FileUploadComponent.jsx';
import FilePreviewModal from './FilePreviewModal.jsx';
import ConfirmationDialog from './ConfirmationDialog.jsx';
import Toast from './Toast.jsx';

const FileManager = () => {
     // State management
     const [files, setFiles] = useState([]);
     const [loading, setLoading] = useState(true);
     const [error, setError] = useState(null);
     const [selectedFiles, setSelectedFiles] = useState(new Set());
     const [searchQuery, setSearchQuery] = useState('');
     const [filters, setFilters] = useState({
          fileType: '',
          sortBy: 'created_at',
          sortOrder: 'desc'
     });
     const [pagination, setPagination] = useState({
          page: 1,
          limit: 20,
          total: 0,
          totalPages: 0
     });

     // Modal states
     const [showUpload, setShowUpload] = useState(false);
     const [previewFile, setPreviewFile] = useState(null);
     const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
     const [filesToDelete, setFilesToDelete] = useState([]);

     // Toast state
     const [toast, setToast] = useState(null);

     // Load files
     const loadFiles = useCallback(async () => {
          try {
               setLoading(true);
               setError(null);

               const params = {
                    page: pagination.page,
                    limit: pagination.limit,
                    search: searchQuery,
                    ...filters
               };

               const response = await fileService.getFiles(params);

               setFiles(response.files || []);
               setPagination(prev => ({
                    ...prev,
                    total: response.total || 0,
                    totalPages: response.total_pages || 0
               }));
          } catch (err) {
               console.error('Failed to load files:', err);
               setError('Failed to load files. Please try again.');
               showToast('Failed to load files', 'error');
          } finally {
               setLoading(false);
          }
     }, [pagination.page, pagination.limit, searchQuery, filters]);

     // Load files on mount and when dependencies change
     useEffect(() => {
          loadFiles();
     }, [loadFiles]);

     // Show toast notification
     const showToast = (message, type = 'info') => {
          setToast({ message, type });
          setTimeout(() => setToast(null), 5000);
     };

     // Handle file selection
     const toggleFileSelection = (fileId) => {
          const newSelected = new Set(selectedFiles);
          if (newSelected.has(fileId)) {
               newSelected.delete(fileId);
          } else {
               newSelected.add(fileId);
          }
          setSelectedFiles(newSelected);
     };

     // Select all files
     const selectAllFiles = () => {
          if (selectedFiles.size === files.length) {
               setSelectedFiles(new Set());
          } else {
               setSelectedFiles(new Set(files.map(f => f.id)));
          }
     };

     // Handle search
     const handleSearch = (e) => {
          e.preventDefault();
          setPagination(prev => ({ ...prev, page: 1 }));
          loadFiles();
     };

     // Handle filter change
     const handleFilterChange = (key, value) => {
          setFilters(prev => ({ ...prev, [key]: value }));
          setPagination(prev => ({ ...prev, page: 1 }));
     };

     // Handle file upload success
     const handleUploadSuccess = (uploadedFiles) => {
          // Don't show duplicate notification - FileUploadComponent already shows it
          setShowUpload(false);
          loadFiles();
     };

     // Handle file download
     const handleDownload = async (file) => {
          try {
               const downloadData = await fileService.getDownloadUrl(file.id);

               // Create temporary link and trigger download
               const link = document.createElement('a');
               link.href = downloadData.url;
               link.download = file.filename;
               document.body.appendChild(link);
               link.click();
               document.body.removeChild(link);

               showToast('Download started', 'success');
          } catch (err) {
               console.error('Download failed:', err);
               showToast('Failed to download file', 'error');
          }
     };

     // Handle file preview
     const handlePreview = (file) => {
          setPreviewFile(file);
     };

     // Handle file deletion
     const handleDelete = (fileIds) => {
          setFilesToDelete(Array.isArray(fileIds) ? fileIds : [fileIds]);
          setShowDeleteConfirm(true);
     };

     // Confirm deletion
     const confirmDelete = async () => {
          try {
               if (filesToDelete.length === 1) {
                    await fileService.deleteFile(filesToDelete[0]);
               } else {
                    await fileService.deleteMultipleFiles(filesToDelete);
               }

               showToast(`Successfully deleted ${filesToDelete.length} file(s)`, 'success');
               setSelectedFiles(new Set());
               loadFiles();
          } catch (err) {
               console.error('Delete failed:', err);
               showToast('Failed to delete file(s)', 'error');
          } finally {
               setShowDeleteConfirm(false);
               setFilesToDelete([]);
          }
     };

     // Get file icon based on type
     const getFileIcon = (file) => {
          const extension = file.filename.split('.').pop()?.toLowerCase();

          if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(extension)) {
               return <ImageIcon className="h-5 w-5 text-green-500" />;
          }

          if (['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'cpp', 'c', 'cs', 'go', 'rs', 'php', 'rb'].includes(extension)) {
               return <FileTextIcon className="h-5 w-5 text-blue-500" />;
          }

          return <FileIcon className="h-5 w-5 text-gray-500" />;
     };

     // Format date
     const formatDate = (dateString) => {
          return new Date(dateString).toLocaleDateString('en-US', {
               year: 'numeric',
               month: 'short',
               day: 'numeric',
               hour: '2-digit',
               minute: '2-digit'
          });
     };

     return (
          <div className="max-w-7xl mx-auto p-6">
               {/* Header */}
               <div className="mb-6">
                    <div className="flex items-center justify-between">
                         <div>
                              <h1 className="text-2xl font-bold text-gray-900">File Manager</h1>
                              <p className="text-gray-600 mt-1">
                                   Manage your uploaded files and documents
                              </p>
                         </div>
                         <button
                              onClick={() => setShowUpload(true)}
                              className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors flex items-center space-x-2"
                         >
                              <UploadIcon className="h-5 w-5" />
                              <span>Upload Files</span>
                         </button>
                    </div>
               </div>

               {/* Search and Filters */}
               <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
                    <div className="flex flex-col md:flex-row gap-4">
                         {/* Search */}
                         <form onSubmit={handleSearch} className="flex-1">
                              <div className="relative">
                                   <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                                   <input
                                        type="text"
                                        placeholder="Search files..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                   />
                              </div>
                         </form>

                         {/* Filters */}
                         <div className="flex gap-2">
                              <select
                                   value={filters.fileType}
                                   onChange={(e) => handleFilterChange('fileType', e.target.value)}
                                   className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                              >
                                   <option value="">All Types</option>
                                   <option value="image">Images</option>
                                   <option value="code">Code Files</option>
                                   <option value="document">Documents</option>
                                   <option value="other">Other</option>
                              </select>

                              <select
                                   value={`${filters.sortBy}-${filters.sortOrder}`}
                                   onChange={(e) => {
                                        const [sortBy, sortOrder] = e.target.value.split('-');
                                        handleFilterChange('sortBy', sortBy);
                                        handleFilterChange('sortOrder', sortOrder);
                                   }}
                                   className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                              >
                                   <option value="created_at-desc">Newest First</option>
                                   <option value="created_at-asc">Oldest First</option>
                                   <option value="filename-asc">Name A-Z</option>
                                   <option value="filename-desc">Name Z-A</option>
                                   <option value="file_size-desc">Largest First</option>
                                   <option value="file_size-asc">Smallest First</option>
                              </select>
                         </div>
                    </div>

                    {/* Bulk Actions */}
                    {selectedFiles.size > 0 && (
                         <div className="mt-4 p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                              <div className="flex items-center justify-between">
                                   <span className="text-sm text-indigo-700">
                                        {selectedFiles.size} file(s) selected
                                   </span>
                                   <div className="flex gap-2">
                                        <button
                                             onClick={() => handleDelete(Array.from(selectedFiles))}
                                             className="text-red-600 hover:text-red-700 text-sm font-medium flex items-center space-x-1"
                                        >
                                             <TrashIcon className="h-4 w-4" />
                                             <span>Delete Selected</span>
                                        </button>
                                        <button
                                             onClick={() => setSelectedFiles(new Set())}
                                             className="text-gray-600 hover:text-gray-700 text-sm font-medium"
                                        >
                                             Clear Selection
                                        </button>
                                   </div>
                              </div>
                         </div>
                    )}
               </div>

               {/* Files List */}
               <div className="bg-white rounded-lg shadow-sm border">
                    {loading ? (
                         <div className="p-8 text-center">
                              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                              <p className="text-gray-600 mt-2">Loading files...</p>
                         </div>
                    ) : error ? (
                         <div className="p-8 text-center">
                              <AlertCircleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
                              <p className="text-red-600 mb-4">{error}</p>
                              <button
                                   onClick={loadFiles}
                                   className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                              >
                                   Try Again
                              </button>
                         </div>
                    ) : files.length === 0 ? (
                         <div className="p-8 text-center">
                              <FolderIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                              <p className="text-gray-600 mb-4">
                                   {searchQuery ? 'No files found matching your search.' : 'No files uploaded yet.'}
                              </p>
                              <button
                                   onClick={() => setShowUpload(true)}
                                   className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                              >
                                   Upload Your First File
                              </button>
                         </div>
                    ) : (
                         <>
                              {/* Table Header */}
                              <div className="border-b border-gray-200 p-4">
                                   <div className="flex items-center">
                                        <div className="flex items-center mr-4">
                                             <input
                                                  type="checkbox"
                                                  checked={selectedFiles.size === files.length && files.length > 0}
                                                  onChange={selectAllFiles}
                                                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                                             />
                                        </div>
                                        <div className="flex-1 grid grid-cols-12 gap-4 text-sm font-medium text-gray-700">
                                             <div className="col-span-5">Name</div>
                                             <div className="col-span-2">Size</div>
                                             <div className="col-span-2">Type</div>
                                             <div className="col-span-2">Modified</div>
                                             <div className="col-span-1">Actions</div>
                                        </div>
                                   </div>
                              </div>

                              {/* Files */}
                              <div className="divide-y divide-gray-200">
                                   {files.map((file) => (
                                        <div key={file.id} className="p-4 hover:bg-gray-50">
                                             <div className="flex items-center">
                                                  <div className="flex items-center mr-4">
                                                       <input
                                                            type="checkbox"
                                                            checked={selectedFiles.has(file.id)}
                                                            onChange={() => toggleFileSelection(file.id)}
                                                            className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                                                       />
                                                  </div>
                                                  <div className="flex-1 grid grid-cols-12 gap-4 items-center">
                                                       {/* Name */}
                                                       <div className="col-span-5 flex items-center space-x-3">
                                                            {getFileIcon(file)}
                                                            <div className="min-w-0">
                                                                 <p className="text-sm font-medium text-gray-900 truncate">
                                                                      {file.filename}
                                                                 </p>
                                                                 {file.description && (
                                                                      <p className="text-xs text-gray-500 truncate">
                                                                           {file.description}
                                                                      </p>
                                                                 )}
                                                            </div>
                                                       </div>

                                                       {/* Size */}
                                                       <div className="col-span-2">
                                                            <span className="text-sm text-gray-600">
                                                                 {formatFileSize(file.file_size)}
                                                            </span>
                                                       </div>

                                                       {/* Type */}
                                                       <div className="col-span-2">
                                                            <span className="text-sm text-gray-600">
                                                                 {file.content_type || 'Unknown'}
                                                            </span>
                                                       </div>

                                                       {/* Modified */}
                                                       <div className="col-span-2">
                                                            <span className="text-sm text-gray-600">
                                                                 {formatDate(file.created_at)}
                                                            </span>
                                                       </div>

                                                       {/* Actions */}
                                                       <div className="col-span-1">
                                                            <div className="flex items-center space-x-2">
                                                                 <button
                                                                      onClick={() => handlePreview(file)}
                                                                      className="text-gray-400 hover:text-indigo-600 transition-colors"
                                                                      title="Preview"
                                                                 >
                                                                      <EyeIcon className="h-4 w-4" />
                                                                 </button>
                                                                 <button
                                                                      onClick={() => handleDownload(file)}
                                                                      className="text-gray-400 hover:text-green-600 transition-colors"
                                                                      title="Download"
                                                                 >
                                                                      <DownloadIcon className="h-4 w-4" />
                                                                 </button>
                                                                 <button
                                                                      onClick={() => handleDelete(file.id)}
                                                                      className="text-gray-400 hover:text-red-600 transition-colors"
                                                                      title="Delete"
                                                                 >
                                                                      <TrashIcon className="h-4 w-4" />
                                                                 </button>
                                                            </div>
                                                       </div>
                                                  </div>
                                             </div>
                                        </div>
                                   ))}
                              </div>

                              {/* Pagination */}
                              {pagination.totalPages > 1 && (
                                   <div className="border-t border-gray-200 p-4">
                                        <div className="flex items-center justify-between">
                                             <div className="text-sm text-gray-700">
                                                  Showing {((pagination.page - 1) * pagination.limit) + 1} to{' '}
                                                  {Math.min(pagination.page * pagination.limit, pagination.total)} of{' '}
                                                  {pagination.total} files
                                             </div>
                                             <div className="flex space-x-2">
                                                  <button
                                                       onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                                                       disabled={pagination.page === 1}
                                                       className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                                  >
                                                       Previous
                                                  </button>
                                                  <span className="px-3 py-1 text-sm">
                                                       Page {pagination.page} of {pagination.totalPages}
                                                  </span>
                                                  <button
                                                       onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                                                       disabled={pagination.page === pagination.totalPages}
                                                       className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                                  >
                                                       Next
                                                  </button>
                                             </div>
                                        </div>
                                   </div>
                              )}
                         </>
                    )}
               </div>

               {/* Upload Modal */}
               {showUpload && (
                    <FileUploadComponent
                         onClose={() => setShowUpload(false)}
                         onSuccess={handleUploadSuccess}
                    />
               )}

               {/* Preview Modal */}
               {previewFile && (
                    <FilePreviewModal
                         file={previewFile}
                         onClose={() => setPreviewFile(null)}
                    />
               )}

               {/* Delete Confirmation */}
               {showDeleteConfirm && (
                    <ConfirmationDialog
                         title="Delete Files"
                         message={`Are you sure you want to delete ${filesToDelete.length} file(s)? This action cannot be undone.`}
                         confirmText="Delete"
                         confirmButtonClass="bg-red-600 hover:bg-red-700"
                         onConfirm={confirmDelete}
                         onCancel={() => {
                              setShowDeleteConfirm(false);
                              setFilesToDelete([]);
                         }}
                    />
               )}

               {/* Toast */}
               {toast && (
                    <Toast
                         message={toast.message}
                         type={toast.type}
                         onClose={() => setToast(null)}
                    />
               )}
          </div>
     );
};

export default FileManager;