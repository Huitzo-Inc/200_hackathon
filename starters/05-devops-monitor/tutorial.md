# DevOps Monitor Tutorial

**Time: 30 minutes | Level: Advanced**

In this tutorial, you'll build an intelligent monitoring system that checks
service health, uses AI to diagnose failures, sends multi-channel alerts,
and generates uptime reports. This is the most advanced template and
demonstrates production-ready patterns.

---

## Prerequisites

Complete all previous templates:
- **01-smart-notes** (storage basics)
- **02-ai-content-toolkit** (LLM integration)
- **03-data-cruncher** (file handling + combined APIs)
- **04-lead-engine** (HTTP, email, multi-command workflows)

## Overview

The DevOps Monitor has four commands forming a monitoring pipeline:

```
Endpoints --> [health-check] --> Storage (with TTL)
                                       |
                              [diagnose] --> AI Root Cause Analysis
                                       |
                                [alert] --> Email + Telegram
                                       |
                          [status-report] --> Uptime + AI Insights
```

---

## Step 1: Understanding the Models (3 minutes)

Open `src/devops_monitor/models.py`.

### ServiceStatus enum

```python
class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"
```

Five distinct states give granular visibility into service health. A service
can be "degraded" (responding slowly) without being completely "down".

### Severity levels

```python
class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
```

Severity drives notification behavior. Critical alerts go to all channels;
info alerts might only go to email.

### Bounded validation

```python
class HealthCheckArgs(BaseModel):
    timeout_seconds: int = Field(default=10, ge=1, le=60)
```

`ge=1, le=60` prevents both zero-timeout (instant failure) and excessively
long timeouts. Always bound numeric inputs.

---

## Step 2: The health-check Command (7 minutes)

Open `src/devops_monitor/commands.py` and find `health_check`.

### Checking endpoints

Each endpoint is checked individually with graceful error handling:

```python
async def _check_endpoint(ctx, url, timeout_seconds):
    start = time.monotonic()
    try:
        response = await ctx.http.get(url, timeout=timeout_seconds)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        # Determine status based on response code and latency
        ...
    except TimeoutError:
        return EndpointResult(status=ServiceStatus.TIMEOUT, ...)
    except Exception as e:
        return EndpointResult(status=ServiceStatus.DOWN, error=str(e), ...)
```

Key pattern: the helper **never raises**. It always returns a result,
converting exceptions into status values. This ensures one failing endpoint
doesn't prevent checking the others.

### TTL storage for time-series data

```python
await ctx.storage.save(
    check_key,
    result.model_dump(),
    ttl=HEALTH_TTL,  # 7 days
    metadata={"type": "health_check", "service": service, "status": ...},
)
```

**TTL (Time-to-Live)** means old health records automatically expire after
7 days. This prevents unlimited storage growth from continuous monitoring.

### Automatic incident creation

```python
if result.status in (ServiceStatus.DOWN, ServiceStatus.TIMEOUT, ServiceStatus.DEGRADED):
    incident_key = f"{INCIDENT_PREFIX}{service}:{now}"
    await ctx.storage.save(incident_key, {...}, ttl=HEALTH_TTL, ...)
```

When an endpoint is unhealthy, an incident record is automatically created.
The `diagnose` command later queries these incidents.

### Try it:

```bash
# Check default endpoints
curl -X POST http://localhost:8080/api/v1/commands/monitor/health-check \
  -H "Content-Type: application/json" \
  -d '{}'

# Check specific endpoints
curl -X POST http://localhost:8080/api/v1/commands/monitor/health-check \
  -H "Content-Type: application/json" \
  -d '{
    "endpoints": ["https://httpbin.org/status/200", "https://httpbin.org/status/500"],
    "timeout_seconds": 5
  }'
```

---

## Step 3: The diagnose Command (5 minutes)

The `diagnose` command uses AI to analyze incident patterns.

### Querying incident history

```python
incidents = await ctx.storage.query(
    prefix=f"{INCIDENT_PREFIX}{args.service_name}:",
    metadata={"type": "incident", "service": args.service_name},
    limit=100,
)
```

This combines prefix matching (efficient) with metadata filtering (precise).
The result is all incidents for a specific service.

### AI pattern analysis

The prompt includes common root causes to guide the LLM:

```python
"""Consider common root causes:
- DNS resolution failures
- Connection pool exhaustion
- Memory leaks (increasing response times)
- Deployment issues (sudden failures)
- Rate limiting (periodic failures)
- Database connection issues
- Certificate expiration"""
```

Providing a structured list helps the LLM generate more specific diagnoses.

### Graceful fallback

```python
try:
    response = await ctx.llm.complete(...)
    diagnosis_data = json.loads(response)
except Exception:
    diagnosis_data = {
        "pattern": "Unable to analyze - AI service unavailable",
        "root_cause": "Insufficient data for automated analysis",
        "recommendation": "Review logs manually",
        "confidence": "low",
    }
```

If the LLM is unavailable, we return a meaningful fallback instead of
failing. The confidence is set to "low" to signal this is a default.

### Try it:

