use authentication_service::{config::Config, state::AppState};
use sqlx::{postgres::PgPoolOptions};
use tempfile::TempDir;
use std::fs;
use rsa::{RsaPrivateKey, RsaPublicKey, pkcs1::EncodeRsaPrivateKey, pkcs8::EncodePublicKey};

/// Create a test configuration with temporary key files
pub fn create_test_config() -> (Config, TempDir) {
    let temp_dir = TempDir::new().expect("Failed to create temp directory");
    
    // Generate test RSA key pair
    let private_key = RsaPrivateKey::new(&mut rand::thread_rng(), 2048)
        .expect("Failed to generate private key");
    let public_key = RsaPublicKey::from(&private_key);
    
    // Write private key
    let private_key_path = temp_dir.path().join("private_key.pem");
    let private_key_pem = private_key.to_pkcs1_pem(rsa::pkcs1::LineEnding::LF)
        .expect("Failed to encode private key");
    fs::write(&private_key_path, private_key_pem).expect("Failed to write private key");
    
    // Write public key
    let public_key_path = temp_dir.path().join("public_key.pem");
    let public_key_pem = public_key.to_public_key_pem(rsa::pkcs8::LineEnding::LF)
        .expect("Failed to encode public key");
    fs::write(&public_key_path, public_key_pem).expect("Failed to write public key");
    
    let config = Config {
        rsa_private_key_path: private_key_path.to_string_lossy().to_string(),
        rsa_public_key_path: public_key_path.to_string_lossy().to_string(),
        product_key_id: "test-key-id".to_string(),
        base_url: "http://localhost:8082".to_string(),
        postgres_user: "test_user".to_string(),
        postgres_password: "test_password".to_string(),
        postgres_host: "localhost".to_string(),
        postgres_port: "5432".to_string(),
        postgres_db: "test_db".to_string(),
        otel_service_name: "test-service".to_string(),
        app_version: "0.1.0".to_string(),
        deployment_environment: "test".to_string(),
        otel_exporter_otlp_endpoint: "http://localhost:4318".to_string(),
        port: "8082".to_string(),
        internal_api_key: "test-internal-key".to_string(),
    };
    
    (config, temp_dir)
}

/// Create a simplified config and state for unit tests that don't need a database
pub fn create_unit_test_state() -> (AppState, TempDir) {
    let (config, temp_dir) = create_test_config();
    
    // For unit tests, we create a minimal pool that won't be used
    // We'll use dependency injection to avoid actual database calls
    let database_url = "postgres://test:test@localhost/test_unused";
    let pool = PgPoolOptions::new()
        .max_connections(1)
        .connect_lazy(&database_url)
        .expect("Failed to create lazy pool");
    
    let app_state = AppState { pool, config };
    (app_state, temp_dir)
}
