# Lead Engine Tutorial

**Time: 25 minutes | Level: Intermediate+**

In this tutorial, you'll build an AI-powered lead scoring and outreach engine.
You'll learn how multiple commands compose together into a workflow, how to
use HTTP for data enrichment, and how to send personalized emails.

---

## Prerequisites

Complete the following templates first:
- **01-smart-notes** (storage basics)
- **02-ai-content-toolkit** (LLM integration)
- **03-data-cruncher** (file handling + combined APIs)

## Overview

The Lead Engine has four commands that form a pipeline:

```
add-lead ──> score-lead ──> send-outreach
                  │
                  └──> pipeline-report
```

Each command reads/writes from shared storage, creating a natural workflow
where data flows between commands.

---

## Step 1: Understanding the Models (3 minutes)

Open `src/lead_engine/models.py`. This file defines all the Pydantic models
used across commands.

### Key patterns:

**Enum-based validation:**
```python
class LeadTier(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
```

Using enums ensures only valid values are accepted. When you pass
`tier="invalid"`, Pydantic rejects it automatically.

**EmailStr validation:**
```python
class AddLeadArgs(BaseModel):
    email: EmailStr = Field(..., description="Contact email address")
```

`EmailStr` from `pydantic[email]` validates email format automatically.
No need for custom regex.

**Custom validators:**
```python
@field_validator("company", "contact_name")
@classmethod
def strip_whitespace(cls, v: str) -> str:
    stripped = v.strip()
    if not stripped:
        raise ValueError("Value cannot be empty or whitespace only")
    return stripped
```

This strips whitespace AND rejects empty strings. Validators run before
the command ever executes.

---

## Step 2: The add-lead Command (5 minutes)

Open `src/lead_engine/commands.py` and find the `add_lead` function.

### Storage with metadata

```python
await ctx.storage.save(
    _lead_key(lead_id),
    {**lead.model_dump(), "enrichment": enrichment},
    metadata={"type": "lead", "tier": "unscored", "company": args.company},
)
```

The `metadata` parameter is crucial. It enables `ctx.storage.query()` to
find leads by type and tier without scanning all keys. Think of metadata
as database indexes.

### Graceful HTTP enrichment

```python
async def _enrich_company(ctx, website):
    try:
        data = await ctx.http.get(
            "https://api.enrichment.example.com/v1/company",
            params={"domain": website},
            timeout=5,
        )
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}  # Never fail because of optional enrichment
```

This is a pattern you'll use often: **optional enhancement**. The command
works perfectly without enrichment data, but produces richer results when
the API is available. The short timeout (5s) prevents the enrichment from
slowing down the primary operation.

### Try it:

```bash
curl -X POST http://localhost:8080/api/v1/commands/leads/add-lead \
  -H "Content-Type: application/json" \
  -d '{
    "company": "TechStart Inc",
    "contact_name": "Sarah Chen",
    "email": "sarah@techstart.io",
    "website": "https://techstart.io",
    "notes": "VP of Engineering, Series A, 50 employees"
  }'
```

Save the `lead_id` from the response -- you'll need it for the next steps.

---

## Step 3: The score-lead Command (5 minutes)

Find the `score_lead` function. This is where AI does the heavy lifting.

### Structured LLM output

```python
response = await ctx.llm.complete(
    prompt=scoring_prompt,
    system=system_prompt,
    model="gpt-4o-mini",
    response_format="json",
    temperature=0.3,  # Low temperature for consistent scoring
)
```

Key decisions:
- **`response_format="json"`** ensures the LLM returns valid JSON
- **`temperature=0.3`** reduces randomness for consistent scores
- The prompt includes explicit JSON schema and scoring guidelines

### Parsing and validation

```python
result = LeadScoreResult.model_validate(result_data)
```

Even though we asked for JSON, we validate with Pydantic. This catches
edge cases where the LLM returns unexpected field names or types.

### Updating storage metadata

```python
await ctx.storage.save(
    _lead_key(args.lead_id),
    lead_data,
    metadata={
        "type": "lead",
        "tier": result.tier.value,  # Updated tier!
        "company": lead.company,
    },
)
```

After scoring, we update the metadata to reflect the new tier. This means
`pipeline-report` can query by tier efficiently.

### Try it:

```bash
curl -X POST http://localhost:8080/api/v1/commands/leads/score-lead \
  -H "Content-Type: application/json" \
  -d '{"lead_id": "YOUR_LEAD_ID"}'
```

---

## Step 4: The send-outreach Command (7 minutes)

This command combines three services: storage, LLM, and email.

