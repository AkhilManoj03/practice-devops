use axum::{
    extract::State,
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use bcrypt::{hash_with_result, verify, Version, DEFAULT_COST};
use chrono::{Duration, Utc};
use dotenv::dotenv;
use jsonwebtoken::{encode, EncodingKey, Header, Algorithm};
use serde::{Deserialize, Serialize};
use sqlx::postgres::{PgPool, PgRow};
use sqlx::Row;
use std::fs;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;
use tracing::{error, info};
use rsa::{RsaPublicKey, pkcs1::DecodeRsaPublicKey, pkcs8::DecodePublicKey};
use opentelemetry::global;
use opentelemetry::KeyValue;
use opentelemetry::trace::TracerProvider;
use opentelemetry_otlp::{SpanExporter, WithExportConfig, Protocol};
use opentelemetry_sdk::trace::SdkTracerProvider;
use opentelemetry_sdk::Resource;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter, Layer};
use axum::response::{IntoResponse, Response};
use axum::Json as AxumJson;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AppError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    #[error("Key loading error: {0}")]
    KeyLoading(String),
    #[error("JWT error: {0}")]
    Jwt(#[from] jsonwebtoken::errors::Error),
    #[error("Password verification error: {0}")]
    PasswordVerification(String),
    #[error("Password hashing error: {0}")]
    PasswordHashing(String),
    #[error("Username or email already exists")]
    Conflict,
    #[error("Invalid credentials")]
    Unauthorized,
    #[error("Other error: {0}")]
    Other(String),
    #[error("Bcrypt error: {0}")]
    Bcrypt(#[from] bcrypt::BcryptError),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match &self {
            AppError::Database(_) => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
            AppError::KeyLoading(_) => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
            AppError::Jwt(_) => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
            AppError::PasswordVerification(_) => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
            AppError::PasswordHashing(_) => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
            AppError::Conflict => (StatusCode::CONFLICT, self.to_string()),
            AppError::Unauthorized => (StatusCode::UNAUTHORIZED, self.to_string()),
            AppError::Other(_) => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
            AppError::Bcrypt(_) => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
        };
        let body = serde_json::json!({ "error": message });
        (status, AxumJson(body)).into_response()
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String,
    role: String,
    exp: usize,
    iat: usize,
}

#[derive(Debug, Serialize)]
struct TokenResponse {
    access_token: String,
    token_type: String,
    expires_in: i64,
}

#[derive(Debug, Deserialize)]
struct LoginRequest {
    username: String,
    password: String,
}

#[derive(Debug, Deserialize)]
struct RegisterRequest {
    username: String,
    email: String,
    password: String,
}

#[derive(Debug, Serialize)]
struct User {
    id: i32,
    username: String,
    email: String,
    password_hash: String,
    role: String,
}

#[derive(Serialize)]
struct JwksResponse {
    keys: Vec<JwkKey>,
}

#[derive(Serialize)]
struct JwkKey {
    kty: String,
    #[serde(rename = "use")]
    key_use: String,
    kid: String,
    alg: String,
    n: String,  // RSA modulus
    e: String,  // RSA exponent
}

#[derive(Serialize)]
struct OpenIdConfiguration {
    issuer: String,
    jwks_uri: String,
    authorization_endpoint: String,
    token_endpoint: String,
    userinfo_endpoint: String,
    response_types_supported: Vec<String>,
    subject_types_supported: Vec<String>,
    id_token_signing_alg_values_supported: Vec<String>,
}

#[derive(Clone)]
pub struct AppState {
    pub pool: PgPool,
    pub config: Config,
}

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
}

impl Config {
    pub fn from_env() -> Self {
        Self {
            rsa_private_key_path: std::env::var("RSA_PRIVATE_KEY_PATH").unwrap_or_else(|_| "keys/private_key.pem".to_string()),
            rsa_public_key_path: std::env::var("RSA_PUBLIC_KEY_PATH").unwrap_or_else(|_| "keys/public_key.pem".to_string()),
            product_key_id: std::env::var("PRODUCT_KEY_ID").unwrap_or_else(|_| "product-service-key-1".to_string()),
            base_url: std::env::var("BASE_URL").unwrap_or_else(|_| "http://authentication:8082".to_string()),
            postgres_user: std::env::var("POSTGRES_USER").unwrap_or_else(|_| "devops".to_string()),
            postgres_password: std::env::var("POSTGRES_PASSWORD").unwrap_or_else(|_| "catalogue".to_string()),
            postgres_host: std::env::var("POSTGRES_HOST").unwrap_or_else(|_| "products-db".to_string()),
            postgres_port: std::env::var("POSTGRES_PORT").unwrap_or_else(|_| "5432".to_string()),
            postgres_db: std::env::var("POSTGRES_DB").unwrap_or_else(|_| "products-db".to_string()),
            otel_service_name: std::env::var("OTEL_SERVICE_NAME").unwrap_or_else(|_| "craftista-authentication".to_string()),
            app_version: std::env::var("APP_VERSION").unwrap_or_else(|_| "1.0.0".to_string()),
            deployment_environment: std::env::var("DEPLOYMENT_ENVIRONMENT").unwrap_or_else(|_| "production".to_string()),
            otel_exporter_otlp_endpoint: std::env::var("OTEL_EXPORTER_OTLP_ENDPOINT").unwrap_or_else(|_| "http://otel-collector:4318".to_string()),
            port: std::env::var("PORT").unwrap_or_else(|_| "8082".to_string()),
        }
    }
}

