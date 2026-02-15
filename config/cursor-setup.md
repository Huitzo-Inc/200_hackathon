# Cursor MCP Setup

This guide configures Cursor to connect to the Huitzo documentation server via MCP (Model Context Protocol), giving the AI assistant direct access to searchable hackathon docs and SDK references.

## Prerequisites

- [Cursor](https://cursor.com) installed
- The hackathon repository cloned and opened in Cursor
- Python 3.11+ installed

## Step 1: Start the Documentation Server

Open the integrated terminal in Cursor and run:

```bash
./bootws docs
```

You should see:

```
Documentation server started at http://localhost:8124
```

Verify it's running by visiting http://localhost:8124 in your browser.

## Step 2: Configure MCP in Cursor

Cursor reads MCP server configuration from `.cursor/mcp.json` in the project root.

Create the file:

```bash
mkdir -p .cursor
```

Add the following to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "huitzo-docs": {
      "type": "url",
      "url": "http://localhost:8124/mcp"
    }
  }
}
```

## Step 3: Restart Cursor

After creating the MCP config, restart Cursor to pick up the new configuration:

1. Close the Cursor window
2. Reopen the hackathon project folder in Cursor

## Step 4: Test the Connection

In Cursor's AI chat (Cmd+L / Ctrl+L), try:

```
Search the Huitzo docs for how to use the @command decorator
```

The AI should use MCP tools to search the documentation server and return relevant information.

## Usage Examples

Once configured, Cursor's AI can:

**Search documentation while coding:**
```
What services are available on the ctx object?
```

**Get examples for specific APIs:**
```
Show me how to use ctx.storage.set() with TTL
```

**Understand SDK patterns:**
```
How do I structure a multi-command Intelligence Pack?
```

**Find troubleshooting info:**
```
Why am I getting a ValidationError when calling my command?
```

## Using Cursor Features with Huitzo

### Tab Completion

Cursor's tab completion works well with the Huitzo SDK. After importing `from huitzo_sdk import command, Context`, you'll get suggestions for:

- `@command()` decorator parameters
- `ctx.storage`, `ctx.llm`, `ctx.email`, `ctx.http`, `ctx.files` methods
- Pydantic model field types

### Inline Chat (Cmd+K / Ctrl+K)

Select code and press Cmd+K to ask questions about it or request modifications. Works well for:

- Refactoring command handlers
- Adding error handling
- Writing Pydantic models

### Composer (Cmd+I / Ctrl+I)

Use Composer for larger changes like:

- Creating new commands from scratch
- Adding tests for existing commands
- Building multi-command workflows

## Troubleshooting

### "No MCP tools available"

1. Verify `.cursor/mcp.json` exists and is valid JSON
2. Restart Cursor completely (not just reload)
3. Check that the documentation server is running on port 8124

### "MCP connection failed"

Make sure the docs server is running:

```bash
./bootws docs
curl http://localhost:8124  # Should return HTML
```

### AI doesn't seem to use the docs

Try being explicit:

```
Use the MCP tools to search the Huitzo documentation for "email sending"
```

### Server won't start

Check if port 8124 is already in use:

```bash
lsof -i :8124
```

If another process is using the port, stop it or check `.mcp-docs.yaml` for port configuration.
