"""
API dependencies for the Combined Origami Service.

This module contains dependency injection functions for FastAPI.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request

from core.services import ProductService, VoteService, SystemService
from infrastructure.data_access import data_access
from config import settings

# JWT payload
def get_jwt_payload(request: Request) -> Optional[Dict[str, Any]]:
    """Get JWT payload from request state (set by middleware).
    
    Returns:
        Optional[Dict[str, Any]]: JWT payload if authenticated, None otherwise.
    """
    return getattr(request.state, 'jwt_payload', None)

def require_authentication(request: Request) -> Dict[str, Any]:
    """Require valid JWT token. 
    
    Returns:
        Dict[str, Any]: JWT payload if authenticated.

    Raises:
        HTTPException: If not authenticated.
    """
    jwt_payload = get_jwt_payload(request)
    
    if jwt_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return jwt_payload

def is_authenticated(request: Request) -> bool:
    """Check if the current request is authenticated.
    
    Returns:
        bool: True if the request is authenticated, False otherwise.
    """
    return getattr(request.state, 'is_authenticated', False)

# Service dependencies
def get_product_service() -> ProductService:
    """Get product service instance.
    
    Returns:
        ProductService: Configured product service.
    """
    return ProductService(data_access)

def get_vote_service() -> VoteService:
    """Get vote service instance.
    
    Returns:
        VoteService: Configured vote service.
    """
    return VoteService(data_access)

def get_system_service() -> SystemService:
    """Get system service instance.
    
    Returns:
        SystemService: Configured system service.
    """
    return SystemService(data_access, settings)
