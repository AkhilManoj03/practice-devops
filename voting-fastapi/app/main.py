"""
Voting Service API

A FastAPI service for managing origami voting with improved architecture,
error handling, and performance optimizations.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# Import from our modules
from app.config import settings
from app.models import OrigamiResponse, VoteResponse, HealthResponse
from app.services import VotesService, CatalogueService, OrigamiService


# Application setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logging.info("Starting Voting Service...")
    app.state.settings.debug_log()
    yield
    # Shutdown
    logging.info("Shutting down Voting Service...")


def create_app() -> FastAPI:
    """Application factory."""

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(levelname)s: %(message)s",
    )

    app = FastAPI(
        title="Voting Service",
        description="A service for managing origami voting",
        version=settings.version,
        lifespan=lifespan,
    )

    # Setup services
    votes_service = VotesService(settings.votes_file_path)
    catalogue_service = CatalogueService(
        settings.catalogue_service_url,
        settings.request_timeout,
    )
    origami_service = OrigamiService(votes_service, catalogue_service)

    # Setup templates
    base_dir = Path(__file__).parent
    templates = Jinja2Templates(directory=base_dir / settings.templates_dir)

    # Store services in app state
    app.state.votes_service = votes_service
    app.state.catalogue_service = catalogue_service
    app.state.origami_service = origami_service
    app.state.templates = templates
    app.state.settings = settings

    return app

# Create app instance
app = create_app()

# Routes
@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def root(request: Request):
    """Root endpoint showing welcome page."""
    return app.state.templates.TemplateResponse(
        "welcome.html",
        {"request": request},
    )

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    from datetime import datetime

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.version
    )

@app.get("/api/origamis", response_model=List[OrigamiResponse], tags=["Origamis"])
async def get_all_origamis():
    """Get all origamis with their vote counts."""
    origamis_data = await app.state.origami_service.get_all_origamis_with_votes()

    if not origamis_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching origamis from catalogue",
        )

    return [
        OrigamiResponse(
            id=origami["id"],
            name=origami["name"],
            description=origami["description"],
            image_url=origami["image_url"],
            votes=origami["votes"],
        )
        for origami in origamis_data
    ]

@app.get("/api/origamis/{origami_id}", response_model=OrigamiResponse, tags=["Origamis"])
async def get_origami(origami_id: int):
    """Get a specific origami with its vote count."""
    origami_data = await app.state.origami_service.get_origami_with_votes(origami_id)

    if not origami_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Origami not found for id: {origami_id}"
        )

    return OrigamiResponse(
        id=origami_data["id"],
        name=origami_data["name"],
        description=origami_data["description"],
        image_url=origami_data["image_url"],
        votes=origami_data["votes"],
    )

@app.get("/api/origamis/{origami_id}/votes", tags=["Votes"])
async def get_votes(origami_id: int):
    """Get votes for a specific origami."""
    votes = await app.state.votes_service.get_votes_for_origami(origami_id)
    return {"origami_id": origami_id, "votes": votes}

@app.post("/api/origamis/{origami_id}/vote", response_model=VoteResponse, tags=["Votes"])
async def vote_for_origami(origami_id: int):
    """Vote for a specific origami."""
    # Validate origami exists
    vote_data = await app.state.origami_service.vote_for_origami(origami_id)
    if not vote_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error voting for origami with id: {origami_id}",
        )

    return VoteResponse(
        origami_id=vote_data["origami_id"],
        new_vote_count=vote_data["new_vote_count"],
        message=vote_data["message"],
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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
    )
