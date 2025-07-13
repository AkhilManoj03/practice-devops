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
    @patch('socket.gethostname')
    @patch('socket.gethostbyname')
    @patch('os.path.exists')
    async def test_get_system_info_kubernetes_environment(
        self, mock_exists, mock_gethostbyname, mock_gethostname, system_service
    ):
        """Test system info in Kubernetes environment."""
        mock_gethostname.return_value = "pod-12345"
        mock_gethostbyname.return_value = "10.0.0.50"
        mock_exists.side_effect = lambda path: True  # Both docker and k8s files exist

        result = await system_service.get_system_info()

        assert result.hostname == "pod-12345"
        assert result.ip_address == "10.0.0.50"
        assert result.is_container is True
        assert result.is_kubernetes is True

    @pytest.mark.asyncio
    @patch('socket.gethostname')
    @patch('socket.gethostbyname')
    @patch('os.path.exists')
    async def test_get_system_info_bare_metal(
        self, mock_exists, mock_gethostbyname, mock_gethostname, system_service
    ):
        """Test system info on bare metal (no container)."""
        mock_gethostname.return_value = "bare-metal-server"
        mock_gethostbyname.return_value = "172.16.0.10"
        mock_exists.return_value = False  # No container files

        result = await system_service.get_system_info()

        assert result.hostname == "bare-metal-server"
        assert result.ip_address == "172.16.0.10"
        assert result.is_container is False
        assert result.is_kubernetes is False

    @pytest.mark.asyncio
    @patch('socket.gethostname')
    @patch('socket.gethostbyname')
    @patch('os.path.exists')
    async def test_get_system_info_socket_error_hostname(
        self, mock_exists, mock_gethostbyname, mock_gethostname, system_service
    ):
        """Test system info when hostname resolution fails."""
        mock_gethostname.side_effect = OSError("Hostname resolution failed")
        mock_exists.return_value = False

        result = await system_service.get_system_info()

        assert result.hostname == "unknown"
        assert result.ip_address == "unknown"
        assert result.is_container is False
        assert result.is_kubernetes is False

    @pytest.mark.asyncio
    @patch('socket.gethostname')
    @patch('socket.gethostbyname')
    @patch('os.path.exists')
    async def test_get_system_info_socket_error_ip_address(
        self, mock_exists, mock_gethostbyname, mock_gethostname, system_service
    ):
        """Test system info when IP address resolution fails."""
        mock_gethostname.return_value = "test-hostname"
        mock_gethostbyname.side_effect = OSError("IP resolution failed")
        mock_exists.return_value = False

        result = await system_service.get_system_info()

        assert result.hostname == "unknown"
        assert result.ip_address == "unknown"
        assert result.is_container is False
        assert result.is_kubernetes is False

    @pytest.mark.asyncio
    @patch('socket.gethostname')
    @patch('socket.gethostbyname')
    @patch('os.path.exists')
    async def test_get_system_info_partial_socket_error(
        self, mock_exists, mock_gethostbyname, mock_gethostname, system_service
    ):
        """Test system info when only hostname works but IP fails."""
        mock_gethostname.return_value = "test-hostname"
        mock_gethostbyname.side_effect = OSError("IP resolution failed")
        mock_exists.return_value = True

        result = await system_service.get_system_info()

        assert result.hostname == "unknown"
        assert result.ip_address == "unknown"
        assert result.is_container is True
        assert result.is_kubernetes is True

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
    async def test_health_check_with_different_versions(self, system_service, mock_data_access, mock_settings):
        """Test health check with different app versions."""
        mock_data_access.health_check.return_value = True
        mock_settings.app_version = "2.0.0-beta"

        with patch('core.services.system_service.datetime') as mock_datetime:
            mock_now = datetime(2023, 6, 15, 14, 30, 0)
            mock_datetime.now.return_value = mock_now
            
            result = await system_service.health_check()

        assert result.status == "healthy"
        assert result.version == "2.0.0-beta"
        assert result.timestamp == mock_now

    @pytest.mark.asyncio
    @patch('socket.gethostname')
    @patch('socket.gethostbyname')
    @patch('os.path.exists')
    async def test_container_detection_logic(
        self, mock_exists, mock_gethostbyname, mock_gethostname, system_service
    ):
        """Test container detection logic with various file combinations."""
        mock_gethostname.return_value = "test-host"
        mock_gethostbyname.return_value = "127.0.0.1"

        # Test cases: (dockerenv_exists, k8s_exists, expected_container, expected_k8s)
        test_cases = [
            (True, True, True, True),    # K8s pod (both files exist)
            (True, False, True, False),  # Docker container only
            (False, True, False, True),  # K8s without docker (edge case)
            (False, False, False, False) # Bare metal
        ]

        for dockerenv_exists, k8s_exists, expected_container, expected_k8s in test_cases:
            mock_exists.side_effect = lambda path: (
                dockerenv_exists if path == "/.dockerenv" 
                else k8s_exists if path == "/var/run/secrets/kubernetes.io/serviceaccount"
                else False
            )

            result = await system_service.get_system_info()

            assert result.is_container == expected_container, f"Container detection failed for dockerenv={dockerenv_exists}, k8s={k8s_exists}"
            assert result.is_kubernetes == expected_k8s, f"K8s detection failed for dockerenv={dockerenv_exists}, k8s={k8s_exists}"

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

    def test_service_initialization(self, mock_data_access, mock_settings):
        """Test that SystemService initializes correctly with dependencies."""
        service = SystemService(mock_data_access, mock_settings)

        assert service.data_access == mock_data_access
        assert service.settings == mock_settings

    def test_service_initialization_with_none_dependencies(self):
        """Test that SystemService can be initialized with None dependencies."""
        service = SystemService(None, None)

        assert service.data_access is None
        assert service.settings is None

    @pytest.mark.asyncio
    async def test_multiple_health_checks(self, system_service, mock_data_access, mock_settings):
        """Test multiple health check calls."""
        mock_data_access.health_check.return_value = True
        mock_settings.app_version = "1.0.0"

        result1 = await system_service.health_check()
        result2 = await system_service.health_check()

        assert result1.status == "healthy"
        assert result2.status == "healthy"
        assert result1.version == result2.version
        assert mock_data_access.health_check.call_count == 2

    @pytest.mark.asyncio
    @patch('socket.gethostname')
    @patch('socket.gethostbyname')
    @patch('os.path.exists')
    async def test_multiple_system_info_calls(
        self, mock_exists, mock_gethostbyname, mock_gethostname, system_service
    ):
        """Test multiple system info calls return consistent results."""
        mock_gethostname.return_value = "consistent-host"
        mock_gethostbyname.return_value = "192.168.1.1"
        mock_exists.return_value = False

        result1 = await system_service.get_system_info()
        result2 = await system_service.get_system_info()

        assert result1.hostname == result2.hostname
        assert result1.ip_address == result2.ip_address
        assert result1.is_container == result2.is_container
        assert result1.is_kubernetes == result2.is_kubernetes
 