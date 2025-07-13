"""
Unit tests for VoteService.

This module contains comprehensive tests for the VoteService class,
focusing on business logic, error handling, and data transformation.
"""

import pytest

from core.services.vote_service import VoteService
from core.models.votes import VoteResponse
from core.exceptions import (
    DataPersistenceError,
    ProductNotFoundError,
)


class TestVoteService:
    """Test suite for VoteService class."""

    @pytest.fixture
    def vote_service(self, mock_data_access):
        """Create a VoteService instance with mocked data access."""
        return VoteService(mock_data_access)

    @pytest.mark.asyncio
    async def test_get_votes_for_product_success(
        self, vote_service, mock_data_access,
    ):
        """Test successful retrieval of votes for a product."""
        product_id = 1
        expected_votes = 5
        mock_data_access.get_votes_for_product.return_value = expected_votes

        result = await vote_service.get_votes_for_product(product_id)

        assert result == {"origami_id": product_id, "votes": expected_votes}
        mock_data_access.get_votes_for_product.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_votes_for_product_with_zero_votes(self, vote_service, mock_data_access):
        """Test retrieval of votes when product has zero votes."""
        product_id = 2
        expected_votes = 0
        mock_data_access.get_votes_for_product.return_value = expected_votes

        result = await vote_service.get_votes_for_product(product_id)

        assert result == {"origami_id": product_id, "votes": expected_votes}
        mock_data_access.get_votes_for_product.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_add_vote_success(self, vote_service, mock_data_access, sample_vote_data):
        """Test successful addition of a vote."""
        product_id = 1
        mock_data_access.add_vote.return_value = sample_vote_data

        result = await vote_service.add_vote(product_id)

        assert isinstance(result, VoteResponse)
        assert result.origami_id == 1
        assert result.new_vote_count == 6
        assert result.message == "Vote added successfully for Origami Crane"
        mock_data_access.add_vote.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_votes_for_product_propagates_data_persistence_error(
        self, vote_service, mock_data_access,
    ):
        """Test that DataPersistenceError is properly propagated for get_votes_for_product."""
        product_id = 1
        mock_data_access.get_votes_for_product.side_effect = DataPersistenceError("Database connection failed")

        with pytest.raises(DataPersistenceError) as exc_info:
            await vote_service.get_votes_for_product(product_id)
        
        assert str(exc_info.value) == "Database connection failed"
        mock_data_access.get_votes_for_product.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_votes_for_product_propagates_product_not_found_error(
        self, vote_service, mock_data_access,
    ):
        """Test that ProductNotFoundError is properly propagated for get_votes_for_product."""
        product_id = 999
        mock_data_access.get_votes_for_product.side_effect = ProductNotFoundError("Product not found in database")

        with pytest.raises(ProductNotFoundError) as exc_info:
            await vote_service.get_votes_for_product(product_id)
        
        assert str(exc_info.value) == "Product not found in database"
        mock_data_access.get_votes_for_product.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_votes_for_product_handles_unexpected_exceptions(
        self, vote_service, mock_data_access,
    ):
        """Test that unexpected exceptions are caught and transformed for get_votes_for_product."""
        product_id = 1
        mock_data_access.get_votes_for_product.side_effect = ValueError("Unexpected error")

        with pytest.raises(Exception) as exc_info:
            await vote_service.get_votes_for_product(product_id)
        
        assert str(exc_info.value) == "An unexpected error occurred"
        mock_data_access.get_votes_for_product.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_add_vote_propagates_data_persistence_error(
        self, vote_service, mock_data_access,
    ):
        """Test that DataPersistenceError is properly propagated for add_vote."""
        product_id = 1
        mock_data_access.add_vote.side_effect = DataPersistenceError("Database connection failed")

        with pytest.raises(DataPersistenceError) as exc_info:
            await vote_service.add_vote(product_id)
        
        assert str(exc_info.value) == "Database connection failed"
        mock_data_access.add_vote.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_add_vote_propagates_product_not_found_error(
        self, vote_service, mock_data_access,
    ):
        """Test that ProductNotFoundError is properly propagated for add_vote."""
        product_id = 999
        mock_data_access.add_vote.side_effect = ProductNotFoundError("Product not found in database")

        with pytest.raises(ProductNotFoundError) as exc_info:
            await vote_service.add_vote(product_id)
        
        assert str(exc_info.value) == "Product not found in database"
        mock_data_access.add_vote.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_add_vote_handles_unexpected_exceptions(self, vote_service, mock_data_access):
        """Test that unexpected exceptions are caught and transformed for add_vote."""
        product_id = 1
        mock_data_access.add_vote.side_effect = ValueError("Unexpected error")

        with pytest.raises(Exception) as exc_info:
            await vote_service.add_vote(product_id)
        
        assert str(exc_info.value) == "An unexpected error occurred"
        mock_data_access.add_vote.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_vote_response_model_creation_from_dict(self, vote_service, mock_data_access):
        """Test that dict data is properly transformed to VoteResponse model."""
        product_id = 42
        vote_data = {
            "origami_id": 42,
            "new_vote_count": 15,
            "message": "Vote added successfully for Test Product",
        }
        mock_data_access.add_vote.return_value = vote_data

        result = await vote_service.add_vote(product_id)

        assert isinstance(result, VoteResponse)
        assert result.origami_id == 42
        assert result.new_vote_count == 15
        assert result.message == "Vote added successfully for Test Product"

    @pytest.mark.asyncio
    async def test_vote_response_with_single_vote(self, vote_service, mock_data_access):
        """Test vote response when adding the first vote."""
        product_id = 1
        vote_data = {
            "origami_id": 1,
            "new_vote_count": 1,
            "message": "Vote added successfully for New Product",
        }
        mock_data_access.add_vote.return_value = vote_data

        result = await vote_service.add_vote(product_id)

        assert result.new_vote_count == 1

    @pytest.mark.asyncio
    async def test_vote_response_with_high_vote_count(self, vote_service, mock_data_access):
        """Test vote response with high vote count."""
        product_id = 1
        vote_data = {
            "origami_id": 1,
            "new_vote_count": 9999,
            "message": "Vote added successfully for Popular Product",
        }
        mock_data_access.add_vote.return_value = vote_data

        result = await vote_service.add_vote(product_id)

        assert result.new_vote_count == 9999

    @pytest.mark.asyncio
    async def test_get_votes_response_format(self, vote_service, mock_data_access):
        """Test that get_votes_for_product returns correct response format."""
        product_id = 123
        expected_votes = 42
        mock_data_access.get_votes_for_product.return_value = expected_votes

        result = await vote_service.get_votes_for_product(product_id)

        assert isinstance(result, dict)
        assert "origami_id" in result
        assert "votes" in result
        assert result["origami_id"] == product_id
        assert result["votes"] == expected_votes

    @pytest.mark.asyncio
    async def test_multiple_vote_operations(self, vote_service, mock_data_access):
        """Test multiple vote operations in sequence."""
        # First vote
        product_id_1 = 1
        vote_data_1 = {
            "origami_id": 1,
            "new_vote_count": 6,
            "message": "Vote added successfully for Product 1",
        }
        mock_data_access.add_vote.return_value = vote_data_1

        result_1 = await vote_service.add_vote(product_id_1)
        assert result_1.new_vote_count == 6

        # Second vote for different product
        product_id_2 = 2
        vote_data_2 = {
            "origami_id": 2,
            "new_vote_count": 3,
            "message": "Vote added successfully for Product 2",
        }
        mock_data_access.add_vote.return_value = vote_data_2

        result_2 = await vote_service.add_vote(product_id_2)
        assert result_2.new_vote_count == 3

        # Verify both calls were made
        assert mock_data_access.add_vote.call_count == 2

    def test_service_initialization(self, mock_data_access):
        """Test that VoteService initializes correctly with data access dependency."""
        service = VoteService(mock_data_access)

        assert service.data_access == mock_data_access

    def test_service_initialization_with_none_data_access(self):
        """Test that VoteService can be initialized with None data access (for testing)."""
        service = VoteService(None)

        assert service.data_access is None
