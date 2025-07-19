# Integration Tests

This directory contains a comprehensive integration test suite for the microservices showcase
project. The test framework is designed to validate the functionality and interaction between the
microservices and the core infrastructure components.

## Architecture Overview

The integration test suite follows a modular, service-oriented architecture with shared utilities
and standardized testing patterns:

```
tests/integration/
├── integration_runner.sh      # Main orchestrator for all test suites
├── authentication_tests.sh    # Tests for authentication service
├── frontend_tests.sh          # Tests for frontend service
├── product_tests.sh           # Tests for product service
├── recommendation_tests.sh    # Tests for recommendation service
├── ../helper_scripts.sh       # Shared utilities and functions
└── ../config.sh              # Centralized configuration
```

## Features

### 🧪 Comprehensive Test Coverage
- **Authentication Service**: Registration, login, JWKS, OpenID configuration
- **Product Service**: Product/origami CRUD operations, voting, health checks
- **Frontend Service**: Page rendering and routing
- **Recommendation Service**: Status checks and recommendation engine

### 🚀 Flexible Execution Modes
- **Sequential Execution**: Run test suites one after another (default)
- **Parallel Execution**: Run multiple test suites concurrently for faster feedback
- **Individual Suite Testing**: Target specific services for focused testing

### 📊 Rich Reporting and Logging
- Color-coded console output with status indicators
- Detailed logging to `integration-tests.log`
- Comprehensive test summaries with success rates and timing
- Verbose mode for debugging and troubleshooting

### 🔧 Robust Error Handling
- Exponential backoff for service health checks
- Graceful failure handling with detailed error messages
- Timeout management with configurable limits
- Dependency validation before test execution

## Quick Start

### Prerequisites

Ensure the following tools are installed:
- `curl` - For HTTP requests
- `jq` - For JSON parsing and validation
- `bash` 4.0+ - Shell environment

### Running All Tests

```bash
# Run all integration test suites sequentially
./integration_runner.sh

# Run with verbose output for debugging
./integration_runner.sh --verbose

# Run test suites in parallel for faster execution
./integration_runner.sh --parallel

# Set custom timeout (default: 10 seconds)
./integration_runner.sh --timeout 30
```

### Running Individual Test Suites

```bash
# Run only authentication tests
./integration_runner.sh --suite authentication

# Run only product tests with verbose output
./integration_runner.sh --suite product --verbose

# Available suites: authentication, frontend, product, recommendation
```

### Running Individual Service Tests Directly

```bash
# Run authentication tests directly
./authentication_tests.sh

# Run with custom configuration
./product_tests.sh --verbose --timeout 15
```

## Configuration

The test suite supports configuration via environment variables, command line options, and default
values where command line options take precedence, then environment variables, then default values.

### Environment Variables

The test suite supports configuration via environment variables an:

```bash
# Set global timeout for all requests
export TIMEOUT=15

# Enable verbose output globally
export VERBOSE=true

# Enable parallel execution mode
export PARALLEL_MODE=true

# Override service URLs for testing
export AUTHENTICATION_TESTS_SERVICE_URL=http://localhost:8082
export PRODUCT_SERVICE_URL=http://localhost:8000
export FRONTEND_TESTS_SERVICE_URL=http://localhost:3000
export RECOMMENDATION_TESTS_SERVICE_URL=http://localhost:8080
```

### Command Line Options

Each test script supports the following options:

- `-v, --verbose`: Enable detailed debug output
- `-t, --timeout N`: Set request timeout in seconds
- `-h, --help`: Display help information

Additional options for `integration_runner.sh`:
- `-s, --suite NAME`: Run specific test suite only
- `-p, --parallel`: Execute suites concurrently

## Test Structure

### Test Case Definition

Each test case is defined as a bash associative array with the following structure:

```bash
declare -A test_case_name
test_case_name["name"]="Descriptive test name"
test_case_name["method"]="HTTP_METHOD"
test_case_name["endpoint"]="/api/endpoint"
test_case_name["payload"]='{"json": "data"}'
test_case_name["api_key"]="optional-api-key"
test_case_name["expected_status"]="200"
test_case_name["expected_fields"]="field1 field2 field3"
```

### Service Health Checks

All test suites implement health checks with:
- **Exponential backoff**: 1s, 2s, 4s, 8s intervals
- **Connection timeout**: 3 seconds per attempt
- **Maximum attempts**: 2 retries before failure
- **Graceful failure**: Clear error messages when services are unavailable

### Response Validation

The framework performs comprehensive validation:
- **HTTP Status Code**: Exact match verification
- **JSON Structure**: Syntax validation using `jq`
- **Field Presence**: Validation of required response fields
- **Response Timing**: Performance monitoring and reporting

## Google Shell Style Guide Compliance

This project strictly adheres to the [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
for maintainability and consistency.

### 🎯 Style Compliance Features

**Function Documentation**
```bash
#######################################
# Execute a single test case with HTTP request and validation.
# Globals:
#   TOTAL_TESTS (incremented)
#   PASSED_TESTS (incremented)
#   FAILED_TESTS (incremented)
# Arguments:
#   test_case_array_name - Name of the array containing test case definition
# Returns:
#   0 if test passes, 1 if test fails
#######################################
```

**Variable Naming Conventions**
- `GLOBAL_CONSTANTS` - All caps for constants and environment variables
- `local_variables` - Lowercase with underscores for local variables
- `readonly` declarations for immutable values

**Error Handling**
- `set -uo pipefail` - Strict error handling in all scripts
- Explicit error trapping with `trap 'handle_error ${LINENO} $?' ERR`
- Meaningful exit codes (0=success, 1=failure, 124=timeout)

**Code Organization**
- Modular design with separation of concerns
- Consistent indentation (2 spaces)
- Descriptive function and variable names
- Proper quoting of variables: `"${variable}"`

**Best Practices Implemented**
- ✅ All scripts start with appropriate shebang
- ✅ Variables are properly quoted and use `${var}` syntax
- ✅ Functions are documented with purpose, globals, arguments, and returns
- ✅ Error handling is comprehensive and user-friendly
- ✅ Constants are declared as `readonly`
- ✅ Local variables are declared with `local`
- ✅ Array handling uses proper bash techniques

## Logging and Debugging

### Log Levels

- **INFO**: General operational messages
- **ERROR**: Error conditions and failures
- **DEBUG**: Detailed troubleshooting information (verbose mode only)
- **TEST**: Individual test execution status
- **SUCCESS/FAILURE**: Test result indicators

### Log File Format

```
[2024-01-15 14:30:25] INFO: Starting integration test suite...
[2024-01-15 14:30:25] TEST: Running: Get authentication status
[2024-01-15 14:30:26] SUCCESS: ✅ Get authentication status - PASSED (0.234s)
```

### Debugging Tips

1. **Enable verbose mode** for detailed request/response logging
2. **Check log file** for complete execution history
3. **Verify service URLs** match your deployment configuration
4. **Confirm dependencies** are installed and accessible

## CI/CD Integration

```bash
#!/bin/bash
# Example CI script
cd tests/integration

# Set environment for CI
export TIMEOUT=20
export VERBOSE=false
export PARALLEL_MODE=true

# Run tests and capture exit code
./integration_runner.sh
exit_code=$?

# Process results
if [[ $exit_code -eq 0 ]]; then
    echo "✅ All integration tests passed"
else
    echo "❌ Integration tests failed with $exit_code errors"
    cat integration-tests.log
fi

exit $exit_code
```
