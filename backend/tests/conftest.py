"""
Shared fixtures for backend tests.

This file contains pytest fixtures that are automatically available to all tests.
Fixtures provide reusable test setup/teardown and mock configurations.
"""
import pytest
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_prices():
    """Generate sample price data for indicator testing."""
    # Realistic price movement pattern
    return [
        100.0, 101.5, 102.3, 101.8, 103.2, 104.5, 103.9, 105.1, 106.2, 105.8,
        107.0, 108.3, 107.5, 109.1, 110.2, 109.8, 111.0, 112.5, 111.9, 113.2,
        114.5, 113.8, 115.1, 116.3, 115.7, 117.0, 118.2, 117.6, 119.0, 120.3,
        119.5, 121.0, 122.4, 121.8, 123.1, 124.5, 123.9, 125.2, 126.4, 125.8,
        127.0, 128.3, 127.5, 129.0, 130.2, 129.6, 131.0, 132.3, 131.7, 133.0,
    ]


@pytest.fixture
def sample_uptrend_prices():
    """Generate strong uptrend price data (for testing overbought RSI)."""
    return [100.0 + i * 2 for i in range(30)]


@pytest.fixture
def sample_downtrend_prices():
    """Generate strong downtrend price data (for testing oversold RSI)."""
    return [200.0 - i * 2 for i in range(30)]


@pytest.fixture
def sample_sideways_prices():
    """Generate sideways/ranging price data (for testing neutral RSI)."""
    return [100.0 + (i % 2) * 1 for i in range(30)]


@pytest.fixture
def sample_klines():
    """Sample kline/candlestick data from Binance API format."""
    base_price = 42000.0
    klines = []
    for i in range(100):
        open_price = base_price + (i * 10) + (i % 5) * 5
        high_price = open_price + 50
        low_price = open_price - 30
        close_price = open_price + 20
        klines.append({
            'timestamp': 1700000000000 + (i * 14400000),  # 4h intervals
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': 1000.0 + (i * 10)
        })
    return klines


@pytest.fixture
def sample_tickers():
    """Sample ticker data from Binance API."""
    return [
        {'symbol': 'BTCUSDT', 'quoteVolume': '1000000000', 'priceChangePercent': '2.5'},
        {'symbol': 'ETHUSDT', 'quoteVolume': '500000000', 'priceChangePercent': '-1.2'},
        {'symbol': 'BNBUSDT', 'quoteVolume': '200000000', 'priceChangePercent': '0.8'},
        {'symbol': 'SOLUSDT', 'quoteVolume': '150000000', 'priceChangePercent': '5.3'},
        {'symbol': 'XRPUSDT', 'quoteVolume': '100000000', 'priceChangePercent': '-0.5'},
    ]


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_binance_api(sample_klines, sample_tickers):
    """Mock Binance API calls via aiohttp."""
    with patch('data_fetcher.aiohttp.ClientSession') as mock_session:
        # Create mock response
        mock_response = AsyncMock()
        mock_response.status = 200

        # Configure different responses based on URL
        async def mock_json():
            return sample_tickers

        mock_response.json = mock_json

        # Setup context managers
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None

        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_context
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)

        mock_session.return_value = mock_session_instance

        yield mock_session


@pytest.fixture
def mock_gemini_service():
    """Mock GeminiService to avoid actual API calls."""
    with patch('gemini_service.GeminiService') as MockService:
        instance = MagicMock()
        instance.is_configured.return_value = True
        instance.generate_response = AsyncMock(return_value={
            'success': True,
            'response': 'This is a mock AI response for testing.',
            'error': None
        })
        instance.generate_fundamental_analysis = AsyncMock(return_value={
            'success': True,
            'response': '## Mock Fundamental Analysis\n\nThis is a mock response.',
            'error': None
        })
        instance.get_market_summary.return_value = {
            'total_coins': 100,
            'overbought_count': 10,
            'oversold_count': 15,
            'strong_long_signals': 5,
            'strong_short_signals': 3
        }
        MockService.return_value = instance
        yield instance


@pytest.fixture
def temp_cache_db():
    """Create a temporary SQLite database for cache testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup after test
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_api_key_file():
    """Create temporary API key file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.api_key', delete=False) as f:
        f.write('test-api-key-12345')
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================

@pytest.fixture
async def async_client(mock_gemini_service):
    """Create async test client for FastAPI endpoints."""
    from httpx import AsyncClient, ASGITransport
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        yield client


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory."""
    return Path(__file__).parent / 'fixtures'


def load_fixture(fixtures_dir: Path, filename: str):
    """Load JSON fixture file."""
    filepath = fixtures_dir / filename
    if filepath.exists():
        return json.loads(filepath.read_text())
    return None
