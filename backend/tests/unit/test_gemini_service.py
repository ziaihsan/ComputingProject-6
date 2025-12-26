"""
Unit tests for GeminiService

Tests the Gemini AI service with mocked API calls and file operations.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import os

# Import functions and classes to test
from gemini_service import (
    get_api_key,
    get_api_key_source,
    save_api_key,
    is_api_key_disabled,
    disable_api_key,
    enable_api_key,
    get_selected_model,
    save_selected_model,
    get_available_models,
    validate_api_key,
    GeminiService,
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
)


# ============================================================================
# Test: API Key Management
# ============================================================================

class TestGetApiKey:
    """Tests for get_api_key function."""

    @pytest.mark.unit
    def test_get_api_key_from_env(self):
        """Should return API key from environment variable."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-env-key'}):
            with patch('gemini_service.API_KEY_FILE') as mock_file:
                mock_file.exists.return_value = False
                with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
                    mock_disabled.exists.return_value = False
                    result = get_api_key()
                    assert result == 'test-env-key'

    @pytest.mark.unit
    def test_get_api_key_disabled(self):
        """Should return None if API key is disabled."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = True
            result = get_api_key()
            assert result is None

    @pytest.mark.unit
    def test_get_api_key_from_file(self):
        """Should return API key from file."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = False
            with patch('gemini_service.API_KEY_FILE') as mock_file:
                mock_file.exists.return_value = True
                mock_file.read_text.return_value = 'file-api-key'
                result = get_api_key()
                assert result == 'file-api-key'


class TestGetApiKeySource:
    """Tests for get_api_key_source function."""

    @pytest.mark.unit
    def test_source_disabled(self):
        """Should return 'disabled' if API key is disabled."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = True
            result = get_api_key_source()
            assert result == 'disabled'

    @pytest.mark.unit
    def test_source_file(self):
        """Should return 'file' if key is from file."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = False
            with patch('gemini_service.API_KEY_FILE') as mock_file:
                mock_file.exists.return_value = True
                mock_file.read_text.return_value = 'some-key'
                result = get_api_key_source()
                assert result == 'file'

    @pytest.mark.unit
    def test_source_env(self):
        """Should return 'env' if key is from environment."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'env-key'}):
            with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
                mock_disabled.exists.return_value = False
                with patch('gemini_service.API_KEY_FILE') as mock_file:
                    mock_file.exists.return_value = False
                    result = get_api_key_source()
                    assert result == 'env'

    @pytest.mark.unit
    def test_source_none(self):
        """Should return None if no key available."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove GEMINI_API_KEY if it exists
            os.environ.pop('GEMINI_API_KEY', None)
            with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
                mock_disabled.exists.return_value = False
                with patch('gemini_service.API_KEY_FILE') as mock_file:
                    mock_file.exists.return_value = False
                    result = get_api_key_source()
                    assert result is None


class TestSaveApiKey:
    """Tests for save_api_key function."""

    @pytest.mark.unit
    def test_save_api_key_success(self):
        """Should save API key to file."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = False
            with patch('gemini_service.API_KEY_FILE') as mock_file:
                result = save_api_key('new-api-key')
                assert result is True
                mock_file.write_text.assert_called_once_with('new-api-key')

    @pytest.mark.unit
    def test_save_api_key_removes_disabled(self):
        """Should remove disabled flag when saving."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = True
            with patch('gemini_service.API_KEY_FILE') as mock_file:
                save_api_key('new-key')
                mock_disabled.unlink.assert_called_once()


