"""
Tests for CacheManager connection management.

This module tests Redis connection establishment, disconnection, and health checks.
"""

from unittest.mock import patch

from .conftest import MockRedisError, setup_redis_mock


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

    def test_disconnect_ConnectionExists_ClosesConnectionAndClearsReference(
        self, cache_manager, mock_redis_client
    ):
        """
        Test that disconnect() closes the connection and clears the reference when connection exists.
        """
        cache_manager.redis_client = mock_redis_client
        cache_manager.is_connected = True

        cache_manager.disconnect()

        mock_redis_client.close.assert_called_once()
        assert cache_manager.redis_client is None
        assert cache_manager.is_connected is False

    def test_disconnect_NoConnection_DoesNotRaiseError(self, cache_manager):
        """Test that disconnect() handles gracefully when no connection exists."""
        cache_manager.redis_client = None
        cache_manager.is_connected = False

        cache_manager.disconnect()

        assert cache_manager.redis_client is None
        assert cache_manager.is_connected is False

    def test_check_connection_ConnectionActiveAndPingSucceeds_ReturnsTrue(
        self, cache_manager, mock_redis_client,
    ):
        """
        Test that check_connection() returns True when Redis connection is active and ping succeeds.
        """
        cache_manager.redis_client = mock_redis_client
        mock_redis_client.ping.return_value = True

        result = cache_manager.check_connection()

        assert result is True
        mock_redis_client.ping.assert_called_once()

    def test_check_connection_NoConnection_ReturnsFalse(self, cache_manager):
        """Test that check_connection() returns False when no Redis connection exists."""
        cache_manager.redis_client = None

        result = cache_manager.check_connection()

        assert result is False

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
