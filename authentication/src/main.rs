mod config;
mod errors;
mod handlers;
mod middleware;
mod models;
mod state;
mod telemetry;

use axum::{
    middleware as axum_middleware,
    routing::{get, post},
    Router,
};
use config::Config;
use dotenv::dotenv;
use sqlx::postgres::PgPool;
use state::AppState;
use tower_http::{cors::CorsLayer, trace::TraceLayer};
use tracing::{error, info};

#[tokio::main]
async fn main() {
    // Load environment variables and set config
    dotenv().ok();
    let config = Config::from_env();

    // Initialize tracing
    let tracer_provider = telemetry::init_tracing_subscriber(&config);

    // Set up database connection
    let database_url = format!(
        "postgres://{}:{}@{}:{}/{}",
        config.postgres_user, config.postgres_password, config.postgres_host, config.postgres_port, config.postgres_db
    );
    let pool = PgPool::connect(&database_url)
        .await
        .expect("Failed to connect to Postgres");

    // Build our application state
    let app_state = AppState {
        pool,
        config: config.clone(),
    };

    let protected_routes = Router::new()
        .route("/register", post(handlers::register::register))
        .layer(axum_middleware::from_fn_with_state(app_state.clone(), middleware::auth));

    // Build our application with routes
    let app = Router::new()
        .route("/api/auth/login", post(handlers::login::login))
        .route("/api/auth/status", get(handlers::status::auth_status))
        .route("/.well-known/jwks.json", get(handlers::openid::jwks))
        .route("/.well-known/openid-configuration", get(handlers::openid::openid_configuration))
        .nest("/api/auth", protected_routes)
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
        .with_state(app_state);
    let addr = format!("0.0.0.0:{}", config.port);
    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    info!("Authentication service starting on {}", addr);

    // Shutdown tracer provider
    let tracer_provider_for_shutdown = tracer_provider.clone();
    let shutdown_signal = async move {
        tokio::signal::ctrl_c()
            .await
            .expect("failed to install CTRL+C signal handler");
        if let Err(e) = tracer_provider_for_shutdown.shutdown() {
            error!("Failed to shutdown tracer provider: {}", e);
        }
    };

    // Run the server with graceful shutdown
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal)
        .await
        .unwrap();
}
