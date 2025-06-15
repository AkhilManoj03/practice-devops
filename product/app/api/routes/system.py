"""
System routes for the Combined Origami Service.

This module contains all system-related API endpoints including health checks.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from core.models import SystemInfo, HealthCheck
from core.services import SystemService
from api.dependencies import get_system_service

router = APIRouter(prefix="/api", tags=["System"])
root_router = APIRouter(tags=["Health"])

@router.get("/system-info", response_model=SystemInfo)
async def get_system_info_endpoint(
    system_service: SystemService = Depends(get_system_service)
) -> SystemInfo:
    """Get system information."""
    try:
        return await system_service.get_system_info()
    except Exception as e:
        logging.error(f"Unexpected error in get_system_info(): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to get system information",
        )

@root_router.get("/health", response_model=HealthCheck)
async def health_check(
    system_service: SystemService = Depends(get_system_service)
) -> HealthCheck:
    """Health check endpoint."""
    try:
        return await system_service.health_check()
    except Exception as e:
        logging.error(f"Unexpected error in health_check(): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to perform health check",
        )
