use authentication_service::{
    handlers::openid::{jwks, openid_configuration},
    models::{JwksResponse, OpenIdConfiguration},
    state::AppState,
};
use axum::{extract::State, response::Json};
use base64::{Engine as _, engine::general_purpose};
use rsa::{RsaPublicKey, pkcs8::DecodePublicKey, traits::PublicKeyParts};
use std::fs;
use crate::common::{create_test_config, create_unit_test_state};

#[tokio::test]
async fn test_jwks_endpoint_success() {
    let (app_state, _temp_dir) = create_unit_test_state();
    
    let result = jwks(State(app_state.clone())).await;
    
    assert!(result.is_ok(), "JWKS endpoint should succeed");
    
    let Json(jwks_response): Json<JwksResponse> = result.unwrap();
    
    assert_eq!(jwks_response.keys.len(), 1, "Should have exactly one key");
    
    let key = &jwks_response.keys[0];
    assert_eq!(key.kty, "RSA", "Key type should be RSA");
    assert_eq!(key.key_use, "sig", "Key use should be 'sig' for signature");
    assert_eq!(key.kid, app_state.config.product_key_id, "Key ID should match config");
    assert_eq!(key.alg, "RS256", "Algorithm should be RS256");
    assert!(!key.n.is_empty(), "Modulus should not be empty");
    assert!(!key.e.is_empty(), "Exponent should not be empty");
}

#[tokio::test]
async fn test_jwks_endpoint_key_components_are_valid() {
    let (app_state, _temp_dir) = create_unit_test_state();
    
    let public_key_pem = fs::read_to_string(&app_state.config.rsa_public_key_path)
        .expect("Should be able to read public key file");
    let public_key = RsaPublicKey::from_public_key_pem(&public_key_pem)
        .expect("Should be able to parse public key");
    
    let result = jwks(State(app_state)).await;
    assert!(result.is_ok());
    
    let Json(jwks_response): Json<JwksResponse> = result.unwrap();
    let key = &jwks_response.keys[0];
    
    let modulus_bytes = general_purpose::URL_SAFE_NO_PAD
        .decode(&key.n)
        .expect("Should be able to decode modulus");
    let exponent_bytes = general_purpose::URL_SAFE_NO_PAD
        .decode(&key.e)
        .expect("Should be able to decode exponent");
    
    let expected_modulus = public_key.n().to_bytes_be();
    let expected_exponent = public_key.e().to_bytes_be();
    
    assert_eq!(modulus_bytes, expected_modulus, "Modulus should match");
    assert_eq!(exponent_bytes, expected_exponent, "Exponent should match");
}

#[tokio::test]
async fn test_jwks_endpoint_with_invalid_key_file() {
    let (mut config, temp_dir) = create_test_config();
    
    config.rsa_public_key_path = temp_dir.path().join("non_existent.pem").to_string_lossy().to_string();
    
    let app_state = AppState {
        pool: sqlx::PgPool::connect_lazy("postgres://test:test@localhost/test_unused").unwrap(),
        config,
    };
    
    let result = jwks(State(app_state)).await;
    
    assert!(result.is_err(), "Should fail when key file doesn't exist");
}

#[tokio::test]
async fn test_jwks_endpoint_with_malformed_key_file() {
    let (mut config, temp_dir) = create_test_config();
    
    let bad_key_path = temp_dir.path().join("bad_key.pem");
    fs::write(&bad_key_path, "This is not a valid PEM key")
        .expect("Should be able to write bad key file");
    
    config.rsa_public_key_path = bad_key_path.to_string_lossy().to_string();
    
    let app_state = AppState {
        pool: sqlx::PgPool::connect_lazy("postgres://test:test@localhost/test_unused").unwrap(),
        config,
    };
    
    let result = jwks(State(app_state)).await;
    
    assert!(result.is_err(), "Should fail when key file is malformed");
}

#[tokio::test]
async fn test_openid_configuration_endpoint() {
    let (app_state, _temp_dir) = create_unit_test_state();
    let base_url = app_state.config.base_url.clone();
    
    let Json(config): Json<OpenIdConfiguration> = openid_configuration(State(app_state)).await;
    
    assert_eq!(config.issuer, base_url, "Issuer should match base URL");
    assert_eq!(config.jwks_uri, format!("{}/.well-known/jwks.json", base_url), "JWKS URI should be correct");
    assert_eq!(config.authorization_endpoint, format!("{}/api/auth/login", base_url), "Authorization endpoint should be correct");
    assert_eq!(config.token_endpoint, format!("{}/api/auth/login", base_url), "Token endpoint should be correct");
    assert_eq!(config.userinfo_endpoint, format!("{}/api/auth/status", base_url), "Userinfo endpoint should be correct");
    
    assert!(config.response_types_supported.contains(&"code".to_string()), "Should support 'code' response type");
    assert!(config.response_types_supported.contains(&"token".to_string()), "Should support 'token' response type");
    assert!(config.subject_types_supported.contains(&"public".to_string()), "Should support 'public' subject type");
    assert!(config.id_token_signing_alg_values_supported.contains(&"RS256".to_string()), "Should support RS256 algorithm");
}