// Helper function to load RSA private key
fn load_private_key(config: &Config) -> Result<EncodingKey, AppError> {
    let private_key_path = &config.rsa_private_key_path;
    info!("Loading private key from: {}", private_key_path);
    let private_key_pem = fs::read_to_string(private_key_path)
        .map_err(|e| AppError::KeyLoading(format!("Failed to read private key from {}: {}", private_key_path, e)))?;
    EncodingKey::from_rsa_pem(private_key_pem.as_bytes())
        .map_err(|e| AppError::KeyLoading(format!("Failed to parse RSA private key: {}", e)))
}

// Helper function to load RSA public key for JWKS
fn load_public_key_for_jwks(config: &Config) -> Result<RsaPublicKey, AppError> {
    let public_key_path = &config.rsa_public_key_path;
    info!("Loading public key from: {}", public_key_path);
    let public_key_pem = fs::read_to_string(public_key_path)
        .map_err(|e| AppError::KeyLoading(format!("Failed to read public key from {}: {}", public_key_path, e)))?;
    // Try PKCS#8 format first (default OpenSSL output), then PKCS#1 as fallback
    RsaPublicKey::from_public_key_pem(&public_key_pem)
        .or_else(|_| RsaPublicKey::from_pkcs1_pem(&public_key_pem))
        .map_err(|e| AppError::KeyLoading(format!("Failed to parse RSA public key: {}", e)))
}

// Login endpoint that generates JWT token
async fn login(
    State(state): State<AppState>,
    Json(payload): Json<LoginRequest>,
) -> Result<Json<TokenResponse>, AppError> {
    let pool = &state.pool;
    let config = &state.config;
    info!("Login attempt for user: {}", payload.username);

    // Query the database for the user
    let user = sqlx::query("SELECT id, username, email, password_hash, role FROM users WHERE username = $1")
        .bind(&payload.username)
        .map(|row: PgRow| {
            let stored_hash: String = row.get("password_hash");
            info!("Retrieved hash from database: {}", stored_hash);
            User {
                id: row.get("id"),
                username: row.get("username"),
                email: row.get("email"),
                password_hash: stored_hash,
                role: row.get("role"),
            }
        })
        .fetch_optional(pool)
        .await?;

    // Check if user exists and verify password
    let user = match user {
        Some(user) => {
            info!("User found, attempting to verify password");
            info!("Stored hash: {}", user.password_hash);
            info!("Hash version: {}", &user.password_hash[..4]);
            info!("Attempting to verify password: {}", payload.password);
            
            // Offload password verification to blocking thread pool
            let password = payload.password.clone();
            let stored_hash = user.password_hash.clone();
            
            let password_matches = tokio::task::spawn_blocking(move || {
                verify(&password, &stored_hash)
            })
            .await
            .map_err(|e| AppError::PasswordVerification(format!("Task join error: {}", e)))??;

            if password_matches {
                info!("Password verified successfully");
                user
            } else {
                info!("Password verification failed - hash mismatch");
                return Err(AppError::Unauthorized);
            }
        }
        None => {
            info!("User not found: {}", payload.username);
            return Err(AppError::Unauthorized)
        },
    };

    // Set token expiration time (e.g., 1 hour from now)
    let expiration = Utc::now()
        .checked_add_signed(Duration::hours(1))
        .expect("valid timestamp")
        .timestamp() as usize;
    
    let issued_at = Utc::now().timestamp() as usize;

    // Create the JWT claims
    let claims = Claims {
        sub: user.username,
        role: user.role,
        exp: expiration,
        iat: issued_at,
    };

    // Load RSA private key and create token with RS256
    let encoding_key = load_private_key(config)?;

    let mut header = Header::new(Algorithm::RS256);
    header.kid = Some(config.product_key_id.clone());

    // Create the token using RSA private key
    let token = encode(&header, &claims, &encoding_key)?;

    // Return the token
    Ok(Json(TokenResponse {
        access_token: token,
        token_type: "Bearer".to_string(),
        expires_in: (expiration - issued_at) as i64,
    }))
}

// Placeholder for future authentication endpoints
async fn auth_status() -> Json<serde_json::Value> {
    info!("Authentication status endpoint called");
    Json(serde_json::json!({
        "authenticated": false,
        "message": "Authentication service is ready for implementation"
    }))
}

