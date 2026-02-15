"""
Module: commands
Description: DevOps Monitor commands - intelligent health monitoring and multi-channel alerting.

Implements:
    - docs/sdk/commands.md#the-command-decorator
    - docs/sdk/integrations.md#llm-integration
    - docs/sdk/integrations.md#email-integration
    - docs/sdk/integrations.md#telegram-integration
    - docs/sdk/integrations.md#http-integration
    - docs/sdk/storage.md#core-methods
    - docs/sdk/storage.md#ttl-time-to-live

See Also:
    - docs/sdk/context.md (for Context API)
    - docs/sdk/error-handling.md (for error patterns)

This module demonstrates advanced patterns:
    - Health monitoring with endpoint checks
    - AI-powered pattern analysis for root cause diagnosis
    - Multi-channel alerting (email + Telegram)
    - TTL storage for time-series health data
    - Graceful degradation when services are unavailable
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from huitzo_sdk import Context, command
from huitzo_sdk.errors import CommandError

from devops_monitor.models import (
    AlertArgs,
    AlertResult,
    DiagnoseArgs,
    DiagnosisResult,
    EndpointResult,
    HealthCheckArgs,
    HealthCheckResult,
    ServiceStatus,
    Severity,
    StatusReportArgs,
    StatusReportResult,
    UptimeEntry,
)

# ---------------------------------------------------------------------------
# Storage key conventions
# ---------------------------------------------------------------------------

CHECK_PREFIX = "health:"
INCIDENT_PREFIX = "incident:"
ALERT_PREFIX = "alert:"

# Default endpoints to check when none provided
DEFAULT_ENDPOINTS = [
    "https://api.example.com/health",
    "https://auth.example.com/health",
    "https://cdn.example.com/health",
]

# TTL for health check records (7 days)
HEALTH_TTL = 7 * 24 * 3600


# ---------------------------------------------------------------------------
# Helper: extract service name from URL
# ---------------------------------------------------------------------------


def _service_from_url(url: str) -> str:
    """Extract a readable service name from a URL."""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        host = parsed.hostname or url
        # e.g. "api.example.com" -> "api"
        parts = host.split(".")
        return parts[0] if parts else host
    except Exception:
        return url


# ---------------------------------------------------------------------------
# Helper: check a single endpoint
# ---------------------------------------------------------------------------


async def _check_endpoint(
    ctx: Context, url: str, timeout_seconds: int
) -> EndpointResult:
    """Check a single endpoint and return its status.

    Uses ctx.http for the health check. Gracefully handles failures.
    """
    now = datetime.now(timezone.utc).isoformat()
    import time

    start = time.monotonic()

    try:
        response = await ctx.http.get(url, timeout=timeout_seconds)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        # Determine status based on response
        status_code = None
        if isinstance(response, dict):
            status_code = response.get("status_code", 200)
        else:
            status_code = 200

        if status_code is not None and status_code >= 500:
            status = ServiceStatus.DOWN
        elif status_code is not None and status_code >= 400:
            status = ServiceStatus.DEGRADED
        elif elapsed_ms > 2000:
            status = ServiceStatus.DEGRADED
        else:
            status = ServiceStatus.HEALTHY

        return EndpointResult(
            url=url,
            status=status,
            response_time_ms=elapsed_ms,
            status_code=status_code,
            checked_at=now,
        )

    except TimeoutError:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return EndpointResult(
            url=url,
            status=ServiceStatus.TIMEOUT,
            response_time_ms=elapsed_ms,
            error="Request timed out",
            checked_at=now,
        )
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return EndpointResult(
            url=url,
            status=ServiceStatus.DOWN,
            response_time_ms=elapsed_ms,
            error=str(e),
            checked_at=now,
        )


# ---------------------------------------------------------------------------
# Command: health-check
# ---------------------------------------------------------------------------


@command("health-check", namespace="monitor", timeout=120)
async def health_check(args: HealthCheckArgs, ctx: Context) -> dict[str, Any]:
    """Check health of multiple endpoints and record results with timestamps.

    Checks each endpoint via HTTP, records results in TTL storage, and
    automatically creates incident records for unhealthy services.

    Args:
        args: Endpoints to check and timeout settings.
        ctx: Huitzo context providing HTTP and storage services.

    Returns:
        Aggregated health check results with per-endpoint details.
    """
    endpoints = args.endpoints or DEFAULT_ENDPOINTS
    now = datetime.now(timezone.utc).isoformat()

    # Check all endpoints
    results: list[EndpointResult] = []
    for url in endpoints:
        result = await _check_endpoint(ctx, url, args.timeout_seconds)
        results.append(result)

    # Count statuses
    healthy = sum(1 for r in results if r.status == ServiceStatus.HEALTHY)
    degraded = sum(1 for r in results if r.status == ServiceStatus.DEGRADED)
    down = sum(
        1
        for r in results
        if r.status in (ServiceStatus.DOWN, ServiceStatus.TIMEOUT)
    )

    # Store each result with TTL for time-series analysis
    for result in results:
        service = _service_from_url(result.url)
        check_key = f"{CHECK_PREFIX}{service}:{now}"
        await ctx.storage.save(
            check_key,
            result.model_dump(),
            ttl=HEALTH_TTL,
            metadata={
                "type": "health_check",
                "service": service,
                "status": result.status.value,
            },
        )

        # Record incidents for unhealthy services
        if result.status in (
            ServiceStatus.DOWN,
            ServiceStatus.TIMEOUT,
            ServiceStatus.DEGRADED,
        ):
            incident_key = f"{INCIDENT_PREFIX}{service}:{now}"
            await ctx.storage.save(
                incident_key,
                {
                    "service": service,
                    "url": result.url,
                    "status": result.status.value,
                    "error": result.error,
                    "response_time_ms": result.response_time_ms,
                    "occurred_at": now,
                },
                ttl=HEALTH_TTL,
                metadata={"type": "incident", "service": service},
            )

    check_result = HealthCheckResult(
        total_checked=len(results),
        healthy=healthy,
        degraded=degraded,
        down=down,
        results=results,
        checked_at=now,
    )

    return check_result.model_dump()


# ---------------------------------------------------------------------------
# Command: diagnose
# ---------------------------------------------------------------------------


@command("diagnose", namespace="monitor", timeout=60)
async def diagnose(args: DiagnoseArgs, ctx: Context) -> dict[str, Any]:
    """AI-analyze recent failures for root cause patterns.

    Queries incident history from storage and uses LLM to identify
    patterns, suggest root causes, and provide recommendations.

    Args:
        args: Service name and lookback window.
        ctx: Huitzo context providing storage and LLM services.

    Returns:
        AI-generated diagnosis with pattern, root cause, and recommendations.

    Raises:
        CommandError: If no incidents found for the service.
    """
    # Query recent incidents for this service
    incidents = await ctx.storage.query(
        prefix=f"{INCIDENT_PREFIX}{args.service_name}:",
        metadata={"type": "incident", "service": args.service_name},
        limit=100,
    )

    # Also query health checks for context
    health_records = await ctx.storage.query(
        prefix=f"{CHECK_PREFIX}{args.service_name}:",
        metadata={"type": "health_check", "service": args.service_name},
        limit=100,
    )

    if not incidents and not health_records:
        raise CommandError(
            f"No monitoring data found for service '{args.service_name}'. "
            "Run health-check first.",
            details={"service_name": args.service_name},
        )

    # Format incidents for AI analysis
    incident_summaries = []
    for record in incidents:
        event = record["value"]
        incident_summaries.append(
            f"- [{event.get('occurred_at', '?')}] Status: {event.get('status', '?')}, "
            f"Error: {event.get('error', 'none')}, "
            f"Response: {event.get('response_time_ms', '?')}ms"
        )

    health_summaries = []
    for record in health_records:
        event = record["value"]
        health_summaries.append(
            f"- [{event.get('checked_at', '?')}] Status: {event.get('status', '?')}, "
            f"Response: {event.get('response_time_ms', '?')}ms"
        )

    diagnosis_prompt = f"""Analyze the following monitoring data for service "{args.service_name}"
