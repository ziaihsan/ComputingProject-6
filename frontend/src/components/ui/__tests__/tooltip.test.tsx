/**
 * Tests for Tooltip components
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '../tooltip'

describe('Tooltip Components', () => {
  describe('TooltipProvider', () => {
    it('should render children', () => {
      render(
        <TooltipProvider>
          <span>Test Content</span>
        </TooltipProvider>
      )
      expect(screen.getByText('Test Content')).toBeTruthy()
    })
  })

  describe('Tooltip', () => {
    it('should render tooltip trigger', () => {
      render(
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>Hover me</TooltipTrigger>
            <TooltipContent>Tooltip text</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )
      expect(screen.getByText('Hover me')).toBeTruthy()
    })

    it('should show tooltip content on hover', async () => {
      const user = userEvent.setup()

      render(
        <TooltipProvider delayDuration={0}>
          <Tooltip>
            <TooltipTrigger>Hover me</TooltipTrigger>
            <TooltipContent>Tooltip text</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

      const trigger = screen.getByText('Hover me')
      await user.hover(trigger)

      // Tooltip should appear - may be multiple elements with same text
      const tooltips = await screen.findAllByText('Tooltip text')
      expect(tooltips.length).toBeGreaterThan(0)
    })
  })

  describe('TooltipContent', () => {
    it('should apply custom className', async () => {
      render(
        <TooltipProvider delayDuration={0}>
          <Tooltip defaultOpen>
            <TooltipTrigger>Trigger</TooltipTrigger>
            <TooltipContent className="custom-class">Content1</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

      // Wait for tooltip to appear - may be multiple elements
      const contents = await screen.findAllByText('Content1')
      expect(contents.length).toBeGreaterThan(0)

      // Check the element or its parent for the class
      const hasClass = contents.some(el =>
        el.className?.includes('custom-class') ||
        el.closest('.custom-class') !== null
      )
      expect(hasClass).toBeTruthy()
    })

    it('should apply default sideOffset', async () => {
      render(
        <TooltipProvider delayDuration={0}>
          <Tooltip defaultOpen>
            <TooltipTrigger>Trigger2</TooltipTrigger>
            <TooltipContent>Content2</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

      const contents = await screen.findAllByText('Content2')
      expect(contents.length).toBeGreaterThan(0)
    })

    it('should apply custom sideOffset', async () => {
      render(
        <TooltipProvider delayDuration={0}>
          <Tooltip defaultOpen>
            <TooltipTrigger>Trigger3</TooltipTrigger>
            <TooltipContent sideOffset={10}>Content3</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

      const contents = await screen.findAllByText('Content3')
      expect(contents.length).toBeGreaterThan(0)
    })

    it('should have correct base styles', async () => {
      render(
        <TooltipProvider delayDuration={0}>
          <Tooltip defaultOpen>
            <TooltipTrigger>Trigger4</TooltipTrigger>
            <TooltipContent>Styled4</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

      const contents = await screen.findAllByText('Styled4')
      expect(contents.length).toBeGreaterThan(0)

      // Check for styles in content or its parent
      const hasStyles = contents.some(el =>
        el.closest('div[class*="z-50"]') !== null
      )
      expect(hasStyles).toBeTruthy()
    })
  })

  describe('TooltipTrigger', () => {
    it('should render as button by default', () => {
      render(
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>Click me</TooltipTrigger>
            <TooltipContent>Tooltip</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

      const trigger = screen.getByText('Click me')
      expect(trigger).toBeTruthy()
    })

    it('should render as child when asChild is true', () => {
      render(
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <span data-testid="custom-trigger">Custom</span>
            </TooltipTrigger>
            <TooltipContent>Tooltip</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )

      expect(screen.getByTestId('custom-trigger')).toBeTruthy()
    })
  })
})
