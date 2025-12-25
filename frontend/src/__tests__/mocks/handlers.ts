/**
 * MSW Request Handlers
 *
 * These handlers intercept API requests during tests and return mock data.
 * This allows testing without making real API calls.
 */
import { http, HttpResponse } from 'msw'
import type {
  HeatmapResponse,
  ChatResponse,
  ApiKeyStatus,
  ModelsResponse,
} from '../../types'

// ============================================================================
// Mock Data
// ============================================================================

export const mockHeatmapData: HeatmapResponse = {
  success: true,
  timeframe: '4h',
  updated_at: new Date().toISOString(),
  total_coins: 5,
  signals: [
    {
      symbol: 'BTCUSDT',
      full_name: 'Bitcoin',
      price: 42000,
      price_change_24h: 2.5,
      rsi: 55.3,
      rsi_smoothed: 52.1,
      ema_13: 41500,
      ema_21: 41000,
      market_cap_rank: 1,
      market_cap: 0,
      long_layer: 3,
      short_layer: 0,
    },
    {
      symbol: 'ETHUSDT',
      full_name: 'Ethereum',
      price: 2200,
      price_change_24h: -1.2,
      rsi: 35.8,
      rsi_smoothed: 38.2,
      ema_13: 2180,
      ema_21: 2150,
      market_cap_rank: 2,
      market_cap: 0,
      long_layer: 2,
      short_layer: 0,
    },
    {
      symbol: 'BNBUSDT',
      full_name: 'BNB',
      price: 320,
      price_change_24h: 0.8,
      rsi: 72.5,
      rsi_smoothed: 70.1,
      ema_13: 315,
      ema_21: 310,
      market_cap_rank: 3,
      market_cap: 0,
      long_layer: 0,
      short_layer: 2,
    },
    {
      symbol: 'SOLUSDT',
      full_name: 'Solana',
      price: 95,
      price_change_24h: 5.3,
      rsi: 25.2,
      rsi_smoothed: 28.5,
      ema_13: 92,
      ema_21: 90,
      market_cap_rank: 4,
      market_cap: 0,
      long_layer: 4,
      short_layer: 0,
    },
    {
      symbol: 'XRPUSDT',
      full_name: 'XRP',
      price: 0.52,
      price_change_24h: -0.5,
      rsi: 48.7,
      rsi_smoothed: 50.2,
      ema_13: 0.51,
      ema_21: 0.50,
      market_cap_rank: 5,
      market_cap: 0,
      long_layer: 1,
      short_layer: 0,
    },
  ],
}

export const mockApiKeyStatus: ApiKeyStatus = {
  configured: true,
  masked_key: '****ABCD',
  source: 'file',
  service_ready: true,
}

export const mockApiKeyStatusUnconfigured: ApiKeyStatus = {
  configured: false,
  masked_key: null,
  source: null,
  service_ready: false,
}

export const mockModelsResponse: ModelsResponse = {
  models: {
    'gemini-2.5-flash': {
      name: 'Gemini 2.5 Flash',
      description: 'Fast and efficient for quick tasks',
      tier: 'stable',
    },
    'gemini-3-pro-preview': {
      name: 'Gemini 3 Pro (Preview)',
      description: 'Latest and most powerful',
      tier: 'preview',
    },
  },
  current_model: 'gemini-2.5-flash',
}

// ============================================================================
// Request Handlers
// ============================================================================

