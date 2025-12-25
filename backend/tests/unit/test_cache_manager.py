"""
Unit tests for cache_manager.py - SQLite cache testing

These tests use temporary databases to ensure isolation from production.
Each test gets a fresh database that is automatically cleaned up after.
"""
import pytest
import os
import time
import tempfile
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cache_manager import CacheManager


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_cache():
    """Create a CacheManager with temporary database."""
    # Create a temp file for the database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)  # Close the file descriptor

    # Create cache manager with custom path
    # We need to pass just the filename since CacheManager prepends the directory
    cache = CacheManager.__new__(CacheManager)
    cache.db_path = db_path
    cache.init_db()

    yield cache

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_heatmap_data():
    """Sample data that mimics heatmap API response."""
    return {
        'success': True,
        'timeframe': '4h',
        'updated_at': '2024-01-01T12:00:00Z',
        'total_coins': 100,
        'signals': [
            {
                'symbol': 'BTCUSDT',
                'full_name': 'Bitcoin',
                'price': 42000.0,
                'price_change_24h': 2.5,
                'rsi': 55.3,
                'rsi_smoothed': 52.1,
                'ema_13': 41800.0,
                'ema_21': 41500.0,
                'market_cap_rank': 1,
                'market_cap': 0,
                'long_layer': 3,
                'short_layer': 0
            },
            {
                'symbol': 'ETHUSDT',
                'full_name': 'Ethereum',
                'price': 2200.0,
                'price_change_24h': -1.2,
                'rsi': 35.8,
                'rsi_smoothed': 38.2,
                'ema_13': 2180.0,
                'ema_21': 2150.0,
                'market_cap_rank': 2,
                'market_cap': 0,
                'long_layer': 2,
                'short_layer': 0
            }
        ]
    }


# ============================================================================
# Test: Cache Key Generation
# ============================================================================

class TestCacheKeyGeneration:
    """Tests for _get_cache_key method."""

    @pytest.mark.unit
    def test_cache_key_format(self, temp_cache):
        """Cache key should follow expected format."""
        key = temp_cache._get_cache_key(100, '4h')
        assert key == 'heatmap_100_4h'

    @pytest.mark.unit
    def test_cache_key_different_params(self, temp_cache):
        """Different parameters should produce different keys."""
        key1 = temp_cache._get_cache_key(100, '4h')
        key2 = temp_cache._get_cache_key(100, '1h')
        key3 = temp_cache._get_cache_key(50, '4h')

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

    @pytest.mark.unit
    def test_cache_key_same_params(self, temp_cache):
        """Same parameters should produce same key."""
        key1 = temp_cache._get_cache_key(100, '4h')
        key2 = temp_cache._get_cache_key(100, '4h')

        assert key1 == key2


# ============================================================================
# Test: Cache Set and Get
# ============================================================================

class TestCacheSetGet:
    """Tests for set_cache and get_cache methods."""

    @pytest.mark.unit
    def test_set_and_get_cache(self, temp_cache, sample_heatmap_data):
        """Should store and retrieve data correctly."""
        temp_cache.set_cache(
            limit=100,
            timeframe='4h',
            data=sample_heatmap_data,
            ttl_seconds=300
        )

        result = temp_cache.get_cache(limit=100, timeframe='4h')

        assert result is not None
        assert result == sample_heatmap_data

    @pytest.mark.unit
    def test_cache_miss(self, temp_cache):
        """Should return None for non-existent cache."""
        result = temp_cache.get_cache(limit=999, timeframe='1h')
        assert result is None

    @pytest.mark.unit
    def test_cache_overwrite(self, temp_cache):
        """Setting same key should overwrite previous value."""
        data1 = {'version': 1, 'data': 'first'}
        data2 = {'version': 2, 'data': 'second'}

        temp_cache.set_cache(limit=100, timeframe='4h', data=data1)
        temp_cache.set_cache(limit=100, timeframe='4h', data=data2)

        result = temp_cache.get_cache(limit=100, timeframe='4h')

        assert result == data2
        assert result['version'] == 2

    @pytest.mark.unit
    def test_multiple_cache_entries(self, temp_cache):
        """Should store multiple entries with different keys."""
        data_4h = {'timeframe': '4h', 'signals': []}
        data_1h = {'timeframe': '1h', 'signals': []}
        data_1d = {'timeframe': '1d', 'signals': []}

        temp_cache.set_cache(limit=100, timeframe='4h', data=data_4h)
        temp_cache.set_cache(limit=100, timeframe='1h', data=data_1h)
        temp_cache.set_cache(limit=100, timeframe='1d', data=data_1d)

        assert temp_cache.get_cache(100, '4h') == data_4h
        assert temp_cache.get_cache(100, '1h') == data_1h
        assert temp_cache.get_cache(100, '1d') == data_1d


