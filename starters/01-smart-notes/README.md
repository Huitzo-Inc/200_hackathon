# 01 - Smart Notes

**Difficulty:** Beginner | **Time:** 10 minutes | **Prerequisites:** Python 3.11+

Build a personal notes system using Huitzo's storage API. This is the simplest Intelligence Pack possible and the best starting point for learning Huitzo.

---

## What You Will Learn

1. **`@command` decorator** - How to register functions as API endpoints
2. **`ctx.storage`** - Huitzo's built-in key-value storage (set, get, list, delete)
3. **Pydantic validation** - Automatic input validation with `Field` constraints
4. **`ctx.log`** - Structured logging inside commands

## Commands

| Command | Description | Arguments |
|---------|-------------|-----------|
| `save-note` | Save or update a note | `title` (str), `content` (str) |
| `get-note` | Retrieve a note by title | `title` (str) |
| `list-notes` | List all saved notes | `limit` (int, default 10) |
| `delete-note` | Delete a note by title | `title` (str) |

## Quick Start

```bash
# 1. Navigate to this template
cd starters/01-smart-notes

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Start the dev server
huitzo pack dev

# 4. Test a command (in another terminal)
curl -X POST http://localhost:8080/api/v1/commands/notes/save-note \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello Huitzo","content":"My first note!"}'
```

## Run Tests

```bash
cd starters/01-smart-notes
pytest -v
```

## Project Structure

```
01-smart-notes/
├── README.md              # This file
├── tutorial.md             # Step-by-step walkthrough
├── pyproject.toml          # Dependencies and entry points
├── huitzo.yaml             # Pack manifest
├── .env.example            # No API keys needed
├── src/
│   └── smart_notes/
│       ├── __init__.py
│       └── commands.py     # All 4 commands
├── tests/
│   └── test_commands.py    # Validation + command tests
└── examples/
    └── test-commands.sh    # Curl examples to test all endpoints
```

## Services Used

- **Storage** - `ctx.storage.set()`, `ctx.storage.get()`, `ctx.storage.list()`, `ctx.storage.delete()`

No external API keys are required for this template.

## Next Step

Once you are comfortable with storage and commands, move on to:
**[02-ai-content-toolkit](../02-ai-content-toolkit/)** - Learn LLM integration with `ctx.llm.complete()`
