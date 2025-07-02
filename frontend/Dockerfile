# Build arguments for version control
ARG NODE_VERSION=22.16
ARG ALPINE_VERSION=3.22
ARG NPM_VERSION=11.4.2

# Build stage
FROM node:${NODE_VERSION}-alpine${ALPINE_VERSION} AS builder

# Install specific npm version
RUN npm install -g npm@${NPM_VERSION}

WORKDIR /build

# Copy package files
COPY package*.json ./

# Install build dependencies
RUN npm install --no-audit --no-fund && \
    npm cache clean --force

# Copy source code
COPY . .

# Remove dev dependencies and clean up
RUN npm prune --production && \
    npm cache clean --force

# Runtime stage
FROM node:${NODE_VERSION}-alpine${ALPINE_VERSION}

# Create non-root user
RUN addgroup -S -g 1001 appuser && \
    adduser -S -G appuser -u 1001 -h /home/appuser appuser && \
    rm -rf /var/cache/apk/*

WORKDIR /app

# Switch to non-root user
USER appuser

# Copy production dependencies from builder
COPY --from=builder --chown=appuser:appuser /build/node_modules ./node_modules

# Copy application files (unnecessary files excluded by .dockerignore)
COPY --chown=appuser:appuser . .

# Set environment variables
ENV NODE_ENV=production
ENV OTEL_SERVICE_NAME=craftista-frontend
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
ENV OTEL_TRACES_SAMPLER=always_on

EXPOSE 3000

CMD ["npm", "start"]
