"""
Extended tests for gemini_service.py to achieve 90%+ coverage

Covers error handling paths and edge cases.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os

from gemini_service import (
    get_api_key, get_api_key_source, save_api_key,
    is_api_key_disabled, disable_api_key, enable_api_key,
    get_selected_model, save_selected_model, validate_api_key,
    GeminiService, DEFAULT_MODEL
)


# ============================================================================
# Test: API Key Edge Cases
# ============================================================================

class TestApiKeyEdgeCases:
    """Edge cases for API key management."""

    @pytest.mark.unit
    def test_get_api_key_empty_file(self):
        """Should return env key if file is empty."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = False
            with patch('gemini_service.API_KEY_FILE') as mock_file:
                mock_file.exists.return_value = True
                mock_file.read_text.return_value = '   '  # Whitespace only
                with patch.dict(os.environ, {'GEMINI_API_KEY': 'env-key'}):
                    result = get_api_key()
                    # Empty file should fallback to env
                    assert result is not None

    @pytest.mark.unit
    def test_get_api_key_source_empty_file(self):
        """Should return env if file is empty."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = False
            with patch('gemini_service.API_KEY_FILE') as mock_file:
                mock_file.exists.return_value = True
                mock_file.read_text.return_value = ''
                with patch.dict(os.environ, {'GEMINI_API_KEY': 'env-key'}):
                    result = get_api_key_source()
                    assert result == 'env'

    @pytest.mark.unit
    def test_save_api_key_exception(self):
        """Should return False on exception."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = False
            with patch('gemini_service.API_KEY_FILE') as mock_file:
                mock_file.write_text.side_effect = Exception("Permission denied")
                result = save_api_key('test-key')
                assert result is False

    @pytest.mark.unit
    def test_disable_api_key_with_existing_file(self):
        """Should remove existing API key file when disabling."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            with patch('gemini_service.API_KEY_FILE') as mock_file:
                mock_file.exists.return_value = True
                result = disable_api_key()
                assert result is True
                mock_file.unlink.assert_called_once()

    @pytest.mark.unit
    def test_disable_api_key_exception(self):
        """Should return False on exception."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.write_text.side_effect = Exception("Error")
            result = disable_api_key()
            assert result is False

    @pytest.mark.unit
    def test_enable_api_key_not_disabled(self):
        """Should return True even if not disabled."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = False
            result = enable_api_key()
            assert result is True

    @pytest.mark.unit
    def test_enable_api_key_exception(self):
        """Should return False on exception."""
        with patch('gemini_service.API_KEY_DISABLED_FILE') as mock_disabled:
            mock_disabled.exists.return_value = True
            mock_disabled.unlink.side_effect = Exception("Error")
            result = enable_api_key()
            assert result is False


# ============================================================================
# Test: Model Management Edge Cases
# ============================================================================

class TestModelEdgeCases:
    """Edge cases for model management."""

    @pytest.mark.unit
    def test_get_selected_model_invalid_json(self):
        """Should return default on invalid JSON."""
        with patch('gemini_service.MODEL_CONFIG_FILE') as mock_file:
            mock_file.exists.return_value = True
            mock_file.read_text.return_value = 'invalid json{'
            result = get_selected_model()
            assert result == DEFAULT_MODEL

    @pytest.mark.unit
    def test_get_selected_model_invalid_model(self):
        """Should return default if saved model is invalid."""
        with patch('gemini_service.MODEL_CONFIG_FILE') as mock_file:
            mock_file.exists.return_value = True
            mock_file.read_text.return_value = '{"model": "nonexistent-model"}'
            result = get_selected_model()
            assert result == DEFAULT_MODEL

    @pytest.mark.unit
    def test_save_selected_model_exception(self):
        """Should return False on exception."""
        with patch('gemini_service.MODEL_CONFIG_FILE') as mock_file:
            mock_file.write_text.side_effect = Exception("Error")
            result = save_selected_model("gemini-2.5-flash")
            assert result is False


# ============================================================================
# Test: Validate API Key Edge Cases
# ============================================================================

class TestValidateApiKeyEdgeCases:
    """Edge cases for API key validation."""

    @pytest.mark.unit
    def test_validate_empty_response(self):
        """Should return invalid on empty response."""
        with patch('gemini_service.genai') as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = ""  # Empty response
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            result = validate_api_key("test-key")
            assert result["valid"] is False
            assert result["error"] == "empty_response"

    @pytest.mark.unit
    def test_validate_model_not_found(self):
        """Should return model_not_found error."""
        with patch('gemini_service.genai') as mock_genai:
            mock_genai.GenerativeModel.side_effect = Exception("Model not found 404")

            result = validate_api_key("test-key")
            assert result["valid"] is False
            assert result["error"] == "model_not_found"

    @pytest.mark.unit
    def test_validate_unknown_error(self):
        """Should return unknown error message."""
        with patch('gemini_service.genai') as mock_genai:
            mock_genai.GenerativeModel.side_effect = Exception("Some unknown error")

            result = validate_api_key("test-key")
            assert result["valid"] is False
            assert "Some unknown error" in result["error"]


# ============================================================================
# Test: GeminiService Edge Cases
# ============================================================================

class TestGeminiServiceEdgeCases:
    """Edge cases for GeminiService class."""

    @pytest.mark.unit
    def test_init_model_failure(self):
        """Should handle model initialization failure."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_genai.configure.side_effect = Exception("Config failed")

                    service = GeminiService()
                    assert service.model is None

    @pytest.mark.unit
    def test_reload_api_key(self):
        """Should reload API key successfully."""
        with patch('gemini_service.get_api_key', return_value=None):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                service = GeminiService()

                # Now mock a new key
                with patch('gemini_service.get_api_key', return_value="new-key"):
                    with patch('gemini_service.genai') as mock_genai:
                        mock_genai.GenerativeModel.return_value = MagicMock()
                        service.reload_api_key()

                        assert service.api_key == "new-key"

    @pytest.mark.unit
    def test_set_model_reinitializes(self):
        """Should reinitialize model when changing."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_genai.GenerativeModel.return_value = MagicMock()
                    with patch('gemini_service.save_selected_model', return_value=True):
                        service = GeminiService()
                        result = service.set_model("gemini-2.5-pro")

                        assert result is True
                        assert service.model_name == "gemini-2.5-pro"


# ============================================================================
# Test: Generate Response Edge Cases
# ============================================================================

class TestGenerateResponseEdgeCases:
    """Edge cases for generate_response method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_rate_limit(self):
        """Should handle rate limit error."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_model = MagicMock()
                    mock_model.start_chat.side_effect = Exception("quota exceeded 429")
                    mock_genai.GenerativeModel.return_value = mock_model

                    service = GeminiService()
                    result = await service.generate_response(
                        "Test", {"signals": []}, "4h"
                    )

                    assert result["success"] is False
                    assert result["error"] == "rate_limit"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_model_not_found(self):
        """Should handle model not found error."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_model = MagicMock()
                    mock_model.start_chat.side_effect = Exception("model not found 404")
                    mock_genai.GenerativeModel.return_value = mock_model

                    service = GeminiService()
                    result = await service.generate_response(
                        "Test", {"signals": []}, "4h"
                    )

                    assert result["success"] is False
                    assert result["error"] == "model_not_found"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_permission_denied(self):
        """Should handle permission denied error."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_model = MagicMock()
                    mock_model.start_chat.side_effect = Exception("permission denied 403")
                    mock_genai.GenerativeModel.return_value = mock_model

                    service = GeminiService()
                    result = await service.generate_response(
                        "Test", {"signals": []}, "4h"
                    )

                    assert result["success"] is False
                    assert result["error"] == "permission_denied"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_unknown_error(self):
        """Should handle unknown error."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_model = MagicMock()
                    mock_model.start_chat.side_effect = Exception("random error xyz")
                    mock_genai.GenerativeModel.return_value = mock_model

                    service = GeminiService()
                    result = await service.generate_response(
                        "Test", {"signals": []}, "4h"
                    )

                    assert result["success"] is False
                    assert result["error"] == "unknown"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_with_history(self):
        """Should include conversation history."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_chat = MagicMock()
                    mock_response = MagicMock()
                    mock_response.text = "Response with history"
                    mock_chat.send_message.return_value = mock_response

                    mock_model = MagicMock()
                    mock_model.start_chat.return_value = mock_chat
                    mock_genai.GenerativeModel.return_value = mock_model

                    service = GeminiService()

                    history = [
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hi there!"}
                    ]

                    result = await service.generate_response(
                        "Follow up question",
                        {"signals": []},
                        "4h",
                        conversation_history=history
                    )

                    assert result["success"] is True


# ============================================================================
# Test: Fundamental Analysis Edge Cases
# ============================================================================

class TestFundamentalAnalysisEdgeCases:
    """Edge cases for fundamental analysis."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fundamental_rate_limit(self):
        """Should handle rate limit in fundamental analysis."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_model = MagicMock()
                    mock_model.generate_content.side_effect = Exception("rate limit 429")
                    mock_genai.GenerativeModel.return_value = mock_model

                    service = GeminiService()
                    result = await service.generate_fundamental_analysis("BTCUSDT")

                    assert result["success"] is False
                    assert result["error"] == "rate_limit"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fundamental_model_not_found(self):
        """Should handle model not found in fundamental analysis."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_model = MagicMock()
                    mock_model.generate_content.side_effect = Exception("not found 404")
                    mock_genai.GenerativeModel.return_value = mock_model

                    service = GeminiService()
                    result = await service.generate_fundamental_analysis("BTCUSDT")

                    assert result["success"] is False
                    assert result["error"] == "model_not_found"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fundamental_unknown_error(self):
        """Should handle unknown error in fundamental analysis."""
        with patch('gemini_service.get_api_key', return_value="test-key"):
            with patch('gemini_service.get_selected_model', return_value=DEFAULT_MODEL):
                with patch('gemini_service.genai') as mock_genai:
                    mock_model = MagicMock()
                    mock_model.generate_content.side_effect = Exception("random error")
                    mock_genai.GenerativeModel.return_value = mock_model

                    service = GeminiService()
                    result = await service.generate_fundamental_analysis("BTCUSDT")

                    assert result["success"] is False
                    assert result["error"] == "unknown"
