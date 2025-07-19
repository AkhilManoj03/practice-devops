# Project Modifications and Improvements

## Overview
This document outlines the significant changes and improvements made to the original [Craftista 
project](https://github.com/craftista/craftista). The modifications were primarily focused on 
enhancing the application's performance,  reliability, and maintainability while gaining hands-on 
experience with modern DevOps practices and development techniques.

## Changes Made

### 1. Containerization and Orchestration
- Dockerized all microservices:
  - [Frontend service](frontend/Dockerfile)
  - [Catalogue service](catalogue/Dockerfile)
  - [Recommendation service](recommendation/Dockerfile)
  - [Voting service](voting/Dockerfile)
- Created a comprehensive [Docker Compose configuration](docker-compose.yml) for local development 
and testing
- Improved service isolation and deployment consistency

**Related PR**: [docker: dockerize application #1](https://github.com/AkhilManoj03/microservices-showcase/pull/1)

### 2. Voting Service Refactoring
- **Original Implementation**: Java Spring Boot ([original code](voting/))
- **New Implementation**: Python FastAPI ([new code](voting-fastapi/))
- **Reason for Change**: 
  - Addressed performance issues with the original Spring Boot implementation
  - Eliminated slow boot times and hanging issues
  - Improved service reliability and stability
  - Reduced resource consumption

**Related PR**: [voting: new framework for voting service #2](https://github.com/AkhilManoj03/microservices-showcase/pull/2)

### 3. Catalogue Service Modernization
- **Original Implementation**: Python Flask ([original code](catalogue/))
- **New Implementation**: Python FastAPI ([new code](catalogue-fastapi/))
- **Reason for Change**:
  - Prepared for service consolidation
  - Improved API performance and documentation
  - Enhanced type safety and validation
  - Better async support

**Related PR**: [catalogue: recreate service in FastAPI #3](https://github.com/AkhilManoj03/microservices-showcase/pull/3)

### 4. Service Consolidation
- Created a unified [Origami Product Service](combined-fastapi/)
- Combined Catalogue and Voting services into a single API
- **Benefits**:
  - Reduced service complexity
  - Eliminated redundant code
  - Improved maintainability
  - Better resource utilization
  - Simplified deployment and monitoring

**Related PR**: [combined: create combined voting and catalogue service #4](https://github.com/AkhilManoj03/microservices-showcase/pull/4)

### 5. Database Flexibility
- Implemented dual database support:
  - JSON file storage (for development/testing)
  - PostgreSQL database (for production)
- Added database abstraction layer
- Improved data persistence and reliability

**Related PR**: [combined: add db support in data access layer #5](https://github.com/AkhilManoj03/microservices-showcase/pull/5)

### 6. Performance Optimization
- Implemented Redis caching layer
- Added caching between API and database
- **Benefits**:
  - Reduced database load
  - Improved response times
  - Better scalability
  - Enhanced user experience

**Related PR**: [combined: feat: implement Redis caching for API #6](https://github.com/AkhilManoj03/microservices-showcase/pull/6)

### 7. Observability and Distributed Tracing
- Implemented OpenTelemetry across all microservices for comprehensive observability
- Added Jaeger for distributed tracing visualization
- **Approach**: Standardized on automatic instrumentation across all services for consistency
- **Benefits**:
  - End-to-end request tracing across microservices
  - Performance monitoring and bottleneck identification
  - Error tracking and debugging capabilities
  - Service dependency mapping
  - Improved system observability and maintainability

**Related PR**: [otel: Implement OpenTelementary and Jaegar #8](https://github.com/AkhilManoj03/microservices-showcase/pull/8)

### 8. Application Architecture Restructuring and Cleanup
- **Restructured Combined FastAPI Service**: Reorganized the application into distinct architectural layers
  - **API Layer**: Hosts all public API routes and their dependencies
  - **Core Layer**: Contains business logic for Product, Votes, and System services  
  - **Infrastructure Layer**: Manages data access logic and database operations
- **Removed JSON Datasource Support**:
  - Eliminated all JSON data source configurations and related code
  - Simplified data access layer to use only PostgreSQL for persistent storage
  - Updated `products.json` to serve exclusively for initial database setup
- **Service Renaming**: Renamed `combined-fastapi` folder to `product` for better clarity and representation
- **Database Configuration Improvements**: 
  - Replaced generic database configuration with specific PostgreSQL settings
  - Made database configuration required (non-optional) since database is now the only data source
  - Updated field names to follow PostgreSQL conventions (`postgres_*` prefix)
- **Benefits**:
  - Enhanced scalability and maintainability through clear separation of concerns
  - Reduced complexity by eliminating dual data source support
  - Improved code organization for easier onboarding and future development
  - Simplified configuration management
  - Better alignment with production-ready practices

**Related PR**: [product: refactor: restructure application architecture and remove JSON datasource #9](https://github.com/AkhilManoj03/microservices-showcase/pull/9)

### 9. Addition of Authentication Service
- **New Microservice**: Introduced a Rust-based authentication service using the Axum framework
- **Features**:
  - User registration and login with bcrypt password hashing
  - JWT token generation (RS256, 1-hour expiration, user roles)
  - JWKS and OpenID Connect endpoints for standards-based integration
  - Role-based access control for secure API usage
  - CORS support and structured logging
- **Integration**:
  - Frontend uses the authentication service for user login/registration; JWT tokens are set as 
  HTTP-only cookies
  - Product service validates JWT tokens using the JWKS endpoint, ensuring only authenticated users 
  can access protected endpoints (e.g., voting)
- **Security**:
  - BCrypt for password hashing, RSA for JWT signing
  - Environment-based configuration for database and key management

**Related PR**: [auth: implement authentication microservice #9](https://github.com/AkhilManoj03/microservices-showcase/pull/9)

### 10. Docker Infrastructure Optimization
- **Multi-stage Build Implementation**: Refactored all Dockerfiles to use multi-stage builds for improved efficiency
- **Base Image Optimization**: Migrated services to Alpine Linux for smaller runtime footprints
- **Build Context Optimization**: Added .dockerignore files to exclude unnecessary files from Docker context
- **Dependency Caching**: Implemented cargo-chef for Rust services to prevent redundant dependency rebuilds
- **Version Control**: Introduced build arguments for consistent version management across all Dockerfiles
- **Image Size Reductions**:
  - Authentication service: 71% reduction (121MB → 40MB)
  - Product service: 85% reduction (793MB → 120MB)
  - Recommendation service: 97% reduction (782MB → 26MB)
  - Frontend service: Applied best practices with multi-stage builds
- **Benefits**:
  - Faster build times through efficient dependency caching
  - Reduced network overhead during image transfers
  - Lower storage requirements and memory usage
  - Enhanced security through minimal base images
  - Improved deployment speed and scalability
  - Consistent Alpine-based runtime environments

**Related PR**: [Docker: Optimize docker infrastructure #12](https://github.com/AkhilManoj03/microservices-showcase/pull/12)

### 11. Authentication Service Architecture Enhancement
- **Major Refactoring**: Transformed the authentication service from a monolithic structure to a
modern, modular architecture
- **Security Enhancements**:
  - Service-to-Service Authentication: Added internal API key protection for registration endpoint
  - Custom authentication middleware using shared secrets
  - Enhanced registration flow requiring `X-Internal-API-Key` header
- **Observability Integration**:
  - Full OpenTelemetry distributed tracing with OTLP export
  - Structured logging with configurable levels and thread information
  - Comprehensive request flow monitoring and performance insights
- **Configuration Management**:
  - Centralized `Config` struct for all environment variables
  - Improved maintainability with configuration accessible via `AppState`
  - Streamlined setup for different deployment environments
- **Error Handling Improvements**:
  - Custom `AppError` enum with specific error variants
  - Proper HTTP status code mapping for consistent responses
  - Enhanced debugging with structured error responses
- **Benefits**:
  - Enhanced security through service-to-service authentication
  - Improved code maintainability following Rust API conventions
  - Better observability and monitoring capabilities
  - Centralized configuration management
  - Robust error handling and debugging support

**Related PR**: [auth: Major refactoring and enhancement #13](https://github.com/AkhilManoj03/microservices-showcase/pull/13)

### 12. Database and Recommendation Service Refactoring
- **Database Initialization Improvements**: Moved products table population logic from the products
API to the `init-db` file, improving separation of concerns and modularity
- **Recommendation Service Modernization**:
  - Replaced config.json with environment variables for better containerization
  - Connected to PostgreSQL database for product retrieval instead of in-memory selection
  - Implemented modular API structure with dedicated files for different concerns (`home.go`, 
`status.go`, `origami.go`)
  - Added multi-architecture Docker support with `TARGETARCH` build argument
- **Benefits**:
  - Enhanced performance through direct database queries
  - Improved maintainability with better code organization
  - Better deployment flexibility and developer experience
  - Comprehensive documentation with API examples

**Related PR**: [recom: refactor recommendation service](https://github.com/AkhilManoj03/microservices-showcase/pull/14)

### 13. Product Service Testing Framework and Unit Tests
- **Testing Framework Integration**:
  - Introduced a comprehensive testing framework for the Product Service using pytest.
  - Added custom pytest configuration and fixtures for robust and isolated testing.
- **Unit Test Coverage**:
  - Developed extensive unit tests for API endpoints (products, votes, system info), core services
  (ProductService, SystemService, VoteService), and infrastructure components (CacheManager,
  DataAccessLayer).
  - Implemented test cases for successful operations, error handling, edge cases, and data
  transformation.
  - Utilized fixtures and mock services to ensure test isolation and reliability.
  - Enhanced test coverage for authentication, service integration, health checks, and system
  information retrieval.
- **Test Runner Script**:
  - Added a script to streamline execution of unit, integration, and infrastructure tests with clear
  command descriptions and error handling.
- **Documentation Enhancements**:
  - Expanded the main `README.md` with details about the testing framework, highlighting 100+ unit
  tests, async testing support, and error scenario coverage.
  - Added a dedicated `README.md` in the `tests` directory, outlining testing architecture,
  philosophy, best practices, and instructions for running tests and managing dependencies.
  - Emphasized isolation, mocking strategies, and performance optimization in the testing process.
- **Benefits**:
  - Significantly improved reliability, maintainability, and quality assurance for the Product Service.
  - Facilitated easier maintenance and future development through a solid testing foundation.
  - Reduced risk of regressions and increased confidence in code changes.

**Related PR**: [product: add unit tests to product service #16](https://github.com/AkhilManoj03/microservices-showcase/pull/16)

### 14. Recommendation Service Unit Test Suite
- **Comprehensive Unit Test Coverage**: Added a robust suite of unit tests for the Recommendation
Service, covering data access, API endpoints (status, home, origami), and rendering logic.
- **Test Infrastructure**: Introduced test helpers and utilized `sqlmock` for isolated database
testing. Leveraged Gin's testing framework for HTTP endpoint validation.
- **Handler Refactoring for Testability**: Refactored API handlers to accept function parameters
(dependency injection), improving testability and separation of concerns.
- **Documentation**: Added a detailed README for the test suite, outlining testing philosophy,
setup, and best practices.
- **Benefits**:
  - Improved code reliability and maintainability
  - Easier future enhancements and refactoring
  - Clearer separation of concerns and better test isolation

**Related PR**: [recom: add unit tests for recommendation service #17](https://github.com/AkhilManoj03/microservices-showcase/pull/17)

### 15. Authentication Service Unit Test Suite
- **Comprehensive Unit Test Coverage**: Added a robust suite of unit tests for the Authentication
Service, covering all major authentication handlers (login, registration, JWKS/OpenID, and status).
- **Test Infrastructure**:
  - Introduced new test dependencies (`anstyle`, `async-stream`, `mockall`, `rstest`, etc.) and 
  development tools (`tokio-test`, `tempfile`, `axum-test`).
  - Updated `.gitignore` to exclude `.pem` key files from version control.
  - Enabled the authentication service to be compiled as both a library and a binary for easier testing.
  - Modularized the codebase with submodules for configuration, error handling, handlers, middleware, 
  models, state, and telemetry.
  - Established a simplified state setup for unit tests that do not require a database connection.
- **Handler Unit Tests**:
  - Login handler: Tests for successful login, invalid credentials, invalid payloads, and JSON 
  serialization.
  - JWKS/OpenID handlers: Tests for response validation, key integrity, error handling, 
  serialization, and performance.
  - Registration handler: Tests for successful registration, user conflict, invalid payloads, and 
  serialization.
  - Status handler: Tests for response structure, content, authentication field, serialization, and 
  performance.
- **Documentation**:
  - Added a comprehensive README for the authentication service tests, detailing test structure, 
  categories, guidelines for adding new tests, and instructions for running tests.
- **Benefits**:
  - Improved code reliability, maintainability, and test coverage
  - Safer refactoring and future enhancements
  - Clear documentation and guidelines for contributors

**Related PR**: [auth: add unit tests for authentication service #18](https://github.com/AkhilManoj03/microservices-showcase/pull/18)

### 16. Frontend Service Unit Test Infrastructure
- **Testing Framework Setup**: Introduced comprehensive unit testing infrastructure for the Frontend
Service using Node.js built-in test runner and modern testing tools
- **Test Dependencies and Tools**:
  - Added `jsdom` for DOM environment simulation in browser-like testing scenarios
  - Integrated `sinon` for advanced mocking, stubbing, and test utilities
  - Updated `package.json` with dedicated test scripts for origami functionality
- **Documentation and Guidelines**:
  - Created comprehensive `README.md` for unit tests covering test structure, coverage details,
  and tool usage
  - Documented step-by-step instructions for running tests, including setup and individual test
  execution
  - Highlighted mocking strategies and error logging verification for robust testing practices
- **Testing Strategy**:
  - Focused on origami functionality testing with comprehensive coverage
  - Implemented error handling and logging verification
  - Utilized mock-based testing for external dependencies
  - Ensured test isolation and reliability through proper tooling

**Related PR**: [frontend: add unit tests to frontend service #19](https://github.com/AkhilManoj03/microservices-showcase/pull/19)

### 17. Comprehensive Integration Test Suite
- **Integration Testing Framework**: Introduced a robust integration testing framework for the
entire microservices architecture, providing end-to-end validation of service functionality and
inter-service communication
- **Test Infrastructure**:
  - **Core Infrastructure**: Created `tests/config.sh` for centralized configuration management
  and `tests/helper_scripts.sh` for shared utility functions including logging, error handling,
  HTTP request execution, and response validation
  - **Test Orchestration**: Implemented `tests/integration/integration_runner.sh` as the main
  orchestrator supporting both sequential and parallel test execution modes
  - **Service-Specific Test Suites**: Developed dedicated test suites for each microservice:
- **Advanced Features**:
  - **Flexible Execution Modes**: Sequential execution (default), parallel execution for faster
  feedback, and individual suite testing for focused validation
  - **Robust Error Handling**: Exponential backoff for service health checks, graceful failure
  handling with detailed error messages, and timeout management with configurable limits
  - **Rich Reporting & Logging**: Color-coded console output with status indicators, detailed
  logging to `integration-tests.log`, comprehensive test summaries with success rates and timing,
  and verbose mode for debugging
  - **Google Shell Style Guide Compliance**: Comprehensive function documentation, proper variable
  naming conventions, strict error handling with `set -uo pipefail`, and modular design with
  separation of concerns
- **Configuration Management**:
  - **Environment Variables**: Support for global settings (TIMEOUT, VERBOSE, PARALLEL_MODE) and
  service-specific URLs
  - **Command Line Options**: Verbosity control, timeout configuration, specific suite execution,
  and parallel execution flags
  - **Priority System**: Command line options take precedence over environment variables, which
  take precedence over default values
- **Response Validation**: Comprehensive validation including HTTP status code verification, JSON
structure validation using `jq`, field presence validation, and response timing monitoring
- **CI/CD Integration**: Designed for seamless pipeline integration with meaningful exit codes
(0=success, 1-N=failed tests, 124=timeout), detailed logging, and performance monitoring capabilities
- **Documentation**: Comprehensive `tests/integration/README.md` covering architecture, features,
quick start guide, configuration options, test structure, logging, and CI/CD integration

**Related PR**: [tests: add comprehensive integration test suite #20](https://github.com/AkhilManoj03/microservices-showcase/pull/20)

## Learning Outcomes
This project has provided valuable hands-on experience in:
- Modern containerization techniques
- Microservices architecture and optimization
- API development and performance tuning
- Database design and caching strategies
- DevOps best practices
- Service consolidation and refactoring
- Distributed tracing and observability implementation
