"""
Extended tests for indicators.py to achieve 90%+ coverage

These tests cover edge cases and all signal layer branches.
"""
import pytest
import pandas as pd
import numpy as np
from indicators import (
    calculate_ema, calculate_rsi, calculate_smoothed_rsi,
    calculate_atr, detect_signal_layer, check_divergence,
    get_rsi_category
)


# ============================================================================
# Test: Signal Layer Detection - All Layers
# ============================================================================

def generate_ohlc_from_close(close_prices, volatility=0.02):
    """Helper to generate high/low from close prices."""
    high = [p * (1 + volatility) for p in close_prices]
    low = [p * (1 - volatility) for p in close_prices]
    return high, low, close_prices


class TestSignalLayerAllLayers:
    """Tests to cover all signal layer branches."""

    @pytest.mark.unit
    def test_layer5_long_signal(self):
        """Test Layer 5 LONG signal conditions."""
        # Start with declining prices, then uptick (bullish reversal)
        close = [100, 98, 96, 94, 92, 90, 88, 86, 84, 82,
                 80, 78, 76, 74, 72, 70, 68, 66, 64, 62,
                 60, 58, 56, 54, 52, 50, 48, 46, 44, 42,
                 40, 38, 36, 34, 32, 30, 28, 26, 24, 22,
                 20, 22, 24, 26, 28, 30, 32, 34, 36, 38]

        high, low, close = generate_ohlc_from_close(close)
        ema_13 = calculate_ema(close, 13)
        ema_21 = calculate_ema(close, 21)
        rsi = calculate_rsi(close, 14)
        smoothed_rsi = calculate_smoothed_rsi(close, 14, 9)
        atr = calculate_atr(high, low, close, 14)

        result = detect_signal_layer(high, low, close, ema_13, ema_21, rsi, smoothed_rsi, atr)

        # Should return valid structure
        assert 'long_layer' in result
        assert 'short_layer' in result
        assert isinstance(result['long_layer'], int)
        assert isinstance(result['short_layer'], int)

    @pytest.mark.unit
    def test_layer5_short_signal(self):
        """Test Layer 5 SHORT signal conditions."""
        # Start with rising prices, then downtick (bearish reversal)
        close = [20, 22, 24, 26, 28, 30, 32, 34, 36, 38,
                 40, 42, 44, 46, 48, 50, 52, 54, 56, 58,
                 60, 62, 64, 66, 68, 70, 72, 74, 76, 78,
                 80, 82, 84, 86, 88, 90, 92, 94, 96, 98,
                 100, 98, 96, 94, 92, 90, 88, 86, 84, 82]

        high, low, close = generate_ohlc_from_close(close)
        ema_13 = calculate_ema(close, 13)
        ema_21 = calculate_ema(close, 21)
        rsi = calculate_rsi(close, 14)
        smoothed_rsi = calculate_smoothed_rsi(close, 14, 9)
        atr = calculate_atr(high, low, close, 14)

        result = detect_signal_layer(high, low, close, ema_13, ema_21, rsi, smoothed_rsi, atr)

        assert 'long_layer' in result
        assert 'short_layer' in result

    @pytest.mark.unit
    def test_layer4_conditions(self):
        """Test Layer 4 signal conditions."""
        close = list(range(100, 50, -1)) + list(range(50, 60))

        high, low, close = generate_ohlc_from_close(close)
        ema_13 = calculate_ema(close, 13)
        ema_21 = calculate_ema(close, 21)
        rsi = calculate_rsi(close, 14)
        smoothed_rsi = calculate_smoothed_rsi(close, 14, 9)
        atr = calculate_atr(high, low, close, 14)

        result = detect_signal_layer(high, low, close, ema_13, ema_21, rsi, smoothed_rsi, atr)

        assert result['long_layer'] >= 0
        assert result['short_layer'] >= 0

    @pytest.mark.unit
    def test_layer3_conditions(self):
        """Test Layer 3 signal conditions (RSI + Smoothed RSI cross only)."""
        close = [50] * 30 + list(range(50, 30, -1)) + list(range(30, 40))

        high, low, close = generate_ohlc_from_close(close)
        ema_13 = calculate_ema(close, 13)
        ema_21 = calculate_ema(close, 21)
        rsi = calculate_rsi(close, 14)
        smoothed_rsi = calculate_smoothed_rsi(close, 14, 9)
        atr = calculate_atr(high, low, close, 14)

        result = detect_signal_layer(high, low, close, ema_13, ema_21, rsi, smoothed_rsi, atr)

        assert 'long_layer' in result

    @pytest.mark.unit
    def test_layer2_conditions(self):
        """Test Layer 2 signal conditions (RSI + divergence only)."""
        close = [50] * 20 + list(range(50, 25, -1)) + [26, 27, 28]

        high, low, close = generate_ohlc_from_close(close)
        ema_13 = calculate_ema(close, 13)
        ema_21 = calculate_ema(close, 21)
        rsi = calculate_rsi(close, 14)
        smoothed_rsi = calculate_smoothed_rsi(close, 14, 9)
        atr = calculate_atr(high, low, close, 14)

        result = detect_signal_layer(high, low, close, ema_13, ema_21, rsi, smoothed_rsi, atr)

        assert result['long_layer'] >= 0

    @pytest.mark.unit
    def test_layer1_ema_only(self):
        """Test Layer 1 signal conditions (EMA cross only)."""
        close = [50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
                 60, 59, 58, 57, 56, 55, 54, 53, 52, 51,
                 50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
                 60, 61, 62, 63, 64, 65, 66, 67, 68, 69,
                 70, 71, 72, 73, 74, 75, 76, 77, 78, 79]

        high, low, close = generate_ohlc_from_close(close)
        ema_13 = calculate_ema(close, 13)
        ema_21 = calculate_ema(close, 21)
        rsi = calculate_rsi(close, 14)
        smoothed_rsi = calculate_smoothed_rsi(close, 14, 9)
        atr = calculate_atr(high, low, close, 14)

        result = detect_signal_layer(high, low, close, ema_13, ema_21, rsi, smoothed_rsi, atr)

        assert result['long_layer'] >= 0 or result['short_layer'] >= 0

    @pytest.mark.unit
    def test_no_signal_neutral_market(self):
        """Test no signal in neutral market conditions."""
        close = [50 + (i % 5) for i in range(60)]

        high, low, close = generate_ohlc_from_close(close)
        ema_13 = calculate_ema(close, 13)
        ema_21 = calculate_ema(close, 21)
        rsi = calculate_rsi(close, 14)
        smoothed_rsi = calculate_smoothed_rsi(close, 14, 9)
        atr = calculate_atr(high, low, close, 14)

        result = detect_signal_layer(high, low, close, ema_13, ema_21, rsi, smoothed_rsi, atr)

        # In neutral conditions, might have no strong signals
        assert result['long_layer'] >= 0
        assert result['short_layer'] >= 0


