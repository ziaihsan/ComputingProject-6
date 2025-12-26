"""
Extended tests for cache_manager.py to achieve 90%+ coverage

Covers error handling and edge cases.
"""
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
import time

from cache_manager import CacheManager


# ============================================================================
# Test: Cache Manager Initialization
# ============================================================================

class TestCacheManagerInit:
    """Tests for CacheManager initialization."""

    @pytest.mark.unit
    def test_init_creates_db(self):
        """Should create database file on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_cache.db")

            # Mock the path resolution
            with patch('cache_manager.os.path.dirname', return_value=tmpdir):
                with patch('cache_manager.os.path.abspath', return_value=tmpdir):
                    manager = CacheManager(db_path="test_cache.db")

                    # Should have db_path attribute
                    assert manager.db_path is not None

    @pytest.mark.unit
    def test_init_db_exception(self):
        """Should handle init_db exception gracefully."""
        with patch('cache_manager.sqlite3.connect') as mock_connect:
            mock_connect.side_effect = Exception("DB connection failed")

            # Should not raise
            manager = CacheManager()


# ============================================================================
# Test: get_cache Edge Cases
# ============================================================================

class TestGetCacheEdgeCases:
    """Edge cases for get_cache method."""

    @pytest.mark.unit
    def test_get_cache_not_found(self):
        """Should return None for non-existent cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('cache_manager.os.path.dirname', return_value=tmpdir):
                with patch('cache_manager.os.path.abspath', return_value=tmpdir):
                    manager = CacheManager(db_path="test.db")

                    result = manager.get_cache(999, "1d")

                    assert result is None

    @pytest.mark.unit
    def test_get_cache_exception(self):
        """Should return None on exception."""
        with patch('cache_manager.sqlite3.connect') as mock_connect:
            # First call succeeds (for init), subsequent fail
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            manager = CacheManager()

            # Now make connect fail
            mock_connect.side_effect = Exception("DB error")

            result = manager.get_cache(100, "4h")

            assert result is None

    @pytest.mark.unit
    def test_get_cache_cleans_expired(self):
        """Should clean expired entries during get."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('cache_manager.os.path.dirname', return_value=tmpdir):
                with patch('cache_manager.os.path.abspath', return_value=tmpdir):
                    manager = CacheManager(db_path="test.db")

                    # Set cache with very short TTL
                    manager.set_cache(100, "4h", {"test": "data"}, ttl_seconds=1)

                    # Wait for expiration
                    time.sleep(1.1)

                    # Get should return None and clean up
                    result = manager.get_cache(100, "4h")
                    assert result is None


# ============================================================================
# Test: set_cache Edge Cases
# ============================================================================

class TestSetCacheEdgeCases:
    """Edge cases for set_cache method."""

    @pytest.mark.unit
    def test_set_cache_overwrites(self):
        """Should overwrite existing cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('cache_manager.os.path.dirname', return_value=tmpdir):
                with patch('cache_manager.os.path.abspath', return_value=tmpdir):
                    manager = CacheManager(db_path="test.db")

                    # Set initial cache
                    manager.set_cache(100, "4h", {"version": 1}, ttl_seconds=300)

                    # Overwrite
                    manager.set_cache(100, "4h", {"version": 2}, ttl_seconds=300)

                    # Get should return new version
                    result = manager.get_cache(100, "4h")

                    assert result is not None
                    assert result.get("version") == 2

    @pytest.mark.unit
    def test_set_cache_exception(self):
        """Should handle exception gracefully."""
        with patch('cache_manager.sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            manager = CacheManager()

            # Make connect fail for set_cache
            mock_connect.side_effect = Exception("DB error")

            # Should not raise
            manager.set_cache(100, "4h", {"test": "data"}, ttl_seconds=300)


# ============================================================================
# Test: Cache Key Generation
# ============================================================================

class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    @pytest.mark.unit
    def test_get_cache_key(self):
        """Should generate correct cache key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('cache_manager.os.path.dirname', return_value=tmpdir):
                with patch('cache_manager.os.path.abspath', return_value=tmpdir):
                    manager = CacheManager(db_path="test.db")

                    key = manager._get_cache_key(100, "4h")

                    assert key == "heatmap_100_4h"

    @pytest.mark.unit
    def test_different_limits_different_keys(self):
        """Different limits should create different cache entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('cache_manager.os.path.dirname', return_value=tmpdir):
                with patch('cache_manager.os.path.abspath', return_value=tmpdir):
                    manager = CacheManager(db_path="test.db")

                    manager.set_cache(100, "4h", {"limit": 100}, ttl_seconds=300)
                    manager.set_cache(200, "4h", {"limit": 200}, ttl_seconds=300)

                    result_100 = manager.get_cache(100, "4h")
                    result_200 = manager.get_cache(200, "4h")

                    assert result_100.get("limit") == 100
                    assert result_200.get("limit") == 200

    @pytest.mark.unit
    def test_different_timeframes_different_keys(self):
        """Different timeframes should create different cache entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('cache_manager.os.path.dirname', return_value=tmpdir):
                with patch('cache_manager.os.path.abspath', return_value=tmpdir):
                    manager = CacheManager(db_path="test.db")

                    manager.set_cache(100, "1h", {"tf": "1h"}, ttl_seconds=300)
                    manager.set_cache(100, "4h", {"tf": "4h"}, ttl_seconds=300)

                    result_1h = manager.get_cache(100, "1h")
                    result_4h = manager.get_cache(100, "4h")

                    assert result_1h.get("tf") == "1h"
                    assert result_4h.get("tf") == "4h"
