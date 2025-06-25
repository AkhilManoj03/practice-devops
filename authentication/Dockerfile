# Build stage
FROM rust:1.87.0-alpine3.22 AS builder

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
FROM alpine:3.22.0

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
EXPOSE 8080

# Set environment variables
ENV RUST_LOG=info
ENV PORT=8080

# Run the application with explicit path
CMD ["/app/authentication-service"]
