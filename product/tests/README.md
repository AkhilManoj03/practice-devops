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
│   │   └── conftest.py                    # API-specific fixtures
│   ├── core/                              # Business logic layer tests
│   │   └── services/                      # Service layer tests
│   │       ├── test_product_service.py    # Product business logic (12 tests)
│   │       ├── test_vote_service.py       # Vote business logic (15 tests)
│   │       ├── test_system_service.py     # System service tests (18 tests)
│   │       └── conftest.py                # Core service fixtures
│   └── infrastructure/                    # Infrastructure layer tests
│       ├── database/                      # Database layer tests
│       │   ├── test_connection_management.py  # Connection tests (8 tests)
│       │   ├── test_query_operations.py       # Query tests (18 tests)
│       │   ├── test_write_operations.py       # Write/transaction tests (6 tests)
│       │   └── conftest.py                    # Database-specific fixtures
│       ├── cache/                         # Cache layer tests
│       │   ├── test_connection_management.py  # Redis connection tests (8 tests)
│       │   ├── test_cache_operations.py       # Cache operations tests (12 tests)
│       │   └── conftest.py                    # Cache-specific fixtures
│       └── data_access/                   # Data access coordination tests
│           ├── test_initialization.py         # Lifecycle management (8 tests)
│           ├── test_product_operations.py     # Product data operations (15 tests)
│           ├── test_vote_operations.py        # Vote data operations (10 tests)
│           ├── test_data_access.py           # Coordination logic (25 tests)
│           └── conftest.py                   # Data access fixtures
├── conftest.py                           # Global test configuration
├── run_tests.py                         # Intelligent test runner
└── README.md                           # This documentation
```

**Total Test Coverage: 260+ individual unit tests**

## 🎯 Testing Philosophy & Best Practices

### 1. **Isolation & Independence**
- ✅ **Zero External Dependencies**: All tests run in complete isolation using mocks
- ✅ **Fast Execution**: Entire test suite runs in seconds (no I/O operations)
- ✅ **Deterministic Results**: Tests produce consistent results across environments
- ✅ **Parallel Execution**: Tests can run concurrently without conflicts

### 2. **Comprehensive Mocking Strategy**
```python
# Example: Sophisticated mocking with proper error simulation
@patch('infrastructure.database.postgres_manager.psycopg2')
def test_connect_psycopg2_error(mock_psycopg2, postgres_manager):
    setup_psycopg2_mock(mock_psycopg2)
    mock_psycopg2.connect.side_effect = MockPsycopg2Error("Connection failed")
    
    with pytest.raises(DataPersistenceError, match="Failed to connect to database"):
        postgres_manager.connect()
```

### 3. **Hierarchical Fixture Architecture**
- **Global Fixtures** (`tests/conftest.py`): Shared test data and configuration
- **Layer-Specific Fixtures**: Specialized fixtures for each architectural layer
- **Test Factories**: Consistent test data generation across test modules
- **Mock Managers**: Centralized mock configuration and setup

### 4. **Error Handling & Edge Cases**
- ✅ **Exception Propagation**: Tests verify proper error handling at each layer
- ✅ **Boundary Conditions**: Tests cover edge cases (null values, large numbers, empty results)
- ✅ **Transaction Management**: Database transaction rollback testing
- ✅ **Connection Failures**: Network and service unavailability scenarios

### 5. **Test Organization & Naming**
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

# Component-specific testing
python run_tests.py database              # Database manager tests
python run_tests.py cache                 # Cache manager tests
python run_tests.py data-access           # Data access layer tests

# Granular testing
python run_tests.py api-products          # Product API endpoints only
python run_tests.py core-vote             # Vote service business logic
python run_tests.py database-conn         # Database connection tests

# Performance & Coverage
python run_tests.py fast                  # Parallel execution
python run_tests.py coverage             # Coverage report generation
```

### **Direct pytest Commands**
```bash
# Run specific test categories
pytest tests/unit/api/ -v                 # API layer tests
pytest tests/unit/core/ -v                # Core business logic tests
pytest tests/unit/infrastructure/ -v      # Infrastructure tests

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing -v

# Parallel execution
pytest -n auto -v

# Specific test patterns
pytest -k "test_get_product" -v           # All product retrieval tests
pytest -k "connection" -v                 # All connection-related tests
```