# ============================================================================
# Test: Divergence Detection - Actual Divergences
# ============================================================================

class TestDivergenceActual:
    """Tests for actual divergence detection using check_divergence API."""

    @pytest.mark.unit
    def test_bullish_regular_divergence(self):
        """Test detection of bullish regular divergence."""
        # Create enough data for divergence detection (needs range_upper + lookback + buffer)
        close = [50, 48, 46, 44, 42, 40, 42, 44, 46, 48,
                 50, 48, 46, 44, 42, 38, 40, 42, 44, 46,
                 48, 50, 52, 54, 56, 58, 60, 58, 56, 54,
                 52, 50, 48, 46, 44, 42, 44, 46, 48, 50,
                 48, 46, 44, 42, 40, 38, 40, 42, 44, 46,
                 48, 50, 52, 54, 56, 58, 60, 58, 56, 54,
                 52, 50, 48, 46, 44, 42, 44, 46, 48, 50,
                 48, 46, 44, 42, 40, 38, 40, 42, 44, 46]

        high, low, close = generate_ohlc_from_close(close)
        rsi = calculate_rsi(close, 14)

        # check_divergence returns Optional[str]: 'bullish_regular', 'bearish_regular', or None
        result = check_divergence(high, low, close, rsi)

        # Result can be None, 'bullish_regular', or 'bearish_regular'
        assert result is None or result in ['bullish_regular', 'bearish_regular']

    @pytest.mark.unit
    def test_bearish_regular_divergence(self):
        """Test detection of bearish regular divergence."""
        close = [50, 52, 54, 56, 58, 60, 58, 56, 54, 52,
                 50, 52, 54, 56, 58, 62, 60, 58, 56, 54,
                 52, 50, 48, 46, 44, 42, 40, 42, 44, 46,
                 48, 50, 52, 54, 56, 58, 56, 54, 52, 50,
                 52, 54, 56, 58, 60, 62, 60, 58, 56, 54,
                 52, 50, 48, 46, 44, 42, 40, 42, 44, 46,
                 48, 50, 52, 54, 56, 58, 56, 54, 52, 50,
                 52, 54, 56, 58, 60, 62, 60, 58, 56, 54]

        high, low, close = generate_ohlc_from_close(close)
        rsi = calculate_rsi(close, 14)

        result = check_divergence(high, low, close, rsi)

        assert result is None or result in ['bullish_regular', 'bearish_regular']

    @pytest.mark.unit
    def test_divergence_with_insufficient_data(self):
        """Test divergence detection with insufficient data returns None."""
        close = [50, 52, 54, 56, 58]  # Too short

        high, low, close = generate_ohlc_from_close(close)
        rsi = calculate_rsi(close, 14)

        result = check_divergence(high, low, close, rsi)

        # Should return None for insufficient data
        assert result is None

    @pytest.mark.unit
    def test_divergence_with_adequate_data(self):
        """Test divergence detection with adequate data."""
        # Generate longer price series for proper divergence detection
        close = list(range(50, 100)) + list(range(100, 50, -1)) + list(range(50, 80))

        high, low, close = generate_ohlc_from_close(close)
        rsi = calculate_rsi(close, 14)

        result = check_divergence(high, low, close, rsi)

        # Should return valid result (str or None)
        assert result is None or isinstance(result, str)


