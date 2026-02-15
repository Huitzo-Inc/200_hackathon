"""
AI Content Toolkit Pack Commands.

Implements:
    - docs/sdk/commands.md#the-command-decorator
    - docs/sdk/integrations.md#llm-integration
    - docs/sdk/context.md#llm-api

This module provides three AI-powered content commands:
    - summarize: Summarize text with bullet points and sentiment
    - extract-entities: Extract people, companies, dates, locations
    - rewrite: Rewrite text in a different tone

See Also:
    - docs/sdk/context.md (for Context API)
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# SDK placeholder types (replaced at runtime by huitzo-sdk)
# ---------------------------------------------------------------------------

if TYPE_CHECKING:

    class LLMService(Protocol):
        """Protocol for the Huitzo LLM service."""

        async def complete(
            self,
            prompt: str,
            system: str | None = None,
            model: str = "gpt-4o-mini",
            response_model: type[BaseModel] | None = None,
            response_format: str | None = None,
            temperature: float = 0.7,
        ) -> Any: ...

    class LogService(Protocol):
        """Protocol for the Huitzo logging service."""

        def info(self, message: str) -> None: ...
        def warning(self, message: str) -> None: ...
        def error(self, message: str) -> None: ...

    class Context(Protocol):
        """Protocol for the Huitzo execution context."""

        llm: LLMService
        log: LogService


def command(
    name: str,
    *,
    namespace: str,
    timeout: int = 60,
    retries: int = 3,
    queue: str = "default",
) -> Any:
    """Decorator placeholder for the @command pattern."""

    def decorator(func: Any) -> Any:
        func._command_name = name
        func._command_namespace = namespace
        func._command_timeout = timeout
        func._command_retries = retries
        func._command_queue = queue
        return func

    return decorator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Tone(str, Enum):
    """Available rewrite tones."""

    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"


class Sentiment(str, Enum):
    """Sentiment classification."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


# ---------------------------------------------------------------------------
# Argument Models
# ---------------------------------------------------------------------------


class SummarizeArgs(BaseModel):
    """Arguments for the summarize command."""

    text: str = Field(
        min_length=10,
        max_length=50_000,
        description="Text to summarize",
    )
    max_bullets: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of bullet points in the summary",
    )


class ExtractEntitiesArgs(BaseModel):
    """Arguments for the extract-entities command."""

    text: str = Field(
        min_length=10,
        max_length=50_000,
        description="Text to extract entities from",
    )


class RewriteArgs(BaseModel):
    """Arguments for the rewrite command."""

    text: str = Field(
        min_length=10,
        max_length=50_000,
        description="Text to rewrite",
    )
    tone: Tone = Field(
        default=Tone.FORMAL,
        description="Target tone for the rewrite",
    )


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class SummaryResponse(BaseModel):
    """Structured response from the summarize command."""

    bullets: list[str] = Field(description="Key points as bullet strings")
    sentiment: Sentiment = Field(description="Overall sentiment of the text")
    word_count: int = Field(ge=0, description="Word count of the original text")


class Entity(BaseModel):
    """A single extracted entity."""

    text: str = Field(description="The entity text as it appears in the input")
    type: str = Field(description="Entity type: person, company, date, or location")


class EntitiesResponse(BaseModel):
    """Structured response from the extract-entities command."""

    entities: list[Entity] = Field(description="Extracted entities")
    people: list[str] = Field(description="Person names found")
    companies: list[str] = Field(description="Company names found")
    dates: list[str] = Field(description="Date references found")
    locations: list[str] = Field(description="Location references found")


class RewriteResponse(BaseModel):
    """Structured response from the rewrite command."""

    original: str = Field(description="The original text")
    rewritten: str = Field(description="The rewritten text")
    tone: str = Field(description="The tone used for rewriting")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@command("summarize", namespace="content", timeout=60, queue="medium")
