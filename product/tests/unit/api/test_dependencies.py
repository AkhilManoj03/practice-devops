"""
Unit tests for API dependencies.

This module contains tests for API dependency injection functions,
including authentication and service dependencies.
"""

import pytest

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

    def test_require_authentication_unauthenticated_request(self, mock_request):
        """Test require_authentication with unauthenticated request raises HTTPException."""
        mock_request.state.jwt_payload = None

        with pytest.raises(HTTPException) as exc_info:
            require_authentication(mock_request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Authentication required"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

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