export const handlers = [
  // -------------------------------------------------------------------------
  // Heatmap API
  // -------------------------------------------------------------------------
  http.get('/api/heatmap', ({ request }) => {
    const url = new URL(request.url)
    const timeframe = url.searchParams.get('timeframe') || '4h'

    return HttpResponse.json({
      ...mockHeatmapData,
      timeframe,
    })
  }),

  // -------------------------------------------------------------------------
  // Health Check
  // -------------------------------------------------------------------------
  http.get('/api/health', () => {
    return HttpResponse.json({ status: 'ok' })
  }),

  // -------------------------------------------------------------------------
  // Chat API
  // -------------------------------------------------------------------------
  http.post('/api/chat', async ({ request }) => {
    const body = (await request.json()) as { message: string }

    const response: ChatResponse = {
      success: true,
      response: `This is a mock AI response to: "${body.message}"\n\n## Market Analysis\n\nBased on current market conditions, here's a summary:\n- BTC showing bullish momentum\n- ETH in accumulation phase\n\n*This is test data only.*`,
      market_summary: {
        total_coins: 100,
        overbought_count: 15,
        oversold_count: 20,
        strong_long_signals: 8,
        strong_short_signals: 5,
      },
      error: null,
    }

    return HttpResponse.json(response)
  }),

  // -------------------------------------------------------------------------
  // Fundamental Analysis API
  // -------------------------------------------------------------------------
  http.post('/api/fundamental', async ({ request }) => {
    const body = (await request.json()) as { symbol: string; timeframe: string }

    return HttpResponse.json({
      success: true,
      response: `## Fundamental Analysis for ${body.symbol}\n\n### Intrinsic Value\n- Strong use case and adoption\n- Active development team\n\n### Market Factors\n- Current market sentiment: Neutral\n- Regulatory outlook: Stable\n\n*Mock analysis for testing purposes.*`,
      error: null,
    })
  }),

  // -------------------------------------------------------------------------
  // API Key Settings
  // -------------------------------------------------------------------------
  http.get('/api/settings/apikey', () => {
    return HttpResponse.json(mockApiKeyStatus)
  }),

  http.post('/api/settings/apikey', async ({ request }) => {
    const body = (await request.json()) as { api_key: string }

    if (!body.api_key || body.api_key.trim() === '') {
      return HttpResponse.json(
        { success: false, error: 'API key is required' },
        { status: 400 }
      )
    }

    return HttpResponse.json({
      success: true,
      message: 'API key saved and validated successfully',
    })
  }),

  http.delete('/api/settings/apikey', () => {
    return HttpResponse.json({
      success: true,
      message: 'API key deleted successfully',
    })
  }),

  // -------------------------------------------------------------------------
  // Model Settings
  // -------------------------------------------------------------------------
  http.get('/api/settings/models', () => {
    return HttpResponse.json(mockModelsResponse)
  }),

  http.post('/api/settings/models', async ({ request }) => {
    const body = (await request.json()) as { model: string }

    return HttpResponse.json({
      success: true,
      message: `Model changed to ${body.model}`,
      current_model: body.model,
    })
  }),

  // -------------------------------------------------------------------------
  // Stats API
  // -------------------------------------------------------------------------
  http.get('/api/stats', () => {
    return HttpResponse.json({
      success: true,
      timeframe: '4h',
      stats: {
        total_coins: 100,
        layer_distribution: {
          long: { 1: 20, 2: 15, 3: 10, 4: 5, 5: 2 },
          short: { 1: 18, 2: 12, 3: 8, 4: 4, 5: 1 },
        },
        rsi_distribution: {
          overbought: 15,
          strong: 25,
          neutral: 35,
          weak: 15,
          oversold: 10,
        },
      },
    })
  }),
]

// ============================================================================
// Error Handlers (for testing error scenarios)
// ============================================================================

export const errorHandlers = {
  // Simulate API key not configured
  apiKeyNotConfigured: http.get('/api/settings/apikey', () => {
    return HttpResponse.json(mockApiKeyStatusUnconfigured)
  }),

  // Simulate chat service unavailable
  chatServiceUnavailable: http.post('/api/chat', () => {
    return HttpResponse.json(
      {
        success: false,
        response: '',
        market_summary: null,
        error: 'service_unavailable',
      },
      { status: 503 }
    )
  }),

  // Simulate rate limit
  rateLimited: http.get('/api/heatmap', () => {
    return HttpResponse.json(
      { success: false, error: 'Rate limit exceeded' },
      { status: 429 }
    )
  }),

  // Simulate server error
  serverError: http.get('/api/heatmap', () => {
    return HttpResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    )
  }),
}