async def summarize(args: SummarizeArgs, ctx: Context) -> dict[str, Any]:
    """Summarize text with bullet points and sentiment analysis.

    Uses the LLM to produce a concise summary with key bullet points and
    an overall sentiment classification.

    Args:
        args: Text to summarize and max bullet count.
        ctx: Huitzo context providing LLM and logging.

    Returns:
        Summary with bullets, sentiment, and word count.
    """
    word_count = len(args.text.split())

    prompt = f"""Summarize the following text into at most {args.max_bullets} bullet points.
Also classify the overall sentiment as one of: positive, negative, neutral, mixed.

Text:
{args.text}

Respond as JSON:
{{
    "bullets": ["bullet 1", "bullet 2", ...],
    "sentiment": "positive" | "negative" | "neutral" | "mixed"
}}"""

    system = (
        "You are a concise text analyst. Extract key points as short bullet strings. "
        "Classify sentiment accurately. Always respond with valid JSON."
    )

    response = await ctx.llm.complete(
        prompt=prompt,
        system=system,
        model="gpt-4o-mini",
        response_format="json",
        temperature=0.3,
    )

    # Ensure bullets are within limit
    bullets = response.get("bullets", [])[:args.max_bullets]

    result = SummaryResponse(
        bullets=bullets,
        sentiment=response.get("sentiment", "neutral"),
        word_count=word_count,
    )

    ctx.log.info(
        f"Summarized {word_count} words into {len(result.bullets)} bullets "
        f"(sentiment={result.sentiment.value})"
    )

    return result.model_dump()


@command("extract-entities", namespace="content", timeout=60, queue="medium")
async def extract_entities(args: ExtractEntitiesArgs, ctx: Context) -> dict[str, Any]:
    """Extract named entities from text.

    Uses the LLM to identify people, companies, dates, and locations
    mentioned in the input text.

    Args:
        args: Text to extract entities from.
        ctx: Huitzo context providing LLM and logging.

    Returns:
        Categorized entities found in the text.
    """
    prompt = f"""Extract all named entities from the following text.
Categorize each as: person, company, date, or location.

Text:
{args.text}

Respond as JSON:
{{
    "entities": [
        {{"text": "entity text", "type": "person|company|date|location"}}
    ]
}}"""

    system = (
        "You are a precise named-entity extractor. "
        "Only extract entities that are explicitly mentioned. "
        "Always respond with valid JSON."
    )

    response = await ctx.llm.complete(
        prompt=prompt,
        system=system,
        model="gpt-4o-mini",
        response_format="json",
        temperature=0.1,
    )

    entities = [Entity.model_validate(e) for e in response.get("entities", [])]

    result = EntitiesResponse(
        entities=entities,
        people=[e.text for e in entities if e.type == "person"],
        companies=[e.text for e in entities if e.type == "company"],
        dates=[e.text for e in entities if e.type == "date"],
        locations=[e.text for e in entities if e.type == "location"],
    )

    ctx.log.info(f"Extracted {len(entities)} entities from text")

    return result.model_dump()


@command("rewrite", namespace="content", timeout=60, queue="medium")
async def rewrite(args: RewriteArgs, ctx: Context) -> dict[str, Any]:
    """Rewrite text in a different tone.

    Uses the LLM to rewrite the input text in the specified tone
    (formal, casual, or technical).

    Args:
        args: Text and target tone.
        ctx: Huitzo context providing LLM and logging.

    Returns:
        Original and rewritten text with the tone used.
    """
    tone_instructions = {
        Tone.FORMAL: "Use professional, polished language. Avoid contractions and slang.",
        Tone.CASUAL: "Use friendly, conversational language. Contractions are fine.",
        Tone.TECHNICAL: "Use precise, technical language. Include domain-specific terms where appropriate.",
    }

    prompt = f"""Rewrite the following text in a {args.tone.value} tone.

Instructions: {tone_instructions[args.tone]}

Original text:
{args.text}

Respond as JSON:
{{
    "rewritten": "the rewritten text"
}}"""

    system = (
        "You are a skilled writer who can adapt text to different tones "
        "while preserving the original meaning. Always respond with valid JSON."
    )

    response = await ctx.llm.complete(
        prompt=prompt,
        system=system,
        model="gpt-4o-mini",
        response_format="json",
        temperature=0.7,
    )

    result = RewriteResponse(
        original=args.text,
        rewritten=response.get("rewritten", args.text),
        tone=args.tone.value,
    )

    ctx.log.info(f"Rewrote text in {args.tone.value} tone")

    return result.model_dump()
