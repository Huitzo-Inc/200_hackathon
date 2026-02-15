---
name: Pack Submission
about: Submit your Intelligence Pack for hackathon judging. Eligible for Best Pack ($400), Most Creative ($250), or Most Business Friendly ($250).
title: "[SUBMISSION] "
labels: submission, hackathon
assignees: ''
---

## Pack Information

**Pack Name:**
<!-- e.g., Smart Lead Scorer -->

**Author / Team:**
<!-- Your GitHub username(s) -->

**Category (check all that apply):**
- [ ] Best Pack ($400)
- [ ] Most Creative ($250)
- [ ] Most Business Friendly ($250)

## Description

**What does your pack do?**
A clear, 2-3 sentence description of your Intelligence Pack.

**What problem does it solve?**
Who benefits from this pack and how?

## Key Features

1. Feature one
2. Feature two
3. Feature three

## Demo

**Demo video or screenshots:**
<!-- Link to a video (Loom, YouTube, etc.) or paste screenshots -->

**Live demo (if available):**
<!-- Link to deployed instance, if any -->

## Quick Start

How can judges run your pack locally?

```bash
# Step-by-step commands to get it running
cd showcase/your-username/your-pack-name
pip install -e .
huitzo pack dev
```

## Technical Highlights

**Huitzo services used:**
- [ ] `ctx.storage` - Key-value storage
- [ ] `ctx.llm` - LLM integration
- [ ] `ctx.email` - Email sending
- [ ] `ctx.http` - HTTP requests
- [ ] `ctx.files` - File handling
- [ ] `ctx.telegram` - Telegram integration

**Number of commands:** <!-- e.g., 5 -->

**Interesting technical decisions:**
<!-- What makes your implementation interesting from a technical perspective? -->

## Business Value

*For the Most Business Friendly ($250) prize:*

**Target user/industry:**
<!-- e.g., Sales teams at B2B SaaS companies -->

**Estimated time saved:**
<!-- e.g., 2 hours per week per sales rep -->

**How would this be monetized?**
<!-- e.g., SaaS subscription, per-usage pricing -->

## Built With

- **Started from template:** <!-- e.g., 01-smart-notes, from scratch -->
- **External libraries:** <!-- Any notable dependencies beyond huitzo-sdk -->
- **AI tools used:** <!-- e.g., Claude Code, Cursor, GitHub Copilot -->

## Submission Checklist

- [ ] Pack runs locally with `huitzo pack dev`
- [ ] All commands work and return valid responses
- [ ] README.md documents what the pack does and how to use it
- [ ] `huitzo.yaml` is valid and complete
- [ ] `pyproject.toml` has correct metadata
- [ ] Code is in `showcase/your-username/your-pack-name/` (via `scripts/submit-pack.sh`)
- [ ] No API keys or secrets committed
- [ ] Original work created during the hackathon period (Feb 17-24, 2026)
