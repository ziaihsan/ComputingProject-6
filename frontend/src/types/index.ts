export interface CoinSignal {
  symbol: string
  full_name: string
  price: number
  price_change_24h: number
  rsi: number
  rsi_smoothed: number
  ema_13: number
  ema_21: number
  market_cap_rank: number
  market_cap?: number
  long_layer: number
  short_layer: number
}

export interface HeatmapResponse {
  success: boolean
  timeframe: string
  updated_at?: string
  total_coins: number
  signals: CoinSignal[]
  error?: string
}

export type Direction = 'long' | 'short'
export type Timeframe = '15m' | '1h' | '4h' | '12h' | '1d' | '1w'
export type CoinLimit = string

// Chat types
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface MarketSummary {
  total_coins: number
  overbought_count: number
  oversold_count: number
  strong_long_signals: number
  strong_short_signals: number
}

export interface ChatRequest {
  message: string
  timeframe: string
  conversation_history: Array<{ role: string; content: string }>
}

export interface ChatResponse {
  success: boolean
  response: string
  market_summary: MarketSummary | null
  error: string | null
}

// API Key types
export interface ApiKeyStatus {
  configured: boolean
  masked_key: string | null
  service_ready: boolean
}

export interface ApiKeyResponse {
  success: boolean
  message?: string
  error?: string
  warning?: string
}

// Model types
export interface ModelInfo {
  name: string
  description: string
  tier: 'preview' | 'stable'
}

export interface ModelsResponse {
  models: Record<string, ModelInfo>
  current_model: string
}

export interface ModelChangeResponse {
  success: boolean
  message?: string
  error?: string
  current_model?: string
}
