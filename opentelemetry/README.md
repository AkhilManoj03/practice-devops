# 🔭 OpenTelemetry Collector

This directory contains the OpenTelemetry (OTEL) Collector configuration for the microservices
architecture. The collector acts as a centralized telemetry data processing hub, receiving traces
from all services and forwarding them to Jaeger for visualization and analysis.

## 🎯 Purpose

The OpenTelemetry Collector serves as the observability backbone of the system by:

- **Collecting** distributed traces from all microservices (Frontend, Authentication, Product,
Recommendation)
- **Processing** trace data with batching and attribute enrichment
- **Exporting** processed traces to Jaeger for visualization and analysis

## 🏗️ Architecture Role

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│  Frontend   │    │    Auth     │    │   Product   │    │Recommendation│
│   Service   │    │   Service   │    │   Service   │    │    Service   │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬───────┘
       │                  │                  │                  │
       │ OTLP Traces      │ OTLP Traces      │ OTLP Traces      │ OTLP Traces
       │ (HTTP/gRPC)      │ (HTTP/gRPC)      │ (HTTP/gRPC)      │ (HTTP/gRPC)
       │                  │                  │                  │
       └──────────────────┼──────────────────┼──────────────────┘
                          │                  │
                          ▼                  ▼
                    ┌─────────────────────────────┐
                    │   OpenTelemetry Collector   │
                    │                             │
                    │ • Receives OTLP data        │
                    │ • Batches traces            │
                    │ • Enriches attributes       │
                    │ • Exports to Jaeger         │
                    └─────────────┬───────────────┘
                                  │
                                  │ OTLP Export
                                  ▼
                            ┌─────────────┐
                            │   Jaeger    │
                            │ (Tracing UI)│
                            └─────────────┘
```

## ⚙️ Configuration

### Receivers
The collector accepts telemetry data via the **OTLP (OpenTelemetry Protocol)** receivers:

- **HTTP Endpoint**: `http://0.0.0.0:4318` - For HTTP-based trace ingestion
- **gRPC Endpoint**: `grpc://0.0.0.0:4317` - For gRPC-based trace ingestion

### Processors
Applied to all incoming trace data:

1. **Batch Processor**: Groups traces into batches with a 1-second timeout for efficient processing
2. **Attributes Processor**: Enriches traces by ensuring proper service name attribution

### Exporters
Processed traces are exported to:

- **Jaeger**: Via OTLP protocol on `jaeger:4317` (insecure connection for local development)

## 🐳 Docker Configuration

The collector runs in a containerized environment using:

- **Base Image**: `otel/opentelemetry-collector:0.96.0`
- **Configuration**: Mounted from `otel-collector-config.yaml`
- **Network**: Connects to the same Docker network as other services

## 📊 Key Benefits

### 1. **Centralized Telemetry Processing**
All services send their traces to a single collector, simplifying the observability pipeline.

### 2. **Vendor-Neutral Approach**
Uses OpenTelemetry standards, making it easy to switch between different observability backends.

### 3. **Performance Optimization**
Batching and processing reduce the overhead on individual services while ensuring efficient data
export.

### 4. **Service Decoupling**
Services only need to know about the collector endpoint, not the final destination (Jaeger),
improving flexibility.

## 🔄 Data Flow

1. **Generation**: Each microservice generates traces using OpenTelemetry SDKs
2. **Collection**: Services export traces to the collector via OTLP (HTTP/gRPC)
3. **Processing**: Collector batches traces and enriches them with metadata
4. **Export**: Processed traces are sent to Jaeger for storage and visualization
5. **Visualization**: Developers can view end-to-end traces in Jaeger's web UI

## 🚀 Getting Started

The collector automatically starts when running the entire system via Docker Compose:

```bash
# Start the entire system (includes OTEL Collector)
docker-compose up --build

# Access Jaeger UI to view traces
open http://localhost:16686
```

## 🛠️ Customization

To modify the collector configuration:

1. Edit `otel-collector-config.yaml`
2. Add new receivers, processors, or exporters as needed
3. Rebuild the collector container: `docker-compose up --build otel-collector`

## 📋 Supported Protocols

- **OTLP/HTTP**: Port 4318
- **OTLP/gRPC**: Port 4317

All microservices in this architecture use these standard protocols to ensure compatibility and
interoperability.

## 🔍 Monitoring the Collector

The collector itself can be monitored through:
- **Docker logs**: `docker-compose logs otel-collector`
- **Health checks**: Built into the Docker Compose configuration
- **Jaeger UI**: Check if traces are being received and processed

---

This OpenTelemetry Collector setup provides a robust, scalable foundation for distributed tracing
across the entire microservices architecture, enabling comprehensive observability and performance
monitoring.
