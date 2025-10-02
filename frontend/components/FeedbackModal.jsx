import { useState, useEffect } from 'react'
import { XIcon, AlertCircleIcon, CheckCircleIcon, EditIcon } from 'lucide-react'

/**
 * FeedbackModal component for detailed feedback submission
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether the modal is open
 * @param {Function} props.onClose - Callback to close the modal
 * @param {Function} props.onSubmit - Callback when feedback is submitted
 * @param {Object} props.issue - The issue object to provide feedback on
 * @param {string} props.initialFeedbackType - Initial feedback type ('accept', 'reject', 'modify')
 */
export function FeedbackModal({ 
  isOpen, 
  onClose, 
  onSubmit, 
  issue, 
  initialFeedbackType = 'accept' 
}) {
  const [feedbackType, setFeedbackType] = useState(initialFeedbackType)
  const [feedbackComment, setFeedbackComment] = useState('')
  const [modifiedSuggestion, setModifiedSuggestion] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('')
  const [reviewContext, setReviewContext] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState({})

  // Reset form when modal opens/closes or issue changes
  useEffect(() => {
    if (isOpen) {
      setFeedbackType(initialFeedbackType)
      setFeedbackComment('')
      setModifiedSuggestion(issue?.suggestion || '')
      setExperienceLevel('')
      setReviewContext('')
      setErrors({})
    }
  }, [isOpen, issue, initialFeedbackType])

  const validateForm = () => {
    const newErrors = {}

    if (feedbackType === 'modify' && !modifiedSuggestion.trim()) {
      newErrors.modifiedSuggestion = 'Modified suggestion is required when providing modifications'
    }

    if (feedbackComment && feedbackComment.length > 1000) {
      newErrors.feedbackComment = 'Comment must be less than 1000 characters'
    }

    if (modifiedSuggestion && modifiedSuggestion.length > 5000) {
      newErrors.modifiedSuggestion = 'Modified suggestion must be less than 5000 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)
    try {
      const feedbackData = {
        issueId: issue.id,
        feedbackType,
        feedbackComment: feedbackComment.trim() || null,
        modifiedSuggestion: feedbackType === 'modify' ? modifiedSuggestion.trim() : null,
        userExperienceLevel: experienceLevel || null,
        codeReviewContext: reviewContext || null,
        contextData: {
          originalSuggestion: issue.suggestion,
          issueCategory: issue.category,
          issueSeverity: issue.severity,
          submittedAt: new Date().toISOString()
        }
      }

      await onSubmit(feedbackData)
      onClose()
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      setErrors({ submit: 'Failed to submit feedback. Please try again.' })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      onClose()
    }
  }

  if (!isOpen || !issue) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={handleClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          {/* Header */}
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Provide Feedback
              </h3>
              <button
                onClick={handleClose}
                disabled={isSubmitting}
                className="bg-white rounded-md text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <XIcon className="h-6 w-6" />
              </button>
            </div>

            {/* Issue context */}
            <div className="mb-6 p-3 bg-gray-50 rounded-md">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  {issue.severity === 'error' && <AlertCircleIcon className="h-5 w-5 text-red-500" />}
                  {issue.severity === 'warning' && <AlertCircleIcon className="h-5 w-5 text-yellow-500" />}
                  {issue.severity === 'info' && <CheckCircleIcon className="h-5 w-5 text-blue-500" />}
                </div>
                <div className="ml-3 flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    Line {issue.line}{issue.column ? `, Column ${issue.column}` : ''}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">{issue.message}</p>
                  {issue.suggestion && (
                    <div className="mt-2 p-2 bg-blue-50 rounded border">
                      <p className="text-xs font-medium text-blue-800">AI Suggestion:</p>
                      <p className="text-sm text-blue-700 mt-1">{issue.suggestion}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Feedback Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Response
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="feedbackType"
                      value="accept"
                      checked={feedbackType === 'accept'}
                      onChange={(e) => setFeedbackType(e.target.value)}
                      className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
                    />
                    <span className="ml-2 text-sm text-gray-700">Accept - This suggestion is helpful</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="feedbackType"
                      value="reject"
                      checked={feedbackType === 'reject'}
                      onChange={(e) => setFeedbackType(e.target.value)}
                      className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
                    />
                    <span className="ml-2 text-sm text-gray-700">Reject - This suggestion is not helpful</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="feedbackType"
                      value="modify"
                      checked={feedbackType === 'modify'}
                      onChange={(e) => setFeedbackType(e.target.value)}
                      className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
                    />
                    <span className="ml-2 text-sm text-gray-700">Modify - I have a better suggestion</span>
                  </label>
                </div>
              </div>

              {/* Modified Suggestion (only shown when modify is selected) */}
              {feedbackType === 'modify' && (
                <div>
                  <label htmlFor="modifiedSuggestion" className="block text-sm font-medium text-gray-700 mb-1">
                    Your Improved Suggestion *
                  </label>
                  <textarea
                    id="modifiedSuggestion"
                    value={modifiedSuggestion}
                    onChange={(e) => setModifiedSuggestion(e.target.value)}
                    rows={4}
                    className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                      errors.modifiedSuggestion ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Provide your improved suggestion here..."
                  />
                  {errors.modifiedSuggestion && (
                    <p className="mt-1 text-sm text-red-600">{errors.modifiedSuggestion}</p>
                  )}
                  <p className="mt-1 text-xs text-gray-500">
                    {modifiedSuggestion.length}/5000 characters
                  </p>
                </div>
              )}

              {/* Optional Comment */}
              <div>
                <label htmlFor="feedbackComment" className="block text-sm font-medium text-gray-700 mb-1">
                  Additional Comments (Optional)
                </label>
                <textarea
                  id="feedbackComment"
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  rows={3}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                    errors.feedbackComment ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Any additional context or explanation..."
                />
                {errors.feedbackComment && (
                  <p className="mt-1 text-sm text-red-600">{errors.feedbackComment}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  {feedbackComment.length}/1000 characters
                </p>
              </div>

              {/* Experience Level */}
              <div>
                <label htmlFor="experienceLevel" className="block text-sm font-medium text-gray-700 mb-1">
                  Your Experience Level (Optional)
                </label>
                <select
                  id="experienceLevel"
                  value={experienceLevel}
                  onChange={(e) => setExperienceLevel(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">Select your experience level</option>
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="expert">Expert</option>
                </select>
              </div>

              {/* Review Context */}
              <div>
                <label htmlFor="reviewContext" className="block text-sm font-medium text-gray-700 mb-1">
                  Code Review Context (Optional)
                </label>
                <select
                  id="reviewContext"
                  value={reviewContext}
                  onChange={(e) => setReviewContext(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">Select review context</option>
                  <option value="personal">Personal Project</option>
                  <option value="team">Team Review</option>
                  <option value="production">Production Code</option>
                </select>
              </div>

              {/* Submit Error */}
              {errors.submit && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-600">{errors.submit}</p>
                </div>
              )}
            </form>
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="submit"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Submitting...
                </>
              ) : (
                'Submit Feedback'
              )}
            </button>
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}