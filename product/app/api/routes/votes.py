"""
Voting routes for the Combined Origami Service.

This module contains all voting-related API endpoints.
"""

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from core.models import Product, VoteResponse
from core.exceptions import ProductNotFoundError, DataValidationError, DataPersistenceError
from core.services import ProductService, VoteService
from api.dependencies import get_product_service, get_vote_service

router = APIRouter(prefix="/api", tags=["Origamis", "Votes"])

@router.get("/origamis", response_model=List[Product], tags=["Origamis"])
async def get_all_origamis(
    product_service: ProductService = Depends(get_product_service)
) -> List[Product]:
    """Get all origamis with their vote counts (alias for products)."""
    try:
        return await product_service.get_all_products()
    except DataPersistenceError as e:
        logging.error(f"Infrastructure error in get_all_origamis(): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to access origami data",
        )
    except ProductNotFoundError as e:
        logging.error(f"Origami not found in get_all_origamis(): {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Origami not found",
        )
    except Exception as e:
        logging.error(f"Unexpected error in get_all_origamis(): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )

@router.get("/origamis/{origami_id}", response_model=Product, tags=["Origamis"])
async def get_origami(
    origami_id: int,
    product_service: ProductService = Depends(get_product_service)
) -> Product:
    """Get a specific origami with its vote count (alias for product)."""
    try:
        return await product_service.get_product_by_id(origami_id)
    except DataPersistenceError as e:
        logging.error(f"Infrastructure error in get_origami({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to access origami data"
        )
    except DataValidationError as e:
        logging.error(f"Data validation error in get_origami({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error validating origami data",
        )
    except ProductNotFoundError as e:
        logging.error(f"Origami not found in get_origami({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Origami not found",
        )
    except Exception as e:
        logging.error(f"Unexpected error in get_origami({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )

@router.get("/origamis/{origami_id}/votes", tags=["Votes"])
async def get_votes(
    origami_id: int,
    vote_service: VoteService = Depends(get_vote_service),
) -> Dict[str, Any]:
    """Get votes for a specific origami."""
    try:
        return await vote_service.get_votes_for_product(origami_id)
    except DataValidationError as e:
        logging.error(f"Data validation error in get_votes({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error validating vote data"
        )
    except ProductNotFoundError as e:
        logging.error(f"Origami not found in get_votes({origami_id}): {e}")
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

@router.post("/origamis/{origami_id}/vote", response_model=VoteResponse, tags=["Votes"])
async def vote_for_origami(
    origami_id: int,
    vote_service: VoteService = Depends(get_vote_service)
) -> VoteResponse:
    """Vote for a specific origami."""
    try:
        return await vote_service.add_vote(origami_id)
    except DataPersistenceError as e:
        logging.error(f"Infrastructure error in vote_for_origami({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save vote data",
        )
    except DataValidationError as e:
        logging.error(f"Data validation error in vote_for_origami({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error validating vote data",
        )
    except ProductNotFoundError as e:
        logging.error(f"Origami not found in vote_for_origami({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Origami not found",
        )
    except Exception as e:
        logging.error(f"Unexpected error in vote_for_origami({origami_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
