"""
Unit tests for FastAPI main.py endpoints

Tests API endpoints with mocked dependencies.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import json

# We need to mock external dependencies before importing main
with patch('main.GeminiService'):
    with patch('main.CacheManager'):
        from main import app


# ============================================================================
# Test Client Fixture
# ============================================================================

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# ============================================================================
# Test: API Root
# ============================================================================

class TestApiRoot:
    """Tests for /api endpoint."""

    @pytest.mark.unit
    def test_api_root(self, client):
        """Should return API info."""
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "message" in data


# ============================================================================
# Test: Health Check
# ============================================================================

class TestHealthCheck:
    """Tests for /api/health endpoint."""

    @pytest.mark.unit
    def test_health_check(self, client):
        """Should return ok status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# ============================================================================
# Test: Settings - API Key
# ============================================================================

class TestApiKeySettings:
    """Tests for /api/settings/apikey endpoints."""

    @pytest.mark.unit
    def test_get_apikey_not_configured(self, client):
        """Should return not configured if no API key."""
        with patch('main.get_api_key', return_value=None):
            with patch('main.get_api_key_source', return_value=None):
                response = client.get("/api/settings/apikey")
                assert response.status_code == 200
                data = response.json()
                assert data["configured"] is False
                assert data["masked_key"] is None

    @pytest.mark.unit
    def test_get_apikey_configured(self, client):
        """Should return masked key if configured."""
        with patch('main.get_api_key', return_value="test-api-key-12345"):
            with patch('main.get_api_key_source', return_value='file'):
                with patch('main.gemini_service') as mock_service:
                    mock_service.is_configured.return_value = True
                    response = client.get("/api/settings/apikey")
                    assert response.status_code == 200
                    data = response.json()
                    assert data["configured"] is True
                    assert data["masked_key"].endswith("2345")
                    assert data["source"] == "file"

    @pytest.mark.unit
    def test_set_apikey_empty(self, client):
        """Should reject empty API key."""
        response = client.post(
            "/api/settings/apikey",
            json={"api_key": ""}
        )
        assert response.status_code == 400
        assert response.json()["success"] is False

    @pytest.mark.unit
    def test_set_apikey_invalid(self, client):
        """Should reject invalid API key."""
        with patch('main.validate_api_key', return_value={"valid": False, "error": "invalid_api_key"}):
            response = client.post(
                "/api/settings/apikey",
                json={"api_key": "bad-key"}
            )
            assert response.status_code == 400
            assert response.json()["success"] is False

    @pytest.mark.unit
    def test_set_apikey_valid(self, client):
        """Should accept valid API key."""
        with patch('main.validate_api_key', return_value={"valid": True, "error": None}):
            with patch('main.save_api_key', return_value=True):
                with patch('main.GeminiService'):
                    response = client.post(
                        "/api/settings/apikey",
                        json={"api_key": "valid-api-key"}
                    )
                    assert response.status_code == 200
                    assert response.json()["success"] is True

    @pytest.mark.unit
    def test_delete_apikey_success(self, client):
        """Should delete API key successfully."""
        with patch('main.disable_api_key', return_value=True):
            with patch('main.GeminiService'):
                response = client.delete("/api/settings/apikey")
                assert response.status_code == 200
                assert response.json()["success"] is True

    @pytest.mark.unit
    def test_delete_apikey_failure(self, client):
        """Should handle delete failure."""
        with patch('main.disable_api_key', return_value=False):
            response = client.delete("/api/settings/apikey")
            assert response.status_code == 500


# ============================================================================
# Test: Settings - Models
# ============================================================================