#[tokio::test]
async fn test_openid_configuration_with_custom_base_url() {
    let (mut config, temp_dir) = create_test_config();
    config.base_url = "https://auth.example.com".to_string();
    
    let app_state = AppState {
        pool: sqlx::PgPool::connect_lazy("postgres://test:test@localhost/test_unused").unwrap(),
        config: config.clone(),
    };
    
    let Json(openid_config): Json<OpenIdConfiguration> = openid_configuration(State(app_state)).await;
    
    assert_eq!(openid_config.issuer, "https://auth.example.com");
    assert_eq!(openid_config.jwks_uri, "https://auth.example.com/.well-known/jwks.json");
    assert_eq!(openid_config.authorization_endpoint, "https://auth.example.com/api/auth/login");
    assert_eq!(openid_config.token_endpoint, "https://auth.example.com/api/auth/login");
    assert_eq!(openid_config.userinfo_endpoint, "https://auth.example.com/api/auth/status");
    
    // Keep the temp_dir alive to avoid warnings
    drop(temp_dir);
}

#[tokio::test]
async fn test_jwks_response_serialization() {
    let (app_state, _temp_dir) = create_unit_test_state();
    
    let result = jwks(State(app_state)).await;
    assert!(result.is_ok());
    
    let Json(jwks_response): Json<JwksResponse> = result.unwrap();
    
    let json_str = serde_json::to_string(&jwks_response)
        .expect("Should be able to serialize JWKS response");
    
    let parsed: serde_json::Value = serde_json::from_str(&json_str)
        .expect("Should be able to parse serialized JSON");
    
    assert!(parsed.get("keys").is_some(), "Should have 'keys' field");
    assert!(parsed["keys"].is_array(), "'keys' should be an array");
    assert_eq!(parsed["keys"].as_array().unwrap().len(), 1, "Should have one key");
    
    let key = &parsed["keys"][0];
    assert_eq!(key["kty"], "RSA", "Should have correct key type");
    assert_eq!(key["use"], "sig", "Should have correct key use");
    assert_eq!(key["alg"], "RS256", "Should have correct algorithm");
    assert!(key["n"].is_string(), "Modulus should be a string");
    assert!(key["e"].is_string(), "Exponent should be a string");
    assert!(key["kid"].is_string(), "Key ID should be a string");
}

#[tokio::test]
async fn test_openid_configuration_serialization() {
    let (app_state, _temp_dir) = create_unit_test_state();
    
    let Json(config): Json<OpenIdConfiguration> = openid_configuration(State(app_state)).await;
    
    let json_str = serde_json::to_string(&config)
        .expect("Should be able to serialize OpenID configuration");
    
    let parsed: serde_json::Value = serde_json::from_str(&json_str)
        .expect("Should be able to parse serialized JSON");
    
    let required_fields = [
        "issuer",
        "jwks_uri", 
        "authorization_endpoint",
        "token_endpoint",
        "userinfo_endpoint",
        "response_types_supported",
        "subject_types_supported",
        "id_token_signing_alg_values_supported"
    ];
    
    for field in &required_fields {
        assert!(parsed.get(field).is_some(), "Should have '{}' field", field);
    }
    
    assert!(parsed["response_types_supported"].is_array(), "response_types_supported should be an array");
    assert!(parsed["subject_types_supported"].is_array(), "subject_types_supported should be an array");
    assert!(parsed["id_token_signing_alg_values_supported"].is_array(), "id_token_signing_alg_values_supported should be an array");
}

#[tokio::test]
async fn test_jwks_endpoint_performance() {
    let (app_state, _temp_dir) = create_unit_test_state();
    
    let start = std::time::Instant::now();
    
    for _ in 0..10 {
        let result = jwks(State(app_state.clone())).await;
        assert!(result.is_ok(), "All JWKS calls should succeed");
    }
    
    let duration = start.elapsed();
    
    // Should complete 10 calls reasonably quickly (arbitrary threshold)
    assert!(duration.as_millis() < 1000, "10 JWKS calls should complete in under 1 second");
}

#[tokio::test] 
async fn test_jwks_key_id_consistency() {
    let (app_state, _temp_dir) = create_unit_test_state();
    let expected_kid = app_state.config.product_key_id.clone();
    
    for _ in 0..5 {
        let result = jwks(State(app_state.clone())).await;
        assert!(result.is_ok());
        
        let Json(jwks_response): Json<JwksResponse> = result.unwrap();
        assert_eq!(jwks_response.keys[0].kid, expected_kid, "Key ID should be consistent across calls");
    }
}
