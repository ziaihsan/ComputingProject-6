import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={cn("markdown-content", className)}>
      <ReactMarkdown
        components={{
        h1: ({ children }) => (
          <h1 className="text-xl font-bold text-white mt-4 mb-2">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-lg font-bold text-purple-400 mt-4 mb-2">{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-base font-semibold text-white mt-3 mb-1">{children}</h3>
        ),
        h4: ({ children }) => (
          <h4 className="text-sm font-semibold text-slate-200 mt-2 mb-1">{children}</h4>
        ),
        p: ({ children }) => (
          <p className="text-slate-300 mb-2 leading-relaxed">{children}</p>
        ),
        strong: ({ children }) => (
          <strong className="font-semibold text-white">{children}</strong>
        ),
        em: ({ children }) => (
          <em className="italic text-slate-200">{children}</em>
        ),
        ul: ({ children }) => (
          <ul className="list-disc list-outside ml-5 mb-3 space-y-1">{children}</ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-outside ml-5 mb-3 space-y-1">{children}</ol>
        ),
        li: ({ children }) => (
          <li className="text-slate-300">{children}</li>
        ),
        code: ({ children, className }) => {
          // Check if it's inline code or code block
          const isInline = !className
          if (isInline) {
            return (
              <code className="bg-slate-700 px-1.5 py-0.5 rounded text-sm text-emerald-400">
                {children}
              </code>
            )
          }
          return (
            <code className="block bg-slate-800 p-3 rounded-lg text-sm text-emerald-400 overflow-x-auto my-2">
              {children}
            </code>
          )
        },
        pre: ({ children }) => (
          <pre className="bg-slate-800 rounded-lg overflow-x-auto my-2">{children}</pre>
        ),
        blockquote: ({ children }) => (
          <blockquote className="border-l-2 border-purple-500 pl-3 my-2 italic text-slate-400">
            {children}
          </blockquote>
        ),
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 underline"
          >
            {children}
          </a>
        ),
        hr: () => <hr className="border-slate-700 my-4" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
