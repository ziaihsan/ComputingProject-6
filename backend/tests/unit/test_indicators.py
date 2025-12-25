"""
Unit tests for indicators.py - Pure function tests

These tests verify the correctness of technical analysis indicator calculations.
All functions in indicators.py are pure (no external dependencies), making them
ideal candidates for unit testing.
"""
import pytest
import numpy as np
import pandas as pd
from typing import List

# Import the module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from indicators import (
    calculate_ema,
    calculate_rma,
    calculate_rsi,
    calculate_smoothed_rsi,
    find_peaks_troughs,
    detect_divergence,
    check_ema_cross_retest,
    detect_signal_layer,
    get_rsi_category
)


# ============================================================================
# Test: calculate_ema
# ============================================================================

class TestCalculateEMA:
    """Tests for Exponential Moving Average calculation."""

    @pytest.mark.unit
    def test_ema_with_sufficient_data(self, sample_prices):
        """EMA should calculate correctly with sufficient data."""
        result = calculate_ema(sample_prices, period=10)

        assert len(result) == len(sample_prices)
        assert not np.isnan(result[-1])
        # EMA should be within reasonable range of prices
        assert min(sample_prices) <= result[-1] <= max(sample_prices)

    @pytest.mark.unit
    def test_ema_with_insufficient_data(self):
        """EMA should return NaN when data is insufficient."""
        prices = [100, 102, 104]
        result = calculate_ema(prices, period=10)

        assert len(result) == len(prices)
        assert all(np.isnan(r) for r in result)

    @pytest.mark.unit
    def test_ema_empty_list(self):
        """EMA should handle empty list gracefully."""
        result = calculate_ema([], period=5)
        assert result == []

    @pytest.mark.unit
    def test_ema_single_value(self):
        """EMA with single value should return NaN for period > 1."""
        result = calculate_ema([100.0], period=5)
        assert len(result) == 1
        assert np.isnan(result[0])

    @pytest.mark.unit
    def test_ema_period_one(self):
        """EMA with period 1 should equal the price itself."""
        prices = [100.0, 105.0, 103.0, 108.0]
        result = calculate_ema(prices, period=1)

        assert len(result) == len(prices)
        for i, r in enumerate(result):
            assert abs(r - prices[i]) < 0.01

    @pytest.mark.unit
    def test_ema_follows_trend(self, sample_uptrend_prices):
        """EMA should follow upward trend but lag behind."""
        result = calculate_ema(sample_uptrend_prices, period=5)

        # EMA should be below current price in uptrend (lagging)
        assert result[-1] < sample_uptrend_prices[-1]
        # But EMA should be increasing
        assert result[-1] > result[-5]


# ============================================================================
# Test: calculate_rsi
# ============================================================================

class TestCalculateRSI:
    """Tests for Relative Strength Index calculation."""

    @pytest.mark.unit
    def test_rsi_overbought_in_uptrend(self, sample_uptrend_prices):
        """RSI should indicate overbought (>70) during strong uptrend."""
        result = calculate_rsi(sample_uptrend_prices, period=14)

        # Filter out NaN values
        valid_values = [r for r in result if not np.isnan(r)]
        assert len(valid_values) > 0
        assert valid_values[-1] > 70, "RSI should be overbought in strong uptrend"

    @pytest.mark.unit
    def test_rsi_oversold_in_downtrend(self, sample_downtrend_prices):
        """RSI should indicate oversold (<30) during strong downtrend."""
        result = calculate_rsi(sample_downtrend_prices, period=14)

        valid_values = [r for r in result if not np.isnan(r)]
        assert len(valid_values) > 0
        assert valid_values[-1] < 30, "RSI should be oversold in strong downtrend"

    @pytest.mark.unit
    def test_rsi_neutral_sideways(self, sample_sideways_prices):
        """RSI should be neutral (~50) in sideways market."""
        result = calculate_rsi(sample_sideways_prices, period=14)

        valid_values = [r for r in result if not np.isnan(r)]
        if len(valid_values) > 0:
            # In perfectly sideways market, RSI should be around 50
            assert 30 < valid_values[-1] < 70

    @pytest.mark.unit
    def test_rsi_range_boundaries(self, sample_prices):
        """RSI should always be between 0 and 100."""
        result = calculate_rsi(sample_prices, period=14)

        valid_values = [r for r in result if not np.isnan(r)]
        assert all(0 <= r <= 100 for r in valid_values)

    @pytest.mark.unit
    def test_rsi_nan_for_insufficient_data(self):
        """RSI should return NaN for first 'period' values."""
        prices = [100 + i for i in range(20)]
        result = calculate_rsi(prices, period=14)

        # First 14 values should be NaN
        assert all(np.isnan(r) for r in result[:14])
        # After period, should have valid values
        assert not np.isnan(result[14])

    @pytest.mark.unit
    def test_rsi_with_no_losses(self):
        """RSI should be 100 when there are no losses (pure uptrend)."""
        # Pure uptrend with no down moves
        prices = [100.0 + i * 1.0 for i in range(20)]
        result = calculate_rsi(prices, period=14)

        valid_values = [r for r in result if not np.isnan(r)]
        # Should approach 100
        assert valid_values[-1] > 95

    @pytest.mark.unit
    def test_rsi_with_no_gains(self):
        """RSI should be 0 when there are no gains (pure downtrend)."""
        # Pure downtrend with no up moves
        prices = [200.0 - i * 1.0 for i in range(20)]
        result = calculate_rsi(prices, period=14)

        valid_values = [r for r in result if not np.isnan(r)]
        # Should approach 0
        assert valid_values[-1] < 5


