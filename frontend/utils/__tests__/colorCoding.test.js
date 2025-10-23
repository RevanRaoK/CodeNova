/**
 * Tests for color coding utility functions
 */

import {
  getSeverityColorClass,
  getSeverityColorClasses,
  getSeverityIconColor,
  getSeverityBadgeClasses,
  getSeverityAccessibilityLabel,
  getSeverityTooltip,
  isHighPrioritySeverity,
  compareSeverityPriority
} from '../colorCoding'

describe('Color Coding Utilities', () => {
  describe('getSeverityColorClass', () => {
    test('returns correct background class for critical severity', () => {
      expect(getSeverityColorClass('critical', 'background')).toBe('bg-red-100')
    })

    test('returns correct icon class for high severity', () => {
      expect(getSeverityColorClass('high', 'icon')).toBe('text-orange-500')
    })

    test('returns default for unknown severity', () => {
      expect(getSeverityColorClass('unknown', 'background')).toBe('bg-gray-100')
    })
  })

  describe('getSeverityColorClasses', () => {
    test('returns combined classes for critical severity', () => {
      const classes = getSeverityColorClasses('critical')
      expect(classes).toContain('bg-red-100')
      expect(classes).toContain('border-red-300')
      expect(classes).toContain('text-red-900')
    })

    test('returns suggestion classes when isSuggestion is true', () => {
      const classes = getSeverityColorClasses('critical', true)
      expect(classes).toContain('bg-green-100')
      expect(classes).toContain('border-green-300')
      expect(classes).toContain('text-green-900')
    })
  })

  describe('getSeverityAccessibilityLabel', () => {
    test('returns correct label for critical severity', () => {
      expect(getSeverityAccessibilityLabel('critical')).toBe('Critical severity issue')
    })

    test('returns default label for unknown severity', () => {
      expect(getSeverityAccessibilityLabel('unknown')).toBe('Informational issue')
    })
  })

  describe('getSeverityTooltip', () => {
    test('returns correct tooltip for warning severity', () => {
      expect(getSeverityTooltip('warning')).toBe('Warning: Potential issue that may cause problems')
    })
  })

  describe('isHighPrioritySeverity', () => {
    test('returns true for critical severity', () => {
      expect(isHighPrioritySeverity('critical')).toBe(true)
    })

    test('returns false for info severity', () => {
      expect(isHighPrioritySeverity('info')).toBe(false)
    })
  })

  describe('compareSeverityPriority', () => {
    test('sorts critical higher than warning', () => {
      expect(compareSeverityPriority('critical', 'warning')).toBeGreaterThan(0)
    })

    test('sorts warning higher than info', () => {
      expect(compareSeverityPriority('warning', 'info')).toBeGreaterThan(0)
    })

    test('returns 0 for same severity', () => {
      expect(compareSeverityPriority('error', 'error')).toBe(0)
    })
  })
})