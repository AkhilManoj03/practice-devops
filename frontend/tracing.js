const opentelemetry = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { BatchSpanProcessor } = require('@opentelemetry/sdk-trace-base');

// Get service name from environment variable
const serviceName = process.env.OTEL_SERVICE_NAME || 'craftista-frontend';

// Export serviceName for use in other files
module.exports = { serviceName };

// Create a resource with enhanced attributes
const resource = new Resource({
  [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
  [SemanticResourceAttributes.SERVICE_VERSION]: process.env.APP_VERSION || '1.0.0',
  [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV || 'production',
});

// Configure the trace exporter
const traceExporter = new OTLPTraceExporter({
  url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4318/v1/traces',
  headers: {}, // Add custom headers if needed
  concurrencyLimit: 10, // limit number of concurrent exports
});

const sdk = new opentelemetry.NodeSDK({
  resource: resource,
  traceExporter,
  spanProcessor: new BatchSpanProcessor(traceExporter, {
    maxQueueSize: 1000,
    scheduledDelayMillis: 1000,
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-express': {
        enabled: true,
        requestHook: (span, info) => {
          span.setAttribute('http.route', info.route?.path);
        },
      },
      '@opentelemetry/instrumentation-http': {
        enabled: true,
      },
      '@opentelemetry/instrumentation-axios': {
        enabled: true,
      },
    }),
  ],
});

// Handle shutdown gracefully
process.on('SIGTERM', () => {
  sdk.shutdown()
    .then(() => console.log('Tracing terminated'))
    .catch((error) => console.log('Error terminating tracing', error))
    .finally(() => process.exit(0));
});

sdk.start();
