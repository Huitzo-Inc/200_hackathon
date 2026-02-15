# SDK Quick Reference

Essential Huitzo SDK patterns for the hackathon. For the full reference, run `./bootws docs`.

---

## Installation

```bash
pip install huitzo-sdk
```

## Import

```python
from huitzo_sdk import command, Context
from pydantic import BaseModel, Field
```

---

## Commands

### Basic Command

```python
from huitzo_sdk import command, Context
from pydantic import BaseModel

class GreetArgs(BaseModel):
    name: str

@command("greet", namespace="my-pack")
async def greet(args: GreetArgs, ctx: Context) -> dict:
    """Say hello."""
    return {"message": f"Hello, {args.name}!"}
```

### Decorator Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Command name (lowercase, hyphens allowed) |
| `namespace` | `str` | Required | Pack namespace |
| `timeout` | `int` | `60` | Max execution time in seconds |
| `retries` | `int` | `3` | Number of retry attempts |
| `version` | `str` | `"1.0.0"` | Command version |

### Full Example

```python
@command(
    "analyze-data",
    namespace="analytics",
    timeout=300,
    retries=5,
)
async def analyze_data(args: AnalyzeArgs, ctx: Context) -> dict:
    """Analyze dataset with AI insights."""
    ...
```

---

## Pydantic Models (Input Validation)

### Basic Model

```python
class MyArgs(BaseModel):
    name: str                          # Required string
    count: int = 10                    # Optional with default
    tags: list[str] = []              # Optional list
    email: str | None = None          # Optional, nullable
```

### With Constraints

```python
class LeadInput(BaseModel):
    company: str = Field(..., min_length=1, max_length=200)
    budget: float = Field(ge=0, description="Budget in USD")
    priority: int = Field(ge=1, le=5, default=3)
```

### With Custom Validation

```python
from pydantic import field_validator

class DateRangeArgs(BaseModel):
    start_date: str
    end_date: str

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v
```

### Structured Output Model

```python
class LeadScore(BaseModel):
    score: int = Field(ge=0, le=100, description="Quality score")
    reasoning: str = Field(description="Why this score")
    next_steps: list[str] = Field(description="Recommended actions")
```

---

## Context API (ctx)

### Storage (ctx.storage)

```python
# Save
await ctx.storage.save("key", {"data": "value"})

# Save with TTL (expires in 1 hour)
await ctx.storage.save("cache:data", value, ttl=3600)

# Get
data = await ctx.storage.get("key")

# Get with default
data = await ctx.storage.get("key", default={})

# Check existence
exists = await ctx.storage.exists("key")

# List keys by prefix
keys = await ctx.storage.list(prefix="cache:")

# Delete
await ctx.storage.delete("key")

# Batch operations
await ctx.storage.save_many({"k1": v1, "k2": v2})
results = await ctx.storage.get_many(["k1", "k2"])
```

**Key naming convention:**
```python
await ctx.storage.save(f"lead:{lead_id}", data)        # Use prefixes
await ctx.storage.save(f"cache:rates", rates, ttl=3600) # TTL for caches
```

### LLM (ctx.llm)

```python
# Simple completion
response = await ctx.llm.complete(
    prompt="Summarize this text: " + text,
    model="gpt-4o-mini"
)

# With system message
response = await ctx.llm.complete(
    prompt=user_query,
    system="You are a financial analyst.",
    model="gpt-4o"
)

# Structured output (returns validated Pydantic model)
response = await ctx.llm.complete(
    prompt="Analyze this lead...",
    schema=LeadScore,
    model="gpt-4o-mini"
)

# With options
response = await ctx.llm.complete(
    prompt="...",
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=1000,
)
```

**Supported models:**

| Provider | Models |
|----------|--------|
| OpenAI | `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo` |
| Anthropic | `claude-3-5-sonnet`, `claude-3-haiku` |

### Email (ctx.email)

```python
# Simple email
await ctx.email.send(
    to="user@example.com",
    subject="Your Report",
    body="Here's your weekly report..."
)

# HTML email
await ctx.email.send(
    to="user@example.com",
    subject="Report",
    html="<h1>Report</h1><p>Details here.</p>"
)

# Multiple recipients
await ctx.email.send(
    to=["user1@example.com", "user2@example.com"],
    cc=["manager@example.com"],
    subject="Team Update",
    body="..."
)

# With attachments
await ctx.email.send(
    to="user@example.com",
    subject="Report",
    body="See attached.",
    attachments=[{"filename": "report.pdf", "content": pdf_bytes}]
)
```

### HTTP (ctx.http)

```python
# GET
response = await ctx.http.get("https://api.example.com/data")

# GET with headers and params
response = await ctx.http.get(
    "https://api.example.com/data",
    headers={"Authorization": "Bearer token"},
    params={"page": 1, "limit": 100}
)

# POST JSON
response = await ctx.http.post(
    "https://api.example.com/submit",
    json={"name": "value"}
)

# PUT, DELETE
response = await ctx.http.put(url, json=data)
response = await ctx.http.delete(url)
```

**Domain restrictions:** HTTP requests are restricted to domains declared in `huitzo.yaml`:
```yaml
services:
  http:
    allowed_domains:
      - "api.example.com"
      - "*.trusted-domain.org"
```

