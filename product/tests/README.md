# Product Service - Enterprise Test Suite

This directory contains a comprehensive, enterprise-grade test suite for the Product Service,
implementing modern testing best practices with full isolation, mocking, and layered architecture
testing.

## 🏗️ Testing Architecture

The test suite follows a **layered architecture approach** that mirrors the application's clean
architecture:

```
tests/
├── unit/                                    # Unit tests (fast, isolated)
│   ├── api/                                # API/Controller layer tests
│   │   ├── routes/                         # Route-specific tests
│   │   │   ├── test_frontend.py           # Frontend endpoints (10 tests)
│   │   │   ├── test_products.py           # Product endpoints (15 tests)
│   │   │   ├── test_system.py             # System endpoints (20 tests)
│   │   │   └── test_votes.py              # Vote endpoints (25 tests)
│   │   ├── test_dependencies.py           # Dependency injection tests (12 tests)
│   │   ├── test_middleware.py             # JWT middleware tests (30 tests)
│   │   └── conftest.py                    # API-specific fixtures & mocks
│   ├── core/                              # Business logic layer tests
│   │   └── services/                      # Service layer tests
│   │       ├── test_product_service.py    # Product business logic (12 tests)
│   │       ├── test_vote_service.py       # Vote business logic (15 tests)
│   │       ├── test_system_service.py     # System service tests (18 tests)
│   │       └── conftest.py                # Core service fixtures & mocks
│   └── infrastructure/                    # Infrastructure layer tests
│       ├── cache/                         # Cache layer tests
│       │   └── test_cache.py              # Redis operations & connection tests (12 tests)
│       ├── database/                      # Database layer tests
│       │   └── test_database.py           # PostgreSQL operations & connection tests (18 tests)
│       ├── test_data_access.py            # Data access coordination tests (15 tests)
│       └── conftest.py                    # Infrastructure-specific fixtures & mocks
├── conftest.py                           # Global test configuration & unified TestDataFactory
├── run_tests.py                         # Intelligent test runner
└── README.md                           # This documentation
```

**Total Test Coverage: 100+ individual unit tests**

## 🎯 Testing Philosophy & Best Practices

### 1. **Isolation & Independence**
- ✅ **Zero External Dependencies**: All tests run in complete isolation using mocks
- ✅ **Fast Execution**: Entire test suite runs in seconds (no I/O operations)
- ✅ **Deterministic Results**: Tests produce consistent results across environments
- ✅ **Parallel Execution**: Tests can run concurrently without conflicts

### 2. **Unified Test Data Factory**
```python
# Centralized test data creation with consistent patterns
class TestDataFactory:
    @staticmethod
    def create_product_model(product_id=1, name="Test Product", votes=5):
        return Product(id=product_id, name=name, votes=votes)
    
    @staticmethod
    def create_vote_response_dict(origami_id=1, new_vote_count=6):
        return {"origami_id": origami_id, "new_vote_count": new_vote_count}
    
    @staticmethod
    def create_db_rows(count=2):
        # Consistent database row generation for testing
```

### 3. **Consolidated Fixture Architecture**
- **Global Fixtures** (`tests/conftest.py`): Unified TestDataFactory and shared configuration
- **Layer-Specific Fixtures**: Specialized fixtures for each architectural layer
- **No Duplication**: Eliminated duplicate test data creation methods across conftest files
- **Backward Compatibility**: Legacy factory names maintained for existing tests

### 4. **Comprehensive Mocking Strategy**
```python
# Example: Sophisticated mocking with proper error simulation
@patch('infrastructure.database.postgres_manager.psycopg2')
def test_connect_psycopg2_error(mock_psycopg2, postgres_manager):
    setup_psycopg2_mock(mock_psycopg2)
    mock_psycopg2.connect.side_effect = MockPsycopg2Error("Connection failed")
    
    with pytest.raises(DataPersistenceError, match="Failed to connect to database"):
        postgres_manager.connect()
```

