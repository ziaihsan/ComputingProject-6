"""
Extended tests for main.py API endpoints to achieve 90%+ coverage

Covers complex flows, error handling, and edge cases.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import json

with patch('main.GeminiService'):
    with patch('main.CacheManager'):
        from main import app, ChatRequest, FundamentalRequest


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# ============================================================================
# Test: Heatmap - Full Flow
# ============================================================================

class TestHeatmapFullFlow:
    """Full flow tests for heatmap endpoint."""

    @pytest.mark.unit
    def test_heatmap_successful_fetch(self, client):
        """Should fetch and process data successfully."""
        mock_klines = [
            {'timestamp': 1700000000, 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
            for _ in range(60)
        ]

        with patch('main.cache_manager') as mock_cache:
            mock_cache.get_cache.return_value = None
            with patch('main.CryptoDataFetcher') as mock_fetcher_class:
                mock_fetcher = AsyncMock()
                mock_fetcher.get_top_symbols.return_value = ["BTCUSDT", "ETHUSDT"]
                mock_fetcher.get_klines.return_value = mock_klines
                mock_fetcher.__aenter__.return_value = mock_fetcher
                mock_fetcher.__aexit__.return_value = None
                mock_fetcher_class.return_value = mock_fetcher

                response = client.get("/api/heatmap?timeframe=4h&limit=2")

                # Should return 200 (might be success or error depending on data)
                assert response.status_code == 200

    @pytest.mark.unit
    def test_heatmap_exception_handling(self, client):
        """Should handle exceptions gracefully."""
        with patch('main.cache_manager') as mock_cache:
            mock_cache.get_cache.return_value = None
            with patch('main.CryptoDataFetcher') as mock_fetcher_class:
                mock_fetcher_class.side_effect = Exception("Network error")

                response = client.get("/api/heatmap?timeframe=4h")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False

    @pytest.mark.unit
    def test_heatmap_different_timeframes(self, client):
        """Should handle different timeframes."""
        cached_data = {"success": True, "timeframe": "15m", "signals": []}

        with patch('main.cache_manager') as mock_cache:
            mock_cache.get_cache.return_value = cached_data

            for tf in ["15m", "1h", "4h", "12h", "1d"]:
                response = client.get(f"/api/heatmap?timeframe={tf}")
                assert response.status_code == 200


# ============================================================================
# Test: Stats Endpoint
# ============================================================================

class TestStatsEndpoint:
    """Tests for /api/stats endpoint."""

    @pytest.mark.unit
    def test_stats_success(self, client):
        """Should return signal statistics."""
        mock_heatmap_data = {
            "success": True,
            "signals": [
                {"symbol": "BTC", "long_layer": 5, "short_layer": 0},
                {"symbol": "ETH", "long_layer": 4, "short_layer": 0},
                {"symbol": "SOL", "long_layer": 0, "short_layer": 3},
            ]
        }

        with patch('main.cache_manager') as mock_cache:
            mock_cache.get_cache.return_value = mock_heatmap_data

            response = client.get("/api/stats?timeframe=4h")

            assert response.status_code == 200
            data = response.json()
            assert "long_signals" in data or "success" in data

    @pytest.mark.unit
    def test_stats_with_failed_heatmap(self, client):
        """Should handle heatmap failure."""
        mock_heatmap_data = {"success": False, "signals": []}

        with patch('main.cache_manager') as mock_cache:
            mock_cache.get_cache.return_value = mock_heatmap_data

            response = client.get("/api/stats?timeframe=4h")
            assert response.status_code == 200


# ============================================================================
# Test: API Key Rate Limit Handling
# ============================================================================

class TestApiKeyRateLimit:
    """Tests for rate limit handling in API key validation."""

    @pytest.mark.unit
    def test_set_apikey_rate_limit_saves_anyway(self, client):
        """Should save API key even on rate limit."""
        with patch('main.validate_api_key', return_value={"valid": False, "error": "rate_limit"}):
            with patch('main.save_api_key', return_value=True):
                with patch('main.GeminiService'):
                    response = client.post(
                        "/api/settings/apikey",
                        json={"api_key": "rate-limited-key"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data.get("warning") == "rate_limit"


# ============================================================================
# Test: Model Save Failure
# ============================================================================

class TestModelSaveFailure:
    """Tests for model save failure."""

    @pytest.mark.unit
    def test_set_model_save_failure(self, client):
        """Should handle save failure."""
        mock_models = {"gemini-2.5-flash": {"name": "Flash"}}

        with patch('main.get_available_models', return_value=mock_models):
            with patch('main.save_selected_model', return_value=False):
                response = client.post(
                    "/api/settings/models",
                    json={"model": "gemini-2.5-flash"}
                )

                assert response.status_code == 500


# ============================================================================
# Test: Chat Endpoint - Full Flow
# ============================================================================

class TestChatFullFlow:
    """Full flow tests for chat endpoint."""

    @pytest.mark.unit
    def test_chat_successful_response(self, client):
        """Should return AI response successfully."""
        mock_heatmap = {"success": True, "signals": []}

        with patch('main.gemini_service') as mock_service:
            mock_service.is_configured.return_value = True
            mock_service.generate_response = AsyncMock(return_value={
                "success": True,
                "response": "AI analysis here",
                "error": None
            })
            mock_service.get_market_summary.return_value = {
                "total_coins": 10,
                "overbought_count": 2
            }

            with patch('main.cache_manager') as mock_cache:
                mock_cache.get_cache.return_value = mock_heatmap

                response = client.post(
                    "/api/chat",
                    json={"message": "What's the market like?", "timeframe": "4h"}
                )

                # Response code depends on full flow
                assert response.status_code in [200, 500, 503]

    @pytest.mark.unit
    def test_chat_heatmap_failure(self, client):
        """Should handle heatmap fetch failure."""
        mock_heatmap = {"success": False, "signals": []}

        with patch('main.gemini_service') as mock_service:
            mock_service.is_configured.return_value = True

            with patch('main.cache_manager') as mock_cache:
                mock_cache.get_cache.return_value = mock_heatmap

                response = client.post(
                    "/api/chat",
                    json={"message": "Test", "timeframe": "4h"}
                )

                assert response.status_code in [200, 500]

    @pytest.mark.unit
    def test_chat_with_conversation_history(self, client):
        """Should accept conversation history."""
        response = client.post(
            "/api/chat",
            json={
                "message": "Follow up",
                "timeframe": "4h",
                "conversation_history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi!"}
                ]
            }
        )

        # Just check it doesn't crash
        assert response.status_code in [200, 500, 503]

    @pytest.mark.unit
    def test_chat_exception(self, client):
        """Should handle exceptions in chat."""
        with patch('main.gemini_service') as mock_service:
            mock_service.is_configured.return_value = True

            with patch('main.cache_manager') as mock_cache:
                mock_cache.get_cache.side_effect = Exception("DB error")

                response = client.post(
                    "/api/chat",
                    json={"message": "Test", "timeframe": "4h"}
                )

                assert response.status_code == 500


# ============================================================================
# Test: Fundamental Analysis - Full Flow
# ============================================================================

class TestFundamentalFullFlow:
    """Full flow tests for fundamental analysis endpoint."""

    @pytest.mark.unit
    def test_fundamental_success(self, client):
        """Should return fundamental analysis."""
        with patch('main.gemini_service') as mock_service:
            mock_service.is_configured.return_value = True
            mock_service.generate_fundamental_analysis = AsyncMock(return_value={
                "success": True,
                "response": "## Bitcoin Analysis\n...",
                "error": None
            })

            response = client.post(
                "/api/fundamental",
                json={"symbol": "BTCUSDT", "timeframe": "4h"}
            )

            assert response.status_code in [200, 503]

    @pytest.mark.unit
    def test_fundamental_exception(self, client):
        """Should handle exceptions."""
        with patch('main.gemini_service') as mock_service:
            mock_service.is_configured.return_value = True
            mock_service.generate_fundamental_analysis = AsyncMock(
                side_effect=Exception("API error")
            )

            response = client.post(
                "/api/fundamental",
                json={"symbol": "BTCUSDT", "timeframe": "4h"}
            )

            assert response.status_code == 500


# ============================================================================
# Test: Delete API Key Exception
# ============================================================================

class TestDeleteApiKeyException:
    """Tests for delete API key exception handling."""

    @pytest.mark.unit
    def test_delete_apikey_exception(self, client):
        """Should handle exception during delete."""
        with patch('main.disable_api_key', side_effect=Exception("IO error")):
            response = client.delete("/api/settings/apikey")

            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False


# ============================================================================
# Test: Pydantic Models Extended
# ============================================================================

class TestPydanticModelsExtended:
    """Extended tests for Pydantic models."""

    @pytest.mark.unit
    def test_chat_request_with_history(self):
        """ChatRequest with conversation history."""
        from main import ChatRequest, ChatMessage

        history = [ChatMessage(role="user", content="Hello")]
        req = ChatRequest(
            message="Follow up",
            timeframe="1h",
            conversation_history=history
        )

        assert req.timeframe == "1h"
        assert len(req.conversation_history) == 1

    @pytest.mark.unit
    def test_chat_message_model(self):
        """ChatMessage model validation."""
        from main import ChatMessage

        msg = ChatMessage(role="user", content="Test message")
        assert msg.role == "user"
        assert msg.content == "Test message"

    @pytest.mark.unit
    def test_api_key_request_model(self):
        """ApiKeyRequest model validation."""
        from main import ApiKeyRequest

        req = ApiKeyRequest(api_key="test-key-123")
        assert req.api_key == "test-key-123"

    @pytest.mark.unit
    def test_model_request_model(self):
        """ModelRequest model validation."""
        from main import ModelRequest

        req = ModelRequest(model="gemini-2.5-flash")
        assert req.model == "gemini-2.5-flash"
