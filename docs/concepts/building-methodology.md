---
title: "Building Methodology"
category: "Concepts"
tags: ["concepts", "commands", "intelligence-packs", "architecture", "design"]
order: 2
description: "The commands-not-applications paradigm and how to decompose problems into Intelligence Packs"
---

# Building Methodology

## The Paradigm Shift: Commands, Not Applications

Traditional approach: Build a monolithic application with many features — authentication, routing, database models, business logic, deployment configuration all tangled together.

Huitzo approach: Decompose your problem into **focused commands**. Each command is 30-150 lines of pure business logic with a single responsibility, validated input, and structured output.

Commands are like Unix commands — `grep` doesn't try to also sort and count. It greps. You pipe it to `sort` and `wc` when you need that. Huitzo commands work the same way: focused tools that compose.

This isn't a constraint. It's a liberation. You stop maintaining infrastructure and start shipping intelligence.

## Anatomy of a Command

Here's what you write — this is **everything**:

```python
from huitzo_sdk import command, Context
from pydantic import BaseModel

class AnalyzeClaimArgs(BaseModel):
    """Validated input schema."""
    claim_id: str
    claim_text: str
    policy_type: str

@command("analyze-claim", namespace="insurance", timeout=60)
async def analyze_claim(args: AnalyzeClaimArgs, ctx: Context) -> dict:
    """Analyze insurance claim using LLM for risk assessment.

    This docstring becomes the help text in WebCLI.
    """
    # Use LLM service (configured by platform)
    analysis = await ctx.llm.complete(
        prompt=f"Analyze this {args.policy_type} claim for risk: {args.claim_text}",
        model="gpt-4o-mini"
    )

    # Save to tenant-isolated storage
    await ctx.storage.save(f"analysis:{args.claim_id}", {
        "risk_score": analysis.get("risk_score"),
        "reasoning": analysis.get("reasoning"),
        "timestamp": ctx.timestamp
    })

    return {
        "claim_id": args.claim_id,
        "risk_score": analysis.get("risk_score"),
        "status": "analyzed"
    }
```

**That's it.** No database schema. No API routing. No auth middleware. No worker configuration. No retry logic. No timeout enforcement. No multi-tenant isolation code.

Everything else — execution, authentication, storage, retries, timeouts, logging, correlation IDs — is the platform's job.

## Decomposing Problems into Commands

**Example problem:** "Insurance company needs to process incoming claims."

Instead of building a "claims processing application," build commands:

- `submit-claim` — Parse incoming email, extract claim data, validate against policy
- `analyze-claim` — LLM risk analysis with structured output
- `check-coverage` — Query policy database to verify coverage limits
- `approve-claim` — Update claim status, trigger payment workflow
- `generate-report` — Create PDF report for adjuster review
- `notify-customer` — Send email with claim status update

Each command:
- Is **independently testable** — run `huitzo pack test` on one command
- Is **independently deployable** — update `analyze-claim` without touching `submit-claim`
- **Fails independently** — if LLM analysis fails, policy lookup still works
- Can be **reused elsewhere** — `notify-customer` works for claims, policy updates, renewals

**Contrast with monolith:**
- Change one feature → rebuild entire application
- One component breaks → entire system down
- Want to test email logic → spin up full database + Redis + worker stack
- Want to reuse notification logic → copy-paste or tight coupling

## Intelligence Packs: Composing Commands

An **Intelligence Pack** is a collection of related commands solving a domain problem. It's a Python package with a `huitzo.yaml` manifest.

**Example:** `@acme/insurance` pack structure

```
insurance/
├── huitzo.yaml              # Pack manifest
├── commands/
│   ├── submit_claim.py      # @acme/insurance/submit-claim
│   ├── analyze_claim.py     # @acme/insurance/analyze-claim
│   ├── check_coverage.py    # @acme/insurance/check-coverage
│   ├── approve_claim.py     # @acme/insurance/approve-claim
│   └── notify_customer.py   # @acme/insurance/notify-customer
└── tests/
    └── test_analyze_claim.py
```

**Namespace structure:** Commands follow `@{scope}/{pack-name}/{command}` pattern.

- `@acme/insurance/analyze-claim` — Fully qualified namespace
- WebCLI supports: `cd @acme/insurance` then `run analyze-claim`
- This enables the marketplace: Agencies publish packs, enterprises install them

## Command Size Guidelines

| Complexity | Typical Lines | Example |
|-----------|--------------|---------|
| **Simple** | 10-30 | Data lookup, status update, cache check |
| **Standard** | 30-80 | LLM analysis, email notification, file parsing |
| **Complex** | 80-150 | Multi-step workflow, batch processing, report generation |
| **Too Large** | >150 | **Split into multiple commands** |

If you're writing more than 150 lines of business logic in one command, you're building a monolith again. Break it down.

## Why This Methodology Works

**Easier to understand**
- Read one command in 5 minutes, not a 5,000-line application over days
- Clear input → processing → output flow
- No hidden dependencies or side effects

**Easier to test**
- Isolated units with known inputs and outputs
- No full system spin-up required
- Mock `ctx.llm` or `ctx.storage` for fast unit tests

**Easier to debug**
- Small surface area per command
- Clear failure modes (validation, LLM call, storage save)
- Correlation IDs trace requests across distributed execution

**Easier to compose**
- Mix and match commands from different packs
- Chain commands: `submit-claim` → `analyze-claim` → `approve-claim`
- Reuse commands across workflows

**Easier to maintain**
- Clear responsibilities per command
- Update one command without affecting others
- No "refactor the entire codebase" death spirals

## The Development Loop

1. **Write command** — 30-80 lines of business logic
2. **Test locally** — `huitzo pack dev` runs in cloud sandbox (no local infra needed)
3. **Run tests** — `huitzo pack test` with pytest
4. **Build pack** — `huitzo pack build` packages for distribution
5. **Publish** — `huitzo pack publish` to registry under your `@scope`

Total time from idea to production: **minutes to hours**, not weeks.

If your first pack takes more than 10 minutes to run locally, we've failed. The platform handles the infrastructure so you don't waste time on setup.

## See Also

- **[SDK Quick Reference](../sdk-quick-reference.md)** – Essential decorator and API patterns
- **[From Model to Production](from-model-to-production.md)** – Infrastructure the platform handles
- **[Starter Templates](../../starters/)** – Build your first Intelligence Pack with guided examples
- **[Quick Start Guide](../../QUICKSTART.md)** – Get up and running in 5 minutes