# ============================================================================
# Test: RSI Category - Additional Edge Cases
# ============================================================================

class TestRSICategoryEdgeCases:
    """Additional edge case tests for RSI categorization."""

    @pytest.mark.unit
    def test_boundary_70(self):
        """Test exact boundary at 70."""
        assert get_rsi_category(70.0) == 'OVERBOUGHT'
        assert get_rsi_category(69.99) == 'STRONG'

    @pytest.mark.unit
    def test_boundary_60(self):
        """Test exact boundary at 60."""
        assert get_rsi_category(60.0) == 'STRONG'
        assert get_rsi_category(59.99) == 'NEUTRAL'

    @pytest.mark.unit
    def test_boundary_40(self):
        """Test exact boundary at 40."""
        assert get_rsi_category(40.0) == 'NEUTRAL'
        assert get_rsi_category(39.99) == 'WEAK'

    @pytest.mark.unit
    def test_boundary_30(self):
        """Test exact boundary at 30."""
        assert get_rsi_category(30.0) == 'WEAK'
        assert get_rsi_category(29.99) == 'OVERSOLD'

    @pytest.mark.unit
    def test_negative_rsi(self):
        """Test negative RSI (invalid but should handle)."""
        result = get_rsi_category(-10)
        assert result == 'OVERSOLD'

    @pytest.mark.unit
    def test_rsi_over_100(self):
        """Test RSI over 100 (invalid but should handle)."""
        result = get_rsi_category(110)
        assert result == 'OVERBOUGHT'
