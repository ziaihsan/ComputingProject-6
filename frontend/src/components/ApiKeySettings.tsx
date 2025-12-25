import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Key, Loader2, CheckCircle, AlertCircle, ExternalLink, Eye, EyeOff, Trash2, Cpu, Sparkles } from 'lucide-react'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'
import type { ApiKeyStatus, ApiKeyResponse, ModelsResponse, ModelInfo } from '@/types'

const API_BASE = ''

interface ApiKeySettingsProps {
  isOpen: boolean
  onClose: () => void
  onApiKeyChanged?: () => void
}

export function ApiKeySettings({ isOpen, onClose, onApiKeyChanged }: ApiKeySettingsProps) {
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [status, setStatus] = useState<ApiKeyStatus | null>(null)
  const [models, setModels] = useState<ModelsResponse | null>(null)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isSavingModel, setIsSavingModel] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'warning'; text: string } | null>(null)

  useEffect(() => {
    if (isOpen) {
      fetchStatus()
      fetchModels()
    }
  }, [isOpen])

  const fetchStatus = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/settings/apikey`)
      const data: ApiKeyStatus = await response.json()
      setStatus(data)
    } catch (error) {
      console.error('Failed to fetch API key status:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchModels = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/settings/models`)
      const data: ModelsResponse = await response.json()
      setModels(data)
      setSelectedModel(data.current_model)
    } catch (error) {
      console.error('Failed to fetch models:', error)
    }
  }

  const handleSave = async () => {
    if (!apiKey.trim()) {
      setMessage({ type: 'error', text: 'API key cannot be empty' })
      return
    }

    setIsSaving(true)
    setMessage(null)

    try {
      const response = await fetch(`${API_BASE}/api/settings/apikey`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey }),
      })

      const data: ApiKeyResponse = await response.json()

      if (data.success) {
        setMessage({
          type: data.warning ? 'warning' : 'success',
          text: data.message || 'API key saved successfully!'
        })
        setApiKey('')
        fetchStatus()
        onApiKeyChanged?.()
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to save API key' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to connect to server' })
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete the API key?')) return

    setIsSaving(true)
    try {
      const response = await fetch(`${API_BASE}/api/settings/apikey`, {
        method: 'DELETE',
      })

      const data = await response.json()

      if (data.success) {
        setMessage({ type: 'success', text: 'API key deleted successfully' })
        fetchStatus()
        onApiKeyChanged?.()
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to delete API key' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to connect to server' })
    } finally {
      setIsSaving(false)
    }
  }

  const handleModelChange = async (modelId: string) => {
    setIsSavingModel(true)
    setSelectedModel(modelId)

    try {
      const response = await fetch(`${API_BASE}/api/settings/models`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelId }),
      })

      const data = await response.json()

      if (data.success) {
        setMessage({ type: 'success', text: data.message || 'Model changed successfully!' })
        fetchModels()
        onApiKeyChanged?.()
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to change model' })
        // Revert selection
        if (models) {
          setSelectedModel(models.current_model)
        }
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to connect to server' })
      if (models) {
        setSelectedModel(models.current_model)
      }
    } finally {
      setIsSavingModel(false)
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
            className="w-full max-w-md bg-[#161b22] border border-slate-700 rounded-xl shadow-2xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700 sticky top-0 bg-[#161b22] z-10">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
                  <Key className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="font-semibold text-white">AI Settings</h2>
                  <p className="text-xs text-slate-400">API Key & Gemini Model</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-8 w-8 p-0 text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            {/* Content */}
            <div className="p-5 space-y-5">
              {/* Message */}
              {message && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    "rounded-lg p-3 text-sm",
                    message.type === 'success' && "bg-emerald-900/30 text-emerald-400 border border-emerald-800/50",
                    message.type === 'error' && "bg-red-900/30 text-red-400 border border-red-800/50",
                    message.type === 'warning' && "bg-amber-900/30 text-amber-400 border border-amber-800/50"
                  )}
                >
                  {message.text}
                </motion.div>
              )}

              {/* API Key Section */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
                  <Key className="h-4 w-4" />
                  API Key
                </div>

                {/* Status */}
                {isLoading ? (
                  <div className="flex items-center justify-center py-4">
                    <Loader2 className="h-6 w-6 text-slate-400 animate-spin" />
                  </div>
                ) : status?.configured ? (
                  <div className="bg-emerald-900/20 border border-emerald-800/50 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-emerald-400 mb-1">
                      <CheckCircle className="h-4 w-4" />
                      <span className="font-medium text-sm">Configured</span>
                      <span className={cn(
                        "text-[10px] px-1.5 py-0.5 rounded ml-auto",
                        status.source === 'env'
                          ? "bg-blue-900/50 text-blue-400"
                          : "bg-slate-700 text-slate-400"
                      )}>
                        {status.source === 'env' ? 'ENV VAR' : 'FILE'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">
                      Key: <code className="bg-slate-800 px-1.5 py-0.5 rounded">{status.masked_key}</code>
                    </p>
                    {status.source === 'env' && (
                      <p className="text-xs text-blue-400 mt-2">
                        Set via environment variable. To remove, unset GEMINI_API_KEY from your terminal/system.
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="bg-amber-900/20 border border-amber-800/50 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-amber-400 mb-1">
                      <AlertCircle className="h-4 w-4" />
                      <span className="font-medium text-sm">
                        {status?.source === 'disabled' ? 'Disabled' : 'Not Configured'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">
                      {status?.source === 'disabled'
                        ? 'API key was deleted. Enter a new key to re-enable AI chatbot.'
                        : 'Enter Gemini API key to enable AI chatbot.'}
                    </p>
                  </div>
                )}

                {/* Input */}
                <div className="space-y-2">
                  <div className="relative">
                    <input
                      type={showKey ? 'text' : 'password'}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder={status?.configured ? 'Enter new key...' : 'AIzaSy...'}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 pr-10 text-white text-sm placeholder:text-slate-500 focus:outline-none focus:border-purple-500 transition-colors"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKey(!showKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                    >
                      {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>

                  {/* Buttons */}
                  <div className="flex gap-2">
                    <Button
                      onClick={handleSave}
                      disabled={!apiKey.trim() || isSaving}
                      className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 h-9 text-sm"
                    >
                      {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                      Save
                    </Button>
                    {status?.configured && (
                      <Button
                        onClick={handleDelete}
                        disabled={isSaving}
                        variant="ghost"
                        className="text-red-400 hover:text-red-300 hover:bg-red-900/20 h-9"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>

                {/* Get API Key Link */}
                <a
                  href="https://aistudio.google.com/app/apikey"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                >
                  <ExternalLink className="h-3 w-3" />
                  Get free API Key at Google AI Studio
                </a>
              </div>

              {/* Divider */}
              <div className="border-t border-slate-700" />

              {/* Model Selection */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
                  <Cpu className="h-4 w-4" />
                  AI Model
                  {isSavingModel && <Loader2 className="h-3 w-3 animate-spin text-slate-400" />}
                </div>

                {models ? (
                  <div className="space-y-2">
                    {Object.entries(models.models).map(([modelId, info]: [string, ModelInfo]) => (
                      <button
                        key={modelId}
                        onClick={() => handleModelChange(modelId)}
                        disabled={isSavingModel}
                        className={cn(
                          "w-full text-left p-3 rounded-lg border transition-all",
                          selectedModel === modelId
                            ? "bg-purple-900/30 border-purple-500/50"
                            : "bg-slate-800/50 border-slate-700 hover:border-slate-600"
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {info.tier === 'preview' ? (
                              <Sparkles className="h-4 w-4 text-amber-400" />
                            ) : (
                              <CheckCircle className="h-4 w-4 text-emerald-400" />
                            )}
                            <span className="font-medium text-white text-sm">{info.name}</span>
                          </div>
                          <span className={cn(
                            "text-[10px] px-1.5 py-0.5 rounded",
                            info.tier === 'preview'
                              ? "bg-amber-900/50 text-amber-400"
                              : "bg-emerald-900/50 text-emerald-400"
                          )}>
                            {info.tier}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-1 ml-6">{info.description}</p>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-center py-4">
                    <Loader2 className="h-5 w-5 text-slate-400 animate-spin" />
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="text-xs text-slate-500 space-y-1 pt-2 border-t border-slate-800">
                <p>API key and settings are stored locally on the server.</p>
                <p>Gemini free tier: 15 requests/min. Preview models may be unstable.</p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  )
}
