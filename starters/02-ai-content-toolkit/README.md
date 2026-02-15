# 02 - AI Content Toolkit

**Difficulty:** Beginner+ | **Time:** 15 minutes | **Prerequisites:** Complete [01-smart-notes](../01-smart-notes/) first

Build AI-powered text processing commands using Huitzo's LLM integration. This template teaches you how to call AI models and get structured responses back.

---

## What You Will Learn

1. **`ctx.llm.complete()`** - How to call AI models from your commands
2. **Structured outputs** - Enforce response schemas with Pydantic models
3. **Model selection** - Choosing the right model (gpt-4o-mini as default)
4. **Temperature control** - Tuning creativity vs. consistency
5. **Response validation** - Parsing and validating LLM output

## Commands

| Command | Description | Arguments |
|---------|-------------|-----------|
| `summarize` | Summarize text with bullet points + sentiment | `text` (str), `max_bullets` (int, default 5) |
| `extract-entities` | Extract people, companies, dates, locations | `text` (str) |
| `rewrite` | Rewrite text in a different tone | `text` (str), `tone` (formal/casual/technical) |

## Quick Start

```bash
# 1. Navigate to this template
cd starters/02-ai-content-toolkit

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Start the dev server (uses mock LLM in dev mode)
huitzo pack dev

# 4. Summarize some text
curl -X POST http://localhost:8080/api/v1/commands/content/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Huitzo is the Operating System for Intelligence. It lets developers build smart, AI-powered services using a simple Python SDK.",
    "max_bullets": 3
  }'
```

## Run Tests

```bash
cd starters/02-ai-content-toolkit
pytest -v
```

## Project Structure

```
02-ai-content-toolkit/
├── README.md              # This file
├── tutorial.md             # Step-by-step walkthrough
├── pyproject.toml          # Dependencies and entry points
├── huitzo.yaml             # Pack manifest
├── .env.example            # Optional API key configuration
├── src/
│   └── ai_content_toolkit/
│       ├── __init__.py
│       └── commands.py     # All 3 commands
├── tests/
│   └── test_commands.py    # Validation + mocked LLM tests
└── examples/
    └── test-commands.sh    # Curl examples to test all endpoints
```

## Services Used

- **LLM** - `ctx.llm.complete()` with `response_format="json"` for structured outputs

## API Keys

**No API key is required for local development.** The dev server uses a mock LLM.

To use real AI models, set your API key in `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
```

## Next Step

Once you are comfortable with LLM integration, move on to:
**[03-data-cruncher](../03-data-cruncher/)** - Combine storage, LLM, and file handling