class TestDisableEnableApiKey:
    """Tests for disable_api_key and enable_api_key functions."""

    @pytest.mark.unit
    def test_is_api_key_disabled(self):
        """Should check if disabled file exists."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = True
            assert is_api_key_disabled() is True

            mock_disabled.exists.return_value = False
            assert is_api_key_disabled() is False

    @pytest.mark.unit
    def test_disable_api_key(self):
        """Should create disabled flag file."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            with patch('gemini_service.API_KEY_FILE') as mock_file:
                mock_file.exists.return_value = False
                result = disable_api_key()
                assert result is True
                mock_disabled.write_text.assert_called_once_with("disabled")

    @pytest.mark.unit
    def test_enable_api_key(self):
        """Should remove disabled flag file."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = True
            result = enable_api_key()
            assert result is True
            mock_disabled.unlink.assert_called_once()


# ============================================================================
# Test: Model Management
# ============================================================================

class TestModelManagement:
    """Tests for model selection functions."""

    @pytest.mark.unit
    def test_get_available_models(self):
        """Should return dict of available models."""
        models = get_available_models()
        assert isinstance(models, dict)
        assert "gemini-2.5-flash" in models
        assert "gemini-2.5-pro" in models

    @pytest.mark.unit
    def test_get_selected_model_default(self):
        """Should return default model if no config."""
        with patch('gemini_service.MODEL_CONFIG_FILE') as mock_file:
            mock_file.exists.return_value = False
            result = get_selected_model()
            assert result == DEFAULT_MODEL

    @pytest.mark.unit
    def test_get_selected_model_from_file(self):
        """Should return model from config file."""
        with patch('gemini_service.MODEL_CONFIG_FILE') as mock_file:
            mock_file.exists.return_value = True
            mock_file.read_text.return_value = '{"model": "gemini-2.5-pro"}'
            result = get_selected_model()
            assert result == "gemini-2.5-pro"

    @pytest.mark.unit
    def test_save_selected_model_valid(self):
        """Should save valid model."""
        with patch('gemini_service.MODEL_CONFIG_FILE') as mock_file:
            result = save_selected_model("gemini-2.5-pro")
            assert result is True
            mock_file.write_text.assert_called_once()

    @pytest.mark.unit
    def test_save_selected_model_invalid(self):
        """Should reject invalid model."""
        result = save_selected_model("invalid-model")
        assert result is False


# ============================================================================
# Test: validate_api_key
# ============================================================================

class TestValidateApiKey:
    """Tests for validate_api_key function."""

    @pytest.mark.unit
    def test_validate_api_key_success(self):
        """Should return valid=True on success."""
        with patch('gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Hello!"
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            result = validate_api_key("valid-key")
            assert result["valid"] is True
            assert result["error"] is None

    @pytest.mark.unit
    def test_validate_api_key_invalid(self):
        """Should return invalid_api_key error."""
        with patch('gemini_service.genai') as mock_genai:
            mock_genai.GenerativeModel.side_effect = Exception("API_KEY invalid")

            result = validate_api_key("bad-key")
            assert result["valid"] is False
            assert result["error"] == "invalid_api_key"

    @pytest.mark.unit
    def test_validate_api_key_rate_limit(self):
        """Should return rate_limit error."""
        with patch('gemini_service.genai') as mock_genai:
            mock_genai.GenerativeModel.side_effect = Exception("quota exceeded 429")

            result = validate_api_key("key")
            assert result["valid"] is False
            assert result["error"] == "rate_limit"


# ============================================================================
# Test: GeminiService class
# ============================================================================

class TestGeminiService:
    """Tests for GeminiService class."""

    @pytest.mark.unit
    def test_init_without_api_key(self):
        """Should initialize with None model if no API key."""
        with patch('gemini_service.get_api_key', return_value=None):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                service = GeminiService()
                assert service.api_key is None
                assert service.model is None

    @pytest.mark.unit
    def test_is_configured_false(self):
        """Should return False if not configured."""
        with patch('gemini_service.get_api_key', return_value=None):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                service = GeminiService()
                assert service.is_configured() is False

    @pytest.mark.unit
    def test_is_configured_true(self):
        """Should return True if configured."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_genai.GenerativeModel.return_value = MagicMock()
                    service = GeminiService()
                    assert service.is_configured() is True

    @pytest.mark.unit
    def test_get_current_model(self):
        """Should return current model name."""
        with patch('gemini_service.get_api_key', return_value=None):
            with patch('gemini_service.get_selected_model', return_value="gemini-2.5-pro"):
                service = GeminiService()
                assert service.get_current_model() == "gemini-2.5-pro"

    @pytest.mark.unit
    def test_set_model_valid(self):
        """Should change model successfully."""
        with patch('gemini_service.get_api_key', return_value=None):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.save_selected_model', return_value=True):
                    service = GeminiService()
                    result = service.set_model("gemini-2.5-pro")
                    assert result is True
                    assert service.model_name == "gemini-2.5-pro"

    @pytest.mark.unit
    def test_set_model_invalid(self):
        """Should reject invalid model."""
        with patch('gemini_service.get_api_key', return_value=None):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                service = GeminiService()
                result = service.set_model("invalid-model")
                assert result is False

    @pytest.mark.unit
    def test_get_market_summary(self):
        """Should calculate market summary correctly."""
        with patch('gemini_service.get_api_key', return_value=None):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                service = GeminiService()

                market_data = {
                    "signals": [
                        {"symbol": "BTC", "rsi": 75, "long_layer": 5, "short_layer": 0},
                        {"symbol": "ETH", "rsi": 25, "long_layer": 0, "short_layer": 4},
                        {"symbol": "SOL", "rsi": 50, "long_layer": 2, "short_layer": 0},
                    ]
                }

                summary = service.get_market_summary(market_data)

                assert summary["total_coins"] == 3
                assert summary["overbought_count"] == 1
                assert summary["oversold_count"] == 1
                assert summary["strong_long_signals"] == 1
                assert summary["strong_short_signals"] == 1


