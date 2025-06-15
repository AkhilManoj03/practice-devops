"""
Product service for the Combined Origami Service.

This module contains business logic for product-related operations.
"""

import logging
from typing import List

from core.models.products import Product
from core.exceptions import ProductNotFoundError, DataValidationError, DataPersistenceError

class ProductService:
    """Service class for product business logic."""

    def __init__(self, data_access):
        """Initialize the product service.

        Args:
            data_access: The data access layer instance.
        """
        self.data_access = data_access

    async def get_all_products(self) -> List[Product]:
        """Get all products with their vote counts.

        Returns:
            List[Product]: List of all products.

        Raises:
            DataPersistenceError: If data access fails.
            ProductNotFoundError: If no products are found in the database.
        """
        try:
            products_data = self.data_access.get_products()
            return [Product(**product) for product in products_data]
        except DataPersistenceError:
            logging.error("Infrastructure error in get_all_products()")
            raise
        except ProductNotFoundError:
            logging.error("No products found in get_all_products()")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in get_all_products(): {e}")
            raise Exception("An unexpected error occurred")

    async def get_product_by_id(self, product_id: int) -> Product:
        """Get a specific product by ID with its vote count.

        Args:
            product_id (int): The ID of the product to retrieve.

        Returns:
            Product: The requested product.

        Raises:
            DataPersistenceError: If data access fails.
            ProductNotFoundError: If no product exists with the given ID.
        """
        try:
            product_data = self.data_access.get_product_by_id(product_id)
            return Product(**product_data)
        except DataPersistenceError:
            logging.error(f"Infrastructure error in get_product_by_id({product_id})")
            raise
        except ProductNotFoundError:
            logging.error(f"Product not found for product in get_product_by_id({product_id})")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in get_product_by_id({product_id}): {e}")
            raise Exception("An unexpected error occurred")
