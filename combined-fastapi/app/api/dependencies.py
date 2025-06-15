"""
FastAPI dependencies for the Combined Origami Service.

This module contains dependency injection functions for services and shared resources.
"""

from config import settings
from infrastructure.data_access import data_access
from core.services import ProductService, VoteService, SystemService

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
