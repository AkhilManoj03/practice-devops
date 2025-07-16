# Product Service

A unified FastAPI service that combines both product catalogue and voting functionality into a
single, high-performance API. Built with a clean architecture, this service is modular, scalable,
and easy to maintain. It features secure endpoints using JWT authentication and a Redis-based cache
for accelerated data retrieval.

## Key Features

- **Clean Architecture**: A modular design separating concerns into distinct layers (API, Core,
Infrastructure), making the codebase organized, testable, and maintainable.
- **Secure Endpoints**: Implements JWT-based authentication using the Authentication Service to
protect sensitive endpoints, ensuring that operations like voting are secure.
- **High-Performance Caching**: Utilizes a Cache-Aside (lazy loading) strategy with Redis to
reduce database load and deliver faster API responses for frequently accessed data.
- **Unified API**: Consolidates the original catalogue and voting services into a single, cohesive
API, simplifying client interactions and deployment.
- **Observability**: Integrated with OpenTelemetry for tracing, providing visibility into
application performance and behavior.
- **Data Consistency**: By using a single data source for products and votes, data integrity is
ensured across the application.
- **Enterprise-Grade Testing**: Comprehensive test suite with 260+ unit tests covering all
architectural layers, featuring sophisticated mocking, async testing, and complete isolation for
reliable CI/CD integration.

## Architecture

The service is structured following the principles of Clean Architecture:

- **API Layer**: Handles HTTP requests, routing, validation, and serialization. It contains FastAPI
routers, dependencies, and middleware.
- **Core Layer**: Contains the core business logic, including services that orchestrate business
operations, domain models (Pydantic models), and custom exceptions. This layer is independent of
external frameworks and technologies.
- **Infrastructure Layer**: Manages external concerns like database access (PostgreSQL), caching
(Redis), and communication with other services. It implements the interfaces defined by the Core
layer.

## API Endpoints

### Catalogue Service Endpoints (Original)
- `GET /api/products` - Get all products with vote counts
- `GET /api/products/{product_id}` - Get specific product with vote count

### Voting Service Endpoints (Original)
- `GET /api/origamis` - Get all origamis with vote counts (alias for products)
- `GET /api/origamis/{origami_id}` - Get specific origami with vote count
- `GET /api/origamis/{origami_id}/votes` - Get vote count for specific origami
- `POST /api/origamis/{origami_id}/vote` - Vote for an origami (Requires Authentication)

### System Endpoints
- `GET /health` - Health check
- `GET /api/system-info` - System information
- `GET /` - Home page

## Getting Started

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create a .env file and configure it (see Configuration section)

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build the image
docker build -t product-service .

# Run the container (make sure .env file is present)
docker run -p 8000:8000 --env-file .env product-service
```

### Docker Compose with PostgreSQL & Redis

The service can be run with its dependencies using Docker Compose. This is the recommended way to
run the service and all its dependencies.

```bash
# Build and run the services
docker compose up --build
```

## Configuration

The service is configured via environment variables. Create a `.env` file in the `product/` directory
to hold your settings.

| Variable              | Description                                        | Default                         | Required |
|-----------------------|----------------------------------------------------|---------------------------------|----------|
| `LOG_LEVEL`           | Logging level                                      | "INFO"                          | No       |
| `HOST`                | Server host                                        | "0.0.0.0"                       | No       |
| `PORT`                | Server port                                        | 8000                            | No       |
| `AUTH_SERVICE_URL`    | URL of the authentication service for JWKS         | "http://authentication:8080"    | No       |
| `PRODUCT_KEY_ID`      | Key ID for JWT verification                        | "product-service-key-1"         | No       |
| `POSTGRES_USER`       | PostgreSQL database username                       | -                               | Yes      |
| `POSTGRES_PASSWORD`   | PostgreSQL database password                       | -                               | Yes      |
| `POSTGRES_DB`         | PostgreSQL database name                           | -                               | Yes      |
| `POSTGRES_HOST`       | PostgreSQL database host                           | -                               | Yes      |
| `POSTGRES_PORT`       | PostgreSQL database port                           | 5432                            | No       |
| `REDIS_HOST`          | Redis host for caching.                            | -                               | No       |
| `REDIS_PORT`          | Redis port                                         | 6379                            | No       |

## Testing

The Product Service features a **comprehensive, enterprise-grade test suite** that demonstrates
professional software development practices and ensures code reliability.

### 🎯 **Test Suite Highlights**
- **260+ Unit Tests** across all architectural layers (API, Core, Infrastructure)
- **Complete Isolation** with sophisticated mocking - no external dependencies
- **Async Testing Support** with proper AsyncMock implementation
- **Error Scenario Coverage** including connection failures, timeouts, and edge cases
- **Fast Execution** - entire suite runs in seconds for efficient CI/CD
- **Clean Architecture Testing** with proper layer separation and abstraction boundary verification

### 🚀 **Quick Start**
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
python run_tests.py all

# Run tests with coverage
python run_tests.py coverage

# Run specific layer tests
python run_tests.py api           # API layer tests
python run_tests.py core          # Business logic tests  
python run_tests.py infrastructure # Infrastructure tests
```

### 📚 **Detailed Documentation**
For comprehensive testing documentation, architecture details, and advanced usage, see:
**[📖 Testing Framework Documentation](tests/README.md)**

The testing framework showcases enterprise-level practices including hierarchical fixture
architecture, sophisticated error simulation, transaction testing, and comprehensive mocking
strategies suitable for production environments.

## Migration from Separate Services

This product service maintains full API compatibility with the original separate services, so
existing clients can continue to use the same endpoints without any changes. The primary difference
is that the `POST /api/origamis/{origami_id}/vote` endpoint now requires a valid JWT Bearer token
for authentication.
