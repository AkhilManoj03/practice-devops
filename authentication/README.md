# Authentication Service

A robust JWT-based authentication microservice built with Rust and Axum framework, providing secure 
user authentication for the Craftista microservices architecture.

## Overview

This service handles user registration, authentication, and JWT token management using 
industry-standard security practices. It integrates with PostgreSQL for user storage and provides 
RSA-signed JWT tokens for secure inter-service communication.

## Features

### 🔐 Authentication & Authorization
- **User Registration** - Secure user signup with email and username validation
- **User Login** - Password-based authentication with bcrypt hashing
- **JWT Token Generation** - RS256 (RSA) signed tokens with configurable expiration
- **Role-Based Access Control** - User roles for authorization

### 🔑 Security Features
- **BCrypt Password Hashing** - Industry-standard password security with salt
- **RSA Key Pairs** - Public/private key cryptography for JWT signing
- **Token Validation** - Stateless JWT verification for other services
- **CORS Support** - Cross-origin resource sharing configuration

### 🌐 Standards Compliance
- **JWKS Endpoint** - Public key distribution for JWT verification
- **OpenID Connect Discovery** - Standard discovery endpoint for client configuration
- **JWT Claims** - Standard claims including subject, role, expiration, and issued time

### 📊 Monitoring & Observability
- **Health Checks** - Service status monitoring
- **Structured Logging** - Comprehensive tracing with different log levels
- **Error Handling** - Proper HTTP status codes and error responses

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Authenticate user and receive JWT token
- `GET /api/auth/status` - Get authentication status

### Standards & Discovery
- `GET /.well-known/jwks.json` - JSON Web Key Set for token verification
- `GET /.well-known/openid-configuration` - OpenID Connect discovery

## Request/Response Examples

### User Registration
```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com", 
    "password": "securepassword123"
  }'
```

### User Login
```bash
curl -X POST http://localhost:8080/api/auth/login \
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

### Service Configuration
- `PORT` - Port to run the service on (default: `8080`)
- `BASE_URL` - Base URL for OpenID Connect discovery (default: `http://authentication:8080`)
- `RUST_LOG` - Log level (default: `info`)

## Getting Started

### Prerequisites
- Rust 1.75 or later
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
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user'
);
```

3. **Build and Run:**
```bash
cargo build --release
cargo run
```

### Docker Deployment

```bash
# Build image
docker build -t authentication-service .

# Run container
docker run -p 8080:8080 \
  -e POSTGRES_USER="devops" \
  -e POSTGRES_PASSWORD="catalogue" \
  -e POSTGRES_HOST="products-db" \
  -e POSTGRES_PORT="5432" \
  -e POSTGRES_DB="products-db" \
  -v $(pwd)/keys:/app/keys \
  authentication-service
```

## Integration with Other Services

Other microservices can verify JWT tokens by:

1. **Fetching JWKS:** `GET /.well-known/jwks.json`
2. **Validating JWT:** Using the public key to verify RS256 signatures
3. **Extracting Claims:** User identity and role from token payload

## Security Considerations

- **Password Storage:** BCrypt with salt for secure password hashing
- **Token Security:** RSA signatures prevent token tampering
- **Key Management:** Private keys should be securely stored and rotated
- **HTTPS:** Always use HTTPS in production environments
- **Token Expiration:** Tokens expire after 1 hour for security
