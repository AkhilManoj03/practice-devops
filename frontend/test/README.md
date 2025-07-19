# Origami Unit Tests

This directory contains unit tests for the origami backend route functionality. Client-side
functionality and integration flows are covered by external end-to-end testing.

## Test Files

### `origamis.test.js`
Comprehensive tests for the backend origami routes:
- **POST /:origamiId/vote** - Vote submission with authentication
- **GET /:origamiId/votes** - Vote count retrieval
- Error handling for service failures
- Authentication middleware integration
- HTTP mocking with Nock

## Running Tests

### Install Dependencies
```bash
npm install
```

### Run All Tests
```bash
npm test
```

### Run Only Origami Tests
```bash
npm run test:origami
```

### Run Individual Test File
```bash
# Backend origami routes
npx mocha test/origamis.test.js
```

## Test Coverage

The origami backend route tests provide comprehensive coverage of:

### POST /:origamiId/vote Endpoint
- ✅ Successful vote submission with valid authentication
- ✅ Authentication required (401 when no JWT token/username)
- ✅ Authorization header properly set with Bearer token
- ✅ Handling voting service 401 responses
- ✅ Handling voting service 500 errors
- ✅ Handling voting service complete unavailability
- ✅ Support for different origami IDs
- ✅ Error logging verification

### GET /:origamiId/votes Endpoint
- ✅ Successful vote count retrieval
- ✅ Public endpoint access (no authentication required)
- ✅ Handling voting service errors (500 responses)
- ✅ Handling voting service complete unavailability
- ✅ Support for different origami IDs
- ✅ Zero vote count handling
- ✅ Error logging verification

## Testing Tools Used

- **Mocha** - Test framework
- **Chai** - Assertion library
- **Chai-HTTP** - HTTP testing utilities
- **Sinon** - Mocking and spying for console.error verification
- **Nock** - HTTP mocking for external voting service calls

## Test Structure

Each test file follows a consistent structure:
1. **Setup** - Mock dependencies and create test environment
2. **Test Cases** - Individual test scenarios with descriptive names
3. **Assertions** - Verify expected behavior
4. **Cleanup** - Reset mocks and clean up after tests

## Mocking Strategy

### External Service Mocking
- **Nock** mocks HTTP calls to the voting service (`http://products:8000`)
- Simulates various response scenarios (success, 401, 500, service down)
- Verifies correct Authorization headers are sent

### Authentication Testing
- Creates isolated test Express app with origami routes
- Mocks JWT token extraction from HTTP-only cookies
- Tests both authenticated and unauthenticated scenarios

### Error Logging Verification
- **Sinon** spies on `console.error` to verify error logging
- Ensures proper error handling without breaking the application

## Test Architecture

### Isolated Testing Environment
- Creates dedicated Express app for testing origami routes in isolation
- Independent of main application server and other routes
- Proper middleware setup mimicking production authentication flow

### Comprehensive Scenario Coverage
1. **Happy Path Testing** - Successful vote submission and retrieval
2. **Authentication Testing** - Verified JWT token handling and authorization
3. **Error Resilience** - Service failures, network issues, invalid responses
4. **Edge Cases** - Zero votes, different origami IDs, service unavailability

### Test Quality Assurance
- **Isolation** - Each test is independent with proper setup/teardown
- **Descriptive Names** - Clear test descriptions for maintainability
- **Realistic Mocking** - External service behavior accurately simulated
- **Cleanup** - All mocks and interceptors properly cleaned up
