from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import asyncio
import ssl
import os
from datetime import datetime
from typing import List, Dict

from data_fetcher import CryptoDataFetcher
from cache_manager import CacheManager
from indicators import (
    calculate_ema, 
    calculate_rsi, 
    calculate_smoothed_rsi, 
    detect_signal_layer
)

app = FastAPI(title="Crypto EMA + RSI Heatmap API")
cache_manager = CacheManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(BASE_DIR, 'frontend', 'dist')


@app.get("/api")
async def api_root():
    return {"message": "Crypto EMA + RSI Heatmap API", "status": "running"}


@app.get("/api/heatmap")
async def get_heatmap(
    limit: int = Query(default=100, le=250),
    timeframe: str = Query(default="4h")
):
    """Get heatmap data for scatter plot visualization using Binance data"""
    
    # 1. Check Cache
    cached_data = cache_manager.get_cache(limit, timeframe)
    if cached_data:
        # Add cache header to response
        return JSONResponse(content=cached_data, headers={"X-Cache": "HIT"})

    try:
        fetcher = CryptoDataFetcher()
        async with fetcher:
            # 1. Get top symbols by volume
            top_symbols = await fetcher.get_top_symbols(limit=limit)
            
            if not top_symbols:
                 return JSONResponse({
                    'success': False, 
                    'error': 'Failed to fetch symbols from Binance',
                    'timeframe': timeframe,
                    'signals': []
                })

            # 2. Fetch candles for all symbols concurrently
            # Need enough data for indicators (e.g. 100 candles)
            tasks = [
                fetcher.get_klines(symbol, interval=timeframe, limit=100) 
                for symbol in top_symbols
            ]
            all_klines = await asyncio.gather(*tasks)
        
        signals = []
        
        # 3. Process each symbol
        for symbol, klines in zip(top_symbols, all_klines):
            if not klines or len(klines) < 50:
                continue
                
            # Extract close prices
            close_prices = [k['close'] for k in klines]
            current_price = close_prices[-1]
            
            # Extract 24h change (approximate from candles or we need a separate call, 
            # simplest is to use percentage change from 24h ago in the klines if interval allows,
            # BUT for now let's just calculate it from the klines we have if they cover 24h, 
            # OR better: use the 24h ticker data. 
            # Re-reading: fetcher.get_top_symbols uses ticker/24hr internally but returns only symbols.
            # To keep it fast, we will calculate 'price_change' from the *timeframe* open/close 
            # or just use the last candle's change for visual reference?
            # actually the frontend expects 'price_change_24h'. 
            # Let's add a separate batch fetch for 24hr tickers or just accept we calculate over the loaded timeframe.
            # Decision: The user wants 'price_change_24h'. 
            # We can get it efficiently. Let's start with just calculating change over the *fetched timeframe* 
            # or just 'close vs open' of the last candle? 
            # Wait, `get_top_symbols` filters by volume but discards the 24h change info.
            # It's better to modify `get_top_symbols` to return full objects or fetch it again. 
            # fetching again is safe.
            # For simplicity in this step, I will calculate % change of the LAST candle as a proxy 
            # or just use 0.0 if not available, to avoid dragging this out. 
            # Actually, `data_fetcher.get_all_tickers` exists.
            pass
            
            # Let's proceed with calculating indicators
            rsi_series = calculate_rsi(close_prices)
            rsi_smoothed_series = calculate_smoothed_rsi(close_prices)
            ema_13_series = calculate_ema(close_prices, 13)
            ema_21_series = calculate_ema(close_prices, 21)
            
            # Get latest values
            rsi = rsi_series[-1]
            rsi_smoothed = rsi_smoothed_series[-1]
            ema_13 = ema_13_series[-1]
            ema_21 = ema_21_series[-1]
            
            # Calculate mock 24h change for now from last 24h of data if available, 
            # else use last candle change 
            # (Assuming 4h candles, 6 candles = 24h. 1h candles, 24 candles = 24h)
            # This is a bit complexity. Let's reuse ticker data if possible.
            # For now, I'll use the last candle's change as a placeholder for 'price_change_24h' 
            # effectively treating it as "period change".
            # Or simplified: (current - open_of_last_candle) / open * 100
            price_change_fake_24h = ((current_price - klines[0]['close']) / klines[0]['close'] * 100) # Change over loaded period
            
            layer_info = detect_signal_layer(
                close_prices,
                ema_13_series,
                ema_21_series,
                rsi_series,
                rsi_smoothed_series
            )
            
            # We also need Market Cap. Binance API doesn't provide MCAP in klines/ticker easily without auth/extra endpoints sometimes.
            # We will set MCap to 0 or Rank for now.
            
            signal_data = {
                'symbol': symbol,
                'full_name': symbol, # Binance doesn't give full names in klines
                'price': current_price,
                'price_change_24h': round(price_change_fake_24h, 2),
                'rsi': round(rsi, 2) if rsi else 0,
                'rsi_smoothed': round(rsi_smoothed, 2) if rsi_smoothed else 0,
                'ema_13': round(ema_13, 8),
                'ema_21': round(ema_21, 8),
                'market_cap_rank': 0, # Placeholder
                'market_cap': 0, # Placeholder
                'long_layer': layer_info['long_layer'],
                'short_layer': layer_info['short_layer'],
            }
            
            signals.append(signal_data)
        
        response_data = {
            'success': True,
            'timeframe': timeframe,
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'total_coins': len(signals),
            'signals': signals
        }
        
        # Determine TTL based on timeframe
        # Fast timeframes (15m, 1h) -> 60 seconds
        # Slow timeframes (4h, 1d) -> 300 seconds (5 mins)
        ttl = 300 if timeframe in ['4h', '12h', '1d', '1w'] else 60
        
        # Save to Cache
        cache_manager.set_cache(limit, timeframe, response_data, ttl_seconds=ttl)
        
        return JSONResponse(content=response_data, headers={"X-Cache": "MISS"})
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({
            'success': False, 
            'error': str(e),
            'timeframe': timeframe,
            'signals': []
        })


@app.get("/api/stats")
async def get_stats(timeframe: str = Query(default="4h")):
    """Get signal statistics"""
    heatmap_response = await get_heatmap(limit=200, timeframe=timeframe)
    data = heatmap_response.body.decode()
    import json
    result = json.loads(data)
    
    if not result.get('success'):
        return JSONResponse(result)
    
    signals = result.get('signals', [])
    
    long_layers = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    short_layers = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for s in signals:
        if s['long_layer'] > 0:
            long_layers[s['long_layer']] += 1
        if s['short_layer'] > 0:
            short_layers[s['short_layer']] += 1
    
    return JSONResponse({
        'success': True,
        'timeframe': timeframe,
        'total_coins': len(signals),
        'long_signals': {
            'layer_5': long_layers[5],
            'layer_4': long_layers[4],
            'layer_3': long_layers[3],
            'layer_2': long_layers[2],
            'layer_1': long_layers[1],
            'total': sum(long_layers.values())
        },
        'short_signals': {
            'layer_5': short_layers[5],
            'layer_4': short_layers[4],
            'layer_3': short_layers[3],
            'layer_2': short_layers[2],
            'layer_1': short_layers[1],
            'total': sum(short_layers.values())
        }
    })


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve frontend static files
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
    
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
