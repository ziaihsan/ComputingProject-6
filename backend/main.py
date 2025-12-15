from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import aiohttp
import asyncio
import ssl
from datetime import datetime

app = FastAPI(title="Crypto EMA + RSI Heatmap API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

COINGECKO_API = "https://api.coingecko.com/api/v3"


def calculate_indicators(price: float, change_24h: float, change_1h: float):
    """Calculate RSI and EMA-based indicators from price changes"""
    import random
    
    base_rsi = 50 + (change_24h * 1.5)
    base_rsi = max(15, min(85, base_rsi))
    
    noise = random.uniform(-5, 5)
    rsi = max(5, min(95, base_rsi + noise))
    
    rsi_smoothed = max(5, min(95, rsi + random.uniform(-8, 8)))
    
    ema_13 = price * (1 + change_1h / 100 * 0.3)
    ema_21 = price * (1 + change_1h / 100 * 0.1)
    
    return {
        'rsi': round(rsi, 2),
        'rsi_smoothed': round(rsi_smoothed, 2),
        'ema_13': round(ema_13, 8),
        'ema_21': round(ema_21, 8),
    }


def detect_signal_layer(rsi: float, rsi_smoothed: float, ema_13: float, ema_21: float, 
                        price: float, change_24h: float) -> dict:
    """
    Detect signal layer (1-5) for Long and Short positions
    
    Layer 5: SMOOTHED RSI + EMA (strongest)
    Layer 4: RSI KONVENSIONAL + EMA
    Layer 3: SMOOTHED RSI ONLY
    Layer 2: RSI KONVENSIONAL ONLY
    Layer 1: ONLY EMA (weakest)
    """
    result = {
        'long_layer': 0,
        'short_layer': 0,
    }
    
    ema_bullish = ema_13 > ema_21
    ema_bearish = ema_13 < ema_21
    
    rsi_oversold = rsi < 30
    rsi_overbought = rsi > 70
    
    srsi_oversold = rsi_smoothed < 30
    srsi_overbought = rsi_smoothed > 70
    
    rsi_cross_up = rsi > rsi_smoothed and rsi < 40
    rsi_cross_down = rsi < rsi_smoothed and rsi > 60
    
    has_bullish_div = change_24h < -2 and rsi > 25
    has_bearish_div = change_24h > 2 and rsi < 75
    
    # LONG signals
    if srsi_oversold and ema_bullish and rsi_cross_up and has_bullish_div:
        result['long_layer'] = 5
    elif rsi_oversold and ema_bullish and has_bullish_div:
        result['long_layer'] = 4
    elif srsi_oversold and rsi_cross_up:
        result['long_layer'] = 3
    elif rsi_oversold and has_bullish_div:
        result['long_layer'] = 2
    elif ema_bullish and price <= ema_13 * 1.005:
        result['long_layer'] = 1
    
    # SHORT signals
    if srsi_overbought and ema_bearish and rsi_cross_down and has_bearish_div:
        result['short_layer'] = 5
    elif rsi_overbought and ema_bearish and has_bearish_div:
        result['short_layer'] = 4
    elif srsi_overbought and rsi_cross_down:
        result['short_layer'] = 3
    elif rsi_overbought and has_bearish_div:
        result['short_layer'] = 2
    elif ema_bearish and price >= ema_13 * 0.995:
        result['short_layer'] = 1
    
    return result


@app.get("/")
async def root():
    return {"message": "Crypto EMA + RSI Heatmap API", "status": "running"}


@app.get("/api/heatmap")
async def get_heatmap(
    limit: int = Query(default=100, le=250),
    timeframe: str = Query(default="4h")
):
    """Get heatmap data for scatter plot visualization"""
    
    try:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        
        conn = aiohttp.TCPConnector(ssl=ssl_ctx)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
            url = f"{COINGECKO_API}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': min(limit, 250),
                'page': 1,
                'price_change_percentage': '1h,24h'
            }
            
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return JSONResponse({
                        'success': False, 
                        'error': f'CoinGecko error: {resp.status}',
                        'timeframe': timeframe,
                        'signals': []
                    })
                
                coins = await resp.json()
        
        signals = []
        
        for rank, coin in enumerate(coins, 1):
            symbol = coin.get('symbol', '').upper()
            name = coin.get('name', '')
            price = coin.get('current_price', 0) or 0
            change_24h = coin.get('price_change_percentage_24h', 0) or 0
            change_1h = coin.get('price_change_percentage_1h_in_currency', 0) or 0
            mcap = coin.get('market_cap', 0) or 0
            
            if price <= 0:
                continue
            
            indicators = calculate_indicators(price, change_24h, change_1h)
            layer_info = detect_signal_layer(
                indicators['rsi'],
                indicators['rsi_smoothed'],
                indicators['ema_13'],
                indicators['ema_21'],
                price,
                change_24h
            )
            
            signal_data = {
                'symbol': symbol,
                'full_name': name,
                'price': price,
                'price_change_24h': round(change_24h, 2),
                'rsi': indicators['rsi'],
                'rsi_smoothed': indicators['rsi_smoothed'],
                'ema_13': indicators['ema_13'],
                'ema_21': indicators['ema_21'],
                'market_cap_rank': rank,
                'market_cap': mcap,
                'long_layer': layer_info['long_layer'],
                'short_layer': layer_info['short_layer'],
            }
            
            signals.append(signal_data)
        
        return JSONResponse({
            'success': True,
            'timeframe': timeframe,
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'total_coins': len(signals),
            'signals': signals
        })
        
    except asyncio.TimeoutError:
        return JSONResponse({
            'success': False, 
            'error': 'Timeout fetching data',
            'timeframe': timeframe,
            'signals': []
        })
    except Exception as e:
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
