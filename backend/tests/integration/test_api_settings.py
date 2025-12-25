"""
Integration tests for /api/settings/* endpoints

These tests verify the API key and model settings management endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================================
# Test: API Key Status Endpoint
# ============================================================================

class TestApiKeyStatus:
    """Tests for GET /api/settings/apikey endpoint."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_apikey_not_configured(self, async_client):
        """Should return not configured when no API key exists."""
        with patch('main.get_api_key', return_value=None):
            with patch('main.get_api_key_source', return_value=None):
                response = await async_client.get('/api/settings/apikey')

        assert response.status_code == 200
        data = response.json()
        assert data['configured'] == False
        assert data['masked_key'] is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_apikey_configured_from_file(self, async_client):
        """Should return masked key when configured from file."""
        with patch('main.get_api_key', return_value='AIzaSyABCDEFGHIJKLMNOP'):
            with patch('main.get_api_key_source', return_value='file'):
                with patch('main.gemini_service') as mock_service:
                    mock_service.is_configured.return_value = True
                    response = await async_client.get('/api/settings/apikey')

        assert response.status_code == 200
        data = response.json()
        assert data['configured'] == True
        assert data['source'] == 'file'
        # Last 4 characters should be visible
        assert 'MNOP' in data['masked_key']

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_apikey_configured_from_env(self, async_client):
        """Should return masked key when configured from environment."""
        with patch('main.get_api_key', return_value='AIzaSyXYZ123456789'):
            with patch('main.get_api_key_source', return_value='env'):
                with patch('main.gemini_service') as mock_service:
                    mock_service.is_configured.return_value = True
                    response = await async_client.get('/api/settings/apikey')

        assert response.status_code == 200
        data = response.json()
        assert data['configured'] == True
        assert data['source'] == 'env'

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_apikey_disabled(self, async_client):
        """Should return disabled status when API key is disabled."""
        with patch('main.get_api_key', return_value=None):
            with patch('main.get_api_key_source', return_value='disabled'):
                response = await async_client.get('/api/settings/apikey')

        assert response.status_code == 200
        data = response.json()
        assert data['configured'] == False
        assert data['source'] == 'disabled'


# ============================================================================
# Test: Set API Key Endpoint
# ============================================================================

class TestSetApiKey:
    """Tests for POST /api/settings/apikey endpoint."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_apikey_empty_rejected(self, async_client):
        """Should reject empty API key."""
        response = await async_client.post(
            '/api/settings/apikey',
            json={'api_key': ''}
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] == False

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_apikey_whitespace_rejected(self, async_client):
        """Should reject whitespace-only API key."""
        response = await async_client.post(
            '/api/settings/apikey',
            json={'api_key': '   '}
        )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] == False

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_apikey_valid_key(self, async_client):
        """Should accept and validate valid API key."""
        with patch('main.validate_api_key') as mock_validate:
            mock_validate.return_value = {'valid': True, 'error': None}
            with patch('main.save_api_key', return_value=True):
                with patch('main.GeminiService') as MockService:
                    mock_instance = MagicMock()
                    mock_instance.is_configured.return_value = True
                    MockService.return_value = mock_instance

                    response = await async_client.post(
                        '/api/settings/apikey',
                        json={'api_key': 'AIzaSyValidApiKey12345'}
                    )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_apikey_invalid_key(self, async_client):
        """Should reject invalid API key."""
        with patch('main.validate_api_key') as mock_validate:
            mock_validate.return_value = {'valid': False, 'error': 'invalid_api_key'}

            response = await async_client.post(
                '/api/settings/apikey',
                json={'api_key': 'invalid-key'}
            )

        assert response.status_code == 400
        data = response.json()
        assert data['success'] == False


# ============================================================================
# Test: Delete API Key Endpoint
# ============================================================================

class TestDeleteApiKey:
    """Tests for DELETE /api/settings/apikey endpoint."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_apikey_success(self, async_client):
        """Should successfully delete API key."""
        with patch('main.disable_api_key', return_value=True):
            response = await async_client.delete('/api/settings/apikey')

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_apikey_failure(self, async_client):
        """Should handle deletion failure."""
        with patch('main.disable_api_key', return_value=False):
            response = await async_client.delete('/api/settings/apikey')

        # Should still return 200 but with error info
        assert response.status_code in [200, 500]


# ============================================================================
# Test: Models Endpoint
# ============================================================================

class TestModelsEndpoint:
    """Tests for /api/settings/models endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_models_list(self, async_client):
        """Should return list of available models."""
        with patch('main.get_available_models') as mock_models:
            mock_models.return_value = {
                'gemini-2.5-flash': {
                    'name': 'Gemini 2.5 Flash',
                    'description': 'Fast and efficient',
                    'tier': 'stable'
                }
            }
            with patch('main.get_selected_model', return_value='gemini-2.5-flash'):
                response = await async_client.get('/api/settings/models')

        assert response.status_code == 200
        data = response.json()
        assert 'models' in data
        assert 'current_model' in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_model_success(self, async_client):
        """Should successfully change model."""
        with patch('main.save_selected_model', return_value=True):
            with patch('main.GeminiService') as MockService:
                mock_instance = MagicMock()
                mock_instance.is_configured.return_value = True
                MockService.return_value = mock_instance

                response = await async_client.post(
                    '/api/settings/models',
                    json={'model': 'gemini-2.5-flash'}
                )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_set_model_empty_rejected(self, async_client):
        """Should reject empty model name."""
        response = await async_client.post(
            '/api/settings/models',
            json={'model': ''}
        )

        # Should be rejected
        assert response.status_code in [400, 422]


# ============================================================================
# Test: Response Structure
# ============================================================================

class TestResponseStructure:
    """Tests for consistent response structure."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_apikey_status_has_required_fields(self, async_client):
        """API key status should have all required fields."""
        with patch('main.get_api_key', return_value=None):
            with patch('main.get_api_key_source', return_value=None):
                response = await async_client.get('/api/settings/apikey')

        data = response.json()
        assert 'configured' in data
        assert 'masked_key' in data
        assert 'source' in data
        assert 'service_ready' in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_models_response_has_required_fields(self, async_client):
        """Models response should have required fields."""
        with patch('main.get_available_models', return_value={}):
            with patch('main.get_selected_model', return_value='test'):
                response = await async_client.get('/api/settings/models')

        data = response.json()
        assert 'models' in data
        assert 'current_model' in data
