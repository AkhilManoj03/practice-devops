"""
Voting Service API

A FastAPI service for managing origami voting with improved architecture,
error handling, and performance optimizations.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings

# Configuration
class Settings(BaseSettings):
    """Application settings with environment variable support."""
    catalogue_service_url: str = Field(
        default="http://catalogue:8000",
        description="URL of the catalogue service"
    )
    votes_file_path: str = Field(
        default="votes.json",
        description="Path to the votes JSON file"
    )
    templates_dir: str = Field(
        default="templates",
        description="Directory containing Jinja2 templates"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    request_timeout: float = Field(
        default=10.0,
        description="HTTP request timeout in seconds"
    )
    version: str = Field(
        default="1.0.1",
        description="API version"
    )

    model_config = ConfigDict(env_file="app/.env")

    def debug_log(self) -> None:
        """Log all settings at debug level."""
        logging.debug("Settings configuration:")
        for field_name, field in self.model_fields.items():
            value = getattr(self, field_name)
            description = field.description or field_name
            suffix = "s" if field_name == "request_timeout" else ""
            logging.debug(f"{description}: {value}{suffix}")

# Models
class Origami(BaseModel):
    """Base origami model."""
    name: str
    description: str
    image_url: str


class OrigamiResponse(Origami):
    """Origami response model with votes."""
    id: int
    votes: int

    model_config = ConfigDict(from_attributes=True)


class VoteResponse(BaseModel):
    """Vote operation response."""
    origami_id: int
    new_vote_count: int
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str


# Services
class VotesService:
    """Service for managing votes data."""
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._lock = asyncio.Lock()

    async def load_votes(self) -> Dict[str, Any]:
        """Load votes from file asynchronously."""
        try:
            if not self.file_path.exists():
                return {"origamis": {}}

            async with aiofiles.open(self.file_path, "r") as f:
                content = await f.read()
                return json.loads(content)
        except (json.JSONDecodeError, OSError) as e:
            logging.error(f"Error loading votes: {e}")
            return {"origamis": {}}

    async def save_votes(self, votes_data: Dict[str, Any]) -> None:
        """Save votes to file asynchronously with file locking."""
        async with self._lock:
            try:
                # Ensure directory exists
                self.file_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(self.file_path, "w") as f:
                    await f.write(json.dumps(votes_data, indent=2))
            except OSError as e:
                logging.error(f"Error saving votes: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save votes",
                )

    async def get_votes_for_origami(self, origami_id: int) -> int:
        """Get vote count for a specific origami."""
        votes_data = await self.load_votes()
        return votes_data.get("origamis", {}).get(str(origami_id), 0)

    async def increment_vote(self, origami_id: int) -> int:
        """Increment vote count for an origami and return new count."""
        votes_data = await self.load_votes()

        if "origamis" not in votes_data:
            votes_data["origamis"] = {}

        origami_id_str = str(origami_id)
        votes_data["origamis"][origami_id_str] = (
            votes_data["origamis"].get(origami_id_str, 0) + 1
        )
        await self.save_votes(votes_data)

        return votes_data["origamis"][origami_id_str]

class CatalogueService:
    """Service for interacting with the catalogue API."""
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Fetch all products from catalogue service."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/api/products")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return []
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Catalogue service error",
                )
            except httpx.RequestError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Catalogue service unavailable",
                )

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a specific product from catalogue service."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/products/{product_id}"
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Catalogue service error",
                )
            except httpx.RequestError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Catalogue service unavailable",
                )

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
    settings = Settings()

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

    # Setup templates
    base_dir = Path(__file__).parent
    templates = Jinja2Templates(directory=base_dir / settings.templates_dir)

    # Store services in app state
    app.state.votes_service = votes_service
    app.state.catalogue_service = catalogue_service
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
        version=app.state.settings.version
    )

@app.get("/api/origamis", response_model=List[OrigamiResponse], tags=["Origamis"])
async def get_all_origamis():
    """Get all origamis with their vote counts."""
    # Fetch products and votes concurrently
    products_task = app.state.catalogue_service.get_all_products()
    votes_task = app.state.votes_service.load_votes()

    products, votes_data = await asyncio.gather(products_task, votes_task)

    # Combine product data with votes
    origamis = []
    for product in products:
        votes = votes_data.get("origamis", {}).get(str(product["id"]), 0)
        origamis.append(
            OrigamiResponse(
                id=product["id"],
                name=product["name"],
                description=product["description"],
                image_url=product["image_url"],
                votes=votes,
            )
        )

    return origamis

@app.get("/api/origamis/{origami_id}", response_model=OrigamiResponse, tags=["Origamis"])
async def get_origami(origami_id: int):
    """Get a specific origami with its vote count."""
    # Fetch product and votes concurrently
    product_task = app.state.catalogue_service.get_product(origami_id)
    votes_task = app.state.votes_service.get_votes_for_origami(origami_id)

    product, votes = await asyncio.gather(product_task, votes_task)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Origami not found"
        )

    return OrigamiResponse(
        id=product["id"],
        name=product["name"],
        description=product["description"],
        image_url=product["image_url"],
        votes=votes,
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
    product = await app.state.catalogue_service.get_product(origami_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Origami not found",
        )

    # Increment vote
    new_vote_count = await app.state.votes_service.increment_vote(origami_id)

    return VoteResponse(
        origami_id=origami_id,
        new_vote_count=new_vote_count,
        message=f"Vote recorded for {product['name']}",
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
