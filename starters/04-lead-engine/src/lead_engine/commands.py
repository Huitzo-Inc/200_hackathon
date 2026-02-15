"""
Module: commands
Description: Lead Engine commands - AI-powered lead scoring and outreach automation.

Implements:
    - docs/sdk/commands.md#the-command-decorator
    - docs/sdk/integrations.md#llm-integration
    - docs/sdk/integrations.md#email-integration
    - docs/sdk/integrations.md#http-integration
    - docs/sdk/storage.md#core-methods

See Also:
    - docs/sdk/context.md (for Context API)
    - docs/sdk/error-handling.md (for error patterns)

This module demonstrates multi-command workflows where commands compose
together: add-lead -> score-lead -> send-outreach -> pipeline-report.

Key Concepts:
    - Multi-command composition (commands that reference each other's data)
    - ctx.http for optional company enrichment
    - ctx.email.send() with HTML templates
    - ctx.storage for lead persistence with metadata queries
    - Structured error handling (ValidationError, CommandError)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from huitzo_sdk import Context, command
from huitzo_sdk.errors import CommandError, ValidationError

from lead_engine.models import (
    AddLeadArgs,
    LeadRecord,
    LeadScoreResult,
    LeadTier,
    PipelineReportArgs,
    PipelineSummary,
    ScoreLeadArgs,
    SendOutreachArgs,
)
from lead_engine.templates import TEMPLATE_RENDERERS


# ---------------------------------------------------------------------------
# Helper: storage key conventions
# ---------------------------------------------------------------------------

LEAD_PREFIX = "lead:"


def _lead_key(lead_id: str) -> str:
    return f"{LEAD_PREFIX}{lead_id}"


# ---------------------------------------------------------------------------
# Helper: company enrichment via HTTP (optional, graceful degradation)
# ---------------------------------------------------------------------------


async def _enrich_company(ctx: Context, website: str) -> dict[str, Any]:
    """Try to enrich company data via HTTP. Returns empty dict on failure.

    This demonstrates graceful degradation: the command works fine without
    enrichment data, but is enhanced when the API is available.
    """
    if not website:
        return {}

    try:
        # In production, this would call a real enrichment API like Clearbit.
        # For local dev, it gracefully falls back to empty data.
        data = await ctx.http.get(
            f"https://api.enrichment.example.com/v1/company",
            params={"domain": website},
            timeout=5,
        )
        return data if isinstance(data, dict) else {}
    except Exception:
        # Enrichment is optional - never fail the command because of it
        return {}


# ---------------------------------------------------------------------------
# Command: add-lead
# ---------------------------------------------------------------------------


@command("add-lead", namespace="leads", timeout=30)
async def add_lead(args: AddLeadArgs, ctx: Context) -> dict[str, Any]:
    """Add a new lead with company information.

    Creates a lead record in storage with a unique ID. Optionally enriches
    company data via HTTP if a website is provided.

    Args:
        args: Lead details (company, contact_name, email, website, notes).
        ctx: Huitzo context providing storage, HTTP, and LLM services.

    Returns:
        The created lead record with its generated lead_id.
    """
    lead_id = str(uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()

    # Try optional company enrichment
    enrichment = await _enrich_company(ctx, args.website)

    # Build the lead record
    lead = LeadRecord(
        lead_id=lead_id,
        company=args.company,
        contact_name=args.contact_name,
        email=args.email,
        website=args.website,
        notes=args.notes,
        created_at=now,
    )

    # Save to storage with metadata for querying
    await ctx.storage.save(
        _lead_key(lead_id),
        {**lead.model_dump(), "enrichment": enrichment},
        metadata={"type": "lead", "tier": "unscored", "company": args.company},
    )

    return {
        "lead_id": lead_id,
        "company": args.company,
        "contact_name": args.contact_name,
        "email": args.email,
        "created_at": now,
        "enriched": bool(enrichment),
    }


# ---------------------------------------------------------------------------
# Command: score-lead
# ---------------------------------------------------------------------------


@command("score-lead", namespace="leads", timeout=60)
async def score_lead(args: ScoreLeadArgs, ctx: Context) -> dict[str, Any]:
    """AI-score a lead based on fit criteria, returning 0-100 score and tier.

    Uses LLM to analyze the lead's company, contact, and any enrichment data
    to produce a structured score with reasoning.

    Args:
        args: Contains lead_id of the lead to score.
        ctx: Huitzo context providing storage and LLM services.

    Returns:
        Score result with score (0-100), tier (hot/warm/cold), and reasoning.

    Raises:
        CommandError: If lead_id is not found.
    """
    # Retrieve the lead from storage
    lead_data = await ctx.storage.get(_lead_key(args.lead_id))
    if lead_data is None:
        raise CommandError(
            f"Lead '{args.lead_id}' not found",
            details={"lead_id": args.lead_id},
        )

    lead = LeadRecord.model_validate(lead_data)
    enrichment = lead_data.get("enrichment", {})

    # Build scoring prompt
    enrichment_context = ""
    if enrichment:
        enrichment_context = f"\n\nCompany Enrichment Data:\n{json.dumps(enrichment, indent=2)}"

    scoring_prompt = f"""Score this sales lead from 0-100 based on fit and potential value.

