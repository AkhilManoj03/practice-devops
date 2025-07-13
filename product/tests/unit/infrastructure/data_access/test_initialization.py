"""
Tests for DataAccessLayer initialization and lifecycle management.

This module tests initialization, cleanup, and health check functionality.
"""

from .conftest import setup_data_access_with_mocks


class TestDataAccessLayerInitialization:
    """Test suite for DataAccessLayer initialization and cleanup."""

    def test_init_ValidSettings_InitializesManagersCorrectly(
        self, test_settings, data_access_layer,
    ):
        """Test that __init__ initializes database and cache managers correctly."""
        assert data_access_layer.settings is test_settings
        assert data_access_layer.db_manager is not None
        assert data_access_layer.cache_manager is not None

    def test_initialize_ValidManagers_CallsConnectOnBothManagers(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that initialize() calls connect on both database and cache managers."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)

        data_access_layer.initialize()

        mock_db_manager.connect.assert_called_once()
        mock_cache_manager.connect.assert_called_once()

    def test_cleanup_ValidManagers_CallsDisconnectOnBothManagers(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that cleanup() calls disconnect on both database and cache managers."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)

        data_access_layer.cleanup()

        mock_db_manager.disconnect.assert_called_once()
        mock_cache_manager.disconnect.assert_called_once()

    def test_health_check_BothManagersHealthy_ReturnsTrue(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that health_check() returns True when both managers are healthy."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_db_manager.check_connection.return_value = True
        mock_cache_manager.check_connection.return_value = True

        result = data_access_layer.health_check()

        assert result is True
        mock_db_manager.check_connection.assert_called_once()
        mock_cache_manager.check_connection.assert_called_once()

    def test_health_check_DatabaseUnhealthy_ReturnsFalse(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that health_check() returns False when database is unhealthy."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_db_manager.check_connection.return_value = False
        mock_cache_manager.check_connection.return_value = True

        result = data_access_layer.health_check()

        assert result is False

    def test_health_check_CacheUnhealthy_ReturnsFalse(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that health_check() returns False when cache is unhealthy."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_db_manager.check_connection.return_value = True
        mock_cache_manager.check_connection.return_value = False

        result = data_access_layer.health_check()

        assert result is False

    def test_health_check_BothManagersUnhealthy_ReturnsFalse(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that health_check() returns False when both managers are unhealthy."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_db_manager.check_connection.return_value = False
        mock_cache_manager.check_connection.return_value = False

        result = data_access_layer.health_check()

        assert result is False
