use crate::{
    errors::AppError,
    models::RegisterRequest,
    state::AppState,
};
use axum::{extract::State, response::Json};
use bcrypt::{hash_with_result, Version, DEFAULT_COST};
use sqlx::Row;
use tracing::info;

// constant for the user role
const USER_ROLE: &str = "user";

pub async fn register(
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
    .bind(USER_ROLE)
    .fetch_one(pool)
    .await?;

    let user_id: i32 = result.get("id");

    Ok(Json(serde_json::json!({
        "message": "User registered successfully",
        "user_id": user_id,
        "username": payload.username
    })))
}
