/**
 * Global test setup for Vitest
 *
 * This file runs before all tests and configures:
 * - jest-dom matchers for DOM assertions
 * - MSW (Mock Service Worker) for API mocking
 * - Browser API polyfills for jsdom
 */
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, afterAll, vi } from 'vitest'
import { server } from './mocks/server'

// ============================================================================
// MSW Server Setup
// ============================================================================

// Start MSW server before all tests
beforeAll(() => {
  server.listen({
    onUnhandledRequest: 'warn', // Warn about unhandled requests
  })
})

// Reset handlers after each test (remove any runtime handlers)
afterEach(() => {
  cleanup() // Clean up React Testing Library
  server.resetHandlers()
})

// Clean up after all tests complete
afterAll(() => {
  server.close()
})

// ============================================================================
// Browser API Polyfills
// ============================================================================

// Mock matchMedia for components that use media queries (e.g., Framer Motion)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // Deprecated
    removeListener: vi.fn(), // Deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver for components that observe size changes
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver for lazy loading components
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  root: null,
  rootMargin: '',
  thresholds: [],
}))

// Mock scrollTo for components that programmatically scroll
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: vi.fn(),
})

// Mock requestAnimationFrame for animation-related code
global.requestAnimationFrame = vi.fn((callback) => {
  return setTimeout(callback, 0) as unknown as number
})

global.cancelAnimationFrame = vi.fn((id) => {
  clearTimeout(id)
})

// ============================================================================
// Console Suppression (Optional)
// ============================================================================

// Suppress specific console warnings during tests if needed
// Uncomment if you want to suppress React warnings about act()
// const originalError = console.error
// beforeAll(() => {
//   console.error = (...args: unknown[]) => {
//     if (
//       typeof args[0] === 'string' &&
//       args[0].includes('Warning: ReactDOM.render is no longer supported')
//     ) {
//       return
//     }
//     originalError.call(console, ...args)
//   }
// })
// afterAll(() => {
//   console.error = originalError
// })