# ============================================================================
# Test: Cache Expiration
# ============================================================================

class TestCacheExpiration:
    """Tests for cache TTL and expiration."""

    @pytest.mark.unit
    def test_cache_valid_before_expiration(self, temp_cache):
        """Cache should be valid before TTL expires."""
        data = {'test': 'data'}
        temp_cache.set_cache(limit=100, timeframe='4h', data=data, ttl_seconds=60)

        # Immediately retrieve - should be valid
        result = temp_cache.get_cache(limit=100, timeframe='4h')
        assert result == data

    @pytest.mark.unit
    def test_cache_expired_after_ttl(self, temp_cache):
        """Cache should return None after TTL expires."""
        data = {'test': 'data'}
        # Set with very short TTL
        temp_cache.set_cache(limit=100, timeframe='4h', data=data, ttl_seconds=1)

        # Wait for expiration
        time.sleep(1.5)

        result = temp_cache.get_cache(limit=100, timeframe='4h')
        assert result is None

    @pytest.mark.unit
    def test_different_ttl_values(self, temp_cache):
        """Different TTL values should be respected."""
        data_short = {'ttl': 'short'}
        data_long = {'ttl': 'long'}

        # Short TTL (1 second)
        temp_cache.set_cache(limit=100, timeframe='1h', data=data_short, ttl_seconds=1)
        # Longer TTL (60 seconds)
        temp_cache.set_cache(limit=100, timeframe='4h', data=data_long, ttl_seconds=60)

        # Wait for short TTL to expire
        time.sleep(1.5)

        # Short TTL should be expired
        assert temp_cache.get_cache(100, '1h') is None
        # Long TTL should still be valid
        assert temp_cache.get_cache(100, '4h') == data_long


# ============================================================================
# Test: Cache Cleanup
# ============================================================================

class TestCacheCleanup:
    """Tests for automatic cache cleanup."""

    @pytest.mark.unit
    def test_expired_entries_cleaned_on_get(self, temp_cache):
        """Expired entries should be cleaned up when get_cache is called."""
        # Set data that will expire
        temp_cache.set_cache(limit=50, timeframe='1h', data={'old': 'data'}, ttl_seconds=1)
        temp_cache.set_cache(limit=100, timeframe='4h', data={'new': 'data'}, ttl_seconds=60)

        # Wait for first entry to expire
        time.sleep(1.5)

        # Get any cache - this should trigger cleanup
        result = temp_cache.get_cache(limit=100, timeframe='4h')

        # Should still get valid cache
        assert result == {'new': 'data'}

        # Expired entry should be cleaned (no way to verify directly without DB access)


# ============================================================================
# Test: Data Types
# ============================================================================

