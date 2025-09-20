import { useState, useMemo, useEffect, useCallback } from 'react'
import {
  AlertCircleIcon,
  AlertTriangleIcon,
  InfoIcon,
  CheckCircleIcon,
  FilterIcon,
  SortAscIcon,
  SortDescIcon,
  ExternalLinkIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  CodeIcon,
  LightbulbIcon,
} from 'lucide-react'

export function ReviewResults({ 
  issues, 
  onIssueClick, 
  analysisMetrics, 
  onIssueNavigate,
  onMarkersUpdate 
}) {
  const [filter, setFilter] = useState('all') // 'all', 'error', 'warning', 'info'
  const [sortBy, setSortBy] = useState('line') // 'line', 'severity', 'category'
  const [sortOrder, setSortOrder] = useState('asc') // 'asc', 'desc'
  const [expandedIssues, setExpandedIssues] = useState(new Set()) // Track expanded issue details
  const [groupBy, setGroupBy] = useState('none') // 'none', 'severity', 'category'
  const [selectedIssueIndex, setSelectedIssueIndex] = useState(-1) // For keyboard navigation
  const [focusedElement, setFocusedElement] = useState(null) // Track focused element

  // Process and filter issues
  const processedIssues = useMemo(() => {
    if (!Array.isArray(issues)) return groupBy === 'none' ? [] : {}
    
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

    // Group issues if needed
    if (groupBy === 'none') {
      return filtered
    }

    const grouped = {}
    filtered.forEach(issue => {
      const groupKey = groupBy === 'severity' ? issue.severity : (issue.category || 'general')
      if (!grouped[groupKey]) {
        grouped[groupKey] = []
      }
      grouped[groupKey].push(issue)
    })

    return grouped
  }, [issues, filter, sortBy, sortOrder, groupBy])

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

  const toggleIssueExpansion = (issueId) => {
    const newExpanded = new Set(expandedIssues)
    if (newExpanded.has(issueId)) {
      newExpanded.delete(issueId)
    } else {
      newExpanded.add(issueId)
    }
    setExpandedIssues(newExpanded)
  }

  const isIssueExpanded = (issueId) => {
    return expandedIssues.has(issueId)
  }

  // Get flat list of issues for navigation
  const flatIssuesList = useMemo(() => {
    if (groupBy === 'none' && Array.isArray(processedIssues)) {
      return processedIssues
    } else if (typeof processedIssues === 'object') {
      return Object.values(processedIssues).flat()
    }
    return []
  }, [processedIssues, groupBy])

  // Keyboard navigation handlers
  const handleKeyDown = useCallback((event) => {
    if (!flatIssuesList.length) return

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault()
        setSelectedIssueIndex(prev => 
          prev < flatIssuesList.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        event.preventDefault()
        setSelectedIssueIndex(prev => prev > 0 ? prev - 1 : prev)
        break
      case 'Enter':
        event.preventDefault()
        if (selectedIssueIndex >= 0 && selectedIssueIndex < flatIssuesList.length) {
          const selectedIssue = flatIssuesList[selectedIssueIndex]
          if (onIssueClick) {
            onIssueClick(selectedIssue)
          }
        }
        break
      case 'Escape':
        event.preventDefault()
        setSelectedIssueIndex(-1)
        break
      case ' ':
        event.preventDefault()
        if (selectedIssueIndex >= 0 && selectedIssueIndex < flatIssuesList.length) {
          const selectedIssue = flatIssuesList[selectedIssueIndex]
          const issueId = selectedIssue.id || `issue-${selectedIssueIndex}`
          toggleIssueExpansion(issueId)
        }
        break
    }
  }, [flatIssuesList, selectedIssueIndex, onIssueClick, toggleIssueExpansion])

  // Navigation functions
  const navigateToNextIssue = useCallback(() => {
    if (selectedIssueIndex < flatIssuesList.length - 1) {
      const nextIndex = selectedIssueIndex + 1
      setSelectedIssueIndex(nextIndex)
      // onIssueNavigate will be called by useEffect when selectedIssueIndex changes
    }
  }, [selectedIssueIndex, flatIssuesList])

  const navigateToPreviousIssue = useCallback(() => {
    if (selectedIssueIndex > 0) {
      const prevIndex = selectedIssueIndex - 1
      setSelectedIssueIndex(prevIndex)
      // onIssueNavigate will be called by useEffect when selectedIssueIndex changes
    }
  }, [selectedIssueIndex, flatIssuesList])

  // Auto-navigate to first issue when issues change
  useEffect(() => {
    if (flatIssuesList.length > 0 && selectedIssueIndex === -1) {
      setSelectedIssueIndex(0)
    } else if (flatIssuesList.length === 0) {
      setSelectedIssueIndex(-1)
    }
  }, [flatIssuesList.length, selectedIssueIndex])

  // Add keyboard event listeners
  useEffect(() => {
    if (focusedElement) {
      focusedElement.addEventListener('keydown', handleKeyDown)
      return () => {
        focusedElement.removeEventListener('keydown', handleKeyDown)
      }
    }
  }, [handleKeyDown, focusedElement])

  // Synchronize markers with Monaco Editor
  useEffect(() => {
    if (onMarkersUpdate && Array.isArray(issues)) {
      const markers = issues.map(issue => ({
        startLineNumber: issue.line || 1,
        startColumn: issue.column || 1,
        endLineNumber: issue.line || 1,
        endColumn: issue.column ? issue.column + 1 : 100,
        message: issue.message,
        severity: issue.severity === 'error' ? 8 : issue.severity === 'warning' ? 4 : 1, // Monaco severity levels
        source: issue.rule || 'code-review'
      }))
      onMarkersUpdate(markers)
    }
  }, [issues, onMarkersUpdate])

  // Highlight selected issue in editor
  useEffect(() => {
    if (selectedIssueIndex >= 0 && flatIssuesList.length > 0 && onIssueNavigate) {
      const selectedIssue = flatIssuesList[selectedIssueIndex]
      onIssueNavigate(selectedIssue, selectedIssueIndex)
    }
  }, [selectedIssueIndex, flatIssuesList, onIssueNavigate])

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

  const renderIssueItem = (issue, index, globalIndex = null) => {
    const issueId = issue.id || `issue-${index}`
    const isExpanded = isIssueExpanded(issueId)
    const actualIndex = globalIndex !== null ? globalIndex : flatIssuesList.findIndex(i => 
      (i.id || `issue-${flatIssuesList.indexOf(i)}`) === issueId
    )
    const isSelected = selectedIssueIndex === actualIndex

    return (
      <div 
        key={issueId} 
        className={`border-b border-gray-200 last:border-b-0 ${
          isSelected ? 'ring-2 ring-blue-500 ring-inset' : ''
        }`}
      >
        <div 
          className={`p-4 transition-colors ${
            isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'
          } ${onIssueClick ? 'cursor-pointer' : ''}`}
          onClick={() => {
            setSelectedIssueIndex(actualIndex)
            if (onIssueClick) {
              handleIssueClick(issue)
            }
          }}
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
                <div className="flex items-center space-x-2">
                  {(issue.suggestion || issue.codeExample || issue.documentation) && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleIssueExpansion(issueId)
                      }}
                      className="flex items-center text-sm text-gray-500 hover:text-gray-700"
                    >
                      {isExpanded ? (
                        <ChevronDownIcon className="h-4 w-4" />
                      ) : (
                        <ChevronRightIcon className="h-4 w-4" />
                      )}
                      <span className="ml-1">Details</span>
                    </button>
                  )}
                  {onIssueClick && (
                    <button
                      onClick={() => handleIssueClick(issue)}
                      className="flex items-center text-sm text-blue-600 hover:text-blue-800"
                    >
                      <ExternalLinkIcon className="h-4 w-4" />
                      <span className="ml-1">Go to code</span>
                    </button>
                  )}
                </div>
              </div>
              
              <p className="text-gray-700 mt-1 text-sm leading-relaxed">
                {issue.message}
              </p>
              
              {issue.category && issue.category !== 'general' && (
                <div className="mt-2">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                    {issue.category}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Expandable details section */}
        {isExpanded && (issue.suggestion || issue.codeExample || issue.documentation) && (
          <div className="px-4 pb-4 bg-gray-50 border-t border-gray-200">
            <div className="space-y-3">
              {issue.suggestion && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                  <div className="flex items-start">
                    <LightbulbIcon className="h-4 w-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
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

              {issue.codeExample && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                  <div className="flex items-start">
                    <CodeIcon className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="font-medium text-green-800 text-sm mb-2">
                        Example Fix:
                      </div>
                      <pre className="text-green-700 text-sm bg-green-100 p-2 rounded border overflow-x-auto">
                        <code>{issue.codeExample}</code>
                      </pre>
                    </div>
                  </div>
                </div>
              )}

              {issue.documentation && (
                <div className="p-3 bg-purple-50 border border-purple-200 rounded-md">
                  <div className="flex items-start">
                    <InfoIcon className="h-4 w-4 text-purple-500 mr-2 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium text-purple-800 text-sm mb-1">
                        Learn More:
                      </div>
                      <p className="text-purple-700 text-sm leading-relaxed">
                        {issue.documentation}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    )
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
    <div 
      className="border border-gray-300 rounded-md overflow-hidden focus:outline-none focus:ring-2 focus:ring-blue-500"
      tabIndex={0}
      ref={setFocusedElement}
    >
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
            
            {/* Navigation controls */}
            {flatIssuesList.length > 0 && (
              <div className="flex items-center space-x-2 mt-2 text-sm">
                <span className="text-gray-500">Navigate:</span>
                <button
                  onClick={navigateToPreviousIssue}
                  disabled={selectedIssueIndex <= 0}
                  className="px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 rounded"
                >
                  ↑ Prev
                </button>
                <span className="text-gray-500">
                  {selectedIssueIndex >= 0 ? selectedIssueIndex + 1 : 0} of {flatIssuesList.length}
                </span>
                <button
                  onClick={navigateToNextIssue}
                  disabled={selectedIssueIndex >= flatIssuesList.length - 1}
                  className="px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 rounded"
                >
                  ↓ Next
                </button>
                <span className="text-gray-400 text-xs">
                  (Use ↑↓ keys, Enter to go to code, Space to expand)
                </span>
              </div>
            )}
          </div>

          {/* Filter, group and sort controls */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-3">
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
                <span className="text-sm text-gray-500">Group:</span>
                <select
                  value={groupBy}
                  onChange={(e) => setGroupBy(e.target.value)}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value="none">None</option>
                  <option value="severity">By Severity</option>
                  <option value="category">By Category</option>
                </select>
              </div>
            </div>

            <div className="flex items-center space-x-1">
              <span className="text-sm text-gray-500">Sort:</span>
              <button
                onClick={() => toggleSort('line')}
                className={`flex items-center text-sm px-2 py-1 rounded ${
                  sortBy === 'line' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                Line
                {sortBy === 'line' && (
                  sortOrder === 'asc' ? 
                    <SortAscIcon className="h-3 w-3 ml-1" /> : 
                    <SortDescIcon className="h-3 w-3 ml-1" />
                )}
              </button>
              <button
                onClick={() => toggleSort('severity')}
                className={`flex items-center text-sm px-2 py-1 rounded ${
                  sortBy === 'severity' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                Severity
                {sortBy === 'severity' && (
                  sortOrder === 'asc' ? 
                    <SortAscIcon className="h-3 w-3 ml-1" /> : 
                    <SortDescIcon className="h-3 w-3 ml-1" />
                )}
              </button>
              <button
                onClick={() => toggleSort('category')}
                className={`flex items-center text-sm px-2 py-1 rounded ${
                  sortBy === 'category' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                Category
                {sortBy === 'category' && (
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
      <div className="max-h-96 overflow-y-auto">
        {groupBy === 'none' ? (
          // Ungrouped display
          <div>
            {Array.isArray(processedIssues) && processedIssues.map((issue, index) => 
              renderIssueItem(issue, index, index)
            )}
          </div>
        ) : (
          // Grouped display
          <div>
            {Object.entries(processedIssues).map(([groupKey, groupIssues]) => {
              let globalIndexOffset = 0
              // Calculate offset for this group
              const previousGroups = Object.entries(processedIssues).slice(0, 
                Object.keys(processedIssues).indexOf(groupKey)
              )
              globalIndexOffset = previousGroups.reduce((sum, [, issues]) => sum + issues.length, 0)
              
              return (
                <div key={groupKey} className="border-b border-gray-300 last:border-b-0">
                  <div className="bg-gray-100 px-4 py-2 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {groupBy === 'severity' && getSeverityIcon(groupKey)}
                        <h4 className="font-medium text-gray-900 capitalize">
                          {groupBy === 'severity' ? `${groupKey} Issues` : groupKey}
                        </h4>
                        <span className="text-sm text-gray-500">
                          ({groupIssues.length})
                        </span>
                      </div>
                    </div>
                  </div>
                  <div>
                    {groupIssues.map((issue, index) => 
                      renderIssueItem(issue, `${groupKey}-${index}`, globalIndexOffset + index)
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Empty state for filtered results */}
        {((Array.isArray(processedIssues) && processedIssues.length === 0) || 
          (typeof processedIssues === 'object' && Object.keys(processedIssues).length === 0)) && 
          filter !== 'all' && (
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
    </div>
  )
}
