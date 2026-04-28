use std::time::Instant;

use axum::{
    extract::State,
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use redis::AsyncCommands;
use serde::Serialize;
use serde_json::json;
use utoipa::ToSchema;

use crate::{error::AppError, AppState};

const HEALTHY_STATUS: &str = "healthy";
const DEGRADED_STATUS: &str = "degraded";
const UNHEALTHY_STATUS: &str = "unhealthy";

#[derive(Debug, Clone, Serialize, ToSchema)]
pub struct HealthDependencyStatus {
    pub name: String,
    pub status: String,
    pub latency_ms: u128,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub details: Option<String>,
}

#[derive(Debug, Clone, Serialize, ToSchema)]
pub struct HealthResponse {
    pub status: String,
    pub service: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Clone, Serialize, ToSchema)]
pub struct LivenessResponse {
    pub status: String,
    pub service: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub uptime_hint: String,
}

#[derive(Debug, Clone, Serialize, ToSchema)]
pub struct ReadinessResponse {
    pub status: String,
    pub service: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub checks: Vec<HealthDependencyStatus>,
}

#[derive(Debug, Clone, Serialize, ToSchema)]
pub struct DetailedHealthResponse {
    pub status: String,
    pub service: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub checks: Vec<HealthDependencyStatus>,
    pub monitoring: HealthMonitoringStatus,
}

#[derive(Debug, Clone, Serialize, ToSchema)]
pub struct HealthMonitoringStatus {
    pub error_rate: f64,
    pub total_errors: u64,
    pub last_updated: chrono::DateTime<chrono::Utc>,
}

impl IntoResponse for DetailedHealthResponse {
    fn into_response(self) -> Response {
        let status_code = if self.status == HEALTHY_STATUS {
            StatusCode::OK
        } else {
            StatusCode::SERVICE_UNAVAILABLE
        };

        (status_code, Json(self)).into_response()
    }
}

impl IntoResponse for ReadinessResponse {
    fn into_response(self) -> Response {
        let status_code = if self.status == HEALTHY_STATUS {
            StatusCode::OK
        } else {
            StatusCode::SERVICE_UNAVAILABLE
        };

        (status_code, Json(self)).into_response()
    }
}

fn healthy_dependency(name: &str, started_at: Instant, details: Option<String>) -> HealthDependencyStatus {
    HealthDependencyStatus {
        name: name.to_string(),
        status: HEALTHY_STATUS.to_string(),
        latency_ms: started_at.elapsed().as_millis(),
        details,
    }
}

fn unhealthy_dependency(name: &str, started_at: Instant, details: String) -> HealthDependencyStatus {
    HealthDependencyStatus {
        name: name.to_string(),
        status: UNHEALTHY_STATUS.to_string(),
        latency_ms: started_at.elapsed().as_millis(),
        details: Some(details),
    }
}

fn aggregate_health_status(checks: &[HealthDependencyStatus], error_rate: f64) -> String {
    if checks.iter().any(|check| check.status == UNHEALTHY_STATUS) {
        return UNHEALTHY_STATUS.to_string();
    }

    if error_rate >= 50.0 {
        return DEGRADED_STATUS.to_string();
    }

    HEALTHY_STATUS.to_string()
}

async fn database_status(state: &AppState) -> HealthDependencyStatus {
    let started_at = Instant::now();

    match state.db.health_check().await {
        Ok(_) => healthy_dependency("database", started_at, Some("postgres connection ok".to_string())),
        Err(err) => unhealthy_dependency("database", started_at, err.to_string()),
    }
}

async fn redis_status(state: &AppState) -> HealthDependencyStatus {
    let started_at = Instant::now();

    match state.redis_client.get_multiplexed_tokio_connection().await {
        Ok(mut conn) => {
            let ping_result: redis::RedisResult<String> = conn.ping().await;
            match ping_result {
                Ok(_) => healthy_dependency("redis", started_at, Some("pong".to_string())),
                Err(err) => unhealthy_dependency("redis", started_at, err.to_string()),
            }
        }
        Err(err) => unhealthy_dependency("redis", started_at, err.to_string()),
    }
}

async fn readiness_checks(state: &AppState) -> Vec<HealthDependencyStatus> {
    vec![database_status(state).await, redis_status(state).await]
}

#[utoipa::path(
    get,
    path = "/health",
    tag = "health",
    responses(
        (status = 200, description = "Service and dependencies are healthy", body = DetailedHealthResponse),
        (status = 503, description = "One or more dependencies are unavailable", body = DetailedHealthResponse)
    )
)]
pub async fn health_check(State(state): State<AppState>) -> impl IntoResponse {
    let checks = readiness_checks(&state).await;
    let monitoring_stats = state.error_monitor.get_stats().await;
    let status = aggregate_health_status(&checks, monitoring_stats.error_rate);

    DetailedHealthResponse {
        status,
        service: "chainlogistics-backend".to_string(),
        timestamp: chrono::Utc::now(),
        checks,
        monitoring: HealthMonitoringStatus {
            error_rate: monitoring_stats.error_rate,
            total_errors: monitoring_stats.total_errors,
            last_updated: chrono::Utc::now(),
        },
    }
}

