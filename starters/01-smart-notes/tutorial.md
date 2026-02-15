# Tutorial: Smart Notes

**Goal:** Build a personal notes system with 4 CRUD commands in 10 minutes.

---

## Step 1: Understand the Pack Structure

Every Intelligence Pack has the same layout:

```
01-smart-notes/
├── huitzo.yaml         # Declares your pack to Huitzo
├── pyproject.toml      # Python dependencies + command entry points
└── src/smart_notes/
    └── commands.py     # Your command functions
```

The two most important files are:
- **`huitzo.yaml`** - Tells Huitzo what your pack does (name, commands, permissions)
- **`commands.py`** - Your actual code

## Step 2: Read the Manifest (`huitzo.yaml`)

Open `huitzo.yaml` and look at the structure:

```yaml
pack:
  name: "smart-notes"
  namespace: "notes"       # Commands are accessed at /notes/<command-name>
  version: "1.0.0"

commands:
  - name: "save-note"
    permissions:
      - "storage:write"    # This command needs write access to storage
    timeout: 30

services:
  storage:
    required: true
    scope: "user"          # Each user gets their own storage
```

Key points:
- `namespace: "notes"` means your commands are available at `/notes/save-note`, `/notes/get-note`, etc.
- Each command declares its `permissions` (what services it needs)
- `scope: "user"` means storage is isolated per user

## Step 3: Write Your First Command

Open `src/smart_notes/commands.py`. The first command is `save-note`:

```python
from pydantic import BaseModel, Field

class SaveNoteArgs(BaseModel):
    """Arguments for the save-note command."""
    title: str = Field(
        min_length=1,
        max_length=200,
        description="Title of the note (used as unique key)",
    )
    content: str = Field(
        min_length=1,
        max_length=10_000,
        description="Body text of the note",
    )

@command("save-note", namespace="notes", timeout=30)
async def save_note(args: SaveNoteArgs, ctx: Context) -> dict[str, Any]:
    """Save or update a note by title."""
    key = f"note:{args.title}"
    now = datetime.now(UTC).isoformat()

    existing = await ctx.storage.get(key)

    note_data = {
        "title": args.title,
        "content": args.content,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }

    await ctx.storage.set(key, note_data)
    ctx.log.info(f"Saved note: {args.title}")
    return note_data
```

Let's break this down:

### The Args Model (Pydantic)
```python
class SaveNoteArgs(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
```
- Pydantic validates input **before** your function runs
- If someone sends `{"title": ""}`, Huitzo returns a 400 error automatically
- You never need to write manual validation code

### The `@command` Decorator
```python
@command("save-note", namespace="notes", timeout=30)
```
- `"save-note"` - The command name (used in the URL)
- `namespace="notes"` - Groups related commands together
- `timeout=30` - Maximum seconds before the command is cancelled

### The Function Signature
```python
async def save_note(args: SaveNoteArgs, ctx: Context) -> dict[str, Any]:
```
- `args` - Validated input (Pydantic model)
- `ctx` - Access to Huitzo services (storage, LLM, email, HTTP, etc.)
- Returns a `dict` that becomes the JSON response

### Storage API
```python
await ctx.storage.set(key, note_data)   # Save data
await ctx.storage.get(key)              # Retrieve data (returns None if missing)
await ctx.storage.list("note:", limit=10)  # List by key prefix
await ctx.storage.delete(key)           # Delete data (returns True/False)
```

Storage is user-scoped: each user only sees their own notes.

## Step 4: Understand All Four Commands

| Command | What It Does | Storage Call |
|---------|-------------|--------------|
| `save-note` | Create or update a note | `ctx.storage.set(key, data)` |
| `get-note` | Retrieve a note | `ctx.storage.get(key)` |
| `list-notes` | List all notes | `ctx.storage.list(prefix, limit)` |
| `delete-note` | Remove a note | `ctx.storage.delete(key)` |

All four follow the same pattern:
1. Validate input with Pydantic
2. Call `ctx.storage` to interact with data
3. Log the action with `ctx.log`
4. Return a result dict

## Step 5: Run the Tests

The test file (`tests/test_commands.py`) shows how to test commands without running the server:

```python
from unittest.mock import AsyncMock, MagicMock

# Create a mock Context
ctx = MagicMock()
ctx.storage.set = AsyncMock()
ctx.storage.get = AsyncMock(return_value=None)  # Simulate empty storage
ctx.log = MagicMock()

# Call the command directly
args = SaveNoteArgs(title="Test", content="Hello")
result = await save_note(args, ctx)

# Verify behavior
assert result["title"] == "Test"
ctx.storage.set.assert_awaited_once()
```

Run the tests:
```bash
pytest -v
```

Expected output:
```
tests/test_commands.py::TestSaveNoteArgs::test_valid PASSED
tests/test_commands.py::TestSaveNoteArgs::test_empty_title_rejected PASSED
tests/test_commands.py::TestSaveNote::test_creates_new_note PASSED
tests/test_commands.py::TestSaveNote::test_updates_existing_note PASSED
...
```

## Step 6: Start the Dev Server

```bash
huitzo pack dev
```

Then test with curl:
```bash
# Save a note
curl -X POST http://localhost:8080/api/v1/commands/notes/save-note \
  -H "Content-Type: application/json" \
  -d '{"title":"My First Note","content":"Hello from Huitzo!"}'

# Get the note back
curl -X POST http://localhost:8080/api/v1/commands/notes/get-note \
  -H "Content-Type: application/json" \
  -d '{"title":"My First Note"}'

# List all notes
curl -X POST http://localhost:8080/api/v1/commands/notes/list-notes \
  -H "Content-Type: application/json" \
  -d '{}'

# Delete the note
curl -X POST http://localhost:8080/api/v1/commands/notes/delete-note \
  -H "Content-Type: application/json" \
  -d '{"title":"My First Note"}'
```

## Step 7: Experiment

Try these modifications to deepen your understanding:

1. **Add a `search-notes` command** that filters notes by a keyword in the content
2. **Add a `tag` field** to `SaveNoteArgs` and store tags with each note
3. **Add a `word_count` field** to the response that counts words in the content
4. **Change the key prefix** from `"note:"` to something else and see what happens

## What You Learned

- `@command` registers a function as an API endpoint
- `ctx.storage` provides user-scoped persistent key-value storage
- Pydantic `BaseModel` + `Field` give you automatic input validation
- `ctx.log` provides structured logging
- Commands are `async` functions that return `dict` responses

## Next Step

Move on to **[02-ai-content-toolkit](../02-ai-content-toolkit/)** to learn how to integrate AI with `ctx.llm.complete()`.
