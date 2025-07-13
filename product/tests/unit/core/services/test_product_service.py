"""
Unit tests for ProductService.

This module contains comprehensive tests for the ProductService class,
focusing on business logic, error handling, and data transformation.
"""

import pytest

from core.services.product_service import ProductService
from core.models.products import Product
from core.exceptions import (
    DataPersistenceError,
    ProductNotFoundError,
)


class TestProductService:
    """Test suite for ProductService class."""

    @pytest.fixture
    def product_service(self, mock_data_access):
        """Create a ProductService instance with mocked data access."""
        return ProductService(mock_data_access)

    @pytest.mark.asyncio
    async def test_get_all_products_success(
        self, product_service, mock_data_access, sample_products_data,
    ):
        """Test successful retrieval of all products."""
        mock_data_access.get_products.return_value = sample_products_data

        result = await product_service.get_all_products()

        assert len(result) == 2
        assert all(isinstance(product, Product) for product in result)
        assert result[0].id == 1
        assert result[0].name == "Origami Crane"
        assert result[0].votes == 5
        assert result[1].id == 2
        assert result[1].name == "Origami Frog"
        assert result[1].votes == 3
        mock_data_access.get_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_product_by_id_success(
        self, product_service, mock_data_access, sample_product_data,
    ):
        """Test successful retrieval of a product by ID."""
        product_id = 1
        mock_data_access.get_product_by_id.return_value = sample_product_data

        result = await product_service.get_product_by_id(product_id)

        assert isinstance(result, Product)
        assert result.id == 1
        assert result.name == "Origami Crane"
        assert result.description == "A beautiful origami crane"
        assert result.image_url == "/static/images/origami/001-origami.png"
        assert result.votes == 5
        mock_data_access.get_product_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_all_products_propagates_data_persistence_error(
        self, product_service, mock_data_access,
    ):
        """Test that DataPersistenceError is properly propagated."""
        mock_data_access.get_products.side_effect = DataPersistenceError("Database connection failed")

        with pytest.raises(DataPersistenceError) as exc_info:
            await product_service.get_all_products()
        
        assert str(exc_info.value) == "Database connection failed"
        mock_data_access.get_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_products_propagates_product_not_found_error(
        self, product_service, mock_data_access,
    ):
        """Test that ProductNotFoundError is properly propagated."""
        mock_data_access.get_products.side_effect = ProductNotFoundError("No products found in database")

        with pytest.raises(ProductNotFoundError) as exc_info:
            await product_service.get_all_products()
        
        assert str(exc_info.value) == "No products found in database"
        mock_data_access.get_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_products_handles_unexpected_exceptions(
        self, product_service, mock_data_access,
    ):
        """Test that unexpected exceptions are caught and transformed."""
        mock_data_access.get_products.side_effect = ValueError("Unexpected error")

        with pytest.raises(Exception) as exc_info:
            await product_service.get_all_products()
        
        assert str(exc_info.value) == "An unexpected error occurred"
        mock_data_access.get_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_product_by_id_propagates_data_persistence_error(
        self, product_service, mock_data_access,
    ):
        """Test that DataPersistenceError is properly propagated for get_product_by_id."""
        product_id = 1
        mock_data_access.get_product_by_id.side_effect = DataPersistenceError("Database connection failed")

        with pytest.raises(DataPersistenceError) as exc_info:
            await product_service.get_product_by_id(product_id)
        
        assert str(exc_info.value) == "Database connection failed"
        mock_data_access.get_product_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_product_by_id_propagates_product_not_found_error(
        self, product_service, mock_data_access,
    ):
        """Test that ProductNotFoundError is properly propagated for get_product_by_id."""
        product_id = 999
        mock_data_access.get_product_by_id.side_effect = ProductNotFoundError("Product not found in database")

        with pytest.raises(ProductNotFoundError) as exc_info:
            await product_service.get_product_by_id(product_id)
        
        assert str(exc_info.value) == "Product not found in database"
        mock_data_access.get_product_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_get_product_by_id_handles_unexpected_exceptions(
        self, product_service, mock_data_access,
    ):
        """Test that unexpected exceptions are caught and transformed for get_product_by_id."""
        product_id = 1
        mock_data_access.get_product_by_id.side_effect = ValueError("Unexpected error")

        with pytest.raises(Exception) as exc_info:
            await product_service.get_product_by_id(product_id)
        
        assert str(exc_info.value) == "An unexpected error occurred"
        mock_data_access.get_product_by_id.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_product_model_creation_from_dict(self, product_service, mock_data_access):
        """Test that dict data is properly transformed to Product model."""
        product_data = {
            "id": "42",
            "name": "Test Product",
            "description": "Test Description",
            "image_url": "/test/image.png",
            "votes": 10,
        }
        mock_data_access.get_product_by_id.return_value = product_data

        result = await product_service.get_product_by_id(42)

        assert isinstance(result, Product)
        assert result.id == 42  # Should be converted to int
        assert result.name == "Test Product"
        assert result.description == "Test Description"
        assert result.image_url == "/test/image.png"
        assert result.votes == 10

    @pytest.mark.asyncio
    async def test_product_model_creation_with_zero_votes(self, product_service, mock_data_access):
        """Test product model creation with zero votes."""
        product_data = {
            "id": "1",
            "name": "Test Product",
            "description": "Test Description",
            "image_url": "/test/image.png",
            "votes": 0,
        }
        mock_data_access.get_product_by_id.return_value = product_data

        result = await product_service.get_product_by_id(1)

        assert result.votes == 0

    @pytest.mark.asyncio
    async def test_multiple_products_transformation(self, product_service, mock_data_access):
        """Test transformation of multiple products from dict to Product models."""
        products_data = [
            {
                "id": "1",
                "name": "Product 1",
                "description": "Description 1",
                "image_url": "/image1.png",
                "votes": 5,
            },
            {
                "id": "2",
                "name": "Product 2",
                "description": "Description 2",
                "image_url": "/image2.png",
                "votes": 0,
            },
        ]
        mock_data_access.get_products.return_value = products_data

        result = await product_service.get_all_products()

        assert len(result) == 2
        assert all(isinstance(product, Product) for product in result)
        assert result[0].id == 1
        assert result[1].id == 2
