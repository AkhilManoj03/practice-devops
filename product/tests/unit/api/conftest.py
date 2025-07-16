"""
API-specific fixtures and configuration.

This module contains API-specific fixtures, mock classes, and helpers
used across all API test modules.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Request
from datetime import datetime

from core.services import ProductService, VoteService, SystemService
from core.models import SystemInfo, HealthCheck
from ..conftest import TestDataFactory


@pytest.fixture
def mock_product_service():
    """Create a mock ProductService for testing."""
    mock = AsyncMock(spec=ProductService)
    
    mock.get_all_products.return_value = TestDataFactory.create_product_model_list(2)
    mock.get_product_by_id.return_value = TestDataFactory.create_product_model()
    
    return mock

@pytest.fixture
def mock_vote_service():
    """Create a mock VoteService for testing."""
    mock = AsyncMock(spec=VoteService)
    
    mock.get_votes_for_product.return_value = {"origami_id": 1, "votes": 5}
    mock.add_vote.return_value = TestDataFactory.create_vote_response_model()
    
    return mock

@pytest.fixture
def mock_system_service():
    """Create a mock SystemService for testing."""
    mock = AsyncMock(spec=SystemService)
    
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
def sample_product_models(test_data_factory):
    """Sample Product models for testing."""
    return test_data_factory.create_product_model_list(3)

@pytest.fixture
def sample_product_model(test_data_factory):
    """Single sample Product model for testing."""
    return test_data_factory.create_product_model()

@pytest.fixture
def sample_vote_response(test_data_factory):
    """Sample VoteResponse model for testing."""
    return test_data_factory.create_vote_response_model()
