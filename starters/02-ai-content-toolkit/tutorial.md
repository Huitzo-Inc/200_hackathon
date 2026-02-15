# Tutorial: AI Content Toolkit

**Goal:** Build 3 AI-powered text commands using `ctx.llm.complete()` in 15 minutes.

**Prerequisite:** Complete [01-smart-notes](../01-smart-notes/) first to learn `@command` basics.

---

## Step 1: What is LLM Integration?

In Smart Notes, you used `ctx.storage` to save and retrieve data. Now you will use `ctx.llm` to call AI models directly from your commands.

```python
# Smart Notes used storage:
await ctx.storage.set("note:title", data)

# AI Content Toolkit uses LLM:
response = await ctx.llm.complete(
    prompt="Summarize this text: ...",
    model="gpt-4o-mini",
    response_format="json",
    temperature=0.3,
)
```

The key difference: `ctx.llm.complete()` sends a prompt to an AI model and returns structured data.

## Step 2: The `ctx.llm.complete()` API

```python
response = await ctx.llm.complete(
    prompt="...",              # What you want the AI to do
    system="...",              # Role instructions for the AI
    model="gpt-4o-mini",      # Which model to use
    response_format="json",   # Force JSON output
    temperature=0.3,           # 0.0 = deterministic, 1.0 = creative
)
```

**Parameters explained:**

| Parameter | Purpose | Typical Values |
|-----------|---------|---------------|
| `prompt` | The instruction to the AI | Your text + formatting instructions |
| `system` | Role/behavior instructions | "You are a concise analyst..." |
| `model` | Which AI model to use | `"gpt-4o-mini"` (fast, cheap), `"gpt-4o"` (more capable) |
| `response_format` | Output format | `"json"` for structured data |
| `temperature` | Creativity level | `0.1`-`0.3` for analysis, `0.7`-`0.9` for creative tasks |

## Step 3: Building the Summarize Command

Open `src/ai_content_toolkit/commands.py` and look at the summarize command:

```python
class SummarizeArgs(BaseModel):
    text: str = Field(min_length=10, max_length=50_000)
    max_bullets: int = Field(default=5, ge=1, le=20)

@command("summarize", namespace="content", timeout=60, queue="medium")
async def summarize(args: SummarizeArgs, ctx: Context) -> dict[str, Any]:
    word_count = len(args.text.split())

    prompt = f"""Summarize the following text into at most {args.max_bullets} bullet points.
Also classify the overall sentiment as: positive, negative, neutral, mixed.

Text:
{args.text}

Respond as JSON:
{{
    "bullets": ["bullet 1", "bullet 2", ...],
    "sentiment": "positive" | "negative" | "neutral" | "mixed"
}}"""

    response = await ctx.llm.complete(
        prompt=prompt,
        system="You are a concise text analyst...",
        model="gpt-4o-mini",
        response_format="json",
        temperature=0.3,
    )

    # Parse into a Pydantic model for validation
    result = SummaryResponse(
        bullets=response.get("bullets", [])[:args.max_bullets],
        sentiment=response.get("sentiment", "neutral"),
        word_count=word_count,
    )

    return result.model_dump()
```

**Key patterns:**

1. **Prompt engineering** - Tell the AI exactly what JSON structure you want
2. **Response parsing** - Use `.get()` with defaults for resilience
3. **Pydantic validation** - Validate the AI's response with a response model
4. **Truncation** - Enforce `max_bullets` even if the AI returns more

## Step 4: Structured Responses with Pydantic

The response models ensure AI output matches your expected schema:

```python
class SummaryResponse(BaseModel):
    bullets: list[str] = Field(description="Key points")
    sentiment: Sentiment = Field(description="Overall sentiment")
    word_count: int = Field(ge=0, description="Original word count")
```

If the AI returns invalid data, Pydantic catches it. This is much safer than trusting raw AI output.

## Step 5: Entity Extraction

The `extract-entities` command shows how to work with nested response models:

```python
class Entity(BaseModel):
    text: str = Field(description="Entity text")
    type: str = Field(description="person, company, date, or location")

class EntitiesResponse(BaseModel):
    entities: list[Entity]
    people: list[str]
    companies: list[str]
    dates: list[str]
    locations: list[str]
```

After getting entities from the LLM, we sort them into categories:

```python
entities = [Entity.model_validate(e) for e in response.get("entities", [])]

result = EntitiesResponse(
    entities=entities,
    people=[e.text for e in entities if e.type == "person"],
    companies=[e.text for e in entities if e.type == "company"],
    # ...
)
```

## Step 6: Tone Rewriting with Enums

The `rewrite` command uses an Enum to restrict valid tones:

```python
class Tone(str, Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"

class RewriteArgs(BaseModel):
    text: str = Field(min_length=10, max_length=50_000)
    tone: Tone = Field(default=Tone.FORMAL)
```

If someone sends `{"tone": "poetic"}`, Pydantic rejects it automatically.

The tone choice also controls the prompt instructions:

```python
tone_instructions = {
    Tone.FORMAL: "Use professional, polished language...",
    Tone.CASUAL: "Use friendly, conversational language...",
    Tone.TECHNICAL: "Use precise, technical language...",
}
```

## Step 7: Testing with Mock LLM

You never want to call real AI models in tests. Instead, mock `ctx.llm.complete()`:

```python
from unittest.mock import AsyncMock, MagicMock

ctx = MagicMock()
ctx.llm.complete = AsyncMock(return_value={
    "bullets": ["Point one", "Point two"],
    "sentiment": "positive",
})
ctx.log = MagicMock()

args = SummarizeArgs(text="Sufficiently long text for summarization testing.")
result = await summarize(args, ctx)

assert len(result["bullets"]) == 2
assert result["sentiment"] == "positive"
```

Run the tests:
```bash
pytest -v
```

## Step 8: Start the Dev Server

```bash
huitzo pack dev
```

Test with curl:
```bash
# Summarize
curl -X POST http://localhost:8080/api/v1/commands/content/summarize \
  -H "Content-Type: application/json" \
  -d '{"text":"Long text here...","max_bullets":3}'

# Extract entities
curl -X POST http://localhost:8080/api/v1/commands/content/extract-entities \
  -H "Content-Type: application/json" \
  -d '{"text":"John met Sarah at Google HQ on March 15."}'

# Rewrite
curl -X POST http://localhost:8080/api/v1/commands/content/rewrite \
  -H "Content-Type: application/json" \
  -d '{"text":"The app got faster.","tone":"technical"}'
```

## Step 9: Experiment

1. **Add a `classify` command** that categorizes text into topics (tech, business, sports, etc.)
2. **Change the temperature** in the summarize command to 0.9 and see how responses vary
3. **Add a `word_limit` argument** to the rewrite command to control output length
4. **Try a different model** by changing `model="gpt-4o"` for better quality results

## What You Learned

- `ctx.llm.complete()` calls AI models and returns structured data
- `response_format="json"` forces the AI to return parseable JSON
- `temperature` controls the balance between consistency and creativity
- Pydantic response models validate AI output just like input validation
- Mock `ctx.llm.complete` in tests to avoid real API calls

## Next Step

Move on to **[03-data-cruncher](../03-data-cruncher/)** to learn file handling and multi-command workflows.
