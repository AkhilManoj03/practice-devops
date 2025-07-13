"""
Tests for DataAccessLayer initialization and lifecycle management.

This module tests initialization, cleanup, and health check functionality.
"""
import pytest

from core.exceptions import DataValidationError, DataPersistenceError
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

class TestDataAccessLayerProductOperations:
    """Test suite for DataAccessLayer product operations."""

    def test_get_products_ValidData_ReturnsProductsFromDatabase(
        self, data_access_layer, mock_db_manager, mock_cache_manager, test_data_factory,
    ):
        """Test that get_products() returns products from database when valid data exists."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        expected_products = test_data_factory.create_product_list()
        mock_db_manager.get_products.return_value = expected_products

        result = data_access_layer.get_products()

        assert result == expected_products
        mock_db_manager.get_products.assert_called_once()

    def test_get_products_DatabaseError_PropagatesException(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that get_products() propagates database errors."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_db_manager.get_products.side_effect = DataPersistenceError("Database connection failed")

        with pytest.raises(DataPersistenceError, match="Database connection failed"):
            data_access_layer.get_products()

        mock_db_manager.get_products.assert_called_once()

    def test_get_product_by_id_InvalidId_RaisesDataValidationError(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that get_product_by_id() raises DataValidationError for invalid ID."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        invalid_id = 0  # Invalid ID should be 0 or negative, not string

        with pytest.raises(DataValidationError, match="Product ID must be positive"):
            data_access_layer.get_product_by_id(invalid_id)

        # Should not call database if ID is invalid
        mock_db_manager.get_product_by_id.assert_not_called()

    def test_get_product_by_id_CacheHit_ReturnsProductFromCache(
        self, data_access_layer, mock_db_manager, mock_cache_manager, test_data_factory,
    ):
        """Test that get_product_by_id() returns product from cache when cache hit occurs."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        product_id = 1
        product_data = test_data_factory.create_product_dict()
        mock_cache_manager.get_product.return_value = product_data

        result = data_access_layer.get_product_by_id(product_id)

        assert result == product_data
        mock_cache_manager.get_product.assert_called_once_with(product_id)  # Code passes int, not str
        mock_db_manager.get_product_by_id.assert_not_called()

    def test_get_product_by_id_CacheMiss_ReturnsProductFromDatabaseAndCaches(
        self, data_access_layer, mock_db_manager, mock_cache_manager, test_data_factory,
    ):
        """Test that get_product_by_id() returns product from database and caches it when cache miss occurs."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        product_id = 1
        product_data = test_data_factory.create_product_dict()
        mock_cache_manager.get_product.return_value = None  # Cache miss
        mock_db_manager.get_product_by_id.return_value = product_data

        result = data_access_layer.get_product_by_id(product_id)

        assert result == product_data
        mock_cache_manager.get_product.assert_called_once_with(product_id)  # Code passes int, not str
        mock_db_manager.get_product_by_id.assert_called_once_with(product_id)
        mock_cache_manager.set_product.assert_called_once_with(product_id, product_data)  # Code passes int, not str

    def test_get_votes_for_product_CacheHit_ReturnsVotesFromCache(
        self, data_access_layer, mock_db_manager, mock_cache_manager, test_data_factory,
    ):
        """Test that get_votes_for_product() returns votes from cache when cache hit occurs."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        product_id = 1
        product_data = test_data_factory.create_product_dict(votes=10)
        mock_cache_manager.get_product.return_value = product_data

        result = data_access_layer.get_votes_for_product(product_id)

        assert result == 10
        mock_cache_manager.get_product.assert_called_once_with(product_id)  # Code passes int, not str
        mock_db_manager.get_votes_for_product.assert_not_called()

    def test_get_votes_for_product_CacheMiss_ReturnsVotesFromDatabase(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that get_votes_for_product() returns votes from database when cache miss occurs."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        product_id = 1
        expected_votes = 8
        mock_cache_manager.get_product.return_value = None  # Cache miss
        mock_db_manager.get_votes_for_product.return_value = expected_votes

        result = data_access_layer.get_votes_for_product(product_id)

        assert result == expected_votes
        mock_cache_manager.get_product.assert_called_once_with(product_id)  # Code passes int, not str
        mock_db_manager.get_votes_for_product.assert_called_once_with(product_id)


class TestDataAccessLayerVoteOperations:
    """Test vote-related operations in DataAccessLayer."""

    def test_add_vote_ValidId_UpdatesDatabaseAndInvalidatesCache(
        self, data_access_layer, mock_db_manager, mock_cache_manager, test_data_factory,
    ):
        """Test that add_vote() updates database and invalidates cache."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        vote_response = test_data_factory.create_vote_response_dict()
        mock_db_manager.add_vote.return_value = vote_response
        product_id = 1

        result = data_access_layer.add_vote(product_id)

        assert result == vote_response
        mock_db_manager.add_vote.assert_called_once_with(product_id)
        mock_cache_manager.invalidate_product.assert_called_once_with(product_id)  # Code passes int, not str

    def test_add_vote_DatabaseError_PropagatesException(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that add_vote() propagates database errors."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_db_manager.add_vote.side_effect = DataPersistenceError("Database connection failed")
        product_id = 1

        with pytest.raises(DataPersistenceError, match="Database connection failed"):
            data_access_layer.add_vote(product_id)

        mock_db_manager.add_vote.assert_called_once_with(product_id)

    def test_add_vote_SuccessfulVote_ReturnsCorrectResponseStructure(
        self, data_access_layer, mock_db_manager, mock_cache_manager, test_data_factory,
    ):
        """Test that add_vote() returns response with correct structure."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        vote_response = test_data_factory.create_vote_response_dict(
            origami_id=1,
            new_vote_count=10,
        )
        mock_db_manager.add_vote.return_value = vote_response
        product_id = 1

        result = data_access_layer.add_vote(product_id)

        assert "origami_id" in result
        assert "new_vote_count" in result
        assert "message" in result
        assert result["origami_id"] == 1
        assert result["new_vote_count"] == 10
        mock_db_manager.add_vote.assert_called_once_with(product_id)
        mock_cache_manager.invalidate_product.assert_called_once_with(product_id)  # Code passes int, not str
