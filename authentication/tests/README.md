# Authentication Service Tests

This directory contains comprehensive unit and integration tests for the authentication service.

## Test Structure

```
tests/
├── mod.rs              # Main test module
├── common/             # Common test utilities
│   └── mod.rs         # Test helpers and setup functions
└── handlers/          # Handler-specific tests
    ├── mod.rs         # Handler test modules
    └── openid.rs      # OpenID Connect endpoint tests
```

## Test Categories

### Unit Tests

- **OpenID Tests** (`handlers/openid.rs`): Tests for JWKS and OpenID configuration endpoints
  - JWKS endpoint success scenarios
  - Key component validation
  - Error handling (missing/malformed keys)
  - OpenID configuration generation
  - JSON serialization/deserialization
  - Performance tests
  - Edge cases and consistency checks

### Common Test Utilities

The `common` module provides:
- Test configuration generation with temporary RSA key pairs
- Mock app state creation for unit tests

## Running Tests

### Run all tests:
```bash
cargo test
```

### Run specific test modules:
```bash
# Run only OpenID tests
cargo test handlers::openid

# Run with output
cargo test -- --nocapture

# Run specific test
cargo test test_jwks_endpoint_success
```

### Run tests with different log levels:
```bash
RUST_LOG=debug cargo test -- --nocapture
```

## Test Features

### RSA Key Generation
Tests automatically generate temporary RSA key pairs for each test run, ensuring isolation and avoiding dependency on external key files.

### Error Testing
Comprehensive error scenarios are tested including:
- Missing key files
- Malformed key files
- Invalid configurations

### Performance Testing
Basic performance tests ensure endpoints respond within reasonable time limits.

### JSON Validation
Tests verify that all JSON responses conform to expected schemas and can be properly serialized/deserialized.

## Adding New Tests

When adding new tests:

1. **Follow naming conventions**: Use descriptive test names prefixed with `test_`
2. **Use common utilities**: Leverage the `common` module for setup
3. **Clean up resources**: Use RAII patterns with temporary directories
4. **Test error cases**: Include both success and failure scenarios
5. **Add documentation**: Document complex test scenarios

### Example Test Structure:

```rust
#[tokio::test]
async fn test_your_functionality() {
    let (app_state, _temp_dir) = create_unit_test_state();
    
    // Test logic here
    let result = your_handler(State(app_state)).await;
    
    // Assertions
    assert!(result.is_ok());
    // ... more assertions
}
```

## Dependencies

The test suite uses:
- `tokio-test`: Async testing utilities
- `tempfile`: Temporary file/directory management
- `axum-test`: HTTP testing for Axum applications
- `rstest`: Parameterized testing
- `rand`: Random key generation for tests

## Future Enhancements

Planned test additions:
- Integration tests with real database
- Login handler tests
- Registration handler tests
- Status handler tests
- Middleware tests
- Configuration tests
- Full end-to-end API tests
