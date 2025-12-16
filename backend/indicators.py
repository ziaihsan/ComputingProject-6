import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional

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

def find_peaks_troughs(series: pd.Series, order: int = 3) -> Tuple[List[int], List[int]]:
    """Find indices of peaks and troughs"""
    peaks = []
    troughs = []
    
    # Simple check for local extrema
    for i in range(order, len(series) - order):
        current = series.iloc[i]
        if pd.isna(current):
            continue
            
        # Check for Peak
        is_peak = True
        for j in range(1, order + 1):
            if series.iloc[i-j] > current or series.iloc[i+j] > current:
                is_peak = False
                break
        if is_peak:
            peaks.append(i)
            
        # Check for Trough
        is_trough = True
        for j in range(1, order + 1):
            if series.iloc[i-j] < current or series.iloc[i+j] < current:
                is_trough = False
                break
        if is_trough:
            troughs.append(i)
            
    return peaks, troughs

def detect_divergence(
    prices: List[float], 
    rsi_values: List[float], 
    lookback: int = 30
) -> Dict[str, bool]:
    """
    Detect Regular and Hidden Bullish/Bearish Divergences
    Returns: {
        'bullish_regular': bool,
        'bullish_hidden': bool,
        'bearish_regular': bool,
        'bearish_hidden': bool
    }
    """
    result = {
        'bullish_regular': False,
        'bullish_hidden': False, # Continuation
        'bearish_regular': False,
        'bearish_hidden': False  # Continuation
    }
    
    if len(prices) < lookback:
        return result
        
    price_s = pd.Series(prices[-lookback:])
    rsi_s = pd.Series(rsi_values[-lookback:])
    
    # Re-index to be regular 0..len-1 for easier comparison
    price_s = price_s.reset_index(drop=True)
    rsi_s = rsi_s.reset_index(drop=True)
    
    peaks, troughs = find_peaks_troughs(rsi_s, order=2)
    
    # Need at least 2 troughs for bullish divergence
    if len(troughs) >= 2:
        last_t_idx = troughs[-1]
        prev_t_idx = troughs[-2]
        
        # Ensure the last trough is recent (within last 5 candles)
        if last_t_idx >= len(rsi_s) - 5:
            # Price at troughs
            p_last = price_s.iloc[last_t_idx]
            p_prev = price_s.iloc[prev_t_idx]
            
            # RSI at troughs
            r_last = rsi_s.iloc[last_t_idx]
            r_prev = rsi_s.iloc[prev_t_idx]
            
            # Regular Bullish: Price Lower Low, RSI Higher Low
            if p_last < p_prev and r_last > r_prev:
                result['bullish_regular'] = True
                
            # Hidden Bullish: Price Higher Low, RSI Lower Low
            if p_last > p_prev and r_last < r_prev:
                result['bullish_hidden'] = True

    # Need at least 2 peaks for bearish divergence
    if len(peaks) >= 2:
        last_p_idx = peaks[-1]
        prev_p_idx = peaks[-2]
        
        # Ensure the last peak is recent
        if last_p_idx >= len(rsi_s) - 5:
            p_last = price_s.iloc[last_p_idx]
            p_prev = price_s.iloc[prev_p_idx]
            
            r_last = rsi_s.iloc[last_p_idx]
            r_prev = rsi_s.iloc[prev_p_idx]
            
            # Regular Bearish: Price Higher High, RSI Lower High
            if p_last > p_prev and r_last < r_prev:
                result['bearish_regular'] = True
                
            # Hidden Bearish: Price Lower High, RSI Higher High
            if p_last < p_prev and r_last > r_prev:
                result['bearish_hidden'] = True
                
    return result

def check_ema_cross_retest(
    prices: List[float], 
    ema13: List[float], 
    ema21: List[float],
    lookback: int = 10
) -> Dict[str, bool]:
    """
    Detect Cross + Retest conditions
    Long: EMA13 crossed up EMA21 recently, price touched EMA13
    Short: EMA13 crossed down EMA21 recently, price touched EMA13
    """
    res = {'long_setup': False, 'short_setup': False}
    
    if len(prices) < lookback:
        return res
        
    # Analyze recent history
    p_recent = prices[-lookback:]
    e13_recent = ema13[-lookback:]
    e21_recent = ema21[-lookback:]
    
    # Check for Cross Up
    cross_up_idx = -1
    for i in range(1, lookback):
        # Crossed up: yesterday 13 < 21, today 13 > 21
        if e13_recent[i-1] < e21_recent[i-1] and e13_recent[i] > e21_recent[i]:
            cross_up_idx = i
            break
            
    # Check for Cross Down
    cross_down_idx = -1
    for i in range(1, lookback):
        if e13_recent[i-1] > e21_recent[i-1] and e13_recent[i] < e21_recent[i]:
            cross_down_idx = i
            break
            
    # Long Logic: Cross Up happened, and Price "touched" or tested EMA13 since then
    if cross_up_idx != -1:
        # Check if price tested EMA13 after cross
        # Simple test: Price Low <= EMA13 * 1.001 (allowing small margin)
        # Note: We only have close prices here usually, strictly 'Hit ke EMA 13' implies Low/High.
        # Assuming 'prices' is 'close', we check if Close comes near EMA13.
        # BETTER: Ideally we need High/Low for retest. For now using Close near EMA13.
        for i in range(cross_up_idx, lookback):
            if abs(p_recent[i] - e13_recent[i]) / p_recent[i] < 0.005: # 0.5% margin for retest
                res['long_setup'] = True
                break
                
    # Short Logic
    if cross_down_idx != -1:
        for i in range(cross_down_idx, lookback):
            if abs(p_recent[i] - e13_recent[i]) / p_recent[i] < 0.005:
                res['short_setup'] = True
                break
                
    return res

