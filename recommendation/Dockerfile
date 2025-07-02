# Build arguments for version control
ARG GO_VERSION=1.23.10
ARG ALPINE_VERSION=3.22

# Build stage
FROM golang:${GO_VERSION}-alpine${ALPINE_VERSION} AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache git ca-certificates

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download && \
    go mod verify

# Copy source code
COPY . .

# Ensure go.mod and go.sum are up to date
RUN go mod tidy

# Build the application with optimizations for static binary
RUN CGO_ENABLED=0 \
    GOOS=linux \
    GOARCH=amd64 \
    go build -ldflags='-w -s -extldflags "-static"' -o app .


# Runtime stage
FROM alpine:${ALPINE_VERSION}.0

# Install runtime dependencies
RUN apk add --no-cache ca-certificates tzdata && \
    rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -S -g 1001 appuser && \
    adduser -S -G appuser -u 1001 -h /home/appuser appuser

WORKDIR /app

# Copy the binary from builder stage
COPY --from=builder --chown=appuser:appuser /build/app ./app

# Copy necessary runtime files
COPY --chown=appuser:appuser config.json ./
COPY --chown=appuser:appuser static/ ./static/
COPY --chown=appuser:appuser templates/ ./templates/
COPY --chown=appuser:appuser data/ ./data/

# Switch to non-root user
USER appuser

# Set OpenTelemetry environment variables
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
ENV OTEL_SERVICE_NAME=recommendation-service

EXPOSE 8080

CMD ["./app"]
