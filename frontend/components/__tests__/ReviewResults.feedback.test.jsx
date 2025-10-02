import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { ReviewResults } from '../ReviewResults'
import feedbackService from '../../services/feedbackService'

// Mock the feedback service
vi.mock('../../services/feedbackService', () => ({
  default: {
    submitFeedback: vi.fn(),
    validateFeedbackData: vi.fn()
  }
}))

// Mock the feedback components
vi.mock('../FeedbackButton', () => ({
  FeedbackButton: ({ issueId, onFeedback, existingFeedback }) => (
    <div data-testid={`feedback-button-${issueId}`}>
      <button 
        onClick={() => onFeedback({ issueId, feedbackType: 'accept' })}
        data-testid={`accept-${issueId}`}
      >
        Accept
      </button>
      <button 
        onClick={() => onFeedback({ issueId, feedbackType: 'reject' })}
        data-testid={`reject-${issueId}`}
      >
        Reject
      </button>
      {existingFeedback && (
        <span data-testid={`existing-feedback-${issueId}`}>
          {existingFeedback.type}
        </span>
      )}
    </div>
  )
}))

vi.mock('../FeedbackModal', () => ({
  FeedbackModal: ({ isOpen, onClose, onSubmit, issue }) => (
    isOpen ? (
      <div data-testid="feedback-modal">
        <h3>Feedback for {issue?.id}</h3>
        <button 
          onClick={() => onSubmit({ 
            issueId: issue.id, 
            feedbackType: 'modify',
            modifiedSuggestion: 'Better suggestion'
          })}
          data-testid="submit-modal-feedback"
        >
          Submit
        </button>
        <button onClick={onClose} data-testid="close-modal">Close</button>
      </div>
    ) : null
  )
}))

describe('ReviewResults Feedback Integration', () => { 
 const mockIssues = [
    {
      id: 'issue-123',
      line: 10,
      column: 5,
      severity: 'warning',
      message: 'Consider using const instead of let',
      rule: 'prefer-const',
      suggestion: 'Use const for variables that are not reassigned',
      category: 'best-practices'
    },
    {
      id: 'issue-456', 
      line: 25,
      severity: 'error',
      message: 'Undefined variable',
      rule: 'no-undef',
      category: 'errors'
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    feedbackService.submitFeedback.mockResolvedValue({ success: true })
  })

  it('displays issue IDs when feedback is enabled', () => {
    render(
      <ReviewResults 
        issues={mockIssues} 
        enableFeedback={true}
      />
    )

    expect(screen.getByText('issue-123'.substring(0, 8) + '...')).toBeInTheDocument()
    expect(screen.getByText('issue-456'.substring(0, 8) + '...')).toBeInTheDocument()
  })

  it('does not display issue IDs when feedback is disabled', () => {
    render(
      <ReviewResults 
        issues={mockIssues} 
        enableFeedback={false}
      />
    )

    expect(screen.queryByText('issue-123'.substring(0, 8) + '...')).not.toBeInTheDocument()
  })

  it('renders feedback buttons for each issue', () => {
    render(
      <ReviewResults 
        issues={mockIssues} 
        enableFeedback={true}
      />
    )

    expect(screen.getByTestId('feedback-button-issue-123')).toBeInTheDocument()
    expect(screen.getByTestId('feedback-button-issue-456')).toBeInTheDocument()
  })

  it('handles quick feedback submission', async () => {
    const onFeedbackSubmitted = vi.fn()
    
    render(
      <ReviewResults 
        issues={mockIssues} 
        enableFeedback={true}
        onFeedbackSubmitted={onFeedbackSubmitted}
      />
    )

    const acceptButton = screen.getByTestId('accept-issue-123')
    fireEvent.click(acceptButton)

    await waitFor(() => {
      expect(feedbackService.submitFeedback).toHaveBeenCalledWith({
        issueId: 'issue-123',
        feedbackType: 'accept'
      })
      expect(onFeedbackSubmitted).toHaveBeenCalledWith({
        issueId: 'issue-123',
        feedbackType: 'accept'
      })
    })
  })
})