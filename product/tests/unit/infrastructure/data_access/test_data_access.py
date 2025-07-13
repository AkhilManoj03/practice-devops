"""
Tests for DataAccessLayer coordination logic.

This module tests the coordination between database and cache managers,
including initialization, cleanup, and business logic orchestration.
"""

import pytest
from unittest.mock import MagicMock

from infrastructure.data_access import DataAccessLayer
from core.exceptions import DataValidationError, ProductNotFoundError


class DataAccessTestDataFactory:
    """Factory for creating consistent test data for data access layer tests."""
    
    @staticmethod
    def create_product_dict(
        product_id="1", name="Test Product", description="Test Description", 
        image_url="/test/image.png", votes=5,
    ):
        """Create a product dictionary for testing."""
        return {
            "id": str(product_id),
            "name": name,
            "description": description,
            "image_url": image_url,
            "votes": votes,
        }
    
    @staticmethod
    def create_product_list(count=3):
        """Create a list of products for testing."""
        return [
            DataAccessTestDataFactory.create_product_dict(
                product_id=str(i),
                name=f"Product {i}",
                votes=i * 2,
            )
            for i in range(1, count + 1)
        ]
    
    @staticmethod
    def create_vote_response(product_id=1, new_vote_count=6):
        """Create a vote response dictionary for testing."""
        return {
            "origami_id": product_id,
            "new_vote_count": new_vote_count,
            "message": f"Vote added successfully for Test Product",
        }
    
    @staticmethod
    def create_test_settings():
        """Create test settings."""
        settings = MagicMock()
        settings.postgres_host = "localhost"
        settings.postgres_port = 5432
        settings.postgres_db = "test_db"
        settings.postgres_user = "test_user"
        settings.postgres_password = "test_pass"
        settings.redis_host = "localhost"
        settings.redis_port = 6379
        return settings


