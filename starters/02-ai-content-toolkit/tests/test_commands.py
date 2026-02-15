"""
Tests for the ai-content-toolkit pack commands.

Implements:
    - docs/sdk/commands.md#testing-commands

Tests cover:
    - Pydantic argument validation for all three commands
    - Command execution with mocked LLM Context
    - Structured output parsing (SummaryResponse, EntitiesResponse, RewriteResponse)
    - Edge cases (max bullets, invalid tones, short text)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from ai_content_toolkit.commands import (
    ExtractEntitiesArgs,
    RewriteArgs,
    Sentiment,
    SummarizeArgs,
    Tone,
    extract_entities,
    rewrite,
    summarize,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_ctx(llm_response: dict[str, Any] | None = None) -> MagicMock:
    """Build a mock Context with a configurable LLM response."""
    ctx = MagicMock()
    ctx.llm.complete = AsyncMock(return_value=llm_response or {})
    ctx.log = MagicMock()
    return ctx


# ---------------------------------------------------------------------------
# SummarizeArgs validation
# ---------------------------------------------------------------------------


class TestSummarizeArgs:
    """Validate SummarizeArgs Pydantic model."""

    def test_valid(self) -> None:
        args = SummarizeArgs(text="This is a long enough text to summarize properly.")
        assert args.max_bullets == 5  # default

    def test_custom_max_bullets(self) -> None:
        args = SummarizeArgs(
            text="This is a long enough text to summarize properly.",
            max_bullets=3,
        )
        assert args.max_bullets == 3

    def test_text_too_short_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SummarizeArgs(text="Too short")

    def test_zero_bullets_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SummarizeArgs(
                text="This is a long enough text to summarize properly.",
                max_bullets=0,
            )

    def test_too_many_bullets_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SummarizeArgs(
                text="This is a long enough text to summarize properly.",
                max_bullets=21,
            )


# ---------------------------------------------------------------------------
# ExtractEntitiesArgs validation
# ---------------------------------------------------------------------------


class TestExtractEntitiesArgs:
    """Validate ExtractEntitiesArgs Pydantic model."""

    def test_valid(self) -> None:
        args = ExtractEntitiesArgs(text="John Smith met with Apple Inc in New York on January 5th.")
        assert len(args.text) > 10

    def test_text_too_short_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ExtractEntitiesArgs(text="Too short")


# ---------------------------------------------------------------------------
# RewriteArgs validation
# ---------------------------------------------------------------------------


class TestRewriteArgs:
    """Validate RewriteArgs Pydantic model."""

    def test_valid_with_default_tone(self) -> None:
        args = RewriteArgs(text="This text needs to be rewritten in a different style.")
        assert args.tone == Tone.FORMAL

    def test_valid_casual(self) -> None:
        args = RewriteArgs(
            text="This text needs to be rewritten in a different style.",
            tone=Tone.CASUAL,
        )
        assert args.tone == Tone.CASUAL

    def test_valid_technical(self) -> None:
        args = RewriteArgs(
            text="This text needs to be rewritten in a different style.",
            tone=Tone.TECHNICAL,
        )
        assert args.tone == Tone.TECHNICAL

    def test_text_too_short_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RewriteArgs(text="Too short")

    def test_invalid_tone_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RewriteArgs(
                text="This text needs to be rewritten in a different style.",
                tone="poetic",  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------------
# Tone enum
# ---------------------------------------------------------------------------


class TestTone:
    """Test Tone enum values."""

    def test_all_values(self) -> None:
        assert Tone.FORMAL.value == "formal"
        assert Tone.CASUAL.value == "casual"
        assert Tone.TECHNICAL.value == "technical"

    def test_count(self) -> None:
        assert len(Tone) == 3


# ---------------------------------------------------------------------------
# Sentiment enum
# ---------------------------------------------------------------------------


class TestSentiment:
    """Test Sentiment enum values."""

    def test_all_values(self) -> None:
        assert Sentiment.POSITIVE.value == "positive"
        assert Sentiment.NEGATIVE.value == "negative"
        assert Sentiment.NEUTRAL.value == "neutral"
        assert Sentiment.MIXED.value == "mixed"


# ---------------------------------------------------------------------------
# summarize command
# ---------------------------------------------------------------------------


class TestSummarize:
    """Test summarize command execution with mocked LLM."""

    @pytest.mark.asyncio
    async def test_summarizes_text(self) -> None:
        llm_response = {
            "bullets": ["Point one", "Point two", "Point three"],
            "sentiment": "positive",
        }
        ctx = _make_ctx(llm_response)
        args = SummarizeArgs(text="This is a sufficiently long text to summarize for testing.")

        result = await summarize(args, ctx)

        assert len(result["bullets"]) == 3
        assert result["sentiment"] == "positive"
        assert result["word_count"] > 0
        ctx.llm.complete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_respects_max_bullets(self) -> None:
        llm_response = {
            "bullets": ["A", "B", "C", "D", "E", "F"],
            "sentiment": "neutral",
        }
        ctx = _make_ctx(llm_response)
        args = SummarizeArgs(
            text="This is a sufficiently long text to summarize for testing.",
            max_bullets=3,
        )

        result = await summarize(args, ctx)

        assert len(result["bullets"]) <= 3

    @pytest.mark.asyncio
    async def test_defaults_sentiment_to_neutral(self) -> None:
        llm_response = {"bullets": ["Point one"]}
        ctx = _make_ctx(llm_response)
        args = SummarizeArgs(text="This is a sufficiently long text to summarize for testing.")

        result = await summarize(args, ctx)

        assert result["sentiment"] == "neutral"


# ---------------------------------------------------------------------------
# extract_entities command
# ---------------------------------------------------------------------------


class TestExtractEntities:
    """Test extract_entities command execution with mocked LLM."""

    @pytest.mark.asyncio
    async def test_extracts_entities(self) -> None:
        llm_response = {
            "entities": [
                {"text": "John Smith", "type": "person"},
                {"text": "Apple Inc", "type": "company"},
                {"text": "New York", "type": "location"},
                {"text": "January 5th", "type": "date"},
            ]
        }
        ctx = _make_ctx(llm_response)
        args = ExtractEntitiesArgs(
            text="John Smith met with Apple Inc in New York on January 5th."
        )

        result = await extract_entities(args, ctx)

        assert len(result["entities"]) == 4
        assert result["people"] == ["John Smith"]
        assert result["companies"] == ["Apple Inc"]
        assert result["locations"] == ["New York"]
        assert result["dates"] == ["January 5th"]

    @pytest.mark.asyncio
    async def test_empty_entities(self) -> None:
        llm_response = {"entities": []}
        ctx = _make_ctx(llm_response)
        args = ExtractEntitiesArgs(
            text="No named entities in this boring sentence at all."
        )

        result = await extract_entities(args, ctx)

        assert result["entities"] == []
        assert result["people"] == []
        assert result["companies"] == []


# ---------------------------------------------------------------------------
# rewrite command
# ---------------------------------------------------------------------------


class TestRewrite:
    """Test rewrite command execution with mocked LLM."""

    @pytest.mark.asyncio
    async def test_rewrites_text(self) -> None:
        llm_response = {"rewritten": "The quarterly results were satisfactory."}
        ctx = _make_ctx(llm_response)
        args = RewriteArgs(
            text="The Q1 numbers were pretty good, honestly.",
            tone=Tone.FORMAL,
        )

        result = await rewrite(args, ctx)

        assert result["original"] == "The Q1 numbers were pretty good, honestly."
        assert result["rewritten"] == "The quarterly results were satisfactory."
        assert result["tone"] == "formal"

    @pytest.mark.asyncio
    async def test_preserves_original(self) -> None:
        llm_response = {"rewritten": "Hey, the numbers look great!"}
        ctx = _make_ctx(llm_response)
        original = "The quarterly results exceeded expectations across all segments."
        args = RewriteArgs(text=original, tone=Tone.CASUAL)

        result = await rewrite(args, ctx)

        assert result["original"] == original

    @pytest.mark.asyncio
    async def test_falls_back_to_original_on_empty_response(self) -> None:
        llm_response = {}  # missing "rewritten" key
        ctx = _make_ctx(llm_response)
        original = "This text should be returned as-is when LLM returns nothing."
        args = RewriteArgs(text=original, tone=Tone.TECHNICAL)

        result = await rewrite(args, ctx)

        assert result["rewritten"] == original
