use chainlogistics_sdk::{ChainLogisticsClient, Config};
use mockito::Server;

#[tokio::test]
async fn health_check_parses_structured_response() {
    let mut server = Server::new_async().await;
    let _mock = server
        .mock("GET", "/health")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(
            r#"{
                "status":"healthy",
                "service":"chainlogistics-backend",
                "timestamp":"2026-01-01T00:00:00Z",
                "checks":[{"name":"database","status":"healthy","latency_ms":3,"details":"ok"}],
                "monitoring":{"error_rate":0.0,"total_errors":0}
            }"#,
        )
        .create_async()
        .await;

    let client = ChainLogisticsClient::new(
        Config::new("test-key").with_base_url(server.url()),
    )
    .unwrap();

    let response = client.health_check().await.unwrap();

    assert_eq!(response.status, "healthy");
    assert_eq!(response.checks.len(), 1);
}

#[tokio::test]
async fn batch_health_checks_requests_all_probe_endpoints() {
    let mut server = Server::new_async().await;
    let _health = server
        .mock("GET", "/health")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{"status":"healthy","service":"chainlogistics-backend","timestamp":"2026-01-01T00:00:00Z","checks":[],"monitoring":{"error_rate":0.0,"total_errors":0}}"#)
        .create_async()
        .await;
    let _ready = server
        .mock("GET", "/health/ready")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{"status":"healthy","service":"chainlogistics-backend","timestamp":"2026-01-01T00:00:00Z","checks":[]}"#)
        .create_async()
        .await;
    let _live = server
        .mock("GET", "/health/live")
        .with_status(200)
        .with_header("content-type", "application/json")
        .with_body(r#"{"status":"healthy","service":"chainlogistics-backend","timestamp":"2026-01-01T00:00:00Z","uptime_hint":"ready"}"#)
        .create_async()
        .await;

    let client = ChainLogisticsClient::new(
        Config::new("test-key").with_base_url(server.url()),
    )
    .unwrap();

    let (health, readiness, liveness) = client.batch_health_checks().await.unwrap();

    assert_eq!(health.status, "healthy");
    assert_eq!(readiness.status, "healthy");
    assert_eq!(liveness.status, "healthy");
}
