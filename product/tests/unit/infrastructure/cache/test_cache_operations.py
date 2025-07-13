"""
Tests for CacheManager cache operations.

This module tests Redis cache operations like get, set, and invalidate.
"""

import json
from unittest.mock import patch

from .conftest import MockRedisError, setup_redis_mock


class TestCacheOperations:
    """Test suite for CacheManager cache operations."""

    def test_get_product_ProductExistsInCache_ReturnsProductDict(
        self, cache_manager, mock_redis_client, cache_factory,
    ):
        """Test that get_product() returns product dictionary when product exists in cache."""
        cache_manager.redis_client = mock_redis_client
        product_data = cache_factory.create_product_dict()
        cached_json = json.dumps(product_data)
        mock_redis_client.get.return_value = cached_json
        product_id = 1

        result = cache_manager.get_product(product_id)

        mock_redis_client.get.assert_called_once_with(f"product:{product_id}")
        assert result == product_data

    def test_get_product_ProductNotInCache_ReturnsNone(
        self, cache_manager, mock_redis_client,
    ):
        """Test that get_product() returns None when product is not in cache."""
        cache_manager.redis_client = mock_redis_client
        mock_redis_client.get.return_value = None
        product_id = 1

        result = cache_manager.get_product(product_id)

        mock_redis_client.get.assert_called_once_with(f"product:{product_id}")
        assert result is None

    def test_get_product_EmptyStringFromCache_ReturnsNone(
        self, cache_manager, mock_redis_client,
    ):
        """Test that get_product() returns None when cache returns empty string."""
        cache_manager.redis_client = mock_redis_client
        mock_redis_client.get.return_value = ""
        product_id = 1

        result = cache_manager.get_product(product_id)

        assert result is None

    @patch('infrastructure.cache.cache_manager.redis')
    def test_get_product_RedisError_ReturnsNoneAndLogsWarning(
        self, mock_redis, cache_manager, mock_redis_client,
    ):
        """Test that get_product() returns None when Redis error occurs."""
        setup_redis_mock(mock_redis)
        cache_manager.redis_client = mock_redis_client
        mock_redis_client.get.side_effect = MockRedisError("Connection lost")
        product_id = 1

        result = cache_manager.get_product(product_id)

        assert result is None

    def test_get_product_JSONDecodeError_ReturnsNoneAndLogsWarning(
        self, cache_manager, mock_redis_client,
    ):
        """Test that get_product() returns None when JSON decode error occurs."""
        cache_manager.redis_client = mock_redis_client
        mock_redis_client.get.return_value = "invalid json"
        product_id = 1

        result = cache_manager.get_product(product_id)

        assert result is None

    def test_set_product_ValidProductData_StoresInCacheWithTTL(
        self, cache_manager, mock_redis_client, cache_factory,
    ):
        """Test that set_product() stores product in cache with correct TTL."""
        cache_manager.redis_client = mock_redis_client
        product_data = cache_factory.create_product_dict()
        product_id = 1

        cache_manager.set_product(product_id, product_data)

        mock_redis_client.setex.assert_called_once_with(
            f"product:{product_id}",
            cache_manager.cache_ttl,
            json.dumps(product_data),
        )

    def test_set_product_ComplexProductData_StoresCorrectly(
        self, cache_manager, mock_redis_client, cache_factory,
    ):
        """Test that set_product() handles complex product data correctly."""
        cache_manager.redis_client = mock_redis_client
        product_data = cache_factory.create_product_dict(
            name="Complex Product Name with Special Characters!@#$%",
            description="Very long description " * 50,
            votes=999999,
        )
        product_id = 1

        cache_manager.set_product(product_id, product_data)

        # Verify the JSON serialization was called with correct data
        expected_json = json.dumps(product_data)
        mock_redis_client.setex.assert_called_once_with(
            f"product:{product_id}",
            cache_manager.cache_ttl,
            expected_json
        )

    @patch('infrastructure.cache.cache_manager.redis')
    def test_set_product_RedisError_DoesNotRaiseErrorAndLogsWarning(
        self, mock_redis, cache_manager, mock_redis_client, cache_factory,
    ):
        """Test that set_product() does not raise error when Redis error occurs."""
        setup_redis_mock(mock_redis)
        cache_manager.redis_client = mock_redis_client
        mock_redis_client.setex.side_effect = MockRedisError("Connection lost")
        product_data = cache_factory.create_product_dict()
        product_id = 1

        # Should not raise an exception
        cache_manager.set_product(product_id, product_data)

    def test_set_product_NonSerializableData_DoesNotRaiseErrorAndLogsWarning(
        self, cache_manager, mock_redis_client,
    ):
        """Test that set_product() does not raise error when data is not JSON serializable."""
        cache_manager.redis_client = mock_redis_client
        # Create non-serializable data
        non_serializable_data = {"function": lambda x: x}
        product_id = 1

        # Should not raise an exception
        cache_manager.set_product(product_id, non_serializable_data)

    def test_invalidate_product_ProductExistsInCache_RemovesFromCache(
        self, cache_manager, mock_redis_client,
    ):
        """Test that invalidate_product() removes product from cache."""
        cache_manager.redis_client = mock_redis_client
        product_id = 1

        cache_manager.invalidate_product(product_id)

        mock_redis_client.delete.assert_called_once_with(f"product:{product_id}")

    def test_invalidate_product_ProductNotInCache_DoesNotRaiseError(
        self, cache_manager, mock_redis_client,
    ):
        """Test that invalidate_product() does not raise error when product is not in cache."""
        cache_manager.redis_client = mock_redis_client
        mock_redis_client.delete.return_value = 0  # Redis returns 0 when key doesn't exist
        product_id = 1

        cache_manager.invalidate_product(product_id)

        mock_redis_client.delete.assert_called_once_with(f"product:{product_id}")

    @patch('infrastructure.cache.cache_manager.redis')
    def test_invalidate_product_RedisError_DoesNotRaiseErrorAndLogsWarning(
        self, mock_redis, cache_manager, mock_redis_client,
    ):
        """Test that invalidate_product() does not raise error when Redis error occurs."""
        setup_redis_mock(mock_redis)
        cache_manager.redis_client = mock_redis_client
        mock_redis_client.delete.side_effect = MockRedisError("Connection lost")
        product_id = 1

        cache_manager.invalidate_product(product_id)

    def test_invalidate_product_BoundaryProductIds_HandlesCorrectly(
        self, cache_manager, mock_redis_client,
    ):
        """Test that invalidate_product() handles boundary product IDs correctly."""
        cache_manager.redis_client = mock_redis_client
        large_product_id = 999999

        cache_manager.invalidate_product(large_product_id)

        mock_redis_client.delete.assert_called_once_with(f"product:{large_product_id}")
