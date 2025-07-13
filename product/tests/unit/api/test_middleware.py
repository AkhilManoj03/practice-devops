"""
Unit tests for API middleware.

This module contains comprehensive tests for the JWT middleware and HTTP exception handler,
including token validation, JWKS fetching, and error handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

import httpx
import jwt
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from api.middleware import JWTMiddleware, http_exception_handler


# Global fixtures for middleware tests
@pytest.fixture
def mock_app():
    """Create a mock FastAPI app."""
    return Mock()

@pytest.fixture
def jwt_middleware(mock_app):
    """Create JWTMiddleware instance."""
    return JWTMiddleware(mock_app)

@pytest.fixture
def middleware_mock_request():
    """Create a mock FastAPI Request for middleware tests."""
    request = Mock(spec=Request)
    request.headers = {}
    request.state = Mock()
    return request

@pytest.fixture(scope="module")
def sample_jwks():
    """Create sample JWKS response."""
    return {
        "keys": [
            {
                "kid": "test-key-id",
                "kty": "RSA",
                "alg": "RS256",
                "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
                "e": "AQAB",
            }
        ]
    }

@pytest.fixture(scope="module")
def sample_jwt_payload():
    """Create sample JWT payload."""
    return {
        "sub": "testuser",
        "role": "user",
        "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.now().timestamp()),
    }


class TestJWTMiddleware:
    """Test suite for JWTMiddleware class."""

    def test_init(self, mock_app):
        """Test JWTMiddleware initialization."""
        middleware = JWTMiddleware(mock_app)
        
        assert middleware.jwks_cache == {}
        assert middleware.public_key_cache is None

    @pytest.mark.asyncio
    async def test_get_jwks_success_first_call(self, jwt_middleware, sample_jwks):
        """Test successful JWKS fetching on first call."""
        with patch('api.middleware.httpx.AsyncClient') as mock_client_class, \
             patch('api.middleware.settings') as mock_settings, \
             patch('api.middleware.logging') as mock_logging:
            
            mock_settings.auth_service_url = "http://auth-service"
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.json.return_value = sample_jwks
            mock_client.get.return_value = mock_response
            
            result = await jwt_middleware.get_jwks()
            
            assert result == sample_jwks
            assert jwt_middleware.jwks_cache == sample_jwks
            mock_client.get.assert_called_once_with("http://auth-service/.well-known/jwks.json")
            mock_response.raise_for_status.assert_called_once()
            mock_logging.debug.assert_called_once_with("JWKS fetched and cached successfully")

    @pytest.mark.asyncio
    async def test_get_jwks_cached_response(self, jwt_middleware, sample_jwks):
        """Test JWKS returns cached response on subsequent calls."""
        jwt_middleware.jwks_cache = sample_jwks
        
        with patch('api.middleware.httpx.AsyncClient') as mock_client_class:
            result = await jwt_middleware.get_jwks()
            
            assert result == sample_jwks
            mock_client_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_jwks_http_error(self, jwt_middleware):
        """Test JWKS fetching with HTTP error."""
        with patch('api.middleware.httpx.AsyncClient') as mock_client_class, \
             patch('api.middleware.settings') as mock_settings, \
             patch('api.middleware.logging') as mock_logging:
            
            mock_settings.auth_service_url = "http://auth-service"
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_client.get.side_effect = httpx.HTTPStatusError("404 Not Found", request=Mock(), response=Mock())
            
            with pytest.raises(HTTPException) as exc_info:
                await jwt_middleware.get_jwks()
            
            assert exc_info.value.status_code == 503
            assert exc_info.value.detail == "Authentication service unavailable"
            mock_logging.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_jwks_connection_error(self, jwt_middleware):
        """Test JWKS fetching with connection error."""
        with patch('api.middleware.httpx.AsyncClient') as mock_client_class, \
             patch('api.middleware.settings') as mock_settings, \
             patch('api.middleware.logging') as mock_logging:
            
            mock_settings.auth_service_url = "http://auth-service"
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_client.get.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(HTTPException) as exc_info:
                await jwt_middleware.get_jwks()
            
            assert exc_info.value.status_code == 503
            assert exc_info.value.detail == "Authentication service unavailable"
            mock_logging.error.assert_called_once()

    def test_jwk_to_pem_success(self, jwt_middleware):
        """Test successful JWK to PEM conversion."""
        jwk_key = {
            "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
            "e": "AQAB"
        }
        
        result = jwt_middleware.jwk_to_pem(jwk_key)
        
        assert isinstance(result, str)
        assert result.startswith("-----BEGIN PUBLIC KEY-----")
        assert result.endswith("-----END PUBLIC KEY-----\n")
        assert jwt_middleware.public_key_cache == result

    def test_jwk_to_pem_cached(self, jwt_middleware):
        """Test JWK to PEM returns cached result."""
        cached_pem = "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----\n"
        jwt_middleware.public_key_cache = cached_pem
        
        jwk_key = {"n": "test", "e": "AQAB"}
        result = jwt_middleware.jwk_to_pem(jwk_key)
        
        assert result == cached_pem

    @pytest.mark.asyncio
    async def test_verify_jwt_token_success(self, jwt_middleware, sample_jwks, sample_jwt_payload):
        """Test successful JWT token verification."""
        # Create a real JWT token for testing
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        token = jwt.encode(sample_jwt_payload, private_key, algorithm="RS256")
        
        with patch.object(jwt_middleware, 'get_jwks', return_value=sample_jwks), \
             patch('api.middleware.settings') as mock_settings, \
             patch.object(jwt_middleware, 'jwk_to_pem') as mock_jwk_to_pem, \
             patch('api.middleware.logging') as mock_logging:
            
            mock_settings.product_key_id = "test-key-id"
            
            # Mock the PEM conversion to return the public key
            public_key_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            mock_jwk_to_pem.return_value = public_key_pem
            
            result = await jwt_middleware.verify_jwt_token(token)
            
            assert result is not None
            assert result["sub"] == "testuser"
            assert result["role"] == "user"
            mock_logging.debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_jwt_token_no_keys(self, jwt_middleware):
        """Test JWT token verification with no keys in JWKS."""
        empty_jwks = {"keys": []}
        
        with patch.object(jwt_middleware, 'get_jwks', return_value=empty_jwks), \
             patch('api.middleware.logging') as mock_logging:
            
            result = await jwt_middleware.verify_jwt_token("test-token")
            
            assert result is None
            mock_logging.error.assert_called_once_with("No keys found in JWKS")

    @pytest.mark.asyncio
    async def test_verify_jwt_token_invalid_token(self, jwt_middleware, sample_jwks):
        """Test JWT token verification with invalid token."""
        with patch.object(jwt_middleware, 'get_jwks', return_value=sample_jwks), \
             patch('api.middleware.settings') as mock_settings, \
             patch.object(jwt_middleware, 'jwk_to_pem') as mock_jwk_to_pem, \
             patch('api.middleware.logging') as mock_logging:
            
            mock_settings.product_key_id = "test-key-id"
            mock_jwk_to_pem.return_value = "invalid-pem"
            
            result = await jwt_middleware.verify_jwt_token("invalid-token")
            
            assert result is None
            mock_logging.error.assert_called_once()
            assert "Invalid JWT token" in mock_logging.error.call_args[0][0]

    @pytest.mark.asyncio
    async def test_dispatch_with_valid_token(
        self, jwt_middleware, middleware_mock_request, sample_jwt_payload,
    ):
        """Test middleware dispatch with valid JWT token."""
        middleware_mock_request.headers = {"Authorization": "Bearer valid-token"}
        mock_call_next = AsyncMock()
        mock_response = Mock()
        mock_call_next.return_value = mock_response
        
        with patch.object(jwt_middleware, 'verify_jwt_token', return_value=sample_jwt_payload):
            result = await jwt_middleware.dispatch(middleware_mock_request, mock_call_next)
            
            assert result == mock_response
            assert middleware_mock_request.state.jwt_payload == sample_jwt_payload
            assert middleware_mock_request.state.is_authenticated is True
            mock_call_next.assert_called_once_with(middleware_mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_with_invalid_token(self, jwt_middleware, middleware_mock_request):
        """Test middleware dispatch with invalid JWT token."""
        middleware_mock_request.headers = {"Authorization": "Bearer invalid-token"}
        mock_call_next = AsyncMock()
        mock_response = Mock()
        mock_call_next.return_value = mock_response
        
        with patch.object(jwt_middleware, 'verify_jwt_token', return_value=None):
            result = await jwt_middleware.dispatch(middleware_mock_request, mock_call_next)
            
            assert result == mock_response
            assert middleware_mock_request.state.jwt_payload is None
            assert middleware_mock_request.state.is_authenticated is False
            mock_call_next.assert_called_once_with(middleware_mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_no_auth_header(self, jwt_middleware, middleware_mock_request):
        """Test middleware dispatch with no Authorization header."""
        middleware_mock_request.headers = {}
        mock_call_next = AsyncMock()
        mock_response = Mock()
        mock_call_next.return_value = mock_response
        
        result = await jwt_middleware.dispatch(middleware_mock_request, mock_call_next)
        
        assert result == mock_response
        assert middleware_mock_request.state.jwt_payload is None
        assert middleware_mock_request.state.is_authenticated is False
        mock_call_next.assert_called_once_with(middleware_mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_invalid_auth_header_format(
        self, jwt_middleware, middleware_mock_request,
    ):
        """Test middleware dispatch with invalid Authorization header format."""
        middleware_mock_request.headers = {"Authorization": "Basic invalid-format"}
        mock_call_next = AsyncMock()
        mock_response = Mock()
        mock_call_next.return_value = mock_response
        
        result = await jwt_middleware.dispatch(middleware_mock_request, mock_call_next)
        
        assert result == mock_response
        assert middleware_mock_request.state.jwt_payload is None
        assert middleware_mock_request.state.is_authenticated is False
        mock_call_next.assert_called_once_with(middleware_mock_request)

class TestMiddlewareIntegration:
    """Integration tests for middleware components."""

    @pytest.mark.asyncio
    async def test_jwt_middleware_full_flow(self, sample_jwks, sample_jwt_payload):
        """Test complete JWT middleware flow from token to response."""
        app = Mock()
        middleware = JWTMiddleware(app)
        
        # Create a real JWT token
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        token = jwt.encode(sample_jwt_payload, private_key, algorithm="RS256")
        
        request = Mock(spec=Request)
        request.headers = {"Authorization": f"Bearer {token}"}
        request.state = Mock()
        
        mock_call_next = AsyncMock()
        mock_response = Mock()
        mock_call_next.return_value = mock_response
        
        with patch.object(middleware, 'get_jwks', return_value=sample_jwks), \
             patch('api.middleware.settings') as mock_settings:
            
            mock_settings.product_key_id = "test-key-id"
            
            # Mock the JWK to PEM conversion
            public_key_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            with patch.object(middleware, 'jwk_to_pem', return_value=public_key_pem):
                result = await middleware.dispatch(request, mock_call_next)
                
                assert result == mock_response
                assert request.state.jwt_payload["sub"] == "testuser"
                assert request.state.is_authenticated is True

    @pytest.mark.asyncio
    async def test_middleware_error_handling_integration(self):
        """Test integration between middleware error handling and exception handler."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/test"
        
        # Test middleware raising HTTPException
        exc = HTTPException(status_code=503, detail="Authentication service unavailable")
        
        result = await http_exception_handler(request, exc)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 503
