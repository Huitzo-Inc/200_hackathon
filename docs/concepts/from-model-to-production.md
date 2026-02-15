---
title: "From Model to Production"
category: "Concepts"
tags: ["concepts", "deployment", "infrastructure", "production"]
order: 3
description: "The complete infrastructure layer Huitzo handles — from execution to deployment"
---

# From Model to Production

## The Production Checklist

Moving from "it works on my laptop" to production reveals a hidden checklist most teams discover one painful failure at a time:

- How do requests execute? What handles retries? Timeouts?
- How do you isolate tenants? One customer sees another's data?
- Who authenticates requests? How do you validate JWTs?
- Where does data live? How do you prevent race conditions?
- How do you call LLMs? What if OpenAI is down?
- How do you send emails? Handle bounces? Rate limits?
- How do you deploy? Roll back? Version?
- How do you debug distributed failures?

Huitzo handles **all of this** out of the box. You write business logic. The platform handles infrastructure.

## What Huitzo Provides

### Execution & Runtime

**Celery workers** execute your commands with automatic queue routing:
- **Fast queue** (<5s) — Quick lookups, status checks
- **Medium queue** (<60s) — LLM calls, email sends
- **Long queue** (>60s) — Batch processing, report generation

**Timeout enforcement** follows a hierarchy:
- Command-level: `@command("task", timeout=120)` — 2 minutes max
- Pack-level: `huitzo.yaml` default for all commands
- Platform-level: Global safety limit

**Automatic retries** with exponential backoff:
```python
@command("flaky-api-call", namespace="integration", retries=5, retry_delay=2)
async def call_external_api(args: ApiArgs, ctx: Context) -> dict:
    # Platform retries up to 5 times with exponential backoff
    response = await ctx.http.get(args.url)
    return {"status": "success", "data": response}
```

**Correlation IDs** trace requests across distributed execution:
- Every request has `ctx.correlation_id`
- Appears in all logs, errors, traces
- Debug multi-command workflows end-to-end

### Multi-Tenant Isolation

Every request has identity — automatically injected by the platform:

```python
@command("save-preference", namespace="user")
async def save_preference(args: PreferenceArgs, ctx: Context) -> dict:
    # Identity available in every command
    # - ctx.user_id: UUID of authenticated user
    # - ctx.tenant_id: UUID of customer/organization
    # - ctx.session_id: UUID of WebCLI or API session

    # Storage is automatically scoped to tenant + user + pack
    await ctx.storage.save("theme", args.theme_name)

    return {
        "user_id": str(ctx.user_id),
        "tenant_id": str(ctx.tenant_id),
        "saved": True
    }
```

**PostgreSQL Row-Level Security (RLS)** enforces isolation at database level:
- One tenant's data is **invisible** to another
- Developer never writes `WHERE tenant_id = ?` queries
- Impossible to leak data across tenants (enforced by database, not application code)

### Authentication & Authorization

**JWT tokens** validated by platform before your command executes:
- Every request to `/api/v1/commands/{namespace}/{command}` requires valid token
- Context injection provides `ctx.user_id`, `ctx.tenant_id` automatically
- Invalid tokens rejected before your code runs

**Rate limiting** per tenant per pack:
- Prevent abuse and runaway costs
- Configured in `huitzo.yaml` manifest
- Enforced by platform, not command code

**No auth code in commands** — the platform handles it:
```python
@command("admin-action", namespace="management")
async def admin_action(args: AdminArgs, ctx: Context) -> dict:
    # ctx.user_id is already authenticated by platform
    # You handle business logic authorization:

    user = await ctx.storage.get(f"user:{ctx.user_id}")
    if user.get("role") != "admin":
        raise CommandError("Insufficient permissions")

    # Proceed with admin logic
    return {"status": "completed"}
```

### Storage & State

`ctx.storage` backed by **PostgreSQL JSONB** (Cloud/Self-Hosted) or **SQLite** (Edge future):
- Automatic tenant isolation via RLS
- No schemas, no migrations, no connection pools
- TTL support for cache-style data

