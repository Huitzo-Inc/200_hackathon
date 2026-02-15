"""
Tests for Lead Engine commands.

Covers the full lifecycle: add-lead -> score-lead -> send-outreach -> pipeline-report.
All external services (LLM, email, HTTP) are mocked via conftest fixtures.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from huitzo_sdk import Context

from lead_engine.commands import add_lead, pipeline_report, score_lead, send_outreach
from lead_engine.models import AddLeadArgs, PipelineReportArgs, ScoreLeadArgs, SendOutreachArgs
from tests.conftest import MockEmailBackend, MockHTTPBackend, MockLLMBackend


# ---------------------------------------------------------------------------
# add-lead tests
# ---------------------------------------------------------------------------


class TestAddLead:
    async def test_add_lead_basic(self, ctx: Context) -> None:
        """Adding a lead returns the created record with a generated ID."""
        args = AddLeadArgs(
            company="Acme Corp",
            contact_name="Jane Doe",
            email="jane@acme.com",
            website="https://acme.com",
        )
        result = await add_lead(args, ctx)

        assert result["company"] == "Acme Corp"
        assert result["contact_name"] == "Jane Doe"
        assert result["email"] == "jane@acme.com"
        assert "lead_id" in result
        assert "created_at" in result

    async def test_add_lead_minimal(self, ctx: Context) -> None:
        """Adding a lead with only required fields works."""
        args = AddLeadArgs(
            company="MinCo",
            contact_name="Bob",
            email="bob@min.co",
        )
        result = await add_lead(args, ctx)

        assert result["company"] == "MinCo"
        assert result["enriched"] is False

    async def test_add_lead_stored_in_storage(self, ctx: Context) -> None:
        """Lead is persisted in storage and retrievable."""
        args = AddLeadArgs(
            company="StoreTest Inc",
            contact_name="Alice",
            email="alice@storetest.com",
        )
        result = await add_lead(args, ctx)
        lead_id = result["lead_id"]

        stored = await ctx.storage.get(f"lead:{lead_id}")
        assert stored is not None
        assert stored["company"] == "StoreTest Inc"
        assert stored["contact_name"] == "Alice"

    async def test_add_lead_with_enrichment(
        self, ctx: Context, http_backend: MockHTTPBackend
    ) -> None:
        """When HTTP returns enrichment data, the lead is marked as enriched."""
        http_backend.responses[
            "https://api.enrichment.example.com/v1/company"
        ] = {"industry": "Technology", "employees": 500}

        args = AddLeadArgs(
            company="TechCo",
            contact_name="Sam",
            email="sam@techco.io",
            website="https://techco.io",
        )
        result = await add_lead(args, ctx)
        assert result["enriched"] is True

    async def test_add_lead_enrichment_failure(
        self, ctx: Context, http_backend: MockHTTPBackend
    ) -> None:
        """HTTP failure for enrichment is handled gracefully."""
        http_backend.fail = True

        args = AddLeadArgs(
            company="FailCo",
            contact_name="Pat",
            email="pat@failco.com",
            website="https://failco.com",
        )
        result = await add_lead(args, ctx)
        assert result["enriched"] is False  # Graceful degradation

    async def test_add_lead_validation_empty_company(self) -> None:
        """Empty company name is rejected by validation."""
        with pytest.raises(Exception):
            AddLeadArgs(
                company="   ",
                contact_name="Test",
                email="test@test.com",
            )

    async def test_add_lead_validation_bad_email(self) -> None:
        """Invalid email is rejected by Pydantic validation."""
        with pytest.raises(Exception):
            AddLeadArgs(
                company="TestCo",
                contact_name="Test",
                email="not-an-email",
            )


# ---------------------------------------------------------------------------
# score-lead tests
# ---------------------------------------------------------------------------


class TestScoreLead:
    async def _create_lead(self, ctx: Context) -> str:
        """Helper: create a lead and return its ID."""
        args = AddLeadArgs(
            company="ScoreMe Inc",
            contact_name="Dana",
            email="dana@scoreme.com",
            notes="Enterprise SaaS company, 200 employees",
        )
        result = await add_lead(args, ctx)
        return result["lead_id"]

    async def test_score_lead_success(
        self, ctx: Context, llm_backend: MockLLMBackend
    ) -> None:
        """Scoring a lead returns a valid score and tier."""
        lead_id = await self._create_lead(ctx)

        llm_backend.responses.append(
            json.dumps(
                {
                    "score": 82,
                    "tier": "hot",
                    "reasoning": "Enterprise SaaS with strong fit.",
                    "strengths": ["Enterprise company", "200 employees"],
                    "concerns": ["No website provided"],
                }
            )
        )

        args = ScoreLeadArgs(lead_id=lead_id)
        result = await score_lead(args, ctx)

        assert result["score"] == 82
        assert result["tier"] == "hot"
        assert "reasoning" in result
        assert "strengths" in result
        assert "scored_at" in result

    async def test_score_lead_warm_tier(
        self, ctx: Context, llm_backend: MockLLMBackend
    ) -> None:
        """A moderate score results in warm tier."""
        lead_id = await self._create_lead(ctx)

        llm_backend.responses.append(
            json.dumps(
                {
                    "score": 55,
                    "tier": "warm",
                    "reasoning": "Potential fit but limited data.",
                    "strengths": ["Active company"],
                    "concerns": ["Small team", "Unclear budget"],
                }
            )
        )

        result = await score_lead(ScoreLeadArgs(lead_id=lead_id), ctx)
        assert result["tier"] == "warm"
        assert result["score"] == 55

    async def test_score_lead_cold_tier(
        self, ctx: Context, llm_backend: MockLLMBackend
    ) -> None:
        """A low score results in cold tier."""
        lead_id = await self._create_lead(ctx)

        llm_backend.responses.append(
            json.dumps(
                {
                    "score": 20,
                    "tier": "cold",
                    "reasoning": "Low fit based on available data.",
                    "strengths": [],
                    "concerns": ["No website", "Generic email"],
                }
            )
        )

        result = await score_lead(ScoreLeadArgs(lead_id=lead_id), ctx)
        assert result["tier"] == "cold"
        assert result["score"] == 20

    async def test_score_lead_not_found(self, ctx: Context) -> None:
        """Scoring a non-existent lead raises CommandError."""
        from huitzo_sdk.errors import CommandError

        with pytest.raises(CommandError, match="not found"):
            await score_lead(ScoreLeadArgs(lead_id="nonexistent"), ctx)

    async def test_score_updates_storage(
        self, ctx: Context, llm_backend: MockLLMBackend
    ) -> None:
        """After scoring, the lead record in storage is updated."""
        lead_id = await self._create_lead(ctx)

        llm_backend.responses.append(
            json.dumps(
                {
                    "score": 90,
                    "tier": "hot",
                    "reasoning": "Excellent fit.",
                    "strengths": ["Top tier"],
                    "concerns": [],
                }
            )
        )

        await score_lead(ScoreLeadArgs(lead_id=lead_id), ctx)

        stored = await ctx.storage.get(f"lead:{lead_id}")
        assert stored["score"] == 90
        assert stored["tier"] == "hot"
        assert stored["scored_at"] is not None


# ---------------------------------------------------------------------------
# send-outreach tests
# ---------------------------------------------------------------------------


class TestSendOutreach:
    async def _create_and_score_lead(
        self, ctx: Context, llm_backend: MockLLMBackend
    ) -> str:
        """Helper: create and score a lead, return its ID."""
        args = AddLeadArgs(
            company="OutreachCo",
            contact_name="Morgan",
            email="morgan@outreachco.com",
            website="https://outreachco.com",
        )
        result = await add_lead(args, ctx)
        lead_id = result["lead_id"]

        llm_backend.responses.append(
            json.dumps(
                {
                    "score": 85,
                    "tier": "hot",
                    "reasoning": "Great fit.",
                    "strengths": ["Strong company"],
                    "concerns": [],
                }
            )
        )
        await score_lead(ScoreLeadArgs(lead_id=lead_id), ctx)
        return lead_id

    async def test_send_intro_email(
        self, ctx: Context, llm_backend: MockLLMBackend, email_backend: MockEmailBackend
    ) -> None:
        """Sending intro template delivers an email."""
        lead_id = await self._create_and_score_lead(ctx, llm_backend)

        # LLM response for personalization
        llm_backend.responses.append("I noticed OutreachCo is doing great work.")

        args = SendOutreachArgs(lead_id=lead_id, template_name="intro")
        result = await send_outreach(args, ctx)

        assert result["template"] == "intro"
        assert result["email"] == "morgan@outreachco.com"
        assert "sent_at" in result
        assert len(email_backend.sent) == 1
        assert "OutreachCo" in email_backend.sent[0]["subject"] or "Morgan" in email_backend.sent[0]["subject"]

    async def test_send_follow_up_email(
        self, ctx: Context, llm_backend: MockLLMBackend, email_backend: MockEmailBackend
    ) -> None:
        """Sending follow-up template works."""
        lead_id = await self._create_and_score_lead(ctx, llm_backend)
        llm_backend.responses.append("Following up on our conversation.")

        result = await send_outreach(
            SendOutreachArgs(lead_id=lead_id, template_name="follow-up"), ctx
        )
        assert result["template"] == "follow-up"
        assert len(email_backend.sent) == 1

    async def test_send_demo_invite_email(
        self, ctx: Context, llm_backend: MockLLMBackend, email_backend: MockEmailBackend
    ) -> None:
        """Sending demo-invite template works."""
        lead_id = await self._create_and_score_lead(ctx, llm_backend)
        llm_backend.responses.append("Your team would love our demo.")

        result = await send_outreach(
            SendOutreachArgs(lead_id=lead_id, template_name="demo-invite"), ctx
        )
        assert result["template"] == "demo-invite"
        assert len(email_backend.sent) == 1

    async def test_send_outreach_not_found(self, ctx: Context) -> None:
        """Sending outreach for non-existent lead raises CommandError."""
        from huitzo_sdk.errors import CommandError

        with pytest.raises(CommandError, match="not found"):
            await send_outreach(
                SendOutreachArgs(lead_id="ghost", template_name="intro"), ctx
            )

    async def test_outreach_marks_lead_as_contacted(
        self, ctx: Context, llm_backend: MockLLMBackend
    ) -> None:
        """After outreach, the lead record shows outreach_sent=True."""
        lead_id = await self._create_and_score_lead(ctx, llm_backend)
        llm_backend.responses.append("Personalized line.")

        await send_outreach(
            SendOutreachArgs(lead_id=lead_id, template_name="intro"), ctx
        )

        stored = await ctx.storage.get(f"lead:{lead_id}")
        assert stored["outreach_sent"] is True
        assert stored["outreach_at"] is not None

    async def test_outreach_without_llm_personalization(
        self, ctx: Context, llm_backend: MockLLMBackend, email_backend: MockEmailBackend
    ) -> None:
        """If LLM personalization fails, the base template is still sent."""
        lead_id = await self._create_and_score_lead(ctx, llm_backend)

        # Make LLM fail for personalization
        llm_backend.responses.clear()
        llm_backend._call_count = 0

        # The command catches LLM exceptions for personalization, so we need
        # to make the mock raise an exception for the personalization call.
        # Since _create_and_score_lead consumed calls, the default response
        # will be used, which is valid JSON. We need to override.
        original_complete = llm_backend.complete

        call_count = 0

        async def failing_complete(**kwargs: Any) -> str:
            nonlocal call_count
            call_count += 1
            # First call in send_outreach is personalization
            if call_count == 1:
                raise RuntimeError("LLM unavailable")
            return await original_complete(**kwargs)

        llm_backend.complete = failing_complete  # type: ignore[assignment]

        result = await send_outreach(
            SendOutreachArgs(lead_id=lead_id, template_name="intro"), ctx
        )
        assert result["template"] == "intro"
        assert len(email_backend.sent) == 1  # Email still sent


# ---------------------------------------------------------------------------
# pipeline-report tests
# ---------------------------------------------------------------------------


class TestPipelineReport:
    async def _seed_leads(
        self, ctx: Context, llm_backend: MockLLMBackend
    ) -> None:
        """Create several leads with different tiers."""
        leads = [
            ("HotCo", "Alice", "alice@hot.co", 85, "hot"),
            ("WarmCo", "Bob", "bob@warm.co", 55, "warm"),
            ("ColdCo", "Charlie", "charlie@cold.co", 20, "cold"),
            ("UnscoredCo", "Dana", "dana@unscored.co", None, None),
        ]

        for company, name, email, score, tier in leads:
            result = await add_lead(
                AddLeadArgs(company=company, contact_name=name, email=email), ctx
            )
            if score is not None:
                llm_backend.responses.append(
                    json.dumps(
                        {
                            "score": score,
                            "tier": tier,
                            "reasoning": f"Score for {company}",
                            "strengths": [],
                            "concerns": [],
                        }
                    )
                )
                await score_lead(ScoreLeadArgs(lead_id=result["lead_id"]), ctx)

    async def test_pipeline_report_counts(
        self, ctx: Context, llm_backend: MockLLMBackend
    ) -> None:
        """Pipeline report counts leads by tier correctly."""
        await self._seed_leads(ctx, llm_backend)

        # LLM response for report summary
        llm_backend.responses.append(
            "Focus on HotCo for immediate outreach. Nurture WarmCo with content."
        )

        result = await pipeline_report(PipelineReportArgs(), ctx)

        assert result["total_leads"] == 4
        assert result["hot_leads"] == 1
        assert result["warm_leads"] == 1
        assert result["cold_leads"] == 1
        assert result["unscored_leads"] == 1
        assert "summary" in result

    async def test_pipeline_report_with_details(
        self, ctx: Context, llm_backend: MockLLMBackend
    ) -> None:
        """Pipeline report with include_details shows lead breakdowns."""
        await self._seed_leads(ctx, llm_backend)
        llm_backend.responses.append("Summary text.")

        result = await pipeline_report(PipelineReportArgs(include_details=True), ctx)

        assert "leads" in result
        assert len(result["leads"]["hot"]) == 1
        assert len(result["leads"]["warm"]) == 1
        assert len(result["leads"]["cold"]) == 1
        assert len(result["leads"]["unscored"]) == 1
        assert result["leads"]["hot"][0]["company"] == "HotCo"

    async def test_pipeline_report_empty(self, ctx: Context) -> None:
        """Pipeline report with no leads returns zero counts."""
        result = await pipeline_report(PipelineReportArgs(), ctx)

        assert result["total_leads"] == 0
        assert result["hot_leads"] == 0
        assert "summary" in result

    async def test_pipeline_report_llm_failure(
        self, ctx: Context, llm_backend: MockLLMBackend
    ) -> None:
        """If LLM fails for summary, a fallback summary is used."""
        await self._seed_leads(ctx, llm_backend)

        # Override LLM to fail
        original_complete = llm_backend.complete

        async def failing_complete(**kwargs: Any) -> str:
            raise RuntimeError("LLM unavailable")

        llm_backend.complete = failing_complete  # type: ignore[assignment]

        result = await pipeline_report(PipelineReportArgs(), ctx)

        # Should still succeed with fallback summary
        assert result["total_leads"] == 4
        assert "summary" in result
        assert "4 leads" in result["summary"]


# ---------------------------------------------------------------------------
# Full workflow integration test
# ---------------------------------------------------------------------------


class TestFullWorkflow:
    async def test_add_score_outreach_report(
        self,
        ctx: Context,
        llm_backend: MockLLMBackend,
        email_backend: MockEmailBackend,
    ) -> None:
        """Full workflow: add -> score -> outreach -> report."""
        # 1. Add a lead
        add_result = await add_lead(
            AddLeadArgs(
                company="FullFlow Inc",
                contact_name="Jordan",
                email="jordan@fullflow.com",
                website="https://fullflow.com",
                notes="Met at conference, VP of Engineering",
            ),
            ctx,
        )
        lead_id = add_result["lead_id"]
        assert lead_id

        # 2. Score the lead
        llm_backend.responses.append(
            json.dumps(
                {
                    "score": 92,
                    "tier": "hot",
                    "reasoning": "VP-level contact at established company met in person.",
                    "strengths": [
                        "VP of Engineering contact",
                        "In-person meeting",
                        "Has website",
                    ],
                    "concerns": [],
                }
            )
        )

        score_result = await score_lead(ScoreLeadArgs(lead_id=lead_id), ctx)
        assert score_result["score"] == 92
        assert score_result["tier"] == "hot"

        # 3. Send outreach
        llm_backend.responses.append(
            "It was great meeting you at the conference last week!"
        )

        outreach_result = await send_outreach(
            SendOutreachArgs(lead_id=lead_id, template_name="intro"), ctx
        )
        assert outreach_result["email"] == "jordan@fullflow.com"
        assert len(email_backend.sent) == 1

        # 4. Pipeline report
        llm_backend.responses.append(
            "One hot lead (FullFlow Inc) has been contacted. Follow up within 48 hours."
        )

        report_result = await pipeline_report(
            PipelineReportArgs(include_details=True), ctx
        )
        assert report_result["total_leads"] == 1
        assert report_result["hot_leads"] == 1
        assert report_result["outreach_sent"] == 1
        assert report_result["leads"]["hot"][0]["company"] == "FullFlow Inc"
