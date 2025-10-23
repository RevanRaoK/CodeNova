import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import { AuthProvider } from '../../contexts/AuthContext';
import { NotificationProvider } from '../../contexts/NotificationContext';
import NotificationManager from '../../components/NotificationManager';
import { CodeReview } from '../../pages/CodeReview';
import { FeedbackDashboard } from '../../pages/FeedbackDashboard';
import FeedbackHistory from '../../components/FeedbackHistory';
import httpClient from '../../services/httpClient';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange }) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange && onChange(e.target.value)}
    />
  )
}));

// Test wrapper component
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <NotificationProvider>
      <AuthProvider>
        {children}
        <NotificationManager />
      </AuthProvider>
    </NotificationProvider>
  </BrowserRouter>
);

describe('AI Feedback and Learning E2E Workflow', () => {
  let mockAxios;
  let user;

  beforeEach(() => {
    mockAxios = new MockAdapter(httpClient);
    user = userEvent.setup();
    localStorage.clear();
    
    // Setup authenticated user
    localStorage.setItem('access_token', 'test-token');
    localStorage.setItem('user_data', JSON.stringify({
      id: 1,
      email: 'test@example.com'
    }));
    
    vi.clearAllMocks();
  });

  afterEach(() => {
    mockAxios.restore();
    localStorage.clear();
  });

  describe('AI Suggestion Quality Workflow', () => {
    it('displays distinct problem descriptions and solutions', async () => {
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-123',
        status: 'completed',
        issues: [
          {
            line: 10,
            severity: 'error',
            message: 'Variable "userName" is declared but never used',
            suggestion: 'Remove the unused variable declaration or use it in your code. If you need it later, consider commenting it out instead of deleting it.'
          },
          {
            line: 15,
            severity: 'warning',
            message: 'Function "calculateTotal" has high cyclomatic complexity (12)',
            suggestion: 'Break down this function into smaller, more focused functions. For example, extract validation logic into a separate validateInputs() function and calculation logic into computeSum() and applyDiscounts() functions.'
          }
        ]
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      // Enter code
      const editor = screen.getByTestId('monaco-editor');
      await user.type(editor, 'const userName = "test";\nfunction calculateTotal() { /* complex logic */ }');

      // Analyze
      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      await user.click(analyzeButton);

      // Wait for results
      await waitFor(() => {
        expect(screen.getByText(/analysis complete/i)).toBeInTheDocument();
      });

      // Verify distinct problem descriptions
      expect(screen.getByText(/variable "userName" is declared but never used/i)).toBeInTheDocument();
      expect(screen.getByText(/function "calculateTotal" has high cyclomatic complexity/i)).toBeInTheDocument();

      // Verify actionable solutions
      expect(screen.getByText(/remove the unused variable declaration/i)).toBeInTheDocument();
      expect(screen.getByText(/break down this function into smaller/i)).toBeInTheDocument();

      // Verify suggestions include specific implementation guidance
      expect(screen.getByText(/extract validation logic into a separate validateInputs/i)).toBeInTheDocument();
    });

    it('provides contextual code examples in suggestions', async () => {
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-456',
        issues: [
          {
            line: 5,
            severity: 'warning',
            message: 'Using var instead of const or let',
            suggestion: 'Replace var with const for values that don\'t change, or let for values that do. Example:\n\nBefore: var count = 0;\nAfter: let count = 0; // if value changes\n      const MAX = 100; // if value is constant',
            code_example: 'let count = 0;\nconst MAX = 100;'
          }
        ]
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const editor = screen.getByTestId('monaco-editor');
      await user.type(editor, 'var count = 0;');

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/using var instead of const or let/i)).toBeInTheDocument();
      });

      // Verify code example is shown
      expect(screen.getByText(/let count = 0/i)).toBeInTheDocument();
      expect(screen.getByText(/const MAX = 100/i)).toBeInTheDocument();
    });

    it('ensures unique suggestions for multiple issues', async () => {
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-789',
        issues: [
          {
            line: 5,
            message: 'Missing error handling',
            suggestion: 'Add try-catch block around this async operation'
          },
          {
            line: 10,
            message: 'Missing input validation',
            suggestion: 'Validate user input before processing'
          },
          {
            line: 15,
            message: 'Missing null check',
            suggestion: 'Add null/undefined check before accessing properties'
          }
        ]
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const editor = screen.getByTestId('monaco-editor');
      await user.type(editor, 'async function process(data) { return data.value; }');

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/missing error handling/i)).toBeInTheDocument();
      });

      // Verify all suggestions are unique and contextual
      expect(screen.getByText(/add try-catch block/i)).toBeInTheDocument();
      expect(screen.getByText(/validate user input/i)).toBeInTheDocument();
      expect(screen.getByText(/add null\/undefined check/i)).toBeInTheDocument();

      // Verify no generic or repeated suggestions
      const suggestions = screen.getAllByText(/suggestion/i);
      const suggestionTexts = suggestions.map(s => s.textContent);
      const uniqueSuggestions = new Set(suggestionTexts);
      expect(uniqueSuggestions.size).toBe(suggestionTexts.length);
    });
  });

  describe('Feedback Collection Workflow', () => {
    it('collects user feedback on AI suggestions', async () => {
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-feedback',
        issues: [
          {
            id: 'issue-1',
            line: 5,
            severity: 'warning',
            message: 'Consider using async/await',
            suggestion: 'Replace promise chains with async/await for better readability'
          }
        ]
      });

      mockAxios.onPost('/api/v1/feedback/submit').reply(200, {
        id: 'feedback-1',
        action: 'accept',
        issue_id: 'issue-1'
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const editor = screen.getByTestId('monaco-editor');
      await user.type(editor, 'promise.then().catch();');

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/consider using async\/await/i)).toBeInTheDocument();
      });

      // Accept suggestion
      const acceptButton = screen.getByRole('button', { name: /accept/i });
      await user.click(acceptButton);

      // Verify feedback submission
      await waitFor(() => {
        expect(mockAxios.history.post.some(req => 
          req.url.includes('feedback/submit')
        )).toBe(true);
      });

      // Verify feedback data
      const feedbackRequest = mockAxios.history.post.find(req => 
        req.url.includes('feedback/submit')
      );
      const feedbackData = JSON.parse(feedbackRequest.data);
      expect(feedbackData.action).toBe('accept');
      expect(feedbackData.issue_id).toBe('issue-1');
    });

    it('allows rejecting suggestions with reason', async () => {
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-reject',
        issues: [
          {
            id: 'issue-2',
            message: 'Use arrow function',
            suggestion: 'Convert to arrow function syntax'
          }
        ]
      });

      mockAxios.onPost('/api/v1/feedback/submit').reply(200, {
        id: 'feedback-2',
        action: 'reject'
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const editor = screen.getByTestId('monaco-editor');
      await user.type(editor, 'function test() {}');

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/use arrow function/i)).toBeInTheDocument();
      });

      // Reject suggestion
      const rejectButton = screen.getByRole('button', { name: /reject/i });
      await user.click(rejectButton);

      // Optionally provide reason
      const reasonInput = screen.queryByPlaceholderText(/reason for rejection/i);
      if (reasonInput) {
        await user.type(reasonInput, 'Need traditional function for hoisting');
      }

      // Submit rejection
      const submitButton = screen.getByRole('button', { name: /submit/i });
      await user.click(submitButton);

      // Verify rejection was submitted
      await waitFor(() => {
        expect(mockAxios.history.post.some(req => 
          req.url.includes('feedback/submit') && 
          JSON.parse(req.data).action === 'reject'
        )).toBe(true);
      });
    });

    it('allows modifying suggestions before accepting', async () => {
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-modify',
        issues: [
          {
            id: 'issue-3',
            message: 'Add error handling',
            suggestion: 'Wrap in try-catch block'
          }
        ]
      });

      mockAxios.onPost('/api/v1/feedback/submit').reply(200, {
        id: 'feedback-3',
        action: 'modify'
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const editor = screen.getByTestId('monaco-editor');
      await user.type(editor, 'await fetchData();');

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/add error handling/i)).toBeInTheDocument();
      });

      // Modify suggestion
      const modifyButton = screen.getByRole('button', { name: /modify/i });
      await user.click(modifyButton);

      // Edit suggestion
      const suggestionEditor = screen.getByLabelText(/edit suggestion/i);
      await user.clear(suggestionEditor);
      await user.type(suggestionEditor, 'Use try-catch with specific error types');

      // Submit modified suggestion
      const submitButton = screen.getByRole('button', { name: /submit/i });
      await user.click(submitButton);

      // Verify modification was submitted
      await waitFor(() => {
        const feedbackRequest = mockAxios.history.post.find(req => 
          req.url.includes('feedback/submit')
        );
        const feedbackData = JSON.parse(feedbackRequest.data);
        expect(feedbackData.action).toBe('modify');
        expect(feedbackData.modified_suggestion).toContain('specific error types');
      });
    });
  });

  describe('Personalized AI Learning Workflow', () => {
    it('uses feedback patterns to personalize future suggestions', async () => {
      // Mock user feedback patterns
      mockAxios.onGet('/api/v1/feedback/patterns/1').reply(200, {
        patterns: {
          accepted_categories: ['error-handling', 'async-await'],
          rejected_categories: ['arrow-functions', 'destructuring'],
          preferences: {
            'error-handling': { acceptance_rate: 0.95, count: 20 },
            'arrow-functions': { acceptance_rate: 0.15, count: 10 }
          }
        }
      });

      // Mock personalized analysis
      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-personalized',
        personalized: true,
        issues: [
          {
            line: 5,
            category: 'error-handling',
            message: 'Missing error handling',
            suggestion: 'Based on your preferences, add comprehensive try-catch with specific error types',
            confidence: 0.95
          }
        ]
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const editor = screen.getByTestId('monaco-editor');
      await user.type(editor, 'await fetchData();');

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      await user.click(analyzeButton);

      // Verify personalized suggestion
      await waitFor(() => {
        expect(screen.getByText(/based on your preferences/i)).toBeInTheDocument();
      });

      // Verify high-confidence suggestions are highlighted
      const suggestion = screen.getByText(/comprehensive try-catch/i);
      expect(suggestion).toBeInTheDocument();
    });

    it('reduces emphasis on consistently rejected patterns', async () => {
      mockAxios.onGet('/api/v1/feedback/patterns/1').reply(200, {
        patterns: {
          rejected_categories: ['arrow-functions'],
          preferences: {
            'arrow-functions': { acceptance_rate: 0.1, count: 30 }
          }
        }
      });

      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-filtered',
        issues: [
          {
            line: 5,
            category: 'performance',
            message: 'Inefficient loop',
            suggestion: 'Use map() instead of forEach()'
          }
          // Note: No arrow function suggestions due to user's rejection pattern
        ]
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const editor = screen.getByTestId('monaco-editor');
      await user.type(editor, 'function test() { arr.forEach(x => {}); }');

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/inefficient loop/i)).toBeInTheDocument();
      });

      // Verify arrow function suggestions are not present
      expect(screen.queryByText(/convert to arrow function/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/use arrow syntax/i)).not.toBeInTheDocument();
    });

    it('prioritizes consistently accepted suggestion patterns', async () => {
      mockAxios.onGet('/api/v1/feedback/patterns/1').reply(200, {
        patterns: {
          accepted_categories: ['security', 'validation'],
          preferences: {
            'security': { acceptance_rate: 0.98, count: 50 },
            'validation': { acceptance_rate: 0.92, count: 40 }
          }
        }
      });

      mockAxios.onPost('/api/v1/analysis/analyze-code').reply(200, {
        id: 'analysis-prioritized',
        issues: [
          {
            line: 3,
            category: 'security',
            severity: 'high',
            message: 'Potential SQL injection',
            suggestion: 'Use parameterized queries',
            priority: 'high'
          },
          {
            line: 8,
            category: 'validation',
            severity: 'medium',
            message: 'Missing input validation',
            suggestion: 'Validate and sanitize user input',
            priority: 'high'
          },
          {
            line: 12,
            category: 'style',
            severity: 'low',
            message: 'Inconsistent spacing',
            suggestion: 'Use consistent spacing',
            priority: 'low'
          }
        ]
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const editor = screen.getByTestId('monaco-editor');
      await user.type(editor, 'const query = "SELECT * FROM users WHERE id=" + userId;');

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/potential sql injection/i)).toBeInTheDocument();
      });

      // Verify high-priority (accepted pattern) suggestions are shown first
      const issues = screen.getAllByRole('listitem');
      expect(issues[0]).toHaveTextContent(/sql injection/i);
      expect(issues[1]).toHaveTextContent(/input validation/i);
    });

    it('includes relevant feedback examples in AI context', async () => {
      mockAxios.onGet('/api/v1/feedback/patterns/1').reply(200, {
        patterns: {
          top_examples: [
            {
              issue_type: 'error-handling',
              original_suggestion: 'Add try-catch',
              user_feedback: 'accepted',
              context: 'async operations'
            },
            {
              issue_type: 'naming',
              original_suggestion: 'Use camelCase',
              user_feedback: 'rejected',
              reason: 'Using snake_case for API responses'
            }
          ]
        }
      });

      mockAxios.onPost('/api/v1/analysis/analyze-code').reply((config) => {
        const requestData = JSON.parse(config.data);
        
        // Verify feedback context is included
        expect(requestData.user_context).toBeDefined();
        expect(requestData.user_context.feedback_patterns).toBeDefined();
        
        return [200, {
          id: 'analysis-context',
          issues: [
            {
              message: 'Consider error handling',
              suggestion: 'Add try-catch for async operations (you previously accepted similar suggestions)'
            }
          ]
        }];
      });

      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const editor = screen.getByTestId('monaco-editor');
      await user.type(editor, 'await api.call();');

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/you previously accepted similar suggestions/i)).toBeInTheDocument();
      });
    });
  });

  describe('Feedback Dashboard Workflow', () => {
    it('displays feedback statistics and trends', async () => {
      mockAxios.onGet(/\/api\/v1\/feedback\/statistics/).reply(200, {
        total_feedback: 150,
        accepted: 120,
        rejected: 20,
        modified: 10,
        acceptance_rate: 80,
        trends: [
          { date: '2024-01-01', accepted: 10, rejected: 2 },
          { date: '2024-01-02', accepted: 12, rejected: 1 },
          { date: '2024-01-03', accepted: 15, rejected: 3 }
        ]
      });

      render(
        <TestWrapper>
          <FeedbackDashboard />
        </TestWrapper>
      );

      // Wait for dashboard to load
      await waitFor(() => {
        expect(screen.getByText(/feedback statistics/i)).toBeInTheDocument();
      });

      // Verify statistics
      expect(screen.getByText('150')).toBeInTheDocument(); // Total feedback
      expect(screen.getByText('120')).toBeInTheDocument(); // Accepted
      expect(screen.getByText(/80%/)).toBeInTheDocument(); // Acceptance rate

      // Verify "Active Users" is NOT shown (admin-only)
      expect(screen.queryByText(/active users/i)).not.toBeInTheDocument();

      // Verify trends chart
      expect(screen.getByText(/feedback trends/i)).toBeInTheDocument();
    });

    it('displays model performance metrics', async () => {
      mockAxios.onGet(/\/api\/v1\/feedback\/statistics/).reply(200, {
        model_performance: {
          accuracy: 0.85,
          precision: 0.82,
          recall: 0.88,
          f1_score: 0.85
        }
      });

      render(
        <TestWrapper>
          <FeedbackDashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/model performance/i)).toBeInTheDocument();
      });

      // Verify metrics
      expect(screen.getByText(/85%/)).toBeInTheDocument(); // Accuracy
      expect(screen.getByText(/82%/)).toBeInTheDocument(); // Precision
      expect(screen.getByText(/88%/)).toBeInTheDocument(); // Recall
    });

    it('shows feedback history with filtering', async () => {
      mockAxios.onGet('/api/v1/feedback/history/1').reply(200, {
        feedback: [
          {
            id: 'fb-1',
            date: '2024-01-15',
            action: 'accept',
            issue_type: 'error-handling',
            suggestion: 'Add try-catch'
          },
          {
            id: 'fb-2',
            date: '2024-01-14',
            action: 'reject',
            issue_type: 'arrow-functions',
            suggestion: 'Use arrow syntax'
          },
          {
            id: 'fb-3',
            date: '2024-01-13',
            action: 'modify',
            issue_type: 'validation',
            suggestion: 'Validate input'
          }
        ]
      });

      render(
        <TestWrapper>
          <FeedbackHistory userId={1} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/add try-catch/i)).toBeInTheDocument();
      });

      // Filter by action
      const filterSelect = screen.getByLabelText(/filter by action/i);
      await user.selectOptions(filterSelect, 'accept');

      // Verify only accepted feedback is shown
      await waitFor(() => {
        expect(screen.getByText(/add try-catch/i)).toBeInTheDocument();
        expect(screen.queryByText(/use arrow syntax/i)).not.toBeInTheDocument();
      });
    });
  });
});