class TestDataAccessLayerInitialization:
    """Test suite for DataAccessLayer initialization and cleanup."""

    @pytest.fixture
    def test_settings(self):
        """Create test settings."""
        return DataAccessTestDataFactory.create_test_settings()

    @pytest.fixture
    def data_access_layer(self, test_settings):
        """Create DataAccessLayer instance with mock settings."""
        return DataAccessLayer(test_settings)

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        return MagicMock()

    @pytest.fixture
    def mock_cache_manager(self):
        """Create mock cache manager."""
        return MagicMock()

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
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager

        data_access_layer.initialize()

        mock_db_manager.connect.assert_called_once()
        mock_cache_manager.connect.assert_called_once()

    def test_cleanup_ValidManagers_CallsDisconnectOnBothManagers(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that cleanup() calls disconnect on both database and cache managers."""
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager

        data_access_layer.cleanup()

        mock_db_manager.disconnect.assert_called_once()
        mock_cache_manager.disconnect.assert_called_once()

    def test_health_check_BothManagersHealthy_ReturnsTrue(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that health_check() returns True when both managers are healthy."""
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
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
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
        mock_db_manager.check_connection.return_value = False
        mock_cache_manager.check_connection.return_value = True

        result = data_access_layer.health_check()

        assert result is False

    def test_health_check_CacheUnhealthy_ReturnsFalse(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that health_check() returns False when cache is unhealthy."""
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
        mock_db_manager.check_connection.return_value = True
        mock_cache_manager.check_connection.return_value = False

        result = data_access_layer.health_check()

        assert result is False


class TestDataAccessLayerProductOperations:
    """Test suite for DataAccessLayer product operations."""

    @pytest.fixture
    def test_settings(self):
        """Create test settings."""
        return DataAccessTestDataFactory.create_test_settings()

    @pytest.fixture
    def data_access_layer(self, test_settings):
        """Create DataAccessLayer instance with mock settings."""
        return DataAccessLayer(test_settings)

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        return MagicMock()

    @pytest.fixture
    def mock_cache_manager(self):
        """Create mock cache manager."""
        return MagicMock()

    @pytest.fixture
    def data_factory(self):
        """Provide access to DataAccessTestDataFactory."""
        return DataAccessTestDataFactory

    def test_get_products_ValidData_ReturnsProductsFromDatabase(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that get_products() always returns products from database."""
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
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
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
        invalid_product_id = 0

        with pytest.raises(DataValidationError, match="Product ID must be positive"):
            data_access_layer.get_product_by_id(invalid_product_id)

    def test_get_product_by_id_CacheHit_ReturnsProductFromCache(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that get_product_by_id() returns product from cache when available."""
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
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
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
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
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
        mock_cache_manager.is_connected = False
        product_data = data_factory.create_product_dict()
        mock_db_manager.get_product_by_id.return_value = product_data
        product_id = 1

        result = data_access_layer.get_product_by_id(product_id)

        assert result == product_data
        mock_cache_manager.get_product.assert_not_called()
        mock_db_manager.get_product_by_id.assert_called_once_with(product_id)
        mock_cache_manager.set_product.assert_not_called()

    def test_get_votes_for_product_InvalidId_RaisesDataValidationError(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that get_votes_for_product() raises DataValidationError for invalid product ID."""
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
        invalid_product_id = -1

        with pytest.raises(DataValidationError, match="Product ID must be positive"):
            data_access_layer.get_votes_for_product(invalid_product_id)

    def test_get_votes_for_product_CacheHit_ReturnsVotesFromCache(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that get_votes_for_product() returns votes from cache when available."""
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
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
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
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
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
        mock_cache_manager.is_connected = True
        product_data = data_factory.create_product_dict()
        del product_data['votes']  # Remove votes key
        mock_cache_manager.get_product.return_value = product_data
        product_id = 1

        result = data_access_layer.get_votes_for_product(product_id)

        assert result == 0


class TestDataAccessLayerVoteOperations:
    """Test suite for DataAccessLayer vote operations."""

    @pytest.fixture
    def test_settings(self):
        """Create test settings."""
        return DataAccessTestDataFactory.create_test_settings()

    @pytest.fixture
    def data_access_layer(self, test_settings):
        """Create DataAccessLayer instance with mock settings."""
        return DataAccessLayer(test_settings)

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        return MagicMock()

    @pytest.fixture
    def mock_cache_manager(self):
        """Create mock cache manager."""
        return MagicMock()

    @pytest.fixture
    def data_factory(self):
        """Provide access to DataAccessTestDataFactory."""
        return DataAccessTestDataFactory

    def test_add_vote_InvalidId_RaisesDataValidationError(
        self, data_access_layer, mock_db_manager, mock_cache_manager,
    ):
        """Test that add_vote() raises DataValidationError for invalid product ID."""
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
        invalid_product_id = 0

        with pytest.raises(DataValidationError, match="Product ID must be positive"):
            data_access_layer.add_vote(invalid_product_id)

    def test_add_vote_ValidId_UpdatesDatabaseAndInvalidatesCache(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that add_vote() updates database and invalidates cache."""
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
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
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
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
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
        mock_db_manager.add_vote.side_effect = ProductNotFoundError("Product not found")
        product_id = 1

        with pytest.raises(ProductNotFoundError, match="Product not found"):
            data_access_layer.add_vote(product_id)

        mock_cache_manager.invalidate_product.assert_not_called()

    def test_add_vote_LargeProductId_HandlesCorrectly(
        self, data_access_layer, mock_db_manager, mock_cache_manager, data_factory,
    ):
        """Test that add_vote() handles large product IDs correctly."""
        data_access_layer.db_manager = mock_db_manager
        data_access_layer.cache_manager = mock_cache_manager
        mock_cache_manager.is_connected = True
        large_product_id = 999999
        vote_response = data_factory.create_vote_response(product_id=large_product_id)
        mock_db_manager.add_vote.return_value = vote_response

        result = data_access_layer.add_vote(large_product_id)

        assert result == vote_response
        mock_db_manager.add_vote.assert_called_once_with(large_product_id)
        mock_cache_manager.invalidate_product.assert_called_once_with(large_product_id)
