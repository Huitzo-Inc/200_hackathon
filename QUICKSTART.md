# Huitzo Quick Start Guide

**Goal: Understand Huitzo and run your first Intelligence Pack in 5 minutes.**

---

## What is Huitzo?

Huitzo is a platform for building **Intelligence Packs**—smart, AI-powered services that think, adapt, and make decisions.

**Think of it like this:**
- **Zapier/n8n**: "IF email received, THEN send to Slack" (rigid rules)
- **Huitzo**: "Analyze incoming emails, score urgency 0-100, route important ones to Slack with AI-generated summaries" (intelligent decisions)

**Core Concept:**
```python
@command("analyze-email")
async def analyze_email(args: EmailInput, ctx: Context) -> EmailAnalysis:
    # AI analyzes the email
    analysis = await ctx.llm.complete(
        prompt=f"Analyze this email: {args.content}. Score urgency 0-100.",
        response_model=EmailAnalysis  # Pydantic schema enforces structure
    )

    # Conditionally route based on AI's decision
    if analysis.urgency > 70:
        await ctx.email.send(to="urgent@company.com", ...)

    return analysis
```

You write the intelligence, Huitzo handles the infrastructure.

---

## Installation (1 minute)

**Prerequisites:**
- Python 3.11+ (check: `python3 --version`)
- Git
- curl (for testing)

**Setup:**
```bash
git clone https://github.com/Huitzo-Inc/hackathon-2026.git
cd hackathon-2026
./bootws setup
```

**What this does:**
- Installs `huitzo-sdk` and dependencies
- Creates `.env` file for configuration (optional for local dev)
- Validates installation

**Expected output:**
```
✅ Setup complete!

Next steps:
  1. ./bootws docs          # Start documentation server
  2. cd starters/01-smart-notes
  3. huitzo pack dev        # Start developing your first pack!
```

---

## Run Your First Pack (3 minutes)

### Step 1: Navigate to Smart Notes Template
```bash
cd starters/01-smart-notes
cat README.md  # Quick overview of what you'll learn
```

### Step 2: Start the Development Server
```bash
huitzo pack dev
```

**Expected output:**
```
🚀 Starting Huitzo development server...
📦 Pack: smart-notes
🔗 API available at: http://localhost:8080
📝 Commands:
   - notes/save-note
   - notes/get-note
   - notes/list-notes
   - notes/delete-note

Press Ctrl+C to stop.
```

### Step 3: Test Commands

**Save a note:**
```bash
curl -X POST http://localhost:8080/api/v1/commands/notes/save-note \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Meeting Notes",
    "content": "Discussed Q1 roadmap. Focus on user growth."
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "title": "Meeting Notes",
    "content": "Discussed Q1 roadmap. Focus on user growth.",
    "created_at": "2026-02-14T10:30:00Z"
  }
}
```

**Get the note back:**
```bash
curl -X POST http://localhost:8080/api/v1/commands/notes/get-note \
  -H "Content-Type: application/json" \
  -d '{"title": "Meeting Notes"}'
```

**List all notes:**
```bash
curl -X POST http://localhost:8080/api/v1/commands/notes/list-notes \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## What Just Happened?

Let's break down what you just ran:

### 1. The Command Decorator
```python
@command("save-note", namespace="notes")
async def save_note(args: NoteInput, ctx: Context) -> NoteOutput:
    ...
```

- **`@command`**: Registers this function as an API endpoint
- **`namespace="notes"`**: Groups related commands (becomes `/notes/save-note`)
- **`args: NoteInput`**: Pydantic model enforces input validation
- **`ctx: Context`**: Access to Huitzo services (storage, LLM, email, HTTP, etc.)

### 2. Storage API
```python
await ctx.storage.set(f"note:{args.title}", note_data)
```

- **User-scoped**: Each user gets their own storage namespace
- **Persistent**: Data survives across command invocations
- **Simple**: Key-value store with optional TTL

### 3. Validation with Pydantic
```python
class NoteInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
```

- **Automatic validation**: Invalid requests return 400 with clear errors
- **Type safety**: Python's type system enforces correctness
- **Documentation**: Schema becomes auto-generated API docs

### 4. Development Server
```bash
huitzo pack dev
```

- **Local testing**: No cloud deployment needed
- **Hot reload**: Changes apply automatically (restart server to reload)
- **Full API**: Acts like production environment

---

## Next Steps

### Beginner Path (30 minutes)
1. **Read the Smart Notes code** (`starters/01-smart-notes/src/smart_notes/commands.py`)
   - See how `@command` works
   - Understand `ctx.storage` API
   - Learn Pydantic validation

2. **Try AI Content Toolkit** (`starters/02-ai-content-toolkit`)
   - Learn `ctx.llm.complete()` for AI-powered commands
   - See structured outputs with Pydantic schemas
   - Experiment with different prompts and models

### Intermediate Path (45 minutes more)
3. **Data Cruncher** (`starters/03-data-cruncher`)
   - File handling with `ctx.files`
   - Combining AI + storage + files

4. **Lead Engine** (`starters/04-lead-engine`)
   - Multi-command workflows
   - HTTP and email integration
   - Real business automation

### Advanced Path (30 minutes more)
5. **DevOps Monitor** (`starters/05-devops-monitor`)
   - Health checks and alerting
   - Multi-channel notifications
   - Production-ready patterns

---

## Common Questions

**Q: Do I need API keys for local development?**
A: No! All starter templates work locally without external API keys. You'll only need keys if you want to use real LLM models or send actual emails.

**Q: How do I deploy my pack?**
A: During the hackathon, focus on local development. Huitzo Cloud deployment will be available soon.

**Q: Can I use external libraries?**
A: Yes! Add them to `pyproject.toml` and Huitzo will install them.

**Q: Where is my data stored?**
A: Locally in `.huitzo/storage/` during development. In production, it's in secure cloud storage.

**Q: Can I see API documentation?**
A: Yes! Visit http://localhost:8080/docs when your pack is running.

**Q: How do I debug?**
A: Use `ctx.log.info()`, `ctx.log.error()` in your commands. Logs appear in the console.

---

## Troubleshooting

**Problem: `huitzo: command not found`**
```bash
# Make sure setup completed successfully
./bootws check

# Reinstall if needed
pip install huitzo-sdk
```

**Problem: Port 8080 already in use**
```bash
# Find what's using the port
lsof -i :8080

# Kill the process or use a different port
huitzo pack dev --port 8081
```

**Problem: Import errors in commands**
```bash
# Install pack dependencies
cd starters/XX-template-name
pip install -e .
```

**More issues?**
- Check [docs/troubleshooting.md](docs/troubleshooting.md)
- Search [docs/faq.md](docs/faq.md)
- Ask in [Discord](https://discord.gg/huitzo)

---

## Resources

- **[README](README.md)**: Hackathon overview and prizes
- **[SDK Quick Reference](docs/sdk-quick-reference.md)**: Essential APIs
- **[Hackathon Guide](docs/hackathon-guide.md)**: Rules and timeline
- **[Documentation Server](http://localhost:8124)**: Searchable docs (run `./bootws docs`)

---

**Ready to build intelligence? Start with `starters/01-smart-notes` →**
