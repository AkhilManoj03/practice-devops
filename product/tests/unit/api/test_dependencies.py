"""
Unit tests for API dependencies.

This module contains tests for API dependency injection functions,
including authentication and service dependencies.
"""

import pytest
from unittest.mock import Mock

from fastapi import HTTPException, status

from api.dependencies import (
    get_jwt_payload,
    require_authentication,
    is_authenticated,
    get_product_service,
    get_vote_service,
    get_system_service,
)
from core.services import ProductService, VoteService, SystemService


class TestAuthenticationDependencies:
    """Test suite for authentication-related dependencies."""

    def test_get_jwt_payload_authenticated_request(self, authenticated_request):
        """Test getting JWT payload from authenticated request."""
        expected_payload = {
            "sub": "testuser",
            "role": "user",
            "exp": 9999999999,
        }
        authenticated_request.state.jwt_payload = expected_payload

        result = get_jwt_payload(authenticated_request)

        assert result == expected_payload

    def test_get_jwt_payload_unauthenticated_request(self, mock_request):
        """Test getting JWT payload from unauthenticated request."""
        mock_request.state.jwt_payload = None

        result = get_jwt_payload(mock_request)

        assert result is None

    def test_get_jwt_payload_no_jwt_payload_attribute(self):
        """Test getting JWT payload when request state has no jwt_payload attribute."""
        request = Mock()
        request.state = Mock(spec=[])  # Empty spec means no attributes
        
        result = get_jwt_payload(request)
        
        # getattr with default None should return None for missing attributes
        assert result is None

    def test_require_authentication_authenticated_request(self, authenticated_request):
        """Test require_authentication with authenticated request."""
        expected_payload = {
            "sub": "testuser",
            "role": "user",
            "exp": 9999999999,
        }
        authenticated_request.state.jwt_payload = expected_payload

        result = require_authentication(authenticated_request)

        assert result == expected_payload

    def test_require_authentication_unauthenticated_request(self, mock_request):
        """Test require_authentication with unauthenticated request raises HTTPException."""
        mock_request.state.jwt_payload = None

        with pytest.raises(HTTPException) as exc_info:
            require_authentication(mock_request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Authentication required"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    def test_require_authentication_no_jwt_payload_attribute(self):
        """Test require_authentication when request state has no jwt_payload attribute."""
        request = Mock()
        request.state = Mock(spec=[])  # Empty spec means no attributes

        with pytest.raises(HTTPException) as exc_info:
            require_authentication(request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Authentication required"

    def test_is_authenticated_authenticated_request(self, authenticated_request):
        """Test is_authenticated with authenticated request."""
        authenticated_request.state.is_authenticated = True

        result = is_authenticated(authenticated_request)

        assert result is True

    def test_is_authenticated_unauthenticated_request(self, mock_request):
        """Test is_authenticated with unauthenticated request."""
        mock_request.state.is_authenticated = False

        result = is_authenticated(mock_request)

        assert result is False

    def test_is_authenticated_no_is_authenticated_attribute(self):
        """Test is_authenticated when request state has no is_authenticated attribute."""
        request = Mock()
        request.state = Mock(spec=[])  # Empty spec means no attributes

        result = is_authenticated(request)

        assert result is False

    def test_require_authentication_different_jwt_payloads(self):
        """Test require_authentication with different JWT payload structures."""
        test_cases = [
            {"sub": "admin", "role": "admin", "permissions": ["read", "write"]},
            {"sub": "user123", "role": "user", "exp": 1234567890},
            {"sub": "service", "role": "service", "scope": "api"},
        ]

        for payload in test_cases:
            request = Mock()
            request.state = Mock()
            request.state.jwt_payload = payload

            result = require_authentication(request)

            assert result == payload


class TestServiceDependencies:
    """Test suite for service dependency injection."""

    def test_get_product_service_returns_product_service_instance(self):
        """Test that get_product_service returns ProductService instance."""
        result = get_product_service()

        assert isinstance(result, ProductService)

    def test_get_vote_service_returns_vote_service_instance(self):
        """Test that get_vote_service returns VoteService instance."""
        result = get_vote_service()

        assert isinstance(result, VoteService)

    def test_get_system_service_returns_system_service_instance(self):
        """Test that get_system_service returns SystemService instance."""
        result = get_system_service()

        assert isinstance(result, SystemService)

    def test_service_dependencies_are_properly_configured(self):
        """Test that service dependencies are properly configured with data access."""
        product_service = get_product_service()
        vote_service = get_vote_service()
        system_service = get_system_service()

        # Verify services have data access layer
        assert hasattr(product_service, 'data_access')
        assert hasattr(vote_service, 'data_access')
        assert hasattr(system_service, 'data_access')

    def test_multiple_calls_return_new_instances(self):
        """Test that multiple calls to service dependencies return new instances."""
        product_service1 = get_product_service()
        product_service2 = get_product_service()

        vote_service1 = get_vote_service()
        vote_service2 = get_vote_service()

        system_service1 = get_system_service()
        system_service2 = get_system_service()

        # Services should be different instances (not singletons)
        assert product_service1 is not product_service2
        assert vote_service1 is not vote_service2
        assert system_service1 is not system_service2


class TestDependencyIntegration:
    """Integration tests for dependency combinations."""

    def test_authentication_flow_with_services(self, authenticated_request):
        """Test authentication flow combined with service dependencies."""
        # Set up authenticated request
        jwt_payload = {"sub": "testuser", "role": "user"}
        authenticated_request.state.jwt_payload = jwt_payload

        # Test authentication requirement
        auth_result = require_authentication(authenticated_request)
        assert auth_result == jwt_payload

        # Test service dependencies still work
        product_service = get_product_service()
        vote_service = get_vote_service()
        system_service = get_system_service()

        assert isinstance(product_service, ProductService)
        assert isinstance(vote_service, VoteService)
        assert isinstance(system_service, SystemService)

    def test_unauthenticated_flow_with_services(self, mock_request):
        """Test unauthenticated flow combined with service dependencies."""
        # Set up unauthenticated request
        mock_request.state.jwt_payload = None
        mock_request.state.is_authenticated = False

        # Test authentication check
        assert is_authenticated(mock_request) is False

        # Test authentication requirement fails
        with pytest.raises(HTTPException):
            require_authentication(mock_request)

        # Test service dependencies still work (for public endpoints)
        product_service = get_product_service()
        vote_service = get_vote_service()
        system_service = get_system_service()

        assert isinstance(product_service, ProductService)
        assert isinstance(vote_service, VoteService)
        assert isinstance(system_service, SystemService) 