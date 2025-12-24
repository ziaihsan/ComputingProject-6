import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  RefreshCw, TrendingUp, TrendingDown, Loader2,
  Activity, Clock, BarChart3, Zap, ArrowUpRight, ArrowDownRight,
  Circle, ChevronUp, ChevronDown, Filter, Table2, LayoutGrid,
  ExternalLink, Coins
} from 'lucide-react'
import { Button } from './ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Card, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { cn, formatPrice } from '@/lib/utils'
import type { CoinSignal, Direction, Timeframe, CoinLimit, HeatmapResponse } from '@/types'

const API_BASE = 'http://localhost:8000'

// RSI Level Configuration (similar to Coinglass)
const RSI_LEVELS = {
  OVERBOUGHT: { min: 70, max: 100, label: 'OVERBOUGHT', color: 'from-red-500 to-red-600', bgColor: 'bg-red-500', textColor: 'text-red-500' },
  STRONG: { min: 60, max: 70, label: 'STRONG', color: 'from-orange-400 to-orange-500', bgColor: 'bg-orange-400', textColor: 'text-orange-500' },
  NEUTRAL: { min: 40, max: 60, label: 'NEUTRAL', color: 'from-slate-400 to-slate-500', bgColor: 'bg-slate-400', textColor: 'text-slate-500' },
  WEAK: { min: 30, max: 40, label: 'WEAK', color: 'from-cyan-400 to-cyan-500', bgColor: 'bg-cyan-400', textColor: 'text-cyan-500' },
  OVERSOLD: { min: 0, max: 30, label: 'OVERSOLD', color: 'from-emerald-500 to-emerald-600', bgColor: 'bg-emerald-500', textColor: 'text-emerald-500' },
}

const LAYER_CONFIG = [
  { label: 'ONLY EMA', shortLabel: 'EMA', icon: Activity, strength: 1 },
  { label: 'RSI KONVENSIONAL', shortLabel: 'RSI', icon: BarChart3, strength: 2 },
  { label: 'SMOOTHED RSI', shortLabel: 'S-RSI', icon: Zap, strength: 3 },
  { label: 'RSI + EMA', shortLabel: 'RSI+EMA', icon: TrendingUp, strength: 4 },
  { label: 'SMOOTHED RSI + EMA', shortLabel: 'S-RSI+EMA', icon: TrendingUp, strength: 5 },
]

type ViewMode = 'heatmap' | 'table'
type RSIFilter = 'all' | 'OVERBOUGHT' | 'STRONG' | 'NEUTRAL' | 'WEAK' | 'OVERSOLD'
type SortField = 'rank' | 'price' | 'price_1h' | 'price_24h' | 'rsi' | 'rsi_smoothed'
type SortDirection = 'asc' | 'desc'


// Get RSI color for heatmap cell
const getRSIColor = (rsi: number) => {
  if (rsi >= 70) return 'bg-gradient-to-br from-red-400 to-red-600'
  if (rsi >= 60) return 'bg-gradient-to-br from-orange-300 to-orange-500'
  if (rsi >= 40) return 'bg-gradient-to-br from-slate-300 to-slate-500'
  if (rsi >= 30) return 'bg-gradient-to-br from-cyan-300 to-cyan-500'
  return 'bg-gradient-to-br from-emerald-400 to-emerald-600'
}

// Get text color for RSI badge
const getRSIBadgeColor = (rsi: number) => {
  if (rsi >= 70) return 'bg-red-100 text-red-700 border-red-200'
  if (rsi >= 60) return 'bg-orange-100 text-orange-700 border-orange-200'
  if (rsi >= 40) return 'bg-slate-100 text-slate-700 border-slate-200'
  if (rsi >= 30) return 'bg-cyan-100 text-cyan-700 border-cyan-200'
  return 'bg-emerald-100 text-emerald-700 border-emerald-200'
}

