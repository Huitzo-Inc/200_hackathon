# [Huitzo Hackathon 2026](https://huitzo.com) 🚀

**February 17-24, 2026 | $1,000 in Prizes**

Build Intelligence, Not Automation. Create AI-powered Intelligence Packs that solve real problems.

# [Sign Up to Participate](https://forms.office.com/r/UYDq4mrxkk)

---

## What is Huitzo?

Huitzo is the **Operating System for Intelligence** a platform where you build smart, reusable Intelligence Packs using AI, storage, email, HTTP, and more. Unlike automation tools (Zapier, n8n, Make), Huitzo lets you **build intelligence** that thinks, adapts, and makes decisions.

**Key Difference:**
- **Automation tools**: IF this happens, THEN do that (rigid, rule-based)
- **Huitzo**: Give it context, let AI decide what to do (intelligent, adaptive)

**Example:**
```python
@command("score-lead")
async def score_lead(args: LeadInput, ctx: Context) -> LeadScore:
    # AI analyzes the lead and scores it 0-100
    analysis = await ctx.llm.complete(
        prompt=f"Analyze this lead: {args.company}. Score 0-100.",
        response_model=LeadScore  # Pydantic schema
    )
    return analysis
```

That's it. Huitzo handles the infrastructure, you write the intelligence.

---

## 🎯 Hackathon Prizes

**Total Prize Pool: $1,000**

| Prize | Amount | Criteria |
|-------|--------|----------|
| **Most Impressive** | $250 | (functionality + creativity + polish) |
| **Most Creative** | $250 | Most innovative use of Huitzo features |
| **Most Business Friendly** | $250 | Solves a real business problem elegantly |
| **Worst Bug Found** | $250 | Find the most critical bug in Huitzo |

**Submission Deadline:** February 24, 2026 11:59 PM PT

---

## ⚡ 10-Minute Quick Start

**1. Clone and Setup**
```bash
git clone https://github.com/Huitzo-Inc/200_hackathon.git
cd 200_hackathon
./bootws setup
```

**2. Start with Smart Notes (10 minutes)**
```bash
cd starters/01-smart-notes
cat README.md  # Read what you'll learn
huitzo pack dev  # Starts local development server
```

**3. Test Your First Command**
```bash
# Save a note
curl -X POST http://localhost:8080/api/v1/commands/notes/save-note \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello Huitzo","content":"My first intelligent command!"}'

# Get it back
curl -X POST http://localhost:8080/api/v1/commands/notes/get-note \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello Huitzo"}'
```

**4. Explore More Templates**

Try progressively advanced examples:
- **02-ai-content-toolkit** (15 min) - LLM-powered summarization, entity extraction
- **03-data-cruncher** (20 min) - CSV analysis with AI insights
- **04-lead-engine** (25 min) - Multi-command AI sales pipeline
- **05-devops-monitor** (30 min) - Intelligent health checks with multi-channel alerts

---

## 📚 Learning Path

### Beginner (30 minutes total)
Start here if you're new to Huitzo:
1. **01-smart-notes** (10 min) - Learn: `@command`, `ctx.storage`, Pydantic validation
2. **02-ai-content-toolkit** (15 min) - Learn: `ctx.llm`, structured AI outputs

### Intermediate (45 minutes total)
After completing beginner templates:
3. **03-data-cruncher** (20 min) - Learn: `ctx.files`, combining storage + LLM
4. **04-lead-engine** (25 min) - Learn: `ctx.http`, `ctx.email`, multi-command workflows

### Advanced (30 minutes)
Ready for production-grade patterns:
5. **05-devops-monitor** (30 min) - Learn: Health checks, intelligent alerting, multi-channel

**Total Learning Time: ~2 hours to go from zero to advanced.**

---

## 🏗️ Starter Template Matrix

| Template | Difficulty | Time | What You'll Learn | Services Used |
|----------|-----------|------|-------------------|---------------|
| **01-smart-notes** | Beginner | 10 min | Command basics, storage, validation | Storage |
| **02-ai-content-toolkit** | Beginner+ | 15 min | LLM integration, structured outputs | LLM |
| **03-data-cruncher** | Intermediate | 20 min | File handling, data transformation | Files, LLM, Storage |
| **04-lead-engine** | Intermediate+ | 25 min | HTTP APIs, email, multi-command flows | HTTP, Email, LLM, Storage |
| **05-devops-monitor** | Advanced | 30 min | Health monitoring, intelligent alerts | HTTP, Email, Telegram, LLM |

---

## 🎨 Huitzo vs. The Alternatives