# ============================================================================
# Test: generate_response
# ============================================================================

class TestGenerateResponse:
    """Tests for generate_response method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_not_configured(self):
        """Should return error if not configured."""
        with patch('gemini_service.get_api_key', return_value=None):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                service = GeminiService()

                result = await service.generate_response(
                    "What's the market like?",
                    {"signals": []},
                    "4h"
                )

                assert result["success"] is False
                assert result["error"] == "not_configured"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        """Should return AI response on success."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    # Setup mocks
                    mock_chat = MagicMock()
                    mock_response = MagicMock()
                    mock_response.text = "Market analysis response"
                    mock_chat.send_message.return_value = mock_response

                    mock_model = MagicMock()
                    mock_model.start_chat.return_value = mock_chat
                    mock_genai.GenerativeModel.return_value = mock_model

                    service = GeminiService()

                    result = await service.generate_response(
                        "What's the market like?",
                        {"signals": []},
                        "4h"
                    )

                    assert result["success"] is True
                    assert result["response"] == "Market analysis response"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_api_error(self):
        """Should handle API errors gracefully."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_model = MagicMock()
                    mock_model.start_chat.side_effect = Exception("API error 401 invalid")
                    mock_genai.GenerativeModel.return_value = mock_model

                    service = GeminiService()

                    result = await service.generate_response(
                        "Test",
                        {"signals": []},
                        "4h"
                    )

                    assert result["success"] is False
                    assert result["error"] == "invalid_api_key"


# ============================================================================
# Test: generate_fundamental_analysis
# ============================================================================

class TestGenerateFundamentalAnalysis:
    """Tests for generate_fundamental_analysis method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fundamental_not_configured(self):
        """Should return error if no API key."""
        with patch('gemini_service.get_api_key', return_value=None):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                service = GeminiService()

                result = await service.generate_fundamental_analysis("BTCUSDT")

                assert result["success"] is False
                assert result["error"] == "not_configured"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fundamental_success(self):
        """Should return fundamental analysis on success."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_response = MagicMock()
                    mock_response.text = "## BTCUSDT Analysis\nBitcoin is..."

                    mock_model = MagicMock()
                    mock_model.generate_content.return_value = mock_response
                    mock_genai.GenerativeModel.return_value = mock_model

                    service = GeminiService()

                    result = await service.generate_fundamental_analysis("BTCUSDT")

                    assert result["success"] is True
                    assert "BTCUSDT" in result["response"]