class TestModelSettings:
    """Tests for /api/settings/models endpoints."""

    @pytest.mark.unit
    def test_get_models(self, client):
        """Should return available models."""
        mock_models = {
            "gemini-2.5-flash": {"name": "Flash", "tier": "stable"},
            "gemini-2.5-pro": {"name": "Pro", "tier": "stable"},
        }
        with patch('main.get_available_models', return_value=mock_models):
            with patch('main.get_selected_model', return_value="gemini-2.5-flash"):
                response = client.get("/api/settings/models")
                assert response.status_code == 200
                data = response.json()
                assert "models" in data
                assert data["current_model"] == "gemini-2.5-flash"

    @pytest.mark.unit
    def test_set_model_valid(self, client):
        """Should set valid model."""
        mock_models = {"gemini-2.5-pro": {"name": "Pro"}}
        with patch('main.get_available_models', return_value=mock_models):
            with patch('main.save_selected_model', return_value=True):
                with patch('main.GeminiService'):
                    response = client.post(
                        "/api/settings/models",
                        json={"model": "gemini-2.5-pro"}
                    )
                    assert response.status_code == 200
                    assert response.json()["success"] is True

    @pytest.mark.unit
    def test_set_model_invalid(self, client):
        """Should reject invalid model."""
        with patch('main.get_available_models', return_value={}):
            response = client.post(
                "/api/settings/models",
                json={"model": "invalid-model"}
            )
            assert response.status_code == 400


# ============================================================================
# Test: Heatmap
# ============================================================================

class TestHeatmap:
    """Tests for /api/heatmap endpoint."""

    @pytest.mark.unit
    def test_heatmap_cache_hit(self, client):
        """Should return cached data when available."""
        cached_data = {
            "success": True,
            "timeframe": "4h",
            "signals": [{"symbol": "BTCUSDT", "rsi": 55}]
        }
        with patch('main.cache_manager') as mock_cache:
            mock_cache.get_cache.return_value = cached_data
            response = client.get("/api/heatmap?timeframe=4h")
            assert response.status_code == 200
            assert response.headers.get("X-Cache") == "HIT"

    @pytest.mark.unit
    def test_heatmap_no_symbols(self, client):
        """Should handle empty symbols list."""
        with patch('main.cache_manager') as mock_cache:
            mock_cache.get_cache.return_value = None
            with patch('main.CryptoDataFetcher') as mock_fetcher_class:
                mock_fetcher = AsyncMock()
                mock_fetcher.get_top_symbols.return_value = []
                mock_fetcher.__aenter__.return_value = mock_fetcher
                mock_fetcher.__aexit__.return_value = None
                mock_fetcher_class.return_value = mock_fetcher

                response = client.get("/api/heatmap?timeframe=4h")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False


# ============================================================================
# Test: Chat
# ============================================================================

class TestChat:
    """Tests for /api/chat endpoint."""

    @pytest.mark.unit
    def test_chat_not_configured(self, client):
        """Should return error if service not configured."""
        with patch('main.gemini_service', None):
            response = client.post(
                "/api/chat",
                json={"message": "Hello", "timeframe": "4h"}
            )
            assert response.status_code == 503
            data = response.json()
            assert data["success"] is False
            assert data["error"] == "service_unavailable"


# ============================================================================
# Test: Fundamental Analysis
# ============================================================================

class TestFundamental:
    """Tests for /api/fundamental endpoint."""

    @pytest.mark.unit
    def test_fundamental_not_configured(self, client):
        """Should return error if service not configured."""
        with patch('main.gemini_service', None):
            response = client.post(
                "/api/fundamental",
                json={"symbol": "BTCUSDT", "timeframe": "4h"}
            )
            assert response.status_code == 503
            data = response.json()
            assert data["success"] is False


# ============================================================================
# Test: Pydantic Models
# ============================================================================

class TestPydanticModels:
    """Tests for request/response models."""

    @pytest.mark.unit
    def test_chat_request_defaults(self):
        """ChatRequest should have correct defaults."""
        from main import ChatRequest
        req = ChatRequest(message="test")
        assert req.timeframe == "4h"
        assert req.conversation_history is None

    @pytest.mark.unit
    def test_fundamental_request_defaults(self):
        """FundamentalRequest should have correct defaults."""
        from main import FundamentalRequest
        req = FundamentalRequest(symbol="BTCUSDT")
        assert req.timeframe == "4h"
