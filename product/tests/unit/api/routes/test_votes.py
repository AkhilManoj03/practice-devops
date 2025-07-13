"""
Unit tests for Votes API endpoints.

This module contains comprehensive tests for the votes API routes,
including authentication requirements, HTTP status codes, and error handling.
"""

import pytest
from unittest.mock import patch

from fastapi import HTTPException, status

from api.routes.votes import get_votes, vote_for_origami, get_all_origamis, get_origami
from core.exceptions import (
    DataPersistenceError,
    ProductNotFoundError,
    DataValidationError,
)


class TestGetVotesEndpoint:
    """Test suite for GET /api/origamis/{origami_id}/votes endpoint."""

    @pytest.mark.asyncio
    async def test_get_votes_success(self, mock_vote_service):
        """Test successful retrieval of votes for a specific origami."""
        origami_id = 1
        expected_response = {"origami_id": 1, "votes": 10}
        mock_vote_service.get_votes_for_product.return_value = expected_response

        result = await get_votes(origami_id, mock_vote_service)

        assert result == expected_response
        mock_vote_service.get_votes_for_product.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_get_votes_zero_votes(self, mock_vote_service):
        """Test retrieval of votes when origami has zero votes."""
        origami_id = 1
        expected_response = {"origami_id": 1, "votes": 0}
        mock_vote_service.get_votes_for_product.return_value = expected_response

        result = await get_votes(origami_id, mock_vote_service)

        assert result == expected_response
        assert result["votes"] == 0
        mock_vote_service.get_votes_for_product.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_get_votes_large_vote_count(self, mock_vote_service):
        """Test retrieval of votes with large vote count."""
        origami_id = 1
        expected_response = {"origami_id": 1, "votes": 999999}
        mock_vote_service.get_votes_for_product.return_value = expected_response

        result = await get_votes(origami_id, mock_vote_service)

        assert result == expected_response
        assert result["votes"] == 999999
        mock_vote_service.get_votes_for_product.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_get_votes_large_origami_id(self, mock_vote_service):
        """Test retrieval of votes with large origami ID."""
        large_origami_id = 999999
        expected_response = {"origami_id": large_origami_id, "votes": 5}
        mock_vote_service.get_votes_for_product.return_value = expected_response

        result = await get_votes(large_origami_id, mock_vote_service)

        assert result == expected_response
        assert result["origami_id"] == large_origami_id
        mock_vote_service.get_votes_for_product.assert_called_once_with(large_origami_id)

    @pytest.mark.asyncio
    async def test_get_votes_data_validation_error(self, mock_vote_service):
        """Test handling of DataValidationError from service layer."""
        origami_id = 1
        mock_vote_service.get_votes_for_product.side_effect = DataValidationError("Invalid origami ID")

        with pytest.raises(HTTPException) as exc_info:
            await get_votes(origami_id, mock_vote_service)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Error validating vote data"
        mock_vote_service.get_votes_for_product.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_get_votes_product_not_found_error(self, mock_vote_service):
        """Test handling of ProductNotFoundError from service layer."""
        origami_id = 999
        mock_vote_service.get_votes_for_product.side_effect = ProductNotFoundError("Origami not found")

        with pytest.raises(HTTPException) as exc_info:
            await get_votes(origami_id, mock_vote_service)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Origami not found"
        mock_vote_service.get_votes_for_product.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_get_votes_data_persistence_error(self, mock_vote_service):
        """Test handling of DataPersistenceError from service layer."""
        origami_id = 1
        mock_vote_service.get_votes_for_product.side_effect = DataPersistenceError("Database connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await get_votes(origami_id, mock_vote_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Unable to access vote data"
        mock_vote_service.get_votes_for_product.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_get_votes_unexpected_error(self, mock_vote_service):
        """Test handling of unexpected errors from service layer."""
        origami_id = 1
        mock_vote_service.get_votes_for_product.side_effect = ValueError("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            await get_votes(origami_id, mock_vote_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "An unexpected error occurred"
        mock_vote_service.get_votes_for_product.assert_called_once_with(origami_id)


class TestVoteForOrigamiEndpoint:
    """Test suite for POST /api/origamis/{origami_id}/vote endpoint."""

    @pytest.mark.asyncio
    async def test_vote_for_origami_success(self, mock_vote_service, authenticated_request, sample_vote_response):
        """Test successful voting for an origami with authentication."""
        origami_id = 1
        jwt_payload = {"sub": "testuser", "role": "user"}
        mock_vote_service.add_vote.return_value = sample_vote_response

        result = await vote_for_origami(authenticated_request, origami_id, mock_vote_service, jwt_payload)

        assert result == sample_vote_response
        assert result.origami_id == 1
        assert result.new_vote_count == 6
        assert "Vote added successfully" in result.message
        mock_vote_service.add_vote.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_vote_for_origami_with_different_user(
        self, mock_vote_service, authenticated_request, api_factory,
    ):
        """Test voting with different authenticated user."""
        origami_id = 1
        jwt_payload = {"sub": "different_user", "role": "admin"}
        vote_response = api_factory.create_vote_response(origami_id=origami_id, new_vote_count=15)
        mock_vote_service.add_vote.return_value = vote_response

        result = await vote_for_origami(authenticated_request, origami_id, mock_vote_service, jwt_payload)

        assert result.origami_id == origami_id
        assert result.new_vote_count == 15
        mock_vote_service.add_vote.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_vote_for_origami_large_id(
        self, mock_vote_service, authenticated_request, api_factory,
    ):
        """Test voting for origami with large ID."""
        large_origami_id = 999999
        jwt_payload = {"sub": "testuser", "role": "user"}
        vote_response = api_factory.create_vote_response(origami_id=large_origami_id, new_vote_count=1)
        mock_vote_service.add_vote.return_value = vote_response

        result = await vote_for_origami(authenticated_request, large_origami_id, mock_vote_service, jwt_payload)

        assert result.origami_id == large_origami_id
        assert result.new_vote_count == 1
        mock_vote_service.add_vote.assert_called_once_with(large_origami_id)

    @pytest.mark.asyncio
    async def test_vote_for_origami_data_persistence_error(
        self, mock_vote_service, authenticated_request,
    ):
        """Test handling of DataPersistenceError from service layer."""
        origami_id = 1
        jwt_payload = {"sub": "testuser", "role": "user"}
        mock_vote_service.add_vote.side_effect = DataPersistenceError("Database connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await vote_for_origami(authenticated_request, origami_id, mock_vote_service, jwt_payload)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Unable to save vote data"
        mock_vote_service.add_vote.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_vote_for_origami_data_validation_error(
        self, mock_vote_service, authenticated_request,
    ):
        """Test handling of DataValidationError from service layer."""
        origami_id = 1
        jwt_payload = {"sub": "testuser", "role": "user"}
        mock_vote_service.add_vote.side_effect = DataValidationError("Invalid origami ID")

        with pytest.raises(HTTPException) as exc_info:
            await vote_for_origami(authenticated_request, origami_id, mock_vote_service, jwt_payload)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Error validating vote data"
        mock_vote_service.add_vote.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_vote_for_origami_product_not_found_error(self, mock_vote_service, authenticated_request):
        """Test handling of ProductNotFoundError from service layer."""
        origami_id = 999
        jwt_payload = {"sub": "testuser", "role": "user"}
        mock_vote_service.add_vote.side_effect = ProductNotFoundError("Origami not found")

        with pytest.raises(HTTPException) as exc_info:
            await vote_for_origami(authenticated_request, origami_id, mock_vote_service, jwt_payload)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Origami not found"
        mock_vote_service.add_vote.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_vote_for_origami_unexpected_error(self, mock_vote_service, authenticated_request):
        """Test handling of unexpected errors from service layer."""
        origami_id = 1
        jwt_payload = {"sub": "testuser", "role": "user"}
        mock_vote_service.add_vote.side_effect = ValueError("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            await vote_for_origami(authenticated_request, origami_id, mock_vote_service, jwt_payload)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "An unexpected error occurred"
        mock_vote_service.add_vote.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_vote_for_origami_user_logging(self, mock_vote_service, authenticated_request, sample_vote_response):
        """Test that user information is logged when voting."""
        origami_id = 1
        jwt_payload = {"sub": "testuser", "role": "user"}
        mock_vote_service.add_vote.return_value = sample_vote_response

        with patch('api.routes.votes.logging') as mock_logging:
            await vote_for_origami(authenticated_request, origami_id, mock_vote_service, jwt_payload)
            
            # Verify debug logging was called
            mock_logging.debug.assert_called_once()
            log_call = mock_logging.debug.call_args[0][0]
            assert "testuser" in log_call
            assert str(origami_id) in log_call
            assert "voting for origami" in log_call

    @pytest.mark.asyncio
    async def test_vote_for_origami_missing_username(self, mock_vote_service, authenticated_request, sample_vote_response):
        """Test voting when JWT payload doesn't contain username."""
        origami_id = 1
        jwt_payload = {"role": "user"}  # Missing 'sub' field
        mock_vote_service.add_vote.return_value = sample_vote_response

        with patch('api.routes.votes.logging') as mock_logging:
            await vote_for_origami(authenticated_request, origami_id, mock_vote_service, jwt_payload)
            
            # Verify debug logging was called with "unknown" user
            mock_logging.debug.assert_called_once()
            log_call = mock_logging.debug.call_args[0][0]
            assert "unknown" in log_call
            assert str(origami_id) in log_call


class TestGetAllOrigamisEndpoint:
    """Test suite for GET /api/origamis endpoint (alias for products)."""

    @pytest.mark.asyncio
    async def test_get_all_origamis_success(self, mock_product_service, sample_product_models):
        """Test successful retrieval of all origamis."""
        mock_product_service.get_all_products.return_value = sample_product_models

        result = await get_all_origamis(mock_product_service)

        assert len(result) == 3
        assert result[0].id == 1
        assert result[0].name == "Product 1"
        assert result[1].id == 2
        assert result[1].name == "Product 2"
        mock_product_service.get_all_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_origamis_empty_list(self, mock_product_service):
        """Test retrieval when no origamis exist."""
        mock_product_service.get_all_products.return_value = []

        result = await get_all_origamis(mock_product_service)

        assert result == []
        mock_product_service.get_all_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_origamis_data_persistence_error(self, mock_product_service):
        """Test handling of DataPersistenceError from service layer."""
        mock_product_service.get_all_products.side_effect = DataPersistenceError("Database connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await get_all_origamis(mock_product_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Unable to access origami data"
        mock_product_service.get_all_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_origamis_product_not_found_error(self, mock_product_service):
        """Test handling of ProductNotFoundError from service layer."""
        mock_product_service.get_all_products.side_effect = ProductNotFoundError("No origamis found")

        with pytest.raises(HTTPException) as exc_info:
            await get_all_origamis(mock_product_service)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Origami not found"
        mock_product_service.get_all_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_origamis_unexpected_error(self, mock_product_service):
        """Test handling of unexpected errors from service layer."""
        mock_product_service.get_all_products.side_effect = ValueError("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            await get_all_origamis(mock_product_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "An unexpected error occurred"
        mock_product_service.get_all_products.assert_called_once()


class TestGetOrigamiEndpoint:
    """Test suite for GET /api/origamis/{origami_id} endpoint (alias for product)."""

    @pytest.mark.asyncio
    async def test_get_origami_success(self, mock_product_service, sample_product_model):
        """Test successful retrieval of a specific origami."""
        origami_id = 1
        mock_product_service.get_product_by_id.return_value = sample_product_model

        result = await get_origami(origami_id, mock_product_service)

        assert result.id == 1
        assert result.name == "Test Product"
        assert result.description == "Test Description"
        assert result.votes == 5
        mock_product_service.get_product_by_id.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_get_origami_with_zero_votes(self, mock_product_service, api_factory):
        """Test retrieval of origami with zero votes."""
        origami_id = 1
        origami_with_zero_votes = api_factory.create_product_model(votes=0)
        mock_product_service.get_product_by_id.return_value = origami_with_zero_votes

        result = await get_origami(origami_id, mock_product_service)

        assert result.votes == 0
        mock_product_service.get_product_by_id.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_get_origami_data_persistence_error(self, mock_product_service):
        """Test handling of DataPersistenceError from service layer."""
        origami_id = 1
        mock_product_service.get_product_by_id.side_effect = DataPersistenceError("Database connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await get_origami(origami_id, mock_product_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Unable to access origami data"
        mock_product_service.get_product_by_id.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_get_origami_data_validation_error(self, mock_product_service):
        """Test handling of DataValidationError from service layer."""
        origami_id = 1
        mock_product_service.get_product_by_id.side_effect = DataValidationError("Invalid origami ID")

        with pytest.raises(HTTPException) as exc_info:
            await get_origami(origami_id, mock_product_service)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Error validating origami data"
        mock_product_service.get_product_by_id.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_get_origami_product_not_found_error(self, mock_product_service):
        """Test handling of ProductNotFoundError from service layer."""
        origami_id = 999
        mock_product_service.get_product_by_id.side_effect = ProductNotFoundError("Origami not found")

        with pytest.raises(HTTPException) as exc_info:
            await get_origami(origami_id, mock_product_service)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Origami not found"
        mock_product_service.get_product_by_id.assert_called_once_with(origami_id)

    @pytest.mark.asyncio
    async def test_get_origami_unexpected_error(self, mock_product_service):
        """Test handling of unexpected errors from service layer."""
        origami_id = 1
        mock_product_service.get_product_by_id.side_effect = ValueError("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            await get_origami(origami_id, mock_product_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "An unexpected error occurred"
        mock_product_service.get_product_by_id.assert_called_once_with(origami_id)


class TestVotesEndpointIntegration:
    """Integration tests for votes endpoints."""

    @pytest.mark.asyncio
    async def test_vote_and_get_votes_consistency(self, mock_vote_service, authenticated_request, api_factory):
        """Test that voting and getting votes return consistent data."""
        origami_id = 1
        jwt_payload = {"sub": "testuser", "role": "user"}
        
        # Set up vote response
        vote_response = api_factory.create_vote_response(origami_id=origami_id, new_vote_count=6)
        mock_vote_service.add_vote.return_value = vote_response
        
        # Vote for origami
        vote_result = await vote_for_origami(authenticated_request, origami_id, mock_vote_service, jwt_payload)
        
        # Set up get votes response
        get_votes_response = {"origami_id": origami_id, "votes": 6}
        mock_vote_service.get_votes_for_product.return_value = get_votes_response
        
        # Get votes for origami
        votes_result = await get_votes(origami_id, mock_vote_service)
        
        # Verify consistency
        assert vote_result.origami_id == votes_result["origami_id"]
        assert vote_result.new_vote_count == votes_result["votes"]

    @pytest.mark.asyncio
    async def test_votes_endpoint_error_logging(self, mock_vote_service):
        """Test that errors are properly logged in votes endpoints."""
        origami_id = 1
        mock_vote_service.get_votes_for_product.side_effect = DataPersistenceError("Database error")

        with patch('api.routes.votes.logging') as mock_logging:
            with pytest.raises(HTTPException):
                await get_votes(origami_id, mock_vote_service)
            
            # Verify error was logged
            mock_logging.error.assert_called_once()
            log_call = mock_logging.error.call_args[0][0]
            assert "Infrastructure error" in log_call
            assert str(origami_id) in log_call 