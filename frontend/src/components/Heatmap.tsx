import { useState, useEffect, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  RefreshCw, TrendingUp, TrendingDown, Loader2, 
  Activity, Clock, BarChart3, Zap, ArrowUpRight, ArrowDownRight,
  Circle
} from 'lucide-react'
import { Button } from './ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Card, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { cn, formatPrice } from '@/lib/utils'
import type { CoinSignal, Direction, Timeframe, CoinLimit, HeatmapResponse } from '@/types'

const API_BASE = 'http://localhost:8000'

const LAYER_CONFIG = [
  { label: 'ONLY EMA', shortLabel: 'EMA', icon: Activity, strength: 1 },
  { label: 'RSI KONVENSIONAL', shortLabel: 'RSI', icon: BarChart3, strength: 2 },
  { label: 'SMOOTHED RSI', shortLabel: 'S-RSI', icon: Zap, strength: 3 },
  { label: 'RSI + EMA', shortLabel: 'RSI+EMA', icon: TrendingUp, strength: 4 },
  { label: 'SMOOTHED RSI + EMA', shortLabel: 'S-RSI+EMA', icon: TrendingUp, strength: 5 },
]

const LONG_GRADIENTS = [
  'from-rose-100 to-rose-200',
  'from-rose-200 to-rose-300',
  'from-emerald-200 to-emerald-300',
  'from-emerald-300 to-emerald-400',
  'from-emerald-400 to-emerald-500',
]

const SHORT_GRADIENTS = [
  'from-teal-100 to-teal-200',
  'from-emerald-200 to-emerald-300',
  'from-rose-200 to-rose-300',
  'from-rose-300 to-rose-400',
  'from-rose-400 to-rose-500',
]

