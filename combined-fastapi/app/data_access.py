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
        """Initialize the DataAccess instance.
        
        This creates an empty products list and sets the initialized flag to False.
        """
        self.products_data: List[Dict[str, Any]] = []
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the data access layer.
        
        This method loads products from the JSON file and sets up the data access layer.
        It should be called before any other operations.
        
        Raises:
            DataPersistenceError: If there's an error loading the products file.
        """
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
        """Load products from JSON file.
        
        This method reads the products from the configured JSON file and ensures
        all products have a votes field initialized to 0.
        
        Raises:
            DataPersistenceError: If there's an error reading or parsing the JSON file.
        """
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
        """Save products to JSON file.
        
        This method writes the current products data to the configured JSON file.
        
        Raises:
            DataPersistenceError: If there's an error writing to the JSON file.
        """
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
        """Get all products with their vote counts.
        
        Returns:
            List[Dict[str, Any]]: A list of all products, each containing their data and vote count.
            
        Raises:
            DataPersistenceError: If there's an error accessing the products data.
        """
        if not self._initialized:
            self.initialize()
            
        return [product.copy() for product in self.products_data]

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific product by ID with its vote count.
        
        Args:
            product_id (int): The ID of the product to retrieve.
            
        Returns:
            Optional[Dict[str, Any]]: The product data if found, None otherwise.
            
        Raises:
            DataValidationError: If the product_id is not positive.
            ProductNotFoundError: If no product exists with the given ID.
            DataPersistenceError: If there's an error accessing the products data.
        """
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
        """Get vote count for a specific product.
        
        Args:
            product_id (int): The ID of the product to get votes for.
            
        Returns:
            int: The number of votes for the product.
            
        Raises:
            DataValidationError: If the product_id is not positive.
            ProductNotFoundError: If no product exists with the given ID.
            DataPersistenceError: If there's an error accessing the products data.
        """
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
        """Add a vote for a product.
        
        Args:
            product_id (int): The ID of the product to vote for.
            
        Returns:
            Dict[str, Any]: A dictionary containing the vote operation result with:
                - origami_id: The ID of the voted product
                - new_vote_count: The updated vote count
                - message: A success message
            
        Raises:
            DataValidationError: If the product_id is not positive.
            ProductNotFoundError: If no product exists with the given ID.
            DataPersistenceError: If there's an error saving the vote.
        """
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
        """Check if the data access layer is healthy.
        
        Returns:
            bool: True if the data access layer is healthy, False otherwise.
        """
        try:
            if not self._initialized:
                self.initialize()
            return True
        except Exception as e:
            # Log health check failures for monitoring
            logging.error(f"Health check failed: {e}")
            return False

    def cleanup(self) -> None:
        """Cleanup resources.
        
        This method saves any pending changes and performs necessary cleanup.
        
        Raises:
            DataPersistenceError: If there's an error saving data during cleanup.
        """
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