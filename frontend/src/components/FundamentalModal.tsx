import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Loader2, AlertCircle, TrendingUp, RefreshCw } from 'lucide-react'
import { Button } from './ui/button'
import { MarkdownRenderer } from './MarkdownRenderer'

const API_BASE = ''

interface FundamentalModalProps {
  isOpen: boolean
  onClose: () => void
  symbol: string
  timeframe: string
}

export function FundamentalModal({ isOpen, onClose, symbol, timeframe }: FundamentalModalProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [analysis, setAnalysis] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && symbol) {
      fetchAnalysis()
    }
  }, [isOpen, symbol])

  const fetchAnalysis = async () => {
    setIsLoading(true)
    setError(null)
    setAnalysis('')

    try {
      const response = await fetch(`${API_BASE}/api/fundamental`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, timeframe })
      })

      const data = await response.json()

      if (data.success) {
        setAnalysis(data.response)
      } else {
        setError(data.response || data.error || 'Failed to fetch analysis')
      }
    } catch {
      setError('Unable to connect to server. Make sure the backend is running.')
    } finally {
      setIsLoading(false)
    }
  }

  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4"
          onClick={onClose}
        >
          {/* Modal Content */}
          <motion.div
            initial={{ scale: 0.95 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0.95 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="w-full max-w-2xl bg-[#161b22] border border-slate-700 rounded-xl shadow-2xl max-h-[85vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700 bg-[#161b22]">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                  <TrendingUp className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="font-semibold text-white text-lg">{symbol}</h2>
                  <p className="text-xs text-slate-400">Fundamental Analysis</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={fetchAnalysis}
                  disabled={isLoading}
                  className="h-8 w-8 p-0 text-slate-400 hover:text-white hover:bg-slate-800"
                >
                  <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
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

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-5">
              {isLoading ? (
                <div className="flex flex-col items-center justify-center py-16">
                  <Loader2 className="h-10 w-10 text-purple-500 animate-spin mb-4" />
                  <p className="text-slate-400">Analyzing {symbol}...</p>
                  <p className="text-xs text-slate-500 mt-1">This may take a few seconds</p>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="h-12 w-12 rounded-full bg-red-900/30 flex items-center justify-center mb-4">
                    <AlertCircle className="h-6 w-6 text-red-400" />
                  </div>
                  <p className="text-red-400 text-center mb-4">{error}</p>
                  <Button
                    onClick={fetchAnalysis}
                    className="bg-slate-700 hover:bg-slate-600 text-white"
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Try Again
                  </Button>
                </div>
              ) : analysis ? (
                <MarkdownRenderer content={analysis} />
              ) : null}
            </div>

            {/* Footer */}
            <div className="px-5 py-3 border-t border-slate-700 bg-[#161b22]">
              <p className="text-xs text-slate-500 text-center">
                Powered by Gemini AI | Timeframe: {timeframe} | Not financial advice
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  )
}
