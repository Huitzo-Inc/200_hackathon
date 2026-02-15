# Claude Code MCP Setup

This guide configures Claude Code to connect to the Huitzo documentation server via MCP (Model Context Protocol), giving Claude direct access to searchable hackathon docs and SDK references.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and working
- The hackathon repository cloned locally
- Python 3.11+ installed

## Step 1: Start the Documentation Server

```bash
cd hackathon-2026
./bootws docs
```

You should see:

```
Documentation server started at http://localhost:8124
```

Verify it's running by visiting http://localhost:8124 in your browser.

## Step 2: Configure MCP in Claude Code

Claude Code reads MCP server configuration from `.claude/mcp.json` in the project root.

Create the file if it doesn't exist:

```bash
mkdir -p .claude
```

Add the following to `.claude/mcp.json`:

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

## Step 3: Test the Connection

Open Claude Code in the hackathon directory and try asking:

```
Search the docs for how to use ctx.llm
```

or

```
What are the available services in the Huitzo SDK?
```

Claude should use the MCP tools to search the documentation and return relevant results.

## Usage Examples

Once configured, Claude Code can:

**Search documentation:**
```
Search the Huitzo docs for "storage API"
```

**Find specific patterns:**
```
How do I define a command with a timeout?
```

**Browse starter templates:**
```
What starter templates are available?
```

**Get SDK reference info:**
```
What parameters does ctx.email.send() accept?
```

## Troubleshooting

### "MCP server not responding"

Make sure the documentation server is running:

```bash
./bootws docs
```

Check that port 8124 is not blocked:

```bash
curl http://localhost:8124
```

### "No MCP tools available"

1. Verify `.claude/mcp.json` exists and is valid JSON
2. Restart Claude Code after creating or editing the config file
3. Check that the URL in the config matches the running server

### "Connection refused"

The docs server might have stopped. Restart it:

```bash
./bootws docs
```

### Server won't start

Check if port 8124 is already in use:

```bash
lsof -i :8124
```

If another process is using the port, stop it or check `.mcp-docs.yaml` for port configuration.
