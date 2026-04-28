use crate::{
    client::HttpClient,
    models::GlobalStats,
    Config, Result,
};

/// Service for accessing statistics and analytics
#[derive(Debug, Clone)]
pub struct StatsService {
    client: HttpClient,
}

impl StatsService {
    pub(crate) fn new(client: reqwest::Client, config: Config) -> Self {
        Self {
            client: HttpClient::new(client, config),
        }
    }

    /// Get global statistics
    pub async fn get_global(&self) -> Result<GlobalStats> {
        let request = self.client.get("api/v1/stats");
        self.client.execute(request).await
    }

    /// Get system health status
    pub async fn health(&self) -> Result<crate::models::HealthResponse> {
        let request = self.client.get("health");
        self.client.execute(request).await
    }

    /// Get application readiness status
    pub async fn readiness(&self) -> Result<crate::models::ReadinessResponse> {
        let request = self.client.get("health/ready");
        self.client.execute(request).await
    }

    /// Get process liveness status
    pub async fn liveness(&self) -> Result<crate::models::LivenessResponse> {
        let request = self.client.get("health/live");
        self.client.execute(request).await
    }

    /// Get database health status
    pub async fn db_health(&self) -> Result<crate::models::DbHealthResponse> {
        let request = self.client.get("health/db");
        self.client.execute(request).await
    }

    /// Get monitoring health status
    pub async fn monitoring_health(&self) -> Result<crate::models::MonitoringHealthResponse> {
        let request = self.client.get("health/monitoring");
        self.client.execute(request).await
    }
}