Lead Information:
- Company: {lead.company}
- Contact: {lead.contact_name} ({lead.email})
- Website: {lead.website or 'Not provided'}
- Notes: {lead.notes or 'None'}{enrichment_context}

Scoring Criteria:
- Company fit (industry relevance, company size signals)
- Contact quality (decision-maker signals, email domain)
- Engagement signals (website presence, notes quality)
- Overall potential value

Respond with valid JSON:
{{
    "score": <0-100>,
    "tier": "hot" | "warm" | "cold",
    "reasoning": "<2-3 sentence explanation>",
    "strengths": ["<strength1>", "<strength2>"],
    "concerns": ["<concern1>", "<concern2>"]
}}

Scoring guide:
- 70-100 = "hot" (high-value, strong fit)
- 40-69 = "warm" (potential, needs nurturing)
- 0-39 = "cold" (low fit or insufficient data)"""

    system_prompt = (
        "You are an experienced B2B sales analyst. Score leads objectively based "
        "on available data. When data is limited, lean toward conservative scores. "
        "Always respond with valid JSON matching the requested structure."
    )

    response = await ctx.llm.complete(
        prompt=scoring_prompt,
        system=system_prompt,
        model="gpt-4o-mini",
        response_format="json",
        temperature=0.3,
    )

    # Parse the LLM response
    if isinstance(response, str):
        result_data = json.loads(response)
    else:
        result_data = response

    result = LeadScoreResult.model_validate(result_data)

    # Update the lead record with score
    now = datetime.now(timezone.utc).isoformat()
    lead_data.update(
        {
            "score": result.score,
            "tier": result.tier.value,
            "score_reasoning": result.reasoning,
            "scored_at": now,
        }
    )

    await ctx.storage.save(
        _lead_key(args.lead_id),
        lead_data,
        metadata={
            "type": "lead",
            "tier": result.tier.value,
            "company": lead.company,
        },
    )

    return {
        "lead_id": args.lead_id,
        "company": lead.company,
        "score": result.score,
        "tier": result.tier.value,
        "reasoning": result.reasoning,
        "strengths": result.strengths,
        "concerns": result.concerns,
        "scored_at": now,
    }


# ---------------------------------------------------------------------------
# Command: send-outreach
# ---------------------------------------------------------------------------


@command("send-outreach", namespace="leads", timeout=30)
async def send_outreach(args: SendOutreachArgs, ctx: Context) -> dict[str, Any]:
    """Send a personalized outreach email to a lead.

    Uses LLM to personalize the email template based on lead data, then
    sends via ctx.email. Works in dev mode (logs the email) or with real
    SMTP configuration.

    Args:
        args: Contains lead_id and template_name.
        ctx: Huitzo context providing storage, LLM, and email services.

    Returns:
        Confirmation with email subject and recipient.

    Raises:
        CommandError: If lead_id is not found.
        ValidationError: If template_name is invalid.
    """
    # Retrieve the lead
    lead_data = await ctx.storage.get(_lead_key(args.lead_id))
    if lead_data is None:
        raise CommandError(
            f"Lead '{args.lead_id}' not found",
            details={"lead_id": args.lead_id},
        )

    lead = LeadRecord.model_validate(lead_data)

    # Get the template renderer
    renderer = TEMPLATE_RENDERERS.get(args.template_name.value)
    if renderer is None:
        raise ValidationError(
            field="template_name",
            value=args.template_name.value,
            message=f"Unknown template: {args.template_name.value}. "
            f"Available: {', '.join(TEMPLATE_RENDERERS.keys())}",
        )

    # Render the email template
    subject, html_body = renderer(lead)

    # Optionally use LLM to personalize the email further
    try:
        personalization_prompt = f"""Personalize this sales email for {lead.contact_name} at {lead.company}.

Current email subject: {subject}
Lead notes: {lead.notes or 'None'}
Lead score: {lead.score or 'Not scored'}
Lead tier: {lead.tier or 'Not scored'}

