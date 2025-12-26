"""
Unit tests for CryptoDataFetcher

Tests the data fetching functionality with mocked HTTP responses.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from data_fetcher import CryptoDataFetcher


# ============================================================================
# Test: CryptoDataFetcher initialization
# ============================================================================

class TestCryptoDataFetcherInit:
    """Tests for CryptoDataFetcher initialization."""

    @pytest.mark.unit
    def test_init_creates_instance(self):
        """Should create instance with None session."""
        fetcher = CryptoDataFetcher()
        assert fetcher.session is None

    @pytest.mark.unit
    def test_intervals_defined(self):
        """Should have predefined intervals."""
        fetcher = CryptoDataFetcher()
        assert '5m' in fetcher.INTERVALS
        assert '1h' in fetcher.INTERVALS
        assert '4h' in fetcher.INTERVALS
        assert '1d' in fetcher.INTERVALS
        assert '1w' in fetcher.INTERVALS

    @pytest.mark.unit
    def test_binance_api_url(self):
        """Should have correct Binance API URL."""
        assert CryptoDataFetcher.BINANCE_API == "https://data-api.binance.vision/api/v3"


# ============================================================================
# Test: get_top_symbols
# ============================================================================

class TestGetTopSymbols:
    """Tests for get_top_symbols method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_top_symbols_success(self):
        """Should return list of symbols on success."""
        mock_data = [
            {"symbol": "BTCUSDT", "quoteVolume": "1000000000"},
            {"symbol": "ETHUSDT", "quoteVolume": "500000000"},
            {"symbol": "SOLUSDT", "quoteVolume": "100000000"},
            {"symbol": "USDCUSDT", "quoteVolume": "50000000"},  # Should be filtered
        ]

        fetcher = CryptoDataFetcher()

        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        fetcher.session = mock_session

        result = await fetcher.get_top_symbols(limit=3)

        assert isinstance(result, list)
        assert "BTCUSDT" in result
        assert "ETHUSDT" in result
        # USDCUSDT should be filtered out (starts with USDC)
        assert "USDCUSDT" not in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_top_symbols_api_error(self):
        """Should return empty list on API error."""
        fetcher = CryptoDataFetcher()

        mock_response = AsyncMock()
        mock_response.status = 500

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        fetcher.session = mock_session

        result = await fetcher.get_top_symbols()

        assert result == []


# ============================================================================
# Test: get_klines
# ============================================================================

class TestGetKlines:
    """Tests for get_klines method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_klines_success(self):
        """Should return formatted kline data on success."""
        mock_klines = [
            [1703980800000, "42000.00", "42500.00", "41800.00", "42300.00", "1000.5", 0, 0, 0, 0, 0, 0],
            [1703984400000, "42300.00", "42800.00", "42100.00", "42600.00", "800.3", 0, 0, 0, 0, 0, 0],
        ]

        fetcher = CryptoDataFetcher()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_klines)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        fetcher.session = mock_session

        result = await fetcher.get_klines("BTCUSDT", "4h", 100)

        assert len(result) == 2
        assert result[0]['timestamp'] == 1703980800000
        assert result[0]['open'] == 42000.00
        assert result[0]['high'] == 42500.00
        assert result[0]['low'] == 41800.00
        assert result[0]['close'] == 42300.00
        assert result[0]['volume'] == 1000.5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_klines_api_error(self):
        """Should return empty list on API error."""
        fetcher = CryptoDataFetcher()

        mock_response = AsyncMock()
        mock_response.status = 404

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        fetcher.session = mock_session

        result = await fetcher.get_klines("INVALIDPAIR", "4h")

        assert result == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_klines_exception(self):
        """Should return empty list on exception."""
        fetcher = CryptoDataFetcher()

        mock_session = AsyncMock()
        mock_session.get = MagicMock(side_effect=Exception("Network error"))

        fetcher.session = mock_session

        result = await fetcher.get_klines("BTCUSDT", "4h")

        assert result == []


# ============================================================================
# Test: get_ticker_24h
# ============================================================================

class TestGetTicker24h:
    """Tests for get_ticker_24h method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_ticker_success(self):
        """Should return ticker data on success."""
        mock_ticker = {
            "symbol": "BTCUSDT",
            "priceChange": "1000.00",
            "priceChangePercent": "2.5",
            "lastPrice": "42000.00"
        }

        fetcher = CryptoDataFetcher()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_ticker)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        fetcher.session = mock_session

        result = await fetcher.get_ticker_24h("BTCUSDT")

        assert result is not None
        assert result['symbol'] == "BTCUSDT"
        assert result['lastPrice'] == "42000.00"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_ticker_api_error(self):
        """Should return None on API error."""
        fetcher = CryptoDataFetcher()

        mock_response = AsyncMock()
        mock_response.status = 400

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        fetcher.session = mock_session

        result = await fetcher.get_ticker_24h("INVALID")

        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_ticker_exception(self):
        """Should return None on exception."""
        fetcher = CryptoDataFetcher()

        mock_session = AsyncMock()
        mock_session.get = MagicMock(side_effect=Exception("Timeout"))

        fetcher.session = mock_session

        result = await fetcher.get_ticker_24h("BTCUSDT")

        assert result is None


# ============================================================================
# Test: get_all_tickers
# ============================================================================

class TestGetAllTickers:
    """Tests for get_all_tickers method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_all_tickers_success(self):
        """Should return list of tickers on success."""
        mock_tickers = [
            {"symbol": "BTCUSDT", "lastPrice": "42000.00"},
            {"symbol": "ETHUSDT", "lastPrice": "2200.00"},
        ]

        fetcher = CryptoDataFetcher()

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_tickers)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        fetcher.session = mock_session

        result = await fetcher.get_all_tickers()

        assert len(result) == 2
        assert result[0]['symbol'] == "BTCUSDT"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_all_tickers_error(self):
        """Should return empty list on error."""
        fetcher = CryptoDataFetcher()

        mock_response = AsyncMock()
        mock_response.status = 500

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        fetcher.session = mock_session

        result = await fetcher.get_all_tickers()

        assert result == []


# ============================================================================
# Test: fetch_multi_timeframe_data
# ============================================================================

class TestFetchMultiTimeframeData:
    """Tests for fetch_multi_timeframe_data method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_multi_timeframe_returns_dict(self):
        """Should return dict with timeframe keys."""
        fetcher = CryptoDataFetcher()

        mock_klines = [[1703980800000, "42000", "42500", "41800", "42300", "1000", 0, 0, 0, 0, 0, 0]]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_klines)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        fetcher.session = mock_session

        result = await fetcher.fetch_multi_timeframe_data("BTCUSDT", ["1h", "4h"])

        assert isinstance(result, dict)
        assert "1h" in result
        assert "4h" in result
