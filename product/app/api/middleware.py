"""
Custom middleware for the Combined Origami Service.

This module contains custom middleware functions and error handlers.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

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
