import { useState, useEffect } from 'react';
import {
  ThumbsUpIcon,
  ThumbsDownIcon,
  XIcon,
  CheckCircleIcon,
  AlertCircleIcon,
} from 'lucide-react';
import feedbackService from '../services/feedbackService.js';

/**
 * Enhanced FeedbackWidget component with rejection reasons and real-time updates
 *
 * @param {Object} props
 * @param {Object} props.suggestion - The AI suggestion/issue to provide feedback on
 * @param {Function} props.onFeedbackSubmit - Callback when feedback is submitted
 * @param {boolean} props.disabled - Whether the widget is disabled
 * @param {string} props.size - Size variant ('sm', 'md', 'lg')
 * @param {boolean} props.showLabels - Whether to show text labels
 * @param {Object} props.existingFeedback - Existing feedback for this suggestion
 * @param {boolean} props.realTimeUpdates - Enable real-time feedback status updates
 */
export function FeedbackWidget({
  suggestion,
  onFeedbackSubmit,
  disabled = false,
  size = 'md',
  showLabels = true,
  existingFeedback = null,
  realTimeUpdates = false,
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedFeedback, setSubmittedFeedback] = useState(existingFeedback);
  const [showRejectionReasons, setShowRejectionReasons] = useState(false);
  const [selectedReasons, setSelectedReasons] = useState([]);
  const [customReason, setCustomReason] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Predefined rejection reasons
  const rejectionReasons = [
    { id: 'incorrect', label: 'Incorrect suggestion' },
    { id: 'not_applicable', label: 'Not applicable to my code' },
    { id: 'too_generic', label: 'Too generic or vague' },
    { id: 'already_implemented', label: 'Already implemented' },
    { id: 'performance_concern', label: 'Performance concerns' },
    { id: 'style_preference', label: 'Style preference' },
    { id: 'context_missing', label: 'Missing context' },
    { id: 'others', label: 'Others (please specify)' },
  ];

  // Real-time updates effect
  useEffect(() => {
    if (realTimeUpdates && suggestion?.id && !submittedFeedback) {
      const checkFeedbackStatus = async () => {
        try {
          const feedback = await feedbackService.getFeedbackByIssue(
            suggestion.id
          );
          if (feedback) {
            setSubmittedFeedback(feedback);
          }
        } catch (error) {
          // Silently handle - feedback might not exist yet
        }
      };

      const interval = setInterval(checkFeedbackStatus, 5000); // Check every 5 seconds
      return () => clearInterval(interval);
    }
  }, [realTimeUpdates, suggestion?.id, submittedFeedback]);

  const handleAccept = async () => {
    await handleFeedback('accept');
  };

  const handleReject = () => {
    setShowRejectionReasons(true);
    setError(null);
  };

  const handleRejectSubmit = async () => {
    if (selectedReasons.length === 0) {
      setError('Please select at least one rejection reason');
      return;
    }

    if (selectedReasons.includes('others') && !customReason.trim()) {
      setError('Please provide a custom reason when selecting "Others"');
      return;
    }

    const reasons = selectedReasons.filter((reason) => reason !== 'others');
    if (selectedReasons.includes('others') && customReason.trim()) {
      reasons.push(customReason.trim());
    }

    await handleFeedback('reject', reasons);
  };

  const handleFeedback = async (feedbackType, rejectionReasons = null) => {
    if (disabled || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const feedbackData = {
        issueId: suggestion.id,
        feedbackType,
        feedbackComment: rejectionReasons && rejectionReasons.length > 0 
          ? `Rejection reasons: ${rejectionReasons.join(', ')}` 
          : null,
        contextData: {
          suggestionText: (suggestion.message || suggestion.suggestion || '').substring(0, 500), // Limit to 500 chars
          severity: suggestion.severity,
          line: suggestion.line,
          column: suggestion.column,
          category: suggestion.category,
          rejectionReasonsCount: rejectionReasons ? rejectionReasons.length : 0, // Just count, not full reasons
          submittedAt: new Date().toISOString(),
        },
      };

      const response = await feedbackService.submitFeedback(feedbackData);

      setSubmittedFeedback({
        type: feedbackType,
        rejectionReasons,
        timestamp: new Date(),
        id: response.id,
      });

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);

      // Reset rejection form
      setShowRejectionReasons(false);
      setSelectedReasons([]);
      setCustomReason('');

      // Call parent callback
      if (onFeedbackSubmit) {
        onFeedbackSubmit({
          suggestion,
          feedbackType,
          rejectionReasons,
          response,
        });
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      setError(error.message || 'Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReasonChange = (reasonId) => {
    setSelectedReasons((prev) =>
      prev.includes(reasonId)
        ? prev.filter((id) => id !== reasonId)
        : [...prev, reasonId]
    );
    setError(null);
  };

  const handleReset = () => {
    setSubmittedFeedback(null);
    setShowRejectionReasons(false);
    setSelectedReasons([]);
    setCustomReason('');
    setError(null);
    setSuccess(false);
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'px-2 py-1 text-xs';
      case 'lg':
        return 'px-4 py-2 text-base';
      default:
        return 'px-3 py-1.5 text-sm';
    }
  };

  const getIconSize = () => {
    switch (size) {
      case 'sm':
        return 'h-3 w-3';
      case 'lg':
        return 'h-5 w-5';
      default:
        return 'h-4 w-4';
    }
  };

  const baseButtonClasses = `
    inline-flex items-center justify-center rounded-md border font-medium
    transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
    ${getSizeClasses()}
  `;

  // Success state
  if (success) {
    return (
      <div className="flex items-center space-x-2 p-2 bg-green-50 border border-green-200 rounded-md">
        <CheckCircleIcon className="h-4 w-4 text-green-600" />
        <span className="text-sm text-green-700">
          Feedback submitted successfully!
        </span>
      </div>
    );
  }

  // Submitted feedback state
  if (submittedFeedback) {
    const isAccepted = submittedFeedback.type === 'accept';
    const isRejected = submittedFeedback.type === 'reject';

    return (
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <div
            className={`
            ${baseButtonClasses}
            ${
              isAccepted
                ? 'bg-green-100 border-green-300 text-green-700'
                : 'bg-red-100 border-red-300 text-red-700'
            }
          `}
          >
            {isAccepted && <ThumbsUpIcon className={getIconSize()} />}
            {isRejected && <ThumbsDownIcon className={getIconSize()} />}
            {showLabels && (
              <span className="ml-1">
                {isAccepted ? 'Accepted' : 'Rejected'}
              </span>
            )}
          </div>

          <button
            onClick={handleReset}
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

        {/* Show rejection reasons if rejected */}
        {isRejected && submittedFeedback.rejectionReasons && (
          <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded border">
            <strong>Rejection reasons:</strong>
            <ul className="mt-1 list-disc list-inside">
              {submittedFeedback.rejectionReasons.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // Rejection reasons form
  if (showRejectionReasons) {
    return (
      <div className="space-y-3 p-3 bg-red-50 border border-red-200 rounded-md">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium text-red-800">
            Why are you rejecting this suggestion?
          </h4>
          <button
            onClick={() => setShowRejectionReasons(false)}
            className="text-red-600 hover:text-red-800"
          >
            <XIcon className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-2">
          {rejectionReasons.map((reason) => (
            <label key={reason.id} className="flex items-start space-x-2">
              <input
                type="checkbox"
                checked={selectedReasons.includes(reason.id)}
                onChange={() => handleReasonChange(reason.id)}
                className="mt-0.5 h-4 w-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
              />
              <span className="text-sm text-gray-700">{reason.label}</span>
            </label>
          ))}
        </div>

        {/* Custom reason input */}
        {selectedReasons.includes('others') && (
          <div>
            <textarea
              value={customReason}
              onChange={(e) => setCustomReason(e.target.value)}
              placeholder="Please specify your reason..."
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
              rows={2}
              maxLength={500}
            />
            <p className="text-xs text-gray-500 mt-1">
              {customReason.length}/500 characters
            </p>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="flex items-center space-x-2 text-red-600">
            <AlertCircleIcon className="h-4 w-4" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* Submit buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleRejectSubmit}
            disabled={isSubmitting}
            className={`
              ${baseButtonClasses}
              bg-red-600 border-red-600 text-white hover:bg-red-700
              focus:ring-red-500
            `}
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                Submitting...
              </>
            ) : (
              'Submit Rejection'
            )}
          </button>
          <button
            onClick={() => setShowRejectionReasons(false)}
            disabled={isSubmitting}
            className={`
              ${baseButtonClasses}
              bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200
            `}
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  // Default state - Accept/Reject buttons
  return (
    <div className="space-y-2">
      <div className="flex items-center space-x-1">
        {/* Accept Button */}
        <button
          onClick={handleAccept}
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
          onClick={handleReject}
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

        {isSubmitting && (
          <div className="flex items-center text-gray-500">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
            <span className="ml-1 text-xs">Submitting...</span>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="flex items-center space-x-2 text-red-600 text-sm">
          <AlertCircleIcon className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