### Template rendering

Open `src/lead_engine/templates.py`. Each template is a function that
takes a `LeadRecord` and returns `(subject, html_body)`:

```python
def render_intro(lead: LeadRecord) -> tuple[str, str]:
    subject = f"Hi {lead.contact_name} - Quick intro from our team"
    body = f"""<p>Hi {lead.contact_name},</p>
    <p>I came across <strong>{lead.company}</strong>...</p>"""
    return subject, _base_html(body)
```

Templates are registered in a dict for easy lookup:

```python
TEMPLATE_RENDERERS = {
    "intro": render_intro,
    "follow-up": render_follow_up,
    "demo-invite": render_demo_invite,
}
```

### AI personalization (optional enhancement)

```python
try:
    personal_line = await ctx.llm.complete(
        prompt=personalization_prompt,
        model="gpt-4o-mini",
        temperature=0.7,  # Higher for creative personalization
        max_tokens=100,
    )
    # Insert into email...
except Exception:
    pass  # Send base template if personalization fails
```

Notice the pattern: personalization is wrapped in try/except. If the LLM
fails, we still send the base template. This is **graceful degradation** -
the command never fails because of an optional enhancement.

### Sending email

```python
await ctx.email.send(
    to=lead.email,
    subject=subject,
    html=html_body,
)
```

In dev mode, this logs the email. With SMTP configuration, it sends real
emails. The command code is identical in both cases.

### Try it:

```bash
# Intro email
curl -X POST http://localhost:8080/api/v1/commands/leads/send-outreach \
  -H "Content-Type: application/json" \
  -d '{"lead_id": "YOUR_LEAD_ID", "template_name": "intro"}'

# Follow-up email
curl -X POST http://localhost:8080/api/v1/commands/leads/send-outreach \
  -H "Content-Type: application/json" \
  -d '{"lead_id": "YOUR_LEAD_ID", "template_name": "follow-up"}'

# Demo invite
curl -X POST http://localhost:8080/api/v1/commands/leads/send-outreach \
  -H "Content-Type: application/json" \
  -d '{"lead_id": "YOUR_LEAD_ID", "template_name": "demo-invite"}'
```

---

## Step 5: The pipeline-report Command (5 minutes)

This command queries all leads and generates an AI-powered summary.

### Storage queries with metadata

```python
leads_data = await ctx.storage.query(
    prefix=LEAD_PREFIX,        # "lead:"
    metadata={"type": "lead"}, # Only lead records
    limit=500,
)
```

`ctx.storage.query()` returns records matching both the prefix and metadata
filters. Each record has `key`, `value`, and `metadata` fields.

### Categorization

```python
for record in leads_data:
    lead = record["value"]
    tier = lead.get("tier")
    if tier == "hot":
        hot.append(lead)
    elif tier == "warm":
        warm.append(lead)
    # ...
```

### AI-generated summary with fallback

```python
try:
    summary_text = await ctx.llm.complete(
        prompt=summary_prompt,
        system="You are a sales operations analyst.",
        temperature=0.5,
    )
except Exception:
    summary_text = f"Pipeline has {total} leads: ..."
```

If the LLM is unavailable, a basic text summary is generated from the
numbers. The command always succeeds.

### Try it:

```bash
# Add a few more leads first, then:
curl -X POST http://localhost:8080/api/v1/commands/leads/pipeline-report \
  -H "Content-Type: application/json" \
  -d '{"include_details": true}'
```

---

## Step 6: Run the Tests (3 minutes)

```bash
pip install -e ".[dev]"
pytest -v
```

Look at `tests/conftest.py` to understand the mock setup:
- **MockLLMBackend** - Returns configurable JSON responses
- **MockEmailBackend** - Records sent emails for assertions
- **MockHTTPBackend** - Returns configurable responses, can simulate failures
- **StorageWrapper** - Wraps `InMemoryBackend` for `ctx.storage`

The integration test in `test_commands.py::TestFullWorkflow` runs the
complete add -> score -> outreach -> report pipeline.

---

## What's Next?

You've learned:
- Multi-command workflows with shared storage
- Optional HTTP enrichment with graceful degradation
- Email sending with HTML templates and AI personalization
- Storage queries with metadata filters
- Production error handling patterns

**Next template:** [05-devops-monitor](../05-devops-monitor/) - Health
monitoring with multi-channel alerting (the most advanced template).

**Or start building your hackathon project!** Ideas:
- Add lead qualification questions via AI
- Build a multi-step nurture sequence
- Create a lead scoring model that improves over time
- Add Slack/Telegram alerts for hot leads
