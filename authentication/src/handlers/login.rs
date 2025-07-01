use crate::{
    errors::AppError,
    models::{Claims, LoginRequest, TokenResponse, User},
    state::AppState,
    config::Config,
};
use axum::{extract::State, response::Json};
use bcrypt::verify;
use chrono::{Duration, Utc};
use jsonwebtoken::{encode, Algorithm, Header};
use sqlx::{postgres::PgRow, Row};
use std::fs;
use jsonwebtoken::EncodingKey;
use tracing::info;


// Helper function to load RSA private key
fn load_private_key(config: &Config) -> Result<EncodingKey, AppError> {
    let private_key_path = &config.rsa_private_key_path;
    info!("Loading private key from: {}", private_key_path);
    let private_key_pem = fs::read_to_string(private_key_path)
        .map_err(|e| AppError::KeyLoading(format!("Failed to read private key from {}: {}", private_key_path, e)))?;
    EncodingKey::from_rsa_pem(private_key_pem.as_bytes())
        .map_err(|e| AppError::KeyLoading(format!("Failed to parse RSA private key: {}", e)))
}

// Login endpoint that generates JWT token
pub async fn login(
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

    // Set token expiration time
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