| Feature | Huitzo | Zapier | n8n | Make |
|---------|--------|--------|-----|------|
| **AI-Native** | ✅ Built-in LLM, structured outputs | ❌ OpenAI integration only | ❌ Manual setup | ❌ Manual setup |
| **Code-First** | ✅ Python SDK, full control | ❌ Visual editor only | ⚠️ Limited code nodes | ❌ Visual only |
| **Intelligence** | ✅ AI makes decisions | ❌ Rule-based only | ❌ Rule-based only | ❌ Rule-based only |
| **Storage** | ✅ Built-in key-value + TTL | ❌ External only | ❌ External only | ❌ External only |
| **Local Development** | ✅ Full local testing | ❌ Cloud-only | ✅ Self-hosted | ❌ Cloud-only |
| **Pricing** | Free + usage-based | $$$ per task | Free (self-host) | $$$ per operation |

**Bottom Line:** Huitzo is for developers who want to **build intelligence**, not wire together API calls.

---

## 📖 Documentation

### Getting Started
- **[Quick Start Guide](QUICKSTART.md)** - 5-minute intro to Huitzo concepts
- **[What is Huitzo?](docs/what-is-huitzo.md)** - Deep dive on the platform
- **[SDK Quick Reference](docs/sdk-quick-reference.md)** - Essential patterns & APIs

### Core Concepts
- **[Why Huitzo](docs/concepts/why-huitzo.md)** - The infrastructure gap between AI models and production
- **[Building Methodology](docs/concepts/building-methodology.md)** - Commands, not applications: the Huitzo approach
- **[From Model to Production](docs/concepts/from-model-to-production.md)** - Complete infrastructure layer walkthrough

### Hackathon Info
- **[Hackathon Guide](docs/hackathon-guide.md)** - Rules, prizes, timeline, office hours
- **[Value Proposition](docs/value-proposition.md)** - Why Huitzo vs alternatives
- **[FAQ](docs/faq.md)** - Common questions
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues & solutions

**Documentation Server:**
```bash
./bootws docs  # Opens http://localhost:8124 with searchable docs
```

**AI-Native Documentation:**
- Works with Claude Code, Cursor, GitHub Copilot
- MCP server integration for intelligent doc search
- See `config/claude-code-setup.md` for setup

---

## 🏆 How to Submit

### For Intelligence Packs

**1. Build Your Pack**
```bash
cd starters/01-smart-notes  # Start from any template
# Modify, extend, create something awesome
```

**2. Validate Your Pack**
```bash
./scripts/validate-pack.sh path/to/your-pack
```

**3. Submit to Showcase**
```bash
./scripts/submit-pack.sh path/to/your-pack your-github-username
```

**4. Create a GitHub Issue**
- Use the **"Pack Submission"** template
- Include demo video or screenshots
- Specify prize category: Best Pack, Most Creative, or Most Business Friendly

### For Bug Reports ("Worst Bug Found" Prize)

**1. Find a Critical Bug**
- Does it block functionality?
- Is it reproducible?
- Not already reported?

**2. File a GitHub Issue**
- Use the **"Bug Report"** template
- Provide clear reproduction steps
- Include impact assessment

**3. We'll Confirm & Award**
- We verify the bug
- Award goes to the most critical bug found

---

## 🕐 Office Hours

**Office Hours AVAILABLE (February 17-24)**
- Email `ernesto@huitzo.ai` and request a meeting
- Live on Discord: [Join Here](https://discord.gg/huitzo) COMING SOON
- Ask questions, get unstuck, show off your progress
- Huitzo team will be online to help

---

## 🚀 Next Steps

**Ready to build?**
1. Run `./bootws setup` (one-time setup)
2. Run `./bootws docs` (start documentation server)
3. Try `starters/01-smart-notes` (your first 10 minutes)
4. Join [Discord](https://discord.gg/huitzo) to connect with other builders

**Questions?**
- Check [FAQ](docs/faq.md)
- Browse [Troubleshooting](docs/troubleshooting.md)
- Ask in [Discord](https://discord.gg/huitzo)
- Open a GitHub issue

---

## 📜 License & Community

MIT License - See [LICENSE](LICENSE) for details.

Hackathon submissions must be original work. See [CONTRIBUTING.md](CONTRIBUTING.md) for full terms.

**Code of Conduct**: All participants must follow our [Code of Conduct](CODE_OF_CONDUCT.md). We're committed to providing a welcoming and inclusive environment for everyone.

---

**Built by [Huitzo Inc](https://huitzo.com) | The Operating System for Intelligence**

Good luck, and happy building! 🎉
