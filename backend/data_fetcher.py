import aiohttp
import asyncio
import ssl
import certifi
from typing import List, Dict, Optional
import time

class CryptoDataFetcher:
    """Fetch crypto data from Binance API"""
    
    BINANCE_API = "https://data-api.binance.vision/api/v3"
    
    INTERVALS = {
        '5m': '5m',
        '15m': '15m', 
        '1h': '1h',
        '4h': '4h',
        '12h': '12h',
        '1d': '1d',
        '1w': '1w'
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        return self
        
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def get_top_symbols(self, limit: int = 100) -> List[str]:
        """Get top trading pairs by volume that are actively TRADING"""
        # 1. Get valid trading symbols
        info_url = f"{self.BINANCE_API}/exchangeInfo"
        valid_symbols = set()
        
        try:
            async with self.session.get(info_url) as response:
                if response.status == 200:
                    data = await response.json()
                    for s in data['symbols']:
                        if s['status'] == 'TRADING' and s['symbol'].endswith('USDT'):
                            valid_symbols.add(s['symbol'])
        except Exception as e:
            print(f"Error fetching exchange info: {e}")
            # Fallback to loose filtering if exchange info fails
            pass
            
        # 2. Get ticker data
        url = f"{self.BINANCE_API}/ticker/24hr"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                return []
            
            data = await response.json()
            
            # Filter USDT pairs and sort by volume
            usdt_pairs = []
            for d in data:
                sym = d['symbol']
                # Check strict filter if available, else just USDT check
                if valid_symbols and sym not in valid_symbols:
                    continue
                    
                if sym.endswith('USDT') and not sym.startswith('USDC') and float(d['quoteVolume']) > 0:
                    usdt_pairs.append(d)
            
            sorted_pairs = sorted(
                usdt_pairs, 
                key=lambda x: float(x['quoteVolume']), 
                reverse=True
            )
            
            return [p['symbol'] for p in sorted_pairs[:limit]]
    
    async def get_klines(
        self, 
        symbol: str, 
        interval: str = '4h', 
        limit: int = 100
    ) -> List[Dict]:
        """Get OHLCV data for a symbol"""
        url = f"{self.BINANCE_API}/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                
                return [{
                    'timestamp': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                } for k in data]
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return []
    
    async def get_ticker_24h(self, symbol: str) -> Optional[Dict]:
        """Get 24h ticker data"""
        url = f"{self.BINANCE_API}/ticker/24hr"
        params = {'symbol': symbol}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                return await response.json()
        except:
            return None
    
    async def get_all_tickers(self) -> List[Dict]:
        """Get all ticker prices"""
        url = f"{self.BINANCE_API}/ticker/24hr"
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return []
                return await response.json()
        except:
            return []

    async def fetch_multi_timeframe_data(
        self, 
        symbol: str,
        timeframes: List[str] = ['15m', '1h', '4h', '12h', '1d']
    ) -> Dict:
        """Fetch data for multiple timeframes"""
        tasks = [
            self.get_klines(symbol, tf, limit=100) 
            for tf in timeframes
        ]
        results = await asyncio.gather(*tasks)
        
        return {
            tf: data 
            for tf, data in zip(timeframes, results)
        }
