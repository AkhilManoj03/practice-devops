# Recommendation Service

A Go-based microservice using the Gin framework that provides daily origami recommendations. It
fetches a random product from a PostgreSQL database and is instrumented with OpenTelemetry for
observability.

## Overview

This service is a core component of the Craftista platform, responsible for suggesting a new origami
creation to users each day. It serves a simple HTML homepage, provides a Restful API for fetching
recommendations and checking service status, and connects to a shared PostgreSQL database to
retrieve product information.

## Features

### 🖼️ API & Frontend
- **Random Recommendation** - An API endpoint to fetch a random origami product.
- **Service Status** - A health check endpoint to verify service and database connectivity.
- **HTML Homepage** - A simple web page displaying system information and available API endpoints.

### 🗃️ Database
- **PostgreSQL Integration** - Connects to a PostgreSQL database using the `pgx` driver.
- **Randomized Queries** - Fetches a single product at random from the `products` table.

### 📊 Observability
- **OpenTelemetry Integration** - Fully instrumented for tracing to provide insights into request
flows and performance.
- **Structured Logging** - Configured for structured logging for easier debugging and monitoring.

### 🐳 Containerization
- **Optimized Dockerfile** - A multi-stage Dockerfile creates a small, secure, and efficient final
image.
- **Non-Root User** - The container runs with a non-root user for enhanced security.
- **Multi-Arch Builds** - Automatically builds for the correct platform architecture using
`TARGETARCH`.

## API Endpoints

- `GET /` - Renders the HTML homepage.
- `GET /api/origami-of-the-day` - Returns a random origami product as a JSON object.
- `GET /api/recommendation-status` - Returns the operational status of the service and its database
connection.

## Request/Response Examples

### Get Origami of the Day
```bash
curl http://localhost:8080/api/origami-of-the-day
```
**Response:**
```json
{
  "id": 15,
  "name": "Penguin",
  "description": "A cute origami penguin.",
  "image_url": "/static/images/origami/015-penguin.png",
  "votes": 120
}
```

### Get Service Status
```bash
curl http://localhost:8080/api/recommendation-status
```
**Response:**
```json
{
  "status": "operational",
  "database_status": "operational"
}
```

## Environment Variables

| Variable                      | Description                                                              | Default                       |
| ----------------------------- | ------------------------------------------------------------------------ | ----------------------------- |
| `DATABASE_URL`                | **Required.** The connection string for the PostgreSQL database.         | `""`                          |
| `OTEL_SERVICE_NAME`           | The service name for OpenTelemetry tracing.                              | `recommendation-service`      |
| `APP_VERSION`                 | The application version, also used in OpenTelemetry traces.              | `1.0.0`                       |
| `DEPLOYMENT_ENVIRONMENT`      | The deployment environment for OpenTelemetry.                            | `production`                  |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | The OTLP collector endpoint for exporting traces.                        | `otel-collector:4318`         |


## Getting Started

### Prerequisites
- Go 1.20 or later
- A running PostgreSQL database instance

### Database Setup
The service requires a `products` table in the database. You can create it using the following SQL
schema:
```sql
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    votes INTEGER DEFAULT 0
);
```

### Build and Run
1. **Set the database connection string:**
   ```bash
   export DATABASE_URL="postgres://user:password@hostname:5432/dbname"
   ```

2. **Build the application:**
   ```bash
   go build -o app .
   ```

3. **Run the application:**
   ```bash
   ./app
   ```
The service will start on port `8080`.

## Docker Deployment

### Build the Image
```bash
docker build -t recommendation-service .
```

### Run the Container
```bash
docker run -p 8080:8080 \
  -e DATABASE_URL="postgres://user:password@hostname:5432/dbname" \
  -e OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4318/v1/traces" \
  --name recommendation-app \
  recommendation-service
```
This command starts the service and connects it to a PostgreSQL database named `products-db` and an
OpenTelemetry collector.
