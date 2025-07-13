"""
DataAccessLayer-specific fixtures and configuration.

This module contains data access layer-specific fixtures, mock classes, and helpers
used across all DataAccessLayer test modules.
"""

import pytest
from unittest.mock import MagicMock

from infrastructure.data_access import DataAccessLayer


class DataAccessTestDataFactory:
    """Factory for creating consistent test data for data access layer tests."""
    
    @staticmethod
    def create_product_dict(
        product_id="1",
        name="Test Product",
        description="Test Description",
        image_url="/test/image.png",
        votes=5,
    ):
        """Create a product dictionary for testing."""
        return {
            "id": str(product_id),
            "name": name,
            "description": description,
            "image_url": image_url,
            "votes": votes,
        }
    
    @staticmethod
    def create_product_list(count=3):
        """Create a list of products for testing."""
        return [
            DataAccessTestDataFactory.create_product_dict(
                product_id=str(i),
                name=f"Product {i}",
                votes=i * 2,
            )
            for i in range(1, count + 1)
        ]
    
    @staticmethod
    def create_vote_response(product_id=1, new_vote_count=6):
        """Create a vote response dictionary for testing."""
        return {
            "origami_id": product_id,
            "new_vote_count": new_vote_count,
            "message": f"Vote added successfully for Test Product",
        }
    
    @staticmethod
    def create_test_settings():
        """Create test settings."""
        settings = MagicMock()
        settings.postgres_host = "localhost"
        settings.postgres_port = 5432
        settings.postgres_db = "test_db"
        settings.postgres_user = "test_user"
        settings.postgres_password = "test_pass"
        settings.redis_host = "localhost"
        settings.redis_port = 6379
        return settings


@pytest.fixture
def test_settings():
    """Create test settings."""
    return DataAccessTestDataFactory.create_test_settings()


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


@pytest.fixture
def data_factory():
    """Provide access to DataAccessTestDataFactory."""
    return DataAccessTestDataFactory


def setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager):
    """Helper function to set up data access layer with mock managers."""
    data_access_layer.db_manager = mock_db_manager
    data_access_layer.cache_manager = mock_cache_manager
    return data_access_layer
