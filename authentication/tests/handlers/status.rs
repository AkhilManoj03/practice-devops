use authentication_service::handlers::status::auth_status;
use axum::response::Json;
use serde_json::Value;

#[tokio::test]
async fn test_auth_status_response_structure() {
    let Json(response): Json<Value> = auth_status().await;
    assert!(response.is_object(), "Response should be a JSON object");
    assert!(response.get("authenticated").is_some(), "Should have 'authenticated' field");
    assert!(response.get("message").is_some(), "Should have 'message' field");
}

#[tokio::test]
async fn test_auth_status_authenticated_field() {
    let Json(response): Json<Value> = auth_status().await;
    assert_eq!(response["authenticated"], false, "'authenticated' should be false");
}

#[tokio::test]
async fn test_auth_status_message_content() {
    let Json(response): Json<Value> = auth_status().await;
    let message = response["message"].as_str().unwrap_or("");
    assert!(message.contains("Authentication service is ready"), "Message should indicate service readiness");
}

#[tokio::test]
async fn test_auth_status_json_serialization() {
    let Json(response): Json<Value> = auth_status().await;
    let json_str = serde_json::to_string(&response).expect("Should serialize to JSON");
    let parsed: Value = serde_json::from_str(&json_str).expect("Should parse serialized JSON");
    assert_eq!(parsed, response, "Deserialized JSON should match original");
}

#[tokio::test]
async fn test_auth_status_performance() {
    let start = std::time::Instant::now();
    for _ in 0..20 {
        let Json(response): Json<Value> = auth_status().await;
        assert!(response.get("authenticated").is_some());
    }
    let duration = start.elapsed();
    assert!(duration.as_millis() < 500, "20 status calls should complete in under 500ms");
}
