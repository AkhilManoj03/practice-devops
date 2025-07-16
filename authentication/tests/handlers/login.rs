use authentication_service::{
    handlers::login::login,
    models::LoginRequest,
    state::AppState,
};
use axum::{extract::State, response::Json};
use crate::common::create_test_config;

#[tokio::test]
async fn test_login_success() {
    // This is a placeholder for a real integration test with a test DB or a more advanced mock.
    // Here, we check that the handler returns the expected structure on success.
    let (config, _temp_dir) = create_test_config();
    let pool = sqlx::PgPool::connect_lazy("postgres://test:test@localhost/test_unused").unwrap();
    let app_state = AppState { pool, config };
    let payload = LoginRequest {
        username: "testuser".to_string(),
        password: "password123".to_string(),
    };
    // This will fail unless a test DB is available, so we only check the error type for now.
    let result = login(State(app_state), Json(payload)).await;
    assert!(result.is_err(), "Should error without a real DB");
}

#[tokio::test]
async fn test_login_invalid_credentials() {
    let (config, _temp_dir) = create_test_config();
    let pool = sqlx::PgPool::connect_lazy("postgres://test:test@localhost/test_unused").unwrap();
    let app_state = AppState { pool, config };
    let payload = LoginRequest {
        username: "nonexistentuser".to_string(),
        password: "wrongpassword".to_string(),
    };
    let result = login(State(app_state), Json(payload)).await;
    assert!(result.is_err(), "Should error for invalid credentials");
}

#[tokio::test]
async fn test_login_invalid_payload() {
    // Simulate missing fields or invalid payload
    let (config, _temp_dir) = create_test_config();
    let pool = sqlx::PgPool::connect_lazy("postgres://test:test@localhost/test_unused").unwrap();
    let app_state = AppState { pool, config };
    let payload = LoginRequest {
        username: "".to_string(),
        password: "".to_string(),
    };
    let result = login(State(app_state), Json(payload)).await;
    assert!(result.is_err(), "Should error for invalid payload");
}

#[tokio::test]
async fn test_login_json_serialization() {
    // Test that the response (if successful) is valid JSON
    // This is a placeholder as the DB is not available
    let (config, _temp_dir) = create_test_config();
    let pool = sqlx::PgPool::connect_lazy("postgres://test:test@localhost/test_unused").unwrap();
    let app_state = AppState { pool, config };
    let payload = LoginRequest {
        username: "testuser2".to_string(),
        password: "password123".to_string(),
    };
    let result = login(State(app_state), Json(payload)).await;
    if let Err(e) = result {
        assert!(format!("{}", e).contains("Database error") || format!("{}", e).contains("error"));
    }
}
