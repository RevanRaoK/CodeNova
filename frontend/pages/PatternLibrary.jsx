import React, { useState, useEffect } from 'react'
import { SearchIcon, FilterIcon, ClockIcon, CodeIcon, AlertCircleIcon, AlertTriangleIcon, InfoIcon, ChevronDownIcon, ChevronRightIcon, ThumbsUpIcon, ThumbsDownIcon, CheckCircleIcon, XCircleIcon, LightbulbIcon } from 'lucide-react'
import analysisService from '../services/analysisService'
import feedbackService from '../services/feedbackService'
import { FeedbackWidget } from '../components/FeedbackWidget'

export function PatternLibrary() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedLanguage, setSelectedLanguage] = useState('all')
  const [selectedStatus, setSelectedStatus] = useState('all')
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedAnalyses, setExpandedAnalyses] = useState(new Set())
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  // Fetch analysis history
  useEffect(() => {
    fetchAnalysisHistory()
  }, [currentPage, selectedLanguage, selectedStatus])

  const fetchAnalysisHistory = async () => {
    try {
      setLoading(true)
      const options = {
        page: currentPage,
        page_size: 20
      }

      if (selectedLanguage !== 'all') {
        options.language = selectedLanguage
      }

      if (selectedStatus !== 'all') {
        options.status = selectedStatus
      }

      const response = await analysisService.getUserAnalyses(options)
      setAnalyses(response.analyses || [])
      setTotalPages(Math.ceil(response.total_count / response.page_size))
      setError(null)
    } catch (err) {
      console.error('Failed to fetch analysis history:', err)
      setError('Failed to load analysis history. Please try again.')
      setAnalyses([])
    } finally {
      setLoading(false)
    }
  }

  const toggleAnalysisExpansion = (analysisId) => {
    const newExpanded = new Set(expandedAnalyses)
    if (newExpanded.has(analysisId)) {
      newExpanded.delete(analysisId)
    } else {
      newExpanded.add(analysisId)
    }
    setExpandedAnalyses(newExpanded)
  }

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return <AlertCircleIcon className="h-4 w-4 text-red-600" />
      case 'high':
        return <AlertCircleIcon className="h-4 w-4 text-orange-500" />
      case 'error':
        return <AlertCircleIcon className="h-4 w-4 text-red-500" />
      case 'warning':
        return <AlertTriangleIcon className="h-4 w-4 text-yellow-500" />
      case 'low':
        return <InfoIcon className="h-4 w-4 text-blue-500" />
      case 'info':
        return <InfoIcon className="h-4 w-4 text-gray-500" />
      case 'suggestion':
        return <LightbulbIcon className="h-4 w-4 text-green-500" />
      default:
        return <InfoIcon className="h-4 w-4 text-gray-500" />
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'high':
        return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low':
        return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'info':
        return 'text-gray-600 bg-gray-50 border-gray-200'
      case 'suggestion':
        return 'text-green-600 bg-green-50 border-green-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  // Color coding function for issue containers based on severity
  const getSeverityColorClasses = (severity, isSuggestion = false) => {
    // Green background for suggestion sections
    if (isSuggestion) {
      return 'bg-green-100 border-green-300 text-green-900'
    }

    // Color mapping for different severity levels
    const colorMap = {
      critical: 'bg-red-100 border-red-300 text-red-900',
      high: 'bg-orange-100 border-orange-300 text-orange-900',
      warning: 'bg-yellow-100 border-yellow-300 text-yellow-900',
      low: 'bg-blue-100 border-blue-300 text-blue-900',
      info: 'bg-gray-100 border-gray-300 text-gray-900',
      error: 'bg-red-100 border-red-300 text-red-900', // Legacy support
      suggestion: 'bg-green-100 border-green-300 text-green-900'
    }

    return colorMap[severity?.toLowerCase()] || colorMap.info
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString()
  }

  const filteredAnalyses = analyses.filter((analysis) => {
    const matchesSearch =
      (analysis.filename && analysis.filename.toLowerCase().includes(searchQuery.toLowerCase())) ||
      analysis.language.toLowerCase().includes(searchQuery.toLowerCase()) ||
      analysis.id.toLowerCase().includes(searchQuery.toLowerCase())

    return matchesSearch
  })

  if (loading) {
    return (
      <div className="w-full">
        <h1 className="text-2xl font-bold mb-6">Analysis History</h1>
        <div className="bg-white p-8 text-center rounded-lg border border-gray-200">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading analysis history...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full">
        <h1 className="text-2xl font-bold mb-6">Analysis History</h1>
        <div className="bg-red-50 p-8 text-center rounded-lg border border-red-200">
          <AlertCircleIcon className="mx-auto h-12 w-12 text-red-400" />
          <h3 className="mt-2 text-lg font-medium text-red-900">Error</h3>
          <p className="mt-1 text-red-700">{error}</p>
          <button
            onClick={fetchAnalysisHistory}
            className="mt-4 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full">
      <h1 className="text-2xl font-bold mb-6">Analysis History</h1>

      {/* Search and Filter Controls */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm mb-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="relative flex-grow max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <SearchIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Search by filename, language, or analysis ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="flex flex-col sm:flex-row gap-4">
            <div>
              <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">
                Language
              </label>
              <select
                id="language"
                className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
              >
                <option value="all">All Languages</option>
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
                <option value="python">Python</option>
                <option value="java">Java</option>
                <option value="cpp">C++</option>
                <option value="csharp">C#</option>
              </select>
            </div>
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                id="status"
                className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Analysis History List */}
      {filteredAnalyses.length > 0 ? (
        <div className="space-y-4">
          {filteredAnalyses.map((analysis) => (
            <div key={analysis.id} className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
              {/* Analysis Header */}
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <CodeIcon className="h-8 w-8 text-indigo-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">
                        {analysis.filename || `Analysis ${analysis.id.slice(0, 8)}`}
                      </h3>
                      <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                        <span className="capitalize">{analysis.language}</span>
                        <span>•</span>
                        <span>{formatDate(analysis.createdAt)}</span>
                        <span>•</span>
                        <span>{analysis.linesOfCode} lines</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    {/* Status Badge */}
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${analysis.status === 'completed' ? 'bg-green-100 text-green-800' :
                      analysis.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                      {analysis.status}
                    </span>

                    {/* Issues Summary */}
                    {analysis.status === 'completed' && (
                      <div className="flex items-center space-x-2 text-sm">
                        {analysis.errorsCount > 0 && (
                          <span className="flex items-center text-red-600">
                            <AlertCircleIcon className="h-4 w-4 mr-1" />
                            {analysis.errorsCount}
                          </span>
                        )}
                        {analysis.warningsCount > 0 && (
                          <span className="flex items-center text-yellow-600">
                            <AlertTriangleIcon className="h-4 w-4 mr-1" />
                            {analysis.warningsCount}
                          </span>
                        )}
                        <span className="text-gray-500">
                          {analysis.issuesCount} total issues
                        </span>
                      </div>
                    )}

                    {/* Expand/Collapse Button */}
                    {analysis.issuesCount > 0 && (
                      <button
                        onClick={() => toggleAnalysisExpansion(analysis.id)}
                        className="flex items-center text-sm text-indigo-600 hover:text-indigo-800"
                      >
                        {expandedAnalyses.has(analysis.id) ? (
                          <>
                            <ChevronDownIcon className="h-4 w-4 mr-1" />
                            Hide Issues
                          </>
                        ) : (
                          <>
                            <ChevronRightIcon className="h-4 w-4 mr-1" />
                            Show Issues
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Issues Section */}
              {expandedAnalyses.has(analysis.id) && analysis.issuesCount > 0 && (
                <AnalysisIssuesGroup analysisId={analysis.id} analysisType={analysis.type} />
              )}
            </div>
          ))}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between bg-white px-4 py-3 border border-gray-200 rounded-lg">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Page <span className="font-medium">{currentPage}</span> of{' '}
                    <span className="font-medium">{totalPages}</span>
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white p-8 text-center rounded-lg border border-gray-200">
          <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900">
            No analysis history found
          </h3>
          <p className="mt-1 text-gray-500">
            {searchQuery ? 'Try adjusting your search criteria' : 'Start analyzing some code to see your history here'}
          </p>
        </div>
      )}
    </div>
  )
}

// Component to display grouped issues for an analysis
function AnalysisIssuesGroup({ analysisId, analysisType }) {
  const [issues, setIssues] = useState([])
  const [filteredIssues, setFilteredIssues] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [issueFeedback, setIssueFeedback] = useState({}) // Store feedback for each issue

  // Filtering and sorting state
  const [severityFilter, setSeverityFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [sortBy, setSortBy] = useState('severity') // severity, line, category
  const [sortOrder, setSortOrder] = useState('desc') // asc, desc
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchAnalysisDetails()
  }, [analysisId])

  useEffect(() => {
    applyFiltersAndSorting()
  }, [issues, severityFilter, categoryFilter, sortBy, sortOrder, searchTerm])

  const fetchAnalysisDetails = async () => {
    try {
      setLoading(true)
      console.log('Fetching analysis details for ID:', analysisId)
      const analysis = await analysisService.getAnalysisById(analysisId, analysisType)
      console.log('Analysis details received:', analysis)
      const analysisIssues = analysis.issues || []
      setIssues(analysisIssues)

      // Fetch feedback for each issue
      await fetchIssueFeedback(analysisIssues)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch analysis details:', err)
      setError('Failed to load analysis details')
      setIssues([])
    } finally {
      setLoading(false)
    }
  }

  const applyFiltersAndSorting = () => {
    let filtered = [...issues]

    // Apply search filter
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase()
      filtered = filtered.filter(issue =>
        issue.message?.toLowerCase().includes(searchLower) ||
        issue.rule?.toLowerCase().includes(searchLower) ||
        issue.category?.toLowerCase().includes(searchLower)
      )
    }

    // Apply severity filter
    if (severityFilter !== 'all') {
      filtered = filtered.filter(issue => issue.severity === severityFilter)
    }

    // Apply category filter
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(issue => issue.category === categoryFilter)
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue, bValue

      switch (sortBy) {
        case 'severity':
          // Define severity order: error > warning > info
          const severityOrder = { error: 3, warning: 2, info: 1 }
          aValue = severityOrder[a.severity] || 0
          bValue = severityOrder[b.severity] || 0
          break
        case 'line':
          aValue = a.line || 0
          bValue = b.line || 0
          break
        case 'category':
          aValue = a.category || ''
          bValue = b.category || ''
          break
        default:
          aValue = a.severity || ''
          bValue = b.severity || ''
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0
      } else {
        return aValue < bValue ? 1 : aValue > bValue ? -1 : 0
      }
    })

    setFilteredIssues(filtered)
  }

  const resetFilters = () => {
    setSeverityFilter('all')
    setCategoryFilter('all')
    setSortBy('severity')
    setSortOrder('desc')
    setSearchTerm('')
  }

  // Get unique categories from issues
  const getUniqueCategories = () => {
    const categories = [...new Set(issues.map(issue => issue.category).filter(Boolean))]
    return categories.sort()
  }

  // Get issue counts by severity
  const getIssueCounts = () => {
    const counts = { error: 0, warning: 0, info: 0, total: issues.length }
    issues.forEach(issue => {
      if (counts.hasOwnProperty(issue.severity)) {
        counts[issue.severity]++
      }
    })
    return counts
  }

  const fetchIssueFeedback = async (analysisIssues) => {
    try {
      const feedbackPromises = analysisIssues.map(async (issue) => {
        try {
          const feedback = await feedbackService.getFeedbackByIssue(issue.id)
          return { issueId: issue.id, feedback }
        } catch (error) {
          // No feedback found for this issue
          return { issueId: issue.id, feedback: null }
        }
      })

      const feedbackResults = await Promise.all(feedbackPromises)
      const feedbackMap = {}
      feedbackResults.forEach(({ issueId, feedback }) => {
        feedbackMap[issueId] = feedback
      })
      setIssueFeedback(feedbackMap)
    } catch (error) {
      console.error('Failed to fetch issue feedback:', error)
    }
  }

  const handleFeedbackSubmit = async (feedbackData) => {
    try {
      // Update the local feedback state
      setIssueFeedback(prev => ({
        ...prev,
        [feedbackData.suggestion.id]: {
          type: feedbackData.feedbackType,
          rejectionReasons: feedbackData.rejectionReasons,
          timestamp: new Date(),
          id: feedbackData.response.id
        }
      }))
    } catch (error) {
      console.error('Failed to handle feedback submission:', error)
    }
  }

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return <AlertCircleIcon className="h-4 w-4 text-red-600" />
      case 'high':
        return <AlertCircleIcon className="h-4 w-4 text-orange-500" />
      case 'error':
        return <AlertCircleIcon className="h-4 w-4 text-red-500" />
      case 'warning':
        return <AlertTriangleIcon className="h-4 w-4 text-yellow-500" />
      case 'low':
        return <InfoIcon className="h-4 w-4 text-blue-500" />
      case 'info':
        return <InfoIcon className="h-4 w-4 text-gray-500" />
      case 'suggestion':
        return <LightbulbIcon className="h-4 w-4 text-green-500" />
      default:
        return <InfoIcon className="h-4 w-4 text-gray-500" />
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'high':
        return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low':
        return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'info':
        return 'text-gray-600 bg-gray-50 border-gray-200'
      case 'suggestion':
        return 'text-green-600 bg-green-50 border-green-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  // Color coding function for issue containers based on severity
  const getSeverityColorClasses = (severity, isSuggestion = false) => {
    // Green background for suggestion sections
    if (isSuggestion) {
      return 'bg-green-100 border-green-300 text-green-900'
    }

    // Color mapping for different severity levels
    const colorMap = {
      critical: 'bg-red-100 border-red-300 text-red-900',
      high: 'bg-orange-100 border-orange-300 text-orange-900',
      warning: 'bg-yellow-100 border-yellow-300 text-yellow-900',
      low: 'bg-blue-100 border-blue-300 text-blue-900',
      info: 'bg-gray-100 border-gray-300 text-gray-900',
      error: 'bg-red-100 border-red-300 text-red-900', // Legacy support
      suggestion: 'bg-green-100 border-green-300 text-green-900'
    }

    return colorMap[severity?.toLowerCase()] || colorMap.info
  }

  // Group issues by severity
  const groupedIssues = issues.reduce((groups, issue) => {
    const severity = issue.severity || 'info'
    if (!groups[severity]) {
      groups[severity] = []
    }
    groups[severity].push(issue)
    return groups
  }, {})

  if (loading) {
    return (
      <div className="p-6 bg-gray-50">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border-t border-red-200">
        <p className="text-red-700">{error}</p>
      </div>
    )
  }

  const issueCounts = getIssueCounts()
  const uniqueCategories = getUniqueCategories()

  // Group filtered issues by severity
  const groupedFilteredIssues = filteredIssues.reduce((groups, issue) => {
    const severity = issue.severity || 'info'
    if (!groups[severity]) {
      groups[severity] = []
    }
    groups[severity].push(issue)
    return groups
  }, {})

  return (
    <div className="bg-gray-50 border-t border-gray-200">
      {/* Filtering and Sorting Controls */}
      <div className="px-6 py-4 bg-white border-b border-gray-200">
        <div className="flex flex-col space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <SearchIcon className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search issues by message, rule, or category..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Issue Summary */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h4 className="font-medium text-gray-900">
                Analysis Issues ({filteredIssues.length} of {issues.length})
              </h4>
              <div className="flex items-center space-x-3 text-sm">
                <span className="flex items-center space-x-1">
                  <AlertCircleIcon className="h-4 w-4 text-red-500" />
                  <span className="text-red-600">{issueCounts.error} errors</span>
                </span>
                <span className="flex items-center space-x-1">
                  <AlertTriangleIcon className="h-4 w-4 text-yellow-500" />
                  <span className="text-yellow-600">{issueCounts.warning} warnings</span>
                </span>
                <span className="flex items-center space-x-1">
                  <InfoIcon className="h-4 w-4 text-blue-500" />
                  <span className="text-blue-600">{issueCounts.info} info</span>
                </span>
              </div>
            </div>
            <button
              onClick={resetFilters}
              className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
            >
              Reset Filters
            </button>
          </div>

          {/* Quick Filter Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Quick filters:</span>
            <button
              onClick={() => {
                setSeverityFilter('error')
                setCategoryFilter('all')
              }}
              className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${severityFilter === 'error'
                ? 'bg-red-100 text-red-800 border border-red-200'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Errors Only
            </button>
            <button
              onClick={() => {
                setSeverityFilter('all')
                setCategoryFilter('security')
              }}
              className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${categoryFilter === 'security'
                ? 'bg-orange-100 text-orange-800 border border-orange-200'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Security Issues
            </button>
            <button
              onClick={() => {
                setSeverityFilter('all')
                setCategoryFilter('performance')
              }}
              className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${categoryFilter === 'performance'
                ? 'bg-blue-100 text-blue-800 border border-blue-200'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Performance
            </button>
            <button
              onClick={() => {
                setSeverityFilter('all')
                setCategoryFilter('maintainability')
              }}
              className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${categoryFilter === 'maintainability'
                ? 'bg-green-100 text-green-800 border border-green-200'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Maintainability
            </button>
          </div>

          {/* Filters and Sorting */}
          <div className="flex flex-wrap items-center gap-4">
            {/* Severity Filter */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Severity:</label>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="all">All Severities</option>
                <option value="error">Errors Only</option>
                <option value="warning">Warnings Only</option>
                <option value="info">Info Only</option>
              </select>
            </div>

            {/* Category Filter */}
            {uniqueCategories.length > 0 && (
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Category:</label>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="all">All Categories</option>
                  {uniqueCategories.map(category => (
                    <option key={category} value={category}>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Sort By */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Sort by:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="severity">Severity</option>
                <option value="line">Line Number</option>
                <option value="category">Category</option>
              </select>
            </div>

            {/* Sort Order */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Order:</label>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="desc">High to Low</option>
                <option value="asc">Low to High</option>
              </select>
            </div>
          </div>

          {/* Active Filters Display */}
          {(severityFilter !== 'all' || categoryFilter !== 'all' || searchTerm.trim()) && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Active filters:</span>
              {searchTerm.trim() && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                  Search: "{searchTerm}"
                  <button
                    onClick={() => setSearchTerm('')}
                    className="ml-1 text-indigo-600 hover:text-indigo-800"
                  >
                    ×
                  </button>
                </span>
              )}
              {severityFilter !== 'all' && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                  Severity: {severityFilter}
                  <button
                    onClick={() => setSeverityFilter('all')}
                    className="ml-1 text-indigo-600 hover:text-indigo-800"
                  >
                    ×
                  </button>
                </span>
              )}
              {categoryFilter !== 'all' && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                  Category: {categoryFilter}
                  <button
                    onClick={() => setCategoryFilter('all')}
                    className="ml-1 text-indigo-600 hover:text-indigo-800"
                  >
                    ×
                  </button>
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Issues Display */}
      {filteredIssues.length === 0 ? (
        <div className="px-6 py-8 text-center">
          <InfoIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No issues match your filters</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your filters to see more results.
          </p>
        </div>
      ) : (
        Object.entries(groupedFilteredIssues).map(([severity, severityIssues]) => (
          <div key={severity} className="border-b border-gray-200 last:border-b-0">
            <div className="px-6 py-3 bg-gray-100 border-b border-gray-200">
              <div className="flex items-center space-x-2">
                {getSeverityIcon(severity)}
                <h4 className="font-medium text-gray-900 capitalize">
                  {severity} Issues ({severityIssues.length})
                </h4>
              </div>
            </div>
            <div className="divide-y divide-gray-200">
              {severityIssues.map((issue, index) => {
                // Determine if this is a suggestion-type issue
                const isSuggestion = issue.category?.toLowerCase() === 'suggestion' ||
                  issue.type?.toLowerCase() === 'suggestion' ||
                  issue.severity?.toLowerCase() === 'suggestion'

                // Get color classes for the issue container
                const colorClasses = getSeverityColorClasses(issue.severity, isSuggestion)

                return (
                  <div key={issue.id || index} className={`px-6 py-4 border-l-4 ${colorClasses}`}>
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 mt-0.5">
                        {getSeverityIcon(issue.severity)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <h5 className="text-sm font-medium text-gray-900">
                              {issue.rule || 'Code Issue'}
                            </h5>
                            {issue.line && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                Line {issue.line}
                              </span>
                            )}
                            {issue.category && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                {issue.category}
                              </span>
                            )}
                          </div>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(issue.severity)}`}>
                            {issue.severity}
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-gray-700">
                          {issue.message}
                        </p>
                        {issue.suggestion && (
                          <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-md">
                            <p className="text-sm text-green-800">
                              <strong>Suggestion:</strong> {issue.suggestion}
                            </p>
                          </div>
                        )}

                        {/* Feedback Widget */}
                        <div className="mt-3">
                          <FeedbackWidget
                            suggestion={issue}
                            onFeedbackSubmit={handleFeedbackSubmit}
                            existingFeedback={issueFeedback[issue.id]}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
