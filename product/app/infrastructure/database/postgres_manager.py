"""
PostgreSQL database manager for the Combined Origami Service.

This module handles data operations for products with integrated votes using PostgreSQL.
"""

import json
import logging
from typing import Dict, List, Optional, Any

import psycopg2

from core.exceptions import DataPersistenceError, ProductNotFoundError

class PostgresManager:
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

        try:
            self.connection = psycopg2.connect(
                host=self.settings.postgres_host,
                database=self.settings.postgres_db,
                user=self.settings.postgres_user,
                password=self.settings.postgres_password,
                port=self.settings.postgres_port
            )
            logging.info(f"Database connection established to {self.settings.postgres_host}:{self.settings.postgres_port}")
        except psycopg2.Error as e:
            logging.error(f"Failed to connect to database: {e}")
            raise DataPersistenceError("Failed to connect to database")
        except Exception as e:
            logging.error(f"Unexpected error in connect(): {e}")
            raise Exception("Unexpected error connecting to database")

    
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
            # Test connection with a simple query
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except psycopg2.Error:
            return False

    def get_products(self) -> List[Dict[str, Any]]:
        """Fetch all products from database with votes.

        Returns:
            List[Dict[str, Any]]: List of products

        Raises:
            DataPersistenceError: If database connection is not established or query fails.
            ProductNotFoundError: If no products are found in the database.
        """
        if not self.connection:
            raise DataPersistenceError("Database connection not established")

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, description, image_url, votes FROM products ORDER BY id"
                )
                rows = cursor.fetchall()
                if not rows or len(rows) == 0:
                    raise ProductNotFoundError("No products found in database")

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
            ProductNotFoundError: If no product exists with the given ID.
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
                    logging.error(f"Product with ID {product_id} not found in database in get_product_by_id()")
                    raise ProductNotFoundError("Product not found in database")
                
                return {
                    "id": str(row[0]),
                    "name": row[1],
                    "description": row[2],
                    "image_url": row[3],
                    "votes": row[4] or 0,
                }
        except psycopg2.Error as e:
            logging.error(f"Database error in get_product_by_id(): {e}")
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
                    logging.error(f"Product with ID {product_id} not found in database in get_votes_for_product()")
                    raise ProductNotFoundError("Product not found in database")
                
                return row[0] or 0
        except psycopg2.Error as e:
            logging.error(f"Database error in get_votes_for_product(): {e}")
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

                # Update vote count
                product_name, current_votes = row
                new_votes = (current_votes or 0) + 1
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
        