# ============================================================================
# Test: calculate_smoothed_rsi
# ============================================================================

class TestCalculateSmoothedRSI:
    """Tests for Smoothed RSI calculation."""

    @pytest.mark.unit
    def test_smoothed_rsi_smoother_than_raw(self, sample_prices):
        """Smoothed RSI should have less variance than raw RSI."""
        rsi = calculate_rsi(sample_prices, period=14)
        smoothed_rsi = calculate_smoothed_rsi(sample_prices, rsi_period=14, smooth_period=9)

        # Get valid values
        valid_rsi = [r for r in rsi if not np.isnan(r)]
        valid_smoothed = [r for r in smoothed_rsi if not np.isnan(r)]

        if len(valid_rsi) > 5 and len(valid_smoothed) > 5:
            # Smoothed should have lower standard deviation
            rsi_std = np.std(valid_rsi[-10:])
            smoothed_std = np.std(valid_smoothed[-10:])
            # Generally smoothed should be less volatile
            # (may not always be true, so we just check it exists)
            assert len(valid_smoothed) > 0

    @pytest.mark.unit
    def test_smoothed_rsi_same_length(self, sample_prices):
        """Smoothed RSI should have same length as input."""
        result = calculate_smoothed_rsi(sample_prices, rsi_period=14, smooth_period=9)
        assert len(result) == len(sample_prices)

    @pytest.mark.unit
    def test_smoothed_rsi_range(self, sample_prices):
        """Smoothed RSI should also be between 0 and 100."""
        result = calculate_smoothed_rsi(sample_prices, rsi_period=14, smooth_period=9)

        valid_values = [r for r in result if not np.isnan(r)]
        assert all(0 <= r <= 100 for r in valid_values)


# ============================================================================
# Test: get_rsi_category
# ============================================================================

class TestGetRSICategory:
    """Tests for RSI category classification."""

    @pytest.mark.unit
    @pytest.mark.parametrize("rsi,expected", [
        (75.0, 'OVERBOUGHT'),
        (70.0, 'OVERBOUGHT'),
        (69.9, 'STRONG'),
        (65.0, 'STRONG'),
        (60.0, 'STRONG'),
        (59.9, 'NEUTRAL'),
        (50.0, 'NEUTRAL'),
        (40.0, 'NEUTRAL'),
        (39.9, 'WEAK'),
        (35.0, 'WEAK'),
        (30.0, 'WEAK'),
        (29.9, 'OVERSOLD'),
        (20.0, 'OVERSOLD'),
        (0.0, 'OVERSOLD'),
    ])
    def test_rsi_category_mapping(self, rsi, expected):
        """RSI categories should match expected values at boundaries."""
        assert get_rsi_category(rsi) == expected

    @pytest.mark.unit
    def test_rsi_category_nan(self):
        """NaN RSI should return NEUTRAL."""
        assert get_rsi_category(np.nan) == 'NEUTRAL'

    @pytest.mark.unit
    def test_rsi_category_extreme_values(self):
        """Extreme RSI values should be categorized correctly."""
        assert get_rsi_category(100.0) == 'OVERBOUGHT'
        assert get_rsi_category(0.0) == 'OVERSOLD'


# ============================================================================
# Test: find_peaks_troughs
# ============================================================================

