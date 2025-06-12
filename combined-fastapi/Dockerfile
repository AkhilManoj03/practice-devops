FROM --platform=linux/amd64 python:3.13-alpine

# Set common environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Create non-root user
RUN addgroup -S -g 1001 appuser && \
    adduser -S -G appuser -u 1001 -h /home/appuser appuser

# Install system dependencies and build tools
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    postgresql-dev

# Switch to non-root user
USER appuser

# Copy requirements file for dependency installation
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser app app/

EXPOSE 8000

# Set OpenTelemetry environment variables with defaults
ENV OTEL_SERVICE_NAME=products-api
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
ENV OTEL_TRACES_SAMPLER=always_on

# Add local bin to PATH for pip-installed executables
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV PYTHONPATH="/app"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
