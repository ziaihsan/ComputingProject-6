import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, Loader2, MessageCircle, Sparkles, AlertCircle, Settings, Key } from 'lucide-react'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'
import { ApiKeySettings } from './ApiKeySettings'
import { MarkdownRenderer } from './MarkdownRenderer'
import type { ChatMessage, ChatResponse, Timeframe } from '@/types'

const API_BASE = 'http://localhost:8000'

interface ChatPanelProps {
  isOpen: boolean
  onClose: () => void
  timeframe: Timeframe
}

const QUICK_PROMPTS = [
  "What's the strongest buy signal right now?",
  "Which coins are oversold?",
  "Market condition summary",
  "What does Layer 5 signal mean?",
]

export function ChatPanel({ isOpen, onClose, timeframe }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setError(null)

    try {
      const conversationHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content,
      }))

      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText.trim(),
          timeframe,
          conversation_history: conversationHistory,
        }),
      })

      const data: ChatResponse = await response.json()

      if (data.success) {
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, assistantMessage])
      } else {
        setError(data.error || 'Failed to get response')
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response || 'Sorry, an error occurred. Please try again.',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (err) {
      setError('Unable to connect to server')
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, unable to connect to server. Make sure backend is running.',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessage(input)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40"
              onClick={onClose}
            />

          {/* Chat Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-[#161b22] border-l border-slate-800 z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-[#0d1117]">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="font-semibold text-white">AI Trading Assistant</h2>
                  <p className="text-xs text-slate-400">Powered by Gemini</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowSettings(true)}
                  className="h-8 w-8 p-0 text-slate-400 hover:text-white hover:bg-slate-800"
                  title="API Key Settings"
                >
                  <Settings className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="h-8 w-8 p-0 text-slate-400 hover:text-white hover:bg-slate-800"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center px-4">
                  <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center mb-4">
                    <MessageCircle className="h-8 w-8 text-purple-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    Hello! I'm AI Assistant
                  </h3>
                  <p className="text-sm text-slate-400 mb-4">
                    Ask about crypto market conditions, trading signals, or technical analysis.
                  </p>

                  {/* Setup API Key Button */}
                  <button
                    onClick={() => setShowSettings(true)}
                    className="flex items-center justify-center gap-2 w-full px-4 py-2.5 mb-4 bg-amber-900/30 hover:bg-amber-900/50 border border-amber-700/50 rounded-lg text-amber-400 text-sm transition-colors"
                  >
                    <Key className="h-4 w-4" />
                    Configure Gemini API Key
                  </button>

                  {/* Quick Prompts */}
                  <div className="w-full space-y-2">
                    <p className="text-xs text-slate-500 mb-2">Try asking:</p>
                    {QUICK_PROMPTS.map((prompt, idx) => (
                      <button
                        key={idx}
                        onClick={() => sendMessage(prompt)}
                        className="w-full text-left px-4 py-2.5 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-300 transition-colors"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((message) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={cn(
                        "flex",
                        message.role === 'user' ? "justify-end" : "justify-start"
                      )}
                    >
                      <div
                        className={cn(
                          "max-w-[85%] rounded-2xl px-4 py-3",
                          message.role === 'user'
                            ? "bg-purple-600 text-white rounded-br-md"
                            : "bg-slate-800 text-slate-200 rounded-bl-md"
                        )}
                      >
                        {message.role === 'assistant' ? (
                          <MarkdownRenderer content={message.content} className="text-sm" />
                        ) : (
                          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        )}
                        <p className={cn(
                          "text-[10px] mt-1",
                          message.role === 'user' ? "text-purple-200" : "text-slate-500"
                        )}>
                          {message.timestamp.toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                      </div>
                    </motion.div>
                  ))}

                  {/* Loading indicator */}
                  {isLoading && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex justify-start"
                    >
                      <div className="bg-slate-800 rounded-2xl rounded-bl-md px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Loader2 className="h-4 w-4 text-purple-400 animate-spin" />
                          <span className="text-sm text-slate-400">Analyzing...</span>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Error Banner */}
            {error && (
              <div className="px-4 py-2 bg-red-900/20 border-t border-red-800/50">
                <div className="flex items-center gap-2 text-red-400 text-xs">
                  <AlertCircle className="h-4 w-4" />
                  <span>{error}</span>
                </div>
              </div>
            )}

            {/* Input Area */}
            <form onSubmit={handleSubmit} className="p-4 border-t border-slate-800 bg-[#0d1117]">
              <div className="flex items-end gap-2">
                <div className="flex-1 bg-slate-800 rounded-xl border border-slate-700 focus-within:border-purple-500 transition-colors">
                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about crypto market..."
                    rows={1}
                    className="w-full bg-transparent text-white text-sm px-4 py-3 resize-none outline-none placeholder:text-slate-500"
                    style={{ minHeight: '44px', maxHeight: '120px' }}
                  />
                </div>
                <Button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className={cn(
                    "h-11 w-11 p-0 rounded-xl transition-all",
                    input.trim() && !isLoading
                      ? "bg-purple-600 hover:bg-purple-700"
                      : "bg-slate-800 text-slate-500"
                  )}
                >
                  {isLoading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </Button>
              </div>
              <p className="text-[10px] text-slate-500 mt-2 text-center">
                Timeframe: {timeframe} | Not financial advice
              </p>
            </form>
          </motion.div>

        </>
        )}
      </AnimatePresence>

      {/* API Key Settings Modal - outside AnimatePresence to fix positioning */}
      <ApiKeySettings
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
    </>
  )
}
