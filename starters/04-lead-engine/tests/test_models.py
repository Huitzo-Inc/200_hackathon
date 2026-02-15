"""
Tests for Lead Engine Pydantic models and validation.
"""

from __future__ import annotations

import pytest

from lead_engine.models import (
    AddLeadArgs,
    LeadScoreResult,
    LeadTier,
    OutreachTemplate,
    PipelineReportArgs,
    PipelineSummary,
    ScoreLeadArgs,
    SendOutreachArgs,
)


class TestAddLeadArgs:
    def test_valid_lead(self) -> None:
        args = AddLeadArgs(
            company="Acme Corp",
            contact_name="Jane Doe",
            email="jane@acme.com",
            website="https://acme.com",
            notes="Met at conference",
        )
        assert args.company == "Acme Corp"
        assert args.email == "jane@acme.com"

    def test_minimal_lead(self) -> None:
        args = AddLeadArgs(
            company="Co", contact_name="J", email="j@co.com"
        )
        assert args.website == ""
        assert args.notes == ""

    def test_whitespace_stripped(self) -> None:
        args = AddLeadArgs(
            company="  Acme  ", contact_name="  Jane  ", email="jane@acme.com"
        )
        assert args.company == "Acme"
        assert args.contact_name == "Jane"

    def test_empty_company_rejected(self) -> None:
        with pytest.raises(Exception):
            AddLeadArgs(company="", contact_name="Jane", email="jane@acme.com")

    def test_whitespace_only_company_rejected(self) -> None:
        with pytest.raises(Exception):
            AddLeadArgs(company="   ", contact_name="Jane", email="jane@acme.com")

    def test_invalid_email_rejected(self) -> None:
        with pytest.raises(Exception):
            AddLeadArgs(company="Co", contact_name="J", email="not-valid")

    def test_long_company_rejected(self) -> None:
        with pytest.raises(Exception):
            AddLeadArgs(
                company="x" * 201, contact_name="J", email="j@co.com"
            )


class TestScoreLeadArgs:
    def test_valid(self) -> None:
        args = ScoreLeadArgs(lead_id="abc123")
        assert args.lead_id == "abc123"

    def test_empty_rejected(self) -> None:
        with pytest.raises(Exception):
            ScoreLeadArgs(lead_id="")


class TestSendOutreachArgs:
    def test_valid_with_default_template(self) -> None:
        args = SendOutreachArgs(lead_id="abc")
        assert args.template_name == OutreachTemplate.INTRO

    def test_valid_with_follow_up(self) -> None:
        args = SendOutreachArgs(lead_id="abc", template_name="follow-up")
        assert args.template_name == OutreachTemplate.FOLLOW_UP

    def test_valid_with_demo_invite(self) -> None:
        args = SendOutreachArgs(lead_id="abc", template_name="demo-invite")
        assert args.template_name == OutreachTemplate.DEMO_INVITE

    def test_invalid_template_rejected(self) -> None:
        with pytest.raises(Exception):
            SendOutreachArgs(lead_id="abc", template_name="invalid")


class TestPipelineReportArgs:
    def test_defaults(self) -> None:
        args = PipelineReportArgs()
        assert args.include_details is False

    def test_with_details(self) -> None:
        args = PipelineReportArgs(include_details=True)
        assert args.include_details is True


class TestLeadScoreResult:
    def test_valid_hot(self) -> None:
        result = LeadScoreResult(
            score=85,
            tier=LeadTier.HOT,
            reasoning="Strong fit",
            strengths=["A"],
            concerns=[],
        )
        assert result.tier == LeadTier.HOT

    def test_score_out_of_range(self) -> None:
        with pytest.raises(Exception):
            LeadScoreResult(
                score=101, tier=LeadTier.HOT, reasoning="Too high"
            )

    def test_negative_score(self) -> None:
        with pytest.raises(Exception):
            LeadScoreResult(
                score=-1, tier=LeadTier.COLD, reasoning="Too low"
            )


class TestPipelineSummary:
    def test_valid(self) -> None:
        summary = PipelineSummary(
            total_leads=10,
            hot_leads=3,
            warm_leads=4,
            cold_leads=2,
            unscored_leads=1,
            outreach_sent=5,
            summary="Good pipeline health.",
        )
        assert summary.total_leads == 10
