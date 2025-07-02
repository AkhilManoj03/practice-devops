#[derive(Debug, Clone)]
pub struct Config {
    pub rsa_private_key_path: String,
    pub rsa_public_key_path: String,
    pub product_key_id: String,
    pub base_url: String,
    pub postgres_user: String,
    pub postgres_password: String,
    pub postgres_host: String,
    pub postgres_port: String,
    pub postgres_db: String,
    pub otel_service_name: String,
    pub app_version: String,
    pub deployment_environment: String,
    pub otel_exporter_otlp_endpoint: String,
    pub port: String,
    pub internal_api_key: String,
}

impl Config {
    pub fn from_env() -> Self {
        Self {
            rsa_private_key_path: std::env::var("RSA_PRIVATE_KEY_PATH")
                .unwrap_or_else(|_| "keys/private_key.pem".to_string()),
            rsa_public_key_path: std::env::var("RSA_PUBLIC_KEY_PATH")
                .unwrap_or_else(|_| "keys/public_key.pem".to_string()),
            product_key_id: std::env::var("PRODUCT_KEY_ID")
                .unwrap_or_else(|_| "product-service-key-1".to_string()),
            base_url: std::env::var("BASE_URL")
                .unwrap_or_else(|_| "http://authentication:8082".to_string()),
            postgres_user: std::env::var("POSTGRES_USER")
                .unwrap_or_else(|_| "devops".to_string()),
            postgres_password: std::env::var("POSTGRES_PASSWORD")
                .unwrap_or_else(|_| "catalogue".to_string()),
            postgres_host: std::env::var("POSTGRES_HOST")
                .unwrap_or_else(|_| "products-db".to_string()),
            postgres_port: std::env::var("POSTGRES_PORT")
                .unwrap_or_else(|_| "5432".to_string()),
            postgres_db: std::env::var("POSTGRES_DB")
                .unwrap_or_else(|_| "products-db".to_string()),
            otel_service_name: std::env::var("OTEL_SERVICE_NAME")
                .unwrap_or_else(|_| "craftista-authentication".to_string()),
            app_version: std::env::var("APP_VERSION")
                .unwrap_or_else(|_| "1.0.0".to_string()),
            deployment_environment: std::env::var("DEPLOYMENT_ENVIRONMENT")
                .unwrap_or_else(|_| "production".to_string()),
            otel_exporter_otlp_endpoint: std::env::var("OTEL_EXPORTER_OTLP_ENDPOINT")
                .unwrap_or_else(|_| "http://otel-collector:4318/v1/traces".to_string()),
            port: std::env::var("PORT")
                .unwrap_or_else(|_| "8082".to_string()),
            internal_api_key: std::env::var("INTERNAL_API_KEY")
                .unwrap_or_else(|_| "a-super-secret-key".to_string()),
        }
    }
}
