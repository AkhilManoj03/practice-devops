"""
JSON manager for the Combined Origami Service.

This module handles data operations for products with integrated votes using JSON files.
"""

import json
import logging
from typing import Dict, List, Optional, Any

from core.exceptions import ProductNotFoundError, DataPersistenceError, DataValidationError

class JSONDataManager:
    """Data manager for JSON file-based data source with votes support."""

    def __init__(self, settings):
        """Initialize the JSON data manager.

        Args:
            settings: Application settings containing JSON file configuration.
        """
        self.settings = settings
        self._products_cache: Optional[List[Dict[str, Any]]] = None

    def load_products(self) -> List[Dict[str, Any]]:
        """Load products from JSON file with error handling.

        Returns:
            List[Dict[str, Any]]: List of products loaded from the JSON file.

        Raises:
            DataPersistenceError: If there's an error reading or parsing the JSON file.
            DataValidationError: If the products file does not contain a list.
        """
        products_file = self.settings.get_products_file_path()

        if not products_file.exists():
            logging.info(f"Products file not found: {products_file}, starting with empty data")
            self._products_cache = []
            self.save_products()
            return []

        try:
            with open(products_file, 'r', encoding='utf-8') as f:
                products = json.load(f)

            if not isinstance(products, list):
                raise DataValidationError("Products file must contain a list")

            # Ensure all products have a votes field
            for product in products:
                if 'votes' not in product:
                    product['votes'] = 0

            self._products_cache = products
            logging.info(f"Loaded {len(products)} products from JSON file: {products_file}")
            return products
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load products from {products_file}: {e}")
            raise DataPersistenceError("Failed to load products from json file")
        except Exception as e:
            logging.error(f"Unexpected Error loading products: {e}")
            raise Exception("Unexpected Error loading products from json file")

    def save_products(self) -> None:
        """Save products to JSON file.

        Raises:
            DataPersistenceError: If there's an error writing to the JSON file.
        """
        if self._products_cache is None:
            return

        products_file = self.settings.get_products_file_path()

        try:
            # Ensure directory exists 
            products_file.parent.mkdir(parents=True, exist_ok=True)

            with open(products_file, 'w', encoding='utf-8') as f:
                json.dump(self._products_cache, f, indent=2)
            logging.debug(f"Products saved successfully to {products_file}")
        except OSError as e:
            logging.error(f"Failed to save products to {products_file}: {e}")
            raise DataPersistenceError("Failed to save products to json file")

    def get_products(self) -> List[Dict[str, Any]]:
        """Get all products from cache.

        Returns:
            List[Dict[str, Any]]: List of all products with their data.

        Raises:
            DataPersistenceError: If products are not loaded.
        """
        if self._products_cache is None:
            raise DataPersistenceError("Products not loaded. Call load_products() first.")
        return [product.copy() for product in self._products_cache]

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific product by ID from cache.

        Args:
            product_id (int): The ID of the product to retrieve.

        Returns:
            Optional[Dict[str, Any]]: Product data if found, None if not found.

        Raises:
            DataPersistenceError: If products are not loaded.
            ProductNotFoundError: If no product exists with the given ID.
        """
        if self._products_cache is None:
            raise DataPersistenceError("Products not loaded. Call load_products() first.")

        product = next(
            (product for product in self._products_cache 
             if product.get('id') == str(product_id)),
            None
        )
        if not product:
            logging.error(f"Product with ID {product_id} not found in cache")
            raise ProductNotFoundError("Product not found in cache")

        return product.copy()

    def get_votes_for_product(self, product_id: int) -> int:
        """Get vote count for a specific product from cache.

        Args:
            product_id (int): The ID of the product to get votes for.

        Returns:
            int: The number of votes for the product.

        Raises:
            ProductNotFoundError: If no product exists with the given ID.
            DataPersistenceError: If products are not loaded.
        """
        if self._products_cache is None:
            raise DataPersistenceError("Products not loaded. Call load_products() first.")

        product = next(
            (product for product in self._products_cache 
             if product.get('id') == str(product_id)),
            None
        )

        if product is None:
            logging.error(f"Product with ID {product_id} not found in cache")
            raise ProductNotFoundError("Product not found in cache")

        return product.get("votes", 0)

    def add_vote(self, product_id: int) -> Dict[str, Any]:
        """Add a vote for a product in the JSON cache.

        Args:
            product_id (int): The ID of the product to vote for.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - origami_id: The ID of the voted product
                - new_vote_count: The updated vote count
                - message: A success message

        Raises:
            ProductNotFoundError: If no product exists with the given ID.
            DataPersistenceError: If products are not loaded or saving fails.
        """
        if self._products_cache is None:
            raise DataPersistenceError("Products not loaded. Call load_products() first.")

        product_index = next(
            (i for i, p in enumerate(self._products_cache) 
             if p.get('id') == str(product_id)),
            None
        )

        if product_index is None:
            logging.error(f"Product with ID {product_id} not found in cache")
            raise ProductNotFoundError("Product not found in cache")

        current_votes = self._products_cache[product_index].get("votes", 0)
        new_votes = current_votes + 1
        self._products_cache[product_index]["votes"] = new_votes

        try:
            self.save_products()
        except DataPersistenceError:
            self._products_cache[product_index]["votes"] = current_votes
            logging.warning(f"Rolled back vote for product {product_id} due to save failure")
            raise DataPersistenceError("Failed to save products to json file")

        logging.debug(f"Vote added for product {product_id}: {current_votes} -> {new_votes}")

        return {
            "origami_id": product_id,
            "new_vote_count": new_votes,
            "message": f"Vote added successfully for {self._products_cache[product_index]['name']}"
        }

    def is_loaded(self) -> bool:
        """Check if products are loaded in cache.

        Returns:
            bool: True if products are loaded, False otherwise.
        """
        return self._products_cache is not None
