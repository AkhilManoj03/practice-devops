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
use std::{env, fs};
use tower_http::cors::CorsLayer;
use tracing::{error, info, Level};
use rsa::{RsaPublicKey, pkcs1::DecodeRsaPublicKey, pkcs8::DecodePublicKey};


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

// Helper function to load RSA private key
fn load_private_key() -> Result<EncodingKey, Box<dyn std::error::Error>> {
    let private_key_path = env::var("RSA_PRIVATE_KEY_PATH")
        .unwrap_or_else(|_| "keys/private_key.pem".to_string());
    
    let private_key_pem = fs::read_to_string(&private_key_path)
        .map_err(|e| format!("Failed to read private key from {}: {}", private_key_path, e))?;
    
    EncodingKey::from_rsa_pem(private_key_pem.as_bytes())
        .map_err(|e| format!("Failed to parse RSA private key: {}", e).into())
}

// Helper function to load RSA public key for JWKS
fn load_public_key_for_jwks() -> Result<RsaPublicKey, Box<dyn std::error::Error>> {
    let public_key_path = env::var("RSA_PUBLIC_KEY_PATH")
        .unwrap_or_else(|_| "keys/public_key.pem".to_string());
    
    let public_key_pem = fs::read_to_string(&public_key_path)
        .map_err(|e| format!("Failed to read public key from {}: {}", public_key_path, e))?;
    
    // Try PKCS#8 format first (default OpenSSL output), then PKCS#1 as fallback
    RsaPublicKey::from_public_key_pem(&public_key_pem)
        .or_else(|_| RsaPublicKey::from_pkcs1_pem(&public_key_pem))
        .map_err(|e| format!("Failed to parse RSA public key: {}", e).into())
}

// Login endpoint that generates JWT token
async fn login(
    State(pool): State<PgPool>,
    Json(payload): Json<LoginRequest>,
) -> Result<Json<TokenResponse>, (StatusCode, String)> {
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
        .fetch_optional(&pool)
        .await
        .map_err(|e| {
            error!("Database error: {}", e);
            (StatusCode::INTERNAL_SERVER_ERROR, "Database error".to_string())
        })?;

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
            .map_err(|e| {
                error!("Task join error: {}", e);
                (StatusCode::INTERNAL_SERVER_ERROR, "Internal server error".to_string())
            })?
            .map_err(|e| {
                error!("Password verification error: {:?}", e);
                error!("Hash format: {}", &user.password_hash[..4]);
                (StatusCode::INTERNAL_SERVER_ERROR, format!("Password verification error: {:?}", e))
            })?;

            if password_matches {
                info!("Password verified successfully");
                user
            } else {
                info!("Password verification failed - hash mismatch");
                return Err((StatusCode::UNAUTHORIZED, "Invalid credentials".to_string()));
            }
        }
        None => {
            info!("User not found: {}", payload.username);
            return Err((StatusCode::UNAUTHORIZED, "Invalid credentials".to_string()))
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
    let encoding_key = load_private_key()
        .map_err(|e| {
            error!("Failed to load private key: {}", e);
            (StatusCode::INTERNAL_SERVER_ERROR, "Key loading error".to_string())
        })?;

    let mut header = Header::new(Algorithm::RS256);
    header.kid = Some(env::var("PRODUCT_KEY_ID").unwrap_or_else(|_| "product-service-key-1".to_string()));

    // Create the token using RSA private key
    let token = encode(&header, &claims, &encoding_key)
        .map_err(|e| {
            error!("Failed to create token: {}", e);
            (StatusCode::INTERNAL_SERVER_ERROR, "Failed to create token".to_string())
        })?;

    // Return the token
    Ok(Json(TokenResponse {
        access_token: token,
        token_type: "Bearer".to_string(),
        expires_in: (expiration - issued_at) as i64,
    }))
}

// Placeholder for future authentication endpoints
async fn auth_status() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "authenticated": false,
        "message": "Authentication service is ready for implementation"
    }))
}