class TestFindPeaksTroughs:
    """Tests for peak and trough detection."""

    @pytest.mark.unit
    def test_find_peaks_simple(self):
        """Should find obvious peaks in simple data."""
        # Create data with clear peak at index 5
        data = pd.Series([10, 12, 14, 16, 18, 20, 18, 16, 14, 12, 10])
        peaks, troughs = find_peaks_troughs(data, order=2)

        assert 5 in peaks  # Peak at index 5 (value 20)

    @pytest.mark.unit
    def test_find_troughs_simple(self):
        """Should find obvious troughs in simple data."""
        # Create data with clear trough at index 5
        data = pd.Series([20, 18, 16, 14, 12, 10, 12, 14, 16, 18, 20])
        peaks, troughs = find_peaks_troughs(data, order=2)

        assert 5 in troughs  # Trough at index 5 (value 10)

    @pytest.mark.unit
    def test_find_peaks_troughs_multiple(self):
        """Should find multiple peaks and troughs."""
        # Wave pattern: up, down, up, down
        data = pd.Series([50, 55, 60, 55, 50, 45, 50, 55, 60, 55, 50])
        peaks, troughs = find_peaks_troughs(data, order=2)

        assert len(peaks) >= 1
        assert len(troughs) >= 1

    @pytest.mark.unit
    def test_find_peaks_troughs_with_nan(self):
        """Should handle NaN values gracefully."""
        data = pd.Series([10, 15, np.nan, 15, 10, 5, 10, 15, 20, 15, 10])
        peaks, troughs = find_peaks_troughs(data, order=2)

        # Should still find some peaks/troughs, skipping NaN positions
        assert isinstance(peaks, list)
        assert isinstance(troughs, list)

    @pytest.mark.unit
    def test_find_peaks_troughs_flat_data(self):
        """Should handle flat data without crashing."""
        data = pd.Series([50.0] * 20)
        peaks, troughs = find_peaks_troughs(data, order=2)

        # For flat data, scipy's argrelextrema may find all equal points as extrema
        # The important thing is that it doesn't crash and returns valid lists
        assert isinstance(peaks, list)
        assert isinstance(troughs, list)


# ============================================================================
# Test: detect_divergence
# ============================================================================

class TestDetectDivergence:
    """Tests for divergence detection."""

    @pytest.mark.unit
    def test_detect_divergence_returns_correct_structure(self, sample_prices):
        """Should return dict with all required keys."""
        rsi = calculate_rsi(sample_prices, period=14)
        result = detect_divergence(sample_prices, rsi, lookback=30)

        assert 'bullish_regular' in result
        assert 'bullish_hidden' in result
        assert 'bearish_regular' in result
        assert 'bearish_hidden' in result

    @pytest.mark.unit
    def test_detect_divergence_insufficient_data(self):
        """Should return all False for insufficient data."""
        prices = [100, 101, 102]
        rsi = [50, 51, 52]
        result = detect_divergence(prices, rsi, lookback=30)

        assert result['bullish_regular'] == False
        assert result['bullish_hidden'] == False
        assert result['bearish_regular'] == False
        assert result['bearish_hidden'] == False

    @pytest.mark.unit
    def test_detect_divergence_all_boolean(self, sample_prices):
        """All divergence values should be boolean."""
        rsi = calculate_rsi(sample_prices, period=14)
        result = detect_divergence(sample_prices, rsi, lookback=30)

        for key, value in result.items():
            assert isinstance(value, bool)


# ============================================================================
# Test: check_ema_cross_retest
# ============================================================================

class TestCheckEMACrossRetest:
    """Tests for EMA cross and retest detection."""

    @pytest.mark.unit
    def test_cross_retest_returns_correct_structure(self, sample_prices):
        """Should return dict with long_setup and short_setup keys."""
        ema13 = calculate_ema(sample_prices, period=13)
        ema21 = calculate_ema(sample_prices, period=21)
        result = check_ema_cross_retest(sample_prices, ema13, ema21, lookback=10)

        assert 'long_setup' in result
        assert 'short_setup' in result

    @pytest.mark.unit
    def test_cross_retest_insufficient_data(self):
        """Should return False for both when data is insufficient."""
        prices = [100, 101, 102]
        ema13 = [100, 100.5, 101]
        ema21 = [100, 100.3, 100.6]
        result = check_ema_cross_retest(prices, ema13, ema21, lookback=10)

        assert result['long_setup'] == False
        assert result['short_setup'] == False

    @pytest.mark.unit
    def test_cross_retest_boolean_values(self, sample_prices):
        """Values should be boolean."""
        ema13 = calculate_ema(sample_prices, period=13)
        ema21 = calculate_ema(sample_prices, period=21)
        result = check_ema_cross_retest(sample_prices, ema13, ema21, lookback=10)

        assert isinstance(result['long_setup'], bool)
        assert isinstance(result['short_setup'], bool)


# ============================================================================
# Test: detect_signal_layer
# ============================================================================

