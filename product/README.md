# Combined Origami Service

A unified FastAPI service that combines both product catalogue and voting functionality into a
single API. This service eliminates the need for inter-service communication and simplifies the
architecture while maintaining all existing endpoints.

## Features

- **All Original Endpoints**: Maintains compatibility with both catalogue and voting service APIs
- **Simplified Architecture**: No inter-service HTTP calls needed
- **Better Performance**: Direct data access without network overhead
- **Easier Deployment**: Single service to deploy and manage

## API Endpoints

### Catalogue Service Endpoints (Original)
- `GET /api/products` - Get all products with vote counts
- `GET /api/products/{product_id}` - Get specific product with vote count

### Voting Service Endpoints (Original)
- `GET /api/origamis` - Get all origamis with vote counts (alias for products)
- `GET /api/origamis/{origami_id}` - Get specific origami with vote count
- `GET /api/origamis/{origami_id}/votes` - Get vote count for specific origami
- `POST /api/origamis/{origami_id}/vote` - Vote for an origami

### System Endpoints
- `GET /health` - Health check
- `GET /api/system-info` - System information
- `GET /` - Home page

## Running the Service

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build the image
docker build -t combined-origami-service .

# Run the container
docker run -p 8000:8000 combined-origami-service
```

### Docker Compose with PostgreSQL as datasource

```bash
# build the docker-compose file
docker compose up --build
```

## Configuration

The service can be configured via environment variables:

- `LOG_LEVEL`: Logging level (default: "INFO")
- `HOST`: Server host (default: "0.0.0.0")
- `PORT`: Server port (default: 8000)

## Benefits of the Combined Approach

1. **Reduced Complexity**: No need to manage inter-service communication
2. **Better Performance**: Direct data access without HTTP overhead
3. **Simplified Deployment**: Single service to deploy and scale
4. **Data Consistency**: Votes and products are always in sync
5. **Easier Testing**: Single service to test instead of multiple services
6. **Lower Resource Usage**: Fewer containers and network calls
7. **Single Data Source**: All data in one place, easier to backup and manage

## Migration from Separate Services

This combined service maintains full API compatibility with the original separate services, so
existing clients can continue to use the same endpoints without any changes. 