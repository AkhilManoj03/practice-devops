"""
Database manager for the Combined Origami Service.

This module handles data operations for products with integrated votes.
"""

import json
import logging
from typing import Dict, List, Optional, Any

import psycopg2

from app.exceptions import ProductNotFoundError, DataPersistenceError

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
