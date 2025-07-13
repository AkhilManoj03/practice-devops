"""
Tests for PostgresManager query operations.

This module tests read operations like get_products, get_product_by_id, and get_votes_for_product.
"""

import pytest
from unittest.mock import patch

from core.exceptions import DataPersistenceError, ProductNotFoundError
from .conftest import MockPsycopg2Error, setup_psycopg2_mock


class TestPostgresQueryOperations:
    """Test suite for PostgresManager query operations."""

    def test_get_products_ProductsExist_ReturnsAllProducts(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
        product_factory,
    ):
        """Test that get_products() returns all products when products exist in database."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        test_db_rows = product_factory.create_db_rows(2)
        mock_cursor.fetchall.return_value = test_db_rows
        postgres_manager.connection = mock_connection

        result = postgres_manager.get_products()

        mock_cursor.execute.assert_called_once_with(
            "SELECT id, name, description, image_url, votes FROM products ORDER BY id"
        )
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[0]["name"] == "Test Product 1"
        assert result[0]["description"] == "Description 1"
        assert result[0]["image_url"] == "/image1.png"
        assert result[0]["votes"] == 5
        assert result[1]["id"] == "2"
        assert result[1]["name"] == "Test Product 2"
        assert result[1]["votes"] == 10

    def test_get_products_SingleProduct_ReturnsSingleProduct(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
        product_factory,
    ):
        """Test that get_products() returns single product when only one exists in database."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        test_db_rows = product_factory.create_db_rows(1)
        mock_cursor.fetchall.return_value = test_db_rows
        postgres_manager.connection = mock_connection

        result = postgres_manager.get_products()

        assert len(result) == 1
        assert result[0]["id"] == "1"
        assert result[0]["name"] == "Test Product 1"

    def test_get_products_ZeroVotes_ReturnsZeroVotes(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
        product_factory,
    ):
        """Test that get_products() handles products with zero votes correctly."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        test_db_row = product_factory.create_db_row(votes=0)
        mock_cursor.fetchall.return_value = [test_db_row]
        postgres_manager.connection = mock_connection

        result = postgres_manager.get_products()

        assert len(result) == 1
        assert result[0]["votes"] == 0

    def test_get_products_NullVotes_ReturnsZeroVotes(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
        product_factory,
    ):
        """
        Test that get_products() handles products with null votes correctly by converting to zero.
        """
        mock_connection.cursor.return_value = mock_cursor_context_manager
        test_db_row = product_factory.create_db_row(votes=None)
        mock_cursor.fetchall.return_value = [test_db_row]
        postgres_manager.connection = mock_connection

        result = postgres_manager.get_products()

        assert len(result) == 1
        assert result[0]["votes"] == 0

    def test_get_products_NoConnection_RaisesDataPersistenceError(self, postgres_manager):
        """
        Test that get_products() raises DataPersistenceError when no database connection exists.
        """
        postgres_manager.connection = None

        with pytest.raises(DataPersistenceError, match="Database connection not established"):
            postgres_manager.get_products()

    def test_get_products_NoProductsExist_RaisesProductNotFoundError(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
    ):
        """
        Test that get_products() raises ProductNotFoundError when no products exist in database.
        """
        mock_connection.cursor.return_value = mock_cursor_context_manager
        mock_cursor.fetchall.return_value = []
        postgres_manager.connection = mock_connection

        with pytest.raises(ProductNotFoundError, match="No products found in database"):
            postgres_manager.get_products()

    @patch('infrastructure.database.postgres_manager.psycopg2')
    def test_get_products_DatabaseQueryFails_RaisesDataPersistenceError(
        self, mock_psycopg2, postgres_manager, mock_connection, mock_cursor_context_manager,
        mock_cursor,
    ):
        """Test that get_products() raises DataPersistenceError when database query fails."""
        setup_psycopg2_mock(mock_psycopg2)
        mock_connection.cursor.return_value = mock_cursor_context_manager
        mock_cursor.execute.side_effect = MockPsycopg2Error("Query failed")
        postgres_manager.connection = mock_connection

        with pytest.raises(DataPersistenceError, match="Error fetching products from database"):
            postgres_manager.get_products()

    def test_get_product_by_id_ProductExists_ReturnsProduct(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
        product_factory,
    ):
        """Test that get_product_by_id() returns product when product exists in database."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        test_db_row = product_factory.create_db_row()
        mock_cursor.fetchone.return_value = test_db_row
        postgres_manager.connection = mock_connection
        product_id = 1

        result = postgres_manager.get_product_by_id(product_id)

        mock_cursor.execute.assert_called_once_with(
            "SELECT id, name, description, image_url, votes FROM products WHERE id = %s",
            (product_id,),
        )
        assert result["id"] == "1"
        assert result["name"] == "Test Product"
        assert result["description"] == "Test Description"
        assert result["image_url"] == "/test/image.png"
        assert result["votes"] == 5

    def test_get_product_by_id_ZeroVotes_ReturnsZeroVotes(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
        product_factory,
    ):
        """Test that get_product_by_id() handles product with zero votes correctly."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        test_db_row = product_factory.create_db_row(votes=0)
        mock_cursor.fetchone.return_value = test_db_row
        postgres_manager.connection = mock_connection
        product_id = 1

        result = postgres_manager.get_product_by_id(product_id)

        assert result["votes"] == 0

    def test_get_product_by_id_BoundaryProductIds_ReturnsProduct(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
        product_factory,
    ):
        """Test that get_product_by_id() handles boundary product IDs correctly."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        test_db_row = product_factory.create_db_row(product_id=999999)
        mock_cursor.fetchone.return_value = test_db_row
        postgres_manager.connection = mock_connection
        large_product_id = 999999

        result = postgres_manager.get_product_by_id(large_product_id)

        mock_cursor.execute.assert_called_once_with(
            "SELECT id, name, description, image_url, votes FROM products WHERE id = %s",
            (large_product_id,),
        )
        assert result["id"] == "999999"

    def test_get_product_by_id_NoConnection_RaisesDataPersistenceError(self, postgres_manager):
        """
        Test that get_product_by_id() raises DataPersistenceError when no database connection exists.
        """
        postgres_manager.connection = None
        product_id = 1

        with pytest.raises(DataPersistenceError, match="Database connection not established"):
            postgres_manager.get_product_by_id(product_id)

    def test_get_product_by_id_ProductNotFound_RaisesProductNotFoundError(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
    ):
        """Test that get_product_by_id() raises ProductNotFoundError when product doesn't exist."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        mock_cursor.fetchone.return_value = None
        postgres_manager.connection = mock_connection
        nonexistent_product_id = 999

        with pytest.raises(ProductNotFoundError, match="Product not found in database"):
            postgres_manager.get_product_by_id(nonexistent_product_id)

    @patch('infrastructure.database.postgres_manager.psycopg2')
    def test_get_product_by_id_DatabaseQueryFails_RaisesDataPersistenceError(
        self, mock_psycopg2, postgres_manager, mock_connection, mock_cursor_context_manager,
        mock_cursor,
    ):
        """Test that get_product_by_id() raises DataPersistenceError when database query fails."""
        setup_psycopg2_mock(mock_psycopg2)
        mock_connection.cursor.return_value = mock_cursor_context_manager
        mock_cursor.execute.side_effect = MockPsycopg2Error("Query failed")
        postgres_manager.connection = mock_connection
        product_id = 1

        with pytest.raises(DataPersistenceError, match="Error fetching product from database"):
            postgres_manager.get_product_by_id(product_id)

    def test_get_votes_for_product_ProductHasVotes_ReturnsVoteCount(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
    ):
        """Test that get_votes_for_product() returns vote count when product exists with votes."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        expected_votes = 10
        mock_cursor.fetchone.return_value = (expected_votes,)
        postgres_manager.connection = mock_connection
        product_id = 1

        result = postgres_manager.get_votes_for_product(product_id)

        mock_cursor.execute.assert_called_once_with(
            "SELECT votes FROM products WHERE id = %s", (product_id,),
        )
        assert result == expected_votes

    def test_get_votes_for_product_ZeroVotes_ReturnsZero(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
    ):
        """Test that get_votes_for_product() returns zero when product exists with zero votes."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        mock_cursor.fetchone.return_value = (0,)
        postgres_manager.connection = mock_connection
        product_id = 1

        result = postgres_manager.get_votes_for_product(product_id)

        assert result == 0

    def test_get_votes_for_product_NullVotes_ReturnsZero(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
    ):
        """
        Test that get_votes_for_product() returns zero when product exists but votes field is null.
        """
        mock_connection.cursor.return_value = mock_cursor_context_manager
        mock_cursor.fetchone.return_value = (None,)
        postgres_manager.connection = mock_connection
        product_id = 1

        result = postgres_manager.get_votes_for_product(product_id)

        assert result == 0

    def test_get_votes_for_product_LargeVoteCounts_ReturnsLargeCount(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
    ):
        """Test that get_votes_for_product() handles large vote counts correctly."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        large_vote_count = 999999
        mock_cursor.fetchone.return_value = (large_vote_count,)
        postgres_manager.connection = mock_connection
        product_id = 1

        result = postgres_manager.get_votes_for_product(product_id)

        assert result == large_vote_count

    def test_get_votes_for_product_NoConnection_RaisesDataPersistenceError(self, postgres_manager):
        """
        Test that get_votes_for_product() raises DataPersistenceError when no database connection
        exists.
        """
        postgres_manager.connection = None
        product_id = 1

        with pytest.raises(DataPersistenceError, match="Database connection not established"):
            postgres_manager.get_votes_for_product(product_id)

    def test_get_votes_for_product_ProductNotFound_RaisesProductNotFoundError(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
    ):
        """
        Test that get_votes_for_product() raises ProductNotFoundError when product doesn't exist.
        """
        mock_connection.cursor.return_value = mock_cursor_context_manager
        mock_cursor.fetchone.return_value = None
        postgres_manager.connection = mock_connection
        nonexistent_product_id = 999

        with pytest.raises(ProductNotFoundError, match="Product not found in database"):
            postgres_manager.get_votes_for_product(nonexistent_product_id)

    @patch('infrastructure.database.postgres_manager.psycopg2')
    def test_get_votes_for_product_DatabaseQueryFails_RaisesDataPersistenceError(
        self, mock_psycopg2, postgres_manager, mock_connection, mock_cursor_context_manager,
        mock_cursor,
    ):
        """Test that get_votes_for_product() raises DataPersistenceError when database query fails."""
        setup_psycopg2_mock(mock_psycopg2)
        mock_connection.cursor.return_value = mock_cursor_context_manager
        mock_cursor.execute.side_effect = MockPsycopg2Error("Query failed")
        postgres_manager.connection = mock_connection
        product_id = 1

        with pytest.raises(DataPersistenceError, match="Error fetching votes for product from database"):
            postgres_manager.get_votes_for_product(product_id)
