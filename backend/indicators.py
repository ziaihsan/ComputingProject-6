import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union

def calculate_ema(prices: List[float], period: int) -> List[float]:
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return [np.nan] * len(prices)
    
    df = pd.DataFrame({'close': prices})
    ema = df['close'].ewm(span=period, adjust=False).mean()
    return ema.tolist()

def calculate_rma(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate RMA (Relative Moving Average) / Wilder's Smoothing / SMMA
    """
    alpha = 1.0 / period
    return series.ewm(alpha=alpha, adjust=False).mean()

def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """
    Calculate RSI (Relative Strength Index) using Wilder's Smoothing (RMA)
    """
    if len(prices) < period + 1:
        return [np.nan] * len(prices)

    df = pd.DataFrame({'close': prices})
    change = df['close'].diff()
    gain = change.where(change > 0, 0.0)
    loss = (-change).where(change < 0, 0.0)

    avg_gain = calculate_rma(gain, period)
    avg_loss = calculate_rma(loss, period)

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    rsi = rsi.where(avg_loss != 0, 100.0)
    rsi = rsi.where(avg_gain != 0, rsi)
    rsi = rsi.where((avg_gain != 0) | (avg_loss != 0), 50.0)
    rsi.iloc[:period] = np.nan

    return rsi.tolist()

def calculate_smoothed_rsi(prices: List[float], rsi_period: int = 14, smooth_period: int = 9) -> List[float]:
    """
    Calculate Smoothed RSI (RSI with EMA smoothing)
    """
    rsi_values = calculate_rsi(prices, rsi_period)
    df = pd.DataFrame({'rsi': rsi_values})
    smoothed = df['rsi'].ewm(span=smooth_period, adjust=False).mean()
    return smoothed.tolist()

def calculate_atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
    """Calculate ATR (Average True Range) using RMA"""
    if len(close) < period:
        return [np.nan] * len(close)
    
    df = pd.DataFrame({'high': high, 'low': low, 'close': close})
    df['prev_close'] = df['close'].shift(1)
    
    # TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
    df['tr0'] = df['high'] - df['low']
    df['tr1'] = (df['high'] - df['prev_close']).abs()
    df['tr2'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    
    # ATR = RMA(TR)
    atr = calculate_rma(df['tr'], period)
    return atr.tolist()

def check_divergence(
    high: List[float],
    low: List[float],
    close: List[float],
    rsi: List[float],
    lookback_left: int = 5,
    lookback_right: int = 5,
    range_lower: int = 5,
    range_upper: int = 60
) -> Optional[str]:
    """
    Checks for Regular Bullish/Bearish Divergence based on Pivot logic.
    Implements logic from newCompro/src/indicators.py.
    """
    # Create DF-like structure for easy indexing (simulating what newCompro does)
    # We assume inputs are lists/arrays of same length
    length = len(close)
    if length < range_upper + lookback_left + lookback_right + 5:
        return None
    
    # Pivot logic looks at `pivot_idx` which is `lookback_right` candles ago from the END.
    # We are checking if the pivot is confirmed NOW (at the end of the series).
    pivot_idx = length - 1 - lookback_right
    
    if pivot_idx < range_upper:
        return None

    # Helper functions (using list indexing)
    def is_pivot_low(arr, i, left, right):
        val = arr[i]
        # Check left
        for k in range(1, left + 1):
            if i - k < 0: return False
            if arr[i - k] <= val: return False
        # Check right
        for k in range(1, right + 1):
            if i + k >= len(arr): return False
            if arr[i + k] <= val: return False
        return True

    def is_pivot_high(arr, i, left, right):
        val = arr[i]
        # Check left
        for k in range(1, left + 1):
            if i - k < 0: return False
            if arr[i - k] >= val: return False
        # Check right
        for k in range(1, right + 1):
            if i + k >= len(arr): return False
            if arr[i + k] >= val: return False
        return True

    # --- CHECK BULLISH DIVERGENCE (Pivot Low) ---
    if is_pivot_low(rsi, pivot_idx, lookback_left, lookback_right):
        current_pivot_rsi = rsi[pivot_idx]
        current_pivot_low_price = low[pivot_idx]
        
        # Search for previous pivot
        for k in range(range_lower, range_upper + 1):
            prev_idx = pivot_idx - k
            if prev_idx < lookback_left:
                break
                
            if is_pivot_low(rsi, prev_idx, lookback_left, lookback_right):
                prev_pivot_rsi = rsi[prev_idx]
                prev_pivot_low_price = low[prev_idx]
                
                # Regular Bullish: Price Lower Low, RSI Higher Low
                if current_pivot_low_price < prev_pivot_low_price and current_pivot_rsi > prev_pivot_rsi:
                    return 'bullish_regular'
                break

    # --- CHECK BEARISH DIVERGENCE (Pivot High) ---
    if is_pivot_high(rsi, pivot_idx, lookback_left, lookback_right):
        current_pivot_rsi = rsi[pivot_idx]
        current_pivot_high_price = high[pivot_idx]
        
        for k in range(range_lower, range_upper + 1):
            prev_idx = pivot_idx - k
            if prev_idx < lookback_left:
                break
            
            if is_pivot_high(rsi, prev_idx, lookback_left, lookback_right):
                prev_pivot_rsi = rsi[prev_idx]
                prev_pivot_high_price = high[prev_idx]
                
                # Regular Bearish: Price Higher High, RSI Lower High
                if current_pivot_high_price > prev_pivot_high_price and current_pivot_rsi < prev_pivot_rsi:
                    return 'bearish_regular'
                break
                
    return None

def detect_signal_layer(
    high: List[float],
    low: List[float],
    close: List[float],
    ema_13: List[float],
    ema_21: List[float],
    rsi_14: List[float],
    smoothed_rsi: List[float],
    atr: List[float]
) -> Dict:
    """
    Detect signal layer based on 5 user-defined rules from newCompro.
    Evaluates on Confirmed Closed Candle (Index -2).
    """
    result = {
        'long_layer': 0,
        'short_layer': 0,
        'long_signal': None,
        'short_signal': None
    }
    
    if len(close) < 50:
        return result
        
    # Index -2 (Confirmed Closed Candle)
    idx = -2
    
    # --- Data at Closed Candle ---
    c_price = close[idx]
    c_ema13 = ema_13[idx]
    c_ema21 = ema_21[idx]
    c_atr = atr[idx]
    c_rsi = rsi_14[idx]
    c_srsi = smoothed_rsi[idx]
    
    # --- Rule 1: EMA Pullback / Touch ---
    # Tolerance: ATR * 0.3
    offset = c_atr * 0.3
    
    is_touch_13 = abs(c_price - c_ema13) <= offset
    is_touch_21 = abs(c_price - c_ema21) <= offset
    is_pullback = is_touch_13 and is_touch_21
    
    # Trend Check
    long_trend = c_ema13 > c_ema21
    short_trend = c_ema13 < c_ema21
    
    # Spread Filter: |EMA13 - EMA21| >= 0.15 * ATR
    ema_spread = abs(c_ema13 - c_ema21)
    min_spread = 0.15 * c_atr
    
    if ema_spread < min_spread:
        long_trend = False
        short_trend = False
        
    s1_long = long_trend and is_pullback
    s1_short = short_trend and is_pullback
    
    # --- Divergence Check ---
    # Check divergence on the closed series (excluding active candle at -1)
    # We pass the lists sliced up to -1
    div_status = check_divergence(
        high[:-1], low[:-1], close[:-1], rsi_14[:-1]
    )
    
    has_bullish_div = div_status == 'bullish_regular'
    has_bearish_div = div_status == 'bearish_regular'
    
    # --- Cross Logic for RSI/Smoothed RSI ---
    # Check cross at idx (Closed)
    # prev is idx-1
    prev_rsi = rsi_14[idx-1]
    prev_srsi = smoothed_rsi[idx-1]
    
    rsi_cross_up = prev_rsi <= prev_srsi and c_rsi > c_srsi
    rsi_cross_down = prev_rsi >= prev_srsi and c_rsi < c_srsi
    
    # --- Rule 2: RSI Standard ---
    # RSI < 40 (Long) / > 60 (Short) AND Divergence
    s2_long = (c_rsi < 40) and has_bullish_div
    s2_short = (c_rsi > 60) and has_bearish_div
    
    # --- Rule 3: RSI Smoothed ---
    # RSI Cross Smoothed RSI + Divergence
    # Filter: Smoothed RSI < 40 (Long) / > 60 (Short)
    s3_long = (c_srsi < 40) and rsi_cross_up and has_bullish_div
    s3_short = (c_srsi > 60) and rsi_cross_down and has_bearish_div
    
    # --- Rule 4: EMA + RSI Conventional ---
    # Rule 1 AND Rule 2
    s4_long = s1_long and s2_long
    s4_short = s1_short and s2_short
    
    # --- Rule 5: EMA + RSI Smoothed ---
    # Rule 1 AND Rule 3
    s5_long = s1_long and s3_long
    s5_short = s1_short and s3_short
    
    # --- Map to Layers ---
    # Layer 5: Rule 5 (Strongest)
    if s5_long:
        result['long_layer'] = 5
        result['long_signal'] = 'STRONG_LONG (L5)'
    elif s4_long:
        result['long_layer'] = 4
        result['long_signal'] = 'LONG (L4)'
    elif s3_long:
        result['long_layer'] = 3
        result['long_signal'] = 'WEAK_LONG (L3)'
    elif s2_long:
        result['long_layer'] = 2
        result['long_signal'] = 'POTENTIAL_LONG (L2)'
    elif s1_long:
        result['long_layer'] = 1
        result['long_signal'] = 'EMA_LONG (L1)'
        
    if s5_short:
        result['short_layer'] = 5
        result['short_signal'] = 'STRONG_SHORT (L5)'
    elif s4_short:
        result['short_layer'] = 4
        result['short_signal'] = 'SHORT (L4)'
    elif s3_short:
        result['short_layer'] = 3
        result['short_signal'] = 'WEAK_SHORT (L3)'
    elif s2_short:
        result['short_layer'] = 2
        result['short_signal'] = 'POTENTIAL_SHORT (L2)'
    elif s1_short:
        result['short_layer'] = 1
        result['short_signal'] = 'EMA_SHORT (L1)'
        
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