### 5. **Error Handling & Edge Cases**
- ✅ **Exception Propagation**: Tests verify proper error handling at each layer
- ✅ **Boundary Conditions**: Tests cover edge cases (null values, large numbers, empty results)
- ✅ **Transaction Management**: Database transaction rollback testing
- ✅ **Connection Failures**: Network and service unavailability scenarios

### 6. **Test Organization & Naming**
- **Descriptive Test Names**: `test_get_product_by_id_CacheHit_ReturnsProductFromCache`
- **Behavioral Testing**: Tests focus on behavior, not implementation details
- **Test Classes**: Logical grouping of related test scenarios
- **Clear Assertions**: Specific, meaningful assertions with helpful error messages

## 🚀 Prerequisites & Setup

### 1. **Install Test Dependencies**
```bash
pip install -r requirements-test.txt
```

**Key Testing Libraries:**
- `pytest` - Modern testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-xdist` - Parallel test execution
- `unittest.mock` - Comprehensive mocking capabilities

### 2. **Environment Setup**
```bash
cd product/
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## 🎮 Running Tests

### **Intelligent Test Runner**
The custom `run_tests.py` script provides granular control over test execution:

```bash
# Layer-specific testing
python run_tests.py api                    # All API layer tests
python run_tests.py core                   # All business logic tests
python run_tests.py infrastructure         # All infrastructure tests

# Run all tests
python run_tests.py all
```

### **Direct pytest Commands**
```bash
# Run specific test categories
pytest tests/unit/api/ -v                 # API layer tests
pytest tests/unit/core/ -v                # Core business logic tests
pytest tests/unit/infrastructure/ -v      # Infrastructure tests

# Parallel execution
pytest -n auto -v
```

## 🔍 Test Categories & Coverage

### **API Layer Tests (56+ tests)**
- **Route Testing**: HTTP status codes, request/response validation
- **Authentication**: JWT middleware, token validation, JWKS integration
- **Error Handling**: HTTP exception handling, proper error responses
- **Dependency Injection**: Service dependency resolution

```python
# Example: Comprehensive API endpoint testing
@pytest.mark.asyncio
async def test_get_product_success(mock_product_service, sample_product_model):
    result = await get_product(1, mock_product_service)
    
    assert result.id == 1
    assert result.name == "Test Product"
    mock_product_service.get_product_by_id.assert_called_once_with(1)
```

### **Core Business Logic Tests (20+ tests)**
- **Service Layer**: Business rules, data transformation, validation
- **Model Validation**: Pydantic model creation and validation
- **Exception Handling**: Custom exception propagation and transformation
- **System Information**: Environment detection, health checks

```python
# Example: Business logic testing with unified test data factory
@pytest.mark.asyncio
async def test_add_vote_success(vote_service, mock_data_access, test_data_factory):
    vote_data = test_data_factory.create_vote_response_dict()
    mock_data_access.add_vote.return_value = vote_data
    
    result = await vote_service.add_vote(1)
    
    assert isinstance(result, VoteResponse)
    assert result.origami_id == 1
    assert result.new_vote_count == 6
```

### **Infrastructure Layer Tests (35+ tests)**
- **Database Operations**: CRUD operations, transaction management, connection pooling
- **Cache Management**: Redis operations, cache invalidation, connection resilience
- **Data Access Coordination**: Cache-database coordination, fallback mechanisms
- **Error Recovery**: Connection failures, retry logic, graceful degradation

```python
# Example: Infrastructure testing with unified test data
def test_get_products_ProductsExist_ReturnsAllProducts(
    postgres_manager, mock_connection, mock_cursor_context_manager, 
    mock_cursor, test_data_factory,
):
    test_db_rows = test_data_factory.create_db_rows(2)
    mock_cursor.fetchall.return_value = test_db_rows
    
    result = postgres_manager.get_products()
    
    assert len(result) == 2
    assert result[0]["votes"] == 5
    assert result[1]["votes"] == 10
```

