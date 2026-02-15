# Frequently Asked Questions

---

## General

### What is Huitzo?

Huitzo is the **Operating System for Intelligence** -- a Python-first platform for building AI-powered services called Intelligence Packs. Unlike automation tools (Zapier, n8n, Make), Huitzo lets you build services that use AI to think, adapt, and make decisions.

See [What is Huitzo?](what-is-huitzo.md) for a full explainer.

### What is an Intelligence Pack?

An Intelligence Pack is a collection of related commands packaged together. Each command is a Python function decorated with `@command` that becomes an API endpoint. Packs use Huitzo services (storage, AI, email, HTTP, files) to solve problems.

### What counts as "intelligence"?

Intelligence means your pack goes beyond simple IF/THEN rules. It uses AI to:
- **Analyze** data and draw conclusions
- **Score or classify** inputs (lead scoring, sentiment analysis, urgency detection)
- **Generate** structured content (reports, summaries, recommendations)
- **Make decisions** based on context (routing, prioritization, alerting)

A pack that just forwards the user's prompt to an LLM and returns the response is **not** intelligence -- it's a wrapper. A pack that analyzes customer feedback, categorizes it, scores sentiment, and routes critical items to the right team **is** intelligence.

---

## Setup & Installation

### What are the prerequisites?

- Python 3.11 or higher
- Git
- curl (for testing)

Check with: `python3 --version`

### How do I set up the hackathon repo?

```bash
git clone https://github.com/Huitzo-Inc/hackathon-2026.git
cd hackathon-2026
./bootws setup
```

### Do I need Docker?

No. The development server runs locally without Docker. Docker is optional for production deployment.

### Do I need API keys for local development?

No. All starter templates work locally without external API keys. You only need API keys if you want to use real LLM models (OpenAI, Anthropic) or send actual emails. The development server provides mock/local alternatives.

### How do I start the documentation server?

```bash
./bootws docs
# Opens http://localhost:8124 with searchable documentation
```

---

## Development

### How do I create a new command?

```python
from huitzo_sdk import command, Context
from pydantic import BaseModel

class MyArgs(BaseModel):
    name: str

@command("my-command", namespace="my-pack")
async def my_command(args: MyArgs, ctx: Context) -> dict:
    """Description of what this command does."""
    return {"greeting": f"Hello, {args.name}!"}
```

Save this in your pack's `commands.py` file and run `huitzo pack dev`.

### How do I test my commands?

Start the dev server and use curl:
```bash
# Start the server
huitzo pack dev

# Test your command
curl -X POST http://localhost:8080/api/v1/commands/my-pack/my-command \
  -H "Content-Type: application/json" \
  -d '{"name": "World"}'
```

You can also visit `http://localhost:8080/docs` for interactive API documentation.

### Can I use external Python libraries?

Yes. Add them to your pack's `pyproject.toml` under `[project.dependencies]` and Huitzo will install them:

```toml
[project]
dependencies = [
    "huitzo-sdk",
    "pandas>=2.0",
    "requests>=2.28",
]
```

### How do I use AI/LLM in my commands?

Use `ctx.llm.complete()`:

```python
# Simple text completion
response = await ctx.llm.complete(
    prompt="Summarize this text: " + args.text,
    model="gpt-4o-mini"
)

# Structured output with Pydantic schema
response = await ctx.llm.complete(
    prompt="Analyze this lead...",
    schema=LeadScore,  # Pydantic model
    model="gpt-4o-mini"
)
```

### Where is my data stored during development?

Locally in `.huitzo/storage/` within your pack directory. This data persists between server restarts but is local to your machine.

### Can I use both sync and async commands?

Yes. Use `async def` for I/O-bound operations (API calls, storage, LLM) and `def` for CPU-bound operations:

```python
# Async (recommended for most commands)
@command("fetch-data", namespace="my-pack")
async def fetch_data(args: Args, ctx: Context) -> dict:
    data = await ctx.http.get("https://api.example.com/data")
    return data

# Sync (for CPU-intensive work)
@command("compute-hash", namespace="my-pack")
def compute_hash(args: Args, ctx: Context) -> dict:
    result = hashlib.sha256(args.data.encode()).hexdigest()
    return {"hash": result}
```

