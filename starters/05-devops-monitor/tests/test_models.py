"""
Tests for DevOps Monitor Pydantic models and validation.
"""

from __future__ import annotations

import pytest

from devops_monitor.models import (
    AlertArgs,
    DiagnoseArgs,
    EndpointResult,
    HealthCheckArgs,
    ServiceStatus,
    Severity,
    StatusReportArgs,
    UptimeEntry,
)


class TestHealthCheckArgs:
    def test_defaults(self) -> None:
        args = HealthCheckArgs()
        assert args.endpoints == []
        assert args.timeout_seconds == 10

    def test_custom_endpoints(self) -> None:
        args = HealthCheckArgs(
            endpoints=["https://api.example.com/health"],
            timeout_seconds=5,
        )
        assert len(args.endpoints) == 1
        assert args.timeout_seconds == 5

    def test_timeout_bounds(self) -> None:
        with pytest.raises(Exception):
            HealthCheckArgs(timeout_seconds=0)
        with pytest.raises(Exception):
            HealthCheckArgs(timeout_seconds=61)

    def test_empty_url_rejected(self) -> None:
        with pytest.raises(Exception):
            HealthCheckArgs(endpoints=["  "])


class TestDiagnoseArgs:
    def test_valid(self) -> None:
        args = DiagnoseArgs(service_name="api")
        assert args.service_name == "api"
        assert args.lookback_minutes == 60

    def test_empty_service_rejected(self) -> None:
        with pytest.raises(Exception):
            DiagnoseArgs(service_name="")

    def test_whitespace_stripped(self) -> None:
        args = DiagnoseArgs(service_name="  api  ")
        assert args.service_name == "api"

    def test_lookback_bounds(self) -> None:
        with pytest.raises(Exception):
            DiagnoseArgs(service_name="api", lookback_minutes=4)
        with pytest.raises(Exception):
            DiagnoseArgs(service_name="api", lookback_minutes=1441)


class TestAlertArgs:
    def test_valid(self) -> None:
        args = AlertArgs(
            service_name="api",
            severity=Severity.CRITICAL,
            message="Server down",
        )
        assert args.service_name == "api"
        assert args.severity == Severity.CRITICAL
        assert "email" in args.channels
        assert "telegram" in args.channels

    def test_custom_channels(self) -> None:
        args = AlertArgs(
            service_name="api",
            severity=Severity.INFO,
            channels=["telegram"],
        )
        assert args.channels == ["telegram"]

    def test_all_severity_levels(self) -> None:
        for sev in Severity:
            args = AlertArgs(service_name="test", severity=sev)
            assert args.severity == sev


class TestStatusReportArgs:
    def test_defaults(self) -> None:
        args = StatusReportArgs()
        assert args.start_date == ""
        assert args.end_date == ""
        assert args.services == []

    def test_with_filters(self) -> None:
        args = StatusReportArgs(
            start_date="2026-02-14T00:00:00",
            services=["api", "db"],
        )
        assert len(args.services) == 2


class TestEndpointResult:
    def test_healthy(self) -> None:
        result = EndpointResult(
            url="https://api.example.com/health",
            status=ServiceStatus.HEALTHY,
            response_time_ms=45,
            status_code=200,
            checked_at="2026-02-14T10:00:00",
        )
        assert result.status == ServiceStatus.HEALTHY

    def test_down_with_error(self) -> None:
        result = EndpointResult(
            url="https://api.example.com/health",
            status=ServiceStatus.DOWN,
            response_time_ms=0,
            error="Connection refused",
            checked_at="2026-02-14T10:00:00",
        )
        assert result.error == "Connection refused"


class TestUptimeEntry:
    def test_valid(self) -> None:
        entry = UptimeEntry(
            service_name="api",
            total_checks=100,
            healthy_checks=99,
            uptime_percent=99.0,
            avg_response_ms=45,
            incidents=1,
        )
        assert entry.uptime_percent == 99.0

    def test_percent_bounds(self) -> None:
        with pytest.raises(Exception):
            UptimeEntry(
                service_name="api",
                total_checks=100,
                healthy_checks=99,
                uptime_percent=101.0,
                avg_response_ms=45,
                incidents=0,
            )
