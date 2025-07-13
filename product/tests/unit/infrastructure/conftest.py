"""
Infrastructure-specific fixtures and configuration.

This module contains infrastructure-specific fixtures, mock classes, and helpers
used across all infrastructure test modules (cache, database, data access).
"""

import pytest
from unittest.mock import MagicMock

from infrastructure.cache.cache_manager import CacheManager
from infrastructure.database.postgres_manager import PostgresManager
from infrastructure.data_access import DataAccessLayer


# Mock error classes
class MockRedisError(Exception):
    """Mock redis.RedisError class for testing."""
    pass


class MockPsycopg2Error(Exception):
    """Mock psycopg2.Error class for testing."""
    pass


# Cache-related fixtures
@pytest.fixture
def cache_manager(test_settings):
    """Create CacheManager instance with mock settings."""
    return CacheManager(test_settings)

@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    return MagicMock()

# Database-related fixtures
@pytest.fixture
def postgres_manager(test_settings):
    """Create PostgresManager instance with mock settings."""
    return PostgresManager(test_settings)

@pytest.fixture
def mock_connection():
    """Create a mock database connection."""
    return MagicMock()

@pytest.fixture
def mock_cursor():
    """Create a mock database cursor."""
    return MagicMock()

@pytest.fixture
def mock_cursor_context_manager(mock_cursor):
    """Create a mock cursor context manager."""
    mock_cursor_cm = MagicMock()
    mock_cursor_cm.__enter__.return_value = mock_cursor
    mock_cursor_cm.__exit__.return_value = None
    return mock_cursor_cm

# Data access layer fixtures
@pytest.fixture
def data_access_layer(test_settings):
    """Create DataAccessLayer instance with mock settings."""
    return DataAccessLayer(test_settings)

@pytest.fixture
def mock_db_manager():
    """Create mock database manager."""
    return MagicMock()

@pytest.fixture
def mock_cache_manager():
    """Create mock cache manager."""
    return MagicMock()

# Helper functions
def setup_redis_mock(mock_redis):
    """Helper function to set up Redis mock."""
    mock_redis.RedisError = MockRedisError
    return mock_redis

def setup_psycopg2_mock(mock_psycopg2):
    """Helper function to set up psycopg2 mock."""
    mock_psycopg2.Error = MockPsycopg2Error
    return mock_psycopg2

def setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager):
    """Helper function to set up data access layer with mock managers."""
    data_access_layer.db_manager = mock_db_manager
    data_access_layer.cache_manager = mock_cache_manager
    return data_access_layer
