"""
Tests for PostgresManager write operations.

This module tests write operations like add_vote with transaction handling.
"""

import pytest
from unittest.mock import patch

from core.exceptions import DataPersistenceError, ProductNotFoundError
from .conftest import MockPsycopg2Error, setup_psycopg2_mock


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
    def test_add_vote_DatabaseQueryFails_RaisesDataPersistenceErrorAndPerformsRollback(
        self, mock_psycopg2, postgres_manager, mock_connection, mock_cursor_context_manager, 
        mock_cursor,
    ):
        """
        Test that add_vote() raises DataPersistenceError and performs rollback when database query
        fails.
        """
        setup_psycopg2_mock(mock_psycopg2)
        mock_connection.cursor.return_value = mock_cursor_context_manager
        mock_cursor.execute.side_effect = MockPsycopg2Error("Query failed")
        postgres_manager.connection = mock_connection
        product_id = 1

        with pytest.raises(DataPersistenceError, match="Error adding vote to database for product"):
            postgres_manager.add_vote(product_id)

        mock_connection.rollback.assert_called_once()

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
