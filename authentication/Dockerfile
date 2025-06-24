# Build stage
FROM rust:1.87.0-slim-bookworm AS builder

# Set the working directory
WORKDIR /app

# Copy the entire project
COPY . .

# Build for release
RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -g 1001 appuser && \
    useradd -u 1001 -g appuser appuser

# Set the working directory
WORKDIR /app

# Copy the binary from the builder stage
COPY --from=builder /app/target/release/authentication-service /app/authentication-service

# Copy RSA keys
COPY --from=builder /app/keys /app/keys

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
