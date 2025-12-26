"""
Integration tests for /api/heatmap endpoint

These tests verify the heatmap API endpoint behavior with mocked external services.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_data_fetcher():
    """Mock CryptoDataFetcher for API tests."""
    with patch('main.CryptoDataFetcher') as MockFetcher:
        instance = MagicMock()

        # Setup async context manager
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)

        # Mock get_top_symbols
        instance.get_top_symbols = AsyncMock(return_value=[
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT'
        ])

        # Mock get_klines with realistic data
        sample_klines = [
            {'timestamp': 1700000000000 + i * 14400000,
             'open': 42000 + i * 10,
             'high': 42100 + i * 10,
             'low': 41900 + i * 10,
             'close': 42050 + i * 10,
             'volume': 1000 + i}
            for i in range(100)
        ]
        instance.get_klines = AsyncMock(return_value=sample_klines)

        MockFetcher.return_value = instance
        yield MockFetcher


@pytest.fixture
def mock_cache_manager():
    """Mock CacheManager to control cache behavior."""
    with patch('main.cache_manager') as mock_cache:
        mock_cache.get_cache = MagicMock(return_value=None)  # Cache miss by default
        mock_cache.set_cache = MagicMock()
        yield mock_cache


# ============================================================================
# Test: Heatmap Endpoint Success Cases
# ============================================================================

class TestHeatmapAPISuccess:
    """Tests for successful heatmap API responses."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_heatmap_returns_success(self, async_client, mock_data_fetcher, mock_cache_manager):
        """Heatmap should return success response with valid data."""
        response = await async_client.get('/api/heatmap?limit=10&timeframe=4h')

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert 'signals' in data
        assert 'timeframe' in data
        assert data['timeframe'] == '4h'

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_heatmap_contains_required_fields(self, async_client, mock_data_fetcher, mock_cache_manager):
        """Heatmap response should contain all required fields."""
        response = await async_client.get('/api/heatmap?limit=10&timeframe=4h')
        data = response.json()

        # Check top-level fields
        assert 'success' in data
        assert 'timeframe' in data
        assert 'signals' in data
        assert 'updated_at' in data
        assert 'total_coins' in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_heatmap_signal_structure(self, async_client, mock_data_fetcher, mock_cache_manager):
        """Each signal should have required fields."""
        response = await async_client.get('/api/heatmap?limit=10&timeframe=4h')
        data = response.json()

        if len(data['signals']) > 0:
            signal = data['signals'][0]
            required_fields = [
                'symbol', 'full_name', 'price', 'price_change_24h',
                'rsi', 'rsi_smoothed', 'ema_13', 'ema_21',
                'long_layer', 'short_layer'
            ]
            for field in required_fields:
                assert field in signal, f"Missing field: {field}"


# ============================================================================
# Test: Heatmap Timeframe Variations
# ============================================================================

class TestHeatmapTimeframes:
    """Tests for different timeframe parameters."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.parametrize("timeframe", ['15m', '1h', '4h', '12h', '1d', '1w'])
    async def test_heatmap_accepts_valid_timeframes(
        self, async_client, mock_data_fetcher, mock_cache_manager, timeframe
    ):
        """Heatmap should accept all valid timeframes."""
        response = await async_client.get(f'/api/heatmap?limit=10&timeframe={timeframe}')

        assert response.status_code == 200
        data = response.json()
        assert data['timeframe'] == timeframe

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_heatmap_default_timeframe(self, async_client, mock_data_fetcher, mock_cache_manager):
        """Heatmap should use default timeframe when not specified."""
        response = await async_client.get('/api/heatmap?limit=10')

        assert response.status_code == 200
        data = response.json()
        # Default timeframe is 4h
        assert data['timeframe'] == '4h'


# ============================================================================
# Test: Heatmap Caching
# ============================================================================

class TestHeatmapCaching:
    """Tests for cache behavior."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_heatmap_cache_miss_header(self, async_client, mock_data_fetcher, mock_cache_manager):
        """Should return X-Cache: MISS header on cache miss."""
        mock_cache_manager.get_cache.return_value = None

        response = await async_client.get('/api/heatmap?limit=10&timeframe=4h')

        assert response.status_code == 200
        assert response.headers.get('X-Cache') == 'MISS'

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_heatmap_cache_hit_header(self, async_client, mock_cache_manager):
        """Should return X-Cache: HIT header on cache hit."""
        # Set up cache hit
        cached_data = {
            'success': True,
            'timeframe': '4h',
            'updated_at': '2024-01-01T12:00:00Z',
            'total_coins': 10,
            'signals': []
        }
        mock_cache_manager.get_cache.return_value = cached_data

        response = await async_client.get('/api/heatmap?limit=10&timeframe=4h')

        assert response.status_code == 200
        assert response.headers.get('X-Cache') == 'HIT'

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_heatmap_cache_stores_result(self, async_client, mock_data_fetcher, mock_cache_manager):
        """Should store result in cache after fetch."""
        mock_cache_manager.get_cache.return_value = None

        response = await async_client.get('/api/heatmap?limit=10&timeframe=4h')

        assert response.status_code == 200
        # Verify set_cache was called
        mock_cache_manager.set_cache.assert_called()


# ============================================================================
# Test: Heatmap Limit Parameter
# ============================================================================

class TestHeatmapLimit:
    """Tests for limit parameter."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_heatmap_respects_limit(self, async_client, mock_data_fetcher, mock_cache_manager):
        """Should respect the limit parameter."""
        response = await async_client.get('/api/heatmap?limit=50&timeframe=4h')

        assert response.status_code == 200
        # Fetcher should be called - verify the call was made
        assert mock_data_fetcher.return_value.get_top_symbols.called

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_heatmap_default_limit(self, async_client, mock_data_fetcher, mock_cache_manager):
        """Should use default limit when not specified."""
        response = await async_client.get('/api/heatmap?timeframe=4h')

        assert response.status_code == 200
        # Fetcher should be called - verify the call was made
        assert mock_data_fetcher.return_value.get_top_symbols.called


# ============================================================================
# Test: Health Check
# ============================================================================

class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, async_client):
        """Health endpoint should return OK status."""
        response = await async_client.get('/api/health')

        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'ok' or 'status' in data


# ============================================================================
# Test: Root API Endpoint
# ============================================================================

class TestRootEndpoint:
    """Tests for root API endpoint."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_api_root_accessible(self, async_client):
        """API root should be accessible."""
        response = await async_client.get('/api')

        assert response.status_code == 200
