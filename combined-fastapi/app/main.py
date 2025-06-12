"""
Combined Origami Service - A FastAPI application for product management and voting.

This service provides REST API endpoints for both product catalogue management
and voting functionality in a single unified service.
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

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import settings
from app.data_access import data_access
from app.models import Product, SystemInfo, HealthCheck, VoteResponse
from app.exceptions import ProductNotFoundError, DataValidationError, DataPersistenceError

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
        is_kubernetes=is_kubernetes,
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
    logging.info(f"Using data source: {settings.data_source}")

    # Initialize tracing
    resource = Resource.create({
        "service.name": os.environ.get("OTEL_SERVICE_NAME", "products-api"),
        "service.version": os.environ.get("APP_VERSION", "1.0.0"),
        "deployment.environment": "production",
    })
    tracer_provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(
        os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318/v1/traces"),
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Initialize data access layer
    try:
        data_access.initialize()
        logging.info(f"Data source '{settings.data_source}' initialized successfully") 

        products = data_access.get_products()
        logging.info(f"Loaded {len(products)} products from {settings.data_source}")

    except DataPersistenceError as e:
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

FastAPIInstrumentor.instrument_app(app)

# Mount static files and templates
if os.path.exists(settings.static_dir):
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
if os.path.exists(settings.templates_dir):
    templates = Jinja2Templates(directory=settings.templates_dir)
# API Routes

# ===== CATALOGUE SERVICE ENDPOINTS =====
@app.get("/", tags=["Frontend"])
async def home(request: Request):
    """Home page endpoint."""
    if not os.path.exists(settings.templates_dir):
        return JSONResponse(
            content={
                "message": "Welcome to Combined Origami Service",
                "version": settings.app_version,
                "system_info": get_system_info().model_dump(),
            }
        )

    system_info = get_system_info()   
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "current_year": datetime.now().year,
            "system_info": system_info.model_dump(),
            "version": settings.app_version,
        }
    )

@app.get("/api/products", response_model=List[Product], tags=["Products"])
async def get_products() -> List[Product]:
    """Get all products with their vote counts."""
    try:
        products_data = data_access.get_products()
        
        return [Product(**product) for product in products_data]

    except DataPersistenceError as e:
        logging.error(f"Infrastructure error in get_products(): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to access product data",
        )
    except Exception as e:
        logging.error(f"Unexpected error in get_products(): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )

@app.get("/api/products/{product_id}", response_model=Product, tags=["Products"])
async def get_product(product_id: int) -> Product:
    """Get a specific product by ID with its vote count."""
    try:
        product_data = data_access.get_product_by_id(product_id)
        return Product(**product_data)
    
    except ProductNotFoundError as e:
        logging.error(f"Product not found in get_product({product_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    except DataValidationError as e:
        logging.error(f"Data validation error in get_product({product_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error validating product data",
        )
    except DataPersistenceError as e:
        logging.error(f"Infrastructure error in get_product({product_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to access product data"
        )
    except Exception as e:
        logging.error(f"Unexpected error in get_product({product_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )

# ===== VOTING SERVICE ENDPOINTS =====
@app.get("/api/origamis", response_model=List[Product], tags=["Origamis"])
async def get_all_origamis():
    """Get all origamis with their vote counts (alias for products)."""
    return await get_products()

@app.get("/api/origamis/{origami_id}", response_model=Product, tags=["Origamis"])
async def get_origami(origami_id: int):
    """Get a specific origami with its vote count (alias for product)."""
    return await get_product(origami_id)

@app.get("/api/origamis/{origami_id}/votes", tags=["Votes"])
async def get_votes(origami_id: int):
    """Get votes for a specific origami."""
    try:
        votes = data_access.get_votes_for_product(origami_id)
        return {"origami_id": origami_id, "votes": votes}

    except DataValidationError as e:
        logging.error(f"Data validation error in get_votes({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error validating vote data"
        )
    except ProductNotFoundError as e:
        logging.error(f"Product not found in get_votes({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Origami not found",
        )
    except DataPersistenceError as e:
        logging.error(f"Infrastructure error in get_votes({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to access vote data"
        )
    except Exception as e:
        logging.error(f"Unexpected error in get_votes({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )

@app.post("/api/origamis/{origami_id}/vote", response_model=VoteResponse, tags=["Votes"])
async def vote_for_origami(origami_id: int):
    """Vote for a specific origami."""
    try:
        vote_data = data_access.add_vote(origami_id)
        return VoteResponse(**vote_data)

    except DataValidationError as e:
        logging.error(f"Data validation error in vote_for_origami({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error validating vote data",
        )
    except ProductNotFoundError as e:
        logging.error(f"Product not found in vote_for_origami({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Origami not found",
        )
    except DataPersistenceError as e:
        logging.error(f"Infrastructure error in vote_for_origami({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save vote data",
        )
    except Exception as e:
        logging.error(f"Unexpected error in vote_for_origami({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )

# ===== SYSTEM ENDPOINTS =====
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

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
        },
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