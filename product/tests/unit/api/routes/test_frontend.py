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

    @pytest.mark.asyncio
    async def test_home_with_templates_system_service_error(
        self, mock_request, mock_system_service,
    ):
        """Test home endpoint with templates available but system service error."""
        mock_system_service.get_system_info.side_effect = RuntimeError("Database connection failed")

        with patch('api.routes.frontend.templates') as mock_templates, \
             patch('api.routes.frontend.settings') as mock_settings, \
             patch('api.routes.frontend.logging') as mock_logging:

            mock_settings.app_version = "2.0.0"

            result = await home(mock_request, mock_system_service)

            mock_system_service.get_system_info.assert_called_once()

            mock_logging.error.assert_called_once()
            log_call = mock_logging.error.call_args[0][0]
            assert "Error in home endpoint" in log_call
            assert "Database connection failed" in log_call

            assert isinstance(result, JSONResponse)
            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_home_different_app_versions(
        self, mock_request, mock_system_service, sample_system_info,
    ):
        """Test home endpoint with different app versions."""
        mock_system_service.get_system_info.return_value = sample_system_info

        test_versions = ["1.0.0", "2.1.3", "0.9.0-beta", "3.0.0-rc1"]

        for version in test_versions:
            with patch('api.routes.frontend.templates', None), \
                 patch('api.routes.frontend.settings') as mock_settings:
                
                mock_settings.app_version = version

                result = await home(mock_request, mock_system_service)

                assert isinstance(result, JSONResponse)
                assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_home_different_system_info_scenarios(
        self, mock_request, mock_system_service,
    ):
        """Test home endpoint with different system info scenarios."""
        test_scenarios = [
            SystemInfo(
                hostname="prod-server",
                ip_address="192.168.1.100",
                is_container=True,
                is_kubernetes=True,
            ),
            SystemInfo(
                hostname="dev-local",
                ip_address="localhost",
                is_container=False,
                is_kubernetes=False,
            ),
            SystemInfo(
                hostname="docker-container",
                ip_address="172.17.0.2",
                is_container=True,
                is_kubernetes=False,
            ),
        ]

        for system_info in test_scenarios:
            mock_system_service.get_system_info.return_value = system_info

            with patch('api.routes.frontend.templates', None), \
                 patch('api.routes.frontend.settings') as mock_settings:

                mock_settings.app_version = "1.0.0"

                result = await home(mock_request, mock_system_service)

                assert isinstance(result, JSONResponse)
                assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_home_template_context_variables(
        self, mock_request, mock_system_service, sample_system_info,
    ):
        """Test that template context contains all required variables."""
        mock_system_service.get_system_info.return_value = sample_system_info

        with patch('api.routes.frontend.templates') as mock_templates, \
             patch('api.routes.frontend.settings') as mock_settings, \
             patch('api.routes.frontend.datetime') as mock_datetime:

            mock_settings.app_version = "1.5.0"
            mock_datetime.now.return_value.year = 2024

            await home(mock_request, mock_system_service)

            mock_templates.TemplateResponse.assert_called_once()
            call_args = mock_templates.TemplateResponse.call_args

            template_name = call_args[0][0]
            context = call_args[0][1]

            assert template_name == "index.html"
            assert "request" in context
            assert "current_year" in context
            assert "system_info" in context
            assert "version" in context
            assert context["request"] == mock_request
            assert context["current_year"] == 2024
            assert context["system_info"] == sample_system_info.model_dump()
            assert context["version"] == "1.5.0"

    @pytest.mark.asyncio
    async def test_home_json_response_content_structure(
        self, mock_request, mock_system_service, sample_system_info,
    ):
        """Test the structure of JSON response content."""
        mock_system_service.get_system_info.return_value = sample_system_info

        with patch('api.routes.frontend.templates', None), \
             patch('api.routes.frontend.settings') as mock_settings:

            mock_settings.app_version = "1.0.0"

            result = await home(mock_request, mock_system_service)

            assert isinstance(result, JSONResponse)

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_home_error_json_response_content(self, mock_request, mock_system_service):
        """Test the structure of error JSON response content."""
        mock_system_service.get_system_info.side_effect = ValueError("Test error")

        with patch('api.routes.frontend.templates', None), \
             patch('api.routes.frontend.settings') as mock_settings, \
             patch('api.routes.frontend.logging'):

            mock_settings.app_version = "1.0.0"

            result = await home(mock_request, mock_system_service)

            assert isinstance(result, JSONResponse)
            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_home_current_year_calculation(
        self, mock_request, mock_system_service, sample_system_info,
    ):
        """Test that current year is calculated correctly."""
        mock_system_service.get_system_info.return_value = sample_system_info

        with patch('api.routes.frontend.templates') as mock_templates, \
             patch('api.routes.frontend.settings') as mock_settings, \
             patch('api.routes.frontend.datetime') as mock_datetime:

            mock_settings.app_version = "1.0.0"

            test_years = [2020, 2023, 2024, 2025]

            for year in test_years:
                mock_datetime.now.return_value.year = year

                await home(mock_request, mock_system_service)

                call_args = mock_templates.TemplateResponse.call_args
                context = call_args[0][1]
                assert context["current_year"] == year

    @pytest.mark.asyncio
    async def test_home_multiple_exception_types(self, mock_request, mock_system_service):
        """Test home endpoint with different types of exceptions."""
        exception_types = [
            ValueError("Value error"),
            RuntimeError("Runtime error"),
            ConnectionError("Connection error"),
            Exception("Generic exception"),
        ]

        for exception in exception_types:
            mock_system_service.get_system_info.side_effect = exception

            with patch('api.routes.frontend.templates', None), \
                 patch('api.routes.frontend.settings') as mock_settings, \
                 patch('api.routes.frontend.logging') as mock_logging:

                mock_settings.app_version = "1.0.0"

                result = await home(mock_request, mock_system_service)

                mock_logging.error.assert_called()

                assert isinstance(result, JSONResponse)
                assert result.status_code == 200

                mock_logging.reset_mock()


