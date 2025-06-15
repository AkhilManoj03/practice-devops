"""
Frontend routes for the Combined Origami Service.

This module contains all frontend template rendering endpoints.
"""

import os
import logging
from datetime import datetime

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from config import settings
from core.services import SystemService
from api.dependencies import get_system_service

router = APIRouter(tags=["Frontend"])
if os.path.exists(settings.get_templates_dir()):
    templates = Jinja2Templates(directory=settings.get_templates_dir())

@router.get("/")
async def home(
    request: Request,
    system_service: SystemService = Depends(get_system_service)
):
    """Home page endpoint."""
    try:
        system_info = await system_service.get_system_info()

        # If templates directory doesn't exist, return JSON response
        if not templates:
            return JSONResponse(
                content={
                    "message": "Welcome to Combined Origami Service",
                    "version": settings.app_version,
                    "system_info": system_info.model_dump(),
                }
            )

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "current_year": datetime.now().year,
                "system_info": system_info.model_dump(),
                "version": settings.app_version,
            }
        )
    except Exception as e:
        logging.error(f"Error in home endpoint: {e}")
        return JSONResponse(
            content={
                "message": "Welcome to Combined Origami Service",
                "version": settings.app_version,
                "error": "Could not load system information",
            }
        )
