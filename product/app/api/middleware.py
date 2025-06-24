"""
Custom middleware for the Combined Origami Service.

This module contains custom middleware functions and error handlers.
"""

import logging
import httpx
import jwt
import base64
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from config import settings

class JWTMiddleware(BaseHTTPMiddleware):
    """Middleware to handle JWT token validation."""
    
    def __init__(self, app):
        super().__init__(app)
        self.jwks_cache: Dict[str, Any] = {}
        self.public_key_cache: Optional[str] = None
    
    async def get_jwks(self) -> Dict[str, Any]:
        """Fetch and cache JWKS from authentication service."""
        if self.jwks_cache:
            return self.jwks_cache
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.auth_service_url}/.well-known/jwks.json")
                response.raise_for_status()
                self.jwks_cache = response.json()
                logging.debug("JWKS fetched and cached successfully")
                return self.jwks_cache
        except Exception as e:
            logging.error(f"Failed to fetch JWKS: {e}")
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable",
            )

    def jwk_to_pem(self, jwk_key: Dict[str, Any]) -> str:
        """Convert JWK RSA key to PEM format."""
        if self.public_key_cache:
            return self.public_key_cache
        
        try:
            # Decode base64url-encoded modulus and exponent
            modulus_bytes = base64.urlsafe_b64decode(jwk_key["n"] + "===")
            exponent_bytes = base64.urlsafe_b64decode(jwk_key["e"] + "===")
            
            # Convert bytes to integers
            modulus = int.from_bytes(modulus_bytes, byteorder='big')
            exponent = int.from_bytes(exponent_bytes, byteorder='big')
            
            # Create RSA public key
            public_key = rsa.RSAPublicNumbers(exponent, modulus).public_key(default_backend())
            
            # Convert to PEM format using the public_key_bytes method
            pem_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            self.public_key_cache = pem_bytes.decode('utf-8')
            return self.public_key_cache
        except Exception as e:
            logging.error(f"Failed to convert JWK to PEM: {e}")
            raise

    async def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return claims if valid."""
        try:
            jwks = await self.get_jwks()
            
            if not jwks.get("keys"):
                logging.error("No keys found in JWKS")
                return None
            
            key_info = jwks["keys"][0]
            
            # Verify this is the expected key id
            if not key_info.get("kid") == settings.product_key_id:
                logging.error(f"Invalid key ID in JWKS. Expected: {settings.product_key_id}, Got: {key_info.get('kid')}")
                return None
            
            # Verify this is an RSA key for RS256
            if key_info.get("kty") != "RSA" or key_info.get("alg") != "RS256":
                logging.error(f"Invalid key type or algorithm. Expected RSA/RS256, Got: {key_info.get('kty')}/{key_info.get('alg')}")
                return None
            
            # Convert JWK to PEM format for PyJWT
            public_key_pem = self.jwk_to_pem(key_info)
            
            # Verify and decode token using RSA public key
            payload = jwt.decode(
                token,
                public_key_pem,
                algorithms=["RS256"],
                options={"verify_signature": True, "verify_exp": True},
            )
            
            logging.debug(f"JWT token verified for user: {payload.get('sub')}")
            return payload
        except jwt.ExpiredSignatureError:
            logging.error("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logging.error(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logging.error(f"JWT verification error: {e}")
            return None
    
    async def dispatch(self, request: Request, call_next):
        """Process request with JWT validation."""
        # Extract JWT token from Authorization header
        auth_header = request.headers.get("Authorization")
        jwt_payload = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            jwt_payload = await self.verify_jwt_token(token)
        
        # Store JWT payload in request state for use in route handlers
        request.state.jwt_payload = jwt_payload
        request.state.is_authenticated = jwt_payload is not None
        
        # Continue with request processing
        response = await call_next(request)
        return response

async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler.
    
    Args:
        request: The FastAPI request object.
        exc: The HTTP exception.
        
    Returns:
        JSONResponse: Formatted error response.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
        },
    )
