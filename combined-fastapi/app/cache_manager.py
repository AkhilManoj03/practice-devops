"""
Cache manager for the Combined Origami Service.

This module handles caching operations using Redis.
"""

import json
import logging
from typing import Optional, Dict, Any
import redis

class CacheManager:
    """Redis cache manager for product data."""

    def __init__(self, settings):
        """Initialize the cache manager.

        Args:
            settings: Application settings containing Redis configuration.
        """
        self.settings = settings
        self.redis_client: Optional[redis.Redis] = None
        self.cache_ttl = 3600  # Cache TTL in seconds (1 hour)

    def connect(self) -> None:
        """Establish Redis connection.

        Raises:
            DataPersistenceError: If connection fails.
        """
        try:
            self.redis_client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logging.info(f"Redis connection established to {self.settings.redis_host}:{self.settings.redis_port}")
        except redis.RedisError as e:
            logging.warning(f"Failed to connect to Redis: {e}")
            # Do not raise an error here, as the cache is not critical for the application to run

    def disconnect(self) -> None:
        """Close Redis connection."""
        if not self.redis_client:
            return
        self.redis_client.close()
        self.redis_client = None
        logging.info("Redis connection closed successfully")

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product from cache by ID.

        Args:
            product_id: The ID of the product to retrieve.

        Returns:
            Optional[Dict[str, Any]]: The product data if found in cache, None otherwise.
        """
        if not self.redis_client:
            return None

        try:
            cached_data = self.redis_client.get(f"product:{product_id}")
            if not cached_data:
                return None
            return json.loads(cached_data)
        except (redis.RedisError, json.JSONDecodeError) as e:
            logging.warning(f"Error retrieving product {product_id} from cache: {e}")

    def set_product(self, product_id: int, product_data: Dict[str, Any]) -> None:
        """Store product in cache.

        Args:
            product_id: The ID of the product to store.
            product_data: The product data to cache.
        """
        if not self.redis_client:
            return

        try:
            self.redis_client.setex(
                f"product:{product_id}",
                self.cache_ttl,
                json.dumps(product_data)
            )
        except (redis.RedisError, TypeError) as e:
            logging.warning(f"Error caching product {product_id}: {e}")

    def invalidate_product(self, product_id: int) -> None:
        """Remove product from cache.

        Args:
            product_id: The ID of the product to remove from cache.
        """
        if not self.redis_client:
            return

        try:
            self.redis_client.delete(f"product:{product_id}")
        except redis.RedisError as e:
            logging.warning(f"Error invalidating cache for product {product_id}: {e}")

    def check_connection(self) -> bool:
        """Check if Redis connection is active.

        Returns:
            bool: True if connection is active, False otherwise.
        """
        if not self.redis_client:
            return False
        try:
            return bool(self.redis_client.ping())
        except redis.RedisError:
            return False
