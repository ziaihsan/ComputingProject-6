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
export type Timeframe = '15m' | '1h' | '4h' | '1d'
export type CoinLimit = '50' | '100' | '150' | '200'
