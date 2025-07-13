"""
Tests for PostgresManager connection management.

This module tests connection establishment, disconnection, and health checks.
"""

import pytest
from unittest.mock import MagicMock, patch

from core.exceptions import DataPersistenceError, ProductNotFoundError
from ..conftest import MockPsycopg2Error, setup_psycopg2_mock


class TestPostgresConnectionManagement:
    """Test suite for PostgresManager connection management."""

    @patch('infrastructure.database.postgres_manager.psycopg2')
    def test_connect_ValidCredentials_EstablishesConnection(
        self, mock_psycopg2, postgres_manager, test_settings,
    ):
        """
        Test that connect() successfully establishes a database connection when valid credentials
        are provided.
        """
        mock_connection = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection

        postgres_manager.connect()

        mock_psycopg2.connect.assert_called_once_with(
            host=test_settings.postgres_host,
            database=test_settings.postgres_db,
            user=test_settings.postgres_user,
            password=test_settings.postgres_password,
            port=test_settings.postgres_port,
        )
        assert postgres_manager.connection is mock_connection

    @patch('infrastructure.database.postgres_manager.psycopg2')
    def test_connect_Psycopg2Error_RaisesDataPersistenceError(self, mock_psycopg2, postgres_manager):
        """Test that connect() raises DataPersistenceError when psycopg2 connection fails."""
        setup_psycopg2_mock(mock_psycopg2)
        mock_psycopg2.connect.side_effect = MockPsycopg2Error("Connection failed")

        with pytest.raises(DataPersistenceError, match="Failed to connect to database"):
            postgres_manager.connect()

    @patch('infrastructure.database.postgres_manager.psycopg2')
    def test_check_connection_DatabaseError_ReturnsFalse(
        self, mock_psycopg2, postgres_manager, mock_connection, mock_cursor_context_manager,
        mock_cursor,
    ):
        """
        Test that check_connection() returns False when database error occurs during health check.
        """
        setup_psycopg2_mock(mock_psycopg2)
        mock_connection.cursor.return_value = mock_cursor_context_manager
        mock_cursor.execute.side_effect = MockPsycopg2Error("Connection lost")
        postgres_manager.connection = mock_connection

        result = postgres_manager.check_connection()

        assert result is False


class TestPostgresQueryOperations:
    """Test suite for PostgresManager query operations."""

    def test_get_products_ProductsExist_ReturnsAllProducts(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
        test_data_factory,
    ):
        """Test that get_products() returns all products when products exist in database."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        test_db_rows = test_data_factory.create_db_rows(2)
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
        test_data_factory,
    ):
        """Test that get_products() returns single product when only one exists."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        test_db_rows = test_data_factory.create_db_rows(1)
        mock_cursor.fetchall.return_value = test_db_rows
        postgres_manager.connection = mock_connection

        result = postgres_manager.get_products()

        assert len(result) == 1
        assert result[0]["id"] == "1"
        assert result[0]["name"] == "Test Product 1"
        assert result[0]["votes"] == 2

    def test_get_products_ZeroVotes_ReturnsZeroVotes(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
        test_data_factory,
    ):
        """Test that get_products() returns 0 votes when product has zero votes."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        test_db_row = test_data_factory.create_db_row(votes=0)
        mock_cursor.fetchall.return_value = [test_db_row]
        postgres_manager.connection = mock_connection

        result = postgres_manager.get_products()

        assert len(result) == 1
        assert result[0]["votes"] == 0

    def test_get_products_NullVotes_ReturnsZeroVotes(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
        test_data_factory,
    ):
        """Test that get_products() returns 0 votes when votes column is NULL."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        # Create a row with NULL votes (None in Python)
        test_db_row = test_data_factory.create_db_row(votes=None)
        mock_cursor.fetchall.return_value = [test_db_row]
        postgres_manager.connection = mock_connection

        result = postgres_manager.get_products()

        assert len(result) == 1
        assert result[0]["votes"] == 0  # Should convert NULL to 0

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
        test_data_factory,
    ):
        """Test that get_product_by_id() returns product when product exists in database."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        test_db_row = test_data_factory.create_db_row()
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
        test_data_factory,
    ):
        """Test that get_product_by_id() handles product with zero votes correctly."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        test_db_row = test_data_factory.create_db_row(votes=0)
        mock_cursor.fetchone.return_value = test_db_row
        postgres_manager.connection = mock_connection
        product_id = 1

        result = postgres_manager.get_product_by_id(product_id)


