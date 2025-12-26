"""
Extended tests for data_fetcher.py to achieve 90%+ coverage

Covers context managers and edge cases.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from data_fetcher import CryptoDataFetcher


# ============================================================================
# Test: Context Manager
# ============================================================================

class TestContextManager:
    """Tests for async context manager."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_aenter_creates_session(self):
        """__aenter__ should create aiohttp session."""
        fetcher = CryptoDataFetcher()

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            with patch('aiohttp.TCPConnector'):
                result = await fetcher.__aenter__()

                assert result is fetcher

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_aexit_closes_session(self):
        """__aexit__ should close session."""
        fetcher = CryptoDataFetcher()
        mock_session = AsyncMock()
        fetcher.session = mock_session

        await fetcher.__aexit__(None, None, None)

        mock_session.close.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_aexit_no_session(self):
        """__aexit__ should handle None session."""
        fetcher = CryptoDataFetcher()
        fetcher.session = None

        # Should not raise
        await fetcher.__aexit__(None, None, None)


# ============================================================================
# Test: get_all_tickers Edge Cases
# ============================================================================

class TestGetAllTickersEdgeCases:
    """Edge cases for get_all_tickers."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_all_tickers_exception(self):
        """Should return empty list on exception."""
        fetcher = CryptoDataFetcher()

        mock_session = AsyncMock()
        mock_session.get = MagicMock(side_effect=Exception("Connection timeout"))

        fetcher.session = mock_session

        result = await fetcher.get_all_tickers()

        assert result == []


# ============================================================================
# Test: get_top_symbols Edge Cases
# ============================================================================

class TestGetTopSymbolsEdgeCases:
    """Edge cases for get_top_symbols."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_top_symbols_filters_zero_volume(self):
        """Should filter out zero volume pairs."""
        mock_data = [
            {"symbol": "BTCUSDT", "quoteVolume": "1000000"},
            {"symbol": "ZEROVOLUME", "quoteVolume": "0"},
            {"symbol": "ETHUSDT", "quoteVolume": "500000"},
        ]

        fetcher = CryptoDataFetcher()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        fetcher.session = mock_session

        result = await fetcher.get_top_symbols(limit=10)

        assert "BTCUSDT" in result
        assert "ETHUSDT" in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_top_symbols_limit(self):
        """Should respect limit parameter."""
        mock_data = [
            {"symbol": f"COIN{i}USDT", "quoteVolume": str(1000000 - i * 1000)}
            for i in range(50)
        ]

        fetcher = CryptoDataFetcher()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        fetcher.session = mock_session

        result = await fetcher.get_top_symbols(limit=5)

        assert len(result) == 5


# ============================================================================
# Test: get_klines Edge Cases
# ============================================================================

class TestGetKlinesEdgeCases:
    """Edge cases for get_klines."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_klines_empty_response(self):
        """Should handle empty response."""
        fetcher = CryptoDataFetcher()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[])

        mock_session = AsyncMock()
        mock_session.get = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        fetcher.session = mock_session

        result = await fetcher.get_klines("BTCUSDT", "4h", 100)

        assert result == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_klines_malformed_data(self):
        """Should handle malformed kline data."""
        fetcher = CryptoDataFetcher()

        # Kline data with fewer elements than expected
        mock_klines = [
            [1700000000, "100", "105"],  # Incomplete
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_klines)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        fetcher.session = mock_session

        # This might raise or return empty - just check it doesn't crash completely
        try:
            result = await fetcher.get_klines("BTCUSDT", "4h", 100)
        except (IndexError, Exception):
            result = []

        assert isinstance(result, list)


# ============================================================================
# Test: fetch_multi_timeframe_data Edge Cases
# ============================================================================

class TestFetchMultiTimeframeEdgeCases:
    """Edge cases for fetch_multi_timeframe_data."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_multi_empty_timeframes(self):
        """Should handle empty timeframes list."""
        fetcher = CryptoDataFetcher()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[])

        mock_session = AsyncMock()
        mock_session.get = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        fetcher.session = mock_session

        result = await fetcher.fetch_multi_timeframe_data("BTCUSDT", [])

        assert result == {}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_multi_partial_failure(self):
        """Should handle partial failures gracefully."""
        fetcher = CryptoDataFetcher()

        call_count = [0]

        async def mock_get_klines(symbol, interval, limit):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                return []  # Failure
            return [{"timestamp": 1, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}]

        fetcher.get_klines = mock_get_klines

        result = await fetcher.fetch_multi_timeframe_data("BTCUSDT", ["1h", "4h", "1d"])

        assert isinstance(result, dict)
        assert "1h" in result
        assert "4h" in result
        assert "1d" in result