def detect_signal_layer(
    prices: List[float],
    ema_13: List[float],
    ema_21: List[float],
    rsi_14: List[float],
    smoothed_rsi: List[float]
) -> Dict:
    """
    Detect signal layer based on 5 user-defined rules
    Requires full data series lists
    """
    result = {
        'long_layer': 0,
        'short_layer': 0,
        'long_signal': None,
        'short_signal': None
    }
    
    if len(prices) < 30:
        return result
        
    # Current Values
    curr_price = prices[-1]
    curr_rsi = rsi_14[-1]
    curr_srsi = smoothed_rsi[-1]
    curr_ema13 = ema_13[-1]
    curr_ema21 = ema_21[-1]
    
    prev_rsi = rsi_14[-2]
    prev_srsi = smoothed_rsi[-2]
    
    # 1. EMA Analysis
    ema_conditions = check_ema_cross_retest(prices, ema_13, ema_21)
    ema_bullish_cross_retest = ema_conditions['long_setup']
    ema_bearish_cross_retest = ema_conditions['short_setup']
    
    # 2. Divergence Analysis
    divs = detect_divergence(prices, rsi_14)
    has_bullish_div = divs['bullish_regular'] or divs['bullish_hidden']
    has_bearish_div = divs['bearish_regular'] or divs['bearish_hidden']
    
    # 3. Cross Logic
    # RSI vs Smoothed RSI
    rsi_cross_up_srsi = prev_rsi < prev_srsi and curr_rsi > curr_srsi
    rsi_cross_down_srsi = prev_rsi > prev_srsi and curr_rsi < curr_srsi
    
    # EMA Cross (Raw check for instant cross)
    prev_ema13 = ema_13[-2]
    prev_ema21 = ema_21[-2]
    ema_cross_up = prev_ema13 < prev_ema21 and curr_ema13 > curr_ema21
    ema_cross_down = prev_ema13 > prev_ema21 and curr_ema13 < curr_ema21

    # --- RULES IMPLEMENTATION ---
    
    # LAYER 5: EMA + RSI Smoothed
    # Long: EMA13 cross up EMA21 & RSI < 30 & Cross Smoothed RSI & Bullish Div
    # (Note: "EMA13 cross up EMA21" usually implies recent cross, combined with current RSI conditions)
    # We allow "Recent Cross" for EMA condition to be more practical than "Exact same candle"
    l5_long = (ema_bullish_cross_retest or ema_cross_up) and curr_rsi < 30 and rsi_cross_up_srsi and has_bullish_div
    l5_short = (ema_bearish_cross_retest or ema_cross_down) and curr_rsi > 70 and rsi_cross_down_srsi and has_bearish_div # User said RSI < 30 for short, assuming > 70
    
    if l5_long:
        result['long_layer'] = 5
        result['long_signal'] = 'STRONG_LONG (L5)'
    if l5_short:
        result['short_layer'] = 5
        result['short_signal'] = 'STRONG_SHORT (L5)'
        
    # LAYER 4: EMA + RSI Conventional
    # Long: EMA Cross Up & RSI < 30 & Bullish Div
    if result['long_layer'] == 0:
        l4_long = (ema_bullish_cross_retest or ema_cross_up) and curr_rsi < 30 and has_bullish_div
        if l4_long:
            result['long_layer'] = 4
            result['long_signal'] = 'LONG (L4)'
            
    if result['short_layer'] == 0:
        l4_short = (ema_bearish_cross_retest or ema_cross_down) and curr_rsi > 70 and has_bearish_div
        if l4_short:
            result['short_layer'] = 4
            result['short_signal'] = 'SHORT (L4)'

    # LAYER 3: Only RSI Smoothed
    # Long: RSI < 30 + Cross Smoothed RSI
    if result['long_layer'] == 0:
        l3_long = curr_rsi < 30 and rsi_cross_up_srsi
        if l3_long:
            result['long_layer'] = 3
            result['long_signal'] = 'WEAK_LONG (L3)'
            
    if result['short_layer'] == 0:
        l3_short = curr_rsi > 70 and rsi_cross_down_srsi
        if l3_short:
            result['short_layer'] = 3
            result['short_signal'] = 'WEAK_SHORT (L3)'

    # LAYER 2: Only RSI Standard
    # Long: RSI < 30 + Bullish Div
    if result['long_layer'] == 0:
        l2_long = curr_rsi < 30 and has_bullish_div
        if l2_long:
            result['long_layer'] = 2
            result['long_signal'] = 'POTENTIAL_LONG (L2)'
            
    if result['short_layer'] == 0:
        l2_short = curr_rsi > 70 and has_bearish_div
        if l2_short:
            result['short_layer'] = 2
            result['short_signal'] = 'POTENTIAL_SHORT (L2)'

    # LAYER 1: Only EMA
    # Long: Cross Up + Retest
    if result['long_layer'] == 0:
        if ema_bullish_cross_retest:
            result['long_layer'] = 1
            result['long_signal'] = 'EMA_LONG (L1)'
            
    if result['short_layer'] == 0:
        if ema_bearish_cross_retest:
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
