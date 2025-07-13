"""
Pytest fixtures for core services unit tests.

This module provides common fixtures for testing the core services layer.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from core.exceptions import (
    DataPersistenceError,
    ProductNotFoundError,
    DataValidationError,
)


@pytest.fixture
def mock_data_access():
    """Create a mock data access layer for testing."""
    mock = Mock()
    # Set up common return values
    mock.get_products.return_value = [
        {
            "id": "1",
            "name": "Origami Crane",
            "description": "A beautiful origami crane",
            "image_url": "/static/images/origami/001-origami.png",
            "votes": 5,
        },
        {
            "id": "2",
            "name": "Origami Frog",
            "description": "A cute origami frog",
            "image_url": "/static/images/origami/012-origami-8.png",
            "votes": 3,
        },
    ]
    
    mock.get_product_by_id.return_value = {
        "id": "1",
        "name": "Origami Crane",
        "description": "A beautiful origami crane",
        "image_url": "/static/images/origami/001-origami.png",
        "votes": 5,
    }
    
    mock.get_votes_for_product.return_value = 5
    
    mock.add_vote.return_value = {
        "origami_id": 1,
        "new_vote_count": 6,
        "message": "Vote added successfully for Origami Crane",
    }
    
    mock.health_check.return_value = True
    
    return mock


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "id": "1",
        "name": "Origami Crane",
        "description": "A beautiful origami crane",
        "image_url": "/static/images/origami/001-origami.png",
        "votes": 5,
    }


@pytest.fixture
def sample_products_data():
    """Sample products list data for testing."""
    return [
        {
            "id": "1",
            "name": "Origami Crane",
            "description": "A beautiful origami crane",
            "image_url": "/static/images/origami/001-origami.png",
            "votes": 5,
        },
        {
            "id": "2",
            "name": "Origami Frog",
            "description": "A cute origami frog",
            "image_url": "/static/images/origami/012-origami-8.png",
            "votes": 3,
        },
    ]


@pytest.fixture
def sample_vote_data():
    """Sample vote response data for testing."""
    return {
        "origami_id": 1,
        "new_vote_count": 6,
        "message": "Vote added successfully for Origami Crane",
    }


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    mock = Mock()
    mock.app_version = "1.0.0"
    mock.postgres_host = "localhost"
    mock.postgres_port = 5432
    mock.redis_host = "localhost"
    mock.redis_port = 6379
    return mock
