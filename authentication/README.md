# Authentication Service

A robust JWT-based authentication microservice built with Rust and Axum framework, providing secure 
user authentication for the Craftista microservices architecture.

## Overview

This service handles user registration, authentication, and JWT token management using 
industry-standard security practices. It integrates with PostgreSQL for user storage and provides 
RSA-signed JWT tokens for secure inter-service communication. The service features a modern,
modular architecture with comprehensive observability and enhanced security measures.

## Features

### 🔐 Authentication & Authorization
- **User Registration** - Secure user signup with email and username validation
- **User Login** - Password-based authentication with bcrypt hashing
- **JWT Token Generation** - RS256 (RSA) signed tokens with configurable expiration
- **Role-Based Access Control** - User roles for authorization
- **Service-to-Service Authentication** - Internal API key protection for registration endpoint

### 🔑 Security Features
- **BCrypt Password Hashing** - Industry-standard password security with salt
- **RSA Key Pairs** - Public/private key cryptography for JWT signing
- **Token Validation** - Stateless JWT verification for other services
- **CORS Support** - Cross-origin resource sharing configuration
- **Internal API Key Middleware** - Shared secret authentication for service-to-service
communication

### 🌐 Standards Compliance
- **JWKS Endpoint** - Public key distribution for JWT verification
- **OpenID Connect Discovery** - Standard discovery endpoint for client configuration
- **JWT Claims** - Standard claims including subject, role, expiration, and issued time

### 📊 Monitoring & Observability
- **OpenTelemetry Integration** - Full distributed tracing with OTLP export
- **Structured Logging** - Comprehensive logging with configurable levels and thread information
- **Health Checks** - Service status monitoring
- **Custom Error Handling** - Centralized error management with proper HTTP status codes

### 🏗️ Architecture & Design
- **Modular Structure** - Clean separation of concerns with dedicated modules for handlers,
middleware, config, and models
- **Centralized Configuration** - Environment-based configuration management through Config struct
- **State Management** - Shared application state with database pool and configuration
- **Async/Await** - Full async support with Tokio runtime

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user (requires internal API key)
- `POST /api/auth/login` - Authenticate user and receive JWT token
- `GET /api/auth/status` - Get authentication status

### Standards & Discovery
- `GET /.well-known/jwks.json` - JSON Web Key Set for token verification
- `GET /.well-known/openid-configuration` - OpenID Connect discovery

## Request/Response Examples

### User Registration
```bash
curl -X POST http://localhost:8082/api/auth/register \
  -H "Content-Type: application/json" \
  -H "X-Internal-API-Key: your-internal-api-key" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com", 
    "password": "securepassword123"
  }'
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user_id": 1,
  "username": "johndoe"
}
```

### User Login
```bash
curl -X POST http://localhost:8082/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "securepassword123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### JWKS Endpoint
```bash
curl http://localhost:8082/.well-known/jwks.json
```

**Response:**
```json
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "product-service-key-1",
      "alg": "RS256",
      "n": "base64url-encoded-modulus",
      "e": "base64url-encoded-exponent"
    }
  ]
}
```

## Environment Variables

### Database Configuration
- `POSTGRES_USER` - PostgreSQL username (default: `devops`)
- `POSTGRES_PASSWORD` - PostgreSQL password (default: `catalogue`)
- `POSTGRES_HOST` - PostgreSQL host (default: `products-db`)
- `POSTGRES_PORT` - PostgreSQL port (default: `5432`)
- `POSTGRES_DB` - PostgreSQL database name (default: `products-db`)

### Authentication & Security
- `RSA_PRIVATE_KEY_PATH` - Path to RSA private key (default: `keys/private_key.pem`)
- `RSA_PUBLIC_KEY_PATH` - Path to RSA public key (default: `keys/public_key.pem`)
- `PRODUCT_KEY_ID` - Key ID for JWT header (default: `product-service-key-1`)
- `INTERNAL_API_KEY` - Shared secret for service-to-service authentication (default: `a-super-secret-key`)

### Service Configuration
- `PORT` - Port to run the service on (default: `8082`)
- `BASE_URL` - Base URL for OpenID Connect discovery (default: `http://authentication:8082`)
- `RUST_LOG` - Log level (default: `info`)