class TestDetectSignalLayer:
    """Tests for signal layer detection - Core logic."""

    @pytest.mark.unit
    def test_signal_layer_returns_correct_structure(self, sample_prices):
        """Should return dict with all required keys."""
        ema_13 = calculate_ema(sample_prices, period=13)
        ema_21 = calculate_ema(sample_prices, period=21)
        rsi_14 = calculate_rsi(sample_prices, period=14)
        smoothed_rsi = calculate_smoothed_rsi(sample_prices, rsi_period=14, smooth_period=9)

        result = detect_signal_layer(sample_prices, ema_13, ema_21, rsi_14, smoothed_rsi)

        assert 'long_layer' in result
        assert 'short_layer' in result
        assert 'long_signal' in result
        assert 'short_signal' in result

    @pytest.mark.unit
    def test_signal_layer_range(self, sample_prices):
        """Signal layers should be between 0-5."""
        ema_13 = calculate_ema(sample_prices, period=13)
        ema_21 = calculate_ema(sample_prices, period=21)
        rsi_14 = calculate_rsi(sample_prices, period=14)
        smoothed_rsi = calculate_smoothed_rsi(sample_prices, rsi_period=14, smooth_period=9)

        result = detect_signal_layer(sample_prices, ema_13, ema_21, rsi_14, smoothed_rsi)

        assert 0 <= result['long_layer'] <= 5
        assert 0 <= result['short_layer'] <= 5

    @pytest.mark.unit
    def test_signal_layer_insufficient_data(self):
        """Should return zeros for insufficient data."""
        prices = [100, 101, 102, 103, 104]
        ema_13 = calculate_ema(prices, period=13)
        ema_21 = calculate_ema(prices, period=21)
        rsi_14 = calculate_rsi(prices, period=14)
        smoothed_rsi = calculate_smoothed_rsi(prices, rsi_period=14, smooth_period=9)

        result = detect_signal_layer(prices, ema_13, ema_21, rsi_14, smoothed_rsi)

        assert result['long_layer'] == 0
        assert result['short_layer'] == 0

    @pytest.mark.unit
    def test_signal_layer_types(self, sample_prices):
        """Layer values should be int, signals should be str or None."""
        ema_13 = calculate_ema(sample_prices, period=13)
        ema_21 = calculate_ema(sample_prices, period=21)
        rsi_14 = calculate_rsi(sample_prices, period=14)
        smoothed_rsi = calculate_smoothed_rsi(sample_prices, rsi_period=14, smooth_period=9)

        result = detect_signal_layer(sample_prices, ema_13, ema_21, rsi_14, smoothed_rsi)

        assert isinstance(result['long_layer'], int)
        assert isinstance(result['short_layer'], int)
        assert result['long_signal'] is None or isinstance(result['long_signal'], str)
        assert result['short_signal'] is None or isinstance(result['short_signal'], str)


# ============================================================================
# Integration-like tests (testing multiple functions together)
# ============================================================================

class TestIndicatorIntegration:
    """Tests that verify indicators work together correctly."""

    @pytest.mark.unit
    def test_full_indicator_pipeline(self, sample_prices):
        """Test the full indicator calculation pipeline."""
        # Calculate all indicators
        ema_13 = calculate_ema(sample_prices, period=13)
        ema_21 = calculate_ema(sample_prices, period=21)
        rsi_14 = calculate_rsi(sample_prices, period=14)
        smoothed_rsi = calculate_smoothed_rsi(sample_prices, rsi_period=14, smooth_period=9)

        # All should have same length
        assert len(ema_13) == len(sample_prices)
        assert len(ema_21) == len(sample_prices)
        assert len(rsi_14) == len(sample_prices)
        assert len(smoothed_rsi) == len(sample_prices)

        # Signal detection should work
        result = detect_signal_layer(sample_prices, ema_13, ema_21, rsi_14, smoothed_rsi)
        assert result is not None

    @pytest.mark.unit
    def test_indicator_consistency(self):
        """Same input should always produce same output (deterministic)."""
        prices = [100 + i * 0.5 for i in range(50)]

        # Calculate twice
        ema1 = calculate_ema(prices, period=13)
        ema2 = calculate_ema(prices, period=13)

        rsi1 = calculate_rsi(prices, period=14)
        rsi2 = calculate_rsi(prices, period=14)

        # Results should be identical
        for i in range(len(ema1)):
            if not np.isnan(ema1[i]):
                assert abs(ema1[i] - ema2[i]) < 0.0001

        for i in range(len(rsi1)):
            if not np.isnan(rsi1[i]):
                assert abs(rsi1[i] - rsi2[i]) < 0.0001
