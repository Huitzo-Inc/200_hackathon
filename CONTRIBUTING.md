# Contributing to Huitzo Hackathon 2026

Welcome! We're excited you're building with Huitzo. This guide covers how to submit your work, report bugs, and share feedback.

## Submitting an Intelligence Pack

### 1. Build Your Pack

Start from any starter template or build from scratch:

```bash
cd starters/01-smart-notes  # or any template
# Customize, extend, or create something new
```

Your pack needs these files:
- `README.md` - What it does and how to use it
- `huitzo.yaml` - Pack configuration (name, version, description)
- `pyproject.toml` - Python package metadata
- `src/` - Your source code with `@command` decorators

### 2. Validate

Run the validation script to check your pack structure:

```bash
./scripts/validate-pack.sh path/to/your-pack
```

This checks for required files, valid YAML, and Python source code.

### 3. Submit to Showcase

Copy your pack to the showcase directory:

```bash
./scripts/submit-pack.sh path/to/your-pack your-github-username
```

This validates your pack, copies it to `showcase/<username>/<pack-name>/`, and creates a `SUBMISSION.md` file.

### 4. Create a Pull Request

```bash
git add showcase/<username>/<pack-name>/
git commit -m "Submit <pack-name> by @<username>"
git push origin HEAD
gh pr create --title "[SUBMISSION] <pack-name>" --template pack-submission.md
```

### 5. File a Submission Issue

Open a **Pack Submission** issue on GitHub with your demo, screenshots, and prize category selection:

https://github.com/Huitzo-Inc/hackathon-2026/issues/new?template=pack-submission.md

## Reporting Bugs (Worst Bug Found Prize)

Found a bug in the Huitzo SDK or platform? You could win the **$100 Worst Bug Found** prize!

### What Qualifies

- Bugs in the Huitzo SDK, CLI, or development server
- Reproducible issues with clear steps
- Not already reported in an existing GitHub issue

### How to Report

1. Search [existing issues](https://github.com/Huitzo-Inc/hackathon-2026/issues?q=label%3Abug) to make sure it's not already reported
2. Open a **Bug Report** issue using the template
3. Include: reproduction steps, expected vs. actual behavior, environment details
4. Rate the severity (Critical, High, Medium, Low)

The most critical, well-documented bug report wins the prize.

## Sharing Feedback

Your feedback helps us improve Huitzo. Use the **Feedback** issue template to share:

- What worked well
- What was confusing
- What's missing
- Your overall experience rating

https://github.com/Huitzo-Inc/hackathon-2026/issues/new?template=feedback.md

## Prize Categories

| Prize | Amount | How to Compete |
|-------|--------|----------------|
| **Best Pack** | $400 | Submit a Pack Submission issue |
| **Most Creative** | $250 | Submit a Pack Submission issue |
| **Most Business Friendly** | $250 | Submit a Pack Submission issue (fill in Business Value section) |
| **Worst Bug Found** | $100 | File a Bug Report issue |

**Deadline:** February 24, 2026, 11:59 PM PT

## Code of Conduct

- Be respectful in all interactions (GitHub, Discord, and elsewhere)
- No harassment, discrimination, or inappropriate content
- Help others when you can; we're all here to learn and build
- Violations may result in disqualification

## Submission Rules

- Submissions must be **original work** created during the hackathon period (February 17-24, 2026)
- Submissions must use the **Huitzo SDK**
- You retain all intellectual property rights to your code
- By submitting, you grant Huitzo Inc permission to showcase your work
- No API keys, secrets, or credentials should be committed

## Getting Help

- **Discord**: [Join here](https://discord.gg/huitzo) for live support
- **Office Hours**: Daily 2-4 PM PT during the hackathon
- **FAQ**: See [docs/faq.md](docs/faq.md)
- **Troubleshooting**: See [docs/troubleshooting.md](docs/troubleshooting.md)

## License

By contributing, you agree that your submissions are licensed under the MIT License. See [LICENSE](LICENSE) for details.