and provide a diagnosis.

Recent Incidents ({len(incidents)} total):
{chr(10).join(incident_summaries) if incident_summaries else 'No recent incidents.'}

Recent Health Checks ({len(health_records)} total):
{chr(10).join(health_summaries[-10:]) if health_summaries else 'No health check data.'}

Provide your analysis as JSON:
{{
    "pattern": "<describe the failure pattern, e.g., 'intermittent timeouts every 15 minutes'>",
    "root_cause": "<most likely root cause based on the data>",
    "recommendation": "<specific actionable steps to resolve>",
    "confidence": "low" | "medium" | "high"
}}

Consider common root causes:
- DNS resolution failures
- Connection pool exhaustion
- Memory leaks (increasing response times)
- Deployment issues (sudden failures)
- Rate limiting (periodic failures)
- Database connection issues
- Certificate expiration"""

    system_prompt = (
        "You are a senior SRE/DevOps engineer analyzing monitoring data. "
        "Be specific and actionable in your diagnosis. When data is limited, "
        "say so and lower your confidence. Always respond with valid JSON."
    )

    try:
        response = await ctx.llm.complete(
            prompt=diagnosis_prompt,
            system=system_prompt,
            model="gpt-4o-mini",
            response_format="json",
            temperature=0.3,
        )

        if isinstance(response, str):
            diagnosis_data = json.loads(response)
        else:
            diagnosis_data = response
    except Exception:
        diagnosis_data = {
            "pattern": "Unable to analyze - AI service unavailable",
            "root_cause": "Insufficient data for automated analysis",
            "recommendation": "Review logs manually and check service health dashboard",
            "confidence": "low",
        }

    # Build recent events summary
    recent_events = [
        {
            "time": record["value"].get("occurred_at", ""),
            "status": record["value"].get("status", ""),
            "error": record["value"].get("error", ""),
        }
        for record in incidents[:5]
    ]

    result = DiagnosisResult(
        service_name=args.service_name,
        incident_count=len(incidents),
        pattern=diagnosis_data.get("pattern", "Unknown"),
        root_cause=diagnosis_data.get("root_cause", "Unknown"),
        recommendation=diagnosis_data.get("recommendation", "Review manually"),
        confidence=diagnosis_data.get("confidence", "low"),
        recent_events=recent_events,
    )

    return result.model_dump()


# ---------------------------------------------------------------------------
# Command: alert
# ---------------------------------------------------------------------------


@command("alert", namespace="monitor", timeout=30)
async def alert(args: AlertArgs, ctx: Context) -> dict[str, Any]:
    """Send multi-channel alert notification.

    Sends alerts via email (detailed) and Telegram (instant) based on
    the configured channels. Gracefully degrades if a channel fails.

    Args:
        args: Service name, severity, message, and channels.
        ctx: Huitzo context providing email and Telegram services.

    Returns:
        Alert confirmation with channels notified.
    """
    alert_id = str(uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    channels_notified: list[str] = []

    severity_emoji = {
        Severity.INFO: "INFO",
        Severity.WARNING: "WARNING",
        Severity.CRITICAL: "CRITICAL",
    }
    severity_label = severity_emoji.get(args.severity, "ALERT")

    # Compose the alert message
    alert_text = (
        f"[{severity_label}] {args.service_name}\n"
        f"Time: {now}\n"
        f"Alert ID: {alert_id}"
    )
    if args.message:
        alert_text += f"\nDetails: {args.message}"

    # Send via Telegram (instant notification)
    if "telegram" in args.channels:
        try:
            telegram_msg = (
                f"*{severity_label}*: {args.service_name}\n"
                f"Time: `{now}`\n"
            )
            if args.message:
                telegram_msg += f"Details: {args.message}\n"
            telegram_msg += f"Alert ID: `{alert_id}`"

            await ctx.telegram.send(
                chat_id="default",
                message=telegram_msg,
                parse_mode="Markdown",
            )
            channels_notified.append("telegram")
        except Exception:
            # Telegram is optional - continue with other channels
            pass

    # Send via email (detailed report)
    if "email" in args.channels:
        try:
            subject = f"[{severity_label}] Alert: {args.service_name}"

            html = f"""\
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
<h2 style="color: {'#dc2626' if args.severity == Severity.CRITICAL else '#f59e0b' if args.severity == Severity.WARNING else '#3b82f6'};">
    {severity_label}: {args.service_name}
