"""
Combined Origami Service - A FastAPI application for product management and voting.

This service provides REST API endpoints for both product catalogue management
and voting functionality in a single unified service with clean architecture.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from config import settings
from infrastructure.data_access import data_access
from core.exceptions import DataPersistenceError, ProductNotFoundError
from api import (
    products_router,
    votes_router,
    system_router,
    root_router,
    frontend_router,
    http_exception_handler
)
from api.middleware import JWTMiddleware

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
        logging.info("Database initialized successfully") 

        products = data_access.get_products()
        logging.info(f"Loaded {len(products)} products from database")
    except DataPersistenceError as e:
        logging.error(f"Failed to initialize data source: {e}")
        raise RuntimeError(f"Failed to initialize data source")
    except ProductNotFoundError as e:
        logging.error(f"Failed to load products: {e}")
        raise RuntimeError(f"Failed to load products")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise RuntimeError(f"Unexpected error occurred loading products")

    yield

    # Shutdown
    try:
        data_access.cleanup()
        logging.info("Data access layer cleaned up successfully")
    except DataPersistenceError as e:
        logging.error(f"Failed to cleanup data source: {e}")
        raise RuntimeError(f"Failed to cleanup data source")
    except Exception as e:
        logging.error(f"Unexpected error during cleanup: {e}")
        raise RuntimeError(f"Unexpected error occurred during cleanup")

    logging.info(f"{settings.app_title} shutdown complete.")

# FastAPI Application
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan
)

# Add OpenTelemetry instrumentation
FastAPIInstrumentor.instrument_app(app)

# Add JWT middleware
app.add_middleware(JWTMiddleware)

# Mount static files
static_dir = settings.get_static_dir()
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logging.info(f"Static files mounted from {static_dir}")

# Register routers
app.include_router(frontend_router)
app.include_router(products_router)
app.include_router(votes_router)
app.include_router(system_router)
app.include_router(root_router)

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)

# Application Entry Point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=True,
    )
