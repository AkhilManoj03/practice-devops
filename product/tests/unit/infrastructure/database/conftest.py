"""
PostgreSQL-specific fixtures and configuration.

This module contains PostgreSQL-specific fixtures, mock classes, and helpers
used across all PostgresManager test modules.
"""

import pytest
from unittest.mock import MagicMock

from infrastructure.database.postgres_manager import PostgresManager

class MockPsycopg2Error(Exception):
    """Mock psycopg2.Error class for testing."""
    pass


class ProductTestDataFactory:
    """Factory for creating consistent test data for product-related tests."""
    
    @staticmethod
    def create_db_row(
        product_id=1, 
        name="Test Product", 
        description="Test Description", 
        image_url="/test/image.png", 
        votes=5,
    ):
        """Create a database row tuple as returned by psycopg2."""
        return (product_id, name, description, image_url, votes)
    
    @staticmethod
    def create_db_rows(count=2):
        """Create multiple database rows for testing."""
        return [
            ProductTestDataFactory.create_db_row(
                1, "Test Product 1", "Description 1", "/image1.png", 5
            ),
            ProductTestDataFactory.create_db_row(
                2, "Test Product 2", "Description 2", "/image2.png", 10
            ),
        ][:count]
    
    @staticmethod
    def create_product_dict(
        product_id="1",
        name="Test Product",
        description="Test Description",
        image_url="/test/image.png",
        votes=5,
    ):
        """Create a product dictionary as returned by PostgresManager methods."""
        return {
            "id": str(product_id),
            "name": name,
            "description": description,
            "image_url": image_url,
            "votes": votes,
        }
    
    @staticmethod
    def create_vote_response(origami_id=1, new_vote_count=6, product_name="Test Product"):
        """Create a vote response dictionary as returned by add_vote method."""
        return {
            "origami_id": origami_id,
            "new_vote_count": new_vote_count,
            "message": f"Vote added successfully for {product_name}",
        }


class DatabaseTestDataFactory:
    """Factory for creating database-related test data."""
    
    @staticmethod
    def create_connection_settings(
        host="localhost",
        port=5432,
        db="test_db",
        user="test_user",
        password="test_password",
    ):
        """Create database connection settings."""
        settings = MagicMock()
        settings.postgres_host = host
        settings.postgres_port = port
        settings.postgres_db = db
        settings.postgres_user = user
        settings.postgres_password = password
        return settings


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


@pytest.fixture
def product_factory():
    """Provide access to ProductTestDataFactory."""
    return ProductTestDataFactory


@pytest.fixture
def database_factory():
    """Provide access to DatabaseTestDataFactory."""
    return DatabaseTestDataFactory


def setup_mock_connection_and_cursor(mock_connection, mock_cursor_cm):
    """Helper function to set up mock connection and cursor."""
    mock_connection.cursor.return_value = mock_cursor_cm
    return mock_connection, mock_cursor_cm


def setup_psycopg2_mock(mock_psycopg2):
    """Helper function to set up psycopg2 mock."""
    mock_psycopg2.Error = MockPsycopg2Error
    return mock_psycopg2
