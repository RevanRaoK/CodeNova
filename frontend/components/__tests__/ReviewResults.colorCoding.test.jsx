import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReviewResults } from '../ReviewResults'

describe('ReviewResults Color Coding', () => {
  const mockIssues = [
    {
      id: '1',
      line: 10,
      column: 5,
      severity: 'critical',
      message: 'Critical security vulnerability',
      category: 'security'
    },
    {
      id: '2',
      line: 20,
      column: 10,
      severity: 'high',
      message: 'High priority issue',
      category: 'performance'
    },
    {
      id: '3',
      line: 30,
      column: 15,
      severity: 'warning',
      message: 'Warning level issue',
      category: 'style'
    },
    {
      id: '4',
      line: 40,
      column: 20,
      severity: 'low',
      message: 'Low priority issue',
      category: 'naming'
    },
    {
      id: '5',
      line: 50,
      column: 25,
      severity: 'info',
      message: 'Informational message',
      category: 'documentation'
    },
    {
      id: '6',
      line: 60,
      column: 30,
      severity: 'suggestion',
      message: 'Helpful suggestion',
      category: 'suggestion'
    }
  ]

  it('should render issues with different severity levels', () => {
    render(<ReviewResults issues={mockIssues} enableFeedback={false} />)
    
    expect(screen.getByText('Critical security vulnerability')).toBeInTheDocument()
    expect(screen.getByText('High priority issue')).toBeInTheDocument()
    expect(screen.getByText('Warning level issue')).toBeInTheDocument()
    expect(screen.getByText('Low priority issue')).toBeInTheDocument()
    expect(screen.getByText('Informational message')).toBeInTheDocument()
    expect(screen.getByText('Helpful suggestion')).toBeInTheDocument()
  })

  it('should apply red background for critical severity', () => {
    render(<ReviewResults issues={[mockIssues[0]]} enableFeedback={false} />)
    
    const issueElement = screen.getByText('Critical security vulnerability').closest('div[class*="bg-red-100"]')
    expect(issueElement).toBeInTheDocument()
    expect(issueElement).toHaveClass('bg-red-100', 'border-red-300', 'text-red-900')
  })

  it('should apply orange background for high severity', () => {
    render(<ReviewResults issues={[mockIssues[1]]} enableFeedback={false} />)
    
    const issueElement = screen.getByText('High priority issue').closest('div[class*="bg-orange-100"]')
    expect(issueElement).toBeInTheDocument()
    expect(issueElement).toHaveClass('bg-orange-100', 'border-orange-300', 'text-orange-900')
  })

  it('should apply yellow background for warning severity', () => {
    render(<ReviewResults issues={[mockIssues[2]]} enableFeedback={false} />)
    
    const issueElement = screen.getByText('Warning level issue').closest('div[class*="bg-yellow-100"]')
    expect(issueElement).toBeInTheDocument()
    expect(issueElement).toHaveClass('bg-yellow-100', 'border-yellow-300', 'text-yellow-900')
  })

  it('should apply blue background for low severity', () => {
    render(<ReviewResults issues={[mockIssues[3]]} enableFeedback={false} />)
    
    const issueElement = screen.getByText('Low priority issue').closest('div[class*="bg-blue-100"]')
    expect(issueElement).toBeInTheDocument()
    expect(issueElement).toHaveClass('bg-blue-100', 'border-blue-300', 'text-blue-900')
  })

  it('should apply gray background for info severity', () => {
    render(<ReviewResults issues={[mockIssues[4]]} enableFeedback={false} />)
    
    const issueElement = screen.getByText('Informational message').closest('div[class*="bg-gray-100"]')
    expect(issueElement).toBeInTheDocument()
    expect(issueElement).toHaveClass('bg-gray-100', 'border-gray-300', 'text-gray-900')
  })

  it('should apply green background for suggestion severity', () => {
    render(<ReviewResults issues={[mockIssues[5]]} enableFeedback={false} />)
    
    const issueElement = screen.getByText('Helpful suggestion').closest('div[class*="bg-green-100"]')
    expect(issueElement).toBeInTheDocument()
    expect(issueElement).toHaveClass('bg-green-100', 'border-green-300', 'text-green-900')
  })

  it('should display all severity levels with distinct colors', () => {
    const { container } = render(<ReviewResults issues={mockIssues} enableFeedback={false} />)
    
    // Check that different color classes are present
    expect(container.querySelector('.bg-red-100')).toBeInTheDocument()
    expect(container.querySelector('.bg-orange-100')).toBeInTheDocument()
    expect(container.querySelector('.bg-yellow-100')).toBeInTheDocument()
    expect(container.querySelector('.bg-blue-100')).toBeInTheDocument()
    expect(container.querySelector('.bg-gray-100')).toBeInTheDocument()
    expect(container.querySelector('.bg-green-100')).toBeInTheDocument()
  })

  it('should handle legacy "error" severity with red color', () => {
    const errorIssue = {
      id: '7',
      line: 70,
      severity: 'error',
      message: 'Legacy error message'
    }
    
    render(<ReviewResults issues={[errorIssue]} enableFeedback={false} />)
    
    const issueElement = screen.getByText('Legacy error message').closest('div[class*="bg-red-100"]')
    expect(issueElement).toBeInTheDocument()
  })

  it('should apply green color to suggestion sections in expanded details', async () => {
    const issueWithSuggestion = {
      id: '8',
      line: 80,
      severity: 'warning',
      message: 'Issue with suggestion',
      suggestion: 'This is a helpful suggestion'
    }
    
    const { container } = render(<ReviewResults issues={[issueWithSuggestion]} enableFeedback={false} />)
    
    // Expand the issue to show suggestion
    const detailsButton = screen.getByText('Details')
    const { act } = await import('@testing-library/react')
    await act(async () => {
      detailsButton.click()
    })
    
    // Check that suggestion section has green background
    const suggestionSection = await screen.findByText('This is a helpful suggestion')
    const greenSection = suggestionSection.closest('div[class*="bg-green-50"]')
    expect(greenSection).toBeInTheDocument()
    expect(greenSection).toHaveClass('bg-green-50', 'border-green-200')
  })

  it('should handle case-insensitive severity values', () => {
    const mixedCaseIssues = [
      { id: '9', line: 90, severity: 'CRITICAL', message: 'Uppercase critical' },
      { id: '10', line: 100, severity: 'High', message: 'Mixed case high' },
      { id: '11', line: 110, severity: 'WaRnInG', message: 'Random case warning' }
    ]
    
    const { container } = render(<ReviewResults issues={mixedCaseIssues} enableFeedback={false} />)
    
    expect(container.querySelector('.bg-red-100')).toBeInTheDocument()
    expect(container.querySelector('.bg-orange-100')).toBeInTheDocument()
    expect(container.querySelector('.bg-yellow-100')).toBeInTheDocument()
  })

  it('should default to gray for unknown severity levels', () => {
    const unknownSeverityIssue = {
      id: '12',
      line: 120,
      severity: 'unknown',
      message: 'Unknown severity level'
    }
    
    render(<ReviewResults issues={[unknownSeverityIssue]} enableFeedback={false} />)
    
    const issueElement = screen.getByText('Unknown severity level').closest('div[class*="bg-gray-100"]')
    expect(issueElement).toBeInTheDocument()
  })
})
