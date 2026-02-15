---
title: "Why Huitzo"
category: "Concepts"
tags: ["concepts", "philosophy", "infrastructure", "motivation"]
order: 1
description: "The infrastructure gap between AI models and production systems"
---

# Why Huitzo

## The Infrastructure Gap

You trained a model. You wrote a script. It works on your laptop. Now what?

Where does it run? How do users access it? Who can use it? How do you authenticate them? How do you isolate their data from other tenants? How do you version it? How do you roll back if something breaks? How do you retry failed requests? How do you log errors? How do you scale it?

Every AI team hits this wall. The model is the easy part. The infrastructure is the 2,000-line stack you rebuild every time: FastAPI routing, SQLAlchemy models, Redis caching, JWT auth, multi-tenant isolation, LLM client configuration, error handling, deployment scripts, Docker composition.

This isn't a tooling problem. It's a **missing layer** in the stack — the operating system for AI that should exist but doesn't.

## What Building Without Huitzo Looks Like

Here's realistic "before" code for a single AI feature — analyzing insurance claims:

```python
# Without Huitzo: Infrastructure code for ONE command
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy import create_engine, Column, String, JSON
from sqlalchemy.orm import Session, declarative_base
from openai import AsyncOpenAI
from jose import jwt
import redis
import os

app = FastAPI()
Base = declarative_base()
engine = create_engine(os.getenv("DATABASE_URL"))
redis_client = redis.from_url(os.getenv("REDIS_URL"))
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(String, primary_key=True)
    tenant_id = Column(String, index=True)
    user_id = Column(String, index=True)
    data = Column(JSON)

def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

async def verify_token(authorization: str = Header(...)):
    try:
        payload = jwt.decode(authorization.split()[1], os.getenv("JWT_SECRET"))
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/process-claim")
async def process_claim(
    claim_text: str,
    policy_id: str,
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Multi-tenant isolation check
    tenant_id = token_data["tenant_id"]
    user_id = token_data["user_id"]

    # LLM call with error handling
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Analyze claim: {claim_text}"}]
        )
        analysis = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Save to database with tenant isolation
    record = Analysis(
        id=policy_id,
        tenant_id=tenant_id,
        user_id=user_id,
        data={"analysis": analysis}
    )
    db.add(record)
    db.commit()

    return {"status": "processed", "policy_id": policy_id}
```

That's 50+ lines for **one feature**. Repeat this for every command you build. The infrastructure code drowns the business logic.

Teams estimate 2,000-5,000 lines of infrastructure before writing meaningful AI features. Most never ship because they're stuck rebuilding Rails.

## The Huitzo Approach

Here's the same feature with Huitzo — just business logic:

```python
from huitzo_sdk import command, Context
from pydantic import BaseModel

class ProcessClaimArgs(BaseModel):
    claim_text: str
    policy_id: str

@command("process-claim", namespace="insurance", timeout=120)
async def process_claim(args: ProcessClaimArgs, ctx: Context) -> dict:
    """Process insurance claim with LLM analysis."""

    # LLM analysis (provider-agnostic)
    analysis = await ctx.llm.complete(
        prompt=f"Analyze claim: {args.claim_text}",
        model="gpt-4o-mini"
    )

    # Save results (tenant-isolated automatically)
    await ctx.storage.save(f"claim:{args.policy_id}", {
        "analysis": analysis,
        "processed_at": ctx.timestamp,
        "user_id": str(ctx.user_id)
    })

    return {"status": "processed", "policy_id": args.policy_id}
```

That's 25 lines. No auth code. No database setup. No LLM client configuration. No multi-tenant isolation logic. No error handling boilerplate.

The infrastructure is the platform's job.

## What Huitzo Handles

| You Write | Huitzo Provides |
|-----------|----------------|
| Business logic (~30 lines) | Authentication & authorization |
| Pydantic validation models | PostgreSQL database + RLS isolation |
| `ctx.llm.complete()` calls | LLM client configuration |
| `ctx.storage.save()` calls | Multi-tenant data isolation |
| Return structured data | REST API endpoints + retries + timeouts |
| Pack manifest config | Deployment (Cloud/Self-Hosted/Edge) |
| — | Celery workers + queue routing |
| — | Logging, metrics, correlation IDs |
| — | Scaling and worker pool management |

## The Operating System Analogy

Operating systems exist so you don't write disk drivers. Web frameworks exist so you don't parse HTTP headers. Huitzo **is** the OS layer for AI — it handles execution, storage, isolation, and scaling.

You focus on commands. The platform handles the rest.

Linux gave us `grep`, `sed`, `awk` — focused tools that compose. Huitzo gives you the same for AI: commands that do one thing well, Intelligence Packs that compose them.

We build the rails. You build the trains.

## See Also

- **[Building Methodology](building-methodology.md)** – How to decompose problems into commands
- **[From Model to Production](from-model-to-production.md)** – Complete infrastructure layer walkthrough
- **[SDK Quick Reference](../sdk-quick-reference.md)** – Essential APIs and patterns
- **[Starter Templates](../../starters/)** – Hands-on examples to start building
