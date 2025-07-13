"""
Tests for CacheManager cache operations.

This module tests Redis cache operations like get, set, and invalidate.
"""

import json
from unittest.mock import patch

from ..conftest import MockRedisError, setup_redis_mock


class TestCacheOperations:
    """Test suite for CacheManager cache operations."""

    def test_get_product_ProductExistsInCache_ReturnsProductDict(
        self, cache_manager, mock_redis_client, test_data_factory,
    ):
        """Test that get_product() returns product data when product exists in cache."""
        product_id = "1"
        product_data = test_data_factory.create_product_dict()
        mock_redis_client.get.return_value = json.dumps(product_data)
        cache_manager.redis_client = mock_redis_client

        result = cache_manager.get_product(product_id)

        assert result == product_data
        mock_redis_client.get.assert_called_once_with(f"product:{product_id}")

    def test_get_product_ProductNotInCache_ReturnsNone(
        self, cache_manager, mock_redis_client,
    ):
        """Test that get_product() returns None when product doesn't exist in cache."""
        product_id = "999"
        mock_redis_client.get.return_value = None
        cache_manager.redis_client = mock_redis_client

        result = cache_manager.get_product(product_id)

        assert result is None
        mock_redis_client.get.assert_called_once_with(f"product:{product_id}")

    def test_get_product_EmptyStringFromCache_ReturnsNone(
        self, cache_manager, mock_redis_client,
    ):
        """Test that get_product() returns None when cache returns empty string."""
        product_id = "1"
        mock_redis_client.get.return_value = ""
        cache_manager.redis_client = mock_redis_client

        result = cache_manager.get_product(product_id)

        assert result is None
        mock_redis_client.get.assert_called_once_with(f"product:{product_id}")

    @patch('infrastructure.cache.cache_manager.redis')
    def test_get_product_RedisError_ReturnsNoneAndLogsWarning(
        self, mock_redis, cache_manager, mock_redis_client,
    ):
        """Test that get_product() returns None and logs warning when Redis error occurs."""
        setup_redis_mock(mock_redis)
        product_id = "1"
        mock_redis_client.get.side_effect = MockRedisError("Redis connection failed")
        cache_manager.redis_client = mock_redis_client

        with patch('infrastructure.cache.cache_manager.logging') as mock_logging:
            result = cache_manager.get_product(product_id)

        assert result is None
        mock_logging.warning.assert_called_once()
        mock_redis_client.get.assert_called_once_with(f"product:{product_id}")

    def test_get_product_JSONDecodeError_ReturnsNoneAndLogsWarning(
        self, cache_manager, mock_redis_client,
    ):
        """Test that get_product() returns None and logs warning when JSON decode fails."""
        product_id = "1"
        mock_redis_client.get.return_value = "invalid json"
        cache_manager.redis_client = mock_redis_client

        with patch('infrastructure.cache.cache_manager.logging') as mock_logging:
            result = cache_manager.get_product(product_id)

        assert result is None
        mock_logging.warning.assert_called_once()
        mock_redis_client.get.assert_called_once_with(f"product:{product_id}")


