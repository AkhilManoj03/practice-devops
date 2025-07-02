use axum::{
    body::Body,
    extract::State,
    http::Request,
    middleware::Next,
    response::Response,
};

use crate::{errors::AppError, state::AppState};

pub async fn auth(
    State(state): State<AppState>,
    req: Request<Body>,
    next: Next,
) -> Result<Response, AppError> {
    let headers = req.headers();
    let api_key = headers
        .get("X-Internal-API-Key")
        .and_then(|value| value.to_str().ok());

    match api_key {
        Some(key) if key == state.config.internal_api_key => Ok(next.run(req).await),
        _ => Err(AppError::Unauthorized),
    }
}