class TestPostgresWriteOperations:
    """Test suite for PostgresManager write operations."""

    def test_add_vote_ProductExists_IncrementsVoteCountAndReturnsSuccessMessage(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
    ):
        """
        Test that add_vote() increments vote count and returns success message when product exists.
        """
        mock_connection.cursor.return_value = mock_cursor_context_manager
        product_name = "Test Product"
        current_votes = 5
        expected_new_votes = 6
        product_id = 1
        mock_cursor.fetchone.return_value = (product_name, current_votes)
        postgres_manager.connection = mock_connection

        result = postgres_manager.add_vote(product_id)

        # Verify the SELECT query was called first
        first_call = mock_cursor.execute.call_args_list[0]
        assert first_call[0][0] == "SELECT name, votes FROM products WHERE id = %s"
        assert first_call[0][1] == (product_id,)

        # Verify the UPDATE query was called second
        second_call = mock_cursor.execute.call_args_list[1]
        assert second_call[0][0] == "UPDATE products SET votes = %s WHERE id = %s"
        assert second_call[0][1] == (expected_new_votes, product_id)

        # Verify commit was called
        mock_connection.commit.assert_called_once()

        # Verify return value structure and content
        assert result["origami_id"] == product_id
        assert result["new_vote_count"] == expected_new_votes
        assert product_name in result["message"]
        assert result["message"] == f"Vote added successfully for {product_name}"

    def test_add_vote_NullVotes_SetsVoteCountToOne(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
    ):
        """
        Test that add_vote() sets vote count to 1 when product exists but current votes is null.
        """
        mock_connection.cursor.return_value = mock_cursor_context_manager
        product_name = "Test Product"
        current_votes = None
        expected_new_votes = 1
        product_id = 1
        mock_cursor.fetchone.return_value = (product_name, current_votes)
        postgres_manager.connection = mock_connection

        result = postgres_manager.add_vote(product_id)

        second_call = mock_cursor.execute.call_args_list[1]
        assert second_call[0][1] == (expected_new_votes, product_id)

        assert result["new_vote_count"] == expected_new_votes

    def test_add_vote_NoConnection_RaisesDataPersistenceError(self, postgres_manager):
        """Test that add_vote() raises DataPersistenceError when no database connection exists."""
        postgres_manager.connection = None
        product_id = 1

        with pytest.raises(DataPersistenceError, match="Database connection not established"):
            postgres_manager.add_vote(product_id)

    def test_add_vote_ProductNotFound_RaisesProductNotFoundError(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
    ):
        """Test that add_vote() raises ProductNotFoundError when product doesn't exist."""
        mock_connection.cursor.return_value = mock_cursor_context_manager
        mock_cursor.fetchone.return_value = None
        postgres_manager.connection = mock_connection
        nonexistent_product_id = 999

        with pytest.raises(ProductNotFoundError, match="Product not found in database"):
            postgres_manager.add_vote(nonexistent_product_id)

    @patch('infrastructure.database.postgres_manager.psycopg2')
    def test_add_vote_ConnectionLostDuringError_AttemptsRollback(
        self, mock_psycopg2, postgres_manager, mock_connection, mock_cursor_context_manager,
        mock_cursor,
    ):
        """
        Test that add_vote() attempts rollback even when connection is lost during database error.
        """
        setup_psycopg2_mock(mock_psycopg2)
        mock_connection.cursor.return_value = mock_cursor_context_manager
        mock_cursor.execute.side_effect = MockPsycopg2Error("Query failed")
        postgres_manager.connection = mock_connection
        product_id = 1

        with pytest.raises(DataPersistenceError):
            postgres_manager.add_vote(product_id)

        mock_connection.rollback.assert_called_once()
