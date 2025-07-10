use axum::response::Json;
use tracing::info;

pub async fn auth_status() -> Json<serde_json::Value> {
    info!("Authentication status endpoint called");
    Json(serde_json::json!({
        "authenticated": false,
        "message": "Authentication service is ready for implementation",
    }))
}