### OpenTelemetry Configuration
- `OTEL_SERVICE_NAME` - Service name for tracing (default: `craftista-authentication`)
- `OTEL_EXPORTER_OTLP_ENDPOINT` - OTLP collector endpoint (default: `http://otel-collector:4318/v1/traces`)
- `APP_VERSION` - Application version for tracing (default: `1.0.0`)
- `DEPLOYMENT_ENVIRONMENT` - Deployment environment (default: `production`)

## Getting Started

### Prerequisites
- Rust 1.87 or later
- PostgreSQL database
- RSA key pair (for JWT signing)

### Setup

1. **Generate RSA Key Pair:**
```bash
mkdir -p keys
openssl genrsa -out keys/private_key.pem 2048
openssl rsa -in keys/private_key.pem -pubout -out keys/public_key.pem
```

2. **Database Setup:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

3. **Environment Configuration:**
```bash
# Create .env file
cat > .env << EOF
POSTGRES_USER=devops
POSTGRES_PASSWORD=catalogue
POSTGRES_HOST=products-db
POSTGRES_PORT=5432
POSTGRES_DB=products-db
INTERNAL_API_KEY=your-secure-internal-api-key
OTEL_SERVICE_NAME=craftista-authentication
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
EOF
```

4. **Build and Run:**
```bash
cargo build --release
cargo run
```

### Docker Deployment

```bash
# Build image
docker build -t authentication-service .

# Run container
docker run -p 8082:8082 \
  -e POSTGRES_USER="devops" \
  -e POSTGRES_PASSWORD="catalogue" \
  -e POSTGRES_HOST="products-db" \
  -e POSTGRES_PORT="5432" \
  -e POSTGRES_DB="products-db" \
  -e INTERNAL_API_KEY="your-secure-internal-api-key" \
  -e OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4318/v1/traces" \
  -v $(pwd)/keys:/app/keys \
  authentication-service
```

## Integration with Other Services

### JWT Token Verification
Other microservices can verify JWT tokens by:

1. **Fetching JWKS:** `GET /.well-known/jwks.json`
2. **Validating JWT:** Using the public key to verify RS256 signatures
3. **Extracting Claims:** User identity and role from token payload

### Service-to-Service Registration
Services can register users by including the internal API key:

```bash
curl -X POST http://authentication:8082/api/auth/register \
  -H "Content-Type: application/json" \
  -H "X-Internal-API-Key: your-internal-api-key" \
  -d '{"username": "user", "email": "user@example.com", "password": "pass"}'
```

## Architecture

The service follows a modular architecture with clear separation of concerns:

```
src/
├── main.rs              # Application entry point and routing
├── config.rs            # Centralized configuration management
├── state.rs             # Shared application state
├── errors.rs            # Custom error types and handling
├── models.rs            # Data structures and serialization
├── middleware.rs        # Authentication middleware
├── telemetry.rs         # OpenTelemetry configuration
└── handlers/            # Request handlers
    ├── mod.rs
    ├── login.rs         # Login endpoint
    ├── register.rs      # Registration endpoint
    ├── status.rs        # Health check endpoint
    └── openid.rs        # JWKS and OpenID discovery
```

## Security Considerations

- **Password Storage:** BCrypt with salt for secure password hashing
- **Token Security:** RSA signatures prevent token tampering
- **Key Management:** Private keys should be securely stored and rotated
- **HTTPS:** Always use HTTPS in production environments
- **Token Expiration:** Tokens expire after 1 hour for security
- **Internal API Keys:** Use strong, unique keys for service-to-service communication
- **Environment Variables:** Never commit sensitive configuration to version control

## Observability

The service includes comprehensive observability features:

- **Distributed Tracing:** Full OpenTelemetry integration with OTLP export
- **Structured Logging:** JSON-formatted logs with correlation IDs
- **Metrics:** Service performance and health metrics
- **Health Checks:** Endpoint monitoring and database connectivity checks

## Error Handling

The service implements centralized error handling with:

- **Custom Error Types:** Specific error variants for different failure modes
- **HTTP Status Mapping:** Proper HTTP status codes for different error types
- **Structured Responses:** Consistent JSON error responses
- **Logging:** Comprehensive error logging for debugging
