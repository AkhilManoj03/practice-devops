# database.py
"""
Database management for the Catalogue Service.

This module handles database connections, operations, and data access patterns
for both PostgreSQL and JSON file data sources.
"""

import json
import logging
from typing import Dict, List, Optional

import psycopg2
from fastapi import HTTPException, status

from app.config import settings


class DatabaseManager:
    """Database connection and operations manager for PostgreSQL."""

    def __init__(self, settings):
        self.settings = settings
        self.connection: Optional[psycopg2.extensions.connection] = None

    def connect(self) -> None:
        """Establish database connection."""
        if self.settings.data_source != "db":
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
        except psycopg2.Error as e:
            logging.error(f"Failed to connect to database: {e}")
            raise RuntimeError(f"Failed to connect to database: {e}")

    def disconnect(self) -> None:
        """Close database connection."""
        if not self.connection:
            return
        try:
            self.connection.close()
            self.connection = None
            logging.info("Database connection closed successfully")
        except Exception as e:
            logging.error(f"Error closing database connection: {e}")
            raise RuntimeError(f"Error closing database connection: {e}")

    def is_connected(self) -> bool:
        """Check if database connection is active."""
        if not self.connection:
            return False
        try:
            # Test the connection with a simple query
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except psycopg2.Error:
            return False

    def get_products(self) -> List[Dict]:
        """Fetch all products from database."""
        if not self.connection:
            raise RuntimeError("Database connection not established")

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT id, description, image_url, name FROM products ORDER BY id")
                rows = cursor.fetchall()

                return [
                    {
                        "id": row[0],
                        "description": row[1],
                        "image_url": row[2],
                        "name": row[3]
                    }
                    for row in rows
                ]
        except psycopg2.Error as e:
            logging.error(f"Database error in get_products: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}"
            )

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Fetch a single product by ID from database."""
        if not self.connection:
            raise RuntimeError("Database connection not established")

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, description, image_url, name FROM products WHERE id = %s",
                    (product_id,)
                )
                row = cursor.fetchone()
                if not row:
                    logging.error(f"Product with ID {product_id} not found in DB lookup")
                    return None
                
                return {
                    "id": row[0],
                    "description": row[1],
                    "image_url": row[2],
                    "name": row[3]
                }
        except psycopg2.Error as e:
            logging.error(f"Database error in get_product_by_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {e}"
            )


class JSONDataManager:
    """Data manager for JSON file-based data source."""

    def __init__(self, settings):
        self.settings = settings
        self._products_cache: Optional[List[Dict]] = None

    def load_products(self) -> List[Dict]:
        """Load products from JSON file with error handling."""
        try:
            with open(self.settings.products_file, 'r', encoding='utf-8') as f:
                products = json.load(f)

            if not products:
                raise ValueError("Products file must not be empty")
            if not isinstance(products, list):
                raise ValueError("Products file must contain a list")

            self._products_cache = products
            logging.info(f"Loaded {len(products)} products from JSON file: {self.settings.products_file}")
            return products
        except FileNotFoundError:
            raise RuntimeError(f"Products file '{self.settings.products_file}' not found")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in products file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading products: {e}")

    def get_products(self) -> List[Dict]:
        """Get all products from cache."""
        if self._products_cache is None:
            raise RuntimeError("Products not loaded. Call load_products() first.")
        return self._products_cache

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get a specific product by ID from cache."""
        if self._products_cache is None:
            raise RuntimeError("Products not loaded. Call load_products() first.")
        
        # Handle both string and int IDs for flexibility
        return next(
            (product for product in self._products_cache 
             if product.get('id') == product_id or product.get('id') == str(product_id)),
            None
        )

    def is_loaded(self) -> bool:
        """Check if products are loaded in cache."""
        return self._products_cache is not None


class DataAccessLayer:
    """
    Unified data access layer that abstracts the underlying data source.
    
    This class provides a consistent interface for data operations regardless
    of whether the data comes from a database or JSON file.
    """

    def __init__(self, settings):
        self.settings = settings
        self.db_manager: Optional[DatabaseManager] = None
        self.json_manager: Optional[JSONDataManager] = None
        
        # Initialize the appropriate data manager based on settings
        if settings.data_source == "db":
            self.db_manager = DatabaseManager(settings)
        else:
            self.json_manager = JSONDataManager(settings)

    def initialize(self) -> None:
        """Initialize the data source connection or load data."""
        if self.settings.data_source == "db":
            if self.db_manager:
                self.db_manager.connect()
        else:
            if self.json_manager:
                self.json_manager.load_products()

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.db_manager:
            self.db_manager.disconnect()

    def get_products(self) -> List[Dict]:
        """Get all products from the configured data source."""
        if self.settings.data_source == "db":
            if not self.db_manager:
                raise RuntimeError("Database manager not initialized")
            return self.db_manager.get_products()
        else:
            if not self.json_manager:
                raise RuntimeError("JSON manager not initialized")
            return self.json_manager.get_products()

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get a specific product by ID from the configured data source."""
        if self.settings.data_source == "db":
            if not self.db_manager:
                raise RuntimeError("Database manager not initialized")
            return self.db_manager.get_product_by_id(product_id)
        else:
            if not self.json_manager:
                raise RuntimeError("JSON manager not initialized")
            return self.json_manager.get_product_by_id(product_id)

    def health_check(self) -> bool:
        """Check if the data source is healthy and accessible."""
        if self.settings.data_source == "db":
            return self.db_manager.is_connected() if self.db_manager else False
        else:
            return self.json_manager.is_loaded() if self.json_manager else False


# Global data access layer instance
data_access = DataAccessLayer(settings)
