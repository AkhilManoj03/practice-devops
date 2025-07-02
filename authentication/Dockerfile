# Build arguments for version control
ARG RUST_VERSION=1.87.0
ARG ALPINE_VERSION=3.22
ARG CARGO_CHEF_VERSION=0.1.71

# Chef stage
FROM lukemathwalker/cargo-chef:${CARGO_CHEF_VERSION}-rust-${RUST_VERSION}-alpine${ALPINE_VERSION} AS chef
WORKDIR /app


# Planner stage
FROM chef AS planner

# Copy only the files needed for planning
COPY Cargo.toml Cargo.lock ./
COPY src/ ./src/

# Generate the recipe file
RUN cargo chef prepare --recipe-path recipe.json


# Builder stage
FROM chef AS builder

# Copy the recipe file from the planner stage
COPY --from=planner /app/recipe.json ./recipe.json

# Cook the dependencies for release
RUN cargo chef cook --recipe-path recipe.json --release

# Copy the rest of the source code
COPY Cargo.toml Cargo.lock ./
COPY src/ ./src/

# Build for release with static linking for Alpine
ENV RUSTFLAGS="-C target-feature=-crt-static"
RUN cargo build --release --bin authentication-service


# Runtime stage
FROM alpine:${ALPINE_VERSION}

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
