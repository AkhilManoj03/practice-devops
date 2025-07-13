"""
Pytest configuration file for the Product Service tests.

This module contains shared fixtures and test configuration for all test modules.
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the app directory to the Python path so we can import modules
app_path = os.path.join(os.path.dirname(__file__), '..', 'app')
if app_path not in sys.path:
    sys.path.insert(0, app_path)

# Mock the settings module to avoid config dependency issues during testing
mock_settings = MagicMock()
mock_settings.postgres_host = "localhost"
mock_settings.postgres_port = 5432
mock_settings.postgres_db = "test_db"
mock_settings.postgres_user = "test_user"
mock_settings.postgres_password = "test_password"
mock_settings.redis_host = "localhost"
mock_settings.redis_port = 6379

# Apply the mock globally
sys.modules['config'] = MagicMock()
sys.modules['config'].settings = mock_settings


@pytest.fixture(scope="session")
def test_settings():
    """Mock application settings for testing."""
    settings = MagicMock()
    
    # Database settings
    settings.postgres_host = "localhost"
    settings.postgres_port = 5432
    settings.postgres_db = "test_db"
    settings.postgres_user = "test_user"
    settings.postgres_password = "test_password"
    
    # Redis settings
    settings.redis_host = "localhost"
    settings.redis_port = 6379
    
    return settings


@pytest.fixture
def sample_products():
    """Sample product data for testing."""
    return [
        {
            "id": "1",
            "name": "Origami Crane",
            "description": "A beautiful origami crane",
            "image_url": "/static/images/origami/001-origami.png",
            "votes": 5
        },
        {
            "id": "2",
            "name": "Origami Frog",
            "description": "A cute origami frog",
            "image_url": "/static/images/origami/012-origami-8.png",
            "votes": 3
        },
        {
            "id": "3",
            "name": "Origami Butterfly",
            "description": "An elegant origami butterfly",
            "image_url": "/static/images/origami/017-origami-9.png",
            "votes": 8
        }
    ]


@pytest.fixture
def sample_product():
    """Single sample product for testing."""
    return {
        "id": "1",
        "name": "Test Product",
        "description": "Test Description",
        "image_url": "/test/image.png",
        "votes": 5
    }


@pytest.fixture
def sample_db_product_rows():
    """Sample database rows formatted as returned by psycopg2."""
    return [
        (1, "Origami Crane", "A beautiful origami crane", "/static/images/origami/001-origami.png", 5),
        (2, "Origami Frog", "A cute origami frog", "/static/images/origami/012-origami-8.png", 3),
        (3, "Origami Butterfly", "An elegant origami butterfly", "/static/images/origami/017-origami-9.png", 8)
    ]


@pytest.fixture
def sample_db_product_row():
    """Single sample database row formatted as returned by psycopg2."""
    return (1, "Test Product", "Test Description", "/test/image.png", 5)


# PostgreSQL-specific fixtures
@pytest.fixture
def sample_db_rows():
    """Sample database rows for PostgreSQL testing."""
    return [
        (1, "Test Product 1", "Description 1", "/image1.png", 5),
        (2, "Test Product 2", "Description 2", "/image2.png", 10),
    ]


@pytest.fixture
def sample_db_row():
    """Single sample database row for PostgreSQL testing."""
    return (1, "Test Product", "Test Description", "/test/image.png", 5)


# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (slower, with dependencies)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that require database interaction"
    )
    config.addinivalue_line(
        "markers", "cache: marks tests that require cache interaction"
    ) 