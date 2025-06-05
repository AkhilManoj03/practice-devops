"""
Catalogue Service - A FastAPI application for product management.

This service provides REST API endpoints for product catalogue management
with support for both JSON file and PostgreSQL database backends.
"""

import logging
import os
import socket
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import from our modules
from app.config import settings
from app.database import data_access
from app.models import Product, SystemInfo, HealthCheck

# Utility Functions
def get_system_info() -> SystemInfo:
    """Get system information."""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
    except socket.error:
        hostname = "unknown"
        ip_address = "unknown"

    is_container = os.path.exists("/.dockerenv")
    is_kubernetes = os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount")

    return SystemInfo(
        hostname=hostname,
        ip_address=ip_address,
        is_container=is_container,
        is_kubernetes=is_kubernetes
    )

# Application Lifecycle Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(levelname)s: %(message)s",
    )
    if settings.log_level == "DEBUG":
        logging.getLogger().setLevel(logging.DEBUG)
        settings.debug_log()

    # Startup
    logging.info(f"Starting {settings.app_title} v{settings.app_version}")

    # Initialize data access layer
    try:
        data_access.initialize()
        logging.info(f"Data source '{settings.data_source}' initialized successfully")
    except RuntimeError as e:
        logging.error(f"Critical error during startup: {e}")
        raise RuntimeError(f"Failed to initialize data source: {e}")

    yield

    # Shutdown
    try:
        data_access.cleanup()
        logging.info("Data access layer cleaned up successfully")
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")

    logging.info(f"{settings.app_title} shutdown complete.")

# FastAPI Application
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan
)

# Mount static files and templates
if os.path.exists(settings.static_dir):
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
if os.path.exists(settings.templates_dir):
    templates = Jinja2Templates(directory=settings.templates_dir)

# API Routes
@app.get("/", tags=["Frontend"])
async def home(request: Request):
    """Home page endpoint."""
    if not os.path.exists(settings.templates_dir):
        return JSONResponse(
            content={
                "message": "Welcome to Catalogue Service",
                "version": settings.app_version,
                "system_info": get_system_info().model_dump()
            }
        )

    system_info = get_system_info()   
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "current_year": datetime.now().year,
            "system_info": system_info.model_dump(),
            "version": settings.app_version
        }
    )

@app.get("/api/products", response_model=List[Product], tags=["Products"])
async def get_products() -> List[Product]:
    """Get all products."""
    try:
        products_data = data_access.get_products()
        return [Product(**product) for product in products_data]
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accessing products for /api/products: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing products for /api/products: {e}"
        )

@app.get("/api/products/{product_id}", response_model=Product, tags=["Products"])
async def get_product(product_id: int) -> Product:
    """Get a specific product by ID."""
    try:
        product_data = data_access.get_product_by_id(product_id)
        if product_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        return Product(**product_data)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accessing product for /api/products/{product_id}: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing product data for /api/products/{product_id}: {e}"
        )

@app.get("/api/system-info", response_model=SystemInfo, tags=["System"])
async def get_system_info_endpoint() -> SystemInfo:
    """Get system information."""
    return get_system_info()

@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check() -> HealthCheck:
    """Health check endpoint."""
    # Check if data source is healthy
    is_healthy = data_access.health_check()
    
    return HealthCheck(
        status="healthy" if is_healthy else "unhealthy",
        timestamp=datetime.now(),
        version=settings.app_version
    )

# Application Entry Point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app" if __name__ == "__main__" else app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=True,
    )
