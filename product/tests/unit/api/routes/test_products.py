"""
Unit tests for Products API endpoints.

This module contains comprehensive tests for the products API routes,
focusing on HTTP status codes, response formats, and error handling.
"""

import pytest
from unittest.mock import patch

from fastapi import HTTPException, status

from api.routes.products import get_products, get_product
from core.exceptions import (
    DataPersistenceError,
    ProductNotFoundError,
    DataValidationError,
)


class TestGetProductsEndpoint:
    """Test suite for GET /api/products endpoint."""

    @pytest.mark.asyncio
    async def test_get_products_success(self, mock_product_service, sample_product_models):
        """Test successful retrieval of all products."""
        mock_product_service.get_all_products.return_value = sample_product_models

        result = await get_products(mock_product_service)

        assert len(result) == 3
        assert all(hasattr(product, 'id') for product in result)
        assert all(hasattr(product, 'name') for product in result)
        assert all(hasattr(product, 'votes') for product in result)
        assert result[0].id == 1
        assert result[0].name == "Product 1"
        assert result[0].votes == 2
        assert result[1].id == 2
        assert result[1].name == "Product 2"
        assert result[1].votes == 4
        mock_product_service.get_all_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_products_empty_list(self, mock_product_service):
        """Test retrieval when no products exist."""
        mock_product_service.get_all_products.return_value = []

        result = await get_products(mock_product_service)

        assert result == []
        mock_product_service.get_all_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_products_single_product(self, mock_product_service, api_factory):
        """Test retrieval when only one product exists."""
        single_product = [api_factory.create_product_model()]
        mock_product_service.get_all_products.return_value = single_product

        result = await get_products(mock_product_service)

        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].name == "Test Product"
        mock_product_service.get_all_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_products_data_persistence_error(self, mock_product_service):
        """Test handling of DataPersistenceError from service layer."""
        mock_product_service.get_all_products.side_effect = DataPersistenceError("Database connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await get_products(mock_product_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Unable to access product data"
        mock_product_service.get_all_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_products_product_not_found_error(self, mock_product_service):
        """Test handling of ProductNotFoundError from service layer."""
        mock_product_service.get_all_products.side_effect = ProductNotFoundError("No products found in database")

        with pytest.raises(HTTPException) as exc_info:
            await get_products(mock_product_service)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Products not found"
        mock_product_service.get_all_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_products_unexpected_error(self, mock_product_service):
        """Test handling of unexpected errors from service layer."""
        mock_product_service.get_all_products.side_effect = ValueError("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            await get_products(mock_product_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "An unexpected error occurred"
        mock_product_service.get_all_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_products_runtime_error(self, mock_product_service):
        """Test handling of RuntimeError from service layer."""
        mock_product_service.get_all_products.side_effect = RuntimeError("Runtime error occurred")

        with pytest.raises(HTTPException) as exc_info:
            await get_products(mock_product_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "An unexpected error occurred"
        mock_product_service.get_all_products.assert_called_once()


class TestGetProductEndpoint:
    """Test suite for GET /api/products/{product_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_product_success(self, mock_product_service, sample_product_model):
        """Test successful retrieval of a specific product."""
        product_id = 1
        mock_product_service.get_product_by_id.return_value = sample_product_model

        result = await get_product(product_id, mock_product_service)

        assert result.id == 1
        assert result.name == "Test Product"
        assert result.description == "Test Description"
        assert result.image_url == "/test/image.png"
        assert result.votes == 5
        mock_product_service.get_product_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_product_with_zero_votes(self, mock_product_service, api_factory):
        """Test retrieval of product with zero votes."""
        product_id = 1
        product_with_zero_votes = api_factory.create_product_model(votes=0)
        mock_product_service.get_product_by_id.return_value = product_with_zero_votes

        result = await get_product(product_id, mock_product_service)

        assert result.votes == 0
        mock_product_service.get_product_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_product_with_high_votes(self, mock_product_service, api_factory):
        """Test retrieval of product with high vote count."""
        product_id = 1
        product_with_high_votes = api_factory.create_product_model(votes=999999)
        mock_product_service.get_product_by_id.return_value = product_with_high_votes

        result = await get_product(product_id, mock_product_service)

        assert result.votes == 999999
        mock_product_service.get_product_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_product_large_id(self, mock_product_service, api_factory):
        """Test retrieval of product with large ID."""
        large_product_id = 999999
        product = api_factory.create_product_model(product_id=large_product_id)
        mock_product_service.get_product_by_id.return_value = product

        result = await get_product(large_product_id, mock_product_service)

        assert result.id == large_product_id
        mock_product_service.get_product_by_id.assert_called_once_with(large_product_id)

    @pytest.mark.asyncio
    async def test_get_product_data_persistence_error(self, mock_product_service):
        """Test handling of DataPersistenceError from service layer."""
        product_id = 1
        mock_product_service.get_product_by_id.side_effect = DataPersistenceError("Database connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await get_product(product_id, mock_product_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Unable to access product data"
        mock_product_service.get_product_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_product_data_validation_error(self, mock_product_service):
        """Test handling of DataValidationError from service layer."""
        product_id = 1
        mock_product_service.get_product_by_id.side_effect = DataValidationError("Invalid product ID")

        with pytest.raises(HTTPException) as exc_info:
            await get_product(product_id, mock_product_service)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Error validating product data"
        mock_product_service.get_product_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_product_not_found_error(self, mock_product_service):
        """Test handling of ProductNotFoundError from service layer."""
        product_id = 999
        mock_product_service.get_product_by_id.side_effect = ProductNotFoundError("Product not found in database")

        with pytest.raises(HTTPException) as exc_info:
            await get_product(product_id, mock_product_service)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Product not found"
        mock_product_service.get_product_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_product_unexpected_error(self, mock_product_service):
        """Test handling of unexpected errors from service layer."""
        product_id = 1
        mock_product_service.get_product_by_id.side_effect = ValueError("Unexpected error")

        with pytest.raises(HTTPException) as exc_info:
            await get_product(product_id, mock_product_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "An unexpected error occurred"
        mock_product_service.get_product_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_product_type_error(self, mock_product_service):
        """Test handling of TypeError from service layer."""
        product_id = 1
        mock_product_service.get_product_by_id.side_effect = TypeError("Type error occurred")

        with pytest.raises(HTTPException) as exc_info:
            await get_product(product_id, mock_product_service)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "An unexpected error occurred"
        mock_product_service.get_product_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_product_boundary_ids(self, mock_product_service, api_factory):
        """Test retrieval with boundary product IDs."""
        boundary_ids = [1, 2, 100, 999, 1000]
        
        for product_id in boundary_ids:
            product = api_factory.create_product_model(product_id=product_id)
            mock_product_service.get_product_by_id.return_value = product

            result = await get_product(product_id, mock_product_service)

            assert result.id == product_id
            mock_product_service.get_product_by_id.assert_called_with(product_id)

        # Verify all calls were made
        assert mock_product_service.get_product_by_id.call_count == len(boundary_ids)


class TestProductsEndpointIntegration:
    """Integration tests for products endpoints."""

    @pytest.mark.asyncio
    async def test_get_products_and_get_product_consistency(self, mock_product_service, api_factory):
        """Test that get_products and get_product return consistent data."""
        # Set up products list
        products = api_factory.create_product_list(2)
        mock_product_service.get_all_products.return_value = products
        
        # Get all products
        all_products = await get_products(mock_product_service)
        
        # Get individual product
        mock_product_service.get_product_by_id.return_value = products[0]
        individual_product = await get_product(1, mock_product_service)
        
        # Verify consistency
        assert all_products[0].id == individual_product.id
        assert all_products[0].name == individual_product.name
        assert all_products[0].votes == individual_product.votes

    @pytest.mark.asyncio
    async def test_products_endpoint_error_logging(self, mock_product_service):
        """Test that errors are properly logged (integration with logging system)."""
        product_id = 1
        mock_product_service.get_product_by_id.side_effect = DataPersistenceError("Database error")

        with patch('api.routes.products.logging') as mock_logging:
            with pytest.raises(HTTPException):
                await get_product(product_id, mock_product_service)
            
            # Verify error was logged
            mock_logging.error.assert_called_once()
            log_call = mock_logging.error.call_args[0][0]
            assert "Infrastructure error" in log_call
            assert str(product_id) in log_call
