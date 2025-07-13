"""
Tests for PostgresManager connection management.

This module tests connection establishment, disconnection, and health checks.
"""

import pytest
from unittest.mock import MagicMock, patch

from core.exceptions import DataPersistenceError
from .conftest import MockPsycopg2Error, setup_psycopg2_mock


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
    def test_connect_UnexpectedError_RaisesException(self, mock_psycopg2, postgres_manager):
        """Test that connect() raises Exception when unexpected error occurs during connection."""
        setup_psycopg2_mock(mock_psycopg2)
        mock_psycopg2.connect.side_effect = Exception("Unexpected error")

        with pytest.raises(Exception, match="Unexpected error connecting to database"):
            postgres_manager.connect()

    def test_disconnect_ConnectionExists_ClosesConnectionAndClearsReference(self, postgres_manager):
        """
        Test that disconnect() closes the connection and clears the reference when connection exists.
        """
        mock_connection = MagicMock()
        postgres_manager.connection = mock_connection

        postgres_manager.disconnect()

        mock_connection.close.assert_called_once()
        assert postgres_manager.connection is None

    def test_disconnect_NoConnection_DoesNotRaiseError(self, postgres_manager):
        """Test that disconnect() handles gracefully when no connection exists."""
        postgres_manager.connection = None

        postgres_manager.disconnect()

        assert postgres_manager.connection is None

    def test_disconnect_CloseFails_RaisesDataPersistenceError(self, postgres_manager):
        """Test that disconnect() raises DataPersistenceError when connection close fails."""
        mock_connection = MagicMock()
        mock_connection.close.side_effect = Exception("Close error")
        postgres_manager.connection = mock_connection

        with pytest.raises(DataPersistenceError, match="Error closing database connection"):
            postgres_manager.disconnect()

    def test_check_connection_ConnectionActive_ReturnsTrue(
        self, postgres_manager, mock_connection, mock_cursor_context_manager, mock_cursor,
    ):
        """
        Test that check_connection() returns True when database connection is active and responsive.
        """
        mock_connection.cursor.return_value = mock_cursor_context_manager
        postgres_manager.connection = mock_connection

        result = postgres_manager.check_connection()

        assert result is True
        mock_cursor.execute.assert_called_once_with("SELECT 1")

    def test_check_connection_NoConnection_ReturnsFalse(self, postgres_manager):
        """Test that check_connection() returns False when no database connection exists."""
        postgres_manager.connection = None

        result = postgres_manager.check_connection()

        assert result is False

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
