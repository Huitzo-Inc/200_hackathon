# 05 - DevOps Monitor

**Difficulty:** Advanced | **Time:** 30 minutes | **Prerequisites:** Complete all previous templates

Build an intelligent monitoring system that checks service health, diagnoses failures with AI, sends multi-channel alerts, and generates uptime reports. This template demonstrates production-ready patterns.

---

## What You Will Learn

1. **Health monitoring** - Checking HTTP endpoints and recording status with timestamps
2. **AI-powered diagnostics** - Using LLM to identify failure patterns and root causes
3. **Multi-channel alerting** - Sending notifications via email and Telegram
4. **TTL storage** - Time-series data that auto-expires after a retention period
5. **Graceful degradation** - Services that work even when external channels are unavailable

## Commands

| Command | Description | Arguments |
|---------|-------------|-----------|
| `health-check` | Check HTTP endpoints, record status | `endpoints` (list, optional), `timeout_seconds` (int) |
| `diagnose` | AI-analyze failures for a service | `service_name` (str), `lookback_minutes` (int) |
| `alert` | Send email + Telegram notifications | `service_name` (str), `severity` (str), `message` (str), `channels` (list) |
| `status-report` | Daily uptime summary with AI insights | `start_date` (str), `end_date` (str), `services` (list) |

## Workflow

```
Endpoints --> [health-check] --> Storage (TTL)
                                      |
                             [diagnose] --> AI Root Cause Analysis
                                      |
                               [alert] --> Email + Telegram
                                      |
                         [status-report] --> Uptime % + AI Insights
```

## Quick Start

```bash
# 1. Navigate to this template
cd starters/05-devops-monitor

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Start the dev server
huitzo pack dev

# 4. Run a health check (uses default mock endpoints)
curl -X POST http://localhost:8080/api/v1/commands/monitor/health-check \
  -H "Content-Type: application/json" \
  -d '{"endpoints": ["https://httpbin.org/status/200", "https://httpbin.org/status/500"]}'

# 5. Diagnose a service
curl -X POST http://localhost:8080/api/v1/commands/monitor/diagnose \
  -H "Content-Type: application/json" \
  -d '{"service_name": "httpbin"}'

# 6. Send an alert
curl -X POST http://localhost:8080/api/v1/commands/monitor/alert \
  -H "Content-Type: application/json" \
  -d '{"service_name": "httpbin", "severity": "critical", "message": "Service returned 500"}'

# 7. Generate a status report
curl -X POST http://localhost:8080/api/v1/commands/monitor/status-report \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Run Tests

```bash
cd starters/05-devops-monitor
pytest -v
```

## Project Structure

```
05-devops-monitor/
├── README.md                       # This file
├── pyproject.toml                  # Dependencies and entry points
├── huitzo.yaml                     # Pack manifest
├── .env.example                    # API keys for real alerting
├── src/
│   └── devops_monitor/
│       ├── __init__.py
│       ├── commands.py             # All 4 commands
│       └── models.py               # Pydantic models (args + responses)
├── tests/
│   ├── __init__.py
│   └── test_commands.py            # Mock-based tests
└── examples/
    └── test-commands.sh            # Curl script for full workflow
```

## Services Used

- **HTTP** - `ctx.http.get()` for endpoint health checks
- **Storage** - `ctx.storage.save()` with TTL for time-series health data, `ctx.storage.query()` for incident history
- **LLM** - `ctx.llm.complete()` for diagnosing failure patterns and generating report insights
- **Email** - `ctx.email.send()` for detailed HTML alert notifications
- **Telegram** - `ctx.telegram.send()` for instant alert messages

## Advanced Patterns

### TTL Storage

Health check records auto-expire after 7 days:

```python
await ctx.storage.save(key, data, ttl=7 * 24 * 3600)
```

### Graceful Degradation

Alert channels are optional -- if Telegram or email fails, the command continues with other channels:

```python
try:
    await ctx.telegram.send(...)
    channels_notified.append("telegram")
except Exception:
    pass  # Continue with other channels
```

### AI Diagnostics

The diagnose command feeds incident history to the LLM for pattern analysis, including common root causes like DNS failures, connection pool exhaustion, and deployment issues.

## Configuration

### Local Development (No Keys Required)

In development mode, email and Telegram commands log messages instead of sending them. Health checks work against any public URL.

### Real Alerting (Optional)

Add API keys to `.env` for real multi-channel alerting:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=your-chat-id

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Ideas for Extension

This template is a strong foundation for the **Best Pack** or **Most Creative** prize:

- Add **Slack** as a notification channel alongside email and Telegram
- Build a **scheduled health check** that runs every 5 minutes
- Add **custom health check logic** (check response body, not just status code)
- Create a **dashboard command** that outputs HTML with charts
- Add **PagerDuty** or **OpsGenie** integration for on-call escalation
- Track **SLA compliance** (e.g., 99.9% uptime over 30 days)

## Previous Templates

This is the final template in the learning path:

1. [01-smart-notes](../01-smart-notes/) - Storage basics
2. [02-ai-content-toolkit](../02-ai-content-toolkit/) - LLM integration
3. [03-data-cruncher](../03-data-cruncher/) - File handling + multi-command workflows
4. [04-lead-engine](../04-lead-engine/) - HTTP, email, business automation
5. **05-devops-monitor** (you are here) - Production-ready monitoring
