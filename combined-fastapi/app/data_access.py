"""
Data access layer for the Combined Origami Service.

This module handles data operations for products with integrated votes,
supporting both JSON file and database backends.
"""

import json
import logging
from typing import Dict, List, Optional, Any

from app.config import settings
from app.exceptions import ProductNotFoundError, DataValidationError, DataPersistenceError


class DataAccess:
    """Data access layer for products with integrated votes."""
    
    def __init__(self):
        self.products_data: List[Dict[str, Any]] = []
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the data access layer."""
        if self._initialized:
            return
            
        try:
            self._load_products()
            self._initialized = True
            logging.info("Data access layer initialized successfully")
        except Exception as e:
            # Log unexpected errors during initialization
            logging.error(f"Critical failure during data access initialization: {e}")
            raise DataPersistenceError(f"Data initialization failed: {e}")

    def _load_products(self) -> None:
        """Load products from JSON file."""
        products_file = settings.get_products_file_path()
        
        if not products_file.exists():
            logging.info(f"Products file not found: {products_file}, starting with empty data")
            self.products_data = []
            return
            
        try:
            with open(products_file, 'r', encoding='utf-8') as f:
                self.products_data = json.load(f)
            
            # Ensure all products have a votes field
            for product in self.products_data:
                if 'votes' not in product:
                    product['votes'] = 0
                    
            logging.info(f"Loaded {len(self.products_data)} products from {products_file}")
        except (OSError, json.JSONDecodeError) as e:
            raise DataPersistenceError(f"Failed to load products from {products_file}: {e}")

    def _save_products(self) -> None:
        """Save products to JSON file."""
        products_file = settings.get_products_file_path()
        
        try:
            # Ensure directory exists
            products_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(products_file, 'w', encoding='utf-8') as f:
                json.dump(self.products_data, f, indent=2)
            logging.debug(f"Products saved successfully to {products_file}")
        except OSError as e:
            raise DataPersistenceError(f"Failed to save products: {e}")

    def get_products(self) -> List[Dict[str, Any]]:
        """Get all products with their vote counts."""
        if not self._initialized:
            self.initialize()
            
        return [product.copy() for product in self.products_data]

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific product by ID with its vote count."""
        if not self._initialized:
            self.initialize()

        if product_id <= 0:
            raise DataValidationError("Product ID must be positive")

        product = next(
            (product.copy() for product in self.products_data if int(product["id"]) == product_id),
            None,
        )

        if product is None:
            raise ProductNotFoundError(f"Product with ID {product_id} not found")
        
        return product

    def get_votes_for_product(self, product_id: int) -> int:
        """Get vote count for a specific product."""
        if not self._initialized:
            self.initialize()

        if product_id <= 0:
            raise DataValidationError("Product ID must be positive")

        product = next(
            (
                product
                for product in self.products_data
                if int(product["id"]) == product_id
            ),
            None,
        )

        if product is None:
            raise ProductNotFoundError(f"Product with ID {product_id} not found")

        return product.get("votes", 0)

    def add_vote(self, product_id: int) -> Dict[str, Any]:
        """Add a vote for a product."""
        if not self._initialized:
            self.initialize()

        # Business logic validation
        if product_id <= 0:
            raise DataValidationError("Product ID must be positive")

        # Find product - raise business error if not found
        product_index = next(
            (i for i, p in enumerate(self.products_data) if int(p["id"]) == product_id),
            None
        )

        if product_index is None:
            raise ProductNotFoundError(f"Product with ID {product_id} not found")

        # Add vote
        current_votes = self.products_data[product_index].get("votes", 0)
        new_votes = current_votes + 1
        self.products_data[product_index]["votes"] = new_votes

        # Save products - handle I/O errors as infrastructure errors
        try:
            self._save_products()
        except DataPersistenceError:
            # Rollback the vote change
            self.products_data[product_index]["votes"] = current_votes
            logging.warning(f"Rolled back vote for product {product_id} due to save failure")
            raise

        logging.debug(f"Vote added for product {product_id}: {current_votes} -> {new_votes}")

        return {
            "origami_id": product_id,
            "new_vote_count": new_votes,
            "message": f"Vote added successfully for {self.products_data[product_index]['name']}"
        }

    def health_check(self) -> bool:
        """Check if the data access layer is healthy."""
        try:
            if not self._initialized:
                self.initialize()
            return True
        except Exception as e:
            # Log health check failures for monitoring
            logging.error(f"Health check failed: {e}")
            return False

    def cleanup(self) -> None:
        """Cleanup resources."""
        # Save any pending changes
        if self._initialized:
            try:
                self._save_products()
                logging.info("Data access cleanup completed successfully")
            except Exception as e:
                # Log cleanup failures as they're important for data integrity
                logging.error(f"Failed to save data during cleanup: {e}")


# Global data access instance
data_access = DataAccess() 