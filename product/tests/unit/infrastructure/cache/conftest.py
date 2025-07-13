"""
Redis cache-specific fixtures and configuration.

This module contains Redis-specific fixtures, mock classes, and helpers
used across all CacheManager test modules.
"""

import pytest
from unittest.mock import MagicMock

from infrastructure.cache.cache_manager import CacheManager


class MockRedisError(Exception):
    """Mock redis.RedisError class for testing."""
    pass


class CacheTestDataFactory:
    """Factory for creating consistent test data for cache-related tests."""
    
    @staticmethod
    def create_product_dict(
        product_id="1",
        name="Test Product",
        description="Test Description",
        image_url="/test/image.png",
        votes=5,
    ):
        """Create a product dictionary for cache testing."""
        return {
            "id": str(product_id),
            "name": name,
            "description": description,
            "image_url": image_url,
            "votes": votes,
        }
    
    @staticmethod
    def create_cache_settings(
        redis_host="localhost",
        redis_port=6379,
    ):
        """Create cache settings for testing."""
        settings = MagicMock()
        settings.redis_host = redis_host
        settings.redis_port = redis_port
        return settings


@pytest.fixture
def cache_manager(test_cache_settings):
    """Create CacheManager instance with mock settings."""
    return CacheManager(test_cache_settings)


@pytest.fixture
def test_cache_settings():
    """Create test cache settings."""
    return CacheTestDataFactory.create_cache_settings()


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    return MagicMock()


@pytest.fixture
def cache_factory():
    """Provide access to CacheTestDataFactory."""
    return CacheTestDataFactory


def setup_redis_mock(mock_redis):
    """Helper function to set up Redis mock."""
    mock_redis.RedisError = MockRedisError
    return mock_redis
