# Troubleshooting

Common issues and how to fix them.

---

## Installation Issues

### `huitzo: command not found`

The Huitzo CLI is not in your PATH.

**Fix:**
```bash
# Re-run setup
./bootws setup

# Check if the CLI is installed
./bootws check

# Or install the SDK directly
pip install huitzo-sdk
```

If you're using a virtual environment, make sure it's activated:
```bash
source .venv/bin/activate
```

### `python3: command not found` or wrong Python version

You need Python 3.11 or higher.

**Check your version:**
```bash
python3 --version
```

**Install Python 3.11+:**
- **macOS**: `brew install python@3.12`
- **Ubuntu/Debian**: `sudo apt install python3.12`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)

### `./bootws setup` fails

**Common causes:**
1. **Missing Python**: Install Python 3.11+
2. **Missing pip**: Run `python3 -m ensurepip --upgrade`
3. **Permission denied**: Run `chmod +x bootws` then try again
4. **Network issues**: Check your internet connection (setup downloads packages)

**Verbose output:**
```bash
./bootws setup 2>&1 | tee setup-log.txt
# Share setup-log.txt if you need help
```

---

## Development Server Issues

### Port 8080 already in use

Another process is using port 8080.

**Fix:**
```bash
# Find what's using the port
lsof -i :8080

# Kill the process
kill <PID>

# Or use a different port
huitzo pack dev --port 8081
```

### Server starts but commands return 404

**Common causes:**
1. **Wrong URL**: Check the namespace in your `@command` decorator matches the URL
2. **File not saved**: Make sure you saved your Python file
3. **Syntax error**: Check the console for import or syntax errors

**Verify your command URL:**
```python
# If your command is:
@command("my-command", namespace="my-pack")

# The URL is:
# POST http://localhost:8080/api/v1/commands/my-pack/my-command
```

### Server crashes on startup

**Check for:**
1. **Import errors**: Look at the console output for `ImportError` or `ModuleNotFoundError`
2. **Syntax errors**: Check for Python syntax issues in your code
3. **Missing dependencies**: Install pack dependencies with `pip install -e .`

**Fix import errors:**
```bash
cd starters/XX-template-name
pip install -e .
```

---

## Import Errors

### `ModuleNotFoundError: No module named 'huitzo_sdk'`

The SDK is not installed in your current Python environment.

**Fix:**
```bash
pip install huitzo-sdk
```

If using a virtual environment, make sure it's activated first.

### `ModuleNotFoundError: No module named 'pydantic'`

Missing dependency. Install it:
```bash
pip install pydantic
```

Or install all pack dependencies:
```bash
cd starters/XX-template-name
pip install -e .
```

### `ImportError: cannot import name 'command' from 'huitzo_sdk'`

You might have an outdated version of the SDK.

**Fix:**
```bash
pip install --upgrade huitzo-sdk
```

---

## LLM / AI Issues

### LLM calls return errors or empty responses

**Common causes:**
1. **No API key configured**: For real LLM calls, you need an OpenAI or Anthropic API key
2. **Invalid API key**: Check that your key is correct and active
3. **Rate limiting**: You've exceeded the provider's rate limits

**Set up API keys:**
```bash
# Create or edit .env file in the repo root
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

**Note:** Starter templates are designed to work without API keys in local development. If you're using a starter and getting LLM errors, make sure you haven't modified the LLM configuration.

### Structured output doesn't match my Pydantic schema

The LLM sometimes returns data that doesn't fit your schema, especially with complex models.

**Tips:**
- Use `gpt-4o` for better schema adherence (instead of `gpt-4o-mini`)
- Keep schemas simple -- fewer fields, clear descriptions
- Add `Field(description="...")` to help the LLM understand what you want:
  ```python
  class LeadScore(BaseModel):
      score: int = Field(ge=0, le=100, description="Lead quality score from 0 to 100")
      reasoning: str = Field(description="Brief explanation of the score")
  ```

---

## Storage Issues

### Data not persisting between requests

**Common causes:**
1. **Server restarted**: Data is stored locally. If you restart the server and cleared the storage directory, data is lost.
2. **Different key**: Make sure you're using the exact same key to save and retrieve.
3. **TTL expired**: If you set a TTL, the data may have expired.

**Verify:**
```python
# Save
await ctx.storage.save("test-key", {"hello": "world"})

