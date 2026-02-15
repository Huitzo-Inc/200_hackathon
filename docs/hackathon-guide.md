# Huitzo Hackathon 2026 Guide

**February 17-24, 2026 | $1,000 in Prizes**

---

## Overview

Build an Intelligence Pack that solves a real problem using the Huitzo SDK. Use AI, storage, email, HTTP, files, and more to create something impressive.

**What is an Intelligence Pack?** A collection of Python commands that use AI to think, adapt, and make decisions. See [What is Huitzo?](what-is-huitzo.md) for details.

---

## Timeline

| Date | Event |
|------|-------|
| **Feb 17 (Mon)** | Hackathon begins. Start building! |
| **Feb 17-24** | Daily office hours: 2-4 PM PT on [Discord](https://discord.gg/huitzo) |
| **Feb 24 (Mon) 11:59 PM PT** | Submission deadline |
| **Feb 25-26** | Judging period |
| **Feb 27** | Winners announced |

---

## Prizes

**Total Prize Pool: $1,000**

| Prize | Amount | Criteria |
|-------|--------|----------|
| **Best Pack** | $400 | Most impressive overall: functionality, creativity, and polish |
| **Most Creative** | $250 | Most innovative use of Huitzo features |
| **Most Business Friendly** | $250 | Solves a real business problem elegantly |
| **Worst Bug Found** | $100 | Most critical bug found in Huitzo platform |

---

## Judging Criteria

### For Intelligence Packs (Best Pack, Most Creative, Most Business Friendly)

| Criterion | Weight | What We Look For |
|-----------|--------|-----------------|
| **Functionality** | 30% | Does it work? Is it reliable? Does it handle edge cases? |
| **Intelligence** | 25% | Does it use AI meaningfully (not just wrapping an LLM call)? |
| **Creativity** | 20% | Is the approach novel? Does it solve the problem in a clever way? |
| **Code Quality** | 15% | Clean code, proper error handling, good structure |
| **Documentation** | 10% | Clear README, usage examples, setup instructions |

### For Bug Reports (Worst Bug Found)

| Criterion | What We Look For |
|-----------|-----------------|
| **Severity** | Does it block functionality or cause data loss? |
| **Reproducibility** | Can we reproduce it consistently? |
| **Description** | Clear steps, expected vs actual behavior |
| **Novelty** | Not already known or reported |

---

## Rules

### Eligibility

- Open to all developers, students, and teams
- Teams of 1-4 people
- You must use the Huitzo SDK (`huitzo-sdk`)
- Submissions must be original work created during the hackathon
- You may use external Python libraries
- You may use AI assistants (Copilot, Claude, ChatGPT) to help write code

### What Counts as a Valid Submission

Your Intelligence Pack must:
1. Use the `@command` decorator from `huitzo-sdk`
2. Have at least 2 working commands
3. Include a README with setup instructions and usage examples
4. Be runnable with `huitzo pack dev`

### What Does NOT Count

- Packs that only wrap a single LLM call with no additional logic
- Packs that don't use any Huitzo services (`ctx.storage`, `ctx.llm`, etc.)
- Previously published code (open-source libraries repackaged as a pack)
- Malicious or offensive content

---

## How to Submit

### Intelligence Pack Submission

**1. Build your pack** starting from any starter template:
```bash
cd starters/01-smart-notes  # Or start from scratch
# Build something awesome
```

**2. Validate your pack:**
```bash
./scripts/validate-pack.sh path/to/your-pack
```

**3. Submit to showcase:**
```bash
./scripts/submit-pack.sh path/to/your-pack your-github-username
```

**4. Create a GitHub Issue** using the "Pack Submission" template:
- Link to your pack code
- Include a demo video or screenshots
- Specify which prize category you're targeting
- Describe what your pack does and why it's special

### Bug Report Submission

**1. Find a bug** in the Huitzo platform (SDK, runtime, CLI, or docs).

**2. Create a GitHub Issue** using the "Bug Report" template:
- Provide clear reproduction steps
- Include expected vs actual behavior
- Note the severity and impact

**3. We verify and award** the prize to the most critical confirmed bug.

---

## Office Hours

**Daily: 2-4 PM PT, February 17-24**

Join us on [Discord](https://discord.gg/huitzo) during office hours:
- Get help with setup and debugging
- Ask questions about the SDK
- Show off your progress
- Connect with other builders

The Huitzo team will be online to help you get unstuck.

---

## Tips for a Winning Submission

### Best Pack

- **Solve a real problem** -- packs that address genuine needs score higher
- **Polish matters** -- error handling, edge cases, clear output formatting
- **Show range** -- use multiple Huitzo services (storage + LLM + email, etc.)
- **Document well** -- a clear README makes judges want to try your pack

### Most Creative

- **Think outside the box** -- combine Huitzo features in unexpected ways
- **Novel use of AI** -- go beyond simple summarization or generation
- **Surprise us** -- the "I didn't know you could do that" factor

### Most Business Friendly

- **Pick a real business workflow** -- sales, support, operations, finance
- **Show ROI** -- how does this save time or money?
- **Make it practical** -- could a real business use this tomorrow?

---

## Getting Help

1. **[FAQ](faq.md)** -- Check if your question is already answered
2. **[Troubleshooting](troubleshooting.md)** -- Common issues and fixes
3. **[SDK Quick Reference](sdk-quick-reference.md)** -- API patterns and examples
4. **[Discord](https://discord.gg/huitzo)** -- Ask the community
5. **Office Hours** -- Get live help from the Huitzo team (2-4 PM PT daily)
6. **GitHub Issues** -- Report bugs or ask technical questions

---

## Quick Setup Reminder

```bash
# 1. Clone the repo
git clone https://github.com/Huitzo-Inc/hackathon-2026.git
cd hackathon-2026

# 2. Run setup
./bootws setup

# 3. Start with a template
cd starters/01-smart-notes
huitzo pack dev

# 4. Start building!
```

See [Quick Start Guide](../QUICKSTART.md) for detailed setup instructions.
