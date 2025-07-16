"""
Unit tests for SystemService.

This module contains comprehensive tests for the SystemService class,
focusing on system information gathering, health checks, and environment detection.
"""

import pytest
from unittest.mock import patch
from datetime import datetime

from core.services.system_service import SystemService
from core.models.system import SystemInfo, HealthCheck


class TestSystemService:
    """Test suite for SystemService class."""

    @pytest.fixture
    def system_service(self, mock_data_access, mock_settings):
        """Create a SystemService instance with mocked dependencies."""
        return SystemService(mock_data_access, mock_settings)

    @pytest.mark.asyncio
    @patch('socket.gethostname')
    @patch('socket.gethostbyname')
    @patch('os.path.exists')
    async def test_get_system_info_success(
        self, mock_exists, mock_gethostbyname, mock_gethostname, system_service
    ):
        """Test successful system information retrieval."""
        mock_gethostname.return_value = "test-hostname"
        mock_gethostbyname.return_value = "192.168.1.100"
        mock_exists.side_effect = lambda path: path == "/.dockerenv"  # Only docker, not k8s

        result = await system_service.get_system_info()

        assert isinstance(result, SystemInfo)
        assert result.hostname == "test-hostname"
        assert result.ip_address == "192.168.1.100"
        assert result.is_container is True
        assert result.is_kubernetes is False
        
        mock_gethostname.assert_called_once()
        mock_gethostbyname.assert_called_once_with("test-hostname")
        assert mock_exists.call_count == 2

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, system_service, mock_data_access, mock_settings):
        """Test health check when system is healthy."""
        mock_data_access.health_check.return_value = True
        mock_settings.app_version = "1.2.3"

        with patch('core.services.system_service.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            result = await system_service.health_check()

        assert isinstance(result, HealthCheck)
        assert result.status == "healthy"
        assert result.timestamp == mock_now
        assert result.version == "1.2.3"
        mock_data_access.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, system_service, mock_data_access, mock_settings):
        """Test health check when system is unhealthy."""
        mock_data_access.health_check.return_value = False
        mock_settings.app_version = "1.2.3"

        with patch('core.services.system_service.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            result = await system_service.health_check()

        assert result.status == "unhealthy"
        assert result.timestamp == mock_now
        assert result.version == "1.2.3"
        mock_data_access.health_check.assert_called_once()

    @pytest.mark.asyncio
    @patch('socket.gethostname')
    @patch('socket.gethostbyname')
    @patch('os.path.exists')
    async def test_system_info_model_validation(
        self, mock_exists, mock_gethostbyname, mock_gethostname, system_service
    ):
        """Test that SystemInfo model is properly created and validated."""
        mock_gethostname.return_value = "validation-test"
        mock_gethostbyname.return_value = "10.0.0.1"
        mock_exists.return_value = True

        result = await system_service.get_system_info()

        assert isinstance(result, SystemInfo)
        assert hasattr(result, 'hostname')
        assert hasattr(result, 'ip_address')
        assert hasattr(result, 'is_container')
        assert hasattr(result, 'is_kubernetes')
        assert isinstance(result.hostname, str)
        assert isinstance(result.ip_address, str)
        assert isinstance(result.is_container, bool)
        assert isinstance(result.is_kubernetes, bool)

    @pytest.mark.asyncio
    async def test_health_check_model_validation(
        self, system_service, mock_data_access, mock_settings
    ):
        """Test that HealthCheck model is properly created and validated."""
        mock_data_access.health_check.return_value = True
        mock_settings.app_version = "test-version"

        result = await system_service.health_check()

        assert isinstance(result, HealthCheck)
        assert hasattr(result, 'status')
        assert hasattr(result, 'timestamp')
        assert hasattr(result, 'version')
        assert isinstance(result.status, str)
        assert isinstance(result.timestamp, datetime)
        assert isinstance(result.version, str)