export function Heatmap() {
  const [data, setData] = useState<CoinSignal[]>([])
  const [direction, setDirection] = useState<Direction>('long')
  const [timeframe, setTimeframe] = useState<Timeframe>('4h')
  const [limit, setLimit] = useState<CoinLimit>('100')
  const [isCustomLimit, setIsCustomLimit] = useState(false)
  const [customLimitInput, setCustomLimitInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<string>('')
  const [status, setStatus] = useState<'ok' | 'warning' | 'error'>('ok')
  const [hoveredCoin, setHoveredCoin] = useState<CoinSignal | null>(null)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  const [viewMode, setViewMode] = useState<ViewMode>('heatmap')
  const [rsiFilter, setRsiFilter] = useState<RSIFilter>('all')
  const [sortField, setSortField] = useState<SortField>('rank')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  const abortControllerRef = useRef<AbortController | null>(null)
  const fetchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const fetchData = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    setLoading(true)

    try {
      const response = await fetch(
        `${API_BASE}/api/heatmap?limit=${limit}&timeframe=${timeframe}`,
        { signal: abortControllerRef.current.signal }
      )
      const result: HeatmapResponse = await response.json()

      if (result.success && result.signals) {
        setData(result.signals)
        setLastUpdate(new Date().toLocaleTimeString())
        setStatus('ok')
      } else if (result.error?.includes('429')) {
        setLastUpdate('Rate limited')
        setStatus('warning')
      } else {
        setStatus('error')
        setLastUpdate('Error')
      }
    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') return
      setStatus('error')
      setLastUpdate('Offline')
    } finally {
      setLoading(false)
    }
  }, [limit, timeframe])

  const debouncedFetch = useCallback(() => {
    if (fetchTimeoutRef.current) clearTimeout(fetchTimeoutRef.current)
    fetchTimeoutRef.current = setTimeout(fetchData, 500)
  }, [fetchData])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 120000)
    return () => clearInterval(interval)
  }, [fetchData])

  useEffect(() => {
    debouncedFetch()
  }, [limit, timeframe, debouncedFetch])

  // Filter and sort data
  const filteredAndSortedData = useMemo(() => {
    let filtered = [...data]

    // Filter by RSI level
    if (rsiFilter !== 'all') {
      const level = RSI_LEVELS[rsiFilter]
      filtered = filtered.filter(coin => coin.rsi >= level.min && coin.rsi < level.max)
    }

    // Filter by direction (long/short layer > 0)
    const layerKey = direction === 'long' ? 'long_layer' : 'short_layer'
    if (viewMode === 'heatmap') {
      filtered = filtered.filter(c => c[layerKey] > 0)
    }

    // Sort
    filtered.sort((a, b) => {
      let aVal: number, bVal: number
      switch (sortField) {
        case 'rank': aVal = a.market_cap_rank || 9999; bVal = b.market_cap_rank || 9999; break
        case 'price': aVal = a.price; bVal = b.price; break
        case 'price_1h': aVal = 0; bVal = 0; break // No 1h data in type
        case 'price_24h': aVal = a.price_change_24h; bVal = b.price_change_24h; break
        case 'rsi': aVal = a.rsi; bVal = b.rsi; break
        case 'rsi_smoothed': aVal = a.rsi_smoothed; bVal = b.rsi_smoothed; break
        default: aVal = 0; bVal = 0
      }
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
    })

    return filtered
  }, [data, rsiFilter, sortField, sortDirection, direction, viewMode])

  const layerKey = direction === 'long' ? 'long_layer' : 'short_layer'

  // Group by layers for heatmap view
  const layerCoins: Record<number, CoinSignal[]> = { 1: [], 2: [], 3: [], 4: [], 5: [] }
  filteredAndSortedData.forEach(coin => {
    const layer = coin[layerKey]
    if (layer >= 1 && layer <= 5) {
      layerCoins[layer].push(coin)
    }
  })

  // RSI level stats
  const rsiStats = useMemo(() => {
    const stats = {
      OVERBOUGHT: 0,
      STRONG: 0,
      NEUTRAL: 0,
      WEAK: 0,
      OVERSOLD: 0,
    }
    data.forEach(coin => {
      if (coin.rsi >= 70) stats.OVERBOUGHT++
      else if (coin.rsi >= 60) stats.STRONG++
      else if (coin.rsi >= 40) stats.NEUTRAL++
      else if (coin.rsi >= 30) stats.WEAK++
      else stats.OVERSOLD++
    })
    return stats
  }, [data])

  const getBubbleSize = (coin: CoinSignal) => {
    const rank = coin.market_cap_rank || 100
    if (rank <= 10) return 52
    if (rank <= 30) return 46
    if (rank <= 50) return 42
    if (rank <= 100) return 38
    return 34
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  return (
    <div className="min-h-screen bg-[#0d1117] text-white">
      {/* Top Stats Bar - Coinglass Style */}
      <div className="border-b border-slate-800 bg-[#161b22]">
        <div className="max-w-7xl mx-auto px-4 py-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Total Coins:</span>
                <span className="text-white font-semibold">{data.length}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Signals:</span>
                <span className={cn(
                  "font-semibold",
                  direction === 'long' ? "text-emerald-400" : "text-red-400"
                )}>
                  {filteredAndSortedData.length} {direction.toUpperCase()}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className={cn(
                "h-2 w-2 rounded-full",
                status === 'ok' && "bg-emerald-500 animate-pulse",
                status === 'warning' && "bg-amber-500",
                status === 'error' && "bg-red-500"
              )} />
              <span className="text-slate-400">
                {status === 'ok' ? `Updated ${lastUpdate}` : lastUpdate}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-4 md:p-6 space-y-4">
        {/* Header Card - Coinglass Style */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          <Card className="border-slate-800 bg-[#161b22]">
            <CardHeader className="pb-4">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                {/* Title Section */}
                <div className="flex items-center gap-4">
                  <motion.div
                    className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20"
                    whileHover={{ scale: 1.05, rotate: 5 }}
                    transition={{ type: "spring", stiffness: 400 }}
                  >
                    <Activity className="h-6 w-6 text-white" />
                  </motion.div>
                  <div>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-xl md:text-2xl text-white">
                        Crypto Market RSI Heatmap
                      </CardTitle>
                      <Badge variant="live" className="gap-1 bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                        <Circle className="h-2 w-2 fill-current" />
                        Live
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-400 mt-0.5">
                      Real-time RSI analysis across {data.length} cryptocurrencies
                    </p>
                  </div>
                </div>

                {/* Tab Controls - Coinglass Style */}
                <div className="flex items-center gap-2 bg-slate-800/50 rounded-lg p-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDirection('long')}
                    className={cn(
                      "gap-1.5 rounded-md px-4 transition-all",
                      direction === 'long'
                        ? "bg-emerald-500 text-white hover:bg-emerald-600"
                        : "text-slate-400 hover:text-white hover:bg-slate-700"
                    )}
                  >
                    <TrendingUp className="h-4 w-4" />
                    Long
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDirection('short')}
                    className={cn(
                      "gap-1.5 rounded-md px-4 transition-all",
                      direction === 'short'
                        ? "bg-red-500 text-white hover:bg-red-600"
                        : "text-slate-400 hover:text-white hover:bg-slate-700"
                    )}
                  >
                    <TrendingDown className="h-4 w-4" />
                    Short
                  </Button>
                </div>
              </div>
            </CardHeader>
          </Card>
        </motion.div>

        {/* Controls Bar */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="flex flex-wrap items-center justify-between gap-4"
        >
          {/* RSI Level Filters - Coinglass Style */}
          <div className="flex flex-wrap items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <button
              onClick={() => setRsiFilter('all')}
              className={cn(
                "px-3 py-1.5 rounded-md text-xs font-medium transition-all",
                rsiFilter === 'all'
                  ? "bg-blue-500 text-white"
                  : "bg-slate-800 text-slate-400 hover:bg-slate-700"
              )}
            >
              ALL ({data.length})
            </button>
            {Object.entries(RSI_LEVELS).map(([key, level]) => (
              <button
                key={key}
                onClick={() => setRsiFilter(key as RSIFilter)}
                className={cn(
                  "px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5",
                  rsiFilter === key
                    ? `bg-gradient-to-r ${level.color} text-white`
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                )}
              >
                <div className={cn("w-2 h-2 rounded-full", level.bgColor)} />
                {level.label} ({rsiStats[key as keyof typeof rsiStats]})
              </button>
            ))}
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-3 ml-auto">
            {/* View Toggle - More visible with labels */}
            <div className="flex bg-slate-800/80 rounded-lg p-1 border border-slate-700">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setViewMode('heatmap')}
                className={cn(
                  "h-8 px-3 gap-1.5 rounded-md transition-all text-xs font-medium",
                  viewMode === 'heatmap'
                    ? "bg-blue-600 text-white shadow-md"
                    : "text-slate-400 hover:text-white hover:bg-slate-700"
                )}
              >
                <LayoutGrid className="h-4 w-4" />
                <span>Heatmap</span>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setViewMode('table')}
                className={cn(
                  "h-8 px-3 gap-1.5 rounded-md transition-all text-xs font-medium",
                  viewMode === 'table'
                    ? "bg-blue-600 text-white shadow-md"
                    : "text-slate-400 hover:text-white hover:bg-slate-700"
                )}
              >
                <Table2 className="h-4 w-4" />
                <span>Table</span>
              </Button>
            </div>

            {/* Timeframe Select */}
            <Select value={timeframe} onValueChange={(v) => setTimeframe(v as Timeframe)}>
              <SelectTrigger className="w-[130px] bg-slate-800 border-slate-700 text-white">
                <Clock className="h-4 w-4 mr-2 text-slate-400 flex-shrink-0" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700 text-white">
                <SelectItem value="15m" className="text-white focus:bg-slate-700 focus:text-white">15 min</SelectItem>
                <SelectItem value="1h" className="text-white focus:bg-slate-700 focus:text-white">1 hour</SelectItem>
                <SelectItem value="4h" className="text-white focus:bg-slate-700 focus:text-white">4 hour</SelectItem>
                <SelectItem value="12h" className="text-white focus:bg-slate-700 focus:text-white">12 hour</SelectItem>
                <SelectItem value="1d" className="text-white focus:bg-slate-700 focus:text-white">1 day</SelectItem>
                <SelectItem value="1w" className="text-white focus:bg-slate-700 focus:text-white">1 week</SelectItem>
              </SelectContent>
            </Select>

            {/* Limit Select */}
            {isCustomLimit ? (
              <div className="flex items-center gap-1">
                <div className="flex items-center bg-slate-800 border border-slate-700 rounded-md px-3 h-10">
                  <Coins className="h-4 w-4 mr-2 text-amber-400 flex-shrink-0" />
                  <input
                    type="number"
                    min="1"
                    value={customLimitInput}
                    onChange={(e) => setCustomLimitInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        const val = parseInt(customLimitInput)
                        if (val >= 1) {
                          setLimit(customLimitInput)
                          setIsCustomLimit(false)
                        }
                      } else if (e.key === 'Escape') {
                        setIsCustomLimit(false)
                        setCustomLimitInput('')
                      }
                    }}
                    placeholder="coins"
                    className="w-16 bg-transparent text-white text-sm outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    autoFocus
                  />
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-10 px-2 text-emerald-400 hover:text-emerald-300 hover:bg-slate-700"
                  onClick={() => {
                    const val = parseInt(customLimitInput)
                    if (val >= 1) {
                      setLimit(customLimitInput)
                      setIsCustomLimit(false)
                    }
                  }}
                >
                  OK
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-10 px-2 text-slate-400 hover:text-slate-300 hover:bg-slate-700"
                  onClick={() => {
                    setIsCustomLimit(false)
                    setCustomLimitInput('')
                  }}
                >
                  X
                </Button>
              </div>
            ) : !['50', '100', '150', '200'].includes(limit) ? (
              <div className="flex items-center gap-1">
                <button
                  onClick={() => {
                    setIsCustomLimit(true)
                    setCustomLimitInput(limit)
                  }}
                  className="flex items-center w-[155px] bg-slate-800 border border-slate-700 rounded-md px-3 h-10 text-white hover:bg-slate-700 transition-colors"
                >
                  <Coins className="h-4 w-4 mr-2 text-amber-400 flex-shrink-0" />
                  <span className="text-sm">{limit} coins</span>
                </button>
                <Select
                  value=""
                  onValueChange={(v) => {
                    if (v === 'custom') {
                      setIsCustomLimit(true)
                      setCustomLimitInput(limit)
                    } else {
                      setLimit(v as CoinLimit)
                    }
                  }}
                >
                  <SelectTrigger className="w-10 bg-slate-800 border-slate-700 text-white px-2">
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700 text-white">
                    <SelectItem value="50" className="text-white focus:bg-slate-700 focus:text-white">50 coins</SelectItem>
                    <SelectItem value="100" className="text-white focus:bg-slate-700 focus:text-white">100 coins</SelectItem>
                    <SelectItem value="150" className="text-white focus:bg-slate-700 focus:text-white">150 coins</SelectItem>
                    <SelectItem value="200" className="text-white focus:bg-slate-700 focus:text-white">200 coins</SelectItem>
                    <SelectItem value="custom" className="text-amber-400 focus:bg-slate-700 focus:text-amber-300">Custom...</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            ) : (
              <Select
                value={limit}
                onValueChange={(v) => {
                  if (v === 'custom') {
                    setIsCustomLimit(true)
                    setCustomLimitInput(limit)
                  } else {
                    setLimit(v as CoinLimit)
                  }
                }}
              >
                <SelectTrigger className="w-[155px] bg-slate-800 border-slate-700 text-white">
                  <Coins className="h-4 w-4 mr-2 text-amber-400 flex-shrink-0" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700 text-white">
                  <SelectItem value="50" className="text-white focus:bg-slate-700 focus:text-white">50 coins</SelectItem>
                  <SelectItem value="100" className="text-white focus:bg-slate-700 focus:text-white">100 coins</SelectItem>
                  <SelectItem value="150" className="text-white focus:bg-slate-700 focus:text-white">150 coins</SelectItem>
                  <SelectItem value="200" className="text-white focus:bg-slate-700 focus:text-white">200 coins</SelectItem>
                  <SelectItem value="custom" className="text-amber-400 focus:bg-slate-700 focus:text-amber-300">Custom...</SelectItem>
                </SelectContent>
              </Select>
            )}

            {/* Refresh Button */}
            <Button
              onClick={fetchData}
              disabled={loading}
              className="gap-2 bg-blue-600 hover:bg-blue-700"
            >
              <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
            </Button>
          </div>
        </motion.div>

        {/* RSI Level Legend */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="flex items-center justify-center gap-2"
        >
          <span className="text-xs text-slate-500">RSI Scale:</span>
          <div className="flex flex-col">
            <div className="flex h-3 rounded-full overflow-hidden">
              <div className="w-16 h-full bg-gradient-to-r from-emerald-600 to-emerald-500" />
              <div className="w-12 h-full bg-gradient-to-r from-cyan-500 to-cyan-400" />
              <div className="w-20 h-full bg-gradient-to-r from-slate-500 to-slate-400" />
              <div className="w-12 h-full bg-gradient-to-r from-orange-400 to-orange-500" />
              <div className="w-16 h-full bg-gradient-to-r from-red-500 to-red-600" />
            </div>
            <div className="relative h-4 text-[10px] text-slate-400 mt-0.5" style={{ width: '304px' }}>
              <span className="absolute" style={{ left: '0px' }}>0</span>
              <span className="absolute" style={{ left: '58px' }}>30</span>
              <span className="absolute" style={{ left: '106px' }}>40</span>
              <span className="absolute" style={{ left: '187px' }}>60</span>
              <span className="absolute" style={{ left: '234px' }}>70</span>
              <span className="absolute" style={{ right: '0px' }}>100</span>
            </div>
          </div>
        </motion.div>

        {/* Main Content */}
        <AnimatePresence mode="wait">
          {viewMode === 'heatmap' ? (
            // Heatmap View
            <motion.div
              key="heatmap"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Card className="border-slate-800 bg-[#161b22] overflow-hidden">
                <div ref={containerRef} className="relative h-[550px]">
                  {/* Loading Overlay */}
                  <AnimatePresence>
                    {loading && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-[#161b22]/95 backdrop-blur-md z-50 flex items-center justify-center"
                      >
                        <motion.div
                          className="flex flex-col items-center gap-4"
                          initial={{ scale: 0.9 }}
                          animate={{ scale: 1 }}
                        >
                          <div className="relative">
                            <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                              <Loader2 className="h-8 w-8 text-white animate-spin" />
                            </div>
                            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 animate-ping opacity-20" />
                          </div>
                          <div className="text-center">
                            <p className="font-semibold text-white">Loading market data</p>
                            <p className="text-sm text-slate-400">Fetching from CoinGecko...</p>
                          </div>
                        </motion.div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Zones with Gradients - Coinglass Style */}
                  {[5, 4, 3, 2, 1].map((layer, idx) => {
                    const coinsInLayer = layerCoins[layer].length
                    const config = LAYER_CONFIG[layer - 1]
                    const zoneColor = layer >= 4
                      ? (direction === 'long' ? 'from-emerald-900/30 to-emerald-800/20' : 'from-red-900/30 to-red-800/20')
                      : layer >= 3
                        ? 'from-slate-800/50 to-slate-700/30'
                        : (direction === 'long' ? 'from-red-900/20 to-red-800/10' : 'from-emerald-900/20 to-emerald-800/10')

                    return (
                      <div
                        key={layer}
                        className={cn(
                          "absolute left-0 right-28 h-[110px] transition-all duration-500",
                          `bg-gradient-to-r ${zoneColor}`
                        )}
                        style={{ top: idx * 110 }}
                      >
                        {/* Grid lines */}
                        <div className="absolute inset-0 opacity-10">
                          <div className="h-full w-full" style={{
                            backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0.1) 1px, transparent 1px)',
                            backgroundSize: '60px 100%'
                          }} />
                        </div>

                        {/* Zone separator */}
                        {idx < 4 && (
                          <div className="absolute bottom-0 left-0 right-0 h-px bg-slate-700/50" />
                        )}

                        {/* Layer label on left */}
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                          <Badge
                            variant={layer >= 4 ? "success" : layer >= 3 ? "warning" : "secondary"}
                            className="text-[10px] px-2 py-0.5 bg-slate-800/80"
                          >
                            L{layer}
                          </Badge>
                          <span className="text-[10px] text-slate-500 hidden md:inline">
                            {config.shortLabel}
                          </span>
                          {coinsInLayer > 0 && (
                            <span className="text-[10px] text-slate-400">
                              ({coinsInLayer})
                            </span>
                          )}
                        </div>
                      </div>
                    )
                  })}

                  {/* Right Sidebar Labels - Coinglass Style */}
                  <div className="absolute right-0 top-0 bottom-0 w-28 bg-[#0d1117] border-l border-slate-800">
                    {[5, 4, 3, 2, 1].map((layer, idx) => {
                      const config = LAYER_CONFIG[layer - 1]
                      const IconComponent = config.icon

                      return (
                        <motion.div
                          key={layer}
                          className="absolute right-0 w-28 h-[110px] flex flex-col items-center justify-center gap-1 px-2 border-b border-slate-800"
                          style={{ top: idx * 110 }}
                          whileHover={{ backgroundColor: 'rgba(30, 41, 59, 0.5)' }}
                        >
                          <div className={cn(
                            "p-2 rounded-lg",
                            layer >= 4 ? "bg-emerald-900/30" : layer >= 3 ? "bg-amber-900/30" : "bg-slate-800/50"
                          )}>
                            <IconComponent className={cn(
                              "h-4 w-4",
                              layer >= 4 ? "text-emerald-400" : layer >= 3 ? "text-amber-400" : "text-slate-400"
                            )} />
                          </div>
                          <span className="text-[10px] font-medium text-slate-400 text-center leading-tight">
                            {config.shortLabel}
                          </span>
                          <span className={cn(
                            "text-xs font-bold",
                            layer >= 4 ? "text-emerald-400" : layer >= 3 ? "text-amber-400" : "text-slate-500"
                          )}>
                            {layerCoins[layer].length}
                          </span>
                        </motion.div>
                      )
                    })}
                  </div>

                  {/* Coins - Bubble Style with RSI Colors */}
                  <div className="absolute inset-0 right-28 overflow-hidden pl-16">
                    <AnimatePresence mode="popLayout">
                      {[5, 4, 3, 2, 1].map((layer, layerIdx) => {
                        const coins = layerCoins[layer]
                        const zoneTop = layerIdx * 110
                        const zoneCenter = zoneTop + 55

                        return coins.map((coin, coinIdx) => {
                          const containerWidth = containerRef.current?.clientWidth ? containerRef.current.clientWidth - 180 : 700
                          const spacing = Math.min(65, (containerWidth - 40) / Math.max(coins.length, 1))
                          const totalWidth = coins.length * spacing
                          const startX = (containerWidth - totalWidth) / 2
                          const x = startX + coinIdx * spacing + spacing / 2
                          const yOffset = (Math.sin(coinIdx * 1.5 + layer) * 0.3) * 70
                          const y = zoneCenter + yOffset
                          const size = getBubbleSize(coin)

                          return (
                            <motion.div
                              key={`${coin.symbol}-${layer}`}
                              initial={{ opacity: 0, scale: 0, y: 20 }}
                              animate={{
                                opacity: 1,
                                scale: 1,
                                y: 0,
                                x: x,
                                top: y,
                              }}
                              exit={{ opacity: 0, scale: 0 }}
                              transition={{
                                type: "spring",
                                stiffness: 400,
                                damping: 25,
                                delay: coinIdx * 0.01 + layerIdx * 0.03
                              }}
                              className={cn(
                                "absolute flex items-center justify-center rounded-full cursor-pointer",
                                "text-[9px] font-bold text-white",
                                "border-2 border-white/20",
                                "shadow-lg hover:shadow-xl",
                                getRSIColor(coin.rsi)
                              )}
                              style={{
                                width: size,
                                height: size,
                                fontSize: size > 44 ? '10px' : '9px',
                                transform: 'translate(-50%, -50%)',
                                left: 0,
                              }}
                              onMouseEnter={(e) => {
                                setHoveredCoin(coin)
                                setMousePos({ x: e.clientX, y: e.clientY })
                              }}
                              onMouseMove={(e) => setMousePos({ x: e.clientX, y: e.clientY })}
                              onMouseLeave={() => setHoveredCoin(null)}
                              whileHover={{
                                scale: 1.3,
                                zIndex: 100,
                              }}
                            >
                              {coin.symbol.slice(0, 4)}
                            </motion.div>
                          )
                        })
                      })}
                    </AnimatePresence>

                    {/* No Signal Message */}
                    {filteredAndSortedData.length === 0 && !loading && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="absolute inset-0 flex items-center justify-center"
                      >
                        <div className="text-center bg-slate-800/80 backdrop-blur-sm rounded-2xl p-8">
                          <div className="h-16 w-16 mx-auto mb-4 rounded-2xl bg-slate-700 flex items-center justify-center">
                            {direction === 'long' ? (
                              <TrendingUp className="h-8 w-8 text-slate-500" />
                            ) : (
                              <TrendingDown className="h-8 w-8 text-slate-500" />
                            )}
                          </div>
                          <p className="text-lg font-semibold text-white">
                            No {direction.toUpperCase()} signals detected
                          </p>
                          <p className="text-sm text-slate-400 mt-1">
                            Try switching to {direction === 'long' ? 'Short' : 'Long'} view or changing filters
                          </p>
                        </div>
                      </motion.div>
                    )}
                  </div>
                </div>
              </Card>
            </motion.div>
          ) : (
            // Table View - Coinglass Style
            <motion.div
              key="table"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Card className="border-slate-800 bg-[#161b22] overflow-hidden">
                {loading ? (
                  <div className="flex items-center justify-center h-96">
                    <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-800/50">
                          <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 w-12">#</th>
                          <th className="text-left px-4 py-3 text-xs font-medium text-slate-400">Symbol</th>
                          <th
                            className="text-right px-4 py-3 text-xs font-medium text-slate-400 cursor-pointer hover:text-white"
                            onClick={() => handleSort('price')}
                          >
                            <div className="flex items-center justify-end gap-1">
                              Price
                              {sortField === 'price' && (
                                sortDirection === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
                              )}
                            </div>
                          </th>
                          <th
                            className="text-right px-4 py-3 text-xs font-medium text-slate-400 cursor-pointer hover:text-white"
                            onClick={() => handleSort('price_24h')}
                          >
                            <div className="flex items-center justify-end gap-1">
                              24h %
                              {sortField === 'price_24h' && (
                                sortDirection === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
                              )}
                            </div>
                          </th>
                          <th
                            className="text-right px-4 py-3 text-xs font-medium text-slate-400 cursor-pointer hover:text-white"
                            onClick={() => handleSort('rsi')}
                          >
                            <div className="flex items-center justify-end gap-1">
                              RSI ({timeframe})
                              {sortField === 'rsi' && (
                                sortDirection === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
                              )}
                            </div>
                          </th>
                          <th
                            className="text-right px-4 py-3 text-xs font-medium text-slate-400 cursor-pointer hover:text-white"
                            onClick={() => handleSort('rsi_smoothed')}
                          >
                            <div className="flex items-center justify-end gap-1">
                              RSI Smoothed
                              {sortField === 'rsi_smoothed' && (
                                sortDirection === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
                              )}
                            </div>
                          </th>
                          <th className="text-center px-4 py-3 text-xs font-medium text-slate-400">Signal</th>
                          <th className="text-center px-4 py-3 text-xs font-medium text-slate-400 w-20">Trade</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredAndSortedData.slice(0, parseInt(limit)).map((coin, idx) => (
                          <motion.tr
                            key={coin.symbol}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.02 }}
                            className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
                          >
                            <td className="px-4 py-3 text-sm text-slate-500">{coin.market_cap_rank || idx + 1}</td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <div className={cn(
                                  "h-8 w-8 rounded-full flex items-center justify-center text-[10px] font-bold text-white",
                                  getRSIColor(coin.rsi)
                                )}>
                                  {coin.symbol.slice(0, 2)}
                                </div>
                                <div>
                                  <div className="font-medium text-white">{coin.symbol}</div>
                                  <div className="text-xs text-slate-500">{coin.full_name}</div>
                                </div>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-right font-medium text-white">
                              ${formatPrice(coin.price)}
                            </td>
                            <td className={cn(
                              "px-4 py-3 text-right font-medium",
                              coin.price_change_24h >= 0 ? "text-emerald-400" : "text-red-400"
                            )}>
                              <div className="flex items-center justify-end gap-1">
                                {coin.price_change_24h >= 0 ? (
                                  <ArrowUpRight className="h-3 w-3" />
                                ) : (
                                  <ArrowDownRight className="h-3 w-3" />
                                )}
                                {Math.abs(coin.price_change_24h).toFixed(2)}%
                              </div>
                            </td>
                            <td className="px-4 py-3 text-right">
                              <span className={cn(
                                "px-2 py-1 rounded text-xs font-semibold border",
                                getRSIBadgeColor(coin.rsi)
                              )}>
                                {coin.rsi.toFixed(1)}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right">
                              <span className={cn(
                                "px-2 py-1 rounded text-xs font-semibold border",
                                getRSIBadgeColor(coin.rsi_smoothed)
                              )}>
                                {coin.rsi_smoothed.toFixed(1)}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-center">
                              {coin[layerKey] > 0 ? (
                                <Badge
                                  variant={coin[layerKey] >= 4 ? "success" : coin[layerKey] >= 3 ? "warning" : "secondary"}
                                  className="text-[10px]"
                                >
                                  L{coin[layerKey]} {direction === 'long' ? '↑' : '↓'}
                                </Badge>
                              ) : (
                                <span className="text-slate-600">-</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-center">
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-7 px-2 text-xs text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                              >
                                Trade <ExternalLink className="h-3 w-3 ml-1" />
                              </Button>
                            </td>
                          </motion.tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Info Section - Only show in Table View */}
        {viewMode === 'table' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="bg-[#161b22] rounded-xl border border-slate-800 p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-3">
              How to use the Relative Strength Index (RSI) Heatmap
            </h3>
            <div className="space-y-3 text-sm text-slate-400">
              <p>
                The RSI Heatmap provides a visual representation of the Relative Strength Index across multiple cryptocurrencies.
                The RSI is a momentum oscillator that measures the speed and change of price movements on a scale of 0 to 100.
              </p>
              <div className="grid md:grid-cols-2 gap-4 mt-4">
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <h4 className="font-medium text-white mb-2 flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    Overbought (RSI &gt; 70)
                  </h4>
                  <p className="text-xs">Asset may be overvalued and could experience a price correction.</p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <h4 className="font-medium text-white mb-2 flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-emerald-500" />
                    Oversold (RSI &lt; 30)
                  </h4>
                  <p className="text-xs">Asset may be undervalued and could experience a price increase.</p>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Tooltip */}
        <AnimatePresence>
          {hoveredCoin && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 10 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
              className="fixed z-[100] bg-[#1c2128] border border-slate-700 text-white rounded-xl px-4 py-3 shadow-2xl pointer-events-none min-w-[200px]"
              style={{
                left: Math.min(mousePos.x + 15, window.innerWidth - 230),
                top: Math.min(mousePos.y + 15, window.innerHeight - 260),
              }}
            >
              <div className="flex items-center gap-3 mb-3 pb-2 border-b border-slate-700">
                <div className={cn(
                  "h-9 w-9 rounded-lg flex items-center justify-center text-xs font-bold text-white",
                  getRSIColor(hoveredCoin.rsi)
                )}>
                  {hoveredCoin.symbol.slice(0, 2)}
                </div>
                <div>
                  <div className="font-bold">{hoveredCoin.symbol}</div>
                  <div className="text-slate-400 text-xs">{hoveredCoin.full_name}</div>
                </div>
              </div>

              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Price</span>
                  <span className="font-semibold">${formatPrice(hoveredCoin.price)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">24h Change</span>
                  <span className={cn(
                    "font-semibold flex items-center gap-1",
                    hoveredCoin.price_change_24h >= 0 ? "text-emerald-400" : "text-red-400"
                  )}>
                    {hoveredCoin.price_change_24h >= 0 ? '+' : ''}{hoveredCoin.price_change_24h.toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">RSI ({timeframe})</span>
                  <span className={cn(
                    "font-semibold px-1.5 py-0.5 rounded text-[10px]",
                    getRSIBadgeColor(hoveredCoin.rsi)
                  )}>
                    {hoveredCoin.rsi.toFixed(1)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">RSI Smoothed</span>
                  <span className={cn(
                    "font-semibold px-1.5 py-0.5 rounded text-[10px]",
                    getRSIBadgeColor(hoveredCoin.rsi_smoothed)
                  )}>
                    {hoveredCoin.rsi_smoothed.toFixed(1)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Signal Layer</span>
                  <Badge
                    variant={hoveredCoin[layerKey] >= 4 ? "success" : hoveredCoin[layerKey] >= 3 ? "warning" : "secondary"}
                    className="text-[10px] px-1.5"
                  >
                    L{hoveredCoin[layerKey]}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Rank</span>
                  <span className="font-semibold">#{hoveredCoin.market_cap_rank}</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}