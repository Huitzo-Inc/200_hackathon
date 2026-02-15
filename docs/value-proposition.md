# Huitzo vs The Alternatives

**Why build with Huitzo instead of Zapier, n8n, or Make?**

---

## The Short Answer

Huitzo is for developers who want to **build intelligence**, not wire together API calls.

- **Zapier/Make**: Visual tools for connecting apps with IF-THEN rules
- **n8n**: Self-hosted automation with limited code support
- **Huitzo**: Python-first platform where AI is a built-in service, not a bolt-on

---

## Comparison Table

| Feature | Huitzo | Zapier | n8n | Make |
|---------|--------|--------|-----|------|
| **AI-Native** | Built-in LLM with structured outputs | OpenAI integration only | Manual setup required | Manual setup required |
| **Code-First** | Python SDK, full IDE support | Visual editor only | Limited code nodes | Visual editor only |
| **Intelligence** | AI makes decisions within workflows | Rule-based (IF/THEN) | Rule-based (IF/THEN) | Rule-based (IF/THEN) |
| **Storage** | Built-in key-value with TTL | External services only | External services only | External services only |
| **Local Dev** | Full local testing and debugging | Cloud-only | Self-hosted option | Cloud-only |
| **Input Validation** | Automatic via Pydantic | Manual | Manual | Manual |
| **Error Handling** | Structured exceptions + auto-retry | Basic retry | Basic retry | Basic retry |
| **Version Control** | Git-native (it's Python code) | Limited | Export/import JSON | Limited |
| **Testing** | pytest, standard Python tooling | No native testing | No native testing | No native testing |
| **Pricing** | Free for hackathon | $$$ per task | Free (self-host) | $$$ per operation |

---

## Deep Dive: Why Huitzo Wins

### 1. Intelligence vs Automation

**Zapier/Make approach (automation):**
```
Trigger: New email received
  → IF subject contains "urgent"
    → Forward to Slack #urgent channel
  → ELSE
    → Forward to Slack #general channel
```

This is keyword matching. It misses context, nuance, and priority.

**Huitzo approach (intelligence):**
```python
@command("route-email", namespace="inbox")
async def route_email(args: EmailInput, ctx: Context) -> dict:
    # AI analyzes the email holistically
    analysis = await ctx.llm.complete(
        prompt=f"""Analyze this email:
        Subject: {args.subject}
        Body: {args.body}

        Score urgency 0-100. Identify key topics.
        Determine best routing channel.""",
        schema=EmailAnalysis
    )

    # Intelligent routing based on AI analysis
    if analysis.urgency > 70:
        await ctx.telegram.send(chat_id=URGENT_CHAT, message=analysis.summary)

    await ctx.storage.save(f"email:{args.id}", analysis.model_dump())
    return analysis.model_dump()
```

The AI understands context. "Our server is down" gets urgency 95 even without the word "urgent."

### 2. Code-First vs Visual-First

Visual editors are great for simple workflows. But when you need:
- **Complex logic** (loops, conditionals, data transformation)
- **Custom validation** (business rules)
- **Testing** (unit tests, integration tests)
- **Version control** (Git, code review, CI/CD)
- **Debugging** (breakpoints, logging, stack traces)

...code is the right answer. Huitzo gives you Python with all the tooling you already know.

### 3. Built-In Infrastructure

With Zapier, you need separate services for storage, AI, email, and monitoring. Each is another integration to configure, another API key to manage, another point of failure.

With Huitzo, everything is available through `ctx`:

```python
# Storage - no database setup needed
await ctx.storage.save("key", data)

# AI - no API key management needed
result = await ctx.llm.complete(prompt="...", schema=MyModel)

# Email - no SMTP/SendGrid configuration needed
await ctx.email.send(to="user@example.com", subject="Report", body="...")

# HTTP - built-in domain restrictions and error handling
data = await ctx.http.get("https://api.example.com/data")

# Files - read Excel, CSV, JSON without pandas boilerplate
df = await ctx.files.read_excel("data.xlsx")
```

### 4. Structured AI Outputs

The biggest challenge with LLM integration is getting reliable, structured data back. Huitzo solves this with Pydantic schemas:

```python
class LeadScore(BaseModel):
    score: int = Field(ge=0, le=100)
    reasoning: str
    recommended_action: str

# The response is GUARANTEED to match this schema
result = await ctx.llm.complete(prompt="...", schema=LeadScore)
print(result.score)  # Always an int between 0-100
```

No parsing JSON strings. No hoping the AI returns valid data. No regex extraction.

---

## When to Use Huitzo

**Use Huitzo when you need:**
- AI-powered decision making (not just rule-based automation)
- Complex business logic that benefits from real code
- Structured AI outputs with validation
- Built-in storage, email, HTTP, and file handling
- Local development and testing with standard Python tools

**Stick with Zapier/Make when you need:**
- Simple "connect App A to App B" integrations
- No-code solutions for non-technical users
- Hundreds of pre-built app connectors
- Quick one-off automations

---

## The Bottom Line

| If you want to... | Use |
|-------------------|-----|
| Connect Slack to Google Sheets | Zapier |
| Auto-post Instagram to Twitter | Make |
| Build an AI-powered lead scoring pipeline | **Huitzo** |
| Create intelligent customer support routing | **Huitzo** |
| Analyze data with AI and generate reports | **Huitzo** |
| Build a smart monitoring system with adaptive alerts | **Huitzo** |

---

## Next Steps

- [What is Huitzo?](what-is-huitzo.md) -- Understand the core concepts
- [Quick Start Guide](../QUICKSTART.md) -- Build your first Intelligence Pack
- [Hackathon Guide](hackathon-guide.md) -- Join the hackathon and win prizes
