"""
Tests for DataAccessLayer product operations.

This module tests product retrieval operations including cache coordination.
"""

import pytest
from core.exceptions import DataValidationError
from .conftest import setup_data_access_with_mocks


class TestDataAccessLayerProductOperations:
    """Test suite for DataAccessLayer product operations."""

    def test_get_products_ValidData_ReturnsProductsFromDatabase(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that get_products() always returns products from database."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        expected_products = data_factory.create_product_list()
        mock_db_manager.get_products.return_value = expected_products

        result = data_access_layer.get_products()

        assert result == expected_products
        mock_db_manager.get_products.assert_called_once()
        # Cache should not be called for get_products
        mock_cache_manager.get_product.assert_not_called()

    def test_get_product_by_id_InvalidId_RaisesDataValidationError(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that get_product_by_id() raises DataValidationError for invalid product ID."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        invalid_product_id = 0

        with pytest.raises(DataValidationError, match="Product ID must be positive"):
            data_access_layer.get_product_by_id(invalid_product_id)

    def test_get_product_by_id_NegativeId_RaisesDataValidationError(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that get_product_by_id() raises DataValidationError for negative product ID."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        invalid_product_id = -1

        with pytest.raises(DataValidationError, match="Product ID must be positive"):
            data_access_layer.get_product_by_id(invalid_product_id)

    def test_get_product_by_id_CacheHit_ReturnsProductFromCache(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that get_product_by_id() returns product from cache when available."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        product_data = data_factory.create_product_dict()
        mock_cache_manager.get_product.return_value = product_data
        product_id = 1

        result = data_access_layer.get_product_by_id(product_id)

        assert result == product_data
        mock_cache_manager.get_product.assert_called_once_with(product_id)
        mock_db_manager.get_product_by_id.assert_not_called()

    def test_get_product_by_id_CacheMiss_ReturnsProductFromDatabaseAndCaches(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that get_product_by_id() fetches from database and caches when cache miss."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        mock_cache_manager.get_product.return_value = None  # Cache miss
        product_data = data_factory.create_product_dict()
        mock_db_manager.get_product_by_id.return_value = product_data
        product_id = 1

        result = data_access_layer.get_product_by_id(product_id)

        assert result == product_data
        mock_cache_manager.get_product.assert_called_once_with(product_id)
        mock_db_manager.get_product_by_id.assert_called_once_with(product_id)
        mock_cache_manager.set_product.assert_called_once_with(product_id, product_data)

    def test_get_product_by_id_CacheDisconnected_ReturnsProductFromDatabase(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that get_product_by_id() fetches from database when cache is disconnected."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = False
        product_data = data_factory.create_product_dict()
        mock_db_manager.get_product_by_id.return_value = product_data
        product_id = 1

        result = data_access_layer.get_product_by_id(product_id)

        assert result == product_data
        mock_cache_manager.get_product.assert_not_called()
        mock_db_manager.get_product_by_id.assert_called_once_with(product_id)
        mock_cache_manager.set_product.assert_not_called()

    def test_get_product_by_id_CacheConnectedButNotCached_FetchesFromDatabaseAndCaches(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """
        Test that get_product_by_id() fetches from database and caches when cache is connected
        but product not cached.
        """
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        mock_cache_manager.get_product.return_value = None  # Not cached
        product_data = data_factory.create_product_dict()
        mock_db_manager.get_product_by_id.return_value = product_data
        product_id = 1

        result = data_access_layer.get_product_by_id(product_id)

        assert result == product_data
        mock_cache_manager.get_product.assert_called_once_with(product_id)
        mock_db_manager.get_product_by_id.assert_called_once_with(product_id)
        mock_cache_manager.set_product.assert_called_once_with(product_id, product_data)

    def test_get_votes_for_product_InvalidId_RaisesDataValidationError(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that get_votes_for_product() raises DataValidationError for invalid product ID."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        invalid_product_id = -1

        with pytest.raises(DataValidationError, match="Product ID must be positive"):
            data_access_layer.get_votes_for_product(invalid_product_id)

    def test_get_votes_for_product_ZeroId_RaisesDataValidationError(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that get_votes_for_product() raises DataValidationError for zero product ID."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        invalid_product_id = 0

        with pytest.raises(DataValidationError, match="Product ID must be positive"):
            data_access_layer.get_votes_for_product(invalid_product_id)

    def test_get_votes_for_product_CacheHit_ReturnsVotesFromCache(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that get_votes_for_product() returns votes from cache when available."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        product_data = data_factory.create_product_dict(votes=10)
        mock_cache_manager.get_product.return_value = product_data
        product_id = 1

        result = data_access_layer.get_votes_for_product(product_id)

        assert result == 10
        mock_cache_manager.get_product.assert_called_once_with(product_id)
        mock_db_manager.get_votes_for_product.assert_not_called()

    def test_get_votes_for_product_CacheMiss_ReturnsVotesFromDatabase(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that get_votes_for_product() fetches from database when cache miss."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        mock_cache_manager.get_product.return_value = None  # Cache miss
        mock_db_manager.get_votes_for_product.return_value = 7
        product_id = 1

        result = data_access_layer.get_votes_for_product(product_id)

        assert result == 7
        mock_cache_manager.get_product.assert_called_once_with(product_id)
        mock_db_manager.get_votes_for_product.assert_called_once_with(product_id)

    def test_get_votes_for_product_CacheHitNoVotes_ReturnsZero(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that get_votes_for_product() returns 0 when cached product has no votes."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        product_data = data_factory.create_product_dict()
        del product_data['votes']  # Remove votes key
        mock_cache_manager.get_product.return_value = product_data
        product_id = 1

        result = data_access_layer.get_votes_for_product(product_id)

        assert result == 0

    def test_get_votes_for_product_CacheDisconnected_ReturnsVotesFromDatabase(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that get_votes_for_product() fetches from database when cache is disconnected."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = False
        mock_db_manager.get_votes_for_product.return_value = 15
        product_id = 1

        result = data_access_layer.get_votes_for_product(product_id)

        assert result == 15
        mock_cache_manager.get_product.assert_not_called()
        mock_db_manager.get_votes_for_product.assert_called_once_with(product_id)
