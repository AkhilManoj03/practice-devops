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

# Copy application code
COPY --chown=appuser:appuser . .

EXPOSE 3000

CMD ["node", "app.js"]
