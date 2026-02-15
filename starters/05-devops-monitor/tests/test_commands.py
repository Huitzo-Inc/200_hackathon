"""
Tests for DevOps Monitor commands.

Covers health checks, diagnosis, multi-channel alerting, and status reports.
All external services are mocked via conftest fixtures.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from huitzo_sdk import Context

from devops_monitor.commands import alert, diagnose, health_check, status_report
from devops_monitor.models import (
    AlertArgs,
    DiagnoseArgs,
    HealthCheckArgs,
    Severity,
    StatusReportArgs,
)
from tests.conftest import (
    MockEmailBackend,
    MockHTTPBackend,
    MockLLMBackend,
    MockTelegramBackend,
)


# ---------------------------------------------------------------------------
# health-check tests
# ---------------------------------------------------------------------------


class TestHealthCheck:
    async def test_all_healthy(
        self, ctx: Context, http_backend: MockHTTPBackend
    ) -> None:
        """All endpoints return healthy status."""
        endpoints = [
            "https://api.example.com/health",
            "https://auth.example.com/health",
        ]
        for url in endpoints:
            http_backend.responses[url] = {"status": "ok", "status_code": 200}

        result = await health_check(
            HealthCheckArgs(endpoints=endpoints), ctx
        )

        assert result["total_checked"] == 2
        assert result["healthy"] == 2
        assert result["down"] == 0
        assert len(result["results"]) == 2

    async def test_endpoint_down(
        self, ctx: Context, http_backend: MockHTTPBackend
    ) -> None:
        """A failing endpoint is marked as down."""
        http_backend.fail_urls.add("https://api.example.com/health")
        http_backend.responses["https://auth.example.com/health"] = {
            "status": "ok",
            "status_code": 200,
        }

        result = await health_check(
            HealthCheckArgs(
                endpoints=[
                    "https://api.example.com/health",
                    "https://auth.example.com/health",
                ]
            ),
            ctx,
        )

        assert result["total_checked"] == 2
        assert result["healthy"] == 1
        assert result["down"] == 1

        # Find the down endpoint
        down_results = [
            r for r in result["results"] if r["status"] == "down"
        ]
        assert len(down_results) == 1
        assert "api.example.com" in down_results[0]["url"]

    async def test_endpoint_timeout(
        self, ctx: Context, http_backend: MockHTTPBackend
    ) -> None:
        """A timing-out endpoint is marked as timeout."""
        http_backend.timeout_urls.add("https://slow.example.com/health")

        result = await health_check(
            HealthCheckArgs(endpoints=["https://slow.example.com/health"]),
            ctx,
        )

        assert result["total_checked"] == 1
        assert result["down"] == 1  # timeout counts as down
        assert result["results"][0]["status"] == "timeout"

    async def test_default_endpoints(self, ctx: Context) -> None:
        """When no endpoints provided, default endpoints are checked."""
        result = await health_check(HealthCheckArgs(), ctx)
        assert result["total_checked"] == 3  # 3 default endpoints

    async def test_stores_health_records(
        self, ctx: Context, http_backend: MockHTTPBackend
    ) -> None:
        """Health check results are stored with TTL."""
        http_backend.responses["https://api.example.com/health"] = {
            "status": "ok",
            "status_code": 200,
        }

        await health_check(
            HealthCheckArgs(endpoints=["https://api.example.com/health"]),
            ctx,
        )

        # Verify health records are stored
        records = await ctx.storage.query(
            prefix="health:",
            metadata={"type": "health_check"},
        )
        assert len(records) >= 1

    async def test_creates_incident_for_failures(
        self, ctx: Context, http_backend: MockHTTPBackend
    ) -> None:
        """Unhealthy endpoints create incident records."""
        http_backend.fail_urls.add("https://api.example.com/health")

        await health_check(
            HealthCheckArgs(endpoints=["https://api.example.com/health"]),
            ctx,
        )

        incidents = await ctx.storage.query(
            prefix="incident:",
            metadata={"type": "incident"},
        )
        assert len(incidents) == 1
        assert incidents[0]["value"]["service"] == "api"

    async def test_mixed_results(
        self, ctx: Context, http_backend: MockHTTPBackend
    ) -> None:
        """Mixed healthy/unhealthy results are handled correctly."""
        http_backend.responses["https://api.example.com/health"] = {
            "status": "ok",
            "status_code": 200,
        }
        http_backend.fail_urls.add("https://db.example.com/health")
        http_backend.responses["https://cache.example.com/health"] = {
            "status": "ok",
            "status_code": 200,
        }

        result = await health_check(
            HealthCheckArgs(
                endpoints=[
                    "https://api.example.com/health",
                    "https://db.example.com/health",
                    "https://cache.example.com/health",
                ]
            ),
            ctx,
        )

        assert result["total_checked"] == 3
        assert result["healthy"] == 2
        assert result["down"] == 1


# ---------------------------------------------------------------------------
# diagnose tests
# ---------------------------------------------------------------------------


class TestDiagnose:
    async def _seed_incidents(
        self, ctx: Context, http_backend: MockHTTPBackend
    ) -> None:
        """Create incidents by running health checks with failures."""
        http_backend.fail_urls.add("https://api.example.com/health")
        http_backend.responses["https://auth.example.com/health"] = {
            "status": "ok",
            "status_code": 200,
        }

        # Run multiple health checks to create incident history
        for _ in range(3):
            await health_check(
                HealthCheckArgs(
                    endpoints=[
                        "https://api.example.com/health",
                        "https://auth.example.com/health",
                    ]
                ),
                ctx,
            )

    async def test_diagnose_with_incidents(
        self, ctx: Context, http_backend: MockHTTPBackend, llm_backend: MockLLMBackend
    ) -> None:
        """Diagnosis analyzes incident patterns and provides root cause."""
        await self._seed_incidents(ctx, http_backend)

        llm_backend.responses.append(
            json.dumps(
                {
                    "pattern": "Consistent connection failures every check",
                    "root_cause": "Service appears completely unreachable. "
                    "Possible DNS failure or service crash.",
                    "recommendation": "1. Check if the service process is running. "
                    "2. Verify DNS resolution. 3. Check firewall rules.",
                    "confidence": "high",
                }
            )
        )

        result = await diagnose(
            DiagnoseArgs(service_name="api"), ctx
        )

        assert result["service_name"] == "api"
        assert result["incident_count"] >= 3
        assert "pattern" in result
        assert "root_cause" in result
        assert "recommendation" in result
        assert result["confidence"] in ("low", "medium", "high")

    async def test_diagnose_no_data(self, ctx: Context) -> None:
        """Diagnosing a service with no data raises CommandError."""
        from huitzo_sdk.errors import CommandError

        with pytest.raises(CommandError, match="No monitoring data"):
            await diagnose(DiagnoseArgs(service_name="nonexistent"), ctx)

    async def test_diagnose_llm_failure(
        self, ctx: Context, http_backend: MockHTTPBackend, llm_backend: MockLLMBackend
    ) -> None:
        """Diagnosis provides fallback when LLM is unavailable."""
        await self._seed_incidents(ctx, http_backend)
        llm_backend.fail = True

        result = await diagnose(DiagnoseArgs(service_name="api"), ctx)

        # Should still succeed with fallback
        assert result["service_name"] == "api"
        assert "Unable to analyze" in result["pattern"]
        assert result["confidence"] == "low"


# ---------------------------------------------------------------------------
# alert tests
# ---------------------------------------------------------------------------


class TestAlert:
    async def test_alert_both_channels(
        self,
        ctx: Context,
        email_backend: MockEmailBackend,
        telegram_backend: MockTelegramBackend,
    ) -> None:
        """Alert sends to both email and Telegram."""
        result = await alert(
            AlertArgs(
                service_name="api",
                severity=Severity.CRITICAL,
                message="API server is down",
            ),
            ctx,
        )

        assert result["service_name"] == "api"
        assert result["severity"] == "critical"
        assert "telegram" in result["channels_notified"]
        assert "email" in result["channels_notified"]
        assert len(telegram_backend.sent) == 1
        assert len(email_backend.sent) == 1
        assert "alert_id" in result

    async def test_alert_telegram_only(
        self, ctx: Context, telegram_backend: MockTelegramBackend
    ) -> None:
        """Alert sends to Telegram only when configured."""
        result = await alert(
            AlertArgs(
                service_name="cache",
                severity=Severity.WARNING,
                channels=["telegram"],
            ),
            ctx,
        )

        assert "telegram" in result["channels_notified"]
        assert "email" not in result["channels_notified"]
        assert len(telegram_backend.sent) == 1

    async def test_alert_email_only(
        self, ctx: Context, email_backend: MockEmailBackend
    ) -> None:
        """Alert sends to email only when configured."""
        result = await alert(
            AlertArgs(
                service_name="db",
                severity=Severity.INFO,
                channels=["email"],
            ),
            ctx,
        )

        assert "email" in result["channels_notified"]
        assert "telegram" not in result["channels_notified"]
        assert len(email_backend.sent) == 1

    async def test_alert_telegram_failure_graceful(
        self,
        ctx: Context,
        email_backend: MockEmailBackend,
        telegram_backend: MockTelegramBackend,
    ) -> None:
        """If Telegram fails, email still sends."""
        telegram_backend.fail = True

        result = await alert(
            AlertArgs(
                service_name="api",
                severity=Severity.CRITICAL,
                message="Server down",
            ),
            ctx,
        )

        assert "telegram" not in result["channels_notified"]
        assert "email" in result["channels_notified"]

    async def test_alert_email_failure_graceful(
        self,
        ctx: Context,
        email_backend: MockEmailBackend,
        telegram_backend: MockTelegramBackend,
    ) -> None:
        """If email fails, Telegram still sends."""
        email_backend.fail = True

        result = await alert(
            AlertArgs(
                service_name="api",
                severity=Severity.WARNING,
                message="High latency",
            ),
            ctx,
        )

        assert "telegram" in result["channels_notified"]
        assert "email" not in result["channels_notified"]

    async def test_alert_stored_in_storage(self, ctx: Context) -> None:
        """Alert records are persisted in storage."""
        result = await alert(
            AlertArgs(
                service_name="test-service",
                severity=Severity.INFO,
                channels=["telegram"],
            ),
            ctx,
        )

        alert_id = result["alert_id"]
        stored = await ctx.storage.get(f"alert:{alert_id}")
        assert stored is not None
        assert stored["service_name"] == "test-service"

    async def test_alert_severity_levels(self, ctx: Context) -> None:
        """All severity levels work correctly."""
        for severity in [Severity.INFO, Severity.WARNING, Severity.CRITICAL]:
            result = await alert(
                AlertArgs(
                    service_name="test",
                    severity=severity,
                    channels=["telegram"],
                ),
                ctx,
            )
            assert result["severity"] == severity.value


# ---------------------------------------------------------------------------
# status-report tests
# ---------------------------------------------------------------------------


class TestStatusReport:
    async def _seed_health_data(
        self, ctx: Context, http_backend: MockHTTPBackend
    ) -> None:
        """Create health check history for multiple services."""
        http_backend.responses["https://api.example.com/health"] = {
            "status": "ok",
            "status_code": 200,
        }
        http_backend.responses["https://auth.example.com/health"] = {
            "status": "ok",
            "status_code": 200,
        }
        http_backend.fail_urls.add("https://db.example.com/health")

        for _ in range(5):
            await health_check(
                HealthCheckArgs(
                    endpoints=[
                        "https://api.example.com/health",
                        "https://auth.example.com/health",
                        "https://db.example.com/health",
                    ]
                ),
                ctx,
            )

    async def test_status_report_basic(
        self, ctx: Context, http_backend: MockHTTPBackend, llm_backend: MockLLMBackend
    ) -> None:
        """Status report shows per-service uptime."""
        await self._seed_health_data(ctx, http_backend)

        llm_backend.responses.append(
            "System is mostly healthy. Database service needs attention "
            "with 0% uptime. Investigate DB connectivity immediately."
        )

        result = await status_report(StatusReportArgs(), ctx)

        assert result["total_services"] == 3
        assert "period_start" in result
        assert "period_end" in result
        assert "ai_insights" in result

        # Check services
        service_map = {s["service_name"]: s for s in result["services"]}
        assert service_map["api"]["uptime_percent"] == 100.0
        assert service_map["auth"]["uptime_percent"] == 100.0
        assert service_map["db"]["uptime_percent"] == 0.0

    async def test_status_report_empty(self, ctx: Context) -> None:
        """Status report with no data returns defaults."""
        result = await status_report(StatusReportArgs(), ctx)

        assert result["total_services"] == 0
        assert result["overall_uptime_percent"] == 100.0
        assert "ai_insights" in result

    async def test_status_report_service_filter(
        self, ctx: Context, http_backend: MockHTTPBackend, llm_backend: MockLLMBackend
    ) -> None:
        """Status report can filter by service name."""
        await self._seed_health_data(ctx, http_backend)
        llm_backend.responses.append("API service has 100% uptime.")

        result = await status_report(
            StatusReportArgs(services=["api"]), ctx
        )

        assert result["total_services"] == 1
        assert result["services"][0]["service_name"] == "api"

    async def test_status_report_llm_failure(
        self, ctx: Context, http_backend: MockHTTPBackend, llm_backend: MockLLMBackend
    ) -> None:
        """Status report provides fallback when LLM fails."""
        await self._seed_health_data(ctx, http_backend)
        llm_backend.fail = True

        result = await status_report(StatusReportArgs(), ctx)

        assert result["total_services"] == 3
        assert "ai_insights" in result
        # Fallback should mention the worst service
        assert "db" in result["ai_insights"]

    async def test_overall_uptime_calculation(
        self, ctx: Context, http_backend: MockHTTPBackend, llm_backend: MockLLMBackend
    ) -> None:
        """Overall uptime is calculated correctly from per-service data."""
        await self._seed_health_data(ctx, http_backend)
        llm_backend.responses.append("Summary.")

        result = await status_report(StatusReportArgs(), ctx)

        # 2 services healthy (5 checks each = 10) + 1 down (5 checks, 0 healthy)
        # Overall = 10/15 = 66.67%
        assert 60.0 <= result["overall_uptime_percent"] <= 70.0


# ---------------------------------------------------------------------------
# Full workflow integration test
# ---------------------------------------------------------------------------


class TestFullWorkflow:
    async def test_monitor_detect_alert_report(
        self,
        ctx: Context,
        http_backend: MockHTTPBackend,
        llm_backend: MockLLMBackend,
        email_backend: MockEmailBackend,
        telegram_backend: MockTelegramBackend,
    ) -> None:
        """Full workflow: health-check -> diagnose -> alert -> status-report."""
        # 1. Run health checks (one service down)
        http_backend.responses["https://api.example.com/health"] = {
            "status": "ok",
            "status_code": 200,
        }
        http_backend.fail_urls.add("https://db.example.com/health")

        hc_result = await health_check(
            HealthCheckArgs(
                endpoints=[
                    "https://api.example.com/health",
                    "https://db.example.com/health",
                ]
            ),
            ctx,
        )
        assert hc_result["healthy"] == 1
        assert hc_result["down"] == 1

        # 2. Diagnose the failing service
        llm_backend.responses.append(
            json.dumps(
                {
                    "pattern": "Service completely unreachable",
                    "root_cause": "Database process not running",
                    "recommendation": "Restart the database service",
                    "confidence": "high",
                }
            )
        )

        diag_result = await diagnose(DiagnoseArgs(service_name="db"), ctx)
        assert diag_result["incident_count"] >= 1
        assert diag_result["confidence"] == "high"

        # 3. Send critical alert
        alert_result = await alert(
            AlertArgs(
                service_name="db",
                severity=Severity.CRITICAL,
                message="Database is down. Root cause: process not running.",
            ),
            ctx,
        )
        assert "telegram" in alert_result["channels_notified"]
        assert "email" in alert_result["channels_notified"]

        # 4. Generate status report
        llm_backend.responses.append(
            "System partially degraded. Database service is down. "
            "API service is healthy at 100% uptime."
        )

        report = await status_report(StatusReportArgs(), ctx)
        assert report["total_services"] == 2
        assert report["overall_uptime_percent"] == 50.0

        # Verify all channels received messages
        assert len(telegram_backend.sent) == 1
        assert len(email_backend.sent) == 1
