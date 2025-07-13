"""
API-specific fixtures and configuration.

This module contains API-specific fixtures, mock classes, and helpers
used across all API test modules.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Request
from fastapi.testclient import TestClient

from core.services import ProductService, VoteService, SystemService
from core.exceptions import (
    DataPersistenceError,
    ProductNotFoundError,
    DataValidationError,
)


class APITestDataFactory:
    """Factory for creating consistent test data for API tests."""
    
    @staticmethod
    def create_product_model(
        product_id=1,
        name="Test Product",
        description="Test Description",
        image_url="/test/image.png",
        votes=5,
    ):
        """Create a Product model instance for testing."""
        from core.models import Product
        return Product(
            id=product_id,
            name=name,
            description=description,
            image_url=image_url,
            votes=votes,
        )
    
    @staticmethod
    def create_product_list(count=2):
        """Create a list of Product models for testing."""
        from core.models import Product
        return [
            Product(
                id=i,
                name=f"Product {i}",
                description=f"Description {i}",
                image_url=f"/image{i}.png",
                votes=i * 2,
            )
            for i in range(1, count + 1)
        ]
    
    @staticmethod
    def create_vote_response(origami_id=1, new_vote_count=6):
        """Create a VoteResponse model instance for testing."""
        from core.models import VoteResponse
        return VoteResponse(
            origami_id=origami_id,
            new_vote_count=new_vote_count,
            message=f"Vote added successfully for Product {origami_id}",
        )


@pytest.fixture
def mock_product_service():
    """Create a mock ProductService for testing."""
    mock = AsyncMock(spec=ProductService)
    
    # Set up default return values
    mock.get_all_products.return_value = APITestDataFactory.create_product_list()
    mock.get_product_by_id.return_value = APITestDataFactory.create_product_model()
    
    return mock


@pytest.fixture
def mock_vote_service():
    """Create a mock VoteService for testing."""
    mock = AsyncMock(spec=VoteService)
    
    # Set up default return values
    mock.get_votes_for_product.return_value = {"origami_id": 1, "votes": 5}
    mock.add_vote.return_value = APITestDataFactory.create_vote_response()
    
    return mock


@pytest.fixture
def mock_system_service():
    """Create a mock SystemService for testing."""
    mock = AsyncMock(spec=SystemService)
    
    # Set up default return values
    from core.models import SystemInfo, HealthCheck
    from datetime import datetime
    
    mock.get_system_info.return_value = SystemInfo(
        hostname="test-host",
        ip_address="127.0.0.1",
        is_container=False,
        is_kubernetes=False,
    )
    
    mock.health_check.return_value = HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0",
    )
    
    return mock


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request for testing."""
    request = Mock(spec=Request)
    request.state = Mock()
    request.state.jwt_payload = None
    request.state.is_authenticated = False
    return request


@pytest.fixture
def authenticated_request():
    """Create a mock authenticated FastAPI Request for testing."""
    request = Mock(spec=Request)
    request.state = Mock()
    request.state.jwt_payload = {
        "sub": "testuser",
        "role": "user",
        "exp": 9999999999,
    }
    request.state.is_authenticated = True
    return request


@pytest.fixture
def api_factory():
    """Provide access to APITestDataFactory."""
    return APITestDataFactory


# Test data fixtures
@pytest.fixture
def sample_product_models():
    """Sample Product models for testing."""
    return APITestDataFactory.create_product_list(3)


@pytest.fixture
def sample_product_model():
    """Single sample Product model for testing."""
    return APITestDataFactory.create_product_model()


@pytest.fixture
def sample_vote_response():
    """Sample VoteResponse model for testing."""
    return APITestDataFactory.create_vote_response()
