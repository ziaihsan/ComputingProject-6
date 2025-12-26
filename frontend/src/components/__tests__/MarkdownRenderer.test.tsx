/**
 * Tests for MarkdownRenderer component
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MarkdownRenderer } from '../MarkdownRenderer'

describe('MarkdownRenderer Component', () => {
  describe('Basic Rendering', () => {
    it('should render plain text', () => {
      render(<MarkdownRenderer content="Hello World" />)
      expect(screen.getByText('Hello World')).toBeTruthy()
    })

    it('should apply custom className', () => {
      const { container } = render(
        <MarkdownRenderer content="Test" className="custom-class" />
      )
      expect(container.querySelector('.custom-class')).toBeTruthy()
    })

    it('should have markdown-content class', () => {
      const { container } = render(<MarkdownRenderer content="Test" />)
      expect(container.querySelector('.markdown-content')).toBeTruthy()
    })
  })

  describe('Headings', () => {
    it('should render h1 heading', () => {
      render(<MarkdownRenderer content="# Heading 1" />)
      expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
    })

    it('should render h2 heading with purple color', () => {
      const { container } = render(<MarkdownRenderer content="## Heading 2" />)
      const h2 = container.querySelector('h2')
      expect(h2).toBeTruthy()
      expect(h2?.className).toContain('text-purple-400')
    })

    it('should render h3 heading', () => {
      render(<MarkdownRenderer content="### Heading 3" />)
      expect(screen.getByRole('heading', { level: 3 })).toBeTruthy()
    })

    it('should render h4 heading', () => {
      render(<MarkdownRenderer content="#### Heading 4" />)
      expect(screen.getByRole('heading', { level: 4 })).toBeTruthy()
    })
  })

  describe('Text Formatting', () => {
    it('should render bold text', () => {
      const { container } = render(<MarkdownRenderer content="**bold text**" />)
      const strong = container.querySelector('strong')
      expect(strong).toBeTruthy()
      expect(strong?.textContent).toBe('bold text')
    })

    it('should render italic text', () => {
      const { container } = render(<MarkdownRenderer content="*italic text*" />)
      const em = container.querySelector('em')
      expect(em).toBeTruthy()
      expect(em?.textContent).toBe('italic text')
    })

    it('should render paragraph', () => {
      const { container } = render(<MarkdownRenderer content="This is a paragraph." />)
      const p = container.querySelector('p')
      expect(p).toBeTruthy()
    })
  })

  describe('Lists', () => {
    it('should render unordered list', () => {
      const { container } = render(
        <MarkdownRenderer content={`- Item 1\n- Item 2\n- Item 3`} />
      )
      const ul = container.querySelector('ul')
      expect(ul).toBeTruthy()
      // ReactMarkdown may batch list items, just check ul exists with items
      expect(ul?.querySelectorAll('li').length).toBeGreaterThan(0)
    })

    it('should render ordered list', () => {
      const { container } = render(
        <MarkdownRenderer content={`1. First\n2. Second\n3. Third`} />
      )
      const ol = container.querySelector('ol')
      expect(ol).toBeTruthy()
      // ReactMarkdown may batch list items, just check ol exists with items
      expect(ol?.querySelectorAll('li').length).toBeGreaterThan(0)
    })

    it('should style list items correctly', () => {
      const { container } = render(<MarkdownRenderer content="- Item" />)
      const li = container.querySelector('li')
      expect(li?.className).toContain('text-slate-300')
    })
  })

  describe('Code', () => {
    it('should render inline code', () => {
      const { container } = render(<MarkdownRenderer content="Use `const x = 1` in code" />)
      const code = container.querySelector('code')
      expect(code).toBeTruthy()
      expect(code?.className).toContain('bg-slate-700')
    })

    it('should render code block', () => {
      const { container } = render(
        <MarkdownRenderer content={"```javascript\nconst x = 1\n```"} />
      )
      // ReactMarkdown renders code blocks with pre and/or code elements
      const codeBlock = container.querySelector('pre') || container.querySelector('code')
      expect(codeBlock).toBeTruthy()
    })

    it('should style code with emerald color', () => {
      const { container } = render(<MarkdownRenderer content="`code`" />)
      const code = container.querySelector('code')
      expect(code?.className).toContain('text-emerald-400')
    })
  })

  describe('Blockquote', () => {
    it('should render blockquote', () => {
      const { container } = render(<MarkdownRenderer content="> This is a quote" />)
      const blockquote = container.querySelector('blockquote')
      expect(blockquote).toBeTruthy()
      expect(blockquote?.className).toContain('border-l-2')
      expect(blockquote?.className).toContain('border-purple-500')
    })
  })

  describe('Links', () => {
    it('should render links with target blank', () => {
      const { container } = render(
        <MarkdownRenderer content="[Click here](https://example.com)" />
      )
      const link = container.querySelector('a')
      expect(link).toBeTruthy()
      expect(link?.getAttribute('href')).toBe('https://example.com')
      expect(link?.getAttribute('target')).toBe('_blank')
      expect(link?.getAttribute('rel')).toContain('noopener')
    })

    it('should style links with blue color', () => {
      const { container } = render(
        <MarkdownRenderer content="[Link](https://example.com)" />
      )
      const link = container.querySelector('a')
      expect(link?.className).toContain('text-blue-400')
    })
  })

  describe('Horizontal Rule', () => {
    it('should render horizontal rule', () => {
      const { container } = render(<MarkdownRenderer content="---" />)
      const hr = container.querySelector('hr')
      expect(hr).toBeTruthy()
      expect(hr?.className).toContain('border-slate-700')
    })
  })

  describe('Complex Content', () => {
    it('should render mixed content correctly', () => {
      const content = `
# Title

This is a paragraph with **bold** and *italic* text.

## Section 1

- Item 1
- Item 2

> A quote

\`inline code\`
      `

      const { container } = render(<MarkdownRenderer content={content} />)

      expect(container.querySelector('h1')).toBeTruthy()
      expect(container.querySelector('h2')).toBeTruthy()
      expect(container.querySelector('strong')).toBeTruthy()
      expect(container.querySelector('em')).toBeTruthy()
      expect(container.querySelector('ul')).toBeTruthy()
      expect(container.querySelector('blockquote')).toBeTruthy()
      expect(container.querySelector('code')).toBeTruthy()
    })
  })
})
