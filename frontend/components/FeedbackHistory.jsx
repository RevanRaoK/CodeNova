import { useState, useEffect } from 'react'
import {
  ThumbsUpIcon,
  ThumbsDownIcon,
  ClockIcon,
  FilterIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  AlertCircleIcon,
  CheckCircleIcon,
  InfoIcon
} from 'lucide-react'
import feedbackService from '../services/feedbackService.js'

/**
 * FeedbackHistory component for displaying user's feedback history
 * 
 * @param {Object} props
 * @param {string} props.userId - User ID to filter feedback (optional)
 * @param {number} props.pageSize - Number of items per page
 * @param {boolean} props.showFilters - Whether to show filter controls
 * @param {Function} props.onFeedbackClick - Callback when feedback item is clicked
 */
export function FeedbackHistory({
  userId = null,
  pageSize = 10,
  showFilters = true,
  onFeedbackClick = null
}) {
  const [feedbackHistory, setFeedbackHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [hasNext, setHasNext] = useState(false)
  const [hasPrevious, setHasPrevious] = useState(false)

  // Filter states
  const [feedbackTypeFilter, setFeedbackTypeFilter] = useState('')
  const [dateRangeFilter, setDateRangeFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')

  // Load feedback history
  const loadFeedbackHistory = async (page = 1, filters = {}) => {
    setLoading(true)
    setError(null)

    try {
      const options = {
        page,
        pageSize,
        ...filters
      }

      const response = await feedbackService.getUserFeedbackHistory(options)

      setFeedbackHistory(response.feedback)
      setTotalCount(response.totalCount)
      setCurrentPage(response.page)
      setHasNext(response.hasNext)
      setHasPrevious(response.hasPrevious)
    } catch (error) {
      console.error('Failed to load feedback history:', error)
      setError(error.message || 'Failed to load feedback history')
    } finally {
      setLoading(false)
    }
  }

  // Initial load
  useEffect(() => {
    loadFeedbackHistory(1, {
      feedbackType: feedbackTypeFilter || undefined,
      dateRange: dateRangeFilter || undefined,
      severity: severityFilter || undefined
    })
  }, [feedbackTypeFilter, dateRangeFilter, severityFilter])

  // Handle pagination
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= Math.ceil(totalCount / pageSize)) {
      loadFeedbackHistory(newPage, {
        feedbackType: feedbackTypeFilter || undefined,
        dateRange: dateRangeFilter || undefined,
        severity: severityFilter || undefined
      })
    }
  }

  // Handle filter reset
  const handleResetFilters = () => {
    setFeedbackTypeFilter('')
    setDateRangeFilter('')
    setSeverityFilter('')
    setCurrentPage(1)
  }

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Get feedback type icon
  const getFeedbackTypeIcon = (type) => {
    switch (type) {
      case 'positive':
        return <ThumbsUpIcon className="w-4 h-4 text-green-500" />
      case 'negative':
        return <ThumbsDownIcon className="w-4 h-4 text-red-500" />
      default:
        return <InfoIcon className="w-4 h-4 text-blue-500" />
    }
  }

  // Get severity badge
  const getSeverityBadge = (severity) => {
    const severityConfig = {
      low: { color: 'bg-green-100 text-green-800', icon: CheckCircleIcon },
      medium: { color: 'bg-yellow-100 text-yellow-800', icon: InfoIcon },
      high: { color: 'bg-red-100 text-red-800', icon: AlertCircleIcon }
    }

    const config = severityConfig[severity] || severityConfig.medium
    const IconComponent = config.icon

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <IconComponent className="w-3 h-3 mr-1" />
        {severity}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2 text-gray-600">Loading feedback history...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertCircleIcon className="w-5 h-5 text-red-500 mr-2" />
          <span className="text-red-700">Error: {error}</span>
        </div>
        <button
          onClick={() => loadFeedbackHistory(1)}
          className="mt-2 text-red-600 hover:text-red-800 underline"
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Feedback History</h3>
          <div className="flex items-center space-x-2">
            <ClockIcon className="w-5 h-5 text-gray-400" />
            <span className="text-sm text-gray-500">{totalCount} total items</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <FilterIcon className="w-4 h-4 text-gray-400" />

            {/* Feedback Type Filter */}
            <select
              value={feedbackTypeFilter}
              onChange={(e) => setFeedbackTypeFilter(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              <option value="positive">Positive</option>
              <option value="negative">Negative</option>
              <option value="suggestion">Suggestion</option>
            </select>

            {/* Date Range Filter */}
            <select
              value={dateRangeFilter}
              onChange={(e) => setDateRangeFilter(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Time</option>
              <option value="today">Today</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
            </select>

            {/* Severity Filter */}
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>

            {/* Reset Filters */}
            <button
              onClick={handleResetFilters}
              className="text-sm text-blue-600 hover:text-blue-800 underline"
            >
              Reset
            </button>
          </div>
        </div>
      )}

      {/* Feedback List */}
      <div className="divide-y divide-gray-200">
        {feedbackHistory.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <InfoIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">No feedback found</h4>
            <p className="text-gray-500">No feedback matches your current filters.</p>
          </div>
        ) : (
          feedbackHistory.map((feedback) => (
            <div
              key={feedback.id}
              className={`px-6 py-4 hover:bg-gray-50 transition-colors ${onFeedbackClick ? 'cursor-pointer' : ''
                }`}
              onClick={() => onFeedbackClick && onFeedbackClick(feedback)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    {getFeedbackTypeIcon(feedback.feedbackType)}
                    <span className="font-medium text-gray-900 capitalize">
                      {feedback.feedbackType}
                    </span>
                    {feedback.severity && getSeverityBadge(feedback.severity)}
                  </div>

                  <p className="text-gray-700 mb-2">{feedback.message}</p>

                  {feedback.context && (
                    <div className="text-sm text-gray-500 mb-2">
                      <strong>Context:</strong> {feedback.context}
                    </div>
                  )}

                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>{formatDate(feedback.createdAt)}</span>
                    {feedback.page && (
                      <span>Page: {feedback.page}</span>
                    )}
                    {feedback.userAgent && (
                      <span>Browser: {feedback.userAgent.split(' ')[0]}</span>
                    )}
                  </div>
                </div>

                {feedback.status && (
                  <div className="ml-4">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${feedback.status === 'resolved'
                      ? 'bg-green-100 text-green-800'
                      : feedback.status === 'in-progress'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                      }`}>
                      {feedback.status}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalCount > pageSize && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} results
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={!hasPrevious}
                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeftIcon className="w-4 h-4 mr-1" />
                Previous
              </button>

              <span className="text-sm text-gray-700">
                Page {currentPage} of {Math.ceil(totalCount / pageSize)}
              </span>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={!hasNext}
                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
                <ChevronRightIcon className="w-4 h-4 ml-1" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default FeedbackHistory