# Showcase

This is where hackathon submissions live. Each participant gets their own directory under `showcase/<github-username>/<pack-name>/`.

## Browse Submissions

Submissions will appear here during the hackathon. Each directory contains a complete Intelligence Pack with a `SUBMISSION.md` file describing the project.

```
showcase/
  octocat/
    smart-lead-scorer/
      README.md
      huitzo.yaml
      pyproject.toml
      src/
      SUBMISSION.md
  janedoe/
    email-triage/
      ...
```

## How to Submit Your Pack

### Quick Version

```bash
# 1. Validate your pack
./scripts/validate-pack.sh path/to/your-pack

# 2. Submit to showcase
./scripts/submit-pack.sh path/to/your-pack your-github-username

# 3. Commit and push
git add showcase/your-username/your-pack-name/
git commit -m "Submit your-pack-name by @your-username"
git push origin HEAD

# 4. Open a Pull Request
gh pr create --title "[SUBMISSION] your-pack-name" --template pack-submission.md
```

### Detailed Version

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full submission guidelines, including how to file a Pack Submission issue on GitHub.

## Prizes

| Prize | Amount | What Judges Look For |
|-------|--------|---------------------|
| **Best Pack** | $400 | Overall quality: functionality, creativity, code quality, and polish |
| **Most Creative** | $250 | Novel use of Huitzo features, unique problem-solving approach |
| **Most Business Friendly** | $250 | Practical business value, clear use case, ease of deployment |
| **Worst Bug Found** | $100 | Critical, reproducible bugs in the Huitzo SDK or platform |

**Submission deadline:** February 24, 2026, 11:59 PM PT

**Winners announced:** Within 7 days of hackathon end (by March 3, 2026)

## Judging Criteria

Packs are evaluated on:

1. **Functionality** -- Does it work? Are commands reliable and well-tested?
2. **Creativity** -- Is the problem interesting? Is the approach novel?
3. **Code Quality** -- Is the code clean, well-structured, and documented?
4. **Business Value** -- Could this solve a real problem for real users?
5. **Use of Huitzo Features** -- How well does it leverage the SDK's capabilities (LLM, storage, email, HTTP, etc.)?

## Questions?

- Check the [FAQ](../docs/faq.md)
- Join [Discord](https://discord.gg/huitzo)
- Office hours: daily 2-4 PM PT during the hackathon
