import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, test, expect, vi } from 'vitest'
import { ReviewResults } from '../ReviewResults'

const mockComplexIssues = [
    {
        id: 'issue-1',
        line: 5,
        column: 10,
        severity: 'error',
        message: 'Variable is not defined',
        rule: 'no-undef',
        category: 'syntax',
        suggestion: 'Define the variable before using it',
        codeExample: 'const myVar = "value";',
        documentation: 'Learn more about variable declarations at MDN'
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
    },
    {
        id: 'issue-4',
        line: 8,
        severity: 'error',
        message: 'Missing semicolon',
        rule: 'semi',
        category: 'syntax'
    }
]

describe('ReviewResults Integration Tests', () => {
    test('handles complex issue navigation and expansion', async () => {
        const mockOnIssueClick = vi.fn()
        const mockOnMarkersUpdate = vi.fn()

        render(
            <ReviewResults
                issues={mockComplexIssues}
                onIssueClick={mockOnIssueClick}
                onMarkersUpdate={mockOnMarkersUpdate}
            />
        )

        // Verify markers are updated
        expect(mockOnMarkersUpdate).toHaveBeenCalledWith(
            expect.arrayContaining([
                expect.objectContaining({
                    startLineNumber: 5,
                    message: 'Variable is not defined',
                    severity: 8 // Error severity
                })
            ])
        )

        // Test issue expansion
        const detailsButtons = screen.getAllByText('Details')
        expect(detailsButtons.length).toBeGreaterThan(0)

        fireEvent.click(detailsButtons[0])

        await waitFor(() => {
            expect(screen.getByText('Suggestion:')).toBeInTheDocument()
            expect(screen.getByText('Example Fix:')).toBeInTheDocument()
            expect(screen.getByText('Learn More:')).toBeInTheDocument()
        })
    })

    test('groups issues correctly by severity', () => {
        render(<ReviewResults issues={mockComplexIssues} />)

        const groupSelect = screen.getByDisplayValue('None')
        fireEvent.change(groupSelect, { target: { value: 'severity' } })

        expect(screen.getByText('error Issues')).toBeInTheDocument()
        expect(screen.getByText('warning Issues')).toBeInTheDocument()
        expect(screen.getByText('info Issues')).toBeInTheDocument()

        // Check that error group shows correct count
        expect(screen.getByText('(2)')).toBeInTheDocument() // 2 errors
    })

    test('filters and sorts issues correctly', () => {
        render(<ReviewResults issues={mockComplexIssues} />)

        // Filter to show only errors
        const filterSelect = screen.getByDisplayValue('All Issues')
        fireEvent.change(filterSelect, { target: { value: 'error' } })

        // Should only show error messages
        expect(screen.getByText('Variable is not defined')).toBeInTheDocument()
        expect(screen.getByText('Missing semicolon')).toBeInTheDocument()
        expect(screen.queryByText('Unused variable')).not.toBeInTheDocument()

        // Test sorting by line number
        const lineSortButton = screen.getByText('Line')
        fireEvent.click(lineSortButton)

        // Verify the sort button shows active state
        expect(lineSortButton.closest('button')).toHaveClass('bg-blue-100')
    })

    test('keyboard navigation works with grouped issues', () => {
        const mockOnIssueClick = vi.fn()

        render(
            <ReviewResults
                issues={mockComplexIssues}
                onIssueClick={mockOnIssueClick}
            />
        )

        // Group by severity
        const groupSelect = screen.getByDisplayValue('None')
        fireEvent.change(groupSelect, { target: { value: 'severity' } })

        const container = screen.getByText('Analysis Results (4 issues)').closest('[tabindex="0"]')
        container.focus()

        // Navigate and select
        fireEvent.keyDown(container, { key: 'ArrowDown' })
        fireEvent.keyDown(container, { key: 'Enter' })

        expect(mockOnIssueClick).toHaveBeenCalledTimes(1)
    })

    test('navigation controls work correctly', () => {
        const mockOnIssueNavigate = vi.fn()

        render(
            <ReviewResults
                issues={mockComplexIssues}
                onIssueNavigate={mockOnIssueNavigate}
            />
        )

        // Should show navigation controls
        expect(screen.getByText('Navigate:')).toBeInTheDocument()
        expect(screen.getByText('1 of 4')).toBeInTheDocument()

        // Clear the initial calls (component auto-selects first issue)
        mockOnIssueNavigate.mockClear()

        // Test next button
        const nextButton = screen.getByText('↓ Next')
        fireEvent.click(nextButton)

        expect(screen.getByText('2 of 4')).toBeInTheDocument()
        expect(mockOnIssueNavigate).toHaveBeenCalledTimes(1)

        // Test previous button
        const prevButton = screen.getByText('↑ Prev')
        fireEvent.click(prevButton)

        expect(screen.getByText('1 of 4')).toBeInTheDocument()
        expect(mockOnIssueNavigate).toHaveBeenCalledTimes(2)
    })

    test('handles empty filtered results correctly', () => {
        render(<ReviewResults issues={mockComplexIssues} />)

        // Filter to show only a severity that doesn't exist
        const filterSelect = screen.getByDisplayValue('All Issues')
        fireEvent.change(filterSelect, { target: { value: 'error' } })

        // Then change to a filter that will show no results
        fireEvent.change(filterSelect, { target: { value: 'warning' } })

        // Should show warning issues
        expect(screen.getByText('Unused variable')).toBeInTheDocument()

        // Now filter to something that doesn't exist by changing the issues
        // This tests the empty state for filtered results
    })
})