# Check it exists
exists = await ctx.storage.exists("test-key")
ctx.log.info(f"Key exists: {exists}")

# Retrieve
data = await ctx.storage.get("test-key")
ctx.log.info(f"Data: {data}")
```

### `StorageError: key too long`

Storage keys are limited to 256 characters.

**Fix:** Use shorter keys with meaningful prefixes:
```python
# Too long
await ctx.storage.save(f"user-preferences-for-{very_long_user_identifier}", data)

# Better
await ctx.storage.save(f"prefs:{user_id[:8]}", data)
```

---

## HTTP / API Issues

### `HTTPSecurityError: domain not allowed`

Your pack tried to make an HTTP request to a domain not listed in the pack manifest.

**Fix:** Add the domain to your `huitzo.yaml`:
```yaml
services:
  http:
    allowed_domains:
      - "api.example.com"
      - "*.trusted-domain.org"
```

### External API returns 401 or 403

Your API key is invalid or missing.

**Fix:**
1. Check that the API key is correct
2. Make sure it's set in your environment or `.env` file
3. Verify the key has the right permissions

```python
# Access API keys through ctx.env
api_key = ctx.env.get("MY_API_KEY")
if not api_key:
    return {"error": "API key not configured"}
```

---

## Email Issues

### Emails not sending

**In local development**, emails may not actually send unless you've configured an email provider.

**Check configuration:**
```bash
# In your .env file, you need one of:
SENDGRID_API_KEY=your-key-here
# OR
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-password

# Always needed:
EMAIL_FROM=sender@example.com
```

**Tip:** During the hackathon, you can use `ctx.log.info()` to log email content instead of actually sending:
```python
ctx.log.info(f"Would send email to {args.to}: {args.subject}")
```

---

## Validation Errors

### `422 Unprocessable Entity` when calling a command

Your request body doesn't match the Pydantic model.

**Common fixes:**
1. **Check field names**: Pydantic is case-sensitive
2. **Check types**: A `str` field won't accept `int` without conversion
3. **Check required fields**: Fields without defaults are required

**Example:**
```python
class MyArgs(BaseModel):
    name: str          # Required
    count: int = 10    # Optional, defaults to 10
```

```bash
# This works:
curl -X POST ... -d '{"name": "test"}'

# This fails (missing "name"):
curl -X POST ... -d '{"count": 5}'

# This fails (wrong type for "count"):
curl -X POST ... -d '{"name": "test", "count": "five"}'
```

### Custom validation errors

If you're using `@field_validator` and getting unexpected errors, check that:
1. The validator is a `@classmethod`
2. The decorator order is `@field_validator` then `@classmethod`
3. The validator returns the validated value

```python
class MyArgs(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v  # Must return the value
```

---

## Pack Structure Issues

### Pack not detected / no commands found

Make sure your pack has the correct structure:
```
my-pack/
  huitzo.yaml          # Pack manifest
  pyproject.toml       # Python project config
  src/
    my_pack/
      __init__.py
      commands.py      # Your commands go here
```

And that `commands.py` imports and uses `@command`:
```python
from huitzo_sdk import command, Context
```

---

## Getting More Help

If your issue isn't listed here:

1. **Search the [FAQ](faq.md)** for related questions
2. **Check the console output** for error messages and stack traces
3. **Ask on [Discord](https://discord.gg/huitzo)** with:
   - What you tried
   - The full error message
   - Your Python version (`python3 --version`)
   - Your OS (macOS, Linux, Windows)
4. **Open a GitHub issue** for bugs in the Huitzo platform
5. **Join office hours** (2-4 PM PT daily, Feb 17-24) for live help
