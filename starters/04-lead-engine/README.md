# 04 - Lead Engine

**Difficulty: Intermediate+ | Time: 25 minutes | Complete Data Cruncher (03) first**

Build an AI-powered lead scoring and outreach engine that demonstrates multi-command workflows, HTTP enrichment, email integration, and storage queries.

---

## What You'll Learn

- **Multi-command workflows** - Commands that compose together (add -> score -> outreach -> report)
- **`ctx.http`** - Optional company enrichment via external APIs
- **`ctx.email.send()`** - Sending HTML emails with personalized templates
- **`ctx.storage.query()`** - Querying stored data by metadata filters
- **`ctx.llm.complete()`** - AI-powered lead scoring and email personalization
- **Error handling** - `ValidationError`, `CommandError`, graceful degradation

## Commands

| Command | Description | Key APIs |
|---------|-------------|----------|
| `add-lead` | Add a lead with company info, optional HTTP enrichment | `ctx.storage`, `ctx.http` |
| `score-lead` | AI scores a lead 0-100, assigns tier (hot/warm/cold) | `ctx.llm`, `ctx.storage` |
| `send-outreach` | Send personalized email via templates + AI | `ctx.email`, `ctx.llm`, `ctx.storage` |
| `pipeline-report` | Daily digest of all leads grouped by tier | `ctx.storage.query()`, `ctx.llm` |

## Quick Start

```bash
# 1. Navigate to this template
cd starters/04-lead-engine

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Start the dev server
huitzo pack dev

# 4. Add your first lead
curl -X POST http://localhost:8080/api/v1/commands/leads/add-lead \
  -H "Content-Type: application/json" \
  -d '{
    "company": "TechStart Inc",
    "contact_name": "Sarah Chen",
    "email": "sarah@techstart.io",
    "website": "https://techstart.io",
    "notes": "VP of Engineering, met at AI conference"
  }'

# 5. Score the lead (use the lead_id from step 4)
curl -X POST http://localhost:8080/api/v1/commands/leads/score-lead \
  -H "Content-Type: application/json" \
  -d '{"lead_id": "YOUR_LEAD_ID"}'

# 6. Send outreach
curl -X POST http://localhost:8080/api/v1/commands/leads/send-outreach \
  -H "Content-Type: application/json" \
  -d '{"lead_id": "YOUR_LEAD_ID", "template_name": "intro"}'

# 7. Pipeline report
curl -X POST http://localhost:8080/api/v1/commands/leads/pipeline-report \
  -H "Content-Type: application/json" \
  -d '{"include_details": true}'
```

## Project Structure

```
04-lead-engine/
├── README.md              # This file
├── tutorial.md             # Step-by-step tutorial
├── pyproject.toml          # Package config and entry points
├── huitzo.yaml             # Pack manifest (services, permissions)
├── src/
│   └── lead_engine/
│       ├── __init__.py     # Package exports
│       ├── commands.py     # All four commands
│       ├── models.py       # Pydantic args/response models
│       └── templates.py    # HTML email templates
├── tests/
│   ├── conftest.py         # Mock backends (LLM, email, HTTP, storage)
│   ├── test_commands.py    # Full command tests + integration workflow
│   └── test_models.py      # Validation tests
└── examples/
    └── full_workflow.sh    # curl-based demo script
```

## Key Concepts

### Multi-Command Composition

Commands share data through storage. The workflow flows naturally:

```
add-lead --> score-lead --> send-outreach
                 |
                 v
          pipeline-report
```

### Graceful Degradation

The `add-lead` command optionally enriches company data via HTTP. If the
enrichment API is unavailable, the command still succeeds:

```python
async def _enrich_company(ctx, website):
    try:
        data = await ctx.http.get(...)
        return data
    except Exception:
        return {}  # Never fail because of optional enrichment
```

### Email Templates

Three HTML templates are available, rendered with lead data and optionally
personalized by AI:

- **intro** - First contact email
- **follow-up** - Follow-up after no response
- **demo-invite** - Invite to a product demo

### Storage Queries

The `pipeline-report` command uses metadata-based queries to find all leads:

```python
leads = await ctx.storage.query(
    prefix="lead:",
    metadata={"type": "lead"},
    limit=500,
)
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest -v
```

All tests use mock backends -- no API keys or external services needed.

## Extending This Template

Ideas for your hackathon project:

- Add a `qualify-lead` command that asks follow-up questions via AI
- Implement lead de-duplication based on email domain
- Add a `schedule-follow-up` command with TTL-based reminders
- Create a multi-step nurture sequence (intro -> follow-up -> demo-invite)
- Build a scoring model that learns from outreach response data
- Add Slack/Telegram notifications for hot leads

## Services Used

| Service | Purpose | Required |
|---------|---------|----------|
| `ctx.storage` | Lead persistence and querying | Yes |
| `ctx.llm` | Lead scoring and email personalization | Yes |
| `ctx.email` | Sending outreach emails | Yes |
| `ctx.http` | Company enrichment (optional) | No |
