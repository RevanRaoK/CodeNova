import { render, screen, fireEvent } from '@testing-library/react'
import { describe, test, expect, vi } from 'vitest'
import { ReviewResults } from '../ReviewResults'

const mockIssues = [
  {
    id: 'issue-1',
    line: 5,
    column: 10,
    severity: 'error',
    message: 'Variable is not defined',
    rule: 'no-undef',
    category: 'syntax',
    suggestion: 'Define the variable before using it',
    codeExample: 'const myVar = "value";'
  },
  {
    id: 'issue-2',
    line: 12,
    column: 5,
    severity: 'warning',
    message: 'Unused variable',
    rule: 'no-unused-vars',
    category: 'best-practices',
    suggestion: 'Remove unused variable or use it in the code'
  },
  {
    id: 'issue-3',
    line: 20,
    severity: 'info',
    message: 'Consider using const instead of let',
    rule: 'prefer-const',
    category: 'style'
  }
]

const mockAnalysisMetrics = {
  linesOfCode: 50,
  complexity: 3,
  maintainabilityIndex: 85
}

describe('ReviewResults Component', () => {
  test('renders issues with correct structure', () => {
    render(
      <ReviewResults 
        issues={mockIssues} 
        analysisMetrics={mockAnalysisMetrics}
      />
    )
    
    expect(screen.getByText('Analysis Results (3 issues)')).toBeInTheDocument()
    expect(screen.getByText('1 error')).toBeInTheDocument()
    expect(screen.getByText('1 warning')).toBeInTheDocument()
    expect(screen.getByText('1 info')).toBeInTheDocument()
  })

  test('filters issues by severity', () => {
    render(<ReviewResults issues={mockIssues} />)
    
    const filterSelect = screen.getByDisplayValue('All Issues')
    fireEvent.change(filterSelect, { target: { value: 'error' } })
    
    expect(screen.getByText('Variable is not defined')).toBeInTheDocument()
    expect(screen.queryByText('Unused variable')).not.toBeInTheDocument()
  })

  test('groups issues by severity', () => {
    render(<ReviewResults issues={mockIssues} />)
    
    const groupSelect = screen.getByDisplayValue('None')
    fireEvent.change(groupSelect, { target: { value: 'severity' } })
    
    expect(screen.getByText('error Issues')).toBeInTheDocument()
    expect(screen.getByText('warning Issues')).toBeInTheDocument()
    expect(screen.getByText('info Issues')).toBeInTheDocument()
  })

  test('expands issue details when clicked', () => {
    render(<ReviewResults issues={mockIssues} />)
    
    const detailsButton = screen.getAllByText('Details')[0]
    fireEvent.click(detailsButton)
    
    expect(screen.getByText('Suggestion:')).toBeInTheDocument()
    expect(screen.getByText('Define the variable before using it')).toBeInTheDocument()
  })

  test('handles keyboard navigation', () => {
    const mockOnIssueClick = vi.fn()
    render(
      <ReviewResults 
        issues={mockIssues} 
        onIssueClick={mockOnIssueClick}
      />
    )
    
    // Find the focusable container by looking for the element with tabIndex
    const container = screen.getByText('Analysis Results (3 issues)').closest('[tabindex="0"]')
    expect(container).toBeInTheDocument()
    
    container.focus()
    
    // The component auto-selects the first issue, so pressing Enter should trigger the first issue
    fireEvent.keyDown(container, { key: 'Enter' })
    
    // Check that the function was called with any of the mock issues (since sorting might change order)
    expect(mockOnIssueClick).toHaveBeenCalledTimes(1)
    const calledWith = mockOnIssueClick.mock.calls[0][0]
    expect(mockIssues.some(issue => issue.id === calledWith.id)).toBe(true)
  })

  test('shows empty state when no issues', () => {
    render(<ReviewResults issues={[]} />)
    
    expect(screen.getByText('Great job!')).toBeInTheDocument()
    expect(screen.getByText('No issues found in your code.')).toBeInTheDocument()
  })

  test('displays analysis metrics', () => {
    render(
      <ReviewResults 
        issues={mockIssues} 
        analysisMetrics={mockAnalysisMetrics}
      />
    )
    
    expect(screen.getByText('Lines:')).toBeInTheDocument()
    expect(screen.getByText('50')).toBeInTheDocument()
    expect(screen.getByText('Complexity:')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('Maintainability:')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
  })
})