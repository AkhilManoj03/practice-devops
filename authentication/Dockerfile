# Build arguments for version control
ARG RUST_VERSION=1.87.0
ARG ALPINE_VERSION=3.22

# Build stage
FROM rust:${RUST_VERSION}-alpine${ALPINE_VERSION} AS builder

# Install build dependencies for Alpine
RUN apk add --no-cache musl-dev pkgconf openssl-dev

# Set the working directory
WORKDIR /app

# Copy only the files needed for building
COPY Cargo.toml Cargo.lock ./
COPY src/ ./src/

# Build for release with static linking for Alpine
ENV RUSTFLAGS="-C target-feature=-crt-static"
RUN cargo build --release


# Runtime stage
FROM alpine:${ALPINE_VERSION}.0

# Install runtime dependencies
RUN apk add --no-cache ca-certificates libgcc

# Create a non-root user
RUN addgroup -g 1001 appuser && \
    adduser -u 1001 -G appuser -s /bin/sh -D appuser

# Set the working directory
WORKDIR /app

# Copy the binary from the builder stage
COPY --from=builder /app/target/release/authentication-service /app/authentication-service

# Copy RSA keys
COPY keys/ /app/keys/

# Make sure the binary is executable
RUN chmod +x /app/authentication-service

# Change ownership to the app user
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8082

# Set environment variables
ENV RUST_LOG=info
ENV PORT=8082

# Set OpenTelemetry environment variables
ENV OTEL_SERVICE_NAME=authentication-api
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
ENV OTEL_TRACES_SAMPLER=always_on
ENV APP_VERSION=1.0.0
ENV DEPLOYMENT_ENVIRONMENT=production

# Run the application with explicit path
CMD ["/app/authentication-service"]
