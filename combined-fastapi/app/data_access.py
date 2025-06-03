"""
Data access layer for the Combined Origami Service.

This module handles data operations for products with integrated votes,
supporting both JSON file and database backends with Redis caching.
"""

import logging
from typing import Dict, List, Optional, Any

from app.config import settings
from app.exceptions import ProductNotFoundError, DataValidationError, DataPersistenceError
from app.cache_manager import CacheManager
from app.database_manager import DatabaseManager
from app.json_manager import JSONDataManager

class DataAccessLayer:
    """Main data access layer combining database/JSON operations with caching."""

    def __init__(self, settings):
        """Initialize the data access layer.

        Args:
            settings: Application settings.
        """
        self.settings = settings
        self.db_manager = DatabaseManager(settings) if settings.data_source == "database" else None
        self.json_manager = JSONDataManager(settings) if settings.data_source == "json" else None
        self.cache_manager = CacheManager(settings)

    def initialize(self) -> None:
        """Initialize data access layer.

        This method establishes necessary connections and loads initial data.

        Raises:
            DataPersistenceError: If initialization fails.
        """
        try:
            if self.db_manager:
                self.db_manager.connect()
            elif self.json_manager:
                self.json_manager.load_products()

            # Initialize cache connection
            self.cache_manager.connect()

        except Exception as e:
            logging.error(f"Failed to initialize data access layer: {e}")
            raise DataPersistenceError("Failed to initialize data access layer")

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.db_manager:
            self.db_manager.disconnect()
        elif self.json_manager:
            self.json_manager.save_products()
        self.cache_manager.disconnect()

    def get_products(self) -> List[Dict[str, Any]]:
        """Get all products with votes.

        Returns:
            List[Dict[str, Any]]: List of products with votes.

        Raises:
            DataPersistenceError: If data access fails.
        """
        # Always get all products from primary storage to ensure we have the complete, up-to-date list
        if self.db_manager:
            logging.debug("Products fetched from database")
            products = self.db_manager.get_products()
        else:
            logging.debug("Products fetched from JSON file")
            products = self.json_manager.get_products()

        return products

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID.

        Args:
            product_id (int): The ID of the product to retrieve.

        Returns:
            Optional[Dict[str, Any]]: Product data if found, None otherwise.

        Raises:
            DataValidationError: If the product_id is not positive.
            ProductNotFoundError: If no product exists with the given ID.
            DataPersistenceError: If data source is not initialized or access fails.
        """
        if product_id <= 0:
            raise DataValidationError("Product ID must be positive")

        # Try cache first
        cached_product = self.cache_manager.get_product(product_id)
        if cached_product:
            logging.debug(f"Product fetched from cache for product: {product_id}")
            return cached_product

        # If not in cache, get from primary storage
        if self.db_manager:
            logging.debug(f"Product fetched from database for product: {product_id}")
            product = self.db_manager.get_product_by_id(product_id)
        else:
            logging.debug(f"Product fetched from JSON file for product {product_id}")
            product = self.json_manager.get_product_by_id(product_id)

        if product is None:
            logging.error(f"Product with ID {product_id} not found in data source")
            raise ProductNotFoundError("Product not found in data source")

        # Cache the result
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
            DataValidationError: If the product_id is not positive.
            ProductNotFoundError: If no product exists with the given ID.
            DataPersistenceError: If data source is not initialized or access fails.
        """
        if product_id <= 0:
            raise DataValidationError("Product ID must be positive")

        # Try to get from cache first
        cached_product = self.cache_manager.get_product(product_id)
        if cached_product:
            logging.debug(f"Votes fetched from cache for product: {product_id}")
            return cached_product.get('votes', 0)

        # If not in cache, get from primary storage
        if self.db_manager:
            logging.debug(f"Votes fetched from database for product: {product_id}")
            votes = self.db_manager.get_votes_for_product(product_id)
        else:
            logging.debug(f"Votes fetched from JSON file for product: {product_id}")
            votes = self.json_manager.get_votes_for_product(product_id)

        return votes

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
            DataValidationError: If the product_id is not positive.
            ProductNotFoundError: If no product exists with the given ID.
            DataPersistenceError: If data source is not initialized or access fails.
        """
        # Update in primary storage first
        if self.db_manager:
            logging.debug(f"Votes added to database for product: {product_id}")
            product = self.db_manager.add_vote(product_id)
        else:
            logging.debug(f"Votes added to JSON file for product: {product_id}")
            product = self.json_manager.add_vote(product_id)

        # Invalidate cache entries
        self.cache_manager.invalidate_product(product_id)
        logging.debug(f"Product cache invalidated for product: {product_id}")
        return product

    def health_check(self) -> bool:
        """Check if data access layer is healthy.

        Returns:
            bool: True if healthy, False otherwise.
        """
        if self.db_manager:
            db_healthy = self.db_manager.check_connection()
        else:
            db_healthy = self.json_manager.is_loaded()

        cache_healthy = self.cache_manager.check_connection()

        return db_healthy and cache_healthy

# Global data access layer instance
data_access = DataAccessLayer(settings)
