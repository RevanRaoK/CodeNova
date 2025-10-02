import { useState } from 'react'
import { ThumbsUpIcon, ThumbsDownIcon, EditIcon, XIcon } from 'lucide-react'

/**
 * FeedbackButton component for quick accept/reject actions on AI suggestions
 * 
 * @param {Object} props
 * @param {string} props.issueId - Unique identifier for the code issue
 * @param {Function} props.onFeedback - Callback function when feedback is submitted
 * @param {boolean} props.disabled - Whether the buttons are disabled
 * @param {string} props.size - Size variant ('sm', 'md', 'lg')
 * @param {boolean} props.showLabels - Whether to show text labels
 * @param {Object} props.existingFeedback - Existing feedback for this issue
 */
export function FeedbackButton({ 
  issueId, 
  onFeedback, 
  disabled = false, 
  size = 'md',
  showLabels = true,
  existingFeedback = null
}) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submittedFeedback, setSubmittedFeedback] = useState(existingFeedback)

  const handleFeedback = async (feedbackType) => {
    if (disabled || isSubmitting) return

    setIsSubmitting(true)
    try {
      await onFeedback({
        issueId,
        feedbackType,
        timestamp: new Date().toISOString()
      })
      
      setSubmittedFeedback({ type: feedbackType, timestamp: new Date() })
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      // Reset state on error
      setSubmittedFeedback(null)
    } finally {
      setIsSubmitting(false)
    }
  }

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'px-2 py-1 text-xs'
      case 'lg':
        return 'px-4 py-2 text-base'
      default:
        return 'px-3 py-1.5 text-sm'
    }
  }

  const getIconSize = () => {
    switch (size) {
      case 'sm':
        return 'h-3 w-3'
      case 'lg':
        return 'h-5 w-5'
      default:
        return 'h-4 w-4'
    }
  }

  const baseButtonClasses = `
    inline-flex items-center justify-center rounded-md border font-medium
    transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
    ${getSizeClasses()}
  `

  // If feedback has been submitted, show the submitted state
  if (submittedFeedback) {
    const isAccepted = submittedFeedback.type === 'accept'
    const isRejected = submittedFeedback.type === 'reject'
    const isModified = submittedFeedback.type === 'modify'

    return (
      <div className="flex items-center space-x-2">
        <div className={`
          ${baseButtonClasses}
          ${isAccepted ? 'bg-green-100 border-green-300 text-green-700' : 
            isRejected ? 'bg-red-100 border-red-300 text-red-700' :
            'bg-blue-100 border-blue-300 text-blue-700'}
        `}>
          {isAccepted && <ThumbsUpIcon className={getIconSize()} />}
          {isRejected && <ThumbsDownIcon className={getIconSize()} />}
          {isModified && <EditIcon className={getIconSize()} />}
          {showLabels && (
            <span className="ml-1">
              {isAccepted ? 'Accepted' : isRejected ? 'Rejected' : 'Modified'}
            </span>
          )}
        </div>
        
        <button
          onClick={() => setSubmittedFeedback(null)}
          className={`
            ${baseButtonClasses}
            bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200
          `}
          title="Change feedback"
        >
          <XIcon className={getIconSize()} />
          {showLabels && <span className="ml-1">Change</span>}
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center space-x-1">
      {/* Accept Button */}
      <button
        onClick={() => handleFeedback('accept')}
        disabled={disabled || isSubmitting}
        className={`
          ${baseButtonClasses}
          bg-green-50 border-green-200 text-green-700 hover:bg-green-100
          focus:ring-green-500
        `}
        title="Accept this suggestion"
      >
        <ThumbsUpIcon className={getIconSize()} />
        {showLabels && <span className="ml-1">Accept</span>}
      </button>

      {/* Reject Button */}
      <button
        onClick={() => handleFeedback('reject')}
        disabled={disabled || isSubmitting}
        className={`
          ${baseButtonClasses}
          bg-red-50 border-red-200 text-red-700 hover:bg-red-100
          focus:ring-red-500
        `}
        title="Reject this suggestion"
      >
        <ThumbsDownIcon className={getIconSize()} />
        {showLabels && <span className="ml-1">Reject</span>}
      </button>

      {/* Modify Button */}
      <button
        onClick={() => handleFeedback('modify')}
        disabled={disabled || isSubmitting}
        className={`
          ${baseButtonClasses}
          bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100
          focus:ring-blue-500
        `}
        title="Modify this suggestion"
      >
        <EditIcon className={getIconSize()} />
        {showLabels && <span className="ml-1">Modify</span>}
      </button>

      {isSubmitting && (
        <div className="flex items-center text-gray-500">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
          <span className="ml-1 text-xs">Submitting...</span>
        </div>
      )}
    </div>
  )
}