"""
Product catalog routes for the Combined Origami Service.

This module contains all product-related API endpoints.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from core.models import Product
from core.exceptions import ProductNotFoundError, DataValidationError, DataPersistenceError
from core.services import ProductService
from api.dependencies import get_product_service

router = APIRouter(prefix="/api", tags=["Products"])

@router.get("/products", response_model=List[Product])
async def get_products(
    product_service: ProductService = Depends(get_product_service)
) -> List[Product]:
    """Get all products with their vote counts."""
    try:
        return await product_service.get_all_products()
    except DataPersistenceError as e:
        logging.error(f"Infrastructure error in get_products(): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to access product data",
        )
    except ProductNotFoundError as e:
        logging.error(f"Product not found in get_products(): {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Products not found",
        )
    except Exception as e:
        logging.error(f"Unexpected error in get_products(): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )

@router.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: int,
    product_service: ProductService = Depends(get_product_service)
) -> Product:
    """Get a specific product by ID with its vote count."""
    try:
        return await product_service.get_product_by_id(product_id)
    except DataPersistenceError as e:
        logging.error(f"Infrastructure error in get_product({product_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to access product data",
        )
    except DataValidationError as e:
        logging.error(f"Data validation error in get_product({product_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error validating product data",
        )
    except ProductNotFoundError as e:
        logging.error(f"Product not found in get_product({product_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    except Exception as e:
        logging.error(f"Unexpected error in get_product({product_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
