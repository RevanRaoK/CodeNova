import React, { useState } from 'react';
import { ThumbsUpIcon, ThumbsDownIcon, EditIcon, CheckCircleIcon, XIcon } from 'lucide-react';
import feedbackService from '../services/feedbackService.js';

/**
 * SuggestionFeedbackWidget - Widget for accepting, rejecting, or modifying AI suggestions
 * Provides inline feedback mechanism for code review suggestions
 */
const SuggestionFeedbackWidget = ({ 
  suggestion, 
  onFeedbackSubmit, 
  disabled = false,
  compact = false 
}) => {
  const [feedbackType, setFeedbackType] = useState(null);
  const [showModifyInput, setShowModifyInput] = useState(false);
  const [modifiedSuggestion, setModifiedSuggestion] = useState('');
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleAccept = async () => {
    await submitFeedback('accept');
  };

  const handleReject = async () => {
    await submitFeedback('reject');
  };

  const handleModify = () => {
    setShowModifyInput(true);
    setFeedbackType('modify');
    setModifiedSuggestion(suggestion.suggestion || suggestion.message || '');
  };

  const handleModifySubmit = async () => {
    if (!modifiedSuggestion.trim()) {
      setError('Please provide a modified suggestion');
      return;
    }
    await submitFeedback('modify', modifiedSuggestion);
  };

  const submitFeedback = async (type, modifiedText = null) => {
    if (disabled || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const feedbackData = {
        issueId: suggestion.id,
        feedbackType: type,
        feedbackComment: comment || null,
        modifiedSuggestion: modifiedText || null,
        contextData: {
          suggestionText: suggestion.message || suggestion.suggestion,
          severity: suggestion.severity,
          line: suggestion.line,
          column: suggestion.column,
          category: suggestion.category,
          submittedAt: new Date().toISOString(),
        }
      };

      const response = await feedbackService.submitFeedback(feedbackData);

      setFeedbackType(type);
      setSuccess(true);
      setShowModifyInput(false);

      // Call parent callback
      if (onFeedbackSubmit) {
        onFeedbackSubmit({
          suggestion,
          feedbackType: type,
          modifiedSuggestion: modifiedText,
          comment,
          response
        });
      }

      // Reset success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to submit feedback:', err);
      setError(err.message || 'Failed to submit feedback');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setFeedbackType(null);
    setShowModifyInput(false);
    setModifiedSuggestion('');
    setComment('');
    setError(null);
    setSuccess(false);
  };

  // Success state
  if (success && feedbackType) {
    return (
      <div className="flex items-center space-x-2 p-2 bg-green-50 border border-green-200 rounded-md">
        <CheckCircleIcon className="h-4 w-4 text-green-600" />
        <span className="text-sm text-green-700">
          Feedback submitted: {feedbackType}
        </span>
        <button
          onClick={handleReset}
          className="ml-auto text-green-600 hover:text-green-800"
        >
          <XIcon className="h-4 w-4" />
        </button>
      </div>
    );
  }

  // Submitted feedback state (persistent)
  if (feedbackType && !showModifyInput) {
    const feedbackColors = {
      accept: 'bg-green-50 border-green-200 text-green-700',
      reject: 'bg-red-50 border-red-200 text-red-700',
      modify: 'bg-blue-50 border-blue-200 text-blue-700'
    };

    return (
      <div className={`flex items-center justify-between p-2 border rounded-md ${feedbackColors[feedbackType]}`}>
        <div className="flex items-center space-x-2">
          {feedbackType === 'accept' && <ThumbsUpIcon className="h-4 w-4" />}
          {feedbackType === 'reject' && <ThumbsDownIcon className="h-4 w-4" />}
          {feedbackType === 'modify' && <EditIcon className="h-4 w-4" />}
          <span className="text-sm font-medium">
            {feedbackType === 'accept' && 'Accepted'}
            {feedbackType === 'reject' && 'Rejected'}
            {feedbackType === 'modify' && 'Modified'}
          </span>
        </div>
        <button
          onClick={handleReset}
          className="text-sm hover:underline"
        >
          Change
        </button>
      </div>
    );
  }

  // Modify input state
  if (showModifyInput) {
    return (
      <div className="space-y-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium text-blue-800">Provide your suggestion:</h4>
          <button
            onClick={() => setShowModifyInput(false)}
            className="text-blue-600 hover:text-blue-800"
          >
            <XIcon className="h-4 w-4" />
          </button>
        </div>

        <textarea
          value={modifiedSuggestion}
          onChange={(e) => setModifiedSuggestion(e.target.value)}
          placeholder="Enter your modified suggestion..."
          className="w-full px-3 py-2 text-sm border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={3}
          maxLength={1000}
        />

        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Optional comment..."
          className="w-full px-3 py-2 text-sm border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={2}
          maxLength={500}
        />

        {error && (
          <div className="text-sm text-red-600">{error}</div>
        )}

        <div className="flex items-center space-x-2">
          <button
            onClick={handleModifySubmit}
            disabled={isSubmitting || !modifiedSuggestion.trim()}
            className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Submitting...' : 'Submit'}
          </button>
          <button
            onClick={() => setShowModifyInput(false)}
            disabled={isSubmitting}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  // Default state - Action buttons
  return (
    <div className="space-y-2">
      <div className={`flex items-center ${compact ? 'space-x-1' : 'space-x-2'}`}>
        {/* Accept Button */}
        <button
          onClick={handleAccept}
          disabled={disabled || isSubmitting}
          className={`inline-flex items-center justify-center ${
            compact ? 'px-2 py-1 text-xs' : 'px-3 py-1.5 text-sm'
          } font-medium text-green-700 bg-green-50 border border-green-200 rounded-md hover:bg-green-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
          title="Accept this suggestion"
        >
          <ThumbsUpIcon className={compact ? 'h-3 w-3' : 'h-4 w-4'} />
          {!compact && <span className="ml-1">Accept</span>}
        </button>

        {/* Reject Button */}
        <button
          onClick={handleReject}
          disabled={disabled || isSubmitting}
          className={`inline-flex items-center justify-center ${
            compact ? 'px-2 py-1 text-xs' : 'px-3 py-1.5 text-sm'
          } font-medium text-red-700 bg-red-50 border border-red-200 rounded-md hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
          title="Reject this suggestion"
        >
          <ThumbsDownIcon className={compact ? 'h-3 w-3' : 'h-4 w-4'} />
          {!compact && <span className="ml-1">Reject</span>}
        </button>

        {/* Modify Button */}
        <button
          onClick={handleModify}
          disabled={disabled || isSubmitting}
          className={`inline-flex items-center justify-center ${
            compact ? 'px-2 py-1 text-xs' : 'px-3 py-1.5 text-sm'
          } font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
          title="Modify this suggestion"
        >
          <EditIcon className={compact ? 'h-3 w-3' : 'h-4 w-4'} />
          {!compact && <span className="ml-1">Modify</span>}
        </button>

        {isSubmitting && (
          <div className="flex items-center text-gray-500">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
            {!compact && <span className="ml-1 text-xs">Submitting...</span>}
          </div>
        )}
      </div>

      {error && (
        <div className="text-sm text-red-600">{error}</div>
      )}
    </div>
  );
};

export default SuggestionFeedbackWidget;
