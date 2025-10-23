import React, { useState, useEffect } from 'react';
import {
  FileTextIcon,
  ClockIcon,
  AlertCircleIcon,
  CheckCircleIcon,
  LoaderIcon,
  FilterIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  TrashIcon
} from 'lucide-react';
import analysisService from '../services/analysisService.js';
import SuggestionFeedbackWidget from './SuggestionFeedbackWidget';
import SuggestionDisplay from './SuggestionDisplay';

/**
 * AnalysisHistory - Component to display user's analysis history with filenames and batch analyses
 * Shows all previous analyses with ability to view details and provide feedback
 */
const AnalysisHistory = ({ onAnalysisSelect, enableFeedback = true }) => {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [expandedAnalyses, setExpandedAnalyses] = useState(new Set());
  const [filterLanguage, setFilterLanguage] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  const pageSize = 20;

  // Fetch analyses
  const fetchAnalyses = async (pageNum = 1) => {
    setLoading(true);
    setError(null);

    try {
      const options = {
        page: pageNum,
        page_size: pageSize
      };

      if (filterLanguage !== 'all') {
        options.language = filterLanguage;
      }

      if (filterStatus !== 'all') {
        options.status = filterStatus;
      }

      const result = await analysisService.getUserAnalyses(options);
      
      setAnalyses(result.analyses || []);
      setTotalCount(result.total_count || 0);
      setHasNext(result.has_next || false);
      setPage(pageNum);
    } catch (err) {
      console.error('Failed to fetch analyses:', err);
      setError(err.message || 'Failed to load analysis history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses(1);
  }, [filterLanguage, filterStatus]);

  const toggleAnalysisExpansion = (analysisId) => {
    const newExpanded = new Set(expandedAnalyses);
    if (newExpanded.has(analysisId)) {
      newExpanded.delete(analysisId);
    } else {
      newExpanded.add(analysisId);
    }
    setExpandedAnalyses(newExpanded);
  };

  const handleAnalysisClick = (analysis) => {
    if (onAnalysisSelect) {
      onAnalysisSelect(analysis);
    }
  };

  const handleDeleteAnalysis = async (analysisId, event) => {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this analysis?')) {
      return;
    }

    try {
      await analysisService.deleteAnalysis(analysisId);
      // Refresh the list
      fetchAnalyses(page);
    } catch (err) {
      console.error('Failed to delete analysis:', err);
      alert('Failed to delete analysis: ' + err.message);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      completed: 'bg-green-100 text-green-800 border-green-200',
      failed: 'bg-red-100 text-red-800 border-red-200',
      processing: 'bg-blue-100 text-blue-800 border-blue-200',
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-200'
    };

    return badges[status] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <AlertCircleIcon className="h-4 w-4 text-red-600" />;
      case 'processing':
        return <LoaderIcon className="h-4 w-4 text-blue-600 animate-spin" />;
      default:
        return <ClockIcon className="h-4 w-4 text-gray-600" />;
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
  };

  if (loading && analyses.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoaderIcon className="h-8 w-8 text-indigo-600 animate-spin" />
        <span className="ml-3 text-gray-600">Loading analysis history...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-start space-x-3">
          <AlertCircleIcon className="h-5 w-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-red-800">Error Loading History</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button
              onClick={() => fetchAnalyses(page)}
              className="mt-3 px-3 py-1 text-sm text-red-700 bg-red-100 hover:bg-red-200 rounded transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (analyses.length === 0) {
    return (
      <div className="p-8 text-center bg-gray-50 border border-gray-200 rounded-lg">
        <FileTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Analysis History</h3>
        <p className="text-gray-600">
          Your code analysis history will appear here once you start analyzing code.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with filters */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">
          Analysis History ({totalCount})
        </h2>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <FilterIcon className="h-4 w-4 text-gray-500" />
            <select
              value={filterLanguage}
              onChange={(e) => setFilterLanguage(e.target.value)}
              className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All Languages</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
              <option value="python">Python</option>
              <option value="java">Java</option>
              <option value="cpp">C++</option>
            </select>
          </div>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Status</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="processing">Processing</option>
          </select>
        </div>
      </div>

      {/* Analysis List */}
      <div className="space-y-3">
        {analyses.map((analysis) => {
          const isExpanded = expandedAnalyses.has(analysis.id);

          return (
            <div
              key={analysis.id}
              className="border border-gray-200 rounded-lg bg-white hover:shadow-md transition-shadow"
            >
              {/* Analysis Header */}
              <div
                className="p-4 cursor-pointer"
                onClick={() => toggleAnalysisExpansion(analysis.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1 min-w-0">
                    <FileTextIcon className="h-5 w-5 text-gray-400 mt-0.5 flex-shrink-0" />
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {analysis.filename || 'Untitled'}
                        </h3>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getStatusBadge(analysis.status)}`}>
                          {getStatusIcon(analysis.status)}
                          <span className="ml-1">{analysis.status}</span>
                        </span>
                      </div>

                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>{analysis.language}</span>
                        <span>•</span>
                        <span>{analysis.issuesCount || 0} issues</span>
                        {analysis.errorsCount > 0 && (
                          <>
                            <span>•</span>
                            <span className="text-red-600">{analysis.errorsCount} errors</span>
                          </>
                        )}
                        {analysis.warningsCount > 0 && (
                          <>
                            <span>•</span>
                            <span className="text-yellow-600">{analysis.warningsCount} warnings</span>
                          </>
                        )}
                        <span>•</span>
                        <span>{formatDate(analysis.createdAt)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-3">
                    <button
                      onClick={(e) => handleDeleteAnalysis(analysis.id, e)}
                      className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete analysis"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                    
                    {isExpanded ? (
                      <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                    ) : (
                      <ChevronRightIcon className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-gray-200 bg-gray-50">
                  <div className="mt-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">
                        Analysis Details
                      </span>
                      <button
                        onClick={() => handleAnalysisClick(analysis)}
                        className="px-3 py-1 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                      >
                        View Full Results
                      </button>
                    </div>

                    {analysis.linesOfCode && (
                      <div className="text-sm text-gray-600">
                        <strong>Lines of Code:</strong> {analysis.linesOfCode}
                      </div>
                    )}

                    {analysis.completedAt && (
                      <div className="text-sm text-gray-600">
                        <strong>Completed:</strong> {new Date(analysis.completedAt).toLocaleString()}
                      </div>
                    )}

                    {/* Placeholder for issues - would need to fetch from API */}
                    <div className="text-xs text-gray-500 italic">
                      Click "View Full Results" to see detailed issues and provide feedback
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      {totalCount > pageSize && (
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, totalCount)} of {totalCount}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => fetchAnalyses(page - 1)}
              disabled={page === 1 || loading}
              className="px-3 py-1 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600">
              Page {page} of {Math.ceil(totalCount / pageSize)}
            </span>
            <button
              onClick={() => fetchAnalyses(page + 1)}
              disabled={!hasNext || loading}
              className="px-3 py-1 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisHistory;
