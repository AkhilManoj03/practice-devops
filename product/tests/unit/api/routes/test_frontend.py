"""
Unit tests for Frontend API routes.

This module contains comprehensive tests for the frontend routes,
including template rendering, JSON fallback, and error handling.
"""

import pytest
from unittest.mock import Mock, patch

from fastapi import Request
from fastapi.responses import JSONResponse

from api.routes.frontend import home
from core.models import SystemInfo


class TestHomeEndpoint:
    """Test suite for GET / endpoint."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI Request."""
        return Mock(spec=Request)

    @pytest.fixture
    def sample_system_info(self):
        """Create sample SystemInfo for testing."""
        return SystemInfo(
            hostname="test-host",
            ip_address="127.0.0.1",
            is_container=False,
            is_kubernetes=False,
        )

    @pytest.mark.asyncio
    async def test_home_with_templates_success(
        self, mock_request, mock_system_service, sample_system_info,
    ):
        """Test home endpoint with templates available and successful system info retrieval."""
        mock_system_service.get_system_info.return_value = sample_system_info

        with patch('api.routes.frontend.templates') as mock_templates, \
             patch('api.routes.frontend.settings') as mock_settings, \
             patch('api.routes.frontend.datetime') as mock_datetime:

            mock_settings.app_version = "1.0.0"
            mock_datetime.now.return_value.year = 2024

            expected_template_response = Mock()
            mock_templates.TemplateResponse.return_value = expected_template_response

            result = await home(mock_request, mock_system_service)

            mock_system_service.get_system_info.assert_called_once()

            mock_templates.TemplateResponse.assert_called_once_with(
                "index.html",
                {
                    "request": mock_request,
                    "current_year": 2024,
                    "system_info": sample_system_info.model_dump(),
                    "version": "1.0.0",
                },
            )

            assert result == expected_template_response

    @pytest.mark.asyncio
    async def test_home_without_templates_returns_json(
        self, mock_request, mock_system_service, sample_system_info,
    ):
        """Test home endpoint when templates are not available returns JSON response."""
        mock_system_service.get_system_info.return_value = sample_system_info

        with patch('api.routes.frontend.templates', None), \
             patch('api.routes.frontend.settings') as mock_settings:

            mock_settings.app_version = "1.0.0"

            result = await home(mock_request, mock_system_service)

            mock_system_service.get_system_info.assert_called_once()

            assert isinstance(result, JSONResponse)

            expected_content = {
                "message": "Welcome to Product Service",
                "version": "1.0.0",
                "system_info": sample_system_info.model_dump(),
            }

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_home_system_service_error_returns_error_json(
        self, mock_request, mock_system_service,
    ):
        """Test home endpoint when system service raises an error."""
        mock_system_service.get_system_info.side_effect = Exception("System service error")

        with patch('api.routes.frontend.templates', None), \
             patch('api.routes.frontend.settings') as mock_settings, \
             patch('api.routes.frontend.logging') as mock_logging:
            
            mock_settings.app_version = "1.0.0"

            result = await home(mock_request, mock_system_service)

            mock_system_service.get_system_info.assert_called_once()

            mock_logging.error.assert_called_once()
            log_call = mock_logging.error.call_args[0][0]
            assert "Error in home endpoint" in log_call
            assert "System service error" in log_call

            assert isinstance(result, JSONResponse)
            assert result.status_code == 200
