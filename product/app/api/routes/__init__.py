"""
API routes for the Combined Origami Service.

This module contains all FastAPI route definitions organized by domain.
"""

from .products import router as products_router
from .votes import router as votes_router
from .system import router as system_router, root_router
from .frontend import router as frontend_router

__all__ = [
    "products_router", 
    "votes_router", 
    "system_router", 
    "root_router", 
    "frontend_router",
]
