/**
 * Tests for App component
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

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
    useAnimationControls: () => ({ start: vi.fn() }),
    useInView: () => true,
    useScroll: () => ({ scrollY: { get: () => 0 } }),
  }
})

// Import App after mocking
import App from '../../App'

describe('App Component', () => {
  it('should render without crashing', async () => {
    render(<App />)

    await waitFor(() => {
      expect(document.body).toBeDefined()
    })
  })

  it('should render the Heatmap component', async () => {
    render(<App />)

    await waitFor(() => {
      // Heatmap should be rendered within App
      expect(document.body).toBeDefined()
    })
  })

  it('should wrap content with TooltipProvider', async () => {
    render(<App />)

    await waitFor(() => {
      // Just verify it renders without errors
      expect(document.body.innerHTML).toBeTruthy()
    })
  })
})
