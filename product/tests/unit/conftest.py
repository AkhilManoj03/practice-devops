"""
Pytest configuration file for the Product Service tests.

This module contains shared fixtures and test configuration for all test modules.
"""

import pytest
import sys
import os
from unittest.mock import MagicMock

# Add the app directory to the Python path before core.models import to avoid circular import
app_path = os.path.join(os.path.dirname(__file__), '..', '..', 'app')
if app_path not in sys.path:
    sys.path.insert(0, app_path)

from core.models import Product, VoteResponse

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


class TestDataFactory:
    """Unified factory for creating consistent test data across all test modules."""
    
    # Product-related test data creation
    @staticmethod
    def create_product_dict(
        product_id="1", name="Test Product", description="Test Description", 
        image_url="/test/image.png", votes=5,
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
        """Create a list of product dictionaries for testing."""
        return [
            TestDataFactory.create_product_dict(
                product_id=str(i),
                name=f"Product {i}",
                description=f"Description {i}",
                image_url=f"/image{i}.png",
                votes=i * 2,
            )
            for i in range(1, count + 1)
        ]
    
    @staticmethod
    def create_product_model(
        product_id=1, name="Test Product", description="Test Description",
        image_url="/test/image.png", votes=5,
    ):
        """Create a Product model instance for testing."""
        return Product(
            id=product_id,
            name=name,
            description=description,
            image_url=image_url,
            votes=votes,
        )
    
    @staticmethod
    def create_product_model_list(count=3):
        """Create a list of Product model instances for testing."""
        return [
            Product(
                id=i,
                name=f"Product {i}",
                description=f"Description {i}",
                image_url=f"/image{i}.png",
                votes=i * 2,
            )
            for i in range(1, count + 1)
        ]
    
    @staticmethod
    def create_db_row(
        product_id=1, name="Test Product", description="Test Description",
        image_url="/test/image.png", votes=5,
    ):
        """Create a database row tuple as returned by psycopg2."""
        return (product_id, name, description, image_url, votes)
    
    @staticmethod
    def create_db_rows(count=2):
        """Create multiple database rows for testing."""
        if count == 2:
            # Default test data that matches existing test expectations
            return [
                TestDataFactory.create_db_row(
                    product_id=1,
                    name="Test Product 1",
                    description="Description 1",
                    image_url="/image1.png",
                    votes=5,
                ),
                TestDataFactory.create_db_row(
                    product_id=2,
                    name="Test Product 2",
                    description="Description 2",
                    image_url="/image2.png",
                    votes=10,
                ),
            ]
        else:
            # Generic generation for other counts
            return [
                TestDataFactory.create_db_row(
                    product_id=i,
                    name=f"Test Product {i}",
                    description=f"Description {i}",
                    image_url=f"/image{i}.png",
                    votes=i * 2,
                )
                for i in range(1, count + 1)
            ]
    
    # Vote-related test data creation
    @staticmethod
    def create_vote_response_dict(
        origami_id=1, new_vote_count=6, product_name="Test Product",
    ):
        """Create a vote response dictionary for testing."""
        return {
            "origami_id": origami_id,
            "new_vote_count": new_vote_count,
            "message": f"Vote added successfully for {product_name}",
        }
    
    @staticmethod
    def create_vote_response_model(
        origami_id=1,
        new_vote_count=6,
    ):
        """Create a VoteResponse model instance for testing."""
        return VoteResponse(
            origami_id=origami_id,
            new_vote_count=new_vote_count,
            message=f"Vote added successfully for Product {origami_id}",
        )
    
    # Settings-related test data creation
    @staticmethod
    def create_test_settings(
        postgres_host="localhost", postgres_port=5432, postgres_db="test_db",
        postgres_user="test_user", postgres_password="test_password",
        redis_host="localhost", redis_port=6379,
    ):
        """Create test settings for testing."""
        settings = MagicMock()
        settings.postgres_host = postgres_host
        settings.postgres_port = postgres_port
        settings.postgres_db = postgres_db
        settings.postgres_user = postgres_user
        settings.postgres_password = postgres_password
        settings.redis_host = redis_host
        settings.redis_port = redis_port
        return settings
    
    # Predefined sample data sets
    @staticmethod
    def create_sample_origami_products():
        """Create sample origami product data for testing."""
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


@pytest.fixture(scope="session")
def test_settings():
    """Mock application settings for testing."""
    return TestDataFactory.create_test_settings()

@pytest.fixture
def test_data_factory():
    """Provide access to TestDataFactory."""
    return TestDataFactory
