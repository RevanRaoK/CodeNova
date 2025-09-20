import React, { useState, useMemo } from 'react'
import {
  AlertCircleIcon,
  AlertTriangleIcon,
  InfoIcon,
  CheckCircleIcon,
  FilterIcon,
  SortAscIcon,
  SortDescIcon,
  ExternalLinkIcon,
} from 'lucide-react'

export function ReviewResults({ issues, onIssueClick, analysisMetrics }) {
  const [filter, setFilter] = useState('all') // 'all', 'error', 'warning', 'info'
  const [sortBy, setSortBy] = useState('line') // 'line', 'severity', 'category'
  const [sortOrder, setSortOrder] = useState('asc') // 'asc', 'desc'

  // Process and filter issues
  const processedIssues = useMemo(() => {
    if (!Array.isArray(issues)) return []
    
    let filtered = issues.filter(issue => {
      if (filter === 'all') return true
      return issue.severity === filter
    })

    // Sort issues
    filtered.sort((a, b) => {
      let aVal, bVal
      
      switch (sortBy) {
        case 'line':
          aVal = a.line || 0
          bVal = b.line || 0
          break
        case 'severity':
          const severityOrder = { error: 3, warning: 2, info: 1 }
          aVal = severityOrder[a.severity] || 0
          bVal = severityOrder[b.severity] || 0
          break
        case 'category':
          aVal = a.category || 'general'
          bVal = b.category || 'general'
          break
        default:
          aVal = a.line || 0
          bVal = b.line || 0
      }

      if (sortOrder === 'desc') {
        return bVal > aVal ? 1 : bVal < aVal ? -1 : 0
      }
      return aVal > bVal ? 1 : aVal < bVal ? -1 : 0
    })

    return filtered
  }, [issues, filter, sortBy, sortOrder])

  // Count issues by severity
  const issueCounts = useMemo(() => {
    if (!Array.isArray(issues)) return { error: 0, warning: 0, info: 0, total: 0 }
    
    return issues.reduce((counts, issue) => {
      counts[issue.severity] = (counts[issue.severity] || 0) + 1
      counts.total++
      return counts
    }, { error: 0, warning: 0, info: 0, total: 0 })
  }, [issues])

  const handleIssueClick = (issue) => {
    if (onIssueClick) {
      onIssueClick(issue)
    }
  }

  const toggleSort = (newSortBy) => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(newSortBy)
      setSortOrder('asc')
    }
  }

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'error':
        return <AlertCircleIcon className="h-5 w-5 text-red-500" />
      case 'warning':
        return <AlertTriangleIcon className="h-5 w-5 text-yellow-500" />
      case 'info':
        return <InfoIcon className="h-5 w-5 text-blue-500" />
      default:
        return <InfoIcon className="h-5 w-5 text-gray-500" />
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'info':
        return 'text-blue-600 bg-blue-50 border-blue-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  if (!Array.isArray(issues) || issues.length === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-md p-6 text-center">
        <CheckCircleIcon className="h-12 w-12 text-green-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-green-800 mb-2">Great job!</h3>
        <p className="text-green-600">No issues found in your code.</p>
        {analysisMetrics && (
          <div className="mt-4 text-sm text-green-700">
            <p>Lines of code: {analysisMetrics.linesOfCode}</p>
            {analysisMetrics.complexity !== undefined && (
              <p>Complexity score: {analysisMetrics.complexity}</p>
            )}
            {analysisMetrics.maintainabilityIndex !== undefined && (
              <p>Maintainability: {analysisMetrics.maintainabilityIndex}%</p>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="border border-gray-300 rounded-md overflow-hidden">
      {/* Header with summary and controls */}
      <div className="bg-gray-100 px-4 py-3 border-b border-gray-300">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
          <div>
            <h3 className="font-medium text-gray-900">
              Analysis Results ({issueCounts.total} issues)
            </h3>
            <div className="flex items-center space-x-4 mt-1 text-sm">
              {issueCounts.error > 0 && (
                <span className="text-red-600">
                  {issueCounts.error} error{issueCounts.error !== 1 ? 's' : ''}
                </span>
              )}
              {issueCounts.warning > 0 && (
                <span className="text-yellow-600">
                  {issueCounts.warning} warning{issueCounts.warning !== 1 ? 's' : ''}
                </span>
              )}
              {issueCounts.info > 0 && (
                <span className="text-blue-600">
                  {issueCounts.info} info
                </span>
              )}
            </div>
          </div>

          {/* Filter and sort controls */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              <FilterIcon className="h-4 w-4 text-gray-500" />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="all">All Issues</option>
                <option value="error">Errors Only</option>
                <option value="warning">Warnings Only</option>
                <option value="info">Info Only</option>
              </select>
            </div>

            <div className="flex items-center space-x-1">
              <button
                onClick={() => toggleSort('line')}
                className="flex items-center text-sm text-gray-600 hover:text-gray-800"
              >
                Line
                {sortBy === 'line' && (
                  sortOrder === 'asc' ? 
                    <SortAscIcon className="h-3 w-3 ml-1" /> : 
                    <SortDescIcon className="h-3 w-3 ml-1" />
                )}
              </button>
              <span className="text-gray-300">|</span>
              <button
                onClick={() => toggleSort('severity')}
                className="flex items-center text-sm text-gray-600 hover:text-gray-800"
              >
                Severity
                {sortBy === 'severity' && (
                  sortOrder === 'asc' ? 
                    <SortAscIcon className="h-3 w-3 ml-1" /> : 
                    <SortDescIcon className="h-3 w-3 ml-1" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Metrics display */}
        {analysisMetrics && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Lines:</span>
                <span className="ml-1 font-medium">{analysisMetrics.linesOfCode}</span>
              </div>
              {analysisMetrics.complexity !== undefined && (
                <div>
                  <span className="text-gray-500">Complexity:</span>
                  <span className="ml-1 font-medium">{analysisMetrics.complexity}</span>
                </div>
              )}
              {analysisMetrics.maintainabilityIndex !== undefined && (
                <div>
                  <span className="text-gray-500">Maintainability:</span>
                  <span className="ml-1 font-medium">{analysisMetrics.maintainabilityIndex}%</span>
                </div>
              )}
              {analysisMetrics.duplicateLines !== undefined && analysisMetrics.duplicateLines > 0 && (
                <div>
                  <span className="text-gray-500">Duplicates:</span>
                  <span className="ml-1 font-medium">{analysisMetrics.duplicateLines}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Issues list */}
      <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {processedIssues.map((issue, index) => (
          <div 
            key={issue.id || `issue-${index}`} 
            className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
              onIssueClick ? 'hover:bg-blue-50' : ''
            }`}
            onClick={() => handleIssueClick(issue)}
          >
            <div className="flex items-start">
              <div className="flex-shrink-0 mr-3 mt-0.5">
                {getSeverityIcon(issue.severity)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">
                      Line {issue.line}{issue.column ? `, Column ${issue.column}` : ''}
                    </span>
                    {issue.rule && (
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getSeverityColor(issue.severity)}`}>
                        {issue.rule}
                      </span>
                    )}
                  </div>
                  {onIssueClick && (
                    <ExternalLinkIcon className="h-4 w-4 text-gray-400" />
                  )}
                </div>
                
                <p className="text-gray-700 mt-1 text-sm leading-relaxed">
                  {issue.message}
                </p>
                
                {issue.category && issue.category !== 'general' && (
                  <div className="mt-1">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                      {issue.category}
                    </span>
                  </div>
                )}
                
                {issue.suggestion && (
                  <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <div className="flex items-start">
                      <InfoIcon className="h-4 w-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                      <div>
                        <div className="font-medium text-blue-800 text-sm mb-1">
                          Suggestion:
                        </div>
                        <p className="text-blue-700 text-sm leading-relaxed">
                          {issue.suggestion}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {processedIssues.length === 0 && filter !== 'all' && (
        <div className="p-6 text-center text-gray-500">
          <FilterIcon className="h-8 w-8 mx-auto mb-2 text-gray-400" />
          <p>No {filter} issues found.</p>
          <button
            onClick={() => setFilter('all')}
            className="mt-2 text-indigo-600 hover:text-indigo-800 text-sm"
          >
            Show all issues
          </button>
        </div>
      )}
    </div>
  )
}