## 🔍 Test Categories & Coverage

### **API Layer Tests (70+ tests)**
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

### **Core Business Logic Tests (45+ tests)**
- **Service Layer**: Business rules, data transformation, validation
- **Model Validation**: Pydantic model creation and validation
- **Exception Handling**: Custom exception propagation and transformation
- **System Information**: Environment detection, health checks

```python
# Example: Business logic testing with proper mocking
@pytest.mark.asyncio
async def test_add_vote_success(vote_service, mock_data_access, sample_vote_data):
    mock_data_access.add_vote.return_value = sample_vote_data
    
    result = await vote_service.add_vote(1)
    
    assert isinstance(result, VoteResponse)
    assert result.origami_id == 1
    assert result.new_vote_count == 6
```

### **Infrastructure Layer Tests (145+ tests)**
- **Database Operations**: CRUD operations, transaction management, connection pooling
- **Cache Management**: Redis operations, cache invalidation, connection resilience
- **Data Access Coordination**: Cache-database coordination, fallback mechanisms
- **Error Recovery**: Connection failures, retry logic, graceful degradation

```python
# Example: Infrastructure testing with transaction verification
def test_add_vote_with_transaction_rollback(postgres_manager, mock_connection):
    mock_cursor.execute.side_effect = MockPsycopg2Error("Query failed")
    
    with pytest.raises(DataPersistenceError):
        postgres_manager.add_vote(1)
    
    mock_connection.rollback.assert_called_once()
```

## 📊 Advanced Testing Features

### **1. Test Data Factories**
Consistent test data generation across all test modules:

```python
class APITestDataFactory:
    @staticmethod
    def create_product_model(product_id=1, name="Test Product", votes=5):
        return Product(id=product_id, name=name, votes=votes)
    
    @staticmethod
    def create_product_list(count=3):
        return [APITestDataFactory.create_product_model(i) for i in range(1, count + 1)]
```

### **2. Sophisticated Mocking**
- **Context Managers**: Proper database cursor mocking
- **Side Effects**: Error simulation and exception handling
- **Return Values**: Consistent mock responses
- **Call Verification**: Ensuring proper method invocations

### **3. Async Testing Support**
Full support for async/await patterns with proper mocking:

```python
@pytest.mark.asyncio
async def test_async_service_method(mock_service):
    mock_service.async_method = AsyncMock(return_value=expected_result)
    result = await service.async_method()
    assert result == expected_result
```

### **4. Parameterized Testing**
Efficient testing of multiple scenarios:

```python
@pytest.mark.parametrize("status_code,detail", [
    (400, "Bad Request"),
    (401, "Unauthorized"),
    (404, "Not Found"),
    (500, "Internal Server Error")
])
def test_http_exception_handler(status_code, detail):
    # Test implementation
```

## 🎯 Key Testing Achievements

### **1. Complete Layer Isolation**
- Each architectural layer is tested independently
- No cross-layer dependencies in tests
- Proper abstraction boundary verification

### **2. Comprehensive Error Scenarios**
- Database connection failures
- Cache unavailability
- Network timeouts
- Invalid input handling
- Transaction rollback scenarios

### **3. Performance Optimization**
- Tests run in milliseconds
- Parallel execution support
- Efficient fixture management
- Minimal test setup overhead

### **4. Maintainability**
- Clear test organization
- Reusable test components
- Comprehensive documentation
- Easy test debugging

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

- ✅ **Comprehensive Coverage**: 260+ tests across all architectural layers
- ✅ **Modern Testing Stack**: pytest, asyncio, sophisticated mocking
- ✅ **Clean Architecture**: Layer-specific testing with proper isolation
- ✅ **Error Handling**: Extensive error scenario coverage
- ✅ **Performance**: Fast, parallel execution capabilities
- ✅ **Maintainability**: Well-organized, documented, and extensible

The testing framework showcases **professional software development practices** suitable for
production environments, emphasizing reliability, maintainability, and comprehensive quality
assurance. 