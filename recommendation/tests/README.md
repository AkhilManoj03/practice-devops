# Recommendation Service - Unit Test Suite

This directory contains a comprehensive, modern unit test suite for the Recommendation Service,
following best practices for Go projects:
- isolation
- dependency injection
- clear test organization.

## 🏗️ Testing Architecture

The test suite is organized by feature and architectural layer:

```
tests/
├── api/                  # API/Handler layer tests
│   ├── home_test.go      # Home page and system info handler tests
│   ├── origami_test.go   # Origami-of-the-day handler tests
│   └── status_test.go    # Service status handler tests
├── data/                 # Data access layer tests
│   └── data_test.go      # Database logic and error handling tests
└── README.md             # This documentation
```

**Total Test Coverage: 20+ individual unit tests**

## 🎯 Testing Philosophy & Best Practices

### 1. **Isolation & Independence**
- ✅ **Zero External Dependencies**: All tests run in isolation using mocks or dependency injection
- ✅ **Fast Execution**: No real database or network required
- ✅ **Deterministic Results**: Consistent results across environments
- ✅ **Parallel Execution**: Tests can run concurrently

### 2. **Dependency Injection for Testability**
- Handlers are designed to accept dependencies (e.g., DB ping, product fetch) as function
parameters, allowing easy mocking in tests.
- No monkey-patching or global state required.

### 3. **Comprehensive Mocking**
- **Database Layer**: Uses [go-sqlmock](https://github.com/DATA-DOG/go-sqlmock) to
simulate all `database/sql` interactions.
- **API Layer**: Injects mock functions for DB and system info dependencies.

### 4. **Error Handling & Edge Cases**
- ✅ **Exception Propagation**: Tests verify proper error handling at each layer
- ✅ **Boundary Conditions**: Tests cover empty results, DB errors, and environment variable issues

### 5. **Test Organization & Naming**
- **Descriptive Test Names**: `TestGetOrigamiOfTheDay_Success`, `TestInitDB_MissingEnvVar`
- **Behavioral Testing**: Focus on observable behavior, not implementation details
- **Clear Assertions**: Use [testify/assert](https://github.com/stretchr/testify) for readable,
meaningful assertions

## 🚀 Prerequisites & Setup

### 1. **Install Test Dependencies**
```bash
go get github.com/DATA-DOG/go-sqlmock
go get github.com/stretchr/testify
```

### 2. **Run All Tests**
From the project root or the `recommendation` directory:
```bash
go test ./tests/...
```

For verbose output:
```bash
go test -v ./tests/...
```

## 🔍 Test Categories & Coverage

### **API Layer Tests**
- **Status Handler** (`api/status_test.go`):
  - Simulates both operational and down database states
  - Asserts correct JSON response and status
- **Home Handler** (`api/home_test.go`):
  - Mocks system info for deterministic output
  - Asserts correct HTML rendering and version display
- **Origami Handler** (`api/origami_test.go`):
  - Mocks random product selection (success and error)
  - Asserts correct JSON and error handling

### **Data Layer Tests**
- **Database Logic** (`data/data_test.go`):
  - Uses `go-sqlmock` to simulate DB connection, ping, and queries
  - Tests for missing env vars, connection errors, query errors, and success cases
  - Ensures no real DB is required

## 📊 Example Test Patterns

### **API Handler with Dependency Injection**
```go
r.GET("/status", api.GetRecommendationStatus(func() error { return nil }))
```

### **Database Mocking with go-sqlmock**
```go
mockDB, mock, _ := sqlmock.New()
data.SetDB(mockDB)
mock.ExpectQuery("SELECT ...").WillReturnRows(...)
```

## 🧩 Advanced Testing Features
- **Test-only helpers** for DB injection are kept internal to the test files using `package data`
for access to unexported variables.
- **No test logic in production code**: All dependency injection is handled via handler parameters.

## 🎉 Summary

This test suite demonstrates:
- ✅ **Modern Go testing practices**
- ✅ **Comprehensive coverage of API and data layers**
- ✅ **Fast, isolated, and maintainable tests**
- ✅ **Clear separation of production and test logic**

For any new features, follow the same patterns: use dependency injection for testability, keep
tests isolated, and use mocks for all external dependencies.
