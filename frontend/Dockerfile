FROM --platform=linux/amd64 node:22-alpine

WORKDIR /app

# Create non-root user
RUN addgroup -S -g 1001 appuser && \
    adduser -S -G appuser -u 1001 -h /home/appuser appuser

# Install system dependencies and set up npm directory
RUN apk add --no-cache && \
    mkdir -p /home/appuser/.npm-global && \
    chown -R appuser:appuser /home/appuser /app && \
    rm -rf /var/cache/apk/*

# Switch to non-root user
USER appuser

# Copy package files for dependency installation
COPY --chown=appuser:appuser package.json config.json ./

# Install Node.js dependencies
RUN npm install --no-audit --no-fund --prefer-offline && \
    npm cache clean --force

# Copy application files
COPY --chown=appuser:appuser . .

# Set OpenTelemetry environment variables with defaults
ENV NODE_ENV=production
ENV OTEL_SERVICE_NAME=craftista-frontend
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
ENV OTEL_TRACES_SAMPLER=always_on

EXPOSE 3000

CMD ["npm", "start"]