```python
# Save data (automatically scoped to tenant + user + pack)
await ctx.storage.save("preferences", {"theme": "dark"}, ttl=86400)  # 24h TTL

# Retrieve data
prefs = await ctx.storage.get("preferences")

# List keys with prefix
keys = await ctx.storage.list("session:*")

# Delete data
await ctx.storage.delete("temp-data")
```

**Key scoping:** Storage keys are scoped as `{tenant_id}:{pack_namespace}:{key}` internally. You just use `"preferences"` — the platform handles the rest.

### Integrations

#### LLM Integration

Provider-agnostic interface supports OpenAI, Anthropic, and more:

```python
from pydantic import BaseModel

class RiskAnalysis(BaseModel):
    risk_score: int  # 0-100
    reasoning: str
    recommended_action: str

@command("analyze-risk", namespace="insurance")
async def analyze_risk(args: ClaimArgs, ctx: Context) -> dict:
    # Structured output with Pydantic schema
    analysis = await ctx.llm.complete(
        prompt=f"Analyze insurance claim risk: {args.claim_text}",
        schema=RiskAnalysis,  # Enforces structured output
        model="gpt-4o-mini"
    )

    return {
        "claim_id": args.claim_id,
        "risk_score": analysis.risk_score,
        "reasoning": analysis.reasoning
    }
```

**Platform handles:**
- API key management (configured per tenant or platform-wide)
- Rate limiting and retry logic
- Provider failover (if configured)
- Cost tracking per tenant

#### Email Integration

Send transactional emails without managing SMTP:

```python
@command("send-welcome", namespace="onboarding")
async def send_welcome_email(args: WelcomeArgs, ctx: Context) -> dict:
    await ctx.email.send(
        to=args.user_email,
        subject="Welcome to Acme Insurance",
        body="Your account is ready...",
        html_body="<h1>Welcome!</h1><p>Your account is ready...</p>"
    )

    return {"status": "sent", "recipient": args.user_email}
```

#### HTTP Integration

Call external APIs with built-in error handling:

```python
@command("fetch-policy", namespace="integration")
async def fetch_policy_data(args: PolicyArgs, ctx: Context) -> dict:
    # GET request with automatic retries
    response = await ctx.http.get(
        url=f"https://api.partner.com/policies/{args.policy_id}",
        headers={"Authorization": f"Bearer {args.api_key}"}
    )

    return {"policy_data": response}
```

#### File Integration

Process files (CSV, Excel, PDF) with built-in readers:

```python
@command("process-claims-csv", namespace="insurance")
async def process_claims_csv(args: FileArgs, ctx: Context) -> dict:
    # Read CSV from storage or URL
    rows = await ctx.files.read_csv(args.file_path)

    processed = []
    for row in rows:
        # Process each claim
        result = await ctx.llm.complete(
            prompt=f"Categorize claim: {row['description']}",
            model="gpt-4o-mini"
        )
        processed.append({"claim_id": row["id"], "category": result})

    return {"processed_count": len(processed)}
```

### Error Handling & Retries

**Automatic retries** with exponential backoff for transient failures:
```python
@command("external-api", namespace="integration", retries=5, retry_delay=2)
async def call_api(args: ApiArgs, ctx: Context) -> dict:
    # Platform retries up to 5 times:
    # Attempt 1: immediate
    # Attempt 2: +2s
    # Attempt 3: +4s
    # Attempt 4: +8s
    # Attempt 5: +16s
    response = await ctx.http.get(args.url)
    return {"data": response}
```

**Structured exception hierarchy** for precise error handling:
```python
from huitzo_sdk.errors import (
    ValidationError,      # Input validation failed
    CommandError,         # General command failure
    TimeoutError,         # Execution timeout
    StorageError,         # Storage operation failed
    ExternalAPIError,     # External API call failed
)

@command("validate-and-process", namespace="app")
async def process_data(args: DataArgs, ctx: Context) -> dict:
    if args.amount < 0:
        raise ValidationError("Amount must be positive")

    try:
        result = await ctx.http.post(args.api_url, json={"amount": args.amount})
    except Exception as e:
        raise ExternalAPIError(f"Failed to call API: {e}")

    return {"result": result}
```

See [SDK Quick Reference](../sdk-quick-reference.md) for error handling patterns.