async fn register(
    State(pool): State<PgPool>,
    Json(payload): Json<RegisterRequest>,
) -> Result<Json<serde_json::Value>, (StatusCode, String)> {
    // Check if username or email already exists
    let existing_user = sqlx::query("SELECT username, email FROM users WHERE username = $1 OR email = $2")
        .bind(&payload.username)
        .bind(&payload.email)
        .fetch_optional(&pool)
        .await
        .map_err(|e| {
            error!("Database error checking existing user/email: {}", e);
            (StatusCode::INTERNAL_SERVER_ERROR, "Database error".to_string())
        })?;

    if existing_user.is_some() {
        return Err((
            StatusCode::CONFLICT,
            "Username already exists".to_string(),
        ));
    }

    // Offload password hashing to blocking thread pool
    let password = payload.password.clone();
    let password_hash = tokio::task::spawn_blocking(move || {
        hash_with_result(&password, DEFAULT_COST)
            .map(|hash_result| hash_result.format_for_version(Version::TwoA))
    })
    .await
    .map_err(|e| {
        error!("Task join error: {}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, "Internal server error".to_string())
    })?
    .map_err(|e| {
        error!("Password hashing error: {}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, "Password hashing failed".to_string())
    })?;

    // Insert the new user
    let result = sqlx::query(
        "INSERT INTO users (username, email, password_hash, role) VALUES ($1, $2, $3, $4) RETURNING id"
    )
    .bind(&payload.username)
    .bind(&payload.email)
    .bind(&password_hash)
    .bind("user") // Default role for new registrations
    .fetch_one(&pool)
    .await
    .map_err(|e| {
        error!("Database error creating user: {}", e);
        (StatusCode::INTERNAL_SERVER_ERROR, "Failed to create user".to_string())
    })?;

    let user_id: i32 = result.get("id");

    Ok(Json(serde_json::json!({
        "message": "User registered successfully",
        "user_id": user_id,
        "username": payload.username
    })))
}

// JWKS endpoint for public key distribution
async fn jwks() -> Result<Json<JwksResponse>, (StatusCode, String)> {
    use base64::{Engine as _, engine::general_purpose};
    use rsa::traits::PublicKeyParts;
    
    // Get key ID from environment
    let key_id = env::var("PRODUCT_KEY_ID")
        .unwrap_or_else(|_| "product-service-key-1".to_string());
    
    // Load RSA public key
    let public_key = load_public_key_for_jwks()
        .map_err(|e| {
            error!("Failed to load public key for JWKS: {}", e);
            (StatusCode::INTERNAL_SERVER_ERROR, "Failed to load public key".to_string())
        })?;
    
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
async fn openid_configuration() -> Json<OpenIdConfiguration> {
    let base_url = env::var("BASE_URL").unwrap_or_else(|_| "http://authentication:8080".to_string());
    
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

#[tokio::main]
async fn main() {
    // Load environment variables
    dotenv().ok();

    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(Level::INFO)
        .with_target(false)
        .init();

    // Set up database connection from individual environment variables
    let postgres_user = env::var("POSTGRES_USER").unwrap_or_else(|_| "devops".to_string());
    let postgres_password = env::var("POSTGRES_PASSWORD").unwrap_or_else(|_| "catalogue".to_string());
    let postgres_host = env::var("POSTGRES_HOST").unwrap_or_else(|_| "products-db".to_string());
    let postgres_port = env::var("POSTGRES_PORT").unwrap_or_else(|_| "5432".to_string());
    let postgres_db = env::var("POSTGRES_DB").unwrap_or_else(|_| "products-db".to_string());
    
    let database_url = format!(
        "postgres://{}:{}@{}:{}/{}",
        postgres_user, postgres_password, postgres_host, postgres_port, postgres_db
    );

    let pool = PgPool::connect(&database_url)
        .await
        .expect("Failed to connect to Postgres");

    // Build our application with routes
    let app = Router::new()
        .route("/api/auth/login", post(login))
        .route("/api/auth/register", post(register))
        .route("/api/auth/status", get(auth_status))
        .route("/.well-known/jwks.json", get(jwks))
        .route("/.well-known/openid-configuration", get(openid_configuration))
        .layer(CorsLayer::permissive())
        .with_state(pool);

    let port = env::var("PORT").unwrap_or_else(|_| "8080".to_string());
    let addr = format!("0.0.0.0:{}", port);
    
    info!("Authentication service starting on {}", addr);
    
    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
