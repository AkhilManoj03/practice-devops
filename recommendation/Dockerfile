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

# Download dependencies
RUN go mod download

# Copy the rest of the application
COPY --chown=appuser:appuser . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -o app

# Switch to non-root user
USER appuser

EXPOSE 8080

CMD ["./app"]
