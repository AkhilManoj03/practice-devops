use crate::config::Config;
use opentelemetry::{global, trace::TracerProvider, KeyValue};
use opentelemetry_otlp::{Protocol, SpanExporter, WithExportConfig};
use opentelemetry_sdk::{trace::SdkTracerProvider, Resource};
use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter, Layer};

// Create resource with service information
fn get_resource(config: &Config) -> Resource {
    Resource::builder()
        .with_service_name(config.otel_service_name.clone())
        .with_attributes(vec![
            KeyValue::new("service.version", config.app_version.clone()),
            KeyValue::new("deployment.environment", config.deployment_environment.clone()),
        ])
        .build()
}

// Initialize OpenTelemetry tracer
fn init_tracer(config: &Config) -> SdkTracerProvider {
    info!("Initializing OpenTelemetry tracer with endpoint: {}", config.otel_exporter_otlp_endpoint);
    // Configure OTLP exporter using HTTP
    let exporter = SpanExporter::builder()
        .with_http()
        .with_endpoint(config.otel_exporter_otlp_endpoint.clone())
        .with_protocol(Protocol::HttpBinary)
        .build()
        .expect("Failed to build exporter");
    // Create tracer provider
    SdkTracerProvider::builder()
        .with_resource(get_resource(config))
        .with_batch_exporter(exporter)
        .build()
}

pub fn init_tracing_subscriber(config: &Config) -> SdkTracerProvider {
    let tracer_provider = init_tracer(config);
    global::set_tracer_provider(tracer_provider.clone());
    let tracer = tracer_provider.tracer("craftista-authentication");
    let otel_layer = tracing_opentelemetry::layer().with_tracer(tracer);
    // Create fmt layer to suppress noisy OpenTelemetry debug logs
    let filter_fmt = EnvFilter::new("info")
        .add_directive("opentelemetry=info".parse().unwrap())
        .add_directive("opentelemetry_sdk=warn".parse().unwrap())
        .add_directive("opentelemetry_otlp=warn".parse().unwrap())
        .add_directive("opentelemetry_http=warn".parse().unwrap());
    let fmt_layer = tracing_subscriber::fmt::layer()
        .with_thread_names(true)
        .with_filter(filter_fmt);
    // Initialize tracing subscriber with both layers
    tracing_subscriber::registry()
        .with(otel_layer)
        .with(fmt_layer)
        .init();

    tracer_provider
}
