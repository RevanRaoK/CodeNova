import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, CheckCircle, XCircle, Edit3, Loader2 } from 'lucide-react';
import { useNotification } from '../contexts/NotificationContext';
import feedbackService from '../services/feedbackService';

/**
 * FeedbackLearningIntegration - Component that connects user feedback to the learning module
 * Shows how feedback is being used to improve AI suggestions
 */
const FeedbackLearningIntegration = ({ issueId, suggestion, onFeedbackSubmit }) => {
  const [feedbackType, setFeedbackType] = useState(null);
  const [comment, setComment] = useState('');
  const [modifiedSuggestion, setModifiedSuggestion] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showModifyInput, setShowModifyInput] = useState(false);
  const [learningImpact, setLearningImpact] = useState(null);
  const { showSuccess, showError, showInfo } = useNotification();

  // Handle feedback submission
  const handleSubmitFeedback = async (type) => {
    setSubmitting(true);

    try {
      const feedbackData = {
        issue_id: issueId,
        feedback_type: type,
        comment: comment || undefined,
        modified_suggestion: type === 'modify' ? modifiedSuggestion : undefined,
      };

      const result = await feedbackService.submitFeedback(feedbackData);
      
      setFeedbackType(type);
      setLearningImpact(result.learning_impact);

      // Show success message with learning impact
      showSuccess(
        `Feedback submitted! ${result.learning_impact?.message || 'This will help improve future suggestions.'}`,
        { title: 'Thank you for your feedback' }
      );

      // Call parent callback
      if (onFeedbackSubmit) {
        onFeedbackSubmit(result);
      }

      // Reset form
      setComment('');
      setModifiedSuggestion('');
      setShowModifyInput(false);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      showError(`Failed to submit feedback: ${error.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  // Handle modify button click
  const handleModifyClick = () => {
    setShowModifyInput(true);
    setModifiedSuggestion(suggestion || '');
  };

  // Handle modify submission
  const handleModifySubmit = () => {
    if (!modifiedSuggestion.trim()) {
      showError('Please provide a modified suggestion');
      return;
    }
    handleSubmitFeedback('modify');
  };

  return (
    <div className="space-y-4">
      {/* Feedback Buttons */}
      {!feedbackType && !submitting && (
        <div className="flex items-center space-x-3">
          <p className="text-sm text-gray-600 font-medium">Was this suggestion helpful?</p>
          
          <button
            onClick={() => handleSubmitFeedback('accept')}
            className="inline-flex items-center px-3 py-1.5 border border-green-300 text-sm font-medium rounded-md text-green-700 bg-green-50 hover:bg-green-100 transition-colors"
            title="Accept this suggestion"
          >
            <CheckCircle className="h-4 w-4 mr-1" />
            Accept
          </button>

          <button
            onClick={() => handleSubmitFeedback('reject')}
            className="inline-flex items-center px-3 py-1.5 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-red-50 hover:bg-red-100 transition-colors"
            title="Reject this suggestion"
          >
            <XCircle className="h-4 w-4 mr-1" />
            Reject
          </button>

          <button
            onClick={handleModifyClick}
            className="inline-flex items-center px-3 py-1.5 border border-blue-300 text-sm font-medium rounded-md text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
            title="Suggest a modification"
          >
            <Edit3 className="h-4 w-4 mr-1" />
            Modify
          </button>
        </div>
      )}

      {/* Submitting State */}
      {submitting && (
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Submitting feedback...</span>
        </div>
      )}

      {/* Feedback Submitted */}
      {feedbackType && !submitting && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-green-800">
                Feedback submitted successfully
              </p>
              <p className="text-xs text-green-700 mt-1">
                Your {feedbackType} feedback has been recorded and will help improve future suggestions.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Modify Input */}
      {showModifyInput && !feedbackType && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
          <label className="block text-sm font-medium text-gray-700">
            Suggest a better solution:
          </label>
          <textarea
            value={modifiedSuggestion}
            onChange={(e) => setModifiedSuggestion(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            rows={4}
            placeholder="Enter your improved suggestion..."
          />
          <div className="flex items-center space-x-2">
            <button
              onClick={handleModifySubmit}
              disabled={submitting || !modifiedSuggestion.trim()}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Submit Modification
            </button>
            <button
              onClick={() => {
                setShowModifyInput(false);
                setModifiedSuggestion('');
              }}
              className="px-4 py-2 bg-white text-gray-700 text-sm font-medium rounded-md border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Optional Comment */}
      {!feedbackType && !showModifyInput && (
        <div className="pt-2">
          <label className="block text-xs text-gray-600 mb-1">
            Additional comments (optional):
          </label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            rows={2}
            placeholder="Any additional feedback..."
          />
        </div>
      )}

      {/* Learning Impact Display */}
      {learningImpact && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <Brain className="h-5 w-5 text-indigo-600 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-indigo-800 flex items-center">
                Learning Module Updated
                <TrendingUp className="h-4 w-4 ml-1" />
              </p>
              <p className="text-xs text-indigo-700 mt-1">
                {learningImpact.message || 'Your feedback has been processed by our learning system.'}
              </p>
              {learningImpact.confidence_improvement && (
                <p className="text-xs text-indigo-600 mt-1">
                  Model confidence improved by {learningImpact.confidence_improvement}%
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FeedbackLearningIntegration;