#[utoipa::path(
    get,
    path = "/health/live",
    tag = "health",
    responses(
        (status = 200, description = "Process is alive", body = LivenessResponse)
    )
)]
pub async fn liveness_check() -> Json<LivenessResponse> {
    Json(LivenessResponse {
        status: HEALTHY_STATUS.to_string(),
        service: "chainlogistics-backend".to_string(),
        timestamp: chrono::Utc::now(),
        uptime_hint: "process accepting requests".to_string(),
    })
}

#[utoipa::path(
    get,
    path = "/health/ready",
    tag = "health",
    responses(
        (status = 200, description = "Application is ready to serve traffic", body = ReadinessResponse),
        (status = 503, description = "Application is not ready to serve traffic", body = ReadinessResponse)
    )
)]
pub async fn readiness_check(State(state): State<AppState>) -> impl IntoResponse {
    let checks = readiness_checks(&state).await;
    let status = if checks.iter().all(|check| check.status == HEALTHY_STATUS) {
        HEALTHY_STATUS.to_string()
    } else {
        UNHEALTHY_STATUS.to_string()
    };

    ReadinessResponse {
        status,
        service: "chainlogistics-backend".to_string(),
        timestamp: chrono::Utc::now(),
        checks,
    }
}

#[utoipa::path(
    get,
    path = "/health/db",
    tag = "health",
    responses(
        (status = 200, description = "Database connection is healthy", body = HealthDependencyStatus),
        (status = 503, description = "Database connection failed", body = HealthDependencyStatus)
    )
)]
pub async fn db_health_check(State(state): State<AppState>) -> Result<impl IntoResponse, AppError> {
    let started_at = Instant::now();
    state.db.health_check().await?;

    Ok(Json(HealthDependencyStatus {
        name: "database".to_string(),
        status: HEALTHY_STATUS.to_string(),
        latency_ms: started_at.elapsed().as_millis(),
        details: Some("postgres connection ok".to_string()),
    }))
}

#[utoipa::path(
    get,
    path = "/health/monitoring",
    tag = "health",
    responses(
        (status = 200, description = "Monitoring health summary", body = serde_json::Value),
        (status = 503, description = "Monitoring indicates degradation", body = serde_json::Value)
    )
)]
pub async fn monitoring_health(State(state): State<AppState>) -> impl IntoResponse {
    let stats = state.error_monitor.get_stats().await;
    let is_healthy = stats.error_rate < 50.0;

    let body = json!({
        "status": if is_healthy { HEALTHY_STATUS } else { DEGRADED_STATUS },
        "timestamp": chrono::Utc::now(),
        "service": "chainlogistics-backend",
        "monitoring": {
            "error_rate": stats.error_rate,
            "total_errors": stats.total_errors,
            "top_errors": stats.top_errors,
        }
    });

    if is_healthy {
        (StatusCode::OK, Json(body)).into_response()
    } else {
        (StatusCode::SERVICE_UNAVAILABLE, Json(body)).into_response()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn aggregate_status_prefers_unhealthy_dependencies() {
        let checks = vec![
            HealthDependencyStatus {
                name: "database".to_string(),
                status: HEALTHY_STATUS.to_string(),
                latency_ms: 4,
                details: None,
            },
            HealthDependencyStatus {
                name: "redis".to_string(),
                status: UNHEALTHY_STATUS.to_string(),
                latency_ms: 10,
                details: Some("connection refused".to_string()),
            },
        ];

        assert_eq!(aggregate_health_status(&checks, 0.0), UNHEALTHY_STATUS);
    }

    #[test]
    fn aggregate_status_marks_high_error_rate_as_degraded() {
        let checks = vec![HealthDependencyStatus {
            name: "database".to_string(),
            status: HEALTHY_STATUS.to_string(),
            latency_ms: 1,
            details: None,
        }];

        assert_eq!(aggregate_health_status(&checks, 75.0), DEGRADED_STATUS);
    }

    #[test]
    fn aggregate_status_is_healthy_when_all_checks_pass() {
        let checks = vec![
            HealthDependencyStatus {
                name: "database".to_string(),
                status: HEALTHY_STATUS.to_string(),
                latency_ms: 1,
                details: None,
            },
            HealthDependencyStatus {
                name: "redis".to_string(),
                status: HEALTHY_STATUS.to_string(),
                latency_ms: 2,
                details: None,
            },
        ];

        assert_eq!(aggregate_health_status(&checks, 1.5), HEALTHY_STATUS);
    }
}
