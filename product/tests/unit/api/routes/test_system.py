"""
Unit tests for system API endpoints.

This module contains comprehensive tests for the system routes including
system information and health check endpoints.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from fastapi import HTTPException

from api.routes.system import router, root_router, get_system_info_endpoint, health_check
from core.models.system import SystemInfo, HealthCheck
from core.services.system_service import SystemService


class TestSystemEndpoints:
    """Test class for system API endpoints."""

    @pytest.fixture
    def mock_system_service(self):
        """Create a mock SystemService."""
        service = Mock(spec=SystemService)
        service.get_system_info = AsyncMock()
        service.health_check = AsyncMock()
        return service

    @pytest.fixture
    def sample_system_info(self):
        """Create sample system info."""
        return SystemInfo(
            hostname="test-host",
            ip_address="192.168.1.100",
            is_container=True,
            is_kubernetes=False,
        )

    @pytest.fixture
    def sample_health_check(self):
        """Create sample health check response."""
        return HealthCheck(
            status="healthy",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            version="1.0.0",
        )

    @pytest.mark.asyncio
    async def test_get_system_info_success(self, mock_system_service, sample_system_info):
        """Test successful system info retrieval."""
        mock_system_service.get_system_info.return_value = sample_system_info

        result = await get_system_info_endpoint(system_service=mock_system_service)

        assert result == sample_system_info
        assert result.hostname == "test-host"
        assert result.ip_address == "192.168.1.100"
        assert result.is_container is True
        assert result.is_kubernetes is False
        mock_system_service.get_system_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_system_info_service_error(self, mock_system_service):
        """Test system info endpoint with service error."""
        mock_system_service.get_system_info.side_effect = Exception("Service error")

        with patch('api.routes.system.logging') as mock_logging:
            with pytest.raises(HTTPException) as exc_info:
                await get_system_info_endpoint(system_service=mock_system_service)

            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Unable to get system information"
            mock_logging.error.assert_called_once()
            mock_system_service.get_system_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_system_service, sample_health_check):
        """Test successful health check."""
        mock_system_service.health_check.return_value = sample_health_check

        result = await health_check(system_service=mock_system_service)

        assert result == sample_health_check
        assert result.status == "healthy"
        assert result.timestamp == datetime(2024, 1, 1, 12, 0, 0)
        assert result.version == "1.0.0"
        mock_system_service.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_service_error(self, mock_system_service):
        """Test health check endpoint with service error."""
        mock_system_service.health_check.side_effect = Exception("Health check failed")

        with patch('api.routes.system.logging') as mock_logging:
            with pytest.raises(HTTPException) as exc_info:
                await health_check(system_service=mock_system_service)

            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Unable to perform health check"
            mock_logging.error.assert_called_once()
            mock_system_service.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_status(self, mock_system_service):
        """Test health check with unhealthy status."""
        unhealthy_check = HealthCheck(
            status="unhealthy",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            version="1.0.0"
        )
        mock_system_service.health_check.return_value = unhealthy_check

        result = await health_check(system_service=mock_system_service)

        assert result.status == "unhealthy"
        assert result.timestamp == datetime(2024, 1, 1, 12, 0, 0)
        assert result.version == "1.0.0"
        mock_system_service.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_info_different_environments(self, mock_system_service):
        """Test system info with different environment configurations."""
        environments = [
            # Docker container
            SystemInfo(
                hostname="docker-host",
                ip_address="172.17.0.2",
                is_container=True,
                is_kubernetes=False,
            ),
            # Kubernetes pod
            SystemInfo(
                hostname="k8s-pod-123",
                ip_address="10.244.0.5",
                is_container=True,
                is_kubernetes=True,
            ),
            # Bare metal
            SystemInfo(
                hostname="bare-metal-host",
                ip_address="192.168.1.50",
                is_container=False,
                is_kubernetes=False,
            ),
        ]

        for env_info in environments:
            mock_system_service.get_system_info.return_value = env_info

            result = await get_system_info_endpoint(system_service=mock_system_service)

            assert result == env_info
            assert result.hostname == env_info.hostname
            assert result.ip_address == env_info.ip_address
            assert result.is_container == env_info.is_container
            assert result.is_kubernetes == env_info.is_kubernetes

    @pytest.mark.asyncio
    async def test_health_check_different_versions(self, mock_system_service):
        """Test health check with different version strings."""
        versions = ["1.0.0", "2.1.3", "0.1.0-beta", "dev-snapshot"]

        for version in versions:
            health_check_response = HealthCheck(
                status="healthy",
                timestamp=datetime(2024, 1, 1, 12, 0, 0),
                version=version,
            )
            mock_system_service.health_check.return_value = health_check_response

            result = await health_check(system_service=mock_system_service)

            assert result.version == version
            assert result.status == "healthy"


class TestSystemRouterIntegration:
    """Integration tests for system router configuration."""

    def test_system_router_configuration(self):
        """Test system router prefix and tags configuration."""
        assert router.prefix == "/api"
        assert "System" in router.tags

    def test_root_router_configuration(self):
        """Test root router configuration."""
        assert root_router.prefix == ""
        assert "Health" in root_router.tags

    def test_system_info_route_metadata(self):
        """Test system info route metadata."""
        routes = [route for route in router.routes if hasattr(route, 'path') and 'system-info' in route.path]
        assert len(routes) >= 1
        
        # Find the specific route
        system_info_route = None
        for route in router.routes:
            if hasattr(route, 'path') and route.path.endswith('/system-info'):
                system_info_route = route
                break
        
        assert system_info_route is not None
        assert "GET" in system_info_route.methods

    def test_health_check_route_metadata(self):
        """Test health check route metadata."""
        # Find the health check route
        health_route = None
        for route in root_router.routes:
            if hasattr(route, 'path') and route.path.endswith('/health'):
                health_route = route
                break
        
        assert health_route is not None
        assert "GET" in health_route.methods

    def test_system_routes_dependencies(self):
        """Test that system routes use correct dependencies."""
        # Test system info route exists
        system_info_route = None
        for route in router.routes:
            if hasattr(route, 'path') and route.path.endswith('/system-info'):
                system_info_route = route
                break
        assert system_info_route is not None
        
        # Test health check route exists
        health_route = None
        for route in root_router.routes:
            if hasattr(route, 'path') and route.path.endswith('/health'):
                health_route = route
                break
        assert health_route is not None


class TestSystemEndpointErrorHandling:
    """Test error handling scenarios for system endpoints."""

    @pytest.fixture
    def mock_system_service(self):
        """Create a mock SystemService."""
        service = Mock(spec=SystemService)
        service.get_system_info = AsyncMock()
        service.health_check = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_system_info_timeout_error(self, mock_system_service):
        """Test system info endpoint with timeout error."""
        mock_system_service.get_system_info.side_effect = TimeoutError("Request timeout")

        with patch('api.routes.system.logging') as mock_logging:
            with pytest.raises(HTTPException) as exc_info:
                await get_system_info_endpoint(system_service=mock_system_service)

            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Unable to get system information"
            mock_logging.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_connection_error(self, mock_system_service):
        """Test health check endpoint with connection error."""
        mock_system_service.health_check.side_effect = ConnectionError("Database connection failed")

        with patch('api.routes.system.logging') as mock_logging:
            with pytest.raises(HTTPException) as exc_info:
                await health_check(system_service=mock_system_service)

            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Unable to perform health check"
            mock_logging.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_info_multiple_errors(self, mock_system_service):
        """Test system info endpoint with various error types."""
        errors = [
            RuntimeError("Runtime error"),
            ValueError("Value error"),
            OSError("OS error"),
            Exception("Generic exception")
        ]

        for error in errors:
            mock_system_service.get_system_info.side_effect = error

            with patch('api.routes.system.logging') as mock_logging:
                with pytest.raises(HTTPException) as exc_info:
                    await get_system_info_endpoint(system_service=mock_system_service)

                assert exc_info.value.status_code == 500
                assert exc_info.value.detail == "Unable to get system information"
                mock_logging.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_multiple_errors(self, mock_system_service):
        """Test health check endpoint with various error types."""
        errors = [
            RuntimeError("Runtime error"),
            ValueError("Value error"),
            OSError("OS error"),
            Exception("Generic exception")
        ]

        for error in errors:
            mock_system_service.health_check.side_effect = error

            with patch('api.routes.system.logging') as mock_logging:
                with pytest.raises(HTTPException) as exc_info:
                    await health_check(system_service=mock_system_service)

                assert exc_info.value.status_code == 500
                assert exc_info.value.detail == "Unable to perform health check"
                mock_logging.error.assert_called_once()


class TestSystemEndpointLogging:
    """Test logging behavior for system endpoints."""

    @pytest.fixture
    def mock_system_service(self):
        """Create a mock SystemService."""
        service = Mock(spec=SystemService)
        service.get_system_info = AsyncMock()
        service.health_check = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_system_info_error_logging(self, mock_system_service):
        """Test that system info errors are properly logged."""
        test_error = Exception("Test error message")
        mock_system_service.get_system_info.side_effect = test_error

        with patch('api.routes.system.logging') as mock_logging:
            with pytest.raises(HTTPException):
                await get_system_info_endpoint(system_service=mock_system_service)

            # Verify logging was called with the correct error
            mock_logging.error.assert_called_once()
            call_args = mock_logging.error.call_args[0][0]
            assert "Unexpected error in get_system_info()" in call_args
            assert "Test error message" in call_args

    @pytest.mark.asyncio
    async def test_health_check_error_logging(self, mock_system_service):
        """Test that health check errors are properly logged."""
        test_error = Exception("Health check test error")
        mock_system_service.health_check.side_effect = test_error

        with patch('api.routes.system.logging') as mock_logging:
            with pytest.raises(HTTPException):
                await health_check(system_service=mock_system_service)

            # Verify logging was called with the correct error
            mock_logging.error.assert_called_once()
            call_args = mock_logging.error.call_args[0][0]
            assert "Unexpected error in health_check()" in call_args
            assert "Health check test error" in call_args

    @pytest.mark.asyncio
    async def test_system_info_no_logging_on_success(self, mock_system_service):
        """Test that successful system info calls don't log errors."""
        sample_system_info = SystemInfo(
            hostname="test-host",
            ip_address="192.168.1.100",
            is_container=True,
            is_kubernetes=False
        )
        mock_system_service.get_system_info.return_value = sample_system_info

        with patch('api.routes.system.logging') as mock_logging:
            result = await get_system_info_endpoint(system_service=mock_system_service)

            assert result == sample_system_info
            mock_logging.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_health_check_no_logging_on_success(self, mock_system_service):
        """Test that successful health checks don't log errors."""
        sample_health_check = HealthCheck(
            status="healthy",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            version="1.0.0"
        )
        mock_system_service.health_check.return_value = sample_health_check

        with patch('api.routes.system.logging') as mock_logging:
            result = await health_check(system_service=mock_system_service)

            assert result == sample_health_check
            mock_logging.error.assert_not_called() 