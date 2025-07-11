# Build arguments for version control
ARG OTEL_VERSION=0.96.0

FROM otel/opentelemetry-collector:${OTEL_VERSION}

COPY otel-collector-config.yaml /etc/otel-collector-config.yaml

CMD ["--config=/etc/otel-collector-config.yaml"]
