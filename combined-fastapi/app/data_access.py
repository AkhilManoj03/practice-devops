"""
Data access layer for the Combined Origami Service.

This module handles data operations for products with integrated votes,
supporting both JSON file and database backends with Redis caching.
"""

import json
import logging
from typing import Dict, List, Optional, Any

import psycopg2
from fastapi import HTTPException, status

from app.config import settings
from app.exceptions import ProductNotFoundError, DataValidationError, DataPersistenceError


class DatabaseManager:
    """Database connection and operations manager for PostgreSQL with votes support."""

    def __init__(self, settings):
        """Initialize the database manager.
        
        Args:
            settings: Application settings containing database configuration.
        """
        self.settings = settings
        self.connection: Optional[psycopg2.extensions.connection] = None

    def connect(self) -> None:
        """Establish database connection.
        
        This method connects to the PostgreSQL database using settings from the configuration.
        It also initializes the database schema if needed.
        
        Raises:
            DataPersistenceError: If connection fails or schema initialization fails.
        """
        if self.settings.data_source != "database":
            return
     
        try:
            self.connection = psycopg2.connect(
                host=self.settings.db_host,
                database=self.settings.db_name,
                user=self.settings.db_user,
                password=self.settings.db_password,
                port=self.settings.db_port
            )
            logging.info(f"Database connection established to {self.settings.db_host}:{self.settings.db_port}")
            
            # Ensure the database schema is set up
            self._initialize_schema()
        except psycopg2.Error as e:
            logging.error(f"Failed to connect to database: {e}")
            raise DataPersistenceError("Failed to connect to database")

    def _initialize_schema(self) -> None:
        """Initialize database schema for products with votes.
        
        Creates the products table and necessary indexes if they don't exist.
        If the table is newly created, populates it with initial data from products.json.
        
        Raises:
            DataPersistenceError: If schema initialization fails.
        """
        if not self.connection:
            return
            
        try:
            with self.connection.cursor() as cursor:
                # Check if table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'products'
                    )
                """)
                table_exists = cursor.fetchone()[0]

                # Create products table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        image_url VARCHAR(500),
                        votes INTEGER DEFAULT 0
                    )
                """)

                # Create index on id for faster lookups
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_products_id ON products(id)
                """)

                if table_exists:
                    self.connection.commit()
                    logging.info("Database schema initialized successfully")
                    return
        except psycopg2.Error as e:
            logging.error(f"Failed to initialize database schema: {e}")
            raise DataPersistenceError("Failed to initialize database schema")

        # Load initial data from JSON file
        products_file = self.settings.get_products_file_path()
        try:
            with open(products_file, 'r', encoding='utf-8') as f:
                products = json.load(f)

            if not isinstance(products, list):
                raise ValueError("Products file must contain a list")

            # Ensure all products have a votes field
            for product in products:
                if 'votes' not in product:
                    product['votes'] = 0

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load initial products from {products_file}: {e}")
            raise DataPersistenceError("Failed to load initial products from json file")

        # Insert initial products into database
        try:
            with self.connection.cursor() as cursor:
                for product in products:
                    cursor.execute("""
                        INSERT INTO products (id, name, description, image_url, votes)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        product['id'],
                        product['name'],
                        product['description'],
                        product['image_url'],
                        product.get('votes', 0)
                    ))
                self.connection.commit()
                logging.info(f"Inserted {len(products)} initial products into database")
                logging.info("Database schema initialized successfully")
        except psycopg2.Error as e:
            logging.error(f"Failed to insert initial products: {e}")
            raise DataPersistenceError("Failed to insert initial products into database")

    def disconnect(self) -> None:
        """Close database connection.
        
        Raises:
            DataPersistenceError: If connection closure fails.
        """
        if not self.connection:
            return
        try:
            self.connection.close()
            self.connection = None
            logging.info("Database connection closed successfully")
        except Exception as e:
            logging.error(f"Error closing database connection: {e}")
            raise DataPersistenceError("Error closing database connection")

    def check_connection(self) -> bool:
        """Check if database connection is active.
        
        Returns:
            bool: True if connection is active and can execute queries, False otherwise.
        """
        if not self.connection:
            return False
        try:
            # Test the connection with a simple query
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except psycopg2.Error:
            return False

    def get_products(self) -> List[Dict[str, Any]]:
        """Fetch all products from database with votes.
        
        Returns:
            List[Dict[str, Any]]: List of products, each containing id, name, description,
                                 image_url, and votes.
        
        Raises:
            DataPersistenceError: If database connection is not established or query fails.
        """
        if not self.connection:
            raise DataPersistenceError("Database connection not established")

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT id, name, description, image_url, votes FROM products ORDER BY id")
                rows = cursor.fetchall()

                logging.info(f"Fetched {len(rows)} products from database") 
                return [
                    {
                        "id": str(row[0]),
                        "name": row[1],
                        "description": row[2],
                        "image_url": row[3],
                        "votes": row[4] or 0,
                    }
                    for row in rows
                ]
        except psycopg2.Error as e:
            logging.error(f"Database error in get_products: {e}")
            raise DataPersistenceError("Error fetching products from database")

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single product by ID from database with votes.
        
        Args:
            product_id (int): The ID of the product to retrieve.
            
        Returns:
            Optional[Dict[str, Any]]: Product data if found, None if not found.
            
        Raises:
            DataPersistenceError: If database connection is not established or query fails.
        """
        if not self.connection:
            raise DataPersistenceError("Database connection not established")

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, description, image_url, votes FROM products WHERE id = %s",
                    (product_id,)
                )
                row = cursor.fetchone()
                if not row:
                    logging.error(f"Product with ID {product_id} not found in database")
                    return None
                
                return {
                    "id": str(row[0]),
                    "name": row[1],
                    "description": row[2],
                    "image_url": row[3],
                    "votes": row[4] or 0,
                }
        except psycopg2.Error as e:
            logging.error(f"Database error in get_product_by_id: {e}")
            raise DataPersistenceError("Error fetching product from database")

    def get_votes_for_product(self, product_id: int) -> int:
        """Get vote count for a specific product from database.
        
        Args:
            product_id (int): The ID of the product to get votes for.
            
        Returns:
            int: The number of votes for the product.
            
        Raises:
            ProductNotFoundError: If no product exists with the given ID.
            DataPersistenceError: If database connection is not established or query fails.
        """
        if not self.connection:
            raise DataPersistenceError("Database connection not established")

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT votes FROM products WHERE id = %s", (product_id,))
                row = cursor.fetchone()
                if not row:
                    logging.error(f"Product with ID {product_id} not found in database")
                    raise ProductNotFoundError("Product not found in database")
                
                return row[0] or 0
        except psycopg2.Error as e:
            logging.error(f"Database error in get_votes_for_product: {e}")
            raise DataPersistenceError("Error fetching votes for product from database")

    def add_vote(self, product_id: int) -> Dict[str, Any]:
        """Add a vote for a product in the database.
        
        Args:
            product_id (int): The ID of the product to vote for.
            
        Returns:
            Dict[str, Any]: A dictionary containing:
                - origami_id: The ID of the voted product
                - new_vote_count: The updated vote count
                - message: A success message
            
        Raises:
            ProductNotFoundError: If no product exists with the given ID.
            DataPersistenceError: If database connection is not established or query fails.
        """
        if not self.connection:
            raise DataPersistenceError("Database connection not established")

        try:
            with self.connection.cursor() as cursor:
                # Check if product exists and get current info
                cursor.execute("SELECT name, votes FROM products WHERE id = %s", (product_id,))
                row = cursor.fetchone()
                if not row:
                    logging.error(f"Product with ID {product_id} not found in database")
                    raise ProductNotFoundError("Product not found in database")
                
                product_name, current_votes = row
                new_votes = (current_votes or 0) + 1
                
                # Update vote count
                cursor.execute(
                    "UPDATE products SET votes = %s WHERE id = %s",
                    (new_votes, product_id),
                )
                
                self.connection.commit()
                logging.debug(f"Vote added for product {product_id}: {current_votes or 0} -> {new_votes}")
                
                return {
                    "origami_id": product_id,
                    "new_vote_count": new_votes,
                    "message": f"Vote added successfully for {product_name}",
                }
        except psycopg2.Error as e:
            if self.connection:
                self.connection.rollback()
            logging.error(f"Error adding vote to database for product {product_id}: {e}")
            raise DataPersistenceError("Error adding vote to database for product")


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
                raise ValueError("Products file must contain a list")

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
            raise DataPersistenceError("Unexpected Error loading products from json file")

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
        """
        if self._products_cache is None:
            raise DataPersistenceError("Products not loaded. Call load_products() first.")
        
        # Handle both string and int IDs for flexibility
        product = next(
            (product for product in self._products_cache 
             if product.get('id') == str(product_id)),
            None
        )
        if not product:
            logging.error(f"Product with ID {product_id} not found in cache")
            return None
        
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

        # Find product index
        product_index = next(
            (i for i, p in enumerate(self._products_cache) 
             if p.get('id') == str(product_id)),
            None
        )

        if product_index is None:
            logging.error(f"Product with ID {product_id} not found in cache")
            raise ProductNotFoundError("Product not found in cache")

        # Add vote
        current_votes = self._products_cache[product_index].get("votes", 0)
        new_votes = current_votes + 1
        self._products_cache[product_index]["votes"] = new_votes

        # Save products - handle I/O errors as infrastructure errors
        try:
            self.save_products()
        except DataPersistenceError:
            # Rollback the vote change
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
