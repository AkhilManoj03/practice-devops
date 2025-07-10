use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json as AxumJson,
};
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
            AppError::Bcrypt(_) => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
        };
        let body = serde_json::json!({ "error": message });
        (status, AxumJson(body)).into_response()
    }
}
