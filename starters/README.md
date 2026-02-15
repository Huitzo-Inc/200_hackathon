# Starter Templates

Welcome to the Huitzo starter templates! These are hands-on examples that teach you how to build Intelligence Packs, progressing from basic storage commands to advanced multi-service AI workflows.

## Prerequisites

Before starting, make sure you've completed setup:

```bash
./bootws setup
```

You should have:
- Python 3.11+
- The `huitzo-sdk` package installed
- A terminal and code editor ready

## Template Matrix

| # | Template | Difficulty | Time | What You'll Learn | Services |
|---|----------|-----------|------|-------------------|----------|
| 01 | [smart-notes](01-smart-notes/) | Beginner | 10 min | `@command` decorator, `ctx.storage`, Pydantic validation | Storage |
| 02 | [ai-content-toolkit](02-ai-content-toolkit/) | Beginner+ | 15 min | `ctx.llm.complete()`, structured AI outputs, prompt design | LLM |
| 03 | [data-cruncher](03-data-cruncher/) | Intermediate | 20 min | `ctx.files`, combining storage + LLM for data analysis | Files, LLM, Storage |
| 04 | [lead-engine](04-lead-engine/) | Intermediate+ | 25 min | `ctx.http`, `ctx.email`, multi-command workflows | HTTP, Email, LLM, Storage |
| 05 | [devops-monitor](05-devops-monitor/) | Advanced | 30 min | Health checks, intelligent alerting, multi-channel notifications | HTTP, Email, Telegram, LLM |

**Total time from zero to advanced: about 2 hours.**

## How to Use a Template

Each template is a self-contained Intelligence Pack. To get started:

```bash
# 1. Navigate to the template
cd starters/01-smart-notes

# 2. Read the README for context
cat README.md

# 3. Start the development server
huitzo pack dev

# 4. Test with curl (commands are shown in each template's README)
curl -X POST http://localhost:8080/api/v1/commands/notes/save-note \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello","content":"My first note!"}'
```

## Recommended Progression

### Beginner Path (30 minutes)

Start here if you're new to Huitzo.

1. **01-smart-notes** -- Learn the fundamentals: how `@command` works, how to store and retrieve data with `ctx.storage`, and how Pydantic models enforce input validation. This is the foundation everything else builds on.

2. **02-ai-content-toolkit** -- Add AI capabilities with `ctx.llm.complete()`. Learn how to use Pydantic schemas as `response_model` to get structured, typed outputs from language models instead of raw text.

### Intermediate Path (45 minutes)

After completing the beginner templates:

3. **03-data-cruncher** -- Work with files using `ctx.files`. Upload CSVs, process data, and combine file handling with LLM analysis to generate insights. Shows how multiple services work together.

4. **04-lead-engine** -- Build a real business workflow. Score leads with AI, enrich company data via `ctx.http`, send follow-up emails with `ctx.email`, and chain multiple commands into a pipeline.

### Advanced Path (30 minutes)

Production-grade patterns:

5. **05-devops-monitor** -- Monitor services with health checks, use AI to analyze failure patterns, and send intelligent alerts through email and Telegram. Demonstrates the full power of multi-service orchestration.

## From Template to Your Own Pack

Once you're comfortable with the templates, build your own:

1. **Copy a template** as your starting point:
   ```bash
   cp -r starters/01-smart-notes my-pack
   cd my-pack
   ```

2. **Edit `huitzo.yaml`** with your pack's name and description

3. **Write your commands** in `src/`

4. **Test locally** with `huitzo pack dev`

5. **Submit** when ready:
   ```bash
   ./scripts/validate-pack.sh ./my-pack
   ./scripts/submit-pack.sh ./my-pack your-github-username
   ```

## Tips for Success

- **Read the code, not just the README.** Each template has well-commented source code. Understanding the patterns will help you build your own pack faster.

- **Start small, iterate.** Get one command working before building a complex multi-command workflow. The starter templates are designed this way for a reason.

- **Use AI tools.** Claude Code, Cursor, and GitHub Copilot all work well with the Huitzo SDK. See `config/claude-code-setup.md` or `config/cursor-setup.md` for MCP integration.

- **Check the docs server.** Run `./bootws docs` to start the searchable documentation at http://localhost:8124.

- **Ask for help.** Join [Discord](https://discord.gg/huitzo) or attend office hours (daily 2-4 PM PT during the hackathon).

## Resources

- [SDK Quick Reference](../docs/sdk-quick-reference.md) -- All APIs at a glance
- [FAQ](../docs/faq.md) -- Common questions
- [Troubleshooting](../docs/troubleshooting.md) -- Solutions to common issues
- [QUICKSTART.md](../QUICKSTART.md) -- Platform overview
