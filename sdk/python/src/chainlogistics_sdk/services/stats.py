"""Stats service for accessing statistics and analytics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import (
    DbHealthResponse,
    GlobalStats,
    HealthResponse,
    LivenessResponse,
    MonitoringHealthResponse,
    ReadinessResponse,
)

if TYPE_CHECKING:
    from ..client import ChainLogisticsClient


class StatsService:
    """Service for accessing statistics and analytics."""
    
    def __init__(self, client: ChainLogisticsClient):
        """Initialize the service.
        
        Args:
            client: ChainLogistics client instance
        """
        self.client = client
    
    def get_global(self) -> GlobalStats:
        """Get global statistics.
        
        Returns:
            Global statistics
        """
        data = self.client.get("api/v1/stats")
        return GlobalStats(**data)
    
    def health(self) -> HealthResponse:
        """Get system health status.
        
        Returns:
            Health response
        """
        data = self.client.get("health")
        return HealthResponse(**data)

    def readiness(self) -> ReadinessResponse:
        """Get readiness status."""
        data = self.client.get("health/ready")
        return ReadinessResponse(**data)

    def liveness(self) -> LivenessResponse:
        """Get liveness status."""
        data = self.client.get("health/live")
        return LivenessResponse(**data)
    
    def db_health(self) -> DbHealthResponse:
        """Get database health status.
        
        Returns:
            Database health response
        """
        data = self.client.get("health/db")
        return DbHealthResponse(**data)

    def monitoring_health(self) -> MonitoringHealthResponse:
        """Get monitoring health status."""
        data = self.client.get("health/monitoring")
        return MonitoringHealthResponse(**data)