class TestCacheOperations:
    """Test cache operations (set, invalidate)."""

    def test_set_product_ValidProductData_StoresInCacheWithTTL(
        self, cache_manager, mock_redis_client, test_data_factory,
    ):
        """Test that set_product() stores product data in cache with TTL."""
        product_id = "1"
        product_data = test_data_factory.create_product_dict()
        cache_manager.redis_client = mock_redis_client

        cache_manager.set_product(product_id, product_data)

        expected_key = f"product:{product_id}"
        expected_value = json.dumps(product_data)
        mock_redis_client.setex.assert_called_once_with(
            expected_key, 3600, expected_value  # 3600 seconds TTL (1 hour)
        )

    @patch('infrastructure.cache.cache_manager.redis')
    def test_set_product_RedisError_DoesNotRaiseErrorAndLogsWarning(
        self, mock_redis, cache_manager, mock_redis_client, test_data_factory,
    ):
        """Test that set_product() doesn't raise error and logs warning when Redis error occurs."""
        setup_redis_mock(mock_redis)
        product_id = "1"
        product_data = test_data_factory.create_product_dict()
        mock_redis_client.setex.side_effect = MockRedisError("Redis connection failed")
        cache_manager.redis_client = mock_redis_client

        with patch('infrastructure.cache.cache_manager.logging') as mock_logging:
            # Should not raise an exception
            cache_manager.set_product(product_id, product_data)

        mock_logging.warning.assert_called_once()
        expected_key = f"product:{product_id}"
        expected_value = json.dumps(product_data)
        mock_redis_client.setex.assert_called_once_with(
            expected_key, 3600, expected_value
        )

    def test_invalidate_product_ProductExistsInCache_RemovesFromCache(
        self, cache_manager, mock_redis_client,
    ):
        """Test that invalidate_product() removes product from cache."""
        cache_manager.redis_client = mock_redis_client
        product_id = 1

        cache_manager.invalidate_product(product_id)

        mock_redis_client.delete.assert_called_once_with(f"product:{product_id}")

class TestCacheConnectionManagement:
    """Test suite for CacheManager connection management."""

    @patch('infrastructure.cache.cache_manager.redis')
    def test_connect_ValidCredentials_EstablishesConnectionAndSetsConnectedTrue(
        self, mock_redis, cache_manager, mock_redis_client,
    ):
        """
        Test that connect() successfully establishes a Redis connection when valid credentials
        are provided and sets is_connected to True.
        """
        mock_redis.Redis.return_value = mock_redis_client
        mock_redis_client.ping.return_value = True

        cache_manager.connect()

        mock_redis.Redis.assert_called_once_with(
            host=cache_manager.settings.redis_host,
            port=cache_manager.settings.redis_port,
            decode_responses=True,
        )
        mock_redis_client.ping.assert_called_once()
        assert cache_manager.redis_client is mock_redis_client
        assert cache_manager.is_connected is True

    @patch('infrastructure.cache.cache_manager.redis')
    def test_connect_RedisConnectionError_SetsConnectedFalseAndDoesNotRaiseError(
        self, mock_redis, cache_manager,
    ):
        """
        Test that connect() sets is_connected to False when Redis connection fails
        and does not raise an error (graceful degradation).
        """
        setup_redis_mock(mock_redis)
        mock_redis.Redis.side_effect = MockRedisError("Connection failed")

        cache_manager.connect()

        assert cache_manager.is_connected is False
        assert cache_manager.redis_client is None

    @patch('infrastructure.cache.cache_manager.redis')
    def test_connect_RedisPingFails_SetsConnectedFalseAndDoesNotRaiseError(
        self, mock_redis, cache_manager, mock_redis_client,
    ):
        """
        Test that connect() sets is_connected to False when Redis ping fails
        and does not raise an error (graceful degradation).
        """
        setup_redis_mock(mock_redis)
        mock_redis.Redis.return_value = mock_redis_client
        mock_redis_client.ping.side_effect = MockRedisError("Ping failed")

        cache_manager.connect()

        assert cache_manager.is_connected is False

    @patch('infrastructure.cache.cache_manager.redis')
    def test_check_connection_RedisError_ReturnsFalseAndSetsConnectedFalse(
        self, mock_redis, cache_manager, mock_redis_client,
    ):
        """
        Test that check_connection() returns False and sets is_connected to False when Redis error occurs.
        """
        setup_redis_mock(mock_redis)
        cache_manager.redis_client = mock_redis_client
        cache_manager.is_connected = True
        mock_redis_client.ping.side_effect = MockRedisError("Connection lost")

        result = cache_manager.check_connection()

        assert result is False
        assert cache_manager.is_connected is False