export function Heatmap() {
  const [data, setData] = useState<CoinSignal[]>([])
  const [direction, setDirection] = useState<Direction>('long')
  const [timeframe, setTimeframe] = useState<Timeframe>('4h')
  const [limit, setLimit] = useState<CoinLimit>('100')
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<string>('')
  const [status, setStatus] = useState<'ok' | 'warning' | 'error'>('ok')
  const [hoveredCoin, setHoveredCoin] = useState<CoinSignal | null>(null)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  const [hoveredZone, setHoveredZone] = useState<number | null>(null)
  
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

  const layerKey = direction === 'long' ? 'long_layer' : 'short_layer'
  const filteredCoins = data.filter(c => c[layerKey] > 0)
  const zoneGradients = direction === 'long' ? LONG_GRADIENTS : SHORT_GRADIENTS

  const layerCoins: Record<number, CoinSignal[]> = { 1: [], 2: [], 3: [], 4: [], 5: [] }
  filteredCoins.forEach(coin => {
    const layer = coin[layerKey]
    if (layer >= 1 && layer <= 5) {
      layerCoins[layer].push(coin)
    }
  })

  const getBubbleSize = (coin: CoinSignal) => {
    const rank = coin.market_cap_rank || 100
    if (rank <= 10) return 48
    if (rank <= 30) return 42
    if (rank <= 50) return 38
    if (rank <= 100) return 34
    return 30
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 p-4 md:p-6">
      <div className="max-w-7xl mx-auto space-y-4">
        {/* Header Card */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                {/* Title Section */}
                <div className="flex items-center gap-4">
                  <motion.div 
                    className="h-12 w-12 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/25"
                    whileHover={{ scale: 1.05, rotate: 5 }}
                    transition={{ type: "spring", stiffness: 400 }}
                  >
                    <Activity className="h-6 w-6 text-white" />
                  </motion.div>
                  <div>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-xl md:text-2xl bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
                        Crypto EMA + RSI Heatmap
                      </CardTitle>
                      <Badge variant="live" className="gap-1">
                        <Circle className="h-2 w-2 fill-current" />
                        Live
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-0.5">
                      Real-time trading signal detection across {data.length} cryptocurrencies
                    </p>
                  </div>
                </div>
                
                {/* Controls */}
                <div className="flex flex-wrap items-center gap-3">
                  {/* Direction Toggle */}
                  <div className="flex bg-slate-100 rounded-xl p-1.5 shadow-inner">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDirection('long')}
                      className={cn(
                        "gap-1.5 rounded-lg transition-all duration-200",
                        direction === 'long' 
                          ? "bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-md shadow-green-500/25 hover:from-green-600 hover:to-emerald-600" 
                          : "hover:bg-slate-200"
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
                        "gap-1.5 rounded-lg transition-all duration-200",
                        direction === 'short' 
                          ? "bg-gradient-to-r from-red-500 to-rose-500 text-white shadow-md shadow-red-500/25 hover:from-red-600 hover:to-rose-600" 
                          : "hover:bg-slate-200"
                      )}
                    >
                      <TrendingDown className="h-4 w-4" />
                      Short
                    </Button>
                  </div>

                  {/* Timeframe Select */}
                  <Select value={timeframe} onValueChange={(v) => setTimeframe(v as Timeframe)}>
                    <SelectTrigger className="w-[110px] bg-white shadow-sm border-slate-200">
                      <Clock className="h-4 w-4 mr-2 text-slate-400" />
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15m">15 min</SelectItem>
                      <SelectItem value="1h">1 hour</SelectItem>
                      <SelectItem value="4h">4 hour</SelectItem>
                      <SelectItem value="1d">1 day</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* Limit Select */}
                  <Select value={limit} onValueChange={(v) => setLimit(v as CoinLimit)}>
                    <SelectTrigger className="w-[130px] bg-white shadow-sm border-slate-200">
                      <BarChart3 className="h-4 w-4 mr-2 text-slate-400" />
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="50">50 coins</SelectItem>
                      <SelectItem value="100">100 coins</SelectItem>
                      <SelectItem value="150">150 coins</SelectItem>
                      <SelectItem value="200">200 coins</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* Refresh Button */}
                  <Button 
                    onClick={fetchData} 
                    disabled={loading} 
                    className="gap-2 bg-gradient-to-r from-slate-800 to-slate-900 hover:from-slate-900 hover:to-slate-950 shadow-lg"
                  >
                    <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                    Refresh
                  </Button>
                </div>
              </div>
            </CardHeader>
          </Card>
        </motion.div>

        {/* Heatmap */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
        >
          <Card className="border-0 shadow-xl bg-white/90 backdrop-blur-sm overflow-hidden">
            <div ref={containerRef} className="relative h-[600px]">
              {/* Loading Overlay */}
              <AnimatePresence>
                {loading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 bg-white/90 backdrop-blur-md z-50 flex items-center justify-center"
                  >
                    <motion.div 
                      className="flex flex-col items-center gap-4"
                      initial={{ scale: 0.9 }}
                      animate={{ scale: 1 }}
                    >
                      <div className="relative">
                        <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                          <Loader2 className="h-8 w-8 text-white animate-spin" />
                        </div>
                        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 animate-ping opacity-20" />
                      </div>
                      <div className="text-center">
                        <p className="font-semibold text-slate-700">Loading market data</p>
                        <p className="text-sm text-slate-500">Fetching from CoinGecko...</p>
                      </div>
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Zones with Gradients */}
              {[5, 4, 3, 2, 1].map((layer, idx) => {
                return (
                  <motion.div
                    key={layer}
                    className={cn(
                      "absolute left-0 right-24 h-[120px] transition-all duration-500",
                      `bg-gradient-to-r ${zoneGradients[layer - 1]}`,
                      hoveredZone === layer && "brightness-105"
                    )}
                    style={{ top: idx * 120 }}
                    onMouseEnter={() => setHoveredZone(layer)}
                    onMouseLeave={() => setHoveredZone(null)}
                  >
                    {/* Grid lines */}
                    <div className="absolute inset-0 opacity-20">
                      <div className="h-full w-full" style={{
                        backgroundImage: 'linear-gradient(to right, rgba(0,0,0,0.05) 1px, transparent 1px)',
                        backgroundSize: '50px 100%'
                      }} />
                    </div>
                    
                    {/* Zone separator */}
                    {idx < 4 && (
                      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-slate-400/30 to-transparent" />
                    )}
                  </motion.div>
                )
              })}

              {/* Right Sidebar Labels */}
              <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-white via-white to-transparent">
                {[5, 4, 3, 2, 1].map((layer, idx) => {
                  const config = LAYER_CONFIG[layer - 1]
                  const IconComponent = config.icon
                  const coinsInLayer = layerCoins[layer].length
                  
                  return (
                    <motion.div
                      key={layer}
                      className="absolute right-0 w-24 h-[120px] flex flex-col items-center justify-center gap-1.5 px-2"
                      style={{ top: idx * 120 }}
                      whileHover={{ x: -4 }}
                    >
                      <div className={cn(
                        "p-1.5 rounded-lg",
                        layer >= 4 ? "bg-emerald-100" : layer >= 3 ? "bg-amber-100" : "bg-slate-100"
                      )}>
                        <IconComponent className={cn(
                          "h-4 w-4",
                          layer >= 4 ? "text-emerald-600" : layer >= 3 ? "text-amber-600" : "text-slate-600"
                        )} />
                      </div>
                      <Badge 
                        variant={layer >= 4 ? "success" : layer >= 3 ? "warning" : "secondary"}
                        className="text-[10px] px-1.5"
                      >
                        L{layer}
                      </Badge>
                      <span className="text-[9px] font-medium text-slate-500 text-center leading-tight">
                        {config.shortLabel}
                      </span>
                      {coinsInLayer > 0 && (
                        <span className="text-[10px] font-bold text-slate-700">
                          {coinsInLayer}
                        </span>
                      )}
                    </motion.div>
                  )
                })}
              </div>

              {/* Coins */}
              <div className="absolute inset-0 right-24 overflow-hidden">
                <AnimatePresence mode="popLayout">
                  {[5, 4, 3, 2, 1].map((layer, layerIdx) => {
                    const coins = layerCoins[layer]
                    const zoneTop = layerIdx * 120
                    const zoneCenter = zoneTop + 60

                    return coins.map((coin, coinIdx) => {
                      const containerWidth = containerRef.current?.clientWidth ? containerRef.current.clientWidth - 96 : 800
                      const spacing = Math.min(70, (containerWidth - 60) / Math.max(coins.length, 1))
                      const totalWidth = coins.length * spacing
                      const startX = (containerWidth - totalWidth) / 2
                      const x = startX + coinIdx * spacing + spacing / 2
                      const yOffset = (Math.sin(coinIdx * 1.5 + layer) * 0.35) * 80
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
                            delay: coinIdx * 0.015 + layerIdx * 0.05
                          }}
                          className={cn(
                            "absolute flex items-center justify-center rounded-full cursor-pointer",
                            "text-[9px] font-bold text-white",
                            "border-2 border-white/60",
                            "shadow-lg hover:shadow-xl",
                            direction === 'long' 
                              ? "bg-gradient-to-br from-green-400 via-green-500 to-emerald-600" 
                              : "bg-gradient-to-br from-red-400 via-red-500 to-rose-600"
                          )}
                          style={{
                            width: size,
                            height: size,
                            fontSize: size > 40 ? '10px' : '9px',
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
                            scale: 1.25, 
                            zIndex: 100,
                            boxShadow: direction === 'long' 
                              ? '0 10px 40px -10px rgba(34, 197, 94, 0.5)'
                              : '0 10px 40px -10px rgba(239, 68, 68, 0.5)'
                          }}
                        >
                          {coin.symbol.slice(0, 4)}
                        </motion.div>
                      )
                    })
                  })}
                </AnimatePresence>

                {/* No Signal Message */}
                {filteredCoins.length === 0 && !loading && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="absolute inset-0 flex items-center justify-center"
                  >
                    <div className="text-center bg-white/80 backdrop-blur-sm rounded-2xl p-8 shadow-lg">
                      <div className="h-16 w-16 mx-auto mb-4 rounded-2xl bg-slate-100 flex items-center justify-center">
                        {direction === 'long' ? (
                          <TrendingUp className="h-8 w-8 text-slate-400" />
                        ) : (
                          <TrendingDown className="h-8 w-8 text-slate-400" />
                        )}
                      </div>
                      <p className="text-lg font-semibold text-slate-700">
                        No {direction.toUpperCase()} signals detected
                      </p>
                      <p className="text-sm text-slate-500 mt-1">
                        Try switching to {direction === 'long' ? 'Short' : 'Long'} view
                      </p>
                    </div>
                  </motion.div>
                )}
              </div>
            </div>

            {/* Stats Bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 bg-gradient-to-r from-slate-50 to-slate-100 border-t">
              <div className="flex items-center gap-4">
                {/* Total Coins Stat */}
                <motion.div 
                  className="flex items-center gap-3 bg-white rounded-xl px-4 py-2 shadow-sm"
                  whileHover={{ scale: 1.02 }}
                >
                  <div className="h-8 w-8 rounded-lg bg-violet-100 flex items-center justify-center">
                    <BarChart3 className="h-4 w-4 text-violet-600" />
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide">Total Coins</p>
                    <p className="text-lg font-bold text-slate-800">{data.length}</p>
                  </div>
                </motion.div>

                {/* Signals Stat */}
                <motion.div 
                  className="flex items-center gap-3 bg-white rounded-xl px-4 py-2 shadow-sm"
                  whileHover={{ scale: 1.02 }}
                >
                  <div className={cn(
                    "h-8 w-8 rounded-lg flex items-center justify-center",
                    direction === 'long' ? "bg-green-100" : "bg-red-100"
                  )}>
                    {direction === 'long' ? (
                      <ArrowUpRight className="h-4 w-4 text-green-600" />
                    ) : (
                      <ArrowDownRight className="h-4 w-4 text-red-600" />
                    )}
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide">
                      {direction === 'long' ? 'Long' : 'Short'} Signals
                    </p>
                    <p className={cn(
                      "text-lg font-bold",
                      direction === 'long' ? "text-green-600" : "text-red-600"
                    )}>
                      {filteredCoins.length}
                    </p>
                  </div>
                </motion.div>
              </div>

              {/* Update Status */}
              <motion.div 
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-xl",
                  status === 'ok' && "bg-green-50 text-green-700",
                  status === 'warning' && "bg-amber-50 text-amber-700",
                  status === 'error' && "bg-red-50 text-red-700"
                )}
                key={lastUpdate}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <div className={cn(
                  "h-2 w-2 rounded-full",
                  status === 'ok' && "bg-green-500 animate-pulse",
                  status === 'warning' && "bg-amber-500",
                  status === 'error' && "bg-red-500"
                )} />
                <Clock className="h-4 w-4" />
                <span className="text-sm font-medium">
                  {status === 'ok' && `Updated ${lastUpdate}`}
                  {status === 'warning' && lastUpdate}
                  {status === 'error' && lastUpdate}
                </span>
              </motion.div>
            </div>
          </Card>
        </motion.div>

        {/* Tooltip */}
        <AnimatePresence>
          {hoveredCoin && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 10 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
              className="fixed z-[100] bg-slate-900/95 backdrop-blur-sm text-white rounded-2xl px-5 py-4 shadow-2xl pointer-events-none min-w-[220px]"
              style={{
                left: Math.min(mousePos.x + 15, window.innerWidth - 250),
                top: Math.min(mousePos.y + 15, window.innerHeight - 280),
              }}
            >
              <div className="flex items-center gap-3 mb-3 pb-3 border-b border-slate-700">
                <div className={cn(
                  "h-10 w-10 rounded-xl flex items-center justify-center text-sm font-bold",
                  direction === 'long' 
                    ? "bg-gradient-to-br from-green-400 to-emerald-500" 
                    : "bg-gradient-to-br from-red-400 to-rose-500"
                )}>
                  {hoveredCoin.symbol.slice(0, 2)}
                </div>
                <div>
                  <div className="font-bold text-lg">{hoveredCoin.symbol}</div>
                  <div className="text-slate-400 text-xs">{hoveredCoin.full_name}</div>
                </div>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Signal Layer</span>
                  <Badge variant={hoveredCoin[layerKey] >= 4 ? "success" : "secondary"}>
                    Layer {hoveredCoin[layerKey]}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Price</span>
                  <span className="font-semibold">${formatPrice(hoveredCoin.price)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">24h Change</span>
                  <span className={cn(
                    "font-semibold flex items-center gap-1",
                    hoveredCoin.price_change_24h >= 0 ? "text-green-400" : "text-red-400"
                  )}>
                    {hoveredCoin.price_change_24h >= 0 ? (
                      <ArrowUpRight className="h-3 w-3" />
                    ) : (
                      <ArrowDownRight className="h-3 w-3" />
                    )}
                    {Math.abs(hoveredCoin.price_change_24h).toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">RSI</span>
                  <span className={cn(
                    "font-semibold",
                    hoveredCoin.rsi < 30 ? "text-green-400" : hoveredCoin.rsi > 70 ? "text-red-400" : "text-slate-300"
                  )}>
                    {hoveredCoin.rsi.toFixed(1)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">RSI Smoothed</span>
                  <span className="font-semibold">{hoveredCoin.rsi_smoothed.toFixed(1)}</span>
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