</h2>
<table style="border-collapse: collapse; width: 100%;">
    <tr><td style="padding: 8px; border: 1px solid #eee;"><strong>Service</strong></td>
        <td style="padding: 8px; border: 1px solid #eee;">{args.service_name}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #eee;"><strong>Severity</strong></td>
        <td style="padding: 8px; border: 1px solid #eee;">{args.severity.value}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #eee;"><strong>Time</strong></td>
        <td style="padding: 8px; border: 1px solid #eee;">{now}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #eee;"><strong>Alert ID</strong></td>
        <td style="padding: 8px; border: 1px solid #eee;">{alert_id}</td></tr>
</table>
{"<h3>Details</h3><p>" + args.message + "</p>" if args.message else ""}
<hr style="border: none; border-top: 1px solid #eee; margin-top: 20px;">
<p style="font-size: 12px; color: #999;">Sent by DevOps Monitor | Powered by Huitzo</p>
</body>
</html>"""

            await ctx.email.send(
                to="ops-team@example.com",
                subject=subject,
                html=html,
            )
            channels_notified.append("email")
        except Exception:
            # Email is optional - continue with other channels
            pass

    # Store the alert record
    await ctx.storage.save(
        f"{ALERT_PREFIX}{alert_id}",
        {
            "alert_id": alert_id,
            "service_name": args.service_name,
            "severity": args.severity.value,
            "message": args.message,
            "channels_notified": channels_notified,
            "sent_at": now,
        },
        ttl=30 * 24 * 3600,  # 30-day TTL for alerts
        metadata={
            "type": "alert",
            "service": args.service_name,
            "severity": args.severity.value,
        },
    )

    result = AlertResult(
        service_name=args.service_name,
        severity=args.severity,
        channels_notified=channels_notified,
        alert_id=alert_id,
        sent_at=now,
    )

    return result.model_dump()


# ---------------------------------------------------------------------------
# Command: status-report
# ---------------------------------------------------------------------------


@command("status-report", namespace="monitor", timeout=60)
async def status_report(args: StatusReportArgs, ctx: Context) -> dict[str, Any]:
    """Generate a daily uptime summary with AI-generated insights.

    Queries all health check records from storage, computes per-service
    uptime percentages, and uses AI to generate actionable insights.

    Args:
        args: Date range and optional service filter.
        ctx: Huitzo context providing storage and LLM services.

    Returns:
        Status report with per-service uptime and AI insights.
    """
    now = datetime.now(timezone.utc)

    # Determine period
    if args.start_date:
        period_start = args.start_date
    else:
        period_start = (
            now.replace(hour=0, minute=0, second=0, microsecond=0)
        ).isoformat()

    period_end = args.end_date or now.isoformat()

    # Query all health check records
    all_checks = await ctx.storage.query(
        prefix=CHECK_PREFIX,
        metadata={"type": "health_check"},
        limit=1000,
    )

    # Query all incidents
    all_incidents = await ctx.storage.query(
        prefix=INCIDENT_PREFIX,
        metadata={"type": "incident"},
        limit=500,
    )

    # Group by service
    service_checks: dict[str, list[dict[str, Any]]] = {}
    service_incidents: dict[str, int] = {}

    for record in all_checks:
        check = record["value"]
        service = record.get("metadata", {}).get("service", "unknown")

        # Filter by service list if provided
        if args.services and service not in args.services:
            continue

        service_checks.setdefault(service, []).append(check)

    for record in all_incidents:
        service = record.get("metadata", {}).get("service", "unknown")
        if args.services and service not in args.services:
            continue
        service_incidents[service] = service_incidents.get(service, 0) + 1

    # Compute per-service uptime
    services: list[UptimeEntry] = []
    for service, checks in sorted(service_checks.items()):
        total = len(checks)
        healthy = sum(
            1 for c in checks if c.get("status") == ServiceStatus.HEALTHY.value
        )
        response_times = [
            c.get("response_time_ms", 0) for c in checks if c.get("response_time_ms")
        ]
        avg_response = (
            int(sum(response_times) / len(response_times)) if response_times else 0
        )
        uptime = (healthy / total * 100) if total > 0 else 0.0

        services.append(
            UptimeEntry(
                service_name=service,
                total_checks=total,
                healthy_checks=healthy,
                uptime_percent=round(uptime, 2),
                avg_response_ms=avg_response,
                incidents=service_incidents.get(service, 0),
            )
        )

    # Calculate overall uptime
    total_checks = sum(s.total_checks for s in services)
    total_healthy = sum(s.healthy_checks for s in services)
    overall_uptime = (total_healthy / total_checks * 100) if total_checks > 0 else 100.0

    # Generate AI insights
    service_summary = "\n".join(
        f"- {s.service_name}: {s.uptime_percent}% uptime, "
        f"{s.avg_response_ms}ms avg response, {s.incidents} incidents"
        for s in services
    )

    insights_prompt = f"""Generate a brief operations report summary.

Period: {period_start} to {period_end}
Overall Uptime: {overall_uptime:.1f}%

Per-Service Status:
{service_summary or 'No monitoring data available.'}

Provide 2-3 sentences covering:
1. Overall system health assessment
2. Any services needing attention
3. One actionable recommendation"""

    try:
        ai_insights = await ctx.llm.complete(
            prompt=insights_prompt,
            system="You are a DevOps operations analyst. Be concise and actionable.",
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=200,
        )
        if not isinstance(ai_insights, str):
            ai_insights = str(ai_insights)
    except Exception:
        if services:
            worst = min(services, key=lambda s: s.uptime_percent)
            ai_insights = (
                f"Overall uptime is {overall_uptime:.1f}%. "
                f"{worst.service_name} has the lowest uptime at "
                f"{worst.uptime_percent}% with {worst.incidents} incidents. "
                "Review incident logs for this service."
            )
        else:
            ai_insights = "No monitoring data available. Run health-check to start collecting data."

    result = StatusReportResult(
        period_start=period_start,
        period_end=period_end,
        total_services=len(services),
        overall_uptime_percent=round(overall_uptime, 2),
        services=services,
        ai_insights=ai_insights,
    )

    return result.model_dump()
