"""
Module: models
Description: Pydantic models for DevOps Monitor arguments and responses.

Implements:
    - docs/sdk/commands.md#argument-validation
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ServiceStatus(str, Enum):
    """Health check result status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Argument models
# ---------------------------------------------------------------------------


class HealthCheckArgs(BaseModel):
    """Arguments for the health-check command."""

    endpoints: list[str] = Field(
        default_factory=list,
        description="List of endpoint URLs to check. If empty, checks configured defaults.",
    )
    timeout_seconds: int = Field(
        default=10, ge=1, le=60, description="Timeout per endpoint in seconds"
    )

    @field_validator("endpoints")
    @classmethod
    def validate_endpoints(cls, v: list[str]) -> list[str]:
        for url in v:
            if not url.strip():
                raise ValueError("Endpoint URLs cannot be empty strings")
        return v


class DiagnoseArgs(BaseModel):
    """Arguments for the diagnose command."""

    service_name: str = Field(
        ..., min_length=1, max_length=100, description="Service name to diagnose"
    )
    lookback_minutes: int = Field(
        default=60, ge=5, le=1440, description="How far back to analyze (minutes)"
    )

    @field_validator("service_name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("service_name cannot be empty")
        return stripped


class AlertArgs(BaseModel):
    """Arguments for the alert command."""

    service_name: str = Field(
        ..., min_length=1, max_length=100, description="Service that triggered the alert"
    )
    severity: Severity = Field(
        ..., description="Alert severity: info, warning, or critical"
    )
    message: str = Field(
        default="", max_length=2000, description="Additional alert message"
    )
    channels: list[str] = Field(
        default_factory=lambda: ["email", "telegram"],
        description="Notification channels: email, telegram",
    )


class StatusReportArgs(BaseModel):
    """Arguments for the status-report command."""

    start_date: str = Field(
        default="", description="Start date (ISO format, e.g. 2026-02-14). Defaults to 24h ago."
    )
    end_date: str = Field(
        default="", description="End date (ISO format). Defaults to now."
    )
    services: list[str] = Field(
        default_factory=list,
        description="Filter to specific services. Empty = all services.",
    )


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class EndpointResult(BaseModel):
    """Result of a single endpoint health check."""

    url: str
    status: ServiceStatus
    response_time_ms: int = Field(ge=0)
    status_code: int | None = None
    error: str | None = None
    checked_at: str


class HealthCheckResult(BaseModel):
    """Aggregated health check result."""

    total_checked: int
    healthy: int
    degraded: int
    down: int
    results: list[EndpointResult]
    checked_at: str


class DiagnosisResult(BaseModel):
    """AI-generated diagnosis of service issues."""

    service_name: str
    incident_count: int
    pattern: str
    root_cause: str
    recommendation: str
    confidence: str = Field(description="low, medium, or high")
    recent_events: list[dict[str, str]] = Field(default_factory=list)


class AlertResult(BaseModel):
    """Result of sending an alert."""

    service_name: str
    severity: Severity
    channels_notified: list[str]
    alert_id: str
    sent_at: str


class UptimeEntry(BaseModel):
    """Uptime data for a single service."""

    service_name: str
    total_checks: int
    healthy_checks: int
    uptime_percent: float = Field(ge=0.0, le=100.0)
    avg_response_ms: int
    incidents: int


class StatusReportResult(BaseModel):
    """Daily status report."""

    period_start: str
    period_end: str
    total_services: int
    overall_uptime_percent: float
    services: list[UptimeEntry]
    ai_insights: str
