import { vi } from 'vitest'
import feedbackService from '../feedbackService'
import httpClient from '../httpClient'

// Mock the httpClient
vi.mock('../httpClient', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('FeedbackService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('submitFeedback', () => {
    it('submits feedback successfully', async () => {
      const mockResponse = {
        data: {
          id: 1,
          issue_id: 'issue-123',
          user_id: 1,
          feedback_type: 'accept',
          feedback_value: 1,
          created_at: '2023-01-01T00:00:00Z'
        }
      }
      
      httpClient.post.mockResolvedValue(mockResponse)

      const feedbackData = {
        issueId: 'issue-123',
        feedbackType: 'accept',
        feedbackComment: 'Good suggestion'
      }

      const result = await feedbackService.submitFeedback(feedbackData)

      expect(httpClient.post).toHaveBeenCalledWith('/feedback', {
        issue_id: 'issue-123',
        feedback_type: 'accept',
        feedback_comment: 'Good suggestion',
        modified_suggestion: null,
        user_experience_level: null,
        code_review_context: null,
        context_data: {}
      })

      expect(result).toEqual({
        id: 1,
        issueId: 'issue-123',
        userId: 1,
        feedbackType: 'accept',
        feedbackValue: 1,
        feedbackComment: undefined,
        modifiedSuggestion: undefined,
        userExperienceLevel: undefined,
        codeReviewContext: undefined,
        contextData: {},
        createdAt: '2023-01-01T00:00:00Z',
        updatedAt: undefined
      })
    })

    it('handles submission errors', async () => {
      const error = new Error('Network error')
      error.response = {
        status: 400,
        data: { detail: 'Invalid feedback data' }
      }
      
      httpClient.post.mockRejectedValue(error)

      const feedbackData = {
        issueId: 'issue-123',
        feedbackType: 'accept'
      }

      await expect(feedbackService.submitFeedback(feedbackData))
        .rejects.toThrow('Invalid feedback data')
    })
  })

  describe('getFeedbackStats', () => {
    it('fetches feedback statistics', async () => {
      const mockResponse = {
        data: {
          total_feedback: 100,
          accepted: 70,
          rejected: 20,
          modified: 10
        }
      }
      
      httpClient.get.mockResolvedValue(mockResponse)

      const result = await feedbackService.getFeedbackStats({ timeRange: 'week' })

      expect(httpClient.get).toHaveBeenCalledWith('/feedback/stats?time_range=week')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('validateFeedbackData', () => {
    it('validates required fields', () => {
      expect(() => feedbackService.validateFeedbackData({}))
        .toThrow('Issue ID is required')

      expect(() => feedbackService.validateFeedbackData({ issueId: 'test' }))
        .toThrow('Feedback type is required')
    })

    it('validates feedback type', () => {
      expect(() => feedbackService.validateFeedbackData({
        issueId: 'test',
        feedbackType: 'invalid'
      })).toThrow('Invalid feedback type')
    })

    it('validates modify feedback requires suggestion', () => {
      expect(() => feedbackService.validateFeedbackData({
        issueId: 'test',
        feedbackType: 'modify'
      })).toThrow('Modified suggestion is required')
    })

    it('validates comment length', () => {
      expect(() => feedbackService.validateFeedbackData({
        issueId: 'test',
        feedbackType: 'accept',
        feedbackComment: 'x'.repeat(1001)
      })).toThrow('Feedback comment must be less than 1000 characters')
    })
  })
})