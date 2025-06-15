"""
Data access layer for the Combined Origami Service.

This module handles data operations for products with integrated votes,
supporting database backend with Redis caching.
"""

import logging
from typing import Dict, List, Optional, Any

from config import settings
from core.exceptions import DataValidationError
from infrastructure.cache.cache_manager import CacheManager
from infrastructure.database.postgres_manager import PostgresManager

class DataAccessLayer:
    """Main data access layer combining database operations with caching."""

    def __init__(self, settings):
        """Initialize the data access layer.

        Args:
            settings: Application settings.
        """
        self.settings = settings
        self.db_manager = PostgresManager(settings)
        self.cache_manager = CacheManager(settings)

    def initialize(self) -> None:
        """Initialize data access layer.

        This method establishes necessary connections and loads initial data.

        Raises:
            DataPersistenceError: If initialization fails.
        """
        self.db_manager.connect()
        self.cache_manager.connect()

    def cleanup(self) -> None:
        """Clean up resources.
        
        Raises:
            DataPersistenceError: If data source is not initialized or access fails.
        """
        self.db_manager.disconnect()
        self.cache_manager.disconnect()

    def get_products(self) -> List[Dict[str, Any]]:
        """Get all products with votes.

        Returns:
            List[Dict[str, Any]]: List of products with votes.

        Raises:
            DataPersistenceError: If data access fails.
            ProductNotFoundError: If no products are found in the database.
        """
        # Always get all products from database to ensure we have the complete, up-to-date list
        return self.db_manager.get_products()

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID.

        Args:
            product_id (int): The ID of the product to retrieve.

        Returns:
            Optional[Dict[str, Any]]: Product data if found, None otherwise.

        Raises:
            DataPersistenceError: If data source is not initialized or access fails.
            DataValidationError: If the product_id is not positive.
            ProductNotFoundError: If no product exists with the given ID.
        """
        if product_id <= 0:
            raise DataValidationError("Product ID must be positive")

        # Try cache first if connected
        if self.cache_manager.is_connected:
            cached_product = self.cache_manager.get_product(product_id)
            if cached_product:
                logging.debug(f"Product fetched from cache for product: {product_id}")
                return cached_product

        # If not in cache, get from database
        product = self.db_manager.get_product_by_id(product_id)
        logging.debug(f"Product fetched from database for product: {product_id}")

        # Cache the result if connected
        if self.cache_manager.is_connected:
            self.cache_manager.set_product(product_id, product)
            logging.debug(f"Product cached for product: {product_id}")

        return product

    def get_votes_for_product(self, product_id: int) -> int:
        """Get vote count for a specific product.

        Args:
            product_id (int): The ID of the product to get votes for.

        Returns:
            int: The number of votes for the product.

        Raises:
            DataPersistenceError: If data source is not initialized or access fails.
            DataValidationError: If the product_id is not positive.
            ProductNotFoundError: If no product exists with the given ID.
        """
        if product_id <= 0:
            raise DataValidationError("Product ID must be positive")

        if self.cache_manager.is_connected:
            cached_product = self.cache_manager.get_product(product_id)
            if cached_product:
                logging.debug(f"Votes fetched from cache for product: {product_id}")
                return cached_product.get('votes', 0)

        logging.debug(f"Votes fetched from database for product: {product_id}")
        return self.db_manager.get_votes_for_product(product_id)

    def add_vote(self, product_id: int) -> Dict[str, Any]:
        """Add vote to product.

        Args:
            product_id (int): The ID of the product to vote for.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - origami_id: The ID of the voted product
                - new_vote_count: The updated vote count
                - message: A success message

        Raises:
            DataPersistenceError: If data source is not initialized or access fails.
            DataValidationError: If the product_id is not positive.
            ProductNotFoundError: If no product exists with the given ID.
        """
        if product_id <= 0:
            raise DataValidationError("Product ID must be positive")

        logging.debug(f"Votes added to database for product: {product_id}")
        product = self.db_manager.add_vote(product_id)

        # Invalidate cache if connected
        if self.cache_manager.is_connected:
            self.cache_manager.invalidate_product(product_id)
            logging.debug(f"Product cache invalidated for product: {product_id}")
        
        return product

    def health_check(self) -> bool:
        """Check if data access layer is healthy.

        Returns:
            bool: True if healthy, False otherwise.
        """
        db_healthy = self.db_manager.check_connection()
        cache_healthy = self.cache_manager.check_connection()

        return db_healthy and cache_healthy

# Global data access layer instance
data_access = DataAccessLayer(settings)