```bash
# First run health-check a few times, then:
curl -X POST http://localhost:8080/api/v1/commands/monitor/diagnose \
  -H "Content-Type: application/json" \
  -d '{"service_name": "httpbin", "lookback_minutes": 60}'
```

---

## Step 4: The alert Command (7 minutes)

This command demonstrates **multi-channel notifications** with graceful
degradation.

### Channel-independent alerting

```python
# Send via Telegram (instant)
if "telegram" in args.channels:
    try:
        await ctx.telegram.send(
            chat_id="default",
            message=telegram_msg,
            parse_mode="Markdown",
        )
        channels_notified.append("telegram")
    except Exception:
        pass  # Continue with other channels

# Send via email (detailed)
if "email" in args.channels:
    try:
        await ctx.email.send(to="ops-team@example.com", subject=..., html=...)
        channels_notified.append("email")
    except Exception:
        pass
```

Each channel is independent. If Telegram is unavailable but email works,
the alert still gets through. The response shows which channels succeeded.

### Severity-based styling

```python
color = '#dc2626' if severity == CRITICAL else '#f59e0b' if severity == WARNING else '#3b82f6'
```

Critical alerts are red, warnings are amber, info is blue. This visual
distinction helps ops teams triage quickly.

### Telegram vs. Email

- **Telegram**: Short, instant, Markdown-formatted for mobile notification
- **Email**: Detailed HTML table with full context for investigation

This dual-channel approach ensures urgent issues get instant attention
(Telegram push notification) while detailed context is available for
follow-up (email).

### Try it:

```bash
curl -X POST http://localhost:8080/api/v1/commands/monitor/alert \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "api",
    "severity": "critical",
    "message": "API server returning 500 errors"
  }'
```

---

## Step 5: The status-report Command (5 minutes)

This command aggregates health data into an uptime report.

### Computing uptime percentage

```python
for service, checks in sorted(service_checks.items()):
    total = len(checks)
    healthy = sum(1 for c in checks if c.get("status") == "healthy")
    uptime = (healthy / total * 100) if total > 0 else 0.0
```

Simple but effective: count healthy checks divided by total checks.
For a more sophisticated version, you could weight by time intervals.

### AI-generated insights

```python
insights_prompt = f"""Generate a brief operations report summary.
Period: {period_start} to {period_end}
Overall Uptime: {overall_uptime:.1f}%
Per-Service Status:
{service_summary}

Provide 2-3 sentences covering:
1. Overall system health assessment
2. Any services needing attention
3. One actionable recommendation"""
```

The LLM turns raw numbers into actionable narrative. This is the
"intelligence" in Intelligence Packs -- transforming data into decisions.

### Fallback summary

```python
except Exception:
    worst = min(services, key=lambda s: s.uptime_percent)
    ai_insights = (
        f"Overall uptime is {overall_uptime:.1f}%. "
        f"{worst.service_name} has the lowest uptime..."
    )
```

Even without AI, the report identifies the worst-performing service.

### Try it:

```bash
curl -X POST http://localhost:8080/api/v1/commands/monitor/status-report \
  -H "Content-Type: application/json" \
  -d '{"services": ["api", "auth"]}'
```

---

## Step 6: Run the Tests (3 minutes)

```bash
pip install -e ".[dev]"
pytest -v
```

The test suite includes 40 tests covering:

- **TestHealthCheck** - Healthy, down, timeout, mixed, storage persistence
- **TestDiagnose** - Pattern analysis, no-data error, LLM failure fallback
- **TestAlert** - Both channels, single channel, graceful channel failures
- **TestStatusReport** - Uptime calculation, filtering, empty data, LLM fallback
- **TestFullWorkflow** - Complete health-check -> diagnose -> alert -> report cycle
- **TestModels** - Validation bounds, enum values, rejection of invalid input

Look at `tests/conftest.py` for the mock setup. Note how
`MockHTTPBackend` supports `fail_urls` and `timeout_urls` to simulate
specific endpoint failures.

---

## Production Patterns Summary

This template demonstrates several production-ready patterns:

| Pattern | Where Used | Why It Matters |
|---------|-----------|----------------|
| **TTL Storage** | health-check, incidents | Prevents unbounded data growth |
| **Graceful Degradation** | alert, diagnose, status-report | Commands never fail due to optional services |
| **Multi-Channel** | alert | Redundancy -- if one channel fails, others work |
| **AI Fallback** | diagnose, status-report | Meaningful results even without LLM |
| **Metadata Queries** | diagnose, status-report | Efficient filtering of stored records |
| **Service Extraction** | _service_from_url | Human-readable names from URLs |

---

## What's Next?

You've completed all five starter templates. You now have the skills to
build a production-quality Intelligence Pack.

**Start your hackathon project!** Here are some ideas combining what
you've learned:

- **Intelligent CI/CD Monitor** - Track build times, predict failures
- **Customer Support Triage** - Score tickets, route to agents, auto-respond
- **Sales Intelligence** - Combine lead engine with DevOps-style monitoring
- **Content Pipeline** - AI content creation with approval workflows
- **Financial Alert System** - Monitor market data, alert on anomalies

Good luck and happy building!