### How do I debug my commands?

Use `ctx.log` for structured logging:
```python
ctx.log.info("Processing started", extra={"item_count": len(items)})
ctx.log.error("Something went wrong", extra={"error": str(e)})
```

Logs appear in the console where you ran `huitzo pack dev`.

---

## Hackathon Rules

### Can I submit multiple packs?

Yes, but each pack must be a separate submission. Quality is more important than quantity -- one polished pack is better than three rough ones.

### Can teams submit?

Yes. Teams of 1-4 people are allowed. Mention all team members in your submission.

### Can I use AI assistants (Copilot, Claude, ChatGPT)?

Yes. You may use AI coding assistants to help write your code. The submission must still be original work created during the hackathon.

### What's the deadline?

**February 24, 2026 at 11:59 PM PT**. Late submissions will not be accepted.

### Can I start building before Feb 17?

You can familiarize yourself with the SDK and templates before the hackathon starts, but the code you submit must be written during the hackathon period (Feb 17-24).

### How are winners selected?

Judges evaluate based on functionality (30%), intelligence (25%), creativity (20%), code quality (15%), and documentation (10%). See [Hackathon Guide](hackathon-guide.md#judging-criteria) for details.

---

## Platform & SDK

### What services are available through `ctx`?

| Service | Access | Use For |
|---------|--------|---------|
| Storage | `ctx.storage` | Save/retrieve data (key-value) |
| LLM | `ctx.llm` | AI text generation and analysis |
| Email | `ctx.email` | Send emails |
| HTTP | `ctx.http` | Call external APIs |
| Files | `ctx.files` | Read/write CSV, Excel, JSON |
| Telegram | `ctx.telegram` | Send Telegram messages |
| Logging | `ctx.log` | Structured logging |

### What LLM models are supported?

| Provider | Models |
|----------|--------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-4-turbo |
| Anthropic | claude-3-5-sonnet, claude-3-haiku |

### How does storage scoping work?

Storage is automatically scoped by tenant, user, and pack. When you save data with key `"my-key"`, different users get different storage -- no conflicts, no data leaks.

```python
# Each user's "settings" key is independent
await ctx.storage.save("settings", {"theme": "dark"})
```

### What's the difference between `ctx.storage` and `ctx.files`?

- **`ctx.storage`**: Key-value store for structured data (JSON). Fast, simple, with TTL support.
- **`ctx.files`**: File operations for reading/writing CSV, Excel, JSON files. For working with file uploads and generating file outputs.

### How do I handle errors?

Use the SDK's built-in exception hierarchy:

```python
from huitzo_sdk.errors import ValidationError, CommandError

@command("example", namespace="my-pack")
async def example(args: Args, ctx: Context) -> dict:
    if args.count < 0:
        raise ValidationError(
            field="count",
            value=args.count,
            message="Count must be non-negative"
        )
    return {"result": "ok"}
```

See [SDK Quick Reference](sdk-quick-reference.md#error-handling) for the full list.

---

## Submission & Deployment

### How do I submit my pack?

1. Validate: `./scripts/validate-pack.sh path/to/your-pack`
2. Submit: `./scripts/submit-pack.sh path/to/your-pack your-github-username`
3. Create a GitHub Issue using the "Pack Submission" template

See [Hackathon Guide](hackathon-guide.md#how-to-submit) for full instructions.

### How do I deploy my pack?

During the hackathon, focus on local development with `huitzo pack dev`. Deployment to Huitzo Cloud will be available in the future.

### Can I keep building after the hackathon?

Yes. Huitzo is an ongoing platform. After the hackathon, you can continue developing and eventually publish your pack to the Huitzo Hub marketplace.

---

## Still Have Questions?

- Check [Troubleshooting](troubleshooting.md) for common issues
- Ask on [Discord](https://discord.gg/huitzo)
- Join office hours: 2-4 PM PT daily (Feb 17-24)
- Open a GitHub issue
