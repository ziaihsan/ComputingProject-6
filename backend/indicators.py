import numpy as np
import pandas as pd
from typing import List, Dict

def calculate_ema(prices: List[float], period: int) -> List[float]:
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return [np.nan] * len(prices)
    
    df = pd.DataFrame({'close': prices})
    ema = df['close'].ewm(span=period, adjust=False).mean()
    return ema.tolist()

def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """Calculate RSI (Relative Strength Index)"""
    if len(prices) < period + 1:
        return [np.nan] * len(prices)
    
    df = pd.DataFrame({'close': prices})
    delta = df['close'].diff()
    
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.tolist()

def calculate_smoothed_rsi(prices: List[float], rsi_period: int = 14, smooth_period: int = 9) -> List[float]:
    """Calculate Smoothed RSI (RSI with EMA smoothing)"""
    rsi_values = calculate_rsi(prices, rsi_period)
    
    df = pd.DataFrame({'rsi': rsi_values})
    smoothed = df['rsi'].ewm(span=smooth_period, adjust=False).mean()
    
    return smoothed.tolist()

def detect_signal_layer(
    close: float,
    ema_13: float,
    ema_21: float,
    rsi_14: float,
    smoothed_rsi: float
) -> Dict:
    """
    Detect signal layer for Long and Short positions
    
    Layers (strongest to weakest):
    5: Smoothed RSI + EMA (Overbought/Oversold)
    4: RSI Conventional + EMA
    3: Smoothed RSI only
    2: RSI Conventional only
    1: EMA only
    """
    result = {
        'long_layer': 0,
        'short_layer': 0,
        'long_signal': None,
        'short_signal': None
    }
    
    if any(pd.isna([close, ema_13, ema_21, rsi_14, smoothed_rsi])):
        return result
    
    # EMA conditions
    ema_bullish = close > ema_13 > ema_21  # Price above EMAs, EMAs aligned bullish
    ema_bearish = close < ema_13 < ema_21  # Price below EMAs, EMAs aligned bearish
    
    # RSI conditions
    rsi_oversold = rsi_14 < 30
    rsi_overbought = rsi_14 > 70
    rsi_bullish = rsi_14 < 50  # Room to grow
    rsi_bearish = rsi_14 > 50  # Room to fall
    
    # Smoothed RSI conditions
    srsi_oversold = smoothed_rsi < 30
    srsi_overbought = smoothed_rsi > 70
    srsi_bullish = smoothed_rsi < 50
    srsi_bearish = smoothed_rsi > 50
    
    # LONG Signal Detection (from strongest to weakest)
    if srsi_oversold and ema_bullish:
        result['long_layer'] = 5
        result['long_signal'] = 'STRONG_LONG'
    elif rsi_oversold and ema_bullish:
        result['long_layer'] = 4
        result['long_signal'] = 'LONG'
    elif srsi_oversold:
        result['long_layer'] = 3
        result['long_signal'] = 'WEAK_LONG'
    elif rsi_oversold:
        result['long_layer'] = 2
        result['long_signal'] = 'POTENTIAL_LONG'
    elif ema_bullish:
        result['long_layer'] = 1
        result['long_signal'] = 'EMA_LONG'
    
    # SHORT Signal Detection (from strongest to weakest)
    if srsi_overbought and ema_bearish:
        result['short_layer'] = 5
        result['short_signal'] = 'STRONG_SHORT'
    elif rsi_overbought and ema_bearish:
        result['short_layer'] = 4
        result['short_signal'] = 'SHORT'
    elif srsi_overbought:
        result['short_layer'] = 3
        result['short_signal'] = 'WEAK_SHORT'
    elif rsi_overbought:
        result['short_layer'] = 2
        result['short_signal'] = 'POTENTIAL_SHORT'
    elif ema_bearish:
        result['short_layer'] = 1
        result['short_signal'] = 'EMA_SHORT'
    
    return result

def get_rsi_category(rsi: float) -> str:
    """Categorize RSI value"""
    if pd.isna(rsi):
        return 'NEUTRAL'
    if rsi >= 70:
        return 'OVERBOUGHT'
    elif rsi >= 60:
        return 'STRONG'
    elif rsi >= 40:
        return 'NEUTRAL'
    elif rsi >= 30:
        return 'WEAK'
    else:
        return 'OVERSOLD'
