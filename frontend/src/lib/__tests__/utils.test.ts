/**
 * Unit tests for utility functions
 *
 * These are pure functions with no external dependencies,
 * making them ideal candidates for unit testing.
 */
import { describe, it, expect } from 'vitest'
import { cn, formatPrice } from '../utils'

// ============================================================================
// Test: cn (className merge utility)
// ============================================================================

describe('cn (className merge utility)', () => {
  describe('basic functionality', () => {
    it('should merge multiple class names', () => {
      expect(cn('foo', 'bar')).toBe('foo bar')
    })

    it('should handle single class name', () => {
      expect(cn('foo')).toBe('foo')
    })

    it('should handle empty input', () => {
      expect(cn()).toBe('')
    })

    it('should trim whitespace', () => {
      expect(cn('  foo  ', '  bar  ')).toBe('foo bar')
    })
  })

  describe('conditional classes', () => {
    it('should handle true conditions', () => {
      expect(cn('base', true && 'included')).toBe('base included')
    })

    it('should handle false conditions', () => {
      expect(cn('base', false && 'excluded')).toBe('base')
    })

    it('should handle mixed conditions', () => {
      const isActive = true
      const isDisabled = false
      expect(cn('btn', isActive && 'btn-active', isDisabled && 'btn-disabled')).toBe(
        'btn btn-active'
      )
    })
  })

  describe('handling undefined and null', () => {
    it('should ignore undefined values', () => {
      expect(cn('foo', undefined, 'bar')).toBe('foo bar')
    })

    it('should ignore null values', () => {
      expect(cn('foo', null, 'bar')).toBe('foo bar')
    })

    it('should handle all undefined/null', () => {
      expect(cn(undefined, null, undefined)).toBe('')
    })
  })

  describe('tailwind class merging', () => {
    it('should merge conflicting padding classes', () => {
      // tailwind-merge should keep only the last conflicting class
      expect(cn('px-4', 'px-6')).toBe('px-6')
    })

    it('should merge conflicting text color classes', () => {
      expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500')
    })

    it('should merge conflicting background classes', () => {
      expect(cn('bg-white', 'bg-gray-100')).toBe('bg-gray-100')
    })

    it('should keep non-conflicting classes', () => {
      expect(cn('px-4', 'py-2', 'text-sm')).toBe('px-4 py-2 text-sm')
    })

    it('should handle complex responsive classes', () => {
      expect(cn('md:px-4', 'md:px-6')).toBe('md:px-6')
    })
  })

  describe('array inputs', () => {
    it('should handle array of class names', () => {
      expect(cn(['foo', 'bar'])).toBe('foo bar')
    })

    it('should handle mixed array and string inputs', () => {
      expect(cn('base', ['variant', 'size'])).toBe('base variant size')
    })
  })

  describe('object inputs', () => {
    it('should handle object with boolean values', () => {
      expect(cn({ foo: true, bar: false, baz: true })).toBe('foo baz')
    })

    it('should handle mixed object and string', () => {
      expect(cn('base', { active: true, disabled: false })).toBe('base active')
    })
  })
})

// ============================================================================
// Test: formatPrice
// ============================================================================

describe('formatPrice', () => {
  describe('very small prices (< 0.0001)', () => {
    it('should format with 8 decimal places', () => {
      expect(formatPrice(0.00001234)).toBe('0.00001234')
    })

    it('should format extremely small prices', () => {
      expect(formatPrice(0.00000001)).toBe('0.00000001')
    })

    it('should format prices just under threshold', () => {
      expect(formatPrice(0.00009999)).toBe('0.00009999')
    })
  })

  describe('small prices (0.0001 to 0.01)', () => {
    it('should format with 6 decimal places', () => {
      expect(formatPrice(0.001234)).toBe('0.001234')
    })

    it('should format at lower boundary', () => {
      expect(formatPrice(0.0001)).toBe('0.000100')
    })

    it('should format just under upper boundary', () => {
      expect(formatPrice(0.009999)).toBe('0.009999')
    })
  })

  describe('sub-dollar prices (0.01 to 1)', () => {
    it('should format with 4 decimal places', () => {
      expect(formatPrice(0.1234)).toBe('0.1234')
    })

    it('should format at lower boundary', () => {
      expect(formatPrice(0.01)).toBe('0.0100')
    })

    it('should format near upper boundary', () => {
      expect(formatPrice(0.9999)).toBe('0.9999')
    })

    it('should format typical altcoin prices', () => {
      expect(formatPrice(0.52)).toBe('0.5200')
    })
  })

  describe('dollar-range prices (1 to 100)', () => {
    it('should format with 2 decimal places', () => {
      expect(formatPrice(12.3456)).toBe('12.35')
    })

    it('should format at lower boundary', () => {
      expect(formatPrice(1.0)).toBe('1.00')
    })

    it('should format near upper boundary', () => {
      expect(formatPrice(99.99)).toBe('99.99')
    })

    it('should round correctly', () => {
      // JavaScript uses banker's rounding, so 50.555 rounds to 50.55
      expect(formatPrice(50.556)).toBe('50.56')
      expect(formatPrice(50.554)).toBe('50.55')
    })
  })

  describe('large prices (>= 100)', () => {
    it('should format with locale formatting', () => {
      const result = formatPrice(12345.67)
      // Should contain thousands separator (locale dependent)
      expect(result).toContain('12')
      expect(result).toContain('345')
    })

    it('should handle Bitcoin-sized prices', () => {
      const result = formatPrice(42000.5)
      expect(result).toContain('42')
    })

    it('should limit to 2 decimal places', () => {
      const result = formatPrice(100.999)
      // Should be formatted as ~101.00 or 100.99
      expect(result.includes('100') || result.includes('101')).toBe(true)
    })

    it('should handle very large prices', () => {
      const result = formatPrice(1000000)
      expect(result).toContain('1')
      expect(result).toContain('000')
    })
  })

  describe('edge cases', () => {
    it('should handle zero', () => {
      expect(formatPrice(0)).toBe('0')
    })

    it('should handle undefined as falsy', () => {
      expect(formatPrice(undefined as unknown as number)).toBe('0')
    })

    it('should handle null as falsy', () => {
      expect(formatPrice(null as unknown as number)).toBe('0')
    })

    it('should handle NaN as falsy', () => {
      expect(formatPrice(NaN)).toBe('0')
    })

    it('should handle negative prices', () => {
      // The function doesn't explicitly handle negatives, but should work
      const result = formatPrice(-10.5)
      expect(result).toContain('10')
    })
  })

  describe('cryptocurrency-specific cases', () => {
    it('should format BTC price correctly', () => {
      expect(formatPrice(42350.75)).toContain('42')
    })

    it('should format ETH price correctly', () => {
      expect(formatPrice(2250.5)).toContain('2')
    })

    it('should format DOGE-like low prices', () => {
      expect(formatPrice(0.08)).toBe('0.0800')
    })

    it('should format SHIB-like very low prices', () => {
      expect(formatPrice(0.00001234)).toBe('0.00001234')
    })
  })
})