Suggest a brief personalized opening line (1 sentence) that references
something specific about their company. Respond with just the sentence."""

        personal_line = await ctx.llm.complete(
            prompt=personalization_prompt,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=100,
        )

        if personal_line and isinstance(personal_line, str):
            # Insert personalized line after the greeting
            html_body = html_body.replace(
                f"<p>Hi {lead.contact_name},</p>",
                f"<p>Hi {lead.contact_name},</p>\n<p><em>{personal_line.strip()}</em></p>",
            )
    except Exception:
        # Personalization is optional - send the base template if LLM fails
        pass

    # Send the email
    await ctx.email.send(
        to=lead.email,
        subject=subject,
        html=html_body,
    )

    # Update lead record
    now = datetime.now(timezone.utc).isoformat()
    lead_data["outreach_sent"] = True
    lead_data["outreach_at"] = now
    await ctx.storage.save(
        _lead_key(args.lead_id),
        lead_data,
        metadata={
            "type": "lead",
            "tier": lead_data.get("tier", "unscored"),
            "company": lead.company,
        },
    )

    return {
        "lead_id": args.lead_id,
        "company": lead.company,
        "email": lead.email,
        "template": args.template_name.value,
        "subject": subject,
        "sent_at": now,
    }


# ---------------------------------------------------------------------------
# Command: pipeline-report
# ---------------------------------------------------------------------------


@command("pipeline-report", namespace="leads", timeout=60)
async def pipeline_report(
    args: PipelineReportArgs, ctx: Context
) -> dict[str, Any]:
    """Generate a daily pipeline report summarizing all leads by tier.

    Queries all leads from storage, groups them by tier, and uses LLM
    to generate an actionable summary with recommendations.

    Args:
        args: Optional include_details flag.
        ctx: Huitzo context providing storage and LLM services.

    Returns:
        Pipeline summary with counts by tier and AI-generated insights.
    """
    # Query all leads from storage
    leads_data = await ctx.storage.query(
        prefix=LEAD_PREFIX,
        metadata={"type": "lead"},
        limit=500,
    )

    # Categorize leads
    hot: list[dict[str, Any]] = []
    warm: list[dict[str, Any]] = []
    cold: list[dict[str, Any]] = []
    unscored: list[dict[str, Any]] = []
    outreach_count = 0

    for record in leads_data:
        lead = record["value"]
        tier = lead.get("tier")
        if tier == "hot":
            hot.append(lead)
        elif tier == "warm":
            warm.append(lead)
        elif tier == "cold":
            cold.append(lead)
        else:
            unscored.append(lead)
        if lead.get("outreach_sent"):
            outreach_count += 1

    total = len(leads_data)

    # Generate AI summary
    summary_prompt = f"""Generate a brief pipeline report summary.

Pipeline Stats:
- Total leads: {total}
- Hot leads (score 70+): {len(hot)}
- Warm leads (score 40-69): {len(warm)}
- Cold leads (score <40): {len(cold)}
- Unscored leads: {len(unscored)}
- Outreach sent: {outreach_count}

Hot leads: {', '.join(l.get('company', '?') for l in hot) or 'None'}
Warm leads: {', '.join(l.get('company', '?') for l in warm) or 'None'}

Provide a 2-3 sentence actionable summary with recommendations.
Focus on what actions the sales team should take today."""

    try:
        summary_text = await ctx.llm.complete(
            prompt=summary_prompt,
            system="You are a sales operations analyst. Be concise and actionable.",
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=200,
        )
    except Exception:
        summary_text = (
            f"Pipeline has {total} leads: {len(hot)} hot, {len(warm)} warm, "
            f"{len(cold)} cold, {len(unscored)} unscored. "
            f"{outreach_count} have received outreach."
        )

    result = PipelineSummary(
        total_leads=total,
        hot_leads=len(hot),
        warm_leads=len(warm),
        cold_leads=len(cold),
        unscored_leads=len(unscored),
        outreach_sent=outreach_count,
        summary=summary_text if isinstance(summary_text, str) else str(summary_text),
    )

    response: dict[str, Any] = result.model_dump()

    if args.include_details:
        response["leads"] = {
            "hot": [_lead_brief(l) for l in hot],
            "warm": [_lead_brief(l) for l in warm],
            "cold": [_lead_brief(l) for l in cold],
            "unscored": [_lead_brief(l) for l in unscored],
        }

    return response


def _lead_brief(lead: dict[str, Any]) -> dict[str, Any]:
    """Extract a brief summary from a lead record."""
    return {
        "lead_id": lead.get("lead_id", ""),
        "company": lead.get("company", ""),
        "contact_name": lead.get("contact_name", ""),
        "score": lead.get("score"),
        "tier": lead.get("tier"),
        "outreach_sent": lead.get("outreach_sent", False),
    }
