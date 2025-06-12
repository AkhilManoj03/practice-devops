FROM --platform=linux/amd64 golang:1.23-alpine

WORKDIR /app

# Add necessary build tools
RUN apk add --no-cache git

# Create non-root user
RUN addgroup -S -g 1001 appuser && \
    adduser -S -G appuser -u 1001 -h /home/appuser appuser && \
    chown -R appuser:appuser /app

# Copy go mod files first for better caching
COPY --chown=appuser:appuser go.mod go.sum ./

# Download dependencies and verify modules
RUN go mod download && \
    go mod verify

# Copy the rest of the application
COPY --chown=appuser:appuser . .

# Update go.mod and go.sum
RUN go mod tidy

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -o app

# Switch to non-root user
USER appuser

# Set OpenTelemetry environment variables
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
ENV OTEL_SERVICE_NAME=recommendation-service

EXPOSE 8080

CMD ["./app"]
