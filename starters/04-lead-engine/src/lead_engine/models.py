"""
Module: models
Description: Pydantic models for lead engine arguments and responses.

Implements:
    - docs/sdk/commands.md#argument-validation
"""

from __future__ import annotations

from enum import Enum

import re

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class LeadTier(str, Enum):
    """Lead quality tier based on AI scoring."""

    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class OutreachTemplate(str, Enum):
    """Available email outreach templates."""

    INTRO = "intro"
    FOLLOW_UP = "follow-up"
    DEMO_INVITE = "demo-invite"


# ---------------------------------------------------------------------------
# Argument models
# ---------------------------------------------------------------------------


class AddLeadArgs(BaseModel):
    """Arguments for the add-lead command."""

    company: str = Field(
        ..., min_length=1, max_length=200, description="Company name"
    )
    contact_name: str = Field(
        ..., min_length=1, max_length=200, description="Primary contact name"
    )
    email: str = Field(
        ..., min_length=3, max_length=320, description="Contact email address"
    )
    website: str = Field(
        default="", max_length=500, description="Company website URL (optional)"
    )
    notes: str = Field(
        default="", max_length=2000, description="Additional notes about the lead"
    )

    @field_validator("company", "contact_name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Value cannot be empty or whitespace only")
        return stripped

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email address")
        return v.lower()


class ScoreLeadArgs(BaseModel):
    """Arguments for the score-lead command."""

    lead_id: str = Field(
        ..., min_length=1, max_length=100, description="Lead identifier to score"
    )


class SendOutreachArgs(BaseModel):
    """Arguments for the send-outreach command."""

    lead_id: str = Field(
        ..., min_length=1, max_length=100, description="Lead identifier"
    )
    template_name: OutreachTemplate = Field(
        default=OutreachTemplate.INTRO,
        description="Email template to use: intro, follow-up, or demo-invite",
    )


class PipelineReportArgs(BaseModel):
    """Arguments for the pipeline-report command (no required fields)."""

    include_details: bool = Field(
        default=False, description="Include full lead details in report"
    )


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class LeadRecord(BaseModel):
    """Stored lead record."""

    lead_id: str
    company: str
    contact_name: str
    email: str
    website: str
    notes: str
    score: int | None = None
    tier: LeadTier | None = None
    score_reasoning: str | None = None
    outreach_sent: bool = False
    created_at: str
    scored_at: str | None = None
    outreach_at: str | None = None


class LeadScoreResult(BaseModel):
    """AI lead scoring result."""

    score: int = Field(ge=0, le=100, description="Lead score 0-100")
    tier: LeadTier
    reasoning: str = Field(description="Explanation of the score")
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)


class PipelineSummary(BaseModel):
    """Pipeline report summary."""

    total_leads: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    unscored_leads: int
    outreach_sent: int
    summary: str
