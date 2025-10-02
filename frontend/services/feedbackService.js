import httpClient from './httpClient.js';

/**
 * Feedback service for handling user feedback on AI suggestions
 */
class FeedbackService {
  /**
   * Submit feedback for a specific issue
   * @param {Object} feedbackData - Feedback submission data
   * @param {string} feedbackData.issueId - Unique identifier for the code issue
   * @param {string} feedbackData.feedbackType - Type of feedback ('accept', 'reject', 'modify')
   * @param {string} [feedbackData.feedbackComment] - Optional comment
   * @param {string} [feedbackData.modifiedSuggestion] - Modified suggestion for 'modify' type
   * @param {string} [feedbackData.userExperienceLevel] - User's experience level
   * @param {string} [feedbackData.codeReviewContext] - Context of the code review
   * @param {Object} [feedbackData.contextData] - Additional context data
   * @returns {Promise<Object>} Feedback submission response
   */
  async submitFeedback(feedbackData) {
    try {
      const response = await httpClient.post('/feedback', {
        issue_id: feedbackData.issueId,
        feedback_type: feedbackData.feedbackType,
        feedback_comment: feedbackData.feedbackComment || null,
        modified_suggestion: feedbackData.modifiedSuggestion || null,
        user_experience_level: feedbackData.userExperienceLevel || null,
        code_review_context: feedbackData.codeReviewContext || null,
        context_data: feedbackData.contextData || {}
      });

      return this.processFeedbackResponse(response.data);
    } catch (error) {
      console.error('Feedback submission failed:', error);
      throw this.handleFeedbackError(error);
    }
  }

  /**
   * Get feedback statistics for the current user
   * @param {Object} [options] - Query options
   * @param {string} [options.timeRange] - Time range for statistics ('day', 'week', 'month', 'year')
   * @param {string} [options.issueType] - Filter by issue type
   * @returns {Promise<Object>} Feedback statistics
   */
  async getFeedbackStats(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.timeRange) params.append('time_range', options.timeRange);
      if (options.issueType) params.append('issue_type', options.issueType);

