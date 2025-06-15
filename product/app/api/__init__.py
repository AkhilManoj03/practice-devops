"""
API layer for the Combined Origami Service.

This package contains all FastAPI routes, dependencies, and middleware.
"""

from .routes import (
    products_router,
    votes_router,
    system_router,
    root_router,
    frontend_router
)
from .middleware import http_exception_handler
from . import dependencies

__all__ = [
    "products_router",
    "votes_router", 
    "system_router",
    "root_router",
    "frontend_router",
    "http_exception_handler",
    "dependencies",
]