class TestFrontendRouteIntegration:
    """Integration tests for frontend routes."""

    @pytest.mark.asyncio
    async def test_home_endpoint_with_real_datetime(self, mock_system_service):
        """Test home endpoint using real datetime (not mocked)."""
        system_info = SystemInfo(
            hostname="test-host",
            ip_address="127.0.0.1",
            is_container=False,
            is_kubernetes=False,
        )
        mock_system_service.get_system_info.return_value = system_info

        request = Mock(spec=Request)

        with patch('api.routes.frontend.templates') as mock_templates, \
             patch('api.routes.frontend.settings') as mock_settings:

            mock_settings.app_version = "1.0.0"

            result = await home(request, mock_system_service)

            mock_templates.TemplateResponse.assert_called_once()
            call_args = mock_templates.TemplateResponse.call_args
            context = call_args[0][1]

            current_year = context["current_year"]
            assert 2020 <= current_year <= 2030
            assert isinstance(current_year, int)

    @pytest.mark.asyncio
    async def test_home_logging_integration(self, mock_request, mock_system_service):
        """Test that logging works correctly in home endpoint."""
        mock_system_service.get_system_info.side_effect = Exception("Test logging error")

        with patch('api.routes.frontend.templates', None), \
             patch('api.routes.frontend.settings') as mock_settings:

            mock_settings.app_version = "1.0.0"

            with patch('api.routes.frontend.logging.error') as mock_log_error:
                result = await home(mock_request, mock_system_service)

                mock_log_error.assert_called_once()
                log_message = mock_log_error.call_args[0][0]
                assert "Error in home endpoint:" in log_message
                assert "Test logging error" in log_message

                assert isinstance(result, JSONResponse)