### Files (ctx.files)

```python
# Read files
df = await ctx.files.read_excel("data.xlsx")
df = await ctx.files.read_csv("data.csv")
data = await ctx.files.read_json("config.json")

# Write files
await ctx.files.write("output/report.csv", df.to_csv())
await ctx.files.write("output/data.json", json.dumps(data))

# File info and listing
info = await ctx.files.info("data.xlsx")
files = await ctx.files.list("uploads/")
exists = await ctx.files.exists("data.xlsx")
```

### Telegram (ctx.telegram)

```python
# Send message
await ctx.telegram.send(
    chat_id="123456789",
    message="Alert: Server is down!"
)

# Formatted message
await ctx.telegram.send(
    chat_id="123456789",
    message="*Bold* and _italic_",
    parse_mode="Markdown"
)

# Send document
await ctx.telegram.send_document(
    chat_id="123456789",
    document=pdf_bytes,
    filename="report.pdf",
    caption="Your report"
)
```

### Logging (ctx.log)

```python
ctx.log.debug("Detailed info for debugging")
ctx.log.info("Normal operation", extra={"items": count})
ctx.log.warning("Something unexpected")
ctx.log.error("Something failed", extra={"error": str(e)})
```

---

## Error Handling

### Exception Hierarchy

```
HuitzoError (base)
  CommandError         -- General command failure
  ValidationError      -- Input validation failed
  StorageError         -- Storage operation failed
  IntegrationError     -- External service failed
    LLMError           -- LLM provider error
    EmailError         -- Email sending error
    HTTPError          -- HTTP request error
  RateLimitError       -- Rate limit exceeded
```

### Common Patterns

```python
from huitzo_sdk.errors import ValidationError, CommandError, LLMError

@command("example", namespace="my-pack")
async def example(args: Args, ctx: Context) -> dict:
    # Validation
    if args.count < 0:
        raise ValidationError(
            field="count",
            value=args.count,
            message="Count must be non-negative"
        )

    # Handle external errors
    try:
        result = await ctx.llm.complete(prompt="...", model="gpt-4o-mini")
    except LLMError as e:
        ctx.log.error(f"LLM failed: {e.message}")
        raise CommandError(message="AI analysis unavailable")

    return {"result": result}
```

---

## Return Types

Commands can return:

```python
# Dictionary (most common)
return {"status": "ok", "count": 42}

# Pydantic model
return LeadScore(score=85, reasoning="Strong fit")

# String
return "Hello, World!"

# None (side effects only)
await ctx.email.send(...)
# No return needed
```

---

## Testing Locally

```bash
# Start dev server
huitzo pack dev

# Test with curl
curl -X POST http://localhost:8080/api/v1/commands/{namespace}/{command} \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}'

# View API docs
open http://localhost:8080/docs
```

---

## Pack Manifest (huitzo.yaml)

```yaml
pack:
  name: "my-pack"
  version: "1.0.0"
  description: "My Intelligence Pack"

services:
  http:
    allowed_domains:
      - "api.example.com"
  files:
    allowed_types:
      - .csv
      - .xlsx
      - .json
```

---

## Common Patterns

### Save + Retrieve

```python
@command("save-item", namespace="inventory")
async def save_item(args: ItemArgs, ctx: Context) -> dict:
    await ctx.storage.save(f"item:{args.id}", args.model_dump())
    return {"saved": True, "id": args.id}

@command("get-item", namespace="inventory")
async def get_item(args: GetArgs, ctx: Context) -> dict:
    item = await ctx.storage.get(f"item:{args.id}")
    if not item:
        raise ValidationError(field="id", value=args.id, message="Item not found")
    return item
```

### AI Analysis + Storage

```python
@command("analyze-feedback", namespace="support")
async def analyze_feedback(args: FeedbackArgs, ctx: Context) -> dict:
    analysis = await ctx.llm.complete(
        prompt=f"Analyze this customer feedback: {args.text}",
        schema=FeedbackAnalysis,
        model="gpt-4o-mini"
    )
    await ctx.storage.save(f"feedback:{args.id}", analysis.model_dump())
    return analysis.model_dump()
```

### Multi-Service Workflow

```python
@command("daily-report", namespace="reports")
async def daily_report(args: ReportArgs, ctx: Context) -> dict:
    # Fetch data
    data = await ctx.http.get("https://api.example.com/metrics")

    # Analyze with AI
    summary = await ctx.llm.complete(
        prompt=f"Summarize these metrics: {data}",
        model="gpt-4o-mini"
    )

    # Save to storage
    await ctx.storage.save(f"report:{args.date}", {"data": data, "summary": summary})

    # Send via email
    await ctx.email.send(
        to=args.recipient,
        subject=f"Daily Report - {args.date}",
        body=summary
    )

    return {"status": "sent", "summary": summary}
```

---

## Quick Links

- [What is Huitzo?](what-is-huitzo.md) -- Platform concepts
- [FAQ](faq.md) -- Common questions
- [Troubleshooting](troubleshooting.md) -- Fix common issues
- [Hackathon Guide](hackathon-guide.md) -- Rules and prizes
