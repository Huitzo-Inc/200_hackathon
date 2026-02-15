# What is Huitzo?

**Read time: 5 minutes**

Huitzo is the **Operating System for Intelligence** -- a platform where you build smart, reusable services called **Intelligence Packs** using Python. Unlike automation tools that follow rigid rules, Huitzo lets you build services that think, adapt, and make decisions using AI.

---

## The Core Idea

Traditional automation:
```
IF email received → THEN forward to Slack
```

Huitzo intelligence:
```
Analyze incoming email → Score urgency 0-100 → Route critical items to Slack
with AI-generated summary → Store analysis for trending
```

The difference: **automation follows rules, intelligence makes decisions**.

---

## Core Concepts

### Intelligence Packs

An Intelligence Pack is a collection of related **commands** packaged together. Think of it like a Python library, but each function is automatically exposed as an API endpoint with built-in validation, storage, AI, and integrations.

Example packs:
- **Smart Notes** -- Save, search, and summarize notes with AI
- **Lead Engine** -- Score and route sales leads using AI analysis
- **DevOps Monitor** -- Health checks with intelligent alerting

### Commands

A command is a single unit of work. You define it with the `@command` decorator:

```python
from huitzo_sdk import command, Context
from pydantic import BaseModel

class GreetArgs(BaseModel):
    name: str

@command("greet", namespace="my-pack")
async def greet(args: GreetArgs, ctx: Context) -> dict:
    """Say hello to someone."""
    return {"message": f"Hello, {args.name}!"}
```

This creates an API endpoint at `/api/v1/commands/my-pack/greet` that:
- Validates input automatically (via Pydantic)
- Has built-in error handling and retries
- Returns structured JSON responses

### Context API

Every command receives a `Context` object (`ctx`) that provides access to platform services:

| Service | Access | What It Does |
|---------|--------|--------------|
| **Storage** | `ctx.storage` | Save and retrieve data (key-value store) |
| **LLM** | `ctx.llm` | AI text generation and analysis |
| **Email** | `ctx.email` | Send emails |
| **HTTP** | `ctx.http` | Make HTTP requests to external APIs |
| **Files** | `ctx.files` | Read/write files (CSV, Excel, JSON) |
| **Telegram** | `ctx.telegram` | Send Telegram messages |
| **Logging** | `ctx.log` | Structured logging |

### Pydantic Validation

All command inputs and outputs use Pydantic models for automatic validation:

```python
from pydantic import BaseModel, Field

class LeadInput(BaseModel):
    company: str = Field(..., min_length=1, description="Company name")
    email: str = Field(..., description="Contact email")
    budget: float = Field(ge=0, description="Budget in USD")
```

If someone sends invalid data, Huitzo automatically returns a clear error -- you don't write validation logic.

---

## How It Works

### 1. You Write Python

Write commands using the Huitzo SDK. Each command is a Python function decorated with `@command`:

```python
@command("score-lead", namespace="sales")
async def score_lead(args: LeadInput, ctx: Context) -> dict:
    # Use AI to analyze the lead
    score = await ctx.llm.complete(
        prompt=f"Score this lead 0-100: {args.company}, budget ${args.budget}",
        schema=LeadScore
    )

    # Save to storage
    await ctx.storage.save(f"lead:{args.company}", score.model_dump())

    return score.model_dump()
```

### 2. Huitzo Handles the Rest

When you run `huitzo pack dev`, the platform:
- Starts a local development server
- Registers your commands as API endpoints
- Provides storage, AI, email, HTTP, and other services
- Handles validation, retries, timeouts, and error formatting

### 3. Test with curl or Any HTTP Client

```bash
curl -X POST http://localhost:8080/api/v1/commands/sales/score-lead \
  -H "Content-Type: application/json" \
  -d '{"company": "Acme Corp", "email": "cto@acme.com", "budget": 50000}'
```

---

## What Makes Huitzo Different

### AI-Native

AI is a first-class citizen. Call `ctx.llm.complete()` with a prompt and get structured, validated responses back. No API key management, no HTTP requests to OpenAI -- it just works.

### Code-First

Write Python, not drag-and-drop flows. Full IDE support, version control, testing, and debugging. Use any Python library you want.

### Built-In Infrastructure

Storage, email, HTTP, file handling, Telegram -- all available through `ctx`. No provisioning databases, no configuring email servers, no managing API connections.

### Structured Outputs

Combine Pydantic models with LLM calls to get AI responses that conform to your schema. No parsing, no regex, no "hope the AI returns valid JSON."

```python
class LeadScore(BaseModel):
    score: int = Field(ge=0, le=100)
    reasoning: str
    next_steps: list[str]

result = await ctx.llm.complete(prompt="...", schema=LeadScore)
# result is guaranteed to be a valid LeadScore instance
```

---

## Use Cases

| Use Case | How Huitzo Helps |
|----------|-----------------|
| **Content Analysis** | Summarize, extract entities, classify text with AI |
| **Lead Scoring** | AI-powered lead qualification and routing |
| **Data Processing** | Read CSV/Excel, transform with AI, export results |
| **Monitoring** | Health checks with intelligent alerting |
| **Customer Support** | Categorize tickets, suggest responses, route to teams |
| **Report Generation** | Pull data from APIs, analyze with AI, email results |

---

## Learn More

### Deep Dive: Core Concepts

For a thorough understanding of Huitzo's architecture and philosophy:

- **[Why Huitzo](concepts/why-huitzo.md)** -- The infrastructure gap between AI models and production systems
- **[Building Methodology](concepts/building-methodology.md)** -- Commands, not applications: how to decompose problems into Intelligence Packs
- **[From Model to Production](concepts/from-model-to-production.md)** -- The complete infrastructure layer Huitzo handles automatically

### Next Steps

- [Quick Start Guide](../QUICKSTART.md) -- Install and run your first pack in 5 minutes
- [SDK Quick Reference](sdk-quick-reference.md) -- All the APIs at a glance
- [Hackathon Guide](hackathon-guide.md) -- Rules, prizes, and how to submit
