use crate::{
    errors::AppError,
    models::{JwkKey, JwksResponse, OpenIdConfiguration},
    state::AppState,
    config::Config,
};
use axum::{extract::State, response::Json};
use rsa::{pkcs1::DecodeRsaPublicKey, pkcs8::DecodePublicKey, RsaPublicKey, traits::PublicKeyParts};
use std::fs;
use tracing::info;

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

// JWKS endpoint for public key distribution
pub async fn jwks(
    State(state): State<AppState>,
) -> Result<Json<JwksResponse>, AppError> {
    let config = &state.config;
    info!("JWKS endpoint called");
    use base64::{Engine as _, engine::general_purpose};
    
    // Get key ID from config
    let key_id = config.product_key_id.clone();
    
    // Load RSA public key
    let public_key = load_public_key_for_jwks(config)?;
    
    // Extract modulus and exponent
    let modulus = public_key.n();
    let exponent = public_key.e();
    
    // Convert to base64url encoding
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
pub async fn openid_configuration(
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
