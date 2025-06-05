# services.py
"""
Service layer for the Voting Service.

This module contains business logic services for managing votes and
interacting with external services like the catalogue API.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import httpx
from fastapi import HTTPException, status


class VotesService:
    """Service for managing votes data with file-based persistence."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._lock = asyncio.Lock()

    async def load_votes(self) -> Dict[str, Any]:
        """Load votes from file asynchronously."""
        try:
            if not self.file_path.exists():
                logging.debug(f"Votes file {self.file_path} does not exist, returning empty data")
                return {"origamis": {}}

            async with aiofiles.open(self.file_path, "r") as f:
                content = await f.read()
                data = json.loads(content)
                if not isinstance(data, dict) or "origamis" not in data:
                    raise ValueError("Invalid votes data format")
                
                logging.debug(f"Loaded votes data: {len(data.get('origamis', {}))} origamis")
                return data
        except (json.JSONDecodeError, OSError) as e:
            logging.error(f"Error loading votes from {self.file_path}: {e}")
            return {"origamis": {}}

    async def save_votes(self, votes_data: Dict[str, Any]) -> None:
        """Save votes to file asynchronously with file locking."""
        async with self._lock:
            try:
                self.file_path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
                async with aiofiles.open(self.file_path, "w") as f:
                    await f.write(json.dumps(votes_data, indent=2))
                logging.debug(f"Saved votes data to {self.file_path}")
            except OSError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error saving votes to {self.file_path}: {e}"
                )

    async def get_votes_for_origami(self, origami_id: int) -> int:
        """Get vote count for a specific origami."""
        votes_data = await self.load_votes()            
        vote_count = votes_data.get("origamis", {}).get(str(origami_id), 0)
        logging.debug(f"Retrieved {vote_count} votes for origami {origami_id}")
        return vote_count

    async def increment_vote(self, origami_id: int) -> int:
        """Increment vote count for an origami and return new count."""
        votes_data = await self.load_votes()
        votes_data["origamis"] = votes_data.get("origamis", {})
        
        origami_id_str = str(origami_id)
        votes_data["origamis"][origami_id_str] = (
            votes_data["origamis"].get(origami_id_str, 0) + 1
        )
        await self.save_votes(votes_data)
        
        new_count = votes_data["origamis"][origami_id_str]
        logging.info(f"Incremented votes for origami {origami_id} to {new_count} votes")
        return new_count

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
                products = response.json()
                logging.info(f"Successfully fetched {len(products)} products from catalogue")
                return products
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logging.warning("No products found in catalogue (404)")
                    return []
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Catalogue service error",
                )
            except httpx.RequestError as e:
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
                product = response.json()
                logging.debug(f"Successfully fetched product {product_id}: {product.get('name')}")
                return product
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logging.warning(f"Product {product_id} not found in catalogue")
                    return None
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Catalogue service error",
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Catalogue service unavailable",
                )


class OrigamiService:
    """High-level service that combines votes and catalogue data."""
    
    def __init__(self, votes_service: VotesService, catalogue_service: CatalogueService):
        self.votes_service = votes_service
        self.catalogue_service = catalogue_service
        logging.info("OrigamiService initialized")

    async def get_origami_with_votes(self, origami_id: int) -> Optional[Dict[str, Any]]:
        """Get origami data combined with vote count."""
        # Fetch product and votes concurrently
        product_task = self.catalogue_service.get_product(origami_id)
        votes_task = self.votes_service.get_votes_for_origami(origami_id) or 0
        product, votes = await asyncio.gather(product_task, votes_task)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Origami not found for id: {origami_id}",
            )
        if not votes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Votes not found for Origami with id: {origami_id}",
            )
        
        return {
            "id": product["id"],
            "name": product["name"],
            "description": product["description"],
            "image_url": product["image_url"],
            "votes": votes,
        }

    async def get_all_origamis_with_votes(self) -> List[Dict[str, Any]]:
        """Get all origamis with their vote counts."""
        # Fetch products and votes concurrently
        products_task = self.catalogue_service.get_all_products()
        votes_task = self.votes_service.load_votes()
        products, votes_data = await asyncio.gather(products_task, votes_task)

        if not products:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching products from catalogue",
            )
        
        if not votes_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error loading votes data",
            )
        
        # Combine product data with votes
        origamis = []
        for product in products:
            votes = votes_data.get("origamis", {}).get(str(product["id"]), 0)
            origamis.append({
                "id": product["id"],
                "name": product["name"],
                "description": product["description"],
                "image_url": product["image_url"],
                "votes": votes,
            })
        
        logging.info(f"Retrieved {len(origamis)} origamis with vote data")
        return origamis

    async def vote_for_origami(self, origami_id: int) -> Dict[str, Any]:
        """Vote for an origami and return updated data."""
        # Validate origami exists
        product = await self.catalogue_service.get_product(origami_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Origami not found for id: {origami_id}",
            )
        
        # Increment vote
        new_vote_count = await self.votes_service.increment_vote(origami_id)
        
        return {
            "origami_id": origami_id,
            "new_vote_count": new_vote_count,
            "message": f"Vote recorded for {product['name']}",
        }