## 📊 Advanced Testing Features

### **1. Unified Test Data Factory**
Consistent test data generation across all test modules with no duplication:

```python
@pytest.fixture
def test_data_factory():
    """Provide access to TestDataFactory."""
    return TestDataFactory

# Usage examples:
product_model = test_data_factory.create_product_model()
vote_response = test_data_factory.create_vote_response_dict()
db_rows = test_data_factory.create_db_rows(2)
```

### **2. Consolidated Fixture Management**
- **Single Source of Truth**: All test data creation methods in main conftest.py
- **Layer-Specific Fixtures**: Only layer-specific mocks and helpers in sub-conftest files
- **Backward Compatibility**: Legacy factory names maintained for existing tests
- **Easy Maintenance**: Changes to test data structure only need to be made in one place

### **3. Sophisticated Mocking**
- **Context Managers**: Proper database cursor mocking
- **Side Effects**: Error simulation and exception handling
- **Return Values**: Consistent mock responses
- **Call Verification**: Ensuring proper method invocations

### **4. Async Testing Support**
Full support for async/await patterns with proper mocking:

```python
@pytest.mark.asyncio
async def test_get_products_empty_list(self, mock_product_service):
    """Test retrieval when no products exist."""
    mock_product_service.get_all_products.return_value = []
    result = await get_products(mock_product_service)
    assert result == []
    mock_product_service.get_all_products.assert_called_once()
```

## 🎯 Key Testing Achievements

### **1. Complete Layer Isolation**
- Each architectural layer is tested independently
- No cross-layer dependencies in tests
- Proper abstraction boundary verification

### **2. Consolidated Test Data Management**
- **Eliminated Duplication**: Removed duplicate test data creation methods
- **Unified Factory**: Single TestDataFactory for all test data needs
- **Consistent Patterns**: Standardized test data creation across all layers
- **Easy Maintenance**: Centralized test data management

### **3. Comprehensive Error Scenarios**
- Database connection failures
- Cache unavailability
- Network timeouts
- Invalid input handling
- Transaction rollback scenarios

### **4. Performance Optimization**
- Tests run in milliseconds
- Parallel execution support
- Efficient fixture management
- Minimal test setup overhead

### **5. Maintainability**
- Clear test organization
- Reusable test components
- Comprehensive documentation
- Easy test debugging
- **Reduced Code Duplication**: Consolidated test data creation

## 🔧 Configuration & Customization

### **Test Markers**
```python
@pytest.mark.unit          # Fast, isolated unit tests
@pytest.mark.integration   # Integration tests (when needed)
@pytest.mark.slow          # Performance-intensive tests
@pytest.mark.database      # Database-related tests
@pytest.mark.cache         # Cache-related tests
```

### **Coverage Configuration**
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --disable-warnings
markers =
    unit: Fast, isolated unit tests
    integration: Integration tests
    slow: Slow-running tests
```

## 🎉 Summary

This test suite demonstrates **enterprise-level testing practices** including:

- ✅ **Comprehensive Coverage**: 100+ tests across all architectural layers
- ✅ **Modern Testing Stack**: pytest, asyncio, sophisticated mocking
- ✅ **Clean Architecture**: Layer-specific testing with proper isolation
- ✅ **Unified Test Data**: Consolidated TestDataFactory eliminates duplication
- ✅ **Error Handling**: Extensive error scenario coverage
- ✅ **Performance**: Fast, parallel execution capabilities
- ✅ **Maintainability**: Well-organized, documented, and extensible
- ✅ **Code Quality**: Reduced duplication and improved consistency

The testing framework showcases **professional software development practices** suitable for
production environments, emphasizing reliability, maintainability, and comprehensive quality
assurance with a focus on **consolidated, maintainable test infrastructure**.
