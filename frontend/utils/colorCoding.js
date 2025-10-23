/**
 * Color coding utility functions for review results
 * Provides consistent color schemes with accessibility compliance
 */

// Color scheme mapping based on requirements
export const SEVERITY_COLORS = {
  critical: {
    background: 'bg-red-100',
    border: 'border-red-300',
    text: 'text-red-900',
    icon: 'text-red-600',
    badge: 'bg-red-100 text-red-800 border-red-200'
  },
  high: {
    background: 'bg-orange-100',
    border: 'border-orange-300',
    text: 'text-orange-900',
    icon: 'text-orange-500',
    badge: 'bg-orange-100 text-orange-800 border-orange-200'
  },
  warning: {
    background: 'bg-yellow-100',
    border: 'border-yellow-300',
    text: 'text-yellow-900',
    icon: 'text-yellow-500',
    badge: 'bg-yellow-100 text-yellow-800 border-yellow-200'
  },
  low: {
    background: 'bg-blue-100',
    border: 'border-blue-300',
    text: 'text-blue-900',
    icon: 'text-blue-500',
    badge: 'bg-blue-100 text-blue-800 border-blue-200'
  },
  info: {
    background: 'bg-gray-100',
    border: 'border-gray-300',
    text: 'text-gray-900',
    icon: 'text-gray-500',
    badge: 'bg-gray-100 text-gray-800 border-gray-200'
  },
  suggestion: {
    background: 'bg-green-100',
    border: 'border-green-300',
    text: 'text-green-900',
    icon: 'text-green-500',
    badge: 'bg-green-100 text-green-800 border-green-200'
  },
  // Legacy support for 'error' severity
  error: {
    background: 'bg-red-100',
    border: 'border-red-300',
    text: 'text-red-900',
    icon: 'text-red-500',
    badge: 'bg-red-100 text-red-800 border-red-200'
  }
}

/**
 * Get color classes for a severity level
 * @param {string} severity - The severity level (critical, high, warning, low, info, suggestion, error)
 * @param {string} type - The type of styling (background, border, text, icon, badge)
 * @returns {string} CSS classes for the specified severity and type
 */
export function getSeverityColorClass(severity, type = 'background') {
  const normalizedSeverity = severity?.toLowerCase() || 'info'
  const colorConfig = SEVERITY_COLORS[normalizedSeverity] || SEVERITY_COLORS.info
  return colorConfig[type] || ''
}

/**
 * Get combined color classes for issue containers
 * @param {string} severity - The severity level
 * @param {boolean} isSuggestion - Whether this is a suggestion-type issue
 * @returns {string} Combined CSS classes for background, border, and text
 */
export function getSeverityColorClasses(severity, isSuggestion = false) {
  // Override severity for suggestion sections
  const effectiveSeverity = isSuggestion ? 'suggestion' : severity
  const normalizedSeverity = effectiveSeverity?.toLowerCase() || 'info'
  const colorConfig = SEVERITY_COLORS[normalizedSeverity] || SEVERITY_COLORS.info
  
  return `${colorConfig.background} ${colorConfig.border} ${colorConfig.text}`
}

/**
 * Get icon color class for severity
 * @param {string} severity - The severity level
 * @returns {string} CSS class for icon color
 */
export function getSeverityIconColor(severity) {
  return getSeverityColorClass(severity, 'icon')
}

/**
 * Get badge color classes for severity
 * @param {string} severity - The severity level
 * @returns {string} CSS classes for badge styling
 */
export function getSeverityBadgeClasses(severity) {
  return getSeverityColorClass(severity, 'badge')
}

/**
 * Get accessibility label for severity level
 * @param {string} severity - The severity level
 * @returns {string} Human-readable label for screen readers
 */
export function getSeverityAccessibilityLabel(severity) {
  const labels = {
    critical: 'Critical severity issue',
    high: 'High severity issue',
    warning: 'Warning level issue',
    low: 'Low severity issue',
    info: 'Informational issue',
    suggestion: 'Suggestion for improvement',
    error: 'Error level issue'
  }
  
  const normalizedSeverity = severity?.toLowerCase() || 'info'
  return labels[normalizedSeverity] || labels.info
}

/**
 * Get tooltip text for severity level
 * @param {string} severity - The severity level
 * @returns {string} Tooltip text explaining the severity level
 */
export function getSeverityTooltip(severity) {
  const tooltips = {
    critical: 'Critical: Requires immediate attention - may cause system failures',
    high: 'High: Important issue that should be addressed soon',
    warning: 'Warning: Potential issue that may cause problems',
    low: 'Low: Minor issue or improvement opportunity',
    info: 'Info: General information or documentation',
    suggestion: 'Suggestion: Recommended improvement or best practice',
    error: 'Error: Code error that needs to be fixed'
  }
  
  const normalizedSeverity = severity?.toLowerCase() || 'info'
  return tooltips[normalizedSeverity] || tooltips.info
}

/**
 * Check if a severity level is considered high priority
 * @param {string} severity - The severity level
 * @returns {boolean} True if the severity is high priority (critical, high, error)
 */
export function isHighPrioritySeverity(severity) {
  const highPriorityLevels = ['critical', 'high', 'error']
  return highPriorityLevels.includes(severity?.toLowerCase())
}

/**
 * Sort severities by priority (highest to lowest)
 * @param {string} a - First severity level
 * @param {string} b - Second severity level
 * @returns {number} Sort comparison result
 */
export function compareSeverityPriority(a, b) {
  const priorityOrder = {
    critical: 6,
    high: 5,
    error: 4,
    warning: 3,
    low: 2,
    info: 1,
    suggestion: 0
  }
  
  const aPriority = priorityOrder[a?.toLowerCase()] || 1
  const bPriority = priorityOrder[b?.toLowerCase()] || 1
  
  return bPriority - aPriority // Descending order (highest priority first)
}