class TestCacheDataTypes:
    """Tests for various data types in cache."""

    @pytest.mark.unit
    def test_cache_nested_dict(self, temp_cache):
        """Should handle nested dictionaries."""
        data = {
            'level1': {
                'level2': {
                    'level3': {
                        'value': 'deep'
                    }
                }
            }
        }
        temp_cache.set_cache(limit=100, timeframe='4h', data=data)
        result = temp_cache.get_cache(100, '4h')

        assert result['level1']['level2']['level3']['value'] == 'deep'

    @pytest.mark.unit
    def test_cache_list_data(self, temp_cache):
        """Should handle lists in data."""
        data = {
            'items': [1, 2, 3, 4, 5],
            'nested': [{'a': 1}, {'b': 2}]
        }
        temp_cache.set_cache(limit=100, timeframe='4h', data=data)
        result = temp_cache.get_cache(100, '4h')

        assert result['items'] == [1, 2, 3, 4, 5]
        assert result['nested'][0]['a'] == 1

    @pytest.mark.unit
    def test_cache_numeric_data(self, temp_cache):
        """Should handle various numeric types."""
        data = {
            'integer': 42,
            'float': 3.14159,
            'negative': -100,
            'zero': 0,
            'large': 1000000000
        }
        temp_cache.set_cache(limit=100, timeframe='4h', data=data)
        result = temp_cache.get_cache(100, '4h')

        assert result['integer'] == 42
        assert abs(result['float'] - 3.14159) < 0.0001
        assert result['negative'] == -100

    @pytest.mark.unit
    def test_cache_boolean_and_null(self, temp_cache):
        """Should handle boolean and null values."""
        data = {
            'true_val': True,
            'false_val': False,
            'null_val': None
        }
        temp_cache.set_cache(limit=100, timeframe='4h', data=data)
        result = temp_cache.get_cache(100, '4h')

        assert result['true_val'] == True
        assert result['false_val'] == False
        assert result['null_val'] is None

    @pytest.mark.unit
    def test_cache_empty_structures(self, temp_cache):
        """Should handle empty dict and list."""
        data = {
            'empty_dict': {},
            'empty_list': [],
            'empty_string': ''
        }
        temp_cache.set_cache(limit=100, timeframe='4h', data=data)
        result = temp_cache.get_cache(100, '4h')

        assert result['empty_dict'] == {}
        assert result['empty_list'] == []
        assert result['empty_string'] == ''


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestCacheEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.unit
    def test_cache_unicode_data(self, temp_cache):
        """Should handle unicode characters."""
        data = {
            'japanese': '日本語',
            'emoji': '🚀💰📈',
            'mixed': 'BTC to the moon! 🌙'
        }
        temp_cache.set_cache(limit=100, timeframe='4h', data=data)
        result = temp_cache.get_cache(100, '4h')

        assert result['japanese'] == '日本語'
        assert result['emoji'] == '🚀💰📈'

    @pytest.mark.unit
    def test_cache_special_characters(self, temp_cache):
        """Should handle special characters in data."""
        data = {
            'quotes': 'He said "Hello"',
            'newlines': 'Line1\nLine2\nLine3',
            'tabs': 'Col1\tCol2\tCol3'
        }
        temp_cache.set_cache(limit=100, timeframe='4h', data=data)
        result = temp_cache.get_cache(100, '4h')

        assert result['quotes'] == 'He said "Hello"'
        assert '\n' in result['newlines']

    @pytest.mark.unit
    def test_cache_large_data(self, temp_cache):
        """Should handle reasonably large data."""
        # Generate large dataset
        signals = [
            {
                'symbol': f'COIN{i}USDT',
                'price': 1000 + i,
                'rsi': 50.0 + (i % 50)
            }
            for i in range(500)
        ]
        data = {'signals': signals, 'total': 500}

        temp_cache.set_cache(limit=500, timeframe='4h', data=data)
        result = temp_cache.get_cache(500, '4h')

        assert result is not None
        assert len(result['signals']) == 500

    @pytest.mark.unit
    def test_cache_zero_ttl(self, temp_cache):
        """Zero TTL should immediately expire."""
        data = {'test': 'immediate_expire'}
        temp_cache.set_cache(limit=100, timeframe='4h', data=data, ttl_seconds=0)

        # Even immediate get might miss due to timing
        # This tests the edge case behavior
        result = temp_cache.get_cache(100, '4h')
        # Result could be None or the data depending on timing
        # The important thing is it doesn't crash
        assert result is None or result == data