      const response = await httpClient.get(`/feedback/stats?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch feedback stats:', error);
      throw this.handleFeedbackError(error);
    }
  }

  /**
   * Get feedback for a specific issue
   * @param {string} issueId - The issue ID
   * @returns {Promise<Object>} Feedback data for the issue
   */
  async getFeedbackByIssue(issueId) {
    try {
      const response = await httpClient.get(`/feedback/issue/${issueId}`);
      return this.processFeedbackResponse(response.data);
    } catch (error) {
      console.error('Failed to fetch issue feedback:', error);
      throw this.handleFeedbackError(error);
    }
  }

  /**
   * Get user's feedback history
   * @param {Object} [options] - Query options
   * @param {number} [options.page] - Page number (1-based)
   * @param {number} [options.pageSize] - Items per page
   * @param {string} [options.feedbackType] - Filter by feedback type
   * @returns {Promise<Object>} List of user's feedback with pagination info
   */
  async getUserFeedbackHistory(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.page) params.append('page', options.page);
      if (options.pageSize) params.append('page_size', options.pageSize);
      if (options.feedbackType) params.append('feedback_type', options.feedbackType);

      const response = await httpClient.get(`/feedback/history?${params}`);
      
      return {
        feedback: response.data.feedback?.map(item => this.processFeedbackResponse(item)) || [],
        totalCount: response.data.total_count || 0,
        page: response.data.page || 1,
        pageSize: response.data.page_size || 20,
        hasNext: response.data.has_next || false,
        hasPrevious: response.data.has_previous || false
      };
    } catch (error) {
      console.error('Failed to fetch feedback history:', error);
      throw this.handleFeedbackError(error);
    }
  }

  /**
   * Update existing feedback
   * @param {string} feedbackId - The feedback ID to update
   * @param {Object} updateData - Updated feedback data
   * @returns {Promise<Object>} Updated feedback response
   */
  async updateFeedback(feedbackId, updateData) {
    try {
      const response = await httpClient.put(`/feedback/${feedbackId}`, {
        feedback_type: updateData.feedbackType,
        feedback_comment: updateData.feedbackComment || null,
        modified_suggestion: updateData.modifiedSuggestion || null,
        user_experience_level: updateData.userExperienceLevel || null,
        code_review_context: updateData.codeReviewContext || null,
        context_data: updateData.contextData || {}
      });

      return this.processFeedbackResponse(response.data);
    } catch (error) {
      console.error('Feedback update failed:', error);
      throw this.handleFeedbackError(error);
    }
  }

  /**
   * Delete feedback
   * @param {string} feedbackId - The feedback ID to delete
   * @returns {Promise<void>}
   */
  async deleteFeedback(feedbackId) {
    try {
      await httpClient.delete(`/feedback/${feedbackId}`);
    } catch (error) {
      console.error('Failed to delete feedback:', error);
      throw this.handleFeedbackError(error);
    }
  }

  /**
   * Get issue details by ID
   * @param {string} issueId - The issue ID
   * @returns {Promise<Object>} Issue details
   */
  async getIssueById(issueId) {
    try {
      const response = await httpClient.get(`/issues/${issueId}`);
      return this.processIssueResponse(response.data);
    } catch (error) {
      console.error('Failed to fetch issue details:', error);
      throw this.handleFeedbackError(error);
    }
  }

  /**
   * Get issues for a specific analysis
   * @param {string} analysisId - The analysis ID
   * @returns {Promise<Array>} List of issues for the analysis
   */
  async getIssuesByAnalysis(analysisId) {
    try {
      const response = await httpClient.get(`/analyses/${analysisId}/issues`);
      return response.data.issues?.map(issue => this.processIssueResponse(issue)) || [];
    } catch (error) {
      console.error('Failed to fetch analysis issues:', error);
      throw this.handleFeedbackError(error);
    }
  }

  /**
   * Process and normalize feedback response data
   * @param {Object} feedbackData - Raw feedback data from API
   * @returns {Object} Processed feedback data
   */
  processFeedbackResponse(feedbackData) {
    return {
      id: feedbackData.id,
      issueId: feedbackData.issue_id,
      userId: feedbackData.user_id,
      feedbackType: feedbackData.feedback_type,
      feedbackValue: feedbackData.feedback_value,
      feedbackComment: feedbackData.feedback_comment,
      modifiedSuggestion: feedbackData.modified_suggestion,
      userExperienceLevel: feedbackData.user_experience_level,
      codeReviewContext: feedbackData.code_review_context,
      contextData: feedbackData.context_data || {},
      createdAt: feedbackData.created_at,
      updatedAt: feedbackData.updated_at
    };
  }

  /**
   * Process and normalize issue response data
   * @param {Object} issueData - Raw issue data from API
   * @returns {Object} Processed issue data
   */
  processIssueResponse(issueData) {
    return {
      id: issueData.id,
      analysisId: issueData.analysis_id,
      patternType: issueData.pattern_type,
      severity: issueData.severity,
      location: issueData.location || {},
      suggestionText: issueData.suggestion_text,
      codeContext: issueData.code_context,
      createdAt: issueData.created_at,
      // Map to ReviewResults expected format
      line: issueData.location?.line || 0,
      column: issueData.location?.column || 0,
      message: issueData.suggestion_text,
      suggestion: issueData.suggestion_text,
      category: issueData.pattern_type || 'general'
    };
  }

  /**
   * Handle feedback-related errors
   * @param {Error} error - The error to handle
   * @returns {Error} Processed error with user-friendly message
   */
  handleFeedbackError(error) {
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          return new Error(data.detail || 'Invalid feedback data. Please check your input.');
        case 401:
          return new Error('Authentication required. Please log in.');
        case 403:
          return new Error('Access forbidden. You may not have permission to submit feedback.');
        case 404:
          return new Error('Issue or feedback not found.');
        case 409:
          return new Error('Feedback already exists for this issue. You can update your existing feedback.');
        case 422:
          return new Error(data.detail || 'Validation error. Please check your feedback data.');
        case 429:
          return new Error('Too many feedback submissions. Please try again later.');
        case 500:
          return new Error('Server error during feedback submission. Please try again later.');
        default:
          return new Error(data.detail || 'Feedback operation failed. Please try again.');
      }
    } else if (error.request) {
      return new Error('Network error. Please check your connection and try again.');
    } else {
      return new Error(error.message || 'An unexpected error occurred during feedback submission.');
    }
  }

  /**
   * Validate feedback data before submission
   * @param {Object} feedbackData - Feedback data to validate
   * @throws {Error} If feedback data is invalid
   */
  validateFeedbackData(feedbackData) {
    if (!feedbackData.issueId) {
      throw new Error('Issue ID is required');
    }

    if (!feedbackData.feedbackType) {
      throw new Error('Feedback type is required');
    }

    const validFeedbackTypes = ['accept', 'reject', 'modify'];
    if (!validFeedbackTypes.includes(feedbackData.feedbackType)) {
      throw new Error(`Invalid feedback type. Must be one of: ${validFeedbackTypes.join(', ')}`);
    }

    if (feedbackData.feedbackType === 'modify' && !feedbackData.modifiedSuggestion?.trim()) {
      throw new Error('Modified suggestion is required when feedback type is "modify"');
    }

    if (feedbackData.feedbackComment && feedbackData.feedbackComment.length > 1000) {
      throw new Error('Feedback comment must be less than 1000 characters');
    }

    if (feedbackData.modifiedSuggestion && feedbackData.modifiedSuggestion.length > 5000) {
      throw new Error('Modified suggestion must be less than 5000 characters');
    }
  }

  /**
   * Get feedback type options
   * @returns {Array} List of feedback type options
   */
  getFeedbackTypes() {
    return [
      { value: 'accept', label: 'Accept', description: 'This suggestion is helpful' },
      { value: 'reject', label: 'Reject', description: 'This suggestion is not helpful' },
      { value: 'modify', label: 'Modify', description: 'I have a better suggestion' }
    ];
  }

  /**
   * Get experience level options
   * @returns {Array} List of experience level options
   */
  getExperienceLevels() {
    return [
      { value: 'beginner', label: 'Beginner' },
      { value: 'intermediate', label: 'Intermediate' },
      { value: 'expert', label: 'Expert' }
    ];
  }

  /**
   * Get code review context options
   * @returns {Array} List of code review context options
   */
  getReviewContexts() {
    return [
      { value: 'personal', label: 'Personal Project' },
      { value: 'team', label: 'Team Review' },
      { value: 'production', label: 'Production Code' }
    ];
  }
}

// Export singleton instance
const feedbackService = new FeedbackService();
export default feedbackService;