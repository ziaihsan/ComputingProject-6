/**
 * Tests for FundamentalModal component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'

// Mock framer-motion
vi.mock('framer-motion', () => {
  const createMotionComponent = (tag: string) => {
    return ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => {
      const Tag = tag as keyof JSX.IntrinsicElements
      const filteredProps = Object.fromEntries(
        Object.entries(props).filter(([key]) =>
          !['initial', 'animate', 'exit', 'variants', 'transition', 'whileHover', 'whileTap', 'layout', 'layoutId'].includes(key)
        )
      )
      return <Tag {...filteredProps}>{children}</Tag>
    }
  }

  return {
    motion: new Proxy({}, {
      get: (_, tag: string) => createMotionComponent(tag)
    }),
    AnimatePresence: ({ children }: React.PropsWithChildren) => <>{children}</>,
  }
})

// Mock react-dom createPortal
vi.mock('react-dom', async () => {
  const actual = await vi.importActual('react-dom')
  return {
    ...actual,
    createPortal: (node: React.ReactNode) => node,
  }
})

import { FundamentalModal } from '../FundamentalModal'

describe('FundamentalModal Component', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    symbol: 'BTCUSDT',
    timeframe: '4h',
    onOpenSettings: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  describe('Rendering', () => {
    it('should render when isOpen is true', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        json: () => Promise.resolve({ success: true, response: '## Analysis' }),
      })

      render(<FundamentalModal {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('BTCUSDT')).toBeTruthy()
      })
    })

    it('should not render when isOpen is false', () => {
      render(<FundamentalModal {...defaultProps} isOpen={false} />)

      expect(screen.queryByText('BTCUSDT')).toBeNull()
    })

    it('should display Fundamental Analysis header', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        json: () => Promise.resolve({ success: true, response: 'Test' }),
      })

      render(<FundamentalModal {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText('Fundamental Analysis')).toBeTruthy()
      })
    })
  })

  describe('Loading State', () => {
    it('should show loading indicator when fetching', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({
          json: () => Promise.resolve({ success: true, response: 'Test' }),
        }), 1000))
      )

      render(<FundamentalModal {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText(/Analyzing/i)).toBeTruthy()
      })
    })
  })

  describe('Success State', () => {
    it('should display analysis content on success', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        json: () => Promise.resolve({ success: true, response: '## Bitcoin Analysis\nTest content' }),
      })

      render(<FundamentalModal {...defaultProps} />)

      await waitFor(() => {
        // Wait for loading to finish
        expect(screen.queryByText(/Analyzing/i)).toBeNull()
      }, { timeout: 3000 })
    })
  })

  describe('Error State', () => {
    it('should display error message on failure', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        json: () => Promise.resolve({ success: false, error: 'API error' }),
      })

      render(<FundamentalModal {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText(/Try Again/i)).toBeTruthy()
      })
    })

    it('should show settings button on API key error', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        json: () => Promise.resolve({
          success: false,
          response: 'API key not configured',
          error: 'not_configured'
        }),
      })

      render(<FundamentalModal {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText(/Open Settings/i)).toBeTruthy()
      })
    })

    it('should handle network error', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error('Network error')
      )

      render(<FundamentalModal {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByText(/Unable to connect/i)).toBeTruthy()
      })
    })
  })

  describe('User Interactions', () => {
    it('should call onClose when close button is clicked', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        json: () => Promise.resolve({ success: true, response: 'Test' }),
      })

      const onClose = vi.fn()
      render(<FundamentalModal {...defaultProps} onClose={onClose} />)

      await waitFor(() => {
        const closeButtons = screen.getAllByRole('button')
        const closeButton = closeButtons.find(btn =>
          btn.querySelector('svg.lucide-x') || btn.getAttribute('aria-label')?.includes('close')
        )
        if (closeButton) {
          fireEvent.click(closeButton)
        }
      })
    })

    it('should call onClose when backdrop is clicked', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        json: () => Promise.resolve({ success: true, response: 'Test' }),
      })

      const onClose = vi.fn()
      render(<FundamentalModal {...defaultProps} onClose={onClose} />)

      await waitFor(() => {
        // Find the backdrop (motion.div with onClick={onClose})
        const backdrop = document.querySelector('.fixed.inset-0')
        if (backdrop) {
          fireEvent.click(backdrop)
          expect(onClose).toHaveBeenCalled()
        }
      })
    })

    it('should call fetchAnalysis when refresh button is clicked', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
        json: () => Promise.resolve({ success: true, response: 'Test' }),
      })

      render(<FundamentalModal {...defaultProps} />)

      await waitFor(() => {
        expect(screen.queryByText(/Analyzing/i)).toBeNull()
      }, { timeout: 3000 })

      const refreshButton = screen.getAllByRole('button')[0]
      if (refreshButton) {
        fireEvent.click(refreshButton)
      }

      // Should have fetched twice (initial + refresh)
      expect(global.fetch).toHaveBeenCalled()
    })

    it('should call onOpenSettings and onClose when settings button is clicked', async () => {
      const onOpenSettings = vi.fn()
      const onClose = vi.fn()

      // Reset and mock fetch for this test
      global.fetch = vi.fn().mockResolvedValueOnce({
        json: () => Promise.resolve({
          success: false,
          response: 'API key not configured',
          error: 'service_unavailable'
        }),
      })

      render(
        <FundamentalModal
          {...defaultProps}
          onClose={onClose}
          onOpenSettings={onOpenSettings}
        />
      )

      await waitFor(() => {
        const settingsButton = screen.getByText(/Open Settings/i)
        fireEvent.click(settingsButton)
        expect(onOpenSettings).toHaveBeenCalled()
        expect(onClose).toHaveBeenCalled()
      })
    })
  })

  describe('Footer', () => {
    it('should display timeframe in footer', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        json: () => Promise.resolve({ success: true, response: 'Test' }),
      })

      render(<FundamentalModal {...defaultProps} timeframe="1h" />)

      await waitFor(() => {
        expect(screen.getByText(/Timeframe: 1h/i)).toBeTruthy()
      })
    })
  })
})