async fn register(
    State(state): State<AppState>,
    Json(payload): Json<RegisterRequest>,
) -> Result<Json<serde_json::Value>, AppError> {
    let pool = &state.pool;
    let _config = &state.config;
    info!("Register endpoint called");
    // Check if username or email already exists
    let existing_user = sqlx::query("SELECT username, email FROM users WHERE username = $1 OR email = $2")
        .bind(&payload.username)
        .bind(&payload.email)
        .fetch_optional(pool)
        .await?;

    if existing_user.is_some() {
        return Err(AppError::Conflict);
    }

    // Offload password hashing to blocking thread pool
    let password = payload.password.clone();
    let password_hash = tokio::task::spawn_blocking(move || {
        hash_with_result(&password, DEFAULT_COST)
            .map(|hash_result| hash_result.format_for_version(Version::TwoA))
    })
    .await
    .map_err(|e| AppError::PasswordHashing(format!("Task join error: {}", e)))??;

    // Insert the new user
    let result = sqlx::query(
        "INSERT INTO users (username, email, password_hash, role) VALUES ($1, $2, $3, $4) RETURNING id"
    )
    .bind(&payload.username)
    .bind(&payload.email)
    .bind(&password_hash)
    .bind("user") // Default role for new registrations
    .fetch_one(pool)
    .await?;

    let user_id: i32 = result.get("id");

    Ok(Json(serde_json::json!({
        "message": "User registered successfully",
        "user_id": user_id,
        "username": payload.username
    })))
}

// JWKS endpoint for public key distribution
async fn jwks(
    State(state): State<AppState>,
) -> Result<Json<JwksResponse>, AppError> {
    let config = &state.config;
    info!("JWKS endpoint called");
    use base64::{Engine as _, engine::general_purpose};
    use rsa::traits::PublicKeyParts;
    
    // Get key ID from config
    let key_id = config.product_key_id.clone();
    
    // Load RSA public key
    let public_key = load_public_key_for_jwks(config)?;
    
    // Extract modulus and exponent
    let modulus = public_key.n();
    let exponent = public_key.e();
    
    // Convert to base64url encoding (without padding) as required by RFC 7517
    let modulus_bytes = modulus.to_bytes_be();
    let exponent_bytes = exponent.to_bytes_be();
    
    let modulus_b64 = general_purpose::URL_SAFE_NO_PAD.encode(&modulus_bytes);
    let exponent_b64 = general_purpose::URL_SAFE_NO_PAD.encode(&exponent_bytes);
    
    Ok(Json(JwksResponse {
        keys: vec![JwkKey {
            kty: "RSA".to_string(),
            key_use: "sig".to_string(),
            kid: key_id,
            alg: "RS256".to_string(),
            n: modulus_b64,
            e: exponent_b64,
        }],
    }))
}

// OpenID Connect Discovery endpoint
async fn openid_configuration(
    State(state): State<AppState>,
) -> Json<OpenIdConfiguration> {
    let config = &state.config;
    info!("OpenID configuration endpoint called");
    let base_url = config.base_url.clone();
    
    Json(OpenIdConfiguration {
        issuer: base_url.clone(),
        jwks_uri: format!("{}/.well-known/jwks.json", base_url),
        authorization_endpoint: format!("{}/api/auth/login", base_url),
        token_endpoint: format!("{}/api/auth/login", base_url),
        userinfo_endpoint: format!("{}/api/auth/status", base_url),
        response_types_supported: vec!["code".to_string(), "token".to_string()],
        subject_types_supported: vec!["public".to_string()],
        id_token_signing_alg_values_supported: vec!["RS256".to_string()],
    })
}

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

#[tokio::main]
async fn main() {
    // Load environment variables
    dotenv().ok();

    // Load config
    let config = Config::from_env();

    // Initialize tracing
    let tracer_provider = init_tracer(&config);
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

    // Set up database connection from config
    let database_url = format!(
        "postgres://{}:{}@{}:{}/{}",
        config.postgres_user, config.postgres_password, config.postgres_host, config.postgres_port, config.postgres_db
    );

    let pool = PgPool::connect(&database_url)
        .await
        .expect("Failed to connect to Postgres");

    // Build our application with routes
    let app_state = AppState {
        pool,
        config: config.clone(),
    };

    let app = Router::new()
        .route("/api/auth/login", post(login))
        .route("/api/auth/register", post(register))
        .route("/api/auth/status", get(auth_status))
        .route("/.well-known/jwks.json", get(jwks))
        .route("/.well-known/openid-configuration", get(openid_configuration))
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
        .with_state(app_state);

    let addr = format!("0.0.0.0:{}", config.port);
    info!("Authentication service starting on {}", addr);
    
    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    
    // Clone tracer provider for shutdown
    let tracer_provider_for_shutdown = tracer_provider.clone();
    
    // Set up graceful shutdown
    let shutdown_signal = async move {
        tokio::signal::ctrl_c()
            .await
            .expect("failed to install CTRL+C signal handler");
        info!("Received shutdown signal, cleaning up...");
        
        // Shutdown tracer provider to ensure all spans are exported
        if let Err(e) = tracer_provider_for_shutdown.shutdown() {
            error!("Failed to shutdown tracer provider: {}", e);
        }
    };
    
    // Run the server with graceful shutdown
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal)
        .await
        .unwrap();
}
