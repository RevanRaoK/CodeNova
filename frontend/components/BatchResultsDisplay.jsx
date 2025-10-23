import React, { useState, useEffect } from 'react';
import {
  CheckCircleIcon,
  AlertCircleIcon,
  XCircleIcon,
  ClockIcon,
  FileTextIcon,
  FilterIcon,
  SearchIcon,
  RefreshCwIcon,
  DownloadIcon,
  EyeIcon,
} from 'lucide-react';
import { ReviewResults } from './ReviewResults';
import { formatFileSize } from '../utils/fileUtils';

export function BatchResultsDisplay({
  batchId,
  batchResults,
  onRefresh,
  isLoading = false,
  className = '',
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all'); // all, completed, failed, pending
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('filename'); // filename, issues, size, status
  const [sortOrder, setSortOrder] = useState('asc'); // asc, desc
  const [showOnlyWithIssues, setShowOnlyWithIssues] = useState(false);

  // Filter and sort files
  const filteredFiles = React.useMemo(() => {
    if (!batchResults?.files) return [];

    let filtered = batchResults.files.filter(file => {
      // Status filter
      if (filterStatus !== 'all' && file.status !== filterStatus) {
        return false;
      }

      // Search filter
      if (searchTerm && !file.filename.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }

      // Issues filter
      if (showOnlyWithIssues && (!file.issues || file.issues.length === 0)) {
        return false;
      }

      return true;
    });

    // Sort files
    filtered.sort((a, b) => {
      let aValue, bValue;

      switch (sortBy) {
        case 'filename':
          aValue = a.filename.toLowerCase();
          bValue = b.filename.toLowerCase();
          break;
        case 'issues':
          aValue = a.issues?.length || 0;
          bValue = b.issues?.length || 0;
          break;
        case 'size':
          aValue = a.file_size_kb || 0;
          bValue = b.file_size_kb || 0;
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        default:
          aValue = a.filename.toLowerCase();
          bValue = b.filename.toLowerCase();
      }

      if (sortOrder === 'desc') {
        return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
      } else {
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
      }
    });

    return filtered;
  }, [batchResults?.files, filterStatus, searchTerm, sortBy, sortOrder, showOnlyWithIssues]);

  // Get status icon and color
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'processing':
      case 'analyzing':
        return <ClockIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  // Get status color class
  const getStatusColorClass = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'failed':
        return 'bg-red-50 border-red-200';
      case 'processing':
      case 'analyzing':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  // Get severity color for issues count
  const getIssuesColorClass = (issuesCount, errorsCount) => {
    if (errorsCount > 0) return 'text-red-600 bg-red-100';
    if (issuesCount > 5) return 'text-orange-600 bg-orange-100';
    if (issuesCount > 0) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  if (!batchResults) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <p className="text-gray-500">No batch results available</p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Batch Summary */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            Batch Analysis Results
          </h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              <RefreshCwIcon className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{batchResults.total_files}</div>
            <div className="text-sm text-gray-500">Total Files</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{batchResults.successful_files}</div>
            <div className="text-sm text-gray-500">Successful</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {batchResults.total_files - batchResults.successful_files}
            </div>
            <div className="text-sm text-gray-500">Failed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {Math.round(batchResults.success_rate || 0)}%
            </div>
            <div className="text-sm text-gray-500">Success Rate</div>
          </div>
        </div>

        {batchResults.combined_results?.summary && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Summary</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="font-medium">Total Issues:</span>{' '}
                <span className="text-red-600">{batchResults.combined_results.summary.total_issues}</span>
              </div>
              <div>
                <span className="font-medium">Errors:</span>{' '}
                <span className="text-red-600">{batchResults.combined_results.summary.total_errors}</span>
              </div>
              <div>
                <span className="font-medium">Warnings:</span>{' '}
                <span className="text-orange-600">{batchResults.combined_results.summary.total_warnings}</span>
              </div>
              <div>
                <span className="font-medium">Lines of Code:</span>{' '}
                <span className="text-blue-600">{batchResults.combined_results.summary.total_lines_of_code}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Filters and Search */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0 md:space-x-4">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-4">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="processing">Processing</option>
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="filename">Sort by Name</option>
              <option value="issues">Sort by Issues</option>
              <option value="size">Sort by Size</option>
              <option value="status">Sort by Status</option>
            </select>

            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50"
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>

            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={showOnlyWithIssues}
                onChange={(e) => setShowOnlyWithIssues(e.target.checked)}
                className="mr-2 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              Issues only
            </label>
          </div>
        </div>
      </div>

      {/* Files List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h4 className="text-lg font-medium text-gray-900">
            Files ({filteredFiles.length})
          </h4>
        </div>

        {filteredFiles.length === 0 ? (
          <div className="text-center py-8">
            <FileTextIcon className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-gray-500">No files match your filters</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredFiles.map((file, index) => (
              <div
                key={index}
                className={`p-6 hover:bg-gray-50 transition-colors ${getStatusColorClass(file.status)}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1">
                    {getStatusIcon(file.status)}
                    <div className="flex-1 min-w-0">
                      <h5 className="text-sm font-medium text-gray-900 truncate">
                        {file.filename}
                      </h5>
                      <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                        <span>{file.language}</span>
                        <span>{formatFileSize(file.file_size_kb * 1024)}</span>
                        <span>{file.lines_count} lines</span>
                        {file.processing_time_seconds && (
                          <span>{file.processing_time_seconds.toFixed(1)}s</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    {/* Issues Count */}
                    {file.status === 'completed' && (
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                        getIssuesColorClass(file.issues?.length || 0, file.errors_count || 0)
                      }`}>
                        {file.issues?.length || 0} issues
                      </div>
                    )}

                    {/* Error Message */}
                    {file.status === 'failed' && file.error_message && (
                      <div className="text-xs text-red-600 max-w-xs truncate">
                        {file.error_message}
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center space-x-2">
                      {file.status === 'completed' && file.issues && file.issues.length > 0 && (
                        <button
                          onClick={() => setSelectedFile(selectedFile === file ? null : file)}
                          className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Results */}
                {selectedFile === file && file.issues && (
                  <div className="mt-4 border-t border-gray-200 pt-4">
                    <ReviewResults
                      issues={file.issues}
                      analysisMetrics={file.metrics}
                      showFileHeader={false}
                      compact={true}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Processing Stats */}
      {batchResults.processing_time_seconds && (
        <div className="bg-white shadow rounded-lg p-6">
          <h4 className="text-lg font-medium text-gray-900 mb-4">Processing Statistics</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium">Processing Time:</span>{' '}
              <span className="text-blue-600">{batchResults.processing_time_seconds.toFixed(1)}s</span>
            </div>
            <div>
              <span className="font-medium">Completed At:</span>{' '}
              <span className="text-gray-600">
                {new Date(batchResults.completed_at).toLocaleString()}
              </span>
            </div>
            {batchResults.combined_results?.processing_stats?.files_per_minute && (
              <div>
                <span className="font-medium">Files/Minute:</span>{' '}
                <span className="text-green-600">
                  {batchResults.combined_results.processing_stats.files_per_minute.toFixed(1)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}