### API Endpoints

Every `@command` gets a **REST endpoint automatically**:

```
POST /api/v1/commands/{namespace}/{command}
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "claim_id": "CLM-12345",
  "claim_text": "Vehicle collision on I-95..."
}
```

**No routing code required.** Define the command, and the endpoint exists.

**OpenAPI documentation** auto-generated:
- Visit `/docs` for interactive Swagger UI
- `/openapi.json` for machine-readable schema
- Pydantic models become request/response schemas automatically

**WebCLI** provides interactive terminal interface:
- `cd @acme/insurance` to navigate to pack
- `run analyze-claim --claim-id=CLM-12345` to execute
- Tab completion, help text, argument validation built-in

## Deployment Portability

**Same command code** works across deployment modes:

| Mode | Status | Infrastructure Owner | Data Location |
|------|--------|---------------------|---------------|
| **CLOUD** | Production | Huitzo (multi-tenant SaaS) | Huitzo cloud (AWS) |
| **SELF_HOSTED** | Production (Year 1) | You (your datacenter) | Your infrastructure |
| **EDGE** | Design (Year 3+) | You (air-gapped devices) | Offline, local SQLite |

Platform abstracts deployment differences. Developer writes once, deploys anywhere.

**Edge mode** (future): Same commands run offline on-device with SQLite + local LLMs. No code changes. This is infrastructure's job, not yours.

## Development Workflow

**No local infrastructure required:**
```bash
# Start development (uses cloud sandbox)
huitzo pack dev

# Your code runs in Huitzo cloud sandbox
# - Auto-reloads on file changes
# - Full PostgreSQL + Redis available
# - LLM, email, HTTP integrations work
# - Logs stream to terminal
# - Local proxy on localhost:8080
# - Docs on localhost:8124
```

**Testing:**
```bash
# Run pytest suite
huitzo pack test

# Run specific test file
huitzo pack test tests/test_analyze_claim.py

# Mock Context for unit tests
from huitzo_sdk.testing import MockContext

async def test_command():
    ctx = MockContext(user_id="test-user", tenant_id="test-tenant")
    result = await analyze_claim(args, ctx)
    assert result["status"] == "analyzed"
```

**Build and publish:**
```bash
# Package pack for distribution
huitzo pack build

# Publish to registry under your @scope
huitzo pack publish
```

See [Quick Start Guide](../../QUICKSTART.md) and [Troubleshooting](../troubleshooting.md) for complete setup.

## What You Still Control

You retain **full control** over:

| Your Responsibility | Examples |
|-------------------|----------|
| **Business logic** | LLM prompts, processing workflows, decision trees |
| **Data validation** | Pydantic models define input/output schemas |
| **Permission checks** | Business logic authorization within commands |
| **External API choices** | Which services to integrate, API endpoints to call |
| **Error messages** | User-facing output, error text, help documentation |
| **Pack configuration** | Timeouts, queues, service usage in `huitzo.yaml` |

Platform handles infrastructure. You handle intelligence.

## The Bottom Line

| You Write | Platform Handles |
|-----------|-----------------|
| Business logic (~30-150 lines) | Execution runtime (Celery workers) |
| Pydantic validation models | Multi-tenant isolation (PostgreSQL RLS) |
| `ctx.llm`/`storage`/`http` calls | Database (PostgreSQL + Redis) |
| Command return values | REST API endpoints + retries + timeouts |
| Pack manifest (`huitzo.yaml`) | Authentication + authorization |
| — | Deployment (Cloud/Self-Hosted/Edge) |
| — | Logging, metrics, correlation IDs |
| — | Scaling and worker pool management |
| — | Rate limiting per tenant |
| — | OpenAPI documentation |

**Result:** 2,000 lines of infrastructure → 30 lines of business logic.

That's the Operating System for Intelligence.

## See Also

- **[SDK Quick Reference](../sdk-quick-reference.md)** – Complete `ctx` and decorator reference
- **[Why Huitzo](why-huitzo.md)** – Understanding the infrastructure gap
- **[Building Methodology](building-methodology.md)** – Commands-not-applications paradigm
- **[Starter Templates](../../starters/)** – See these concepts in action with examples
