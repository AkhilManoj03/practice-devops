"""
Tests for DataAccessLayer vote operations.

This module tests vote operations including database updates and cache invalidation.
"""

import pytest
from core.exceptions import DataValidationError, ProductNotFoundError
from .conftest import setup_data_access_with_mocks


class TestDataAccessLayerVoteOperations:
    """Test suite for DataAccessLayer vote operations."""

    def test_add_vote_InvalidId_RaisesDataValidationError(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that add_vote() raises DataValidationError for invalid product ID."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        invalid_product_id = 0

        with pytest.raises(DataValidationError, match="Product ID must be positive"):
            data_access_layer.add_vote(invalid_product_id)

    def test_add_vote_NegativeId_RaisesDataValidationError(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that add_vote() raises DataValidationError for negative product ID."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        invalid_product_id = -5

        with pytest.raises(DataValidationError, match="Product ID must be positive"):
            data_access_layer.add_vote(invalid_product_id)

    def test_add_vote_ValidId_UpdatesDatabaseAndInvalidatesCache(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that add_vote() updates database and invalidates cache."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        vote_response = data_factory.create_vote_response()
        mock_db_manager.add_vote.return_value = vote_response
        product_id = 1

        result = data_access_layer.add_vote(product_id)

        assert result == vote_response
        mock_db_manager.add_vote.assert_called_once_with(product_id)
        mock_cache_manager.invalidate_product.assert_called_once_with(product_id)

    def test_add_vote_CacheDisconnected_UpdatesDatabaseOnly(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that add_vote() updates database only when cache is disconnected."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = False
        vote_response = data_factory.create_vote_response()
        mock_db_manager.add_vote.return_value = vote_response
        product_id = 1

        result = data_access_layer.add_vote(product_id)

        assert result == vote_response
        mock_db_manager.add_vote.assert_called_once_with(product_id)
        mock_cache_manager.invalidate_product.assert_not_called()

    def test_add_vote_DatabaseError_PropagatesException(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that add_vote() propagates database errors."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_db_manager.add_vote.side_effect = ProductNotFoundError("Product not found")
        product_id = 1

        with pytest.raises(ProductNotFoundError, match="Product not found"):
            data_access_layer.add_vote(product_id)

        mock_cache_manager.invalidate_product.assert_not_called()

    def test_add_vote_DatabaseErrorWithCacheConnected_DoesNotInvalidateCache(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that add_vote() does not invalidate cache when database error occurs."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        mock_db_manager.add_vote.side_effect = ProductNotFoundError("Product not found")
        product_id = 1

        with pytest.raises(ProductNotFoundError):
            data_access_layer.add_vote(product_id)

        mock_cache_manager.invalidate_product.assert_not_called()

    def test_add_vote_LargeProductId_HandlesCorrectly(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that add_vote() handles large product IDs correctly."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        large_product_id = 999999
        vote_response = data_factory.create_vote_response(product_id=large_product_id)
        mock_db_manager.add_vote.return_value = vote_response

        result = data_access_layer.add_vote(large_product_id)

        assert result == vote_response
        mock_db_manager.add_vote.assert_called_once_with(large_product_id)
        mock_cache_manager.invalidate_product.assert_called_once_with(large_product_id)

    def test_add_vote_SuccessfulVote_ReturnsCorrectResponseStructure(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that add_vote() returns response with correct structure."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        vote_response = data_factory.create_vote_response(
            product_id=1, 
            new_vote_count=10
        )
        mock_db_manager.add_vote.return_value = vote_response
        product_id = 1

        result = data_access_layer.add_vote(product_id)

        assert "origami_id" in result
        assert "new_vote_count" in result
        assert "message" in result
        assert result["origami_id"] == product_id
        assert result["new_vote_count"] == 10
        assert isinstance(result["message"], str)

    def test_add_vote_MultipleVotes_EachInvalidatesCache(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that add_vote() invalidates cache for each vote operation."""
        setup_data_access_with_mocks(data_access_layer, mock_db_manager, mock_cache_manager)
        mock_cache_manager.is_connected = True
        vote_response = data_factory.create_vote_response()
        mock_db_manager.add_vote.return_value = vote_response
        product_id = 1

        data_access_layer.add_vote(product_id)
        data_access_layer.add_vote(product_id)
        data_access_layer.add_vote(product_id)

        # Verify database was called 3 times
        assert mock_db_manager.add_vote.call_count == 3
        # Verify cache was invalidated 3 times
        assert mock_cache_manager.invalidate_product.call_